#!/usr/bin/env python3
"""check-kernel (14.0): L0 on the emulator compiles and runs programs inside its own space
(as forth/tests/test_kernel.py --programs-only).

1. Every program of forthc_programs.py, given to L0 on stdin (source up to a zero byte), writes
   what its own boot stream (compiled on the host pForth by the definition) writes.
2. A program reads its input after the zero byte; a compile error prints "error N at WORD".
Option --rebuild (about an hour and a half): L0 runs the compiler, which compiles the definition
from the rest of stdin; the stream must equal L0.
"""
import argparse
import json
import os
import subprocess
import tempfile
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

import check_programs
import host
import paths


def run(data, timeout):
    # Files, not pipes: the streams are megabytes.
    with tempfile.TemporaryFile() as stdin, tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        stdin.write(data); stdin.seek(0)
        start = time.monotonic()
        result = subprocess.run([str(paths.EMULATOR), '-s', str(paths.SIZE), '-p', '8'],
                                stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
        seconds = time.monotonic() - start
        stdout.seek(0); stderr.seek(0); out = stdout.read(); err = stderr.read()
    assert result.returncode == 0 and not err, (result.returncode, err[-300:])
    return out, seconds


def parallel(function, items):
    """function(item) for every item in processes at once (COPYMACHINE_JOBS, default the CPUs of this process),
    the results in the order of items as they are ready. The processes are forks: they see the globals of the
    caller. (Threads do not fit the address-space limit: each takes an arena of 64 MiB.)"""
    jobs = int(os.environ.get('COPYMACHINE_JOBS') or len(os.sched_getaffinity(0)))
    with ProcessPoolExecutor(jobs, mp_context=multiprocessing.get_context('fork')) as pool:
        yield from pool.map(function, items)


def check(case):
    name, source = case
    want, _ = run(check_programs.compile_on_host(EXECUTABLE, LIBRARIES, source), 600)
    got, seconds = run(L0 + source.encode('latin-1') + b'\0', 1800)
    assert got == want, (name, got[-200:], want[-200:])
    return name, len(got), seconds


def main():
    global L0, EXECUTABLE, LIBRARIES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--only', action='append')
    parser.add_argument('--l0', default=str(paths.L0))
    args = parser.parse_args()
    l0 = L0 = open(args.l0, 'rb').read()
    EXECUTABLE = host.build()
    LIBRARIES = paths.source_bytes(paths.LIBRARY_FILES)
    results = dict(stream_bytes=len(l0), programs=[])
    cases = [(name, source) for name, (source, _) in paths.programs().items() if not args.only or name in args.only]

    for name, output_bytes, seconds in parallel(check, cases):
        results['programs'].append(dict(name=name, output_bytes=output_bytes, seconds=round(seconds, 1)))
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
