#!/bin/sh
# Independent kernel checks; needs only this checkout and the built emulator.
set -eu
cd "$(dirname "$0")/.."
mkdir -p "$PWD/tmp"
export TMPDIR="$PWD/tmp" PYTHONDONTWRITEBYTECODE=1
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
CC=${CC-gcc}
CFLAGS=${CFLAGS--std=c11 -Wall -Wextra -O3}
CPPFLAGS=${CPPFLAGS-}
LDFLAGS=${LDFLAGS-}
LDLIBS=${LDLIBS-}

echo "== independent bitcopy oracle =="
$CC $CPPFLAGS $CFLAGS $LDFLAGS -o "$tmp/bitcopy" tests/test_bitcopy.c bitcopy.c $LDLIBS
"$tmp/bitcopy"

echo "== independent decode/tick/SYS oracle =="
# test_engine includes engine.c to exercise private decoder windows too.
$CC $CPPFLAGS $CFLAGS $LDFLAGS -o "$tmp/engine" tests/test_engine.c config.c sys_ctrl.c globals.c bitcopy.c $LDLIBS
"$tmp/engine"

echo "== SYS unit tests =="
$CC $CPPFLAGS $CFLAGS $LDFLAGS -I. -o "$tmp/sys" tests/test_sys.c engine.c config.c sys_ctrl.c globals.c bitcopy.c $LDLIBS
"$tmp/sys"

echo "== independent process/configuration oracle =="
python3 -B tests/test_core_cli.py "${1:-${SPACE_EMULATOR:-./space}}"

python3 -B tests/test_schedule.py

python3 -B tests/test_clean.py

echo "CORE CHECKS PASSED"
