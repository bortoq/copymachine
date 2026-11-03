#!/usr/bin/env python3
"""Isolation of the kernel (14.10, 18.18): what a program given to L0 can do to the space of the kernel.

L0 compiles a program from stdin into the lower half of its own space (the code block 0 and the data block 2
of the four blocks of 2^29 bits) and runs it. The program is built so that it cannot leave its half
(doc/isolation.md): the copies whose position it computes (SPACE! SPACEC! SPACE@ SPACEC@, EXECUTE, the
return) take only the low bits of the position. Every probe is a program given to L0 (as check-kernel does)
that does an attack when its input is 1 and nothing when it is 0, the same text both times, so L0 compiles
it to the same state. After the run the emulator (a copy of emulator/src, built here, that prints the
hashes of the memory at the end) says:

* kernel: the hash of the blocks 1 and 3 (the kernel) is the same after the attack as after the control run:
  the kernel did not change while the program ran (it does not run then);
* code tail, data tail: the upper halves of the blocks 0 and 2, where nothing of the program is, are zero
  (the program wrote neither above its own code nor above its own data).
The output of the attack is compared with what the probe must write (the writes land in the data of the
program: the high bits of the position are the constant of the compiler).

Options: --l0 PATH (default build L0), --only NAME, --report (print the outputs, do not compare).
Exit code 0 if every probe is as expected. The proofs of the word of disjointness are tests/test_disjoint.py.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import boot
import check_kernel
import host
import paths

B = 1 << 29                                    # a block
RSTACK = (1 << 30) + (1 << 21) + (1 << 15)      # the stack of returns of the program (fc-rstk)
FREE = (1 << 30) + (1 << 27)                   # a place of the data of the program that nothing uses
PROBE_SECONDS = 900
LOOP_TICKS = 400_000_000                       # the probes that may not end are cut here

PATCH = r'''
  fflush(stdout);
  {
    uint64_t hk=1469598103934665603ull,hc=1469598103934665603ull,hd=1469598103934665603ull; size_t a;
    for(a=(1u<<26);a<(1u<<27);a++) hk=(hk^space[a])*1099511628211ull;
    for(a=3*(1u<<26);a<(1u<<28);a++) hk=(hk^space[a])*1099511628211ull;
    for(a=(1u<<25);a<(1u<<26);a++) hc=(hc^space[a])*1099511628211ull;
    for(a=(1u<<27)+(1u<<25);a<(1u<<27)+(1u<<26);a++) hd=(hd^space[a])*1099511628211ull;
    fprintf(stderr,"kernel %016llx code-tail %016llx data-tail %016llx\n",(unsigned long long)hk,
            (unsigned long long)hc,(unsigned long long)hd);
  }
  destroy_space();'''


def build_emulator(directory):
    """A copy of the emulator that prints the hashes of the kernel and of the unused halves at the end."""
    src = paths.EMULATOR_ROOT / 'src'
    for f in list(src.glob('*.c')) + list(src.glob('*.h')):
        (directory / f.name).write_bytes(f.read_bytes())
    runtime = directory / 'runtime.c'
    text = runtime.read_text()
    old = '  fflush(stdout); destroy_space();'
    assert old in text
    runtime.write_text(text.replace(old, PATCH))
    out = directory / 'emulator'
    subprocess.run(['cc', '-O2', '-std=c11', *(str(directory / f) for f in
                    ('runtime.c', 'sys_ctrl.c', 'bitcopy.c', 'backend_bitcopy.c')), '-o', str(out)], check=True)
    return out


def kernel_addresses():
    """(entry of fc-.n, address of the record of the constant 48) from the host pForth."""
    stream = boot.boot_input()
    tail = b'fc-go\nbye\n'
    assert stream.endswith(tail)
    query = (b'fc-go\ns" ENTRY " type s" fc-.n" fc-lookup 3 cells + @ . 48 fc-lit-of drop . cr\nbye\n')
    code, out, err = host.run(host.build(), stream[:-len(tail)] + query, 600)
    assert code == 0 and not err, (code, err[-300:])
    entry, constant = out[out.rindex(b'ENTRY ') + 6:].split()[:2]
    return int(entry), int(constant)


def aliases(offset):
    """The positions that name `offset` of the data in every block of the space, in the upper half too."""
    return [b + h + offset for h in (0, 1 << 28) for b in (0, B, 2 * B, 3 * B)]


def probes(entry, constant):
    """name -> (program, output of the control run, output of the attack, what the attack does)."""
    p = {}
    writes = ' '.join(f'{i + 1} {a} space!' for i, a in enumerate(aliases(1 << 27)))
    p['space! on every block'] = (
        f': main key 49 = if {writes} then {FREE} space@ 48 + emit {FREE + 4} spacec@ 48 + emit ;', '00', '80')
    writes = ' '.join(f'{i + 1} {a} spacec!' for i, a in enumerate(aliases(1 << 27)))
    p['spacec! on every block'] = (
        f': main key 49 = if {writes} then {FREE} spacec@ 48 + emit {FREE + 8} spacec@ 48 + emit ;', '00', '80')
    p['space! on the kernel'] = (
        f': main key 49 = if 55 {constant} space! 56 {entry} spacec! 57 {constant + 3 * B} space! then 89 emit ;',
        'Y', 'Y')
    p['space@ of every block'] = (
        f': main 7 {FREE} space! key 49 = if ' + ' '.join(f'{a} space@ 48 + emit' for a in aliases(1 << 27)) +
        ' then 89 emit ;', 'Y', '77777777' + '7' * 0 + 'Y')
    p['spacec@ of every block'] = (
        f': main 7 {FREE} spacec! key 49 = if ' + ' '.join(f'{a} spacec@ 48 + emit' for a in aliases(1 << 27)) +
        ' then 89 emit ;', 'Y', '77777777' + 'Y')
    # @ ! c@ c!: the address is taken modulo the memory of the program, no address leaves it
    far = [(1 << 29) + 8, (1 << 30) + 8, 3 * (1 << 29) + 8, (1 << 31) + 8, 3 * (1 << 30) + 8]
    p['! on addresses above the memory'] = (
        ': main key 49 = if ' + ' '.join(f'{i + 1} {a} !' for i, a in enumerate(far)) + ' then 8 @ 48 + emit ;', '0', '5')
    p['c! on addresses above the memory'] = (
        ': main key 49 = if ' + ' '.join(f'{i + 1} {a + 1} c!' for i, a in enumerate(far)) + ' then 9 c@ 48 + emit ;', '0', '5')
    p['@ c@ on addresses above the memory'] = (
        ': main 9 8 ! key 49 = if ' + ' '.join(f'{a} @ 48 + emit' for a in far)
        + ' ' + ' '.join(f'{a} c@ 48 + emit' for a in far) + ' then 89 emit ;', 'Y', '9999999999Y')
    # the jumps and the returns that name the kernel or the data go only to the code of the program
    p['execute of the kernel'] = (
        f': main 65 emit key 49 = if {entry} execute then 66 emit ;', 'AB', None)
    # the division by 0 halts the program, the kernel stays
    p['division by 0 halts'] = (
        ': main 65 emit key 49 = if 7 0 / drop then 66 emit ;', 'AB', 'A')
    # a jump to a cell of the code of the program that is not an entry may not end (it runs what is there:
    # cell 0 is the processors themselves): the run is cut at LOOP_TICKS, the kernel is still the same
    p['execute of the data'] = (
        'variable v\n: main 65 emit key 49 = if [\'] v execute then 66 emit ;', 'AB', None, LOOP_TICKS)
    p['execute of 0'] = (
        ': main 65 emit key 49 = if 0 execute then 66 emit ;', 'AB', None, LOOP_TICKS)
    p['execute of -1'] = (
        ': main 65 emit key 49 = if -1 execute then 66 emit ;', 'AB', None, LOOP_TICKS)
    # BYE (the halt of FC-REJECT) is a static jump to the halt cell: the rest of the program does not run
    p['bye in the middle'] = (
        ': main 65 emit key 49 = if bye then 66 emit ;', 'AB', 'A')
    p['return to the kernel'] = (
        f': f {entry} >r ;\n: main 65 emit key 49 = if f then 66 emit ;', 'AB', None)
    p['return to the data'] = (
        f': f {FREE} >r ;\n: main 65 emit key 49 = if f then 66 emit ;', 'AB', None)
    p['return forged in the data'] = (
        f': f {entry} {FREE} space! ;\n: main 65 emit key 49 = if f then 66 emit ;', 'AB', None)
    # the return by the number of a point of return (18.22): the program writes the pair of its own return in the stack
    # of returns (the data of the program: MAIN is element 0, F element 1)
    p.update(forged_returns())
    return p


def forged_returns():
    """The program forges the return of F (element 1 of the stack of returns, a pair of two words) and returns.
    The points of return are numbered in the order of the calls: 0 the call of F, 1 the call of P in MAIN, 2 the
    call of MAIN (the end); a number without a point is an empty layer."""
    top = RSTACK + 128
    MID = 23 * 1024                        # a cell in the middle of the word P (before 18.22 the pair of an address went there)

    def probe(lo, hi):
        return (f': p 80 emit ;\n: f {lo} {top} space! {hi} {top + 32} space! ;\n'
                ': main 65 emit key 49 = if f then p 66 emit ;')
    return {
        'return forged to the number of a point (the call of F)': (probe(0, 0), 'APB', 'APB'),
        'return forged to the number of a point (the call of P)': (probe(1, 1), 'APB', 'AB'),
        'return forged to the number of the end': (probe(2, 2), 'APB', 'A'),
        'return forged to a number without a point': (probe(5000, 5000), 'APB', 'A'),
        'return forged to the address of a cell of the code': (probe(MID, MID), 'APB', 'A'),
        # two different numbers: both fields of the link take the first word, the second is not read
        'return forged to a pair of two numbers': (probe(0, 2), 'APB', 'APB'),
        'return forged to the old pair of the address of a cell': (probe(MID, MID + 1024), 'APB', 'A', LOOP_TICKS),
    }


def run_probe(item):
    emulator, l0, name, program, attack, ticks = item
    data = l0 + program.encode('latin-1') + b'\0' + (b'1' if attack else b'0')
    with tempfile.TemporaryFile() as stdin, tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        stdin.write(data)
        stdin.seek(0)
        try:
            options = ['-t', str(ticks)] if ticks else []
            subprocess.run([str(emulator), '-s', str(paths.SIZE), '-p', '8', *options], stdin=stdin, stdout=stdout,
                           stderr=stderr, timeout=PROBE_SECONDS, check=False)
        except subprocess.TimeoutExpired:
            return name, attack, f'<no end in {PROBE_SECONDS} s>', None
        stdout.seek(0)
        stderr.seek(0)
        out = stdout.read().decode('latin-1')
        hashes = dict(zip(*[iter(stderr.read().decode().split())] * 2, strict=True))
    return name, attack, out, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--l0', default=str(paths.L0))
    parser.add_argument('--only', action='append')
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--addresses', nargs=2, type=int, metavar=('ENTRY', 'CONSTANT'),
                        help='the addresses of the kernel of --l0 if its sources are not the current ones')
    args = parser.parse_args()
    l0 = open(args.l0, 'rb').read()
    entry, constant = args.addresses or kernel_addresses()
    print(f'kernel: entry of fc-.n {entry}, record of the constant 48 at {constant}', flush=True)
    table = {k: v for k, v in probes(entry, constant).items() if not args.only or k in args.only}
    with tempfile.TemporaryDirectory() as tmp:
        emulator = build_emulator(Path(tmp))
        items = []
        for name, (program, _, _, *cut) in table.items():
            items.append((emulator, l0, name, program, False, None))
            items.append((emulator, l0, name, program, True, cut[0] if cut else None))
        results = {}
        for name, attack, out, hashes in check_kernel.parallel(run_probe, items):
            results[name, attack] = (out, hashes)
    failed = []
    for name, (_, control, attack, *_) in table.items():
        (c_out, c_hash), (a_out, a_hash) = results[name, False], results[name, True]
        problems = []
        if c_out != control:
            problems.append(f'control output {c_out!r}, expected {control!r}')
        if attack is not None and a_out != attack:
            problems.append(f'attack output {a_out!r}, expected {attack!r}')
        if a_hash is None or c_hash is None:
            problems.append('no end of the run')
        else:
            if a_hash['kernel'] != c_hash['kernel']:
                problems.append('THE KERNEL CHANGED')
            for tail in ('code-tail', 'data-tail'):
                if a_hash[tail] != c_hash[tail]:
                    problems.append(f'{tail} differs from the control run')
        ok = not problems
        print(f'{"PASS" if ok else "FAIL"} {name}: control {c_out!r}, attack {a_out!r}' + ('' if ok else ': ' + '; '.join(problems)),
              flush=True)
        if not ok:
            failed.append(name)
    if failed and not args.report:
        sys.exit(f'isolation: {len(failed)} probes differ: {failed}')
    print('ALL', len(table), 'probes of the isolation of the kernel' + (' (report only)' if args.report else ''))


if __name__ == '__main__':
    main()
