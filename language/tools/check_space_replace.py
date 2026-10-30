#!/usr/bin/env python3
"""check-space-replace (15.4, 3.5.1 on the small value): replacing the word "space" by its definition.

Python only prepares files: the streams of the programs of check-programs (compiled by the definition on the
host pForth), their expected outputs, the empty files of the remote spaces 2 (out) and 3 (exp). The rest is ONE
program of the language, running in the guest on the emulator built by `make space` (the first executor of
the word; it has the long copy):

1. through EXEC (the remote space 0) it builds the emulator NEW from the text of the definition, emulator/src/*.c,
   with the C compiler of the host (`cc`, the flags of the Makefile). The text of the definition already is
   files of the host; copying its 44 KiB through long! would give the same files for more time;
2. for each program k through EXEC it runs NEW on the stream: `NEW -s .. -p 8 < sK > out && cp eK exp`;
3. it reads out and exp by long@ (the remote spaces 2 and 3), compares them word by word and writes P (equal)
   or F (different, or a command failed). Python only prints and requires P for every program.
"""
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

import check_programs
import host
import paths

ROOT = paths.ROOT
SPACE_EMULATOR = paths.OUT / 'space/emulator'
SOURCES = ['runtime.c', 'sys_ctrl.c', 'bitcopy.c', 'backend_bitcopy.c']
FLAGS = '-Wall -Wextra -pedantic -std=c11 -O2'
B = (1 << 30) + (1 << 27)             # the request record, then the command (bit positions of the program half)
C = B + 152
R = B + (1 << 20)                     # the answer
X, Y = B + (1 << 21), B + (1 << 22)   # out and exp, read by long@


def rev(b):
    return int(f'{b:08b}'[::-1], 2)


def text(command):
    """The command as pieces of s" (a line of the stream is short), each written at its offset by put."""
    pieces, at = [], 0
    for piece in re.findall(r'\S+\s*', command):
        if pieces and len(pieces[-1][1]) + len(piece) <= 48:
            pieces[-1][1] += piece
        else:
            pieces.append([at, piece])
        at += len(piece)
    return '\n  '.join(f's" {piece}" {start} put' for start, piece in pieces)


def guest_source(build, workdir, count, words):
    rel = lambda p: os.path.relpath(p, ROOT)         # the guest runs in language
    cc = f'cc {FLAGS} ' + ' '.join(f'{rel(paths.EMULATOR_ROOT / "src" / s)}' for s in SOURCES) + f' -o {rel(build)}'
    d = rel(workdir)
    run = f'{rel(build)} -s {paths.SIZE} -p 8 < {d}/s00 > {d}/out && cp {d}/e00 {d}/exp'
    s, e = run.index('/s00') + 2, run.index('/e00') + 2     # offsets of the digits of the numbers
    return f''': rv ( b -- b' ) dup 1 and 7 lshift over 2 and 5 lshift or over 4 and 3 lshift or over 8 and 1 lshift or
  over 16 and 1 rshift or over 32 and 3 rshift or over 64 and 5 rshift or swap 128 and 7 rshift or ;
: exec ( n -- status ) 5 {B} dup 8 + spacec! dup {B + 56} dup 32 + space!
  8 * 152 + {B} + >r 0 0 {B} r> long! 0 0 {R} {R + 136} long@ {R + 8} {R + 16} spacec@ ;
: same? ( -- f ) -1 {words} 0 do {X} i 32 * + dup 32 + space@ {Y} i 32 * + dup 32 + space@ xor 0= and loop ;
: pat ( ch off -- ) 8 * {C} + swap rv swap dup 8 + spacec! ;
variable po
: put ( addr u off -- ) po ! 0 do dup i + c@ rv po @ i + 8 * {C} + dup 8 + spacec! loop drop ;
: step ( k -- f ) dup 10 / 48 + dup {s} pat {e} pat 10 mod 48 + dup {s + 1} pat {e + 1} pat
  {len(run)} exec if 0 exit then 2 0 {X} {X + 32 * words} long@ 3 0 {Y} {Y + 32 * words} long@ same? ;
: main ( -- ) {text(cc)} {len(cc)} exec if 70 emit 10 emit exit then
  {text(run)}
  {count} 0 do i step if 80 else 70 then emit loop 10 emit ;
'''


def main():
    started = time.monotonic()
    subprocess.run(['make', '-s', '-C', str(ROOT), 'space'], check=True)
    executable, libraries = host.build(), paths.source_bytes(paths.LIBRARY_FILES)
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=paths.BUILD) as name:
        work = Path(name)
        newest = work / 'emulator'
        longest = 0
        cases = paths.programs()
        for k, (source, want) in enumerate(cases.values()):
            stream = check_programs.compile_on_host(executable, libraries, source)
            if want is None:
                want = check_programs.run_host(executable, (source + '\nmain bye\n').encode('latin-1'))
            (work / f's{k:02d}').write_bytes(stream)
            (work / f'e{k:02d}').write_bytes(want)
            longest = max(longest, len(want))
        for n in ('out', 'exp'):
            (work / n).write_bytes(b'')
        words = (longest + 8 + 3) // 4
        program = check_programs.compile_on_host(executable, libraries, guest_source(newest, work, len(cases), words))
        prepared = time.monotonic() - started
        rel = lambda p: os.path.relpath(p, ROOT)
        result = subprocess.run([str(SPACE_EMULATOR), '-s', str(paths.SIZE), '-p', '8', '-r', rel(work / 'out'),
                                 '-r', rel(work / 'exp')], input=program, capture_output=True, cwd=ROOT, timeout=3000, check=False)
        verdict = result.stdout.decode().strip()
        assert result.returncode == 0 and verdict == 'P' * len(cases), (result.returncode, verdict, result.stderr[-300:])
        assert newest.is_file()
        names = list(cases)
        print(f'PASS space replaced: the guest built the emulator from emulator/src/*.c by cc through EXEC and ran the '
              f'{len(cases)} programs of check-programs on it, each output equals the expected one '
              f'(decided in the guest: {verdict}; {names[0]} .. {names[-1]})')
    print(f'ALL space-replace: {len(cases)} programs, {prepared:.0f} s of preparation, '
          f'{time.monotonic() - started:.0f} s in all, guest on {SPACE_EMULATOR}', flush=True)


if __name__ == '__main__':
    main()
