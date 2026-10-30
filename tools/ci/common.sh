# Sourced by the other scripts of tools/ci. Run them from anywhere; they work in the repository root.
set -eu
cd "$(dirname "$0")/../.."
# The runners of GitHub need a larger address-space limit than the local default (language/Makefile).
export MEMORY_MIB="${MEMORY_MIB:-3072}" BIG_MEMORY_MIB="${BIG_MEMORY_MIB:-3072}"
