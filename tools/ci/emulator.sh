#!/bin/sh
# Check of the emulator: tools/ci/emulator.sh [gcc|clang] [release|sanitizers] (the GitHub matrix).
. "$(dirname "$0")/common.sh"
CC=${1:-gcc}
MODE=${2:-release}
export CC
case "$MODE" in
release)
    CFLAGS='-std=c11 -Wall -Wextra -Werror -pedantic -O2' ;;
sanitizers)
    CFLAGS='-std=c11 -Wall -Wextra -Werror -pedantic -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie'
    export ASAN_OPTIONS='detect_leaks=1:halt_on_error=1'
    export UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1' ;;
*) echo "unknown mode: $MODE" >&2; exit 2 ;;
esac
export CFLAGS
make -C emulator clean
make -C emulator -j1 check checked
make -C emulator clean
