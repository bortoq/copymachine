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
parser.add_argument('--require-local-history', action='store_true')
args = parser.parse_args()
record = json.loads((ROOT/'legacy/MIGRATION.json').read_text())
for row in record['files']:
    path = ROOT/row['new']
    # Retained, actively developed integration files may subsequently change.
    if row['new'].startswith('legacy/'):
        assert not path.is_symlink(), row['new']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['new']
        assert (ROOT/row['old']).read_bytes() == path.read_bytes(), row['old']
histories = 0
for name, row in record['histories'].items():
    if not (ROOT/row['git_dir']).exists():
        assert not args.require_local_history, row['git_dir']
        continue
    actual = subprocess.check_output(
        ['git', '--git-dir='+str(ROOT/row['git_dir']), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == row['head'], name
    histories += 1
for name in ('vm1', 'vm2', 'copycode', 'rv32i', 'pforth'):
    assert (ROOT/name).is_dir() and not (ROOT/name).is_symlink(), name
    assert not (ROOT/name/'.git').exists(), name
for name in record['retained_active']:
    assert (ROOT/name).is_file() and not (ROOT/name).is_symlink(), name
for row in record['symlinks']:
    if row['existed']:
        assert (ROOT/row['new']).exists(), row['new']
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
print(f"PASS layout: {len(record['files'])} source records, {histories} local Git histories, "
      f"{len(record['retained_active'])} active integration files, no Git links or local artifacts in index")
