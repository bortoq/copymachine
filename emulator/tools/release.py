#!/usr/bin/env python3
"""Explicit source packaging, staged installation and archive verification."""
import argparse
import gzip
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def version(root):
    value = (root/'VERSION').read_text().strip()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?', value):
        raise ValueError('invalid release version')
    return value


def file_list(root):
    names = (root/'dist.manifest').read_text().splitlines()
    if names != sorted(set(names)):
        raise ValueError('dist.manifest must be sorted and contain no duplicates')
    for name in names:
        path = PurePosixPath(name)
        if not name or path.is_absolute() or '..' in path.parts or str(path) != name:
            raise ValueError(f'invalid distribution path: {name!r}')
        source = root/name
        if (source.is_symlink()) or not source.is_file():
            raise ValueError(f'distribution file missing or a symlink: {name}')
        if any(parent.is_symlink() for parent in source.parents if parent != root.parent):
            raise ValueError(f'distribution path traverses a symlink: {name}')
    return names


def create(root, output):
    names = file_list(root)
    prefix = 'emulator-'+version(root)
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', '0'))
    if not 0 <= epoch <= 0xffffffff:
        raise ValueError('SOURCE_DATE_EPOCH must fit gzip timestamp')
    payloads = {name: (root/name).read_bytes() for name in names}
    payloads['SHA256SUMS'] = ''.join(
        f'{hashlib.sha256(data).hexdigest()}  {name}\n'
        for name, data in sorted(payloads.items())).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as raw:
        temporary = Path(raw.name)
        try:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=epoch) as zipped:
                with tarfile.open(fileobj=zipped, mode='w', format=tarfile.USTAR_FORMAT) as archive:
                    for name, data in sorted(payloads.items()):
                        member = tarfile.TarInfo(prefix+'/'+name)
                        member.size = len(data)
                        member.mtime = epoch
                        member.mode = 0o755 if name != 'SHA256SUMS' and (root/name).stat().st_mode & 0o111 else 0o644
                        archive.addfile(member, io.BytesIO(data))
            raw.flush()
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name+'.sha256').write_text(f'{digest}  {output.name}\n')
    return output


def staged_path(destdir, path):
    location = Path(path)
    if not location.is_absolute() or '..' in location.parts:
        raise ValueError('installation paths must be absolute and contain no ..')
    return Path(destdir)/str(location).lstrip('/') if destdir else location


def install(root, binary, destdir, bindir, docdir):
    # Explicit files only: no build products, editor state or neighboring tree.
    binary_target = staged_path(destdir, bindir)/'emulator'
    documents = staged_path(destdir, docdir)
    binary_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(binary, binary_target)
    binary_target.chmod(0o755)
    for name in file_list(root):
        if name.startswith('doc/') or name in ('README.md', 'CHANGELOG.md', 'VERSION', 'LICENSE', 'src/proto.def', '.github/workflows/ci.yml'):
            target = documents/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root/name, target)
            target.chmod(0o644)
    print('Installed:', binary_target, 'and documentation:', documents)


def unpack(archive_path, directory):
    # Reject links, duplicate paths and traversal before extracting any file.
    with tarfile.open(archive_path, 'r:gz') as archive:
        members = archive.getmembers()
        seen = set()
        prefix = None
        for member in members:
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or len(path.parts) < 2 or member.name in seen
                    or str(path) != member.name):
                raise ValueError('invalid archive member: '+member.name)
            seen.add(member.name)
            if prefix is None:
                prefix = path.parts[0]
            if path.parts[0] != prefix:
                raise ValueError('multiple archive roots')
        if not prefix:
            raise ValueError('empty archive')
        for member in members:
            target = directory/member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, target.open('wb') as output:
                shutil.copyfileobj(source, output)
            target.chmod(member.mode & 0o777)
    root = directory/prefix
    if prefix != 'emulator-'+version(root):
        raise ValueError('archive name/version mismatch')
    names = file_list(root)
    if seen != {prefix+'/'+name for name in names+['SHA256SUMS']}:
        raise ValueError('archive files differ from dist.manifest')
    expected = ''.join(f'{hashlib.sha256((root/name).read_bytes()).hexdigest()}  {name}\n' for name in names)
    if (root/'SHA256SUMS').read_text() != expected:
        raise ValueError('archive checksum mismatch')
    return root


def check(archive_path):
    with tempfile.TemporaryDirectory(prefix='emulator release check ') as directory:
        base = Path(directory)
        root = unpack(archive_path, base)
        env = dict(os.environ)
        for name in ('MAKEFLAGS','MFLAGS','MAKELEVEL','SPACE_EMULATOR'):
            env.pop(name, None)
        def make(*arguments):
            subprocess.run(['make', *arguments], cwd=root, env=env, check=True)
        # Check the shipped generated header against its shipped generator.
        subprocess.run(['python3','tools/proto_gen.py','src/proto.def',str(base/'proto_gen.h')],cwd=root,env=env,check=True)
        if (base/'proto_gen.h').read_bytes() != (root/'src/proto_gen.h').read_bytes():
            raise ValueError('shipped protocol header is stale')
        make('check')
        # Each backend must also install and run independently.
        for backend in ('network', 'bitcopy'):
            make('install', 'BACKEND='+backend, 'DESTDIR='+str(base/backend), 'prefix=/usr')
            packet = subprocess.check_output(['python3', 'examples/write-byte.py', '-p', '8'], cwd=root, env=env)
            result = subprocess.run([str(base/backend/'usr/bin/emulator'), '-p', '8', '-t', '2'], input=packet, capture_output=True, timeout=15)
            if result.returncode or result.stdout != b'A' or result.stderr:
                raise ValueError('installed '+backend+' smoke test failed')
        stage = base/'staged installation'
        make('install', 'DESTDIR='+str(stage), 'prefix=/usr',
             'bindir=/usr/bin', 'docdir=/usr/share/doc/emulator')
        binary = stage/'usr/bin/emulator'
        if binary.read_bytes() != (root/'emulator').read_bytes() or binary.stat().st_mode & 0o777 != 0o755:
            raise ValueError('installed executable differs')
        documents = stage/'usr/share/doc/emulator'
        for name in ('VERSION','LICENSE','CHANGELOG.md','src/proto.def','doc/emulator-contract.md'):
            if (documents/name).read_bytes() != (root/name).read_bytes():
                raise ValueError('installed release material differs: '+name)
        packet = subprocess.check_output(['python3','examples/write-byte.py','-s','65520','-p','8','--write','A'],cwd=root,env=env)
        run = subprocess.run([str(binary),'-p','8','-t','2'],input=packet,capture_output=True,timeout=10,env=env)
        if run.returncode or run.stdout != b'A' or run.stderr:
            raise ValueError('installed executable smoke test failed')
        repacked = create(root, base/'repacked.tar.gz')
        if repacked.read_bytes() != archive_path.read_bytes():
            raise ValueError('archive is not reproducible after build/tests/install')
        print('SOURCE RELEASE CHECK PASSED:', archive_path)
        print('Clean archive build/tests, staged install/run and deterministic repack passed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    package = sub.add_parser('create')
    package.add_argument('--output', type=Path, required=True)
    installation = sub.add_parser('install')
    installation.add_argument('--binary', type=Path, required=True)
    installation.add_argument('--destdir', default='')
    installation.add_argument('--bindir', required=True)
    installation.add_argument('--docdir', required=True)
    verification = sub.add_parser('check')
    verification.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == 'create':
            print('Source archive:', create(ROOT,args.output))
        elif args.action == 'install':
            install(ROOT,args.binary,args.destdir,args.bindir,args.docdir)
        else:
            check(args.archive.resolve())
    except (OSError, ValueError, subprocess.CalledProcessError, tarfile.TarError) as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__':
    main()
