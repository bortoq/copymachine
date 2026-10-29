#!/usr/bin/env python3
"""pForth on the language (16.1): runs space/language/pforth/pforth.fth with system.fth and input.

The program pforth.fth is compiled by L0 as a program of the user: the emulator gets on stdin
L0, pforth.fth, a zero byte, then the input of the program: the unchanged system.fth of upstream
pForth and the Forth input (files given with -i, or stdin of this tool). The output of pForth is
written to stdout of this tool.

Files (16.2): FILES = {name: bytes} is the volume. The emulator is the one built from the definition of
the word "space" (it has the long copy, `make space`; EMULATOR=path chooses another one); the space 2
(-r) is the directory of the volume, the spaces 3.. (-r) are the files, as pforth.fth describes. After
the run FILES holds the files as the program left them (by the sizes of the directory).

--host-compile (for development only): pforth.fth is compiled by the definition of the language
on the host pForth (as check-programs), the stream is run instead of L0; the result is the same,
the compilation takes seconds instead of minutes.

Usage: pforth_run.py [--host-compile] [-i FILE]... [--seconds N]
"""
import argparse, os, struct, subprocess, sys, tempfile, time
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


SPACE_EMULATOR = paths.OUT / 'space/emulator'
EXECUTABLE = paths.EMULATOR if os.environ.get('EMULATOR') else SPACE_EMULATOR


def directory(files):
    """The directory of the volume (space 2): a record of 64 bytes per file, the file in the space 3 + k."""
    assert len(files) <= 32
    data = b''
    for k, (name, content) in enumerate(files.items()):
        raw = name.encode('latin-1')
        assert 0 < len(raw) <= 55
        data += struct.pack('<IIB55s', 3 + k, len(content), len(raw), raw)
    return data


def read_volume(folder, files):
    """Replace FILES by the files of FOLDER as the program left them (the names of the directory)."""
    table = (folder / 'dir').read_bytes()
    files.clear()
    for at in range(0, len(table), 64):
        space, size, length, raw = struct.unpack('<IIB55s', table[at:at + 64])
        if space:
            content = (folder / f'f{space}').read_bytes()
            files[raw[:length].decode('latin-1')] = content[:size].ljust(size, b'\0')
    return files


def run(data, timeout, host_compile=False, head=None, system=True, files=None):
    """Output and seconds of the emulator on HEAD (prefix()) + system.fth + DATA, with the volume FILES."""
    head = prefix(host_compile) if head is None else head
    with tempfile.TemporaryDirectory(dir=paths.BUILD if paths.BUILD.is_dir() else None) as name, \
            tempfile.TemporaryFile() as stdin, tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        folder = Path(name)
        options = []
        if files is not None:
            (folder / 'dir').write_bytes(directory(files))
            options = ['-r', str(folder / 'dir')]
            for k, content in enumerate(files.values()):
                (folder / f'f{3 + k}').write_bytes(content)
                options += ['-r', str(folder / f'f{3 + k}')]
        stdin.write(head + (SYSTEM.read_bytes() if system else b'') + data)
        stdin.seek(0)
        start = time.monotonic()
        result = subprocess.run([str(EXECUTABLE), '-s', str(paths.SIZE), '-p', '8', *options],
                                stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout)
        seconds = time.monotonic() - start
        stdout.seek(0); stderr.seek(0)
        out, err = stdout.read(), stderr.read()
        if files is not None:
            read_volume(folder, files)
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
