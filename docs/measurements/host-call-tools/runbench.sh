#!/bin/sh
# usage: runbench.sh PROG REPS : base (cpu 3), 1811 (cpu 5), call (cpu 7) in parallel, REPS runs each, sequentially per variant
P=$1; R=$2
python3 bench.py 3 ./emu-base L0.base $P $R > bench-$(basename $P .fth)-base.log 2>&1 &
python3 bench.py 5 ./emu-1811 L0.1811 $P $R > bench-$(basename $P .fth)-1811.log 2>&1 &
python3 bench.py 7 ./emu-call L0.call $P $R > bench-$(basename $P .fth)-call.log 2>&1 &
wait
