"""PROVENANCE.json: every source in src/ has a recorded origin (null: a new source of the language),
the origin is unchanged, and the order of compilation of PROVENANCE.json is the one the tools use."""
import hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import paths

record = json.loads((paths.ROOT / 'PROVENANCE.json').read_text())
assert record['order'] == paths.KERNEL_FILES, record['order']
assert sorted(record['files']) == sorted('src/' + name for name in paths.KERNEL_FILES)
for name, entry in record['files'].items():
    assert (paths.ROOT / name).is_file(), name
    if entry['origin'] is None:
        print('PASS provenance', name, '<- new in', entry['item'])
        continue
    origin = paths.WORKSPACE / entry['origin']
    assert hashlib.sha256(origin.read_bytes()).hexdigest() == entry['origin_sha256'], ('the origin changed', name)
    print('PASS provenance', name, '<-', entry['origin'])
print('ALL', len(record['files']), 'sources have their origin recorded')
# 15.1: the definition of the word "space", the copy of the sources of the working emulator. The
# origin is unchanged (the language changes only the copy); the files of space/ are exactly these.
copies = record['space_files']
assert sorted(copies) == sorted(str(path.relative_to(paths.ROOT)) for path in (paths.ROOT / 'space').iterdir()), sorted(copies)
for name, entry in copies.items():
    origin = paths.WORKSPACE / entry['origin']
    assert hashlib.sha256(origin.read_bytes()).hexdigest() == entry['origin_sha256'], ('the origin changed', name)
    print('PASS provenance', name, '<-', entry['origin'])
print('ALL', len(copies), 'files of the definition of the word "space" have their origin recorded')
