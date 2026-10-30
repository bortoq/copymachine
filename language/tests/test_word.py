"""The record of a word and its mechanisms (14.11, language/doc/word.md).

1. The price at compile time and its check by the counters of 13.4 (tools/counters.py: the counters
   of language/tests/reference/vm2_reference.py on the four-index machine): five words without loops (sum,
   branch, memory, call of a word and a channel, the helpers of * and /) are compiled by the
   definition on the host pForth and executed; on the ticks of each execution (from its entry to
   the trampoline of its return) layers and bits equal the price of the word, the executed
   instructions equal its copies, the copies of 13.4 (those that changed memory) are not more.
   The word with a branch is executed on both branches: its price is the largest of each counter.
   The size is the cells from the entry to the first free cell: the ticks of the word are in them.
2. Loops, recursion, a call of an xt, CATCH, a call of a word priced by execution: by execution
   (known 0, no counters).
3. The words of the language COST PRICE PROVED? in a program, in a definition and at the top level,
   give the prices of the records; COST of an xt not known at compile time: -13.
4. The record: the concept cell is the word's own and holds the index definition, the copy and host
   space definitions are empty, the proof is the record of the unproved (nothing checked), the stack
   of definitions is empty; a proof that refers to FC-PROVED makes PROVED? true; a call goes through
   the concept cell (another xt in it: the word calls that definition).
5. The kernel L0 on the emulator gives the same prices to the program it compiles, plus the entry
   mark of the isolation (one copy of 32 bits in the first layer of each word, 14.10).
6. The words of the definition of the language get prices too (summary printed); the prices of the
   colon definitions of the core in doc/language.md are those the compiler gives them.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_kernel
import check_programs
import counters
import host
import language_md
import paths
import word_cost

FIVE = '''variable v
: w1 ( a b -- c ) + 2* ;
: w2 ( a -- b ) dup 0= if 1+ else 1- 1- then ;
: w3 ( addr -- ) dup @ 1+ swap ! ;
: w4 ( -- ) 3 4 w1 drop 65 emit ;
: w5 ( a b -- p q ) over over * >r / r> ;
: main 1 2 w1 drop 0 w2 drop 5 w2 drop v w3 w4 7 3 w5 drop drop 10 emit ;'''
BY_EXECUTION = ''': u1 ( n -- ) begin 1- dup 0= until drop ;
: u2 ( n -- ) 0 do loop ;
: u3 ( n -- ) dup if 1- recurse else drop then ;
: u4 ( xt -- ) execute ;
: u5 ( -- ) ['] u1 catch drop ;
: u6 ( -- ) 3 u1 ;
: k1 ( -- n ) 1 if 2 else 3 then ;
: main 3 u1 3 u2 3 u3 ['] k1 u4 drop u6 k1 drop ;'''
PRINT = (': d. ( u -- ) dup 10 < if 48 + emit exit then dup 10 / recurse 10 mod 48 + emit ;\n'
         ': n. ( n -- ) dup 0 < if 45 emit 0 swap - then d. 32 emit ;\n'
         ': c. ( size bits copies layers known -- ) n. n. n. n. n. ;\n')
WORDS = PRINT + ''': w1 ( a b -- c ) + 2* ;
: u1 ( n -- ) begin 1- dup 0= until drop ;
['] w1 cost c. ['] w1 cost drop price n. 10 emit
: main ['] w1 cost c. ['] u1 cost c. ['] w1 cost drop price n. ['] w1 proved? n. ['] u1 proved? n.
  1 2 3 4 price n. 10 emit ;'''
# Host Forth before the program: a generator PROVE! W gives W the proof FC-PROVED, REBIND A B puts
# the xt of B into the concept cell of A (the registration as in tests/test_literals.py).
BEFORE = ''': gen-prove fc-next! fc-find fc-proved swap 14 cells + ! ;
: gen-rebind fc-next! fc-find fc-next! fc-find fc-xt swap 3 cells + ! ;
: word-generators fc-generators s" prove!" ['] gen-prove 0 fc-generator
  s" rebind" ['] gen-rebind 0 fc-generator ;
' word-generators fc-gens !
'''
HOST_REPORT = (': h.n dup 0< if 45 emit negate then dup 10 / ?dup if recurse then 10 mod 48 + emit ;\n'
               ': try [\'] fc-go catch ?dup if ." error " h.n ."  at " fc-tok fc-tl @ type 10 emit then ;\n')
PRICE = ('size', 'bits', 'copies', 'layers', 'known')


def run_checked(stream):
    run = subprocess.run([str(paths.CHECKED), '-s', str(paths.SIZE), '-p', '8'], input=stream,
                         capture_output=True, timeout=600)
    assert run.returncode == 0, (run.returncode, run.stderr[-300:])
    return run.stdout


def host_compile(source, before=''):
    task = before + HOST_REPORT + '\n'.join('fc| ' + line for line in source.split('\n')) + '\ntry bye\n'
    return check_programs.run_host(host.build(), paths.source_bytes(paths.LIBRARY_FILES) + task.encode('latin-1'))


def printed(record, kernel=False):
    """What C. prints for a record (known first); KERNEL: with the entry mark of a word."""
    mark = 1 if kernel and record['known'] else 0
    return f'{record["known"]} {record["layers"]} {record["copies"] + mark} {record["bits"] + 32 * mark} {record["size"]} '


def price_of(record, kernel=False):
    mark = 1 if kernel and record['known'] else 0
    return record['size'] + record['bits'] + 32 * mark + record['copies'] + mark + record['layers']


def check_five():
    stream, records, info = word_cost.compile_with_records(FIVE)
    run = counters.run(stream)
    assert run['out'] == b'A\n', run['out']
    trace, tramp = run['trace'], info['tramp']
    entries = {r['entry'] for r in records.values()}
    ranges = sorted((r['entry'], r['entry'] + r['size'] * 1024) for r in records.values())
    for (lo, hi), (next_lo, _) in zip(ranges, ranges[1:]):          # the size: no overlap, at most one cell between
        assert next_lo - hi in (0, 1024), (lo, hi, next_lo)
    print(f'PASS sizes: the cells of the words follow each other ({len(ranges)} words); '
          f'{run["ticks"]} ticks, output {run["out"]!r}')
    start = 0
    rows = []
    for name in ('w1', 'w2', 'w2', 'w3', 'w4', 'w5'):
        r = records[name]
        assert r['known'] == -1, (name, r)
        first, last = counters.window(trace, r['entry'], entries, tramp, start)
        start = last + 1
        own = [t for t in range(first, last + 1) if r['entry'] <= (trace[t][0] or 0) < r['entry'] + r['size'] * 1024]
        others = [lo for lo, hi in ranges if lo != r['entry']]
        for t in range(first, last + 1):
            cell = trace[t][0]
            assert cell is not None and (cell == tramp or r['entry'] <= cell < r['entry'] + r['size'] * 1024
                    or any(lo <= cell < hi for lo, hi in ranges) or cell < ranges[0][0]), (name, t, cell)
        assert own and trace[first][0] == r['entry'] and len(own) <= r['layers'], (name, len(own))
        rows.append((name, counters.counters(trace, first, last), r))
    measured = {}
    for name, got, r in rows:                                         # w2: the largest of its two runs
        if name in measured:
            measured[name] = {k: max(v, measured[name][k]) for k, v in got.items()}
        else:
            measured[name] = got
    print('| слово | размер | цена: слои | такты (13.4) | биты | биты (13.4) | копирования | исполнено инструкций '
          '| копирования (13.4) |')
    for name in ('w1', 'w2', 'w3', 'w4', 'w5'):
        r, got = records[name], measured[name]
        assert got['layers'] == r['layers'] and got['bits'] == r['bits'] and got['rows'] == r['copies'], (name, got, r)
        assert got['copies'] <= r['copies'], (name, got, r)
        print(f'| {name} | {r["size"]} | {r["layers"]} | {got["layers"]} | {r["bits"]} | {got["bits"]} | {r["copies"]} '
              f'| {got["rows"]} | {got["copies"]} |')
    runs = [got for name, got, _ in rows if name == 'w2']
    assert runs[0] != runs[1], 'the branches of w2 should differ'
    print('PASS price = counters of 13.4 on the execution: 5 words, layers and bits equal, executed '
          'instructions = copies of the price, changed copies (13.4) not more; w2: the largest branch',
          [(g['layers'], g['bits']) for g in runs])
    assert info['mul']['known'] == -1 and info['div']['known'] == -1, info
    print('PASS helpers priced: mul', info['mul'], 'div', info['div'])
    return records


def check_by_execution():
    stream, records, _ = word_cost.compile_with_records(BY_EXECUTION)
    assert run_checked(stream) == b'', 'the program writes nothing'
    for name in ('u1', 'u2', 'u3', 'u4', 'u5', 'u6', 'main'):
        r = records[name]
        assert r['known'] == 0 and r['bits'] == r['copies'] == r['layers'] == 0 and r['size'] > 0, (name, r)
    assert records['k1']['known'] == -1 and records['k1']['layers'] > 0, records['k1']
    print('PASS by execution: begin-until, do-loop, recurse, execute, catch, a call of such a word;'
          ' k1 (a branch) known:', {k: records['k1'][k] for k in PRICE})


def check_words():
    _, records, _ = word_cost.compile_with_records(WORDS)
    w1, u1 = records['w1'], records['u1']
    want = (printed(w1) + str(price_of(w1)) + ' \n' + printed(w1) + printed(u1) + str(price_of(w1))
            + ' 0 0 10 \n').encode()
    got = run_checked(host_compile(WORDS))
    assert got == want, (got, want)
    print('PASS cost price proved? at the top level and in a definition:', got.decode().split('\n')[1])
    for source in (': main dup cost ;', ': main dup proved? ;', ": x ; : main ['] x 1+ cost ;"):
        out = host_compile(source)
        assert out.endswith(b'error -13 at ' + source.split()[-2].encode() + b'\n'), (source, out[-60:])
    got = run_checked(host_compile(PRINT + ': main 5 cost c. 10 emit ;'))
    assert got == b'0 0 0 0 0 \n', got
    print('PASS cost and proved? of an xt not known at compile time: error -13; of a literal that is no word: 0 0 0 0 0')
    return records, want


def check_record():
    source = ': a 65 emit ; : b 66 emit ; : c 67 emit ; prove! c rebind a b\n: main a [\'] a execute c 10 emit ;'
    stream, records, _ = word_cost.compile_with_records(source, BEFORE)
    assert run_checked(stream) == b'BBC\n', run_checked(stream)
    a, b, c = records['a'], records['b'], records['c']
    for r in (b, c, records['main']):
        assert r['own_concept'] == -1 and r['concept_is_index'] == -1, r
    assert a['own_concept'] == -1 and a['concept_is_index'] == 0, a     # the concept cell holds b
    for r in records.values():
        assert r['copy'] == r['host'] == r['stack'] == 0, r
    assert c['proof'] == 1 and a['proof'] == b['proof'] == 0 and a['checked'] == a['checked_bits'] == a['way'] == 0
    print('PASS record: concept cell, definitions (index; copy and host empty), proof (unproved: nothing '
          'checked), empty stack of definitions; a call and the xt go through the concept cell (a calls b)')
    got = run_checked(host_compile(": a ; : b ; prove! a\n: main ['] a proved? 48 + emit ['] b proved? 48 + emit ;",
                                   BEFORE))
    assert got == b'/0', got                 # -1 + 48 = '/': proved; 0: not proved
    print('PASS proved?: true for a proof that refers to the word proved (fc-proved), false otherwise')


def check_kernel_prices(records):
    if not paths.EMULATOR.is_file():
        subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'runtime-bitcopy'], check=True)
    w1, u1 = records['w1'], records['u1']
    want = (printed(w1, True) + str(price_of(w1, True)) + ' \n' + printed(w1, True) + printed(u1, True)
            + str(price_of(w1, True)) + ' 0 0 10 \n').encode()
    got, seconds = check_kernel.run(paths.L0.read_bytes() + WORDS.encode() + b'\0', 1800)
    assert got == want, (got, want)
    print(f'PASS kernel L0: the same prices, plus the entry mark (1 copy, 32 bits) ({seconds:.0f} s):',
          got.decode().split('\n')[1])


def check_definition():
    _, records, info = word_cost.definition()
    assert records['nip']['known'] == -1 and records['fill']['known'] == 0, (records['nip'], records['fill'])
    assert records['fc-path']['known'] == 0 and records['fc-xt']['known'] == -1
    print('PASS the definition of the language:', word_cost.summary(records).replace('\n', ';'))
    lines = language_md.DOC.read_text().split('\n')
    _, changed, errors = language_md.prices(list(lines), info['versions'])
    assert not errors and not changed, (f'{changed} prices of doc/language.md differ from the compiler '
                                        '(tools/language_md.py --prices)', errors[:5])
    print('PASS doc/language.md: the prices of the colon definitions of the core are those of the compiler')


def main():
    subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'checked'], check=True)
    check_five()
    check_by_execution()
    records, _ = check_words()
    check_record()
    check_kernel_prices(records)
    check_definition()


if __name__ == '__main__':
    main()
