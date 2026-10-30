"""Platforms, time and definitions on the host (15.3, language/doc/platform.md).

The programs are compiled by the definition on the host pForth and run on the emulator built from the
definition of the word "space" (`make space`) in a temporary directory, with the remote spaces 2 = host.c
(the C text) and 3 = host.io (the argument and the result).

1. Tables: `host f` makes the definition of f on the host (C, built by cc through EXEC); the table of
   f on the host over all 256 inputs is the table of f in the guest and of f in Python; check-table of
   the host definition with the table of the guest gives -1; platform-of is 0 and 1; the table of the
   platforms runs a definition on the guest (0 platform) and on the host (1 platform).
2. replace by time: a cheap word stays in the guest (the host is slower: 3), a dear word goes to the
   host (-1, platform-of 1, the same results), a cheap word on the host comes back to the guest (-1).
3. Equal time (the difference less than the sum of the errors, 2.11.5): two host definitions of the same
   word, one with `0 or` more in the guest (more copies): fewer copies replaces (-1), more does not (3).
4. The words are only in a program that names them: the definition of the language has none.
"""
import subprocess, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_programs, host, paths, word_cost

SPACE_EMULATOR = paths.OUT / 'space/emulator'
PRINT = (': u. ( u -- ) dup 10 < if 48 + emit exit then dup 10 / recurse 10 mod 48 + emit ;\n'
         ': d. ( n -- ) dup 0 < if 45 emit 0 swap - then u. ;\n')
TRUE = -1


def f(i):
    return ~(i ^ (i << 3)) & 255


def compile_language(source):
    return check_programs.compile_on_host(host.build(), paths.source_bytes(paths.LIBRARY_FILES), source)


def run(stream, folder):
    for name in ('host.c', 'host.io'):
        (folder / name).write_bytes(b'')
    start = time.monotonic()
    result = subprocess.run([str(SPACE_EMULATOR), '-s', str(paths.SIZE), '-p', '8', '-r', 'host.c', '-r', 'host.io'],
                            input=stream, capture_output=True, cwd=folder, timeout=600)
    assert result.returncode == 0 and not result.stderr, (result.returncode, result.stderr[-300:])
    return result.stdout.decode(), time.monotonic() - start


TABLES = PRINT + ''': invert -1 xor ;
: f ( i -- r ) dup 3 lshift xor invert 255 and ;
: f-host host f ;
create ta 1024 allot create tb 1024 allot
: main 256 0 do i f ta i cells + ! loop 256 0 do i f-host tb i cells + ! loop
  256 0 do ta i cells + @ d. 32 emit loop 10 emit 256 0 do tb i cells + @ d. 32 emit loop 10 emit
  ['] f-host 8 8 ta check-table d. 32 emit ['] f platform-of d. 32 emit ['] f-host platform-of d. 32 emit
  77 ['] f 0 platform execute d. 32 emit 77 0 1 platform execute d. 10 emit ;
'''


def check_tables(folder):
    out, seconds = run(compile_language(TABLES), folder)
    guest, on_host, rest = out.split('\n')[:3]
    want = [f(i) for i in range(256)]
    assert list(map(int, guest.split())) == want and list(map(int, on_host.split())) == want, out[:300]
    assert list(map(int, rest.split())) == [TRUE, 0, 1, f(77), f(77)], rest
    assert 'X(109);' in (folder / 'host.c').read_text(), (folder / 'host.c').read_text()[-300:]
    print(f'PASS tables: f on the host (C, cc through EXEC) gives the table of f in the guest over 256 inputs, '
          f'check-table of the host definition -1, platform-of 0 and 1, the table of the platforms runs both '
          f'({seconds:.2f} s)')


DEAR = '\n'.join(['  dup 7 * xor'] * 300)
REPLACE = PRINT + f''': e 255 and ;
: c 15 and ;
: c-host host c ;
: c-host2 host c ;
: g
{DEAR}
  15 and ;
: g-host host g ;
: h1 host e ;
: h2 host e 0 or ;
: h3 host e ;
: h4 host e 0 or ;
create tc 64 allot create tg 64 allot create tc2 64 allot create th2 64 allot create th3 64 allot
: snap ( xt table -- ) 16 0 do over i swap execute over i cells + ! loop drop drop ;
: chk ( xt table -- ) over over snap 4 8 rot check-table d. 32 emit ;
: t. ( xt -- ) time swap d. 32 emit d. 32 emit ;
: main ['] c tc chk ['] g tg chk ['] c-host2 tc2 chk ['] h2 th2 chk ['] h3 th3 chk 10 emit
  ['] h1 cost drop drop rot drop d. 32 emit drop ['] h2 cost drop drop rot drop d. 32 emit drop 10 emit
  ['] c t. ['] c-host t. ['] g t. ['] g-host t. ['] h1 t. ['] h2 t. ['] h3 t. ['] h4 t. 10 emit
  ['] c-host ['] c replace d. 32 emit ['] g-host ['] g replace d. 32 emit
  ['] c ['] c-host2 replace d. 32 emit ['] h1 ['] h2 replace d. 32 emit ['] h4 ['] h3 replace d. 10 emit
  ['] c platform-of d. 32 emit ['] g platform-of d. 32 emit ['] c-host2 platform-of d. 32 emit
  ['] h2 platform-of d. 32 emit 16 0 do i g d. 32 emit loop 10 emit ['] g t. ['] c-host2 t. 10 emit ;
'''


def guest_g(i):
    for _ in range(300):
        i = (i * 7 & 0xFFFFFFFF) ^ i
    return i & 15


def check_replace(folder):
    stream = compile_language(REPLACE)
    out, seconds = run(stream, folder)
    checks, copies, times, oks, after, later = [list(map(int, line.split())) for line in out.split('\n')[:6]]
    assert checks == [TRUE] * 5, checks
    t = dict(zip(['c', 'c-host', 'g', 'g-host', 'h1', 'h2', 'h3', 'h4'], zip(times[0::2], times[1::2])))
    assert oks == [3, TRUE, TRUE, TRUE, 3], (oks, t)
    assert after[:4] == [0, 1, 0, 1] and after[4:] == [guest_g(i) for i in range(16)], after
    (h1, e1), (h2, e2), (h3, e3), (h4, e4) = t['h1'], t['h2'], t['h3'], t['h4']
    assert copies[0] < copies[1], copies
    assert t['c'][0] < t['c-host'][0] and t['g-host'][0] < t['g'][0], t
    print(f'PASS replace by time: c stays in the guest ({t["c"][0]} ns, on the host {t["c-host"][0]} ns: 3); '
          f'g goes to the host ({t["g"][0]} ns in the guest, {t["g-host"][0]} ns on the host: -1, platform-of 1, '
          f'the same results, after it {later[0]} ns); c-host2 comes back to the guest (-1, {later[2]} ns)')
    print(f'PASS equal time, by the copies: h1 {h1} +- {e1} ns ({copies[0]} copies), h2 {h2} +- {e2} ns '
          f'({copies[1]} copies): h1 replaces h2 (-1), h4 does not replace h3 (3); h3 {h3} +- {e3}, h4 {h4} +- {e4} '
          f'({seconds:.1f} s)')


def check_only_when_named():
    sys.path[:0] = [str(paths.REFERENCE)]
    import model
    source = PRINT + ': main 65 emit 10 emit ;'
    assert compile_language(source) == model.compile_forth(source)
    _, records, _ = word_cost.definition()
    assert not {'%time', '%host', '%better', '%pt', '%pl'} & set(records), 'in the definition'
    print('PASS the words of the platforms are compiled only into a program that names them (the definition of '
          'the language has none)')


def main():
    subprocess.run(['make', '-s', '-C', str(paths.ROOT), 'space'], check=True)
    with tempfile.TemporaryDirectory(dir=paths.BUILD) as name:
        check_tables(Path(name))
    with tempfile.TemporaryDirectory(dir=paths.BUILD) as name:
        check_replace(Path(name))
    check_only_when_named()
    print('ALL platforms: tables on the host, replace by time and by the copies at equal time, on', SPACE_EMULATOR)


if __name__ == '__main__':
    main()
