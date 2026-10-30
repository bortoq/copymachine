#!/usr/bin/env python3
"""check-kernel (14.0): L0 on the emulator compiles and runs programs inside its own space
(as forth/tests/test_kernel.py --programs-only).

1. Every program of forthc_programs.py, given to L0 on stdin (source up to a zero byte), writes
   what its own boot stream (compiled on the host pForth by the definition) writes.
2. A program reads its input after the zero byte; a compile error prints "error N at WORD".
Option --rebuild (about an hour and a half): L0 runs the compiler, which compiles the definition
from the rest of stdin; the stream must equal L0.
"""
import argparse, json, subprocess, sys, tempfile, time

import check_programs
import host
import paths


def run(data, timeout):
    # Files, not pipes: the streams are megabytes.
    with tempfile.TemporaryFile() as stdin, tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        stdin.write(data); stdin.seek(0)
        start = time.monotonic()
        result = subprocess.run([str(paths.EMULATOR), '-s', str(paths.SIZE), '-p', '8'],
                                stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout)
        seconds = time.monotonic() - start
        stdout.seek(0); stderr.seek(0); out = stdout.read(); err = stderr.read()
    assert result.returncode == 0 and not err, (result.returncode, err[-300:])
    return out, seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--only', action='append')
    parser.add_argument('--l0', default=str(paths.L0))
    args = parser.parse_args()
    l0 = open(args.l0, 'rb').read()
    executable = host.build()
    libraries = paths.source_bytes(paths.LIBRARY_FILES)
    results = dict(stream_bytes=len(l0), programs=[])
    for name, (source, _) in paths.programs().items():
        if args.only and name not in args.only:
            continue
        want, _ = run(check_programs.compile_on_host(executable, libraries, source), 600)
        got, seconds = run(l0 + source.encode('latin-1') + b'\0', 1800)
        assert got == want, (name, got[-200:], want[-200:])
        results['programs'].append(dict(name=name, output_bytes=len(got), seconds=round(seconds, 1)))
        print(f'PASS kernel {name}: compiled and run in the space, output as its stream ({seconds:.1f} s)', flush=True)
    echo = ': main begin key dup while 1+ emit repeat drop ;\n'
    got, _ = run(l0 + echo.encode() + b'\0' + b'HAL', 600)
    assert got == b'IBM', got
    print('PASS kernel: the program reads the input after its source', flush=True)
    got, _ = run(l0 + b': main 1 frobnicate ;\n\0', 600)
    assert got == b'error -13 at frobnicate\n', got
    print('PASS kernel: a compile error is reported', flush=True)
    if args.rebuild:
        l1, seconds = run(l0 + paths.source_bytes(paths.COMPILER_FILES) + b'\0' + paths.source_bytes(paths.KERNEL_FILES), 6 * 3600)
        assert l1 == l0, ('the rebuilt kernel differs', len(l1), len(l0))
        results['rebuild_seconds'] = round(seconds)
        print(f'PASS kernel rebuilds itself: {len(l1)} bytes equal to L0 ({seconds:.0f} s)', flush=True)
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    (paths.BUILD / 'check-kernel.json').write_text(json.dumps(results, indent=1) + '\n')
    print('ALL', len(results['programs']), 'programs compiled and run inside the space by L0', flush=True)


if __name__ == '__main__':
    main()
