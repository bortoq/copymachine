#!/usr/bin/env python3
# Every non-empty line of the previous ROADMAP.md (BASE, default HEAD; 17.1-17.10 ❌ -> ✅ applied)
# is in docs/journal/roadmap.md or in ROADMAP.md.
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def done(line):
    return re.sub(r'^### ❌ (17\.(?:[1-9]|10))\. ', r'### ✅ \1. ', line)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
    old = subprocess.run([str(ROOT / 'project-git'), 'show', f'{base}:ROADMAP.md'],
                         capture_output=True, text=True, check=True, cwd=ROOT).stdout
    have = set()
    for name in ('docs/journal/roadmap.md', 'ROADMAP.md'):
        have.update(line.rstrip() for line in (ROOT / name).read_text(encoding='utf-8').split('\n'))
    missing = [line for line in old.split('\n') if line.strip() and done(line).rstrip() not in have]
    if missing:
        sys.exit('roadmap: lines of %s not found in the journal or ROADMAP.md:\n' % base + '\n'.join(missing))
    print('roadmap: all lines of %s are in the journal or ROADMAP.md' % base)


if __name__ == '__main__':
    main()
