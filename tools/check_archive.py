#!/usr/bin/env python3
"""Explicit optional audit of the preserved archive and its Git histories."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--require-local-history',action='store_true')
args=parser.parse_args()
if not (ROOT/'legacy/MIGRATION.json').is_file():
    # The archive is local only and not part of the repository.
    print('SKIP archive: legacy/ is not present in this checkout');raise SystemExit(0)
record = json.loads((ROOT/'legacy/MIGRATION.json').read_text())
for row in record['files']:
    owner = row.get('current_archive', row['new'])
    path = ROOT/owner
    # Retained, actively developed integration files may subsequently change.
    if owner.startswith('legacy'):
        assert not path.is_symlink(), row['new']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row.get('current_sha256', row['sha256']), row['new']
        if not row.get('archived_only'):
            assert (ROOT/row.get('current', row['old'])).read_bytes() == path.read_bytes(), row['old']
for row in record.get('detachment', {}).get('archived_files', []):
    path = ROOT/row['path']
    assert not path.is_symlink(), row['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['path']
histories = 0
for name, row in record['histories'].items():
    if not (ROOT/row['git_dir']).exists():
        assert not args.require_local_history, row['git_dir']
        continue
    actual = subprocess.check_output(
        ['git', '--git-dir='+str(ROOT/row['git_dir']), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == row['head'], name
    histories += 1
for name in record['retained_active']:
    assert (ROOT/name).is_file() and not (ROOT/name).is_symlink(), name
for row in record['symlinks']:
    if row['existed'] and not row.get('retired_alias'):
        assert (ROOT/row['new']).exists(), row['new']
print(f"PASS archive: {len(record['files'])} source records, {histories} preserved local Git histories")
