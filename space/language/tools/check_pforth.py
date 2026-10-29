#!/usr/bin/env python3
"""check-pforth (16.1, 16.2): pForth on the language (pforth/pforth.fth compiled by L0) loads the unchanged
system.fth, runs every program of space/forth/tests/forthc_programs.py and works with files.

One run of the emulator: L0, pforth.fth, a zero byte, system.fth, then for every program a line
that emits a marker, the source and "main bye". BYE ends a session of pForth, the next one starts
from the dictionary saved by SAVE-FORTH at the end of system.fth (as pforth32 from its prepared
dictionary). The output is cut at the markers; the last newline of a part is the one of BYE.

Expected output: of PROGRAMS, what the same source writes on the host pforth32 (as check-programs);
of EXPECTED, the output given with the program, except KNOWN below, where the given output is that
of the direct compiler and not of pForth (the docstring of forthc_programs.py: pForth's MOD and /MOD
are unsigned for negative operands): their reference is the host pforth32 too, or, for faults
(the host has no address checks and stops), the output given with the one byte that pForth's MOD
(UM/MOD by shifts, no division) cannot fault on. Each such program is printed as KNOWN.

Files (16.2): the run has a volume (pforth_run.py): the nine libraries space/copycode/forth/*.fth and files
of the cases below. Library sessions (pforth/sessions.json: the libraries a session needs, then lines with
calls, an error caught by CATCH, depth): the session of pForth on the language INCLUDEs the libraries; the
reference is the host pforth32 on the same lines after the texts of the libraries (the host has no files,
and stops at the first error, so the errors of the sessions are caught). Own cases of the file words
(OPEN-FILE, READ-FILE, READ-LINE, WRITE-FILE, REPOSITION-FILE, RESIZE-FILE, DELETE-FILE, nested INCLUDE,
an error in an included file, a missing file) have the output written below; the files as the run left
them are compared too.

--host-compile (development): pforth.fth is compiled on the host pForth instead of by L0.
--only NAME (development): only these cases; the programs of 16.1 are named as in forthc_programs.py.
"""
import argparse, json, sys, time
from pathlib import Path

import check_programs
import host
import paths
import pforth_run

MARK = b'\0\1PF\2\0'
MARK_LINE = ' '.join(f'{b} emit' for b in MARK)
KNOWN = {
    'mod-signs': 'MOD and /MOD of pForth are unsigned for negative operands; reference: host pforth32',
    'divmod-random': 'MOD and /MOD of pForth are unsigned for negative operands; reference: host pforth32',
    'faults': '7 0 MOD is UM/MOD in pForth, no division, no fault -10: the 7th byte is 0, not 10',
}
# Own cases: QUIT reports an error and goes on with the next line; numbers in bases; a fault not caught by CATCH ends the session, the next session starts from the image.
OWN = {
    'quit-continues': ('frob 65 emit\n66 emit', b'frob  ? - unrecognized word!\nStack<10> \nTHROW code = -13 \n'
                       b'Undefined word!\nB'),
    'number-base': ('hex FF . 10 . decimal -12 . $7F . %101 . \'A\' .', b'FF 10 -12 127 5 65 '),
    'fault-restart': (': main 65 emit 1 @ 66 emit ;\nmain 67 emit', b'A'),
}


LIBRARIES = sorted((paths.COPYCODE_ROOT / 'forth').glob('*.fth'))
SESSIONS = json.loads((paths.ROOT / 'pforth/sessions.json').read_text())
QUIET = 'trace-include off\n'
# Files of the own cases: name -> content before the run; FILES_AFTER: content after it (the others stay).
SCRATCH = {
    'r.txt': b'line one\r\nline two\n\nlast',
    'w.txt': b'old content here',
    'w2.txt': b'xxxxxxxx',
    'gone.txt': b'to be deleted',
    'ren.txt': b'abcdefgh',
    'inc1.fth': b': one 1 . ; one include inc2.fth one\n',
    'inc2.fth': b': two 2 . ; two\n',
    'bad.fth': b'65 emit\nnosuchword 66 emit\n67 emit\n',
}
FILES_AFTER = {'w.txt': b'NEW content here' + b'\0' * 4 + b'end', 'w2.txt': b'hello', 'ren.txt': b'abc\0\0\0'}
FILES_RENAMED = {'ren.txt': 'new.txt'}
# Own file cases: (source, output). A name 'o', 'n' hold C strings for (RENAME-FILE).
FILE_CASES = {
    'file-read': (QUIET + 'create lb 40 allot\n'
                  's" r.txt" r/o open-file . constant rf\n: rl lb 40 rf read-line . . . ;\nrl lb 4 type rl rl rl rl\n'
                  'rf file-size . . . rf file-position . . .\n'
                  '10 0 rf reposition-file . lb 6 rf read-file . . lb 6 type\n'
                  '5 0 rf reposition-file . lb 40 rf read-file . . rf close-file .\n'
                  's" nofile" r/o open-file . drop\nbye\n',
                  b'0 0 -1 8 line0 -1 8 0 -1 0 0 -1 4 0 0 0 0 0 24 0 0 24 0 0 6 line t0 0 19 0 -1 '),
    'file-write': (QUIET + 'create lb 40 allot\n'
                   's" w.txt" r/w open-file . constant wf s" NEW" wf write-file . wf file-position . . .\n'
                   '20 0 wf reposition-file . s" end" wf write-file . wf file-size . . . wf close-file .\n'
                   's" w2.txt" w/o open-file . constant xf s" ab" xf write-file . xf file-size . . . xf close-file .\n'
                   's" w2.txt" r/w create-file . constant yf s" hello" yf write-file .\n'
                   '0 0 yf reposition-file . lb 10 yf read-file . . lb 5 type yf close-file .\n'
                   's" w2.txt" r/o open-file . constant zf lb 40 zf read-file . . zf close-file .\nbye\n',
                   b'0 0 0 0 3 0 0 0 0 23 0 0 0 0 0 2 0 0 0 0 0 5 hello0 0 0 5 0 '),
    'file-names': (QUIET + 'create o 16 allot create n 16 allot\n'
                   's" ren.txt" o swap cmove 0 o 7 + c! s" new.txt" n swap cmove 0 n 7 + c!\n'
                   's" gone.txt" delete-file . s" gone.txt" delete-file . s" gone.txt" r/o open-file . drop\n'
                   'o n (rename-file) . s" ren.txt" r/o open-file . drop s" new.txt" r/w open-file . constant sz\n'
                   '3 0 sz (resize-file) . sz file-size . . . 6 0 sz (resize-file) . sz file-size . . .\n'
                   '0 0 sz reposition-file . o 8 sz read-file . . o 3 type sz close-file .\nbye\n',
                   b'0 -1 -1 0 -1 0 0 0 0 3 0 0 0 6 0 0 6 abc0 '),
    'include-files': (QUIET + 'include inc1.fth\nsource-id . 3 emit\nbye\n', b'1 2 1 0 \x03'),
    'include-error': (QUIET + 'include bad.fth\n68 emit\nbye\n',
                      b'Anosuchword  ? - unrecognized word!\nINCLUDE error on line #2 , level = 1 \nnosuchword 66 emit\n'
                      b'^^^^^^^^^^\nStack<10> \nTHROW code = -13 \nUndefined word!\nD'),
    'include-missing': (QUIET + ': t s" nofile.fth" included ; t\n69 emit\nbye\n',
                        b'Could not find file nofile.fth\nStack<10> \nTHROW code = -1 \nABORT\nE'),
}


def library_cases(executable):
    texts = {path.name: path.read_bytes() for path in LIBRARIES}
    result = {}
    for name, session in SESSIONS.items():
        lines = ''.join(line + '\n' for line in session['lines']).encode('latin-1')
        ours = (QUIET + ''.join(f'include {lib}\n' for lib in session['libs'])).encode('latin-1') + lines
        theirs = b''.join(texts[lib] for lib in session['libs']) + lines
        result[f'library-{name}'] = (ours, check_programs.run_host(executable, theirs))
    return result


def cases():
    executable = host.build()
    result = {}
    for name, (source, want) in paths.programs().items():
        if want is None or name in ('mod-signs', 'divmod-random'):
            want = check_programs.run_host(executable, (source + '\nmain bye\n').encode('latin-1'))
        elif name == 'faults':
            want = want[:6] + b'\0' + want[7:]
        result[name] = (source + '\nmain bye\n', want)
    for name, (source, want) in OWN.items():
        result[name] = (source + '\nbye\n', want)
    result.update(library_cases(executable))
    result.update({name: (source.encode('latin-1'), want) for name, (source, want) in FILE_CASES.items()})
    return {name: (source if isinstance(source, bytes) else source.encode('latin-1'), want)
            for name, (source, want) in result.items()}


def volume():
    files = {path.name: path.read_bytes() for path in LIBRARIES}
    assert not set(files) & set(SCRATCH)
    files.update(SCRATCH)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-compile', action='store_true')
    parser.add_argument('--seconds', type=int, default=3300)
    parser.add_argument('--only', action='append', help='names of cases')
    args = parser.parse_args()
    todo = {name: case for name, case in cases().items() if not args.only or name in args.only}
    data = b''.join(MARK_LINE.encode() + b'\n' + source for source, _ in todo.values())
    files = volume()
    out, seconds = pforth_run.run(data, args.seconds, args.host_compile, files=files)
    parts = out.split(MARK)
    assert len(parts) == len(todo) + 1, (len(parts), out[-300:])
    print(f'system.fth: {len(parts[0])} bytes of messages (the files it includes are absent)', flush=True)
    failed = []
    for (name, (_, want)), got in zip(todo.items(), parts[1:]):
        got = got[:-1] if got.endswith(b'\n') else got
        ok = got == want
        note = f' KNOWN: {KNOWN[name]}' if name in KNOWN else ''
        print(f'{"PASS" if ok else "FAIL"} pforth {name}: {len(got)} bytes{note}', flush=True)
        if not ok:
            print(f'  got  {got[-200:]!r}\n  want {want[-200:]!r}', flush=True)
            failed.append(name)
    if not args.only:
        want = {name: FILES_AFTER.get(name, content) for name, content in volume().items()}
        for old, new in FILES_RENAMED.items():
            want[new] = want.pop(old)
        want = {name: content for name, content in want.items() if name != 'gone.txt'}
        ok = files == want
        print(f'{"PASS" if ok else "FAIL"} pforth files after the run: {len(files)} files')
        if not ok:
            print('  got ', {n: c for n, c in files.items() if want.get(n) != c})
            print('  want', {n: c for n, c in want.items() if files.get(n) != c})
            failed.append('files')
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    (paths.BUILD / 'check-pforth.json').write_text(json.dumps(dict(
        seconds=round(seconds), programs=len(todo), failed=failed, known=sorted(KNOWN),
        compiled_by='host' if args.host_compile else 'L0'), indent=1) + '\n')
    print(f'{len(todo) - len(failed)} of {len(todo)} programs as expected, {len(KNOWN)} of them KNOWN,'
          f' one run of {seconds:.0f} s', flush=True)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
