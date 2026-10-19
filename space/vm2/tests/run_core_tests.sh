#!/bin/sh
# Independent kernel checks; needs only this checkout and the built emulator.
set -eu
cd "$(dirname "$0")/.."
TMPDIR=${TMPDIR:-"$PWD/tmp"}
mkdir -p "$TMPDIR"
export TMPDIR PYTHONDONTWRITEBYTECODE=1
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
CC=${CC-gcc}
CFLAGS=${CFLAGS--std=c11 -Wall -Wextra -O3}
CPPFLAGS=${CPPFLAGS-}
LDFLAGS=${LDFLAGS-}
LDLIBS=${LDLIBS-}

echo "== independent bitcopy oracle =="
$CC $CPPFLAGS $CFLAGS $LDFLAGS -o "$tmp/bitcopy" tests/test_bitcopy.c tests/reference/bitcopy.c $LDLIBS
"$tmp/bitcopy"

echo "== independent decode/tick/SYS oracle =="
# test_engine includes tests/reference/engine.c to exercise private decoder windows too.
$CC $CPPFLAGS $CFLAGS $LDFLAGS -o "$tmp/engine" tests/test_engine.c tests/reference/config.c tests/reference/sys_ctrl.c tests/reference/globals.c tests/reference/bitcopy.c $LDLIBS
"$tmp/engine"

echo "== SYS unit tests =="
$CC $CPPFLAGS $CFLAGS $LDFLAGS -Itests/reference -o "$tmp/sys" tests/test_sys.c tests/reference/engine.c tests/reference/config.c tests/reference/sys_ctrl.c tests/reference/globals.c tests/reference/bitcopy.c $LDLIBS
"$tmp/sys"

echo "== independent process/configuration oracle =="
python3 -B tests/test_core_cli.py "${1:-${SPACE_EMULATOR:-./space}}"

python3 -B tests/test_schedule.py

python3 -B tests/test_clean.py

echo "CORE CHECKS PASSED"
