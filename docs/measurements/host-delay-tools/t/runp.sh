#!/bin/sh
# usage: runp.sh emu L0 letters... : the phases of a tick and the host calls (HW_PROF)
emu=$1; l0=$2; shift 2
for c in "$@"; do
  echo "== test $c"
  (cat $l0; printf "$c") | HW_TICKS=1 HW_PROF=1 taskset -c 6 $emu -s 2147483648 -p 8 2>&1 >/dev/null | grep -v prog-hash
done
