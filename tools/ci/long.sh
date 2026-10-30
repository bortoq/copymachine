#!/bin/sh
# One long goal of the language: tools/ci/long.sh check-kernel|check-self|check-isolation|check-proof|check-replace|check-user-programs.
# The log goes to language/build/ci/<goal>.log; for check-self also the sha256 of L0 (L1 is equal to it, the log has the sha256 of L1).
. "$(dirname "$0")/common.sh"
GOAL=${1:?goal}
case "$GOAL" in
check-kernel|check-self|check-isolation|check-proof|check-replace|check-user-programs) ;;
*) echo "unknown goal: $GOAL" >&2; exit 2 ;;
esac
make -C language -j1 boot
mkdir -p language/build/ci
rm -f "language/build/ci/$GOAL.fail"
(cd language/build && sha256sum L0.boot > ci/L0.sha256)
{ make -C language -j1 "$GOAL" 2>&1 || echo "make exit $?" >"language/build/ci/$GOAL.fail"; } | tee "language/build/ci/$GOAL.log"
test ! -e "language/build/ci/$GOAL.fail" || { cat "language/build/ci/$GOAL.fail"; exit 1; }
