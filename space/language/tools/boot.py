#!/usr/bin/env python3
"""Boot (14.1): the host 32-bit pForth executes the definition of the language and writes L0.

The definition is the text of src/ in the order of compilation (prelude, backend, compute,
forthc, main, kernel). The host pForth loads the compiler (backend, compute, forthc) natively,
takes the sizes of main.fth (fc-sizes), reads the whole definition with FC| line by line and
compiles it with FC-GO: the stream on its output is L0, the core of the language as index
code. The first executor of the definition is the host; later executors are the language itself.

Usage: boot.py [-o L0.boot]
"""
import argparse, hashlib, json, subprocess, sys, time

import host
import paths

# The sizes of fc-sizes in main.fth, set before the definition is read (the host keeps the
# smaller defaults of the compiler, which do not suffice for the whole definition).
SIZES = '131072 fc-text-size ! 4096 fc-max-consts ! 2048 fc-max-words ! 32768 fc-names-size ! 1024 fc-nbuckets !'


def boot_input():
    lines = [SIZES] + ['fc| ' + line for line in paths.text(paths.KERNEL_FILES).split('\n')] + ['fc-go', 'bye']
    return paths.source_bytes(paths.LIBRARY_FILES) + ('\n'.join(lines) + '\n').encode('latin-1')


def boot(timeout=3000):
    executable = host.build()
    start = time.monotonic()
    result = subprocess.run([str(executable)], input=boot_input(), capture_output=True, timeout=timeout)
    seconds = time.monotonic() - start
    if result.returncode or result.stderr or not result.stdout.endswith(b'\n'):
        sys.exit(f'boot failed: code {result.returncode}, {result.stdout[-300:]!r}, {result.stderr[-300:]!r}')
    return result.stdout[:-1], seconds        # the last newline is the one of the host's output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--output', type=lambda s: __import__('pathlib').Path(s), default=paths.L0)
    args = parser.parse_args()
    stream, seconds = boot()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + '.tmp')
    temporary.write_bytes(stream)
    temporary.replace(args.output)
    record = dict(bytes=len(stream), sha256=hashlib.sha256(stream).hexdigest(), seconds=round(seconds, 1),
                  executor='host 32-bit pForth', pool_bytes=host.POOL_BYTES)
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    (paths.BUILD / 'boot.json').write_text(json.dumps(record, indent=1) + '\n')
    print(f'boot: L0 {len(stream)} bytes in {seconds:.1f} s on the host pForth -> {args.output}', flush=True)


if __name__ == '__main__':
    main()
