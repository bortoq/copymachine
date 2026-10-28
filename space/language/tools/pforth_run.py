#!/usr/bin/env python3
"""pForth on the language (16.1): runs space/language/pforth/pforth.fth with system.fth and input.

The program pforth.fth is compiled by L0 as a program of the user: the emulator gets on stdin
L0, pforth.fth, a zero byte, then the input of the program: the unchanged system.fth of upstream
pForth and the Forth input (files given with -i, or stdin of this tool). The output of pForth is
written to stdout of this tool.

--host-compile (for development only): pforth.fth is compiled by the definition of the language
on the host pForth (as check-programs), the stream is run instead of L0; the result is the same,
the compilation takes seconds instead of minutes.

Usage: pforth_run.py [--host-compile] [-i FILE]... [--seconds N]
"""
import argparse, subprocess, sys, tempfile, time
from pathlib import Path

import paths

PFORTH = paths.ROOT / 'pforth/pforth.fth'
SYSTEM = paths.FORTH / 'third_party/pforth/fth/system.fth'
# The sizes of fc-sizes (main.fth) for the host compilation: pforth.fth has more words than the defaults.
SIZES = '131072 fc-text-size ! 4096 fc-max-consts ! 2048 fc-max-words ! 32768 fc-names-size ! 1024 fc-nbuckets !'


def host_stream(source):
    """The boot stream of the program source compiled by forthc.fth on the host pForth."""
    import host
    lines = [SIZES] + ['fc| ' + line for line in source.split('\n')] + ['fc-go', 'bye']
    data = paths.source_bytes(paths.LIBRARY_FILES) + ('\n'.join(lines) + '\n').encode('latin-1')
    result = subprocess.run([str(host.build())], input=data, capture_output=True, timeout=900)
    if result.returncode or result.stderr or not result.stdout.endswith(b'\n'):
        raise RuntimeError(f'host compilation failed: {result.returncode} {result.stdout[-300:]!r}')
    return result.stdout[:-1]


def prefix(host_compile=False):
    """The bytes before the input of pForth: L0 and the source up to the zero byte, or the stream."""
    source = PFORTH.read_bytes()
    if host_compile:
        return host_stream(source.decode('latin-1'))
    return paths.L0.read_bytes() + source + b'\0'


def run(data, timeout, host_compile=False, head=None, system=True):
    """Output and seconds of the emulator on HEAD (prefix()) + system.fth + DATA."""
    head = prefix(host_compile) if head is None else head
    with tempfile.TemporaryFile() as stdin, tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        stdin.write(head + (SYSTEM.read_bytes() if system else b'') + data)
        stdin.seek(0)
        start = time.monotonic()
        result = subprocess.run([str(paths.EMULATOR), '-s', str(paths.SIZE), '-p', '8'],
                                stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout)
        seconds = time.monotonic() - start
        stdout.seek(0); stderr.seek(0)
        out, err = stdout.read(), stderr.read()
    if result.returncode or err:
        raise RuntimeError(f'emulator: code {result.returncode}, {err[-300:]!r}, output {out[-300:]!r}')
    return out, seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-compile', action='store_true')
    parser.add_argument('-i', '--input', action='append', type=Path, default=[])
    parser.add_argument('--seconds', type=int, default=3600)
    args = parser.parse_args()
    data = b''.join(p.read_bytes() for p in args.input) if args.input else sys.stdin.buffer.read()
    out, seconds = run(data, args.seconds, args.host_compile)
    sys.stdout.buffer.write(out)
    sys.stdout.flush()
    print(f'pforth_run: {seconds:.1f} s', file=sys.stderr)


if __name__ == '__main__':
    main()
