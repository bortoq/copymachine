#!/bin/sh
# Markdown: relative links lead to existing files (ROADMAP.md and docs/design/ excluded);
# the Markdown volume is below that of the tag archive-2026-10-30.
. "$(dirname "$0")/common.sh"
python3 -I - <<'PY'
import re, subprocess, sys
from pathlib import Path

root = Path.cwd()
files = [p for p in root.rglob('*.md')
         if not {'.git', 'build', 'node_modules'} & set(p.relative_to(root).parts)]
bad, total = [], 0
for p in files:
    rel = p.relative_to(root).as_posix()
    total += p.stat().st_size
    if rel == 'ROADMAP.md' or rel.startswith('docs/design/'):
        continue
    text = re.sub(r'```.*?```', '', p.read_text(encoding='utf-8'), flags=re.S)
    text = re.sub(r'`[^`\n]*`', '', text)
    for m in re.finditer(r'\]\(([^)\s]+)\)', text):
        t = m.group(1).split('#')[0]
        if not t or re.match(r'^[a-z][a-z0-9+.-]*:', t):
            continue
        if not (p.parent / t).exists():
            bad.append('%s: %s' % (rel, m.group(1)))
if bad:
    sys.exit('broken Markdown links:\n' + '\n'.join(bad))

TAG = 'archive-2026-10-30'
git = ['git'] if (root / '.git').exists() else ['./project-git']
try:
    ls = subprocess.run(git + ['ls-tree', '-r', TAG], capture_output=True, text=True, check=True).stdout
except (OSError, subprocess.CalledProcessError):
    print('docs: tag %s not available, volume check skipped' % TAG)
    print('docs: links ok, %d bytes of Markdown' % total)
    sys.exit(0)
old = 0
for line in ls.splitlines():
    meta, name = line.split('\t', 1)
    if name.endswith('.md'):
        old += len(subprocess.run(git + ['cat-file', 'blob', meta.split()[2]],
                                  capture_output=True, check=True).stdout)
if total >= old:
    sys.exit('Markdown volume %d is not below %d of %s' % (total, old, TAG))
print('docs: links ok, Markdown %d bytes < %d on %s' % (total, old, TAG))
PY
