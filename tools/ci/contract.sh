#!/bin/sh
# The contract of the emulator (the definition of the space) is changed only by the author: its sha256 is pinned in
# emulator/doc/emulator-contract.sha256; an agent must not change either file (ROADMAP.md, rule of the contract).
set -e
cd "$(dirname "$0")/../.."
want=$(cat emulator/doc/emulator-contract.sha256)
have=$(sha256sum emulator/doc/emulator-contract.md | cut -d' ' -f1)
if [ "$want" != "$have" ]; then
  echo "contract: emulator/doc/emulator-contract.md changed (sha256 $have, pinned $want) — only the author changes the contract" >&2
  exit 1
fi
echo "contract: pinned sha256 ok"
