#!/bin/sh
# make lint, make check-fast and the coverage summary: the same as the GitHub job "fast".
. "$(dirname "$0")/common.sh"
make lint
make check-fast
sh "$(dirname "$0")/licenses.sh"
echo "== coverage summary (gcov of the emulator, coverage.py of language/tools if installed) =="
make coverage
