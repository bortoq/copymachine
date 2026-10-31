#!/bin/sh
# usage: runt.sh emu L0 letters... : ticks and seconds (user cpu) of each test
emu=$1; l0=$2; shift 2
for c in "$@"; do
  s=$(date +%s.%N)
  r=$( (cat $l0; printf "$c") | HW_TICKS=1 taskset -c 6 $emu -s 2147483648 -p 8 2>&1 >/dev/null | head -1 | tr '\n' ' ')
  e=$(date +%s.%N)
  echo "$c $r $(echo "$e - $s" | bc)"
done
