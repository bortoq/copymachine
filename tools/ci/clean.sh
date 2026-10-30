#!/bin/sh
# make clean leaves the tree as committed: no changes, no untracked files.
. "$(dirname "$0")/common.sh"
make clean
git diff --exit-code
test -z "$(git ls-files --others --exclude-standard)"
