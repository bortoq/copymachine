#!/usr/bin/env python3
"""Build/test current sources without legacy, cached images or directory aliases."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--releases', action='store_true', help='also check all standalone source releases')
parser.add_argument('--releases-only', action='store_true', help='check standalone releases without repeating the normal workspace suite')
parser.add_argument('--release-component', action='append', choices=('emulator','space/vm2','space/rv32i','space/forth','space/copycode'), help='limit standalone checks to selected components')
args = parser.parse_args()
sys.path.insert(0, str(ROOT/'space/rv32i/modules'))
from rv32i_toolchain import Toolchain
compiler = Toolchain().compiler
assert not Path(compiler).resolve().is_relative_to(ROOT/'legacy')
env = dict(os.environ, RISCV_CC=compiler, PYTHONDONTWRITEBYTECODE='1')
for name in ('EMULATOR', 'EMULATOR_ROOT', 'COPYCODE_ROOT', 'RV32I_ROOT', 'VM2_ROOT',
             'EMULATOR_PROTO', 'CHECKED_EMULATOR', 'PYTHONPATH', 'MAKEFLAGS', 'MFLAGS',
             'MAKELEVEL', 'MAKEOVERRIDES', 'VM2_CACHE', 'TMPDIR', 'BUILD_DIR', 'DISTDIR'):
    env.pop(name, None)

def run(command, root, timeout=600):
    print('RUN', command, flush=True)
    # Only the full copycode stream matrix needs sparse files larger than 16 MiB.
    file_mib = '512' if 'space/copycode' in command and 'distcheck' in command else '16'
    bounded = [sys.executable, '-B', str(root/'space/vm2/tools/limited_run.py'),
               '--seconds', str(timeout), '--memory-mib', '768', '--file-mib', file_mib]
    subprocess.run(bounded+command, cwd=root, env=env, check=True, timeout=timeout+5)

with tempfile.TemporaryDirectory(prefix='copymachine-detached-') as folder:
    base = Path(folder)
    root = base/'workspace'
    root.mkdir()
    index_env = dict(os.environ, GIT_INDEX_FILE=str(base/'index'))
    git = [str(ROOT/'project-git')]
    subprocess.run(git+['read-tree', 'HEAD'], env=index_env, check=True)
    subprocess.run(git+['add', '--all'], env=index_env, check=True)
    names = subprocess.check_output(git+['ls-files', '-z'], env=index_env).split(b'\0')
    active = [n for n in names if n and not n.startswith(b'legacy/')]
    subprocess.run(git+['checkout-index', '-z', '--stdin', '--prefix='+str(root)+'/'],
                   env=index_env, input=b'\0'.join(active)+b'\0', check=True)
    assert not (root/'legacy').exists() and not (root/'build').exists()
    run(['git', 'init', '-q'], root)
    run(['git', 'add', '--all'], root)
    baseline = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root)
    if not args.releases_only:
        run(['make', '-j1'], root)
        run(['make', '-j1', 'check'], root)
        result = subprocess.run([str(root/'tools/run/forth')], cwd=base, env=env,
                                input=b'1 2 + .\nbye\n', capture_output=True, timeout=30)
        assert (result.returncode, result.stdout, result.stderr) == (0, b'3 \n', b''), result
    if args.releases or args.releases_only:
        run(['make', '-C', 'emulator', '-j1', 'runtime-bitcopy', 'runtime-network'], root)
        # copycode's explicit triple-ABI suite uses the independent native oracle.
        run(['make', '-C', 'space/vm2', '-j1', 'reference'], root)
        for component in (args.release_component or ('emulator', 'space/vm2', 'space/rv32i', 'space/forth', 'space/copycode')):
            run(['make', '-C', component, '-j1', 'distcheck'], root)
    cache = root/'build/space/rv32i/tmp/rv32i-toolchain'
    cache.mkdir(parents=True, exist_ok=True)
    (cache/'host-compiler-sentinel').write_bytes(b'compiler prerequisite')
    run(['make', 'clean'], root)
    assert (cache/'host-compiler-sentinel').read_bytes() == b'compiler prerequisite'
    assert not (root/'build/space/forth/build/pforth').exists()
    assert not (root/'legacy').exists()
    for component in ('emulator', 'space/vm2', 'space/rv32i', 'space/forth', 'space/copycode'):
        for name in ('build', 'dist', 'tmp'):
            assert not (root/component/name).exists() and not (root/component/name).is_symlink()
    actual_status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root)
    if actual_status != baseline:
        subprocess.run(['git', 'diff', '--stat'], cwd=root, check=True)
        subprocess.run(['git', 'status', '--short'], cwd=root, check=True)
        raise AssertionError('build/test/clean changed source files')
print('PASS detached source tree: no archive, requested build/test/release checks, clean outputs, preserved host compiler and source status')
result_dir = ROOT/'build/verification'
result_dir.mkdir(parents=True, exist_ok=True)
(result_dir/'detached.json').write_text(json.dumps(dict(result='PASS', compiler=compiler,
    standalone_releases=args.releases or args.releases_only, normal_checks=not args.releases_only, legacy_present=False, directory_aliases=False,
    source_entries=len(active), release_components=args.release_component), indent=2)+'\n')
