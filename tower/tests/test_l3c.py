"""Tests of the compiler of language 3 (23.9, part 2): `programs/l3c.tw` is a program of the chain. It reads a text of language 3 and writes a text of
language 2 with labels and a zero byte, which `l2l` (23.9, part 1) and then the seed (23.7) turn into the image: text of language 3 -> l3c -> l2l -> seed ->
image. The layout is serial (a row of the text is a layer of its own, nothing is packed). Here: the tables and the sizes in the text of l3c.tw, and the
images made by the chain (chain.py) which run on the checked emulator and print what the images of the Python compiler (text.py) print. The outputs of l3c
(the texts of language 2, the reports of the wrong texts) are frozen in tower/golden/l3c.jsonl (test_golden.py); the fixed point (l3c builds its own text)
is in long_golden.py; the texts of language 1 are checked in test_l1_current.py. The long runs are in long_l3c.py.
Run: make check-tower  or  python3 -B tower/tests/test_l3c.py"""
import os
import re
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import chain
import common
import tables
import text
from common import run
from golden_programs import hoist

PROGRAMS = os.path.join(common.HERE, 'programs')
LIMIT = 40 * 10 ** 6
SMALL = ['echo', 'branch', 'add16_hex', 'and_hex', 'arith8', 'arith16', 'array', 'loop_digits']      # the subset, small
STDIN = {'echo': b'hello, chain\0', 'arith8': b'\xa5\x3c', 'arith16': b'\x12\x34\x56\x78'}


def setUpModule():
    common.ensure_built()


def read(name, mode='r'):
    with open(os.path.join(PROGRAMS, name), mode, encoding=None if 'b' in mode else 'utf-8') as h:
        return h.read()


def compiled(name):
    p, errs = text.compile_text(read(name + '.tw'))
    assert not errs, errs
    return p


def hoisted(name):
    return hoist(read(name + '.tw'))


class Texts(unittest.TestCase):
    """The text of l3c.tw (no emulator)."""

    def test_tables_are_current(self):
        """The numbers of the tables in l3c.tw are what tables.py makes."""
        self.assertEqual(tables.generated_block(read('l3c.tw')), tables.tables_text())

    def test_tool_is_in_its_places(self):
        """The names of data, tables and arrays of l3c.tw are at most half of the places of l3c (1020); its image (made by the chain) is under LIMIT bits (the tables of the library stand there)."""
        n = len(re.findall(r'^:\w+ (?:data|table|array)\b', read('l3c.tw'), re.M))
        self.assertGreater(n, 255)
        self.assertLessEqual(2 * n, tables.MAXSYM)
        self.assertLess(len(chain.image('l3c')) * 8, tables.LIMIT)

    def test_capacity_in_the_texts(self):
        """The places of names: 1024 in l3c.tw (six arrays of 2^10, nsym over 11 bits), 1020 for a user; 1024 labels in l2l.tw. The tables of 1020 and 1021 names and of 1024
        and 1025 labels are frozen in tower/golden (l3c.jsonl names-*, l2l.jsonl labels-*)."""
        self.assertEqual(tables.MAXSYM + 4, 1 << 10)                 # with add4, sub4, hex4, zero they fill the 1024 places
        src = read('l3c.tw')
        for n in ('sna', 'snb', 'stg', 'ski', 'sad', 'sin'):
            self.assertIn(':%s array 10 ' % n, src)
        for n in ('nameh', 'namet', 'tags', 'vals', 'hd', 'nx'):
            self.assertIn(':%s array 10 ' % n, read('l2l.tw'))


class Images(unittest.TestCase):
    """The images made by the chain run as the images of the Python compiler (the layout is not the same, the output is)."""

    def test_programs(self):
        for name in SMALL:
            with self.subTest(name):
                img = chain.build(hoisted(name))[0]            # a refusal of a pass of the chain is an AssertionError
                py = compiled(name)
                a = run(img, 20, 2, checked=True, limit=LIMIT, stdin=STDIN.get(name, b''))
                b = run(py.stats['image'], py.stats['A'], py.stats['P'], checked=True, limit=LIMIT, stdin=STDIN.get(name, b''))
                self.assertEqual((a.rc, b.rc), (0, 0), (a.err, b.err))
                self.assertEqual(a.out, b.out)
                self.assertTrue(a.out)

    def test_copy_with_a_channel(self):
        """The rows of a copy with a channel are those of emit and key: stdin to stdout through a part of space; the output is the same."""
        a = run(chain.build(':b data 16 0\n:main block\ncopy &b[0:8] 1048571\ncopy &b[8:16] 1048571\ncopy 1048572 &b\n'
                            'copy 1048572 &b[8:16]\nhalt\n')[0], 20, 2, checked=True, limit=LIMIT, stdin=b'xy')
        self.assertEqual((a.rc, a.out), (0, b'xyy'))

    def test_calls_and_stores(self):
        """A word with call and ret, an array written by store and read by lut, if, a string, shl and shr, lt eq band sub."""
        src = ''':msg data 24 "ab\\n"
:t table 2 4 5 6 7 8
:x array 3 4
:i data 3 0
:v data 4 0
:o data 4 0
:r data 3 0
:s data 5 0
:q data 1 0
:n data 8 0
:sh data 8 0
:h1 data 8 0
:h2 data 8 0
:main block
emit &msg[0:8]
copy &i[0:2] &msg[1:3]
call &w &m2
:m2 block
lt &o &v &r
eq &o &v &q
sub &o &v &s
shl &msg[0:8] &sh 3
shr &msg[0:8] &n 2
lut &hex4 &o &h1
lut &hex4 &s[0:4] &h2
emit &h1
emit &h2
if &q &m3 &m4
:m3 block
emit &msg[8:16]
halt
:m4 block
emit &msg[16:24]
halt
:w word
lut &t &i[0:2] &v
store &x &i &v
lut &x &i &o
ret
'''
        a = run(chain.build(src)[0], 20, 2, checked=True, limit=LIMIT)
        py, errs = text.compile_text(src)
        self.assertEqual(errs, [])
        b = run(py.stats['image'], py.stats['A'], py.stats['P'], checked=True, limit=LIMIT)
        self.assertEqual((a.rc, a.out), (0, b.out))
        self.assertEqual(a.out[:1], b'a')
        self.assertGreater(len(a.out), 3)


if __name__ == '__main__':
    unittest.main()
