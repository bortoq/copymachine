"""Tests of the text of programs (23.6): tower/text.py reads tower/programs/*.tw; the images are byte for byte
the images of the builders of progs.py; wrong texts are rejected at parse time; the program dict.tw (a dictionary
of words and decimal numbers) runs on the emulator in checked mode.
Run: make check-tower  or  python3 -B tower/tests/test_text.py"""
import os
import random
import re
import subprocess
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import common
import l3
import progs
import text
from common import stream
from l4 import host_pos
from test_tower import arith_want, intervals, once

PROGRAMS = os.path.join(common.HERE, 'programs')
BUILDERS = {
    'add': progs.add_print(200, 100), 'branch': progs.branch(3, 9), 'loop_digits': progs.loop_digits(),
    'loop_sum': progs.loop_sum(), 'calls': progs.calls(), 'and_hex': progs.and_hex(0xac, 0x3f),
    'add16_hex': progs.add16_hex(0x1234, 0xfff), 'array': progs.array_rev([65, 10, 255, 0, 128, 127, 19, 196]),
    'arith8': progs.arith(8, 3, 5), 'arith16': progs.arith(16, 7, 9), 'echo': progs.echo(), 'fib': progs.fib(),
    'long_rw': progs.long_rw(host_pos(1, 8), b'hello', host_pos(1, 8)),
    'long_read': progs.long_rw(0, b'', host_pos(1, 8), 4),
    'long_clock': progs.long_clock(), 'long_cat': progs.long_cat(1, 5, 8),
}


def setUpModule():
    common.ensure_built()


def source(name):
    with open(os.path.join(PROGRAMS, name + '.tw'), encoding='utf-8') as h:
        return h.read()


def errors(src, level=4):
    return text.parse(src, level).errors


MAIN = ':main block\n'


class Programs(unittest.TestCase):
    def test_every_program_is_in_text(self):
        names = sorted(f[:-3] for f in os.listdir(PROGRAMS) if f.endswith('.tw'))
        self.assertEqual(names, sorted(list(BUILDERS) + ['dict', 'seed', 'l2c', 'l2l', 'l3c']))

    def test_parse_and_bytes(self):
        """Each text is accepted and gives the image of its builder byte for byte (and the same A and P)."""
        for name, build in BUILDERS.items():
            with self.subTest(name):
                self.assertEqual(errors(source(name)), [])
                p, errs = text.compile_text(source(name))
                self.assertEqual(errs, [])
                q = l3.compile_program(build)
                self.assertEqual((p.stats['A'], p.stats['P']), (q.stats['A'], q.stats['P']))
                self.assertEqual(p.stats['image'], q.stats['image'])

    def test_no_names_in_image(self):
        """The labels are only for the compiler: no name of a label of the text is in the image."""
        for name in BUILDERS:
            src = source(name)
            literals = ''.join(re.findall(r'"[^"\n]*"', src))
            labels = {m for m in re.findall(r':([A-Za-z_]\w*)', re.sub(r'#[^\n]*', '', src)) if len(m) >= 3}
            image = text.compile_text(src)[0].stats['image']
            for lab in labels:
                if lab not in literals:
                    self.assertNotIn(lab.encode(), image, (name, lab))

    def test_run(self):
        """The programs from text run on the checked emulator (the outputs of the builders' tests)."""
        for name, inp, want in (('add', b'', b'300\n'), ('calls', b'', b'3ac3\n'), ('loop_sum', b'', b'055\n'),
                                ('fib', stream(10, 8), b'055\n'), ('branch', b'', b'Y\n'),
                                ('echo', b'hi there\x00tail', b'hi there'), ('and_hex', b'', b'2c'),
                                ('array', b'', bytes([127, 255, 196, 128, 10, 19, 0, 65]) + b'\n'),
                                ('arith8', stream(200, 8) + stream(77, 8), arith_want(8, 3, 5, 200, 77))):
            with self.subTest(name):
                p = text.compile_text(source(name))[0]
                self.assertEqual(once(p, plain=(name == 'add'), stdin=inp).out, want)
                intervals(p)

    def test_cli(self):
        """python3 -m tower.text < prog.tw > image: the image of the builder; an error gives the status 1."""
        root = os.path.dirname(common.HERE)
        r = subprocess.run([sys.executable, '-B', '-m', 'tower.text'], input=source('branch').encode(), cwd=root,
                           capture_output=True, timeout=120, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, l3.compile_program(progs.branch(3, 9)).stats['image'])
        self.assertRegex(r.stderr.decode(), r'A=13 P=\d+ image \d+ bytes')
        r = subprocess.run([sys.executable, '-B', '-m', 'tower.text'], input=b':main block\nfoo\nhalt\n', cwd=root,
                           capture_output=True, timeout=120, check=False)
        self.assertEqual((r.returncode, r.stdout), (1, b''))
        self.assertIn('2:1: unknown word foo', r.stderr.decode())


class Rejected(unittest.TestCase):
    """Wrong texts are reported and rejected at parse: no exception is left for the building or the running."""

    def bad(self, src, part, level=4):
        errs = errors(src, level)
        self.assertTrue(any(part in e for e in errs), (part, errs))

    def test_words(self):
        self.bad(MAIN + 'foo\nhalt\n', '2:1: unknown word foo')
        self.bad(MAIN + 'copy &a\nhalt\n', 'undefined label &a')
        self.bad(':main block\nlong! halt\n', 'missing argument 1 of long!')
        self.bad(':a data 8 0\n:main block\nlong! &a &a\nhalt\n', 'the position', level=4)
        self.bad(':a data 8 0\n:main block\nlong! &a &a\nhalt\n', 'unknown word long! (in language 3)', level=3)
        self.bad(':a data 8 0\n:main block\nhalt\n', 'unknown word block (in language 2)', level=2)
        self.assertEqual(errors(':a data 8 1\n:b data 8 0\ncopy &a &b\n', level=2), [])

    def test_arguments(self):
        d = ':a data 8 0\n:b data 8 0\n'
        self.bad(d + MAIN + 'copy &a\nhalt\n', 'missing argument 2 of copy')
        self.bad(d + MAIN + 'copy &a &b &b\nhalt\n', 'extra argument of copy')
        self.bad(d + MAIN + 'copy &a &b 5\nhalt\n', 'extra argument of copy')
        self.bad(d + MAIN + 'halt &a\n', 'extra argument of halt')
        self.bad(d + MAIN + 'emit\nhalt\n', 'missing argument 1 of emit')
        self.bad(d + MAIN + 'emit 5\nhalt\n', 'a reference &name expected, found 5')
        self.bad(d + MAIN + 'emit &a[3:3]\nhalt\n', 'outside &a')
        self.bad(d + MAIN + 'emit &a[2:9]\nhalt\n', 'outside &a')
        self.bad(d + MAIN + 'lut &hex4 &a &b\nhalt\n', 'lut hex4, argument 1: 4 bits expected, found 8')
        self.bad(d + MAIN + 'lut &hex4 &a[0:4]\nhalt\n', 'missing argument 3 of lut')
        self.bad('1 2 3\n' + d + MAIN + 'halt\n', 'unexpected 1')
        self.bad(':t table 2 4  1 2 3\n' + MAIN + 'halt\n', 'missing argument 6 of table')
        self.bad(':t table 2 4  1 2 3 99 4\n' + MAIN + 'halt\n', 'a number below 2^4')
        self.bad(':t table 2 4  1 2 3 4 5\n' + MAIN + 'halt\n', 'extra argument of table')

    def test_labels(self):
        self.bad(':a data 8 0\n:a data 4 0\n' + MAIN + 'halt\n', 'label :a is repeated')
        self.bad(MAIN + 'goto &nowhere\n', 'undefined label &nowhere')
        self.bad(':a data 8 0\n' + MAIN + 'goto &a\n', '&a is a data, not a block')
        self.bad(MAIN + 'emit &x\nhalt\n:x data 8 0\n', 'defined after its use')
        self.bad(':a data 8 0\n' + MAIN + ':z halt\n', 'label :z is before halt, which defines nothing')
        self.bad(':a data 8 0\n' + MAIN + 'halt\n:q\n', 'label :q has no word after it')
        self.bad('data 8 0\n' + MAIN + 'halt\n', 'data needs a label')
        self.bad(':a :b data 8 0\n' + MAIN + 'halt\n', 'followed by another label')
        self.bad(':hex4 data 8 0\n' + MAIN + 'halt\n', 'reserved')
        self.bad(':zero data 8 0\n' + MAIN + 'halt\n', 'reserved')
        self.bad(':dec7 data 8 0\n' + MAIN + 'halt\n', 'reserved')
        self.bad(':a-b data 8 0\n' + MAIN + 'halt\n', 'a bad label')
        self.bad(':a data 8 0\n' + MAIN + 'copy &zero &a[0:1]\nhalt\n', 'zero is read-only')
        self.bad(':a data 8 0\n:main block\n:main block\nhalt\n', 'label :main is repeated')

    def test_values(self):
        self.bad(':a data 8 256\n' + MAIN + 'halt\n', 'a number below 2^8')
        self.bad(':a data 8 "ab"\n' + MAIN + 'halt\n', 'does not fit 8 bits')
        self.bad(':a data 8 "ab\n' + MAIN + 'halt\n', 'a bad string')
        self.bad(':a data 8 "\\q"\n' + MAIN + 'halt\n', 'a bad string')
        self.bad(':a data 0 0\n' + MAIN + 'halt\n', 'a number 1..65536 expected')
        self.bad(':a data 8 0xzz\n' + MAIN + 'halt\n', 'a number below 2^8 expected')
        self.bad(":t table 1 4  'a' 'b'\n" + MAIN + 'halt\n', 'a character')
        self.bad(':t table 1 8  "ab" "c"\n' + MAIN + 'halt\n', 'a string of 2 bytes does not fit 8 bits')
        self.bad(':t table 9 1  1\n' + MAIN + 'halt\n', 'a number 1..8 expected')

    def test_widths(self):
        d = ':a data 8 0\n:b data 4 0\n:c data 9 0\n:d data 3 0\n:e data 2 0\n'
        self.bad(d + MAIN + 'copy &a &b\nhalt\n', 'copy: 8 bits expected, found 4')
        self.bad(d + MAIN + 'copy &a[0:4] &a[2:6]\nhalt\n', 'onto itself')
        self.bad(d + MAIN + 'key &b\nhalt\n', 'whole bytes')
        self.bad(d + MAIN + 'add &a &a &a\nhalt\n', 'add, the result: 9 bits expected, found 8')
        self.bad(d + MAIN + 'add &d &d &b\nhalt\n', 'whole nibbles')
        self.bad(d + MAIN + 'sub &a &b &c\nhalt\n', 'sub, the second operand')
        self.bad(d + MAIN + 'lt &a &a &e\nhalt\n', 'lt: the result needs 3 bits')
        self.bad(d + MAIN + 'eq &a &a &d\nhalt\n', 'eq, the result: 2 bits expected, found 3')
        self.bad(d + MAIN + 'shl &a &a 1\nhalt\n', 'another part of space')
        self.bad(d + MAIN + 'shl &a &b 1\nhalt\n', 'shl: 8 bits expected')
        self.bad(d + MAIN + 'if &a &main &main\n', 'if: the condition: 1 bits expected')
        self.bad(d + ':ar array 3 8\n' + MAIN + 'store &ar &b &a\nhalt\n', 'store ar, index 1: 3 bits expected, found 4')
        self.bad(d + ':t table 2 4  0 1 2 3\n' + MAIN + 'store &t &b[0:2] &b\nhalt\n', 'is a table, not an array')
        self.bad(d + MAIN + 'long@ &c &a\nhalt\n', 'the position: 128 bits expected')

    def test_blocks(self):
        d = ':a data 8 0\n'
        self.bad(d + 'emit &a\n', 'emit outside a block')
        self.bad(d + MAIN + 'emit &a\n', 'block main has no end')
        self.bad(d + MAIN + 'halt\nemit &a\n', 'emit after the end of the block main')
        self.bad(d + MAIN + 'emit &a\n:next block\nhalt\n', 'block main has no end')
        self.bad(d + MAIN + 'ret\n', 'ret outside a word')
        self.bad(d, 'the program has no block')
        self.bad('', 'the program has no block')
        self.bad(MAIN + 'call &main &main\n', '&main is a block, not a word')
        self.bad(MAIN + 'call &w &nowhere\n:w word\nret\n', 'undefined label &nowhere')
        self.bad(':s stack 3 link\n' + MAIN + 'call &w &b\n:b block\nhalt\n:w word\nret\nrec &w &s\n', 'rec: the word w is used before')
        self.bad(':s stack 3 8\nrec &w &s\n' + MAIN + 'call &w &main\n:w word\nret\n', 'rec: &s is not a stack of links')
        self.bad(':s stack 3 link\n:a data 8 0\n' + MAIN + 'push &s &a\nhalt\n', 'a stack of links, used by rec only')
        self.bad(':s stack 3 8\n:a data 4 0\n' + MAIN + 'push &s &a\nhalt\n', 'push &s: 8 bits expected, found 4')

    def test_comments_and_free_form(self):
        """Layout is free: several words in a line, a word and its arguments over lines, comments everywhere."""
        a = ':a data 8 200 :b data 8 100 :r data 9 0 :main block add &a &b &r halt'
        b = '# comment\n:a data\n  8\n  200 # the value\n:b data 8 100\n:r data 9 0\n:main block\nadd &a\n&b &r\nhalt'
        self.assertEqual(errors(a), [])
        self.assertEqual(errors(b), [])
        self.assertEqual(text.compile_text(a)[0].stats['image'], text.compile_text(b)[0].stats['image'])

    def test_no_exception_after_parse(self):
        """Mutations of accepted texts (a token deleted, doubled, replaced): what the parser accepts builds
        and lays out without any exception (the lower language has asserts: all are covered by the grammar)."""
        rnd = random.Random(2306)
        seen = [0, 0]
        for name in ('branch', 'calls', 'echo', 'and_hex', 'long_clock'):
            toks = [t.text for t in text.tokens(source(name))]
            for _ in range(40):
                t = list(toks)
                k = rnd.randrange(len(t))
                how = rnd.randrange(4)
                if how == 0:
                    del t[k]
                elif how == 1:
                    t.insert(k, t[rnd.randrange(len(t))])
                elif how == 2:
                    t[k] = rnd.choice(t)
                else:
                    t[k] = rnd.choice(['0', '1', '9', '300', '&zero', 'link', '"x"', '&main', ':q'])
                src = '\n'.join(t) + '\n'
                r = text.parse(src)
                if r.errors:
                    seen[0] += 1
                    continue
                seen[1] += 1
                try:
                    l3.compile_program(r.build)
                except MemoryError:
                    pass
        self.assertGreater(seen[0], 50)
        self.assertGreater(seen[1], 0)


# --- the dictionary on the chain (language 3 only): words and decimal numbers from stdin

NAMES = 'copy data lut table array store block word goto if call ret halt emit key stack'.split()


def dict_want(inp, names=NAMES):
    out = b''
    for tok in re.split(rb'[\x01- ]+', inp.split(b'\0')[0]):
        if not tok:
            continue
        if tok.isdigit() and tok.decode().isascii():
            out += b'#%04x\n' % (int(tok) & 0xffff)
        elif tok.decode('latin-1') in names:
            out += b'%03d\n' % names.index(tok.decode('latin-1'))
        else:
            out += b'?\n'
    return out


class Dictionary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = text.compile_text(source('dict'), level=3)[0]

    def ask(self, inp, p=None, plain=False):
        r = once(p or self.p, plain=plain, stdin=inp + b'\0tail')
        return r.out

    def test_no_language_4(self):
        """The dictionary needs only the words of language 3 (the compiler of language 3 reads it)."""
        self.assertEqual(errors(source('dict'), 3), [])

    def test_all_words(self):
        for i, w in enumerate(NAMES):
            self.assertEqual(self.ask(w.encode() + b'\n', plain=(i == 0)), b'%03d\n' % i, w)

    def test_lines(self):
        inp = b'copy data xyz 42 1234 lut longword 007 add key\n  if\tstack 12ab 65535 65536 abcdefg\n'
        self.assertEqual(self.ask(inp), dict_want(inp))
        self.assertEqual(self.ask(b''), b'')
        self.assertEqual(self.ask(b'  \n\t \r\n'), b'')
        self.assertEqual(self.ask(b'ret'), b'011\n')                 # the end of the text ends the word
        self.assertEqual(self.ask(b'goto\x01call\x1fhalt'), b'008\n010\n012\n')

    def test_numbers(self):
        """Decimal to binary, 16 bits (modulo 2^16); a number with a letter is a word."""
        nums = [0, 1, 9, 10, 99, 100, 255, 256, 999, 4095, 12345, 40000, 65535]
        inp = b' '.join(b'%d' % n for n in nums) + b' 00012 0042 65536 70000 4294967299 1x 12ab a1'
        self.assertEqual(self.ask(inp), dict_want(inp))
        self.assertEqual(self.ask(b'255'), b'#00ff\n')
        self.assertEqual(self.ask(b'12ab'), b'?\n')

    def test_not_found(self):
        """Prefixes, extensions, longer words, other bytes; a name of 6 bytes (all the width) is found."""
        inp = b'cop copyy c ifx i longword lutlut stac stack0 A COPY \xe9copy co\x7fpy \x80 ~ 1.5'
        self.assertEqual(self.ask(inp), dict_want(inp))
        src = source('dict').replace('"\\0\\0\\0\\0key"', '"\\0abcdef"')
        self.assertNotEqual(src, source('dict'))
        q = text.compile_text(src, level=3)[0]
        names = NAMES[:14] + ['abcdef', 'stack']
        inp = b'abcdef abcde abcdefg xabcdef key bcdef'
        self.assertEqual(self.ask(inp, q), dict_want(inp, names))
        self.assertEqual(dict_want(inp, names), b'014\n?\n?\n?\n?\n?\n')

    def test_long_text(self):
        rnd = random.Random(2306)
        words = NAMES + ['zz', 'copyx', '7', '65535', 'e', '~~~~~~', 'ab\x7f']
        inp = b''.join(rnd.choice(words).encode('latin-1') + rnd.choice([b' ', b'\n', b'\t', b'  \n']) for _ in range(60))
        self.assertEqual(self.ask(inp), dict_want(inp))
        intervals(self.p)


if __name__ == '__main__':
    unittest.main()
