#!/usr/bin/env python3
"""Verify ownership, source preservation and local Git history after migration."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
args = parser.parse_args()
for name in ('emulator', 'space/vm2', 'space/copycode', 'space/rv32i', 'space/forth'):
    assert (ROOT/name).is_dir() and not (ROOT/name).is_symlink(), name
    assert not (ROOT/name/'.git').exists(), name
for name in ('vm1', 'vm2', 'copycode', 'rv32i', 'pforth', 'copy-space', 'positional addressing'):
    assert not (ROOT/name).exists() and not (ROOT/name).is_symlink(), name
allowed = {'emulator', 'space', 'tools', 'docs', 'build', 'legacy', 'README.md',
           'ROADMAP.md', 'Makefile', 'project-git', '.gitignore', '.git', '.project-git',
           '.agents', '.codex', '.aws'}
assert not {p.name for p in ROOT.iterdir()} - allowed, 'unexpected root entry'
for current, children, files in os.walk(ROOT/'space', followlinks=False):
    at = Path(current)
    assert 'legacy' not in children, str(at/'legacy')
    children[:] = [n for n in children if n not in {'third_party', 'vendor', '__pycache__'}
                   and not (at/n).is_symlink()]
for top in ('emulator', 'space', 'tools'):
    for current, children, files in os.walk(ROOT/top, followlinks=False):
        at = Path(current)
        children[:] = [n for n in children if n not in {'build','dist','tmp','vendor','third_party','__pycache__'}]
        for name in children + files:
            path = at/name
            if path.is_symlink():
                assert path == ROOT/'emulator/emulator', 'unexpected link in active tree: '+str(path)
                assert path.resolve().is_relative_to(ROOT/'build/emulator'), str(path)
                assert not path.resolve().is_relative_to(ROOT/'legacy'), str(path)

for component in ('emulator', 'space/vm2', 'space/copycode', 'space/rv32i', 'space/forth'):
    for name in ('build', 'dist', 'tmp'):
        assert not (ROOT/component/name).exists() and not (ROOT/component/name).is_symlink(), component+'/'+name
cmd = [str(ROOT/'project-git')]
assert subprocess.check_output(cmd+['rev-parse', '--show-toplevel'], text=True).strip() == str(ROOT)
staged = subprocess.check_output(cmd+['ls-files', '--stage', '-z'])
for entry in staged.split(b'\0'):
    if not entry:
        continue
    mode, _, path = entry.partition(b'\t')
    assert not mode.startswith(b'160000 '), path
    parts = Path(os.fsdecode(path)).parts
    assert not any(p in {'.git', '.project-git', '.aws', '.codex', '.agents', '.opencode', '__pycache__', 'build', 'dist', 'tmp', 'vendor'} for p in parts), path
    assert not path.startswith(b'legacy/git/'), path
print("PASS active layout: components, root entries, Git index; archive not required")
