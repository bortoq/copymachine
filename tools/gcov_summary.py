#!/usr/bin/env python3
"""Line coverage of C sources from the gcov data of several binaries: `gcov_summary.py DIR[:DIR...] SRC...`.

Runs gcov on every .gcda of DIR, unites the lines executed by any binary and prints per file and
total percent, then the lines never executed. Needs only gcc's gcov."""
import gzip
import json
import subprocess
import sys
from pathlib import Path


def main():
    dirs, sources = [Path(d) for d in sys.argv[1].split(':')], sys.argv[2:]
    names = {Path(s).resolve(): s for s in sources}
    hit = {}
    for gcda in sorted(g for d in dirs for g in d.rglob('*.gcda')):
        out = subprocess.run(['gcov', '--json-format', '--stdout', gcda.name], cwd=gcda.parent,
                             capture_output=True, check=True).stdout
        try:
            out = gzip.decompress(out)
        except OSError:
            pass
        for line in out.splitlines():
            for f in json.loads(line)['files']:
                path = (gcda.parent / f['file']).resolve()
                if path not in names:
                    continue
                lines = hit.setdefault(path, {})
                for entry in f['lines']:
                    n = entry['line_number']
                    lines[n] = lines.get(n, 0) + entry['count']
    total = covered = 0
    missing = []
    for path, name in sorted(names.items(), key=lambda kv: kv[1]):
        lines = hit.get(path, {})
        c = sum(1 for v in lines.values() if v)
        print(f'coverage {name}: {c}/{len(lines)} lines {100 * c / max(len(lines), 1):.1f}%')
        total += len(lines)
        covered += c
        missing += [f'{name}:{n}' for n, v in sorted(lines.items()) if not v]
    print(f'coverage emulator total: {covered}/{total} lines {100 * covered / max(total, 1):.1f}%')
    if missing:
        print('not executed: ' + ' '.join(missing))


main()
