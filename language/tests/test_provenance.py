"""PROVENANCE.json: every source in src/ is recorded, its digest is that of the file in the tree
(a missing file is an error), and the order of compilation is the one the tools use; the same for
boot/PROVENANCE.json: every file of boot/ is listed with its digest."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import paths


def digest(path):
    assert path.is_file(), path
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = json.loads((paths.ROOT / 'PROVENANCE.json').read_text())
assert record['order'] == paths.KERNEL_FILES, record['order']
assert sorted(record['files']) == sorted('src/' + name for name in paths.KERNEL_FILES)
for name, entry in record['files'].items():
    assert digest(paths.ROOT / name) == entry.get('copy_sha256', entry.get('sha256')), ('changed', name)
    print('PASS provenance', name)
boot = paths.ROOT / 'boot'
listed = json.loads((boot / 'PROVENANCE.json').read_text())['files']
actual = sorted(str(p.relative_to(boot)) for p in boot.rglob('*')
                if p.is_file() and p.name != 'PROVENANCE.json' and '__pycache__' not in p.parts and 'build' not in p.parts)
assert sorted(listed) == actual, sorted(set(listed) ^ set(actual))
for name, sha in listed.items():
    assert digest(boot / name) == sha, ('changed', name)
print('ALL', len(record['files']), 'sources and', len(listed), 'boot files match their records')
