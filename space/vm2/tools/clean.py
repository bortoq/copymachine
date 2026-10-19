#!/usr/bin/env python3
"""Remove owned build/test outputs without following directory symlinks."""
import argparse
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = {'.git', '.agents', '.codex', '.aws', '.opencode'}


def clean(root, binary, distdir, benchmark):
    root = root.resolve()
    # The distribution inventory also protects source files without Git.
    sources = {root/name for name in (root/'dist.manifest').read_text().splitlines()}
    def absolute(name):
        path = Path(name)
        return Path(os.path.abspath(path if path.is_absolute() else root/path))
    files = {absolute(binary), absolute(str(binary)+'.build-config'),
             absolute(str(binary)+'.build-config.tmp'), root/'space',
             root/'space.build-config', root/'space.build-config.tmp',
             root/'space-dev', root/'tests/test_bitcpy'}
    directories = {root/'tmp', root/'dist', root/'build', absolute(distdir), absolute(benchmark)}
    for current, children, names in os.walk(root, followlinks=False):
        at = Path(current)
        children[:] = [name for name in children if name not in ENVIRONMENT]
        for name in list(children):
            path = at/name
            if path in directories or name == '__pycache__':
                directories.add(path)
                children.remove(name)
        for name in names:
            if name.endswith(('.o', '.pyc', '.pyo', '.build-config', '.build-config.tmp')):
                files.add(at/name)
                for suffix in ('.build-config.tmp', '.build-config'):
                    if name.endswith(suffix):
                        files.add(at/name[:-len(suffix)])
                        break
    # Validate every removal first, before modifying any path. Custom output
    # directories cannot turn clean into deletion of sources or external data.
    for path in files | directories:
        if path == root or root not in path.parents:
            raise ValueError('clean output must be inside the project: '+str(path))
        if any(part in ENVIRONMENT for part in path.relative_to(root).parts):
            raise ValueError('clean cannot remove environment state: '+str(path))
        if any(source == path or path in source.parents for source in sources):
            raise ValueError('clean cannot remove distribution sources: '+str(path))
        # A configured directory under a symlink must not reach another tree.
        if any(parent.is_symlink() for parent in path.parents if parent != root.parent):
            raise ValueError('clean output traverses a symlink: '+str(path))
        if path in files and path.is_dir() and not path.is_symlink():
            raise ValueError('binary/build output is a directory: '+str(path))
    for path in sorted(directories, key=lambda p: len(p.parts)):
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)
    for path in files:
        path.unlink(missing_ok=True)
    # Remove empty custom build directories, without touching source trees.
    for path in files | directories:
        parent = path.parent
        while parent != root and root in parent.parents:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent
    print('Cleaned build outputs, test/benchmark scratch, release archives and Python caches')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    parser.add_argument('--distdir', required=True)
    parser.add_argument('--benchmark', required=True)
    args = parser.parse_args()
    try:
        clean(ROOT, args.binary, args.distdir, args.benchmark)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__':
    main()
