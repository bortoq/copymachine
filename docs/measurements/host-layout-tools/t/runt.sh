#!/bin/sh
# usage: runt.sh emu L0 letters... : the ticks of each test (the loop of 1000)
emu=$1; l0=$2; shift 2
for c in "$@"; do
  r=$( (cat $l0; printf "$c") | HW_TICKS=1 HOST_STATS=1 $emu -s 2147483648 -p 8 2>&1 >/dev/null | tr '\n' ' ')
  echo "$c $r"
done
