"""User programs do not get dearer (14.14, language/doc/user_programs.md).

The tool tools/user_programs.py keeps programs of the user (source, code, price, artifact) and, when
the language is recompiled, recompiles them: the new code is accepted if its price is not higher (and
the output is the same), otherwise the previous code stays. The language is a copy of src/ with a
definition of a generator replaced by hand (Language.replaced: no check of the price of the language).

1. Programs compiled by a language with a dear CELLS (two shifts instead of one) are recompiled by the
   language of src/ (a cheaper definition): the programs that use CELLS are accepted with a lower
   price, the one that does not is the same code; the accepted code is the stream the language of src/
   gives directly, and for the language of src/ it equals the stream of the model; the previous code is
   on the stack of the program and still gives the same output. With MEASURE the price of the run (the
   counters of 13.4) of the accepted code is lower too.
2. Programs compiled by the language of src/ are recompiled by the language with the dear CELLS (not
   checked by price): the programs that use CELLS keep their previous code byte for byte (refused:
   price) and their price did not grow, the dear code would have been dearer; a program without CELLS
   keeps its code. Both are executed. A change of the language that costs nothing (a comment) is
   the same code.
3. The rule. Dear CELLS -> dear 1+ (CELLS cheaper, 1+ dearer): a program with three CELLS and one 1+ is
   dearer in one word and cheaper in the sum: refused by the rule 'words' (no word dearer), accepted
   by the rule 'total'.
4. Artifacts and errors: a language whose 1+ adds -1 (the same price) is refused (artifacts); a
   language that cannot compile the program (CELLS throws) is refused (error); the code stays.
5. The language boots: the language of src/ gives L0 of the build, the one with the dear CELLS another.
   The tool on the command line (add, recompile, show). PRICE of the tool is the language word PRICE.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import paths
import user_programs
from user_programs import Language, Store, compile_program, run_checked

PROGRAMS = {
    'cells': '''create buf 64 allot
: slot ( i -- a ) cells buf + ;
: fill ( -- ) 5 0 do i 1+ i slot ! loop ;
: total ( -- n ) 0 5 0 do i slot @ + loop ;
: show ( n -- ) 48 + emit ;
: main fill total show 10 emit ;''',
    'plain': ''': sq ( n -- n ) dup * ;
: main 3 sq 48 + emit 10 emit ;''',
    'mix': ''': c3 ( n -- n ) cells cells cells ;
: inc ( n -- n ) 1+ ;
: main 1 c3 c3 drop 5 inc inc 48 + emit 10 emit ;''',
}
OUTPUT = {'cells': b'?\n', 'plain': b'9\n', 'mix': b'7\n'}
DEAR_CELLS = ': gen-cells ( -- ) 1 fc-fold? if fc-ct- 4 * fc-ct+ exit then 1 fc-shift-copy 1 fc-shift-copy ;'
DEAR_ONE = ': gen-1+ ( -- ) 1 fc-fold? if fc-ct- 1+ fc-ct+ exit then 1 fc-literal gen+ ;'
BAD_ONE = ': gen-1+ ( -- ) 1 fc-fold? if fc-ct- 1+ fc-ct+ exit then lay-t-sub @ 1 1 fc-inc ;'
FAILING = ': gen-cells ( -- ) -13 throw ;'
COMMENT = ': gen-decimal ( -- ) ;   \\ numbers are decimal only (the language is edited)'


def fresh(directory, language, measure=False):
    store = Store(directory)
    for name, source in PROGRAMS.items():
        result = store.add(name, source, language, measure)
        assert result['output'] == OUTPUT[name], (name, result['output'])
    return store


def totals(store):
    return {name: store.record(name)['total'] for name in store.names()}


def statuses(report):
    return {name: (status, reason) for name, status, reason, _ in report}


def check_cheaper(work, real, dear):
    store = fresh(work / 'a', dear, measure=True)
    before, runs = totals(store), {n: store.record(n)['run'] for n in store.names()}
    old_codes = {n: store.code(n) for n in store.names()}
    report = store.recompile(real)
    got = statuses(report)
    assert got == {'cells': ('accepted', ''), 'mix': ('accepted', ''), 'plain': ('same', '')}, report
    after = totals(store)
    direct = {n: compile_program(real, PROGRAMS[n], measure=True) for n in PROGRAMS}
    sys.path[:0] = [str(paths.REFERENCE)]
    import model
    for name in PROGRAMS:
        assert after[name] <= before[name], (name, before, after)
        assert store.code(name) == direct[name]['stream'] == model.compile_forth(PROGRAMS[name]), name
        assert run_checked(store.code(name)) == OUTPUT[name] == store.output(name)
        assert store.record(name)['run']['price'] <= runs[name]['price'], (name, runs[name], store.record(name)['run'])
        assert store.record(name)['history'][-1]['status'] == got[name][0]
    assert after['cells'] < before['cells'] and after['mix'] < before['mix'] and after['plain'] == before['plain']
    assert store.record('cells')['run']['price'] < runs['cells']['price']
    for name in ('cells', 'mix'):                                    # the previous code on the stack still works
        assert store.stack(name) == [old_codes[name]] and old_codes[name] != store.code(name)
        assert run_checked(store.stack(name)[0]) == OUTPUT[name]
    assert store.stack('plain') == []
    print('PASS cheaper language: cells %d -> %d, mix %d -> %d, plain %d (the same code); the accepted code = the code of'
          ' the language of src/ = the stream of the model; the previous code is on the stack and runs; run price'
          ' (13.4) cells %d -> %d' % (before['cells'], after['cells'], before['mix'], after['mix'], after['plain'],
                                      runs['cells']['price'], store.record('cells')['run']['price']))


def check_dearer(work, real, dear, comment):
    store = fresh(work / 'b', real)
    before, codes = totals(store), {n: store.code(n) for n in store.names()}
    report = store.recompile(dear)
    assert statuses(report) == {'cells': ('refused', 'price'), 'mix': ('refused', 'price'), 'plain': ('same', '')}, report
    for name in PROGRAMS:
        assert store.code(name) == codes[name] and totals(store)[name] == before[name], name
        assert run_checked(store.code(name)) == OUTPUT[name]
        assert store.stack(name) == []
    for name in ('cells', 'mix'):                   # the dearer language really gives a dearer program
        assert compile_program(dear, PROGRAMS[name])['total'] > before[name], name
        assert compile_program(dear, PROGRAMS[name])['stream'] != codes[name]
    assert store.record('cells')['history'][-1]['status'] == 'refused'
    again = store.recompile(comment)                # a change that costs nothing: the same code
    assert set(statuses(again).values()) == {('same', '')} and all(store.code(n) == codes[n] for n in codes), again
    assert comment.digest() != real.digest()
    print('PASS dearer language (by hand, no price check): the programs with cells keep their code byte for byte '
          '(refused, price), the price did not grow (%s), the dear code would be dearer; plain: the same code; '
          'a comment in the language: the same code' % before)


def check_rule(work, dear_cells, dear_one):
    store = fresh(work / 'c', dear_cells)
    words, total = store.record('mix')['words'], store.record('mix')['total']
    new = compile_program(dear_one, PROGRAMS['mix'])
    assert new['total'] < total and new['words']['c3']['price'] < words['c3']['price'] \
        and new['words']['inc']['price'] > words['inc']['price'], (words, new['words'])
    assert statuses(store.recompile(dear_one, rule='words'))['mix'] == ('refused', 'price')
    assert store.record('mix')['total'] == total
    assert store.record('mix')['history'][-1]['detail'].startswith('dearer words: inc')
    assert statuses(store.recompile(dear_one, rule='total'))['mix'] == ('accepted', '')
    assert store.record('mix')['total'] == new['total'] < total
    print('PASS rule: mix has c3 %d -> %d (cheaper) and inc %d -> %d (dearer), the program %d -> %d: refused by the'
          " rule 'words', accepted by 'total'" % (words['c3']['price'], new['words']['c3']['price'],
                                                  words['inc']['price'], new['words']['inc']['price'], total, new['total']))


def check_refusals(work, real, bad, failing):
    store = fresh(work / 'd', real)
    codes, before = {n: store.code(n) for n in store.names()}, totals(store)
    assert compile_program(bad, PROGRAMS['mix'])['total'] == before['mix'], 'the price of the bad 1+ should be the same'
    report = store.recompile(bad)
    assert statuses(report) == {'cells': ('refused', 'artifacts'), 'mix': ('refused', 'artifacts'),
                                'plain': ('same', '')}, report
    # cells has 1+ too (fill); plain has no 1+
    report = store.recompile(failing)
    assert statuses(report) == {'cells': ('refused', 'error'), 'mix': ('refused', 'error'), 'plain': ('same', '')}, report
    for name in PROGRAMS:
        assert store.code(name) == codes[name] and totals(store)[name] == before[name]
        assert run_checked(store.code(name)) == OUTPUT[name]
    assert [h['status'] for h in store.record('mix')['history']] == ['new', 'refused', 'refused']
    print('PASS refusals: the language with 1+ that adds -1 (the same price, another output) is refused (artifacts), '
          'the language that cannot compile (error); the code stays')


def check_boot(real, dear):
    stream = real.boot()
    if paths.L0.is_file():
        assert stream == paths.L0.read_bytes(), 'the language of src/ boots to L0'
    other = dear.boot()
    assert other != stream and len(other) > 1_000_000
    print('PASS boot: the language of src/ gives L0 (%d bytes)%s, the one with the dear cells another (%d bytes)'
          % (len(stream), ' equal to the build' if paths.L0.is_file() else '', len(other)))


def check_price_word(real):
    got = run_checked(compile_program(real, ': main 1 2 3 4 price 48 + emit ;')['stream'])
    assert got == bytes([48 + user_programs.price(1, 2, 3, 4)]), got
    print('PASS price: the tool and the word PRICE of the language give the same number (1 2 3 4 price = %d)'
          % user_programs.price(1, 2, 3, 4))


def check_command_line(work, dear):
    store, src = work / 'cli', work / 'plain.fth'
    src.write_text(PROGRAMS['cells'])
    tool = [sys.executable, '-B', str(Path(__file__).resolve().parents[1] / 'tools/user_programs.py')]
    # the language of the directory: src/ with the dear cells
    directory = work / 'language'
    directory.mkdir()
    for name, text in dear.files.items():
        (directory / name).write_bytes(text.encode('latin-1'))
    out = subprocess.run(tool + ['add', str(store), 'cells', str(src), '--language', str(directory)],
                         capture_output=True, text=True, check=True).stdout
    assert out.startswith('cells:'), out
    out = subprocess.run(tool + ['recompile', str(store)], capture_output=True, text=True, check=True).stdout
    assert out.startswith('cells: accepted '), out
    out = subprocess.run(tool + ['show', str(store)], capture_output=True, text=True, check=True).stdout
    assert out.startswith('cells: price') and 'new accepted' in out and 'stack 1' in out, out
    print('PASS command line: add (dear language), recompile (src/), show:', out.strip())


def main():
    subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'checked'], check=True)
    real = Language.load()
    dear = real.replaced('gen-cells', DEAR_CELLS)
    dear_one = real.replaced('gen-1+', DEAR_ONE)
    assert real.replaced('gen-cells', real.files['primitives.fth'][slice(*user_programs.definition_span(
        real.files['primitives.fth'], 'gen-cells'))]).digest() == real.digest()
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=paths.BUILD) as temporary:
        work = Path(temporary)
        check_price_word(real)
        check_cheaper(work, real, dear)
        check_dearer(work, real, dear, real.replaced('gen-decimal', COMMENT))
        check_rule(work, dear, dear_one)
        check_refusals(work, real, real.replaced('gen-1+', BAD_ONE), real.replaced('gen-cells', FAILING))
        check_command_line(work, dear)
        check_boot(real, dear)
    print('ALL user programs do not get dearer')


if __name__ == '__main__':
    main()
