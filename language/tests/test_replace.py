"""Replacement of a definition and synonyms (14.13, language/doc/replace.md).

REPLACE ( xt concept -- ok ) in a program that names it (the need 32 of FC-SCAN-USES): every word of
the program has a concept cell in the code, a layer that jumps to the current definition; a call and
the xt of the word go to it. The candidate xt is checked by the working check word (%check, the
concept of check-table) against the reference artifacts of the concept (the table of its last check);
it passes if the artifacts agree, its accuracy is not lower and its price (PRICE of its record) is
less and known. Then its definition goes into the concept cell (one record of the link row) and the
previous one onto the stack of definitions; else nothing changes and ok is the reason: 0 not words,
1 the artifacts, 2 the accuracy, 3 the price.

1. Addition (4 + 4 bits, the low 5 bits of the sum) by an expensive definition; a spoiled one and
   one with a loop (price by execution) are refused, a cheaper one replaces it, a dearer one and the
   same one again are refused; a concept never checked by a table: reason 1; not a word: 0. A chain
   of three synonyms (: s1 add ; : s2 s1 ; : s3 s2 ;) runs the current definition before and after
   (the definitions differ outside the 8 bits of the concept: 256 gives 16, then 0); COST of a synonym
   equals COST of the original (also after the replacement: the price of the candidate); the previous
   definition is on the stack of definitions and still runs; the concept is proved.
2. Without REPLACE: : A B ; makes no code, A names the concept cell of B (a chain: of the first
   word), the stream equals the stream of the program that calls B; COST of the synonym equals COST of
   the original at compile time; a comment in the body makes an ordinary definition.
3. The price of a word in a program of the replacement is that of its path from the concept cell:
   on the counters of 13.4 (tools/counters.py) the layers and bits of an execution equal the price,
   the executed instructions its copies; after the replacement an execution of the word costs the
   price of the candidate, which COST gives.
4. The kernel L0 on the emulator compiles and runs the program of 1: the same output, the prices
   with the entry marks of the isolation (two per word: the concept cell and the entry).
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_kernel
import check_programs
import counters
import host
import paths

PRINT = (': d. ( u -- ) dup 10 < if 48 + emit exit then dup 10 / recurse 10 mod 48 + emit ;\n'
         ': n. ( n -- ) dup 0 < if 45 emit 0 swap - then d. 32 emit ;\n'
         ': c. ( size bits copies layers known -- ) n. n. n. n. n. 10 emit ;\n')
ROUND = 'over over and 2* >r xor r> '
ADD = ': add dup 15 and swap 4 rshift ' + ROUND * 5 + '+ ;\n'          # the high nibble not masked
WORDS = ADD + ''': add-fast dup 15 and swap 4 rshift 15 and + ;
: add-bad dup 15 and swap 4 rshift 15 and + dup 17 = if drop 16 then ;
: add-loop dup 15 and swap 4 rshift 15 and 5 0 do over over and 2* >r xor r> loop + ;
: add-dear dup 15 and swap 4 rshift 15 and + 1+ 1- ;
: s1 add ;
: s2 s1 ;
: s3 s2 ;
'''
REPLACE = PRINT + WORDS + '''create ref 1024 allot
: build 16 0 do 16 0 do i j + j i 4 lshift or cells ref + ! loop loop ;
: run ( -- ) 37 s3 n. 256 s3 n. 256 s2 n. 256 s1 n. 256 add n. 256 ['] s3 execute n. 10 emit ;
: main build run ['] add 8 5 ref check-table n. ['] s3 ['] add = n. 10 emit
  ['] s3 cost c. ['] add cost c.
  ['] add-bad ['] add replace n. ['] add-loop ['] add replace n. ['] add-fast ['] add replace n.
  ['] add-dear ['] add replace n. ['] add-fast ['] add replace n.
  ['] add-fast ['] c. replace n. 5 ['] add replace n. ['] add 5 replace n. 10 emit
  run ['] s3 cost c. ['] add cost c. ['] add-fast cost c.
  ['] add %rec 36 + @ dup 0= 0= n. dup 36 + @ n. 4 + @ 256 swap execute n.
  ['] add proved? n. ['] add accuracy n. 10 emit ;'''
# Host Forth after FC-GO: for each word its name, the content of its concept cell (FC-XT), the address
# its concept pointer (cell 5) names, the address of its own cell 3, its entry (cell 6) and price (9-13).
DUMP = r'''
: rd.d dup 10 / ?dup if recurse then 10 mod 48 + emit ;
: rd.n dup 0< if 45 emit negate then rd.d 32 emit ;
: rd.all fc-nwords @ 0 ?do i fc-wt@ dup 2 cells + @ 1 = if ." W " dup @ fc-names @ + over cell+ @ type 32 emit
  dup fc-xt rd.n dup 5 cells + @ rd.n dup 3 cells + rd.n dup 6 cells + @ rd.n
  14 9 do dup i cells + @ rd.n loop cr then drop loop ." T " fc-tramp @ rd.n cr ;
'''
MARK = b'\n@@CONCEPTS@@\n'
FIELDS = ('concept', 'points', 'own', 'entry', 'size', 'bits', 'copies', 'layers', 'known')


def compile_dump(source):
    """(stream, records {name: dict(FIELDS)} of the newest record of each name, trampoline)."""
    task = ('\n'.join('fc| ' + line for line in source.split('\n')) + '\nfc-go\n' + DUMP
            + 'cr .( ' + MARK.decode().strip() + ') cr rd.all\nbye\n')
    out = check_programs.run_host(host.build(), paths.source_bytes(paths.LIBRARY_FILES) + task.encode('latin-1'))
    at = out.rindex(MARK)
    records, tramp = {}, None
    for line in out[at + len(MARK):].decode('latin-1').split('\n'):
        parts = line.split()
        if parts and parts[0] == 'W':
            records[parts[1]] = dict(zip(FIELDS, map(int, parts[2:]), strict=False))
        elif parts and parts[0] == 'T':
            tramp = int(parts[1])
    return out[:at], records, tramp


def run_checked(stream):
    run = subprocess.run([str(paths.CHECKED), '-s', str(paths.SIZE), '-p', '8'], input=stream,
                         capture_output=True, timeout=600, check=False)
    assert run.returncode == 0 and b'AUDIT' not in run.stderr.replace(b'VM1_AUDIT_TICKS', b''), \
        (run.returncode, run.stderr[-300:])
    return run.stdout


def slow(i):
    a, b = i & 15, i >> 4
    for _ in range(5):
        a, b = a ^ b, (a & b) << 1
    return a + b


def fast(i):
    return (i & 15) + ((i >> 4) & 15)


def cost_line(r, marks=0):
    """What C. prints for COST of a record: known layers copies bits size (MARKS entry marks of the kernel)."""
    m = marks if r['known'] else 0
    return f'{r["known"]} {r["layers"]} {r["copies"] + m} {r["bits"] + 32 * m} {r["size"]} '


def runs(f):
    return ' '.join(str(f(i)) for i in (37, 256, 256, 256, 256, 256)) + ' '


def expected(records, marks=0):
    add, fast_r = records['add'], records['add-fast']
    assert slow(256) != fast(256) and all(slow(i) & 31 == fast(i) == (i & 15) + (i >> 4) for i in range(256))
    lines = [runs(slow), '-1 -1 ', cost_line(add, marks), cost_line(add, marks),
             '1 3 -1 3 3 1 0 0 ', runs(fast), cost_line(fast_r, marks), cost_line(fast_r, marks),
             cost_line(fast_r, marks), f'-1 0 {slow(256)} -1 1000000 ', '']
    return '\n'.join(lines).encode()


def check_replace():
    stream, records, _ = compile_dump(REPLACE)
    add, fast_r, dear = records['add'], records['add-fast'], records['add-dear']
    assert add['known'] == fast_r['known'] == dear['known'] == -1 and records['add-loop']['known'] == 0
    price = lambda r: r['size'] + r['bits'] + r['copies'] + r['layers']
    assert price(fast_r) < price(dear) < price(add) and price(records['add-bad']) < price(add), \
        [(n, price(records[n])) for n in ('add', 'add-fast', 'add-bad', 'add-dear')]
    for name in ('s1', 's2', 's3'):         # the chain names the concept cell of the first word
        assert records[name]['points'] == add['own'] and records[name]['concept'] == add['concept'], records[name]
        assert {k: records[name][k] for k in FIELDS[4:]} == {k: add[k] for k in FIELDS[4:]}
    for name in ('add', 'add-fast', 'main', '%check', '%replace'):
        r = records[name]
        assert r['points'] == r['own'] and r['concept'] == r['entry'] - 2048, (name, r)
    assert records['check-table']['points'] == records['%check']['own']
    want = expected(records)
    got = run_checked(stream)
    assert got == want, (got, want)
    print('PASS replace: the spoiled one (1: artifacts) and the one with a loop (3: price by execution) are '
          'refused, the cheaper one replaces the addition, the dearer one and the same one again are refused (3), '
          'a concept not checked by a table (1), not a word (0); price add', price(add), 'add-fast', price(fast_r),
          'add-dear', price(dear))
    print('PASS synonyms: s3 -> s2 -> s1 -> add run the current definition (256: 16, after the replacement 0); '
          'cost of s3 = cost of add, before and after; the previous definition on the stack still runs; '
          'the concept is proved')
    return records, want


def check_synonyms_compile_time():
    program = PRINT + ADD + ': s1 add ;\n: s2 s1 ;\n: s3 s2 ;\n: s4 ( a comment ) add ;\n'
    main = ": main 37 {0} n. 256 {0} n. ['] {0} ['] add = n. 10 emit ['] {0} cost c. ['] add cost c. ;"
    stream, records, _ = compile_dump(program + main.format('s3'))
    add = records['add']
    for name in ('s1', 's2', 's3'):
        r = records[name]
        assert r['points'] == add['own'] and r['concept'] == add['entry'] == add['concept'], (name, r, add)
        assert {k: r[k] for k in FIELDS[4:]} == {k: add[k] for k in FIELDS[4:]}
    s4 = records['s4']
    assert s4['points'] == s4['own'] and s4['concept'] == s4['entry'] != add['entry'], s4
    got = run_checked(stream)
    want = f'7 {slow(256)} -1 \n{cost_line(add)}\n{cost_line(add)}\n'.encode()
    assert got == want, (got, want)
    plain, _, _ = compile_dump(PRINT + ADD + ': s4 ( a comment ) add ;\n' + main.format('add'))
    assert stream == plain, 'a synonym made code'
    print('PASS synonyms without replace: : a b ; makes no code (the stream equals that of the program calling '
          'add), s1 s2 s3 name the concept cell of add, cost equal at compile time; with a comment: a definition')


COUNTED = PRINT + ''': w1 ( i -- r ) 1+ 1+ ;
: w2 ( i -- r ) 2 + ;
create t 16 allot
: main 2 t ! 3 t 4 + ! 4 t 8 + ! 5 t 12 + ! ['] w1 2 32 t check-table drop
  5 w1 drop ['] w2 ['] w1 replace drop 5 w1 drop ['] w1 cost c. ;'''


def check_counters():
    stream, records, tramp = compile_dump(COUNTED)
    w1, w2 = records['w1'], records['w2']
    assert w1['known'] == w2['known'] == -1 and w2['size'] + w2['bits'] + w2['copies'] + w2['layers'] < \
        w1['size'] + w1['bits'] + w1['copies'] + w1['layers'], (w1, w2)
    run = counters.run(stream, limit=3_000_000)
    assert run['out'] == cost_line(w2).encode() + b'\n', (run['out'], cost_line(w2))
    trace = run['trace']
    concepts = {r['concept'] for r in records.values()}
    at = [t for t in range(len(trace)) if trace[t][0] == w1['concept']]
    start = 0
    measured = []
    for _ in range(2 + 4):                    # check-table executes w1 on 4 inputs, then 5 w1 twice
        first, last = counters.window(trace, w1['concept'], concepts, tramp, start)
        measured.append(counters.counters(trace, first, last))
        start = last + 1
    assert len(at) == 6, len(at)
    for got, r in ((measured[4], w1), (measured[5], w2)):
        assert got['layers'] == r['layers'] and got['bits'] == r['bits'] and got['rows'] == r['copies'], (got, r)
    print('PASS price from the concept cell = counters of 13.4: w1', {k: measured[4][k] for k in ('layers', 'bits', 'rows')},
          '; after the replacement w1 runs w2:', {k: measured[5][k] for k in ('layers', 'bits', 'rows')},
          f'({run["ticks"]} ticks)')


def check_kernel_l0(records, want):
    if not paths.EMULATOR.is_file():
        subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'runtime-bitcopy'], check=True)
    got, seconds = check_kernel.run(paths.L0.read_bytes() + REPLACE.encode() + b'\0', 3000)
    want = expected(records, marks=2)
    assert got == want, (got, want)
    print(f'PASS kernel L0: compiles and runs the program of the replacement, the same output; prices with '
          f'two entry marks per word ({seconds:.0f} s)')


def main():
    subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'checked'], check=True)
    records, want = check_replace()
    check_synonyms_compile_time()
    check_counters()
    check_kernel_l0(records, want)


if __name__ == '__main__':
    main()
