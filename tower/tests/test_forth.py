"""Forth on the chain (23.15, part 1): `programs/forth.tw` is a compiler of a subset of Forth, a program of the chain (language 3). It reads a text
of Forth and a zero byte and writes a text of language 3 (and a zero byte) which the chain turns into the image of the program:
    Forth text -> forth -> l3c -> l2l -> seed -> image -> output
Every tool is made by the chain from its text of language 1 (seed.l1, l2l.l1, l3c.l1, forth.l1) on the emulator: the compiler of Forth has no
Python reference (the texts of language 3 it writes are checked by running them). The 37 programs of the present language are in
`programs/forth37/*.fs` (the Forth texts) with the output in `expected.txt` (the same as for the hand-written texts of 23.11); here a few small ones
and some texts of other words go through the whole chain; all 37 are in long_forth.py (make check-tower-long). The tables of forth.tw between the
marks are made by programs/forth_gen.sh from programs/forth.def (awk); a test compares them.
Run: make check-tower  or  python3 -B tower/tests/test_forth.py"""
import os
import subprocess
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import l1text
import test_forth37 as f
import test_l3c as t
from common import run

DIR = os.path.join(t.PROGRAMS, 'forth37')
BIG = 300 * 10 ** 6
LIMIT = 10 ** 7
SMALL = ['return_stack', 'stack', 'constant', 'calls', 'execute', 'pick_roll', 'variables', 'strings']
WORDS = 65                  # the lines of the words in forth.def (README of the chain, 3.7: 64 words, `'` and `[']` are one)
_TOOLS = {}


def names():
    return sorted(n[:-3] for n in os.listdir(DIR) if n.endswith('.fs'))


def source(name):
    with open(os.path.join(DIR, name + '.fs'), 'rb') as h:
        return h.read()


def step(name, tool, stdin, checked=False):
    """One run of a tool on the emulator (plain by default: the tools are audited in test_l3c.py and long_l3c.py): the output."""
    image, A, P = tool
    r = run(image, A, P, checked=checked, limit=BIG, stdin=stdin)
    assert r.rc == 0 and not r.err.strip().startswith(('l3c:', 'l2l:', 'l1:')), (name, r.rc, r.err)
    return r


def tools():
    """seed (the Python encoder, once), l2l, l3c and forth (the seed on their texts of language 1): (image, A, P)."""
    if not _TOOLS:
        t.setUpModule()
        seed = (l1text.encode(t.read('seed.l1', 'rb') + b'\0')[0], 16, 7)
        _TOOLS['seed'] = seed
        _TOOLS['l2l'] = (step('seed on l2l.l1', seed, t.read('l2l.l1', 'rb') + b'\0').out, 19, 20)
        _TOOLS['l3c'] = (step('seed on l3c.l1', seed, t.read('l3c.l1', 'rb') + b'\0').out, 20, 2)
        _TOOLS['forth'] = (step('seed on forth.l1', seed, t.read('forth.l1', 'rb') + b'\0').out, 20, 2)
    return _TOOLS


def build(fs):
    """Forth text -> text of language 3 -> language 2 -> language 1 -> image (every step on the plain emulator): the image."""
    tl = tools()
    tw = step('forth', tl['forth'], fs + b'\0').out
    l2 = step('l3c', tl['l3c'], tw).out
    l1 = step('l2l', tl['l2l'], l2 + l2).out
    return step('seed', tl['seed'], l1).out


def output(fs):
    """The output of a Forth text run on the checked emulator."""
    r = run(build(fs), 20, 2, checked=True, limit=LIMIT)
    return r.rc, r.out


class Texts(unittest.TestCase):
    def test_generated_is_current(self):
        """The tables of forth.tw between the marks are what forth_gen.sh makes of forth.def."""
        src = t.read('forth.tw')
        a, b = src.index('# --- begin generated\n') + len('# --- begin generated\n'), src.index('# --- end generated')
        r = subprocess.run(['sh', os.path.join(t.PROGRAMS, 'forth_gen.sh')], check=True, capture_output=True, timeout=120)
        self.assertEqual(src[a:b], r.stdout.decode())

    def test_words(self):
        """The words of forth.def: 65 (the word `'` and `[']` are two spellings of one)."""
        words, on = [], False
        for line in t.read('forth.def').split('\n'):
            if line == '=words':
                on = True
            elif on and line.strip() and not line.startswith('//'):
                words.append(line.split()[0])
        self.assertEqual((len(words), len(set(words))), (WORDS, WORDS))

    def test_sources(self):
        """37 Forth texts, one for each output of expected.txt; they are those of language/tests/reference/forthc_programs.py if it is there."""
        want = f.expected()
        self.assertEqual(names(), sorted(want))
        self.assertEqual(len(names()), 37)
        ref = os.path.join(t.common.ROOT, 'language', 'tests', 'reference')
        if os.path.isfile(os.path.join(ref, 'forthc_programs.py')):
            sys.path.insert(0, ref)
            try:
                import forthc_programs as fp
            finally:
                sys.path.remove(ref)
            texts = dict(fp.PROGRAMS)
            texts.update({n: tx for n, (tx, _) in fp.EXPECTED.items()})
            for n in names():
                self.assertEqual(source(n).decode(), fp.wrapped(texts[n.replace('_', '-')]) + '\n', n)


class Chain(unittest.TestCase):
    """Forth texts through forth, l3c, l2l and seed on the emulator; the image runs on the checked emulator."""

    @classmethod
    def setUpClass(cls):
        tools()
        cls.want = f.expected()

    def test_small_programs(self):
        for n in SMALL:
            with self.subTest(n):
                self.assertEqual(output(source(n)), (0, self.want[n]))

    def test_other_words(self):
        """Forms which the 37 do not use: a line comment, a comment in parentheses, a name longer than 8 characters, `recurse` in a word of a
        test, `create` with `allot`, a string longer than 7 bytes, `j`, `?do` with `leave`, top-level code before and after the definitions."""
        fs = (b'\\ a comment\n: sq dup * ; 5 sq 48 + emit ( a comment ) \n'
              b': verylongname 3 ; : again verylongname 1+ ; again 48 + emit\n'
              b': f dup 3 < if 1+ recurse then ; 0 f 48 + emit\n'
              b'create tab 4 allot 7 tab c! tab c@ 48 + emit s" abcdefghij" swap drop 48 + emit\n'
              b': main 2 0 do 2 0 do j 48 + emit i 48 + emit loop loop 9 0 ?do 66 emit leave loop ; \\ the end\n')
        self.assertEqual(output(fs), (0, b'I437:00011011B'))


if __name__ == '__main__':
    unittest.main()
