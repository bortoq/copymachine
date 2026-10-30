#!/bin/sh
# make lint and make check-fast: the same as the GitHub job "fast".
. "$(dirname "$0")/common.sh"
make lint
make check-fast
