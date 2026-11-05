#!/bin/sh
# The long runs of the chain of languages (tower/): make check-tower-long (own limit of 1800 s). The log goes to build/ci/check-tower-long.log.
. "$(dirname "$0")/common.sh"
mkdir -p build/ci
rm -f build/ci/check-tower-long.fail
{ make check-tower-long 2>&1 || echo "make exit $?" >build/ci/check-tower-long.fail; } | tee build/ci/check-tower-long.log
test ! -e build/ci/check-tower-long.fail || { cat build/ci/check-tower-long.fail; exit 1; }
