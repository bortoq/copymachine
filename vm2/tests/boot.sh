#!/bin/sh
# Seed over stdin: no output on empty, short or all-NOP streams, a bad
# flag errors out, and -t bounds the run. The program itself is loaded
# from the stdin channel (proc_n * instruction_size bits), so an all-zero
# stream is an all-NOP program that stops immediately.
set -e
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
SPACE_EMULATOR=${SPACE_EMULATOR:-./space}
if [ ! -x "$SPACE_EMULATOR" ]; then
  echo "no executable $SPACE_EMULATOR, run make first"
  exit 1
fi
printf '' | "$SPACE_EMULATOR" -t 1 > "$tmp"/boot_empty.out
test ! -s "$tmp"/boot_empty.out
echo "ok: empty stdin, silence"
head -c 100 /dev/zero | timeout 5 "$SPACE_EMULATOR" -t 1 > "$tmp"/boot_short.out
test ! -s "$tmp"/boot_short.out
echo "ok: short stream, silence"
head -c 376 /dev/zero | timeout 5 "$SPACE_EMULATOR" > "$tmp"/boot_nop.out
test ! -s "$tmp"/boot_nop.out
echo "ok: all-NOP program, silence and stop"
printf '\000' | timeout 5 "$SPACE_EMULATOR" -s 26 -p 1 > "$tmp"/boot_min.out
test ! -s "$tmp"/boot_min.out
echo "ok: stream below the seed count, silence (no -t)"
# stub loader: an all-NOP image overwrites the seed, so the space stops
if [ -f tests/stub/nop.bin ]; then
  timeout 5 "$SPACE_EMULATOR" -s 65520 -p 64 < tests/stub/nop.bin > "$tmp"/boot_stub.out
  test ! -s "$tmp"/boot_stub.out
  echo "ok: stub loader, silence and stop (no -t)"
fi
# --nop generates a stub for any size, including a<8
python3 tools/driver_gen.py -s 16 -p 1 --nop -o "$tmp"/nop16.bin 2>/dev/null
timeout 5 "$SPACE_EMULATOR" -s 16 -p 1 < "$tmp"/nop16.bin > "$tmp"/boot_nop16.out
test ! -s "$tmp"/boot_nop16.out
echo "ok: --nop stub in a tiny space (-s 16 -p 1), silence and stop"
set +e
"$SPACE_EMULATOR" foo < /dev/null >/dev/null 2>&1
code=$?
set -e
test "$code" -eq 2
echo "ok: bad flag gives exit code 2"
