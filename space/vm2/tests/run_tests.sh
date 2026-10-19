#!/bin/sh
# Emulator checks (host side: engine, bit copy, config, SYS protocol,
# channel data path) plus local copycode integration fixtures.
set -e
cd "$(dirname "$0")/.."
TMPDIR=${TMPDIR:-"$PWD/tmp"}
mkdir -p "$TMPDIR"
export TMPDIR PYTHONDONTWRITEBYTECODE=1
export CC="${CC-gcc}"
export CFLAGS="${CFLAGS--std=c11 -Wall -Wextra -O3}"
export CPPFLAGS="${CPPFLAGS-}" LDFLAGS="${LDFLAGS-}" LDLIBS="${LDLIBS-}"
SPACE_EMULATOR=$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "${1:-${SPACE_EMULATOR:-./space}}")
export SPACE_EMULATOR
if [ ! -x "$SPACE_EMULATOR" ]; then
  echo "no executable $SPACE_EMULATOR; build it before running tests" >&2
  exit 1
fi
before=$(sha256sum "$SPACE_EMULATOR")
echo "== testing $SPACE_EMULATOR =="
./tests/run_core_tests.sh "$SPACE_EMULATOR"

echo "== SYS end-to-end driver =="
./tests/sys_e2e.sh

echo "== config limits =="
./tests/cfg.sh

echo "== wide format =="
./tests/wide.sh

echo "== boot =="
./tests/boot.sh

echo "== stdin boot and in-space diagnostics =="
python3 tests/test_boundary.py

echo "== shared boundary description =="
python3 tests/test_machine.py

echo "== streaming transport and separate terminal streams =="
python3 tests/test_transport.py

echo "== immutable cooperative checkpoint archives =="
python3 tests/test_checkpoint.py

echo "== dynamic copycode trace and audit =="
python3 tests/test_dynamic_trace.py

echo "== copycode: in-space SYS driver =="
./tests/copycode/sys_driver.sh

python3 -B tests/check_local_schedules.py

after=$(sha256sum "$SPACE_EMULATOR")
[ "$before" = "$after" ] || { echo "selected executable changed during tests" >&2; exit 1; }
echo "ALL CHECKS PASSED (selected executable unchanged)"
