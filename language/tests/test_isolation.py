#!/usr/bin/env python3
"""Isolation of the kernel (14.10): what a program given to L0 can do to the upper half.

L0 compiles a program from stdin into the lower half of its own space and runs it. The program
must not write, read or execute the kernel (the upper half) other than by calling a word. Every
probe is a program given to L0 (as check-kernel does); the table PROBES has what the probe writes
after the fix and what it wrote before it (14.10, doc/isolation.md).

The addresses of the kernel are taken from the definition on the host pForth (the same text that
boot.py compiles): the entry of the word kn-.n (it writes a number in decimal) and the record of
the constant 48 ([char] 0), which kn-.n adds to a digit.

Options: --l0 PATH (default build L0), --only NAME, --report (print the outputs, do not compare).
Exit code 0 if every output is the expected one.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import boot
import check_kernel
import host
import paths

PROGRAM_HALF = (0, 1 << 29), (1 << 30, (1 << 30) + (1 << 29))
FREE = (1 << 30) + (1 << 28)            # a place in the data of the program half that nothing uses
PROBE_SECONDS = 600                     # a probe that does not end (a hole may loop) is a failure
SHOW = ': show 0 swap - 48 + emit ;\n'    # the code of a THROW as a digit: -9 is 9, 0 is 0


def kernel_addresses():
    """(entry of kn-.n, address of the record of the constant 48) from the host pForth."""
    stream = boot.boot_input()
    tail = b'fc-go\nbye\n'
    assert stream.endswith(tail)
    query = (b'fc-go\ns" ENTRY " type s" kn-.n" fc-lookup 3 cells + @ . 48 fc-lit-of drop . cr\nbye\n')
    code, out, err = host.run(host.build(), stream[:-len(tail)] + query, 600)
    assert code == 0 and not err, (code, err[-300:])
    entry, constant = out[out.rindex(b'ENTRY ') + 6:].split()[:2]
    return int(entry), int(constant)


def probes(entry, constant):
    """name -> (program, output after the fix, output before the fix: what a hole did, or None)."""
    lo, hi = constant, constant + 32
    d = FREE
    p = {}
    # --- the holes of 14.10 (1): write, read, execute the kernel -----------------------------------
    # Executing the entry of the kernel word kn-.n runs it on the stack of the kernel (it writes the
    # number 0 in decimal) and never returns to the program. It adds the constant 48 to the digit:
    # the write of 49 over the constant makes it write 1.
    w = f': w 49 {lo} {hi} space! ;\n'
    p['write-kernel'] = (SHOW + w + ": main ['] w catch show 65 emit ;", '9A', '0A')
    p['writec-kernel'] = (SHOW + f': w 49 {lo} {lo + 8} spacec! ;\n' + ": main ['] w catch show 65 emit ;",
                          '9A', '0A')
    p['write-effect'] = (SHOW + f': w 49 {lo} {hi} space! {entry} execute ;\n'
                         + ": main ['] w catch show 66 emit ;", '9B', '1')
    p['read-kernel'] = (SHOW + f': r {lo} {hi} space@ drop ;\n: main [\'] r catch show ;', '9',
                        'error -13 at space@\n')
    p['readc-kernel'] = (SHOW + f': r {lo} {lo + 8} spacec@ drop ;\n: main [\'] r catch show ;', '9',
                         'error -13 at spacec@\n')
    p['execute-kernel'] = (SHOW + f': k {entry} execute ;\n: main 65 emit [\'] k catch show 66 emit ;', 'A9B', 'A0')
    p['catch-kernel'] = (SHOW + f': c {entry} catch show ;\n: main 65 emit [\'] c catch show 66 emit ;', 'A9B', 'A0')
    # --- what must keep working -----------------------------------------------------------------------
    p['program-half'] = (
        f': main 1234567 {d} {d + 32} space! {d} {d + 32} space@ 1234567 = if 89 emit else 78 emit then\n'
        f'  200 {d} {d + 8} spacec! {d} {d + 8} spacec@ 200 = if 89 emit else 78 emit then\n'
        f'  {d} {d + 32} space@ 1234567 = if 89 emit else 78 emit then\n'
        f'  1 {d + 8} {d + 16} spacec! {d + 8} {d + 16} spacec@ 1 = if 89 emit else 78 emit then ;',
        'YYNY', None)
    return p


def range_probes():
    """space@ spacec@ space! spacec! on [lo, hi) near the edges of the half of the program: name -> probe.
    A case is (lo, hi, THROW code, may be written); hi None: lo + the width of the word (32 or 8)."""
    a, b, c, d = 1 << 29, 1 << 30, (1 << 30) + (1 << 29), FREE
    probes = {}
    for op, width, store in [('space@', 32, False), ('spacec@', 8, False), ('space!', 32, True), ('spacec!', 8, True)]:
        w = width
        cases = [(0, None, 0, False), (2048, None, 0, False), (a - w, None, 0, False), (a - w // 2, a + w // 2, 9, True),
                 (a, None, 9, True), (a + w, None, 9, True), (b - w // 2, b + w // 2, 9, True), (b, None, 0, False),
                 (d, None, 0, True), (d + 1, None, 0, True), (c - w, None, 0, True), (c - w // 2, c + w // 2, 9, True),
                 (c, None, 9, True), ((1 << 31) - w, 1 << 31, 9, True), (1 << 31, None, 9, True),
                 (b + w, b, 9, True), (b + w, b + w, 9, True), (0, 0, 9, True), (b, a, 9, True),
                 (3 << 29, None, 9, True), (-w & 0xFFFFFFFF, 0, 9, True), (0, 0xFFFFFFFF, 9, True),
                 (d, d + 1, 9, True), (d, d + 2 * w, 9, True), (d, d + w // 2 if w == 32 else d + 32, 9, True)]
        words, tests, want = [], [], ''
        for i, (lo, hi, code, writable) in enumerate(cases):
            hi = lo + w if hi is None else hi
            if store and not writable:
                continue
            args = f'0 {lo} {hi} {op}' if store else f'{lo} {hi} {op} drop'
            words.append(f': t{i} {args} ;')
            tests.append(f"['] t{i} catch show")
            want += str(code)
        probes['ranges ' + op] = (SHOW + '\n'.join(words) + '\n: main ' + ' '.join(tests) + ' ;', want, None)
    return probes


def execute_probe():
    """execute and catch take only the entry of a word of the program."""
    program = (SHOW + ': a 65 emit ;\n: b 66 emit ;\nvariable v\n'
               ': n1 [\'] v execute ;\n: n3 [\'] a 1+ execute ;\n: n4 0 execute ;\n: n5 -1 execute ;\n'
               f': n6 {FREE} execute ;\n: n7 {1 << 29} execute ;\n: n8 [\'] v catch drop ;\n'
               ': main [\'] a execute [\'] b execute [\'] n1 catch show [\'] n3 catch show [\'] n4 catch show'
               ' [\'] n5 catch show [\'] n6 catch show [\'] n7 catch show [\'] n8 catch show'
               ' [\'] a catch show [\'] b catch show ;')
    # n3: the low bits of xt below the bits that execute uses are not read (a + 1 is the entry of a)
    return (program, 'AB' + '9' + 'A0' + '9' * 5 + 'A0B0', None)


def probe(case):
    source = case[1][0]
    try:
        out, seconds = check_kernel.run(L0 + source.encode('latin-1') + b'\0', PROBE_SECONDS)
        return out.decode('latin-1'), seconds
    except subprocess.TimeoutExpired:
        return f'<no end in {PROBE_SECONDS} s>', PROBE_SECONDS


def main():
    global L0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--l0', default=str(paths.L0))
    parser.add_argument('--only', action='append')
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--addresses', nargs=2, type=int, metavar=('ENTRY', 'CONSTANT'),
                        help='the addresses of the kernel of --l0 if its sources are not the current ones')
    args = parser.parse_args()
    L0 = open(args.l0, 'rb').read()
    entry, constant = args.addresses or kernel_addresses()
    print(f'kernel: entry of kn-.n {entry}, record of the constant 48 at {constant}', flush=True)
    table = probes(entry, constant)
    table.update(range_probes())
    table['execute-program'] = execute_probe()
    failed = []
    cases = [(name, case) for name, case in table.items() if not args.only or name in args.only]

    for (name, (_, after, before)), (got, seconds) in zip(cases, check_kernel.parallel(probe, cases), strict=True):
        ok = got == after
        print(f'{"PASS" if ok else "FAIL"} {name}: output {got!r}' + ('' if ok else f', expected {after!r}')
              + (f' (before the fix: {before!r})' if before is not None else '') + f' ({seconds:.1f} s)', flush=True)
        if not ok:
            failed.append(name)
    if failed and not args.report:
        sys.exit(f'isolation: {len(failed)} probes differ: {failed}')
    print('ALL', len(table), 'probes of the isolation of the kernel' + (' (report only)' if args.report else ''))


if __name__ == '__main__':
    main()
