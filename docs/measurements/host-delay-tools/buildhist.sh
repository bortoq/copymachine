#!/bin/sh
set -e
src=$1; out=$2
rm -rf "$out.d"; mkdir -p "$out.d"; cp "$src"/*.c "$src"/*.h "$out.d"/
python3 $(dirname "$0")/counter_patch.py "$out.d/runtime.c"
python3 $(dirname "$0")/hist_patch.py "$out.d"
cc -Wall -Wextra -std=c11 -O2 "$out.d"/runtime.c "$out.d"/sys_ctrl.c "$out.d"/bitcopy.c "$out.d"/backend_bitcopy.c -o "$out"
