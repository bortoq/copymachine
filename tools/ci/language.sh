#!/bin/sh
# Boot of L0 and the language check; the sha256 of L0 goes to language/build/L0.sha256.
# Needs cc -m32 (gcc-multilib).
. "$(dirname "$0")/common.sh"
make -C language -j1 boot
make -C language -j1 check
(cd language/build && sha256sum L0.boot | tee L0.sha256)
