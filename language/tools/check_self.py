#!/usr/bin/env python3
"""check-self (14.15): L0 on the emulator compiles the definition of the language (step 4 of
forth/tests/test_kernel.py): stdin is L0, the compiler sources, a zero byte and the sources of
the language; the stream L1 written by L0 must equal L0 byte for byte. The time goes to doc/boot.md."""
import argparse, hashlib, json, sys

import check_kernel
import paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--l0', default=str(paths.L0))
    args = parser.parse_args()
    l0 = open(args.l0, 'rb').read()
    data = l0 + paths.source_bytes(paths.COMPILER_FILES) + b'\0' + paths.source_bytes(paths.KERNEL_FILES)
    l1, seconds = check_kernel.run(data, 4 * 3600)
    if l1 != l0:
        n = next((i for i in range(min(len(l0), len(l1))) if l0[i] != l1[i]), min(len(l0), len(l1)))
        print(f'FAIL: L1 differs from L0: {len(l1)} vs {len(l0)} bytes, first difference at byte {n}', flush=True)
        sys.exit(1)
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    result = dict(bytes=len(l1), sha256=hashlib.sha256(l1).hexdigest(), seconds=round(seconds))
    (paths.BUILD / 'check-self.json').write_text(json.dumps(result, indent=1) + '\n')
    print(f'PASS self: L0 compiled the definition of the language, L1 = {len(l1)} bytes equal to L0 ({seconds:.0f} s)', flush=True)


if __name__ == '__main__':
    main()
