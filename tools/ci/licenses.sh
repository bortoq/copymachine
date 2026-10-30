#!/bin/sh
# License check: one LICENSE at the root; every other license file of the tree is listed in THIRD_PARTY_NOTICES.md with its sha256.
. "$(dirname "$0")/common.sh"

test -f LICENSE || { echo "FAIL: no LICENSE in root"; exit 1; }
grep -qx 'MIT License' LICENSE || { echo "FAIL: LICENSE is not MIT"; exit 1; }
grep -qx 'Copyright (c) 2026 bortoq' LICENSE || { echo "FAIL: LICENSE copyright line"; exit 1; }
test -f THIRD_PARTY_NOTICES.md || { echo "FAIL: no THIRD_PARTY_NOTICES.md"; exit 1; }

found=$(./project-git ls-files | grep -i licen)
other=$(printf '%s\n' "$found" | grep -vx 'LICENSE' || true)
if ./project-git ls-files | grep -E '(^|/)LICENSE$' | grep -vx 'LICENSE' >/dev/null; then
    echo "FAIL: LICENSE outside the root"; exit 1
fi

status=0
for file in $other; do
    sum=$(sha256sum "$file" | cut -d' ' -f1)
    if ! grep -qF "\`$file\`" THIRD_PARTY_NOTICES.md || ! grep -qF "$sum" THIRD_PARTY_NOTICES.md; then
        echo "FAIL: not in THIRD_PARTY_NOTICES.md: $file ($sum)"; status=1
    fi
done
[ "$status" -eq 0 ] || exit 1
echo "PASS licenses: root LICENSE (MIT), third-party: $(printf '%s\n' "$other" | wc -l) file(s) listed"
