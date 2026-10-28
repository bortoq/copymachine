#!/usr/bin/env python3
"""check-pforth (16.1): pForth on the language (pforth/pforth.fth compiled by L0) loads the unchanged
system.fth and runs every program of space/forth/tests/forthc_programs.py.

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

--host-compile (development): pforth.fth is compiled on the host pForth instead of by L0.
"""
import argparse, json, sys, time

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
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-compile', action='store_true')
    parser.add_argument('--seconds', type=int, default=3300)
    args = parser.parse_args()
    todo = cases()
    data = ''.join(MARK_LINE + '\n' + source for source, _ in todo.values()).encode('latin-1')
    out, seconds = pforth_run.run(data, args.seconds, args.host_compile)
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
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    (paths.BUILD / 'check-pforth.json').write_text(json.dumps(dict(
        seconds=round(seconds), programs=len(todo), failed=failed, known=sorted(KNOWN),
        compiled_by='host' if args.host_compile else 'L0'), indent=1) + '\n')
    print(f'{len(todo) - len(failed)} of {len(todo)} programs as expected, {len(KNOWN)} of them KNOWN,'
          f' one run of {seconds:.0f} s', flush=True)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
