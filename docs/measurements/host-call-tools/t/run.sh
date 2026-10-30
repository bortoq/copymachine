#!/bin/sh
# usage: run.sh emu L0 letters
emu=$1; l0=$2; shift 2
for c in "$@"; do
  r=$( (cat $l0; printf "$c") | HW_TICKS=1 HOST_STATS=1 taskset -c 4 $emu -s 2147483648 -p 8 2>&1 >/dev/null | tr '\n' ' ')
  echo "$c $r"
done
