#!/usr/bin/env python3
"""Verify the layout of main: root entries, no outputs in the index, no links in the active tree."""
from pathlib import Path
import argparse
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
args = parser.parse_args()
for name in ('emulator', 'language', 'tools', 'docs'):
    assert (ROOT/name).is_dir() and not (ROOT/name).is_symlink(), name
for name in ('space', 'vm2', 'copycode', 'rv32i', 'pforth'):
    assert not (ROOT/name).exists(), name
allowed = {'emulator', 'language', 'tools', 'docs', 'build', 'README.md', 'Makefile', 'project-git',
           '.gitignore', '.git', '.project-git', '.agents', '.codex', '.aws', '.claude', '.ruff_cache', '.opencode',
           'LICENSE', 'ROADMAP.md', 'pyproject.toml'}
assert not {p.name for p in ROOT.iterdir()} - allowed, 'unexpected root entry'
for top in ('emulator', 'language', 'tools'):
    for current, children, files in os.walk(ROOT/top, followlinks=False):
        at = Path(current)
        children[:] = [n for n in children if n not in {'build', 'tmp', '__pycache__', 'csrc'}]
        for name in children + files:
            path = at/name
            if path.is_symlink():
                assert path == ROOT/'emulator/emulator', 'unexpected link in active tree: '+str(path)
cmd = [str(ROOT/'project-git')]
assert subprocess.check_output(cmd+['rev-parse', '--show-toplevel'], text=True).strip() == str(ROOT)
for entry in subprocess.check_output(cmd+['ls-files', '--stage', '-z']).split(b'\0'):
    if not entry:
        continue
    mode, _, path = entry.partition(b'\t')
    assert not mode.startswith(b'160000 '), path
    parts = Path(os.fsdecode(path)).parts
    assert not any(p in {'.git', '.project-git', '.aws', '.codex', '.agents', '.opencode', '__pycache__', 'build', 'dist', 'tmp', 'vendor'} for p in parts), path
print("PASS layout: root entries, Git index")
