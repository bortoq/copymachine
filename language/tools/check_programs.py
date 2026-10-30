#!/usr/bin/env python3
"""check-programs (14.0): every program of language/tests/reference/forthc_programs.py is compiled by
the definition of the language on the host pForth (the compiler forthc.fth fed with FC| lines),
the stream runs on checked-emulator and the output equals the expected one.

The expected output of PROGRAMS is what the same source writes on the host pForth (as in
test_forthc.py pForth is the reference); of EXPECTED, the output given with the program.
STREAMS=equal (or --streams-equal) also requires the stream to equal, byte for byte, the stream
of language/tests/reference/model.py (the model is only the reference of the test).
"""
import argparse
import json
import os
import subprocess
import sys
import time

import host
import paths


def run_host(executable, data, timeout=900):
    result = subprocess.run([str(executable)], input=data, capture_output=True, timeout=timeout)
    assert result.returncode == 0 and not result.stderr, (result.returncode, result.stdout[-300:], result.stderr[-300:])
    return result.stdout[:-1] if result.stdout.endswith(b'\n') else result.stdout


def compile_on_host(executable, libraries, source):
    """The boot stream of a program compiled by forthc.fth on the host pForth."""
    task = ['fc| ' + line for line in source.split('\n')] + ['fc-go', 'bye']
    return run_host(executable, libraries + ('\n'.join(task) + '\n').encode('latin-1'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--streams-equal', action='store_true', default=os.environ.get('STREAMS') == 'equal')
    parser.add_argument('--only', action='append', help='names of programs')
    args = parser.parse_args()
    executable = host.build()
    libraries = paths.source_bytes(paths.LIBRARY_FILES)
    model = None
    if args.streams_equal:
        sys.path[:0] = [str(paths.REFERENCE)]
        import model
    results = []
    for name, (source, want) in paths.programs().items():
        if args.only and name not in args.only:
            continue
        start = time.monotonic()
        stream = compile_on_host(executable, libraries, source)
        compiled = time.monotonic() - start
        if args.streams_equal:
            assert stream == model.compile_forth(source), (name, 'the stream differs from the model')
        if want is None:
            want = run_host(executable, (source + '\nmain bye\n').encode('latin-1'))
        run = subprocess.run([str(paths.EXECUTOR), '-s', str(paths.SIZE), '-p', '8'], input=stream,
                             capture_output=True, timeout=600)
        assert run.returncode == 0, (name, run.returncode, run.stderr[-300:])
        assert run.stdout == want, (name, run.stdout[-200:], want[-200:])
        results.append(dict(name=name, stream_bytes=len(stream), output_bytes=len(want), host_seconds=round(compiled, 2)))
        print(f'PASS program {name}: {len(stream)} stream bytes{" equal to the model" if args.streams_equal else ""},'
              f' output {len(want)} bytes as expected ({compiled:.1f} s on the host)', flush=True)
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    (paths.BUILD / 'check-programs.json').write_text(json.dumps(results, indent=1) + '\n')
    print('ALL', len(results), 'programs compiled by the definition on the host pForth, run on ' + paths.EXECUTOR.name, flush=True)


if __name__ == '__main__':
    main()
