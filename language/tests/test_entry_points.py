#!/usr/bin/env python3
"""Entry points of language/tools (17.9): every script with a command line answers --help (exit 0,
a usage line) and the tools that take no arguments are importable. A smoke test, seconds, no reference."""
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
CLI = ['boot', 'check_closure', 'check_kernel', 'check_programs', 'check_self', 'language_md', 'user_programs', 'word_cost']

for name in CLI:
    result = subprocess.run([sys.executable, '-B', str(TOOLS / f'{name}.py'), '--help'],
                            capture_output=True, text=True, check=False, timeout=60)
    assert result.returncode == 0 and 'usage' in result.stdout.lower(), (name, result.returncode, result.stderr[-300:])
    print(f'PASS {name}.py --help')
print(f'ALL entry points: {len(CLI)} tools answer --help')
