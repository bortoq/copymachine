"""Long tests of the tools of the chain compiled by the chain (23.9, part 2; 23.10), `make check-tower-long` (not in check-fast): what is not frozen in tower/golden.
The outputs of the passes, the images of the programs and the fixed points (l3c builds its own text, serial and packed) are in long_golden.py; the texts of language 1
of l3c, l3p, l4c are in long_l1_current.py. Here, with no Python reference on the path (chain.py makes every tool):
- the label tool l2l, compiled by l3c (text of language 3 -> l3c -> l2l -> seed), turns hello_names.l2 into what the l2l of the chain (the seed on l2l.l1) gives;
- the packed tools (`pack` first: l3c -> l3p -> l2l -> seed; P = 3) work: the packed l3p (A = 20, P = 3, under LIMIT bits) gives on the output of l3c for l3c.tw
  the bytes of the serial l3p, the packed l3c gives the text of language 2 of the serial l3c, the packed seed turns seed.l1 into the image of the seed.
Run: make check-tower-long  or  python3 -B tower/tests/long_l3c.py"""
import os
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, HERE)
import chain
import common
import tables
import test_l3c as t
from common import run

BIG = 300 * 10 ** 6


def setUpModule():
    common.ensure_built()


class Compiled(unittest.TestCase):
    def test_l2l_made_by_the_chain(self):
        """The label tool compiled by l3c (the serial layout) turns hello_names.l2 into the text of language 1 which the l2l of the chain gives."""
        img, P = chain.build(t.hoisted('l2l'))
        hn = t.read('hello_names.l2', 'rb')
        r = run(img, 20, P, checked=True, limit=BIG, stdin=hn + b'\0' + hn + b'\0')
        want = chain.run_pass('l2l', hn + b'\0' + hn + b'\0')
        self.assertEqual((r.rc, r.out), (0, want.out))
        self.assertTrue(want.out)


class Packed(unittest.TestCase):
    def test_packed_l3p(self):
        """The packed planner (made by the packed chain) works as the serial one: the same bytes on the output of l3c for l3c.tw in pack mode."""
        img, A, P = chain.tool('l3p', pack=True)
        self.assertEqual((A, P), (20, 3))
        self.assertLess(len(img) * 8, tables.LIMIT)
        l2 = chain.step('l3c', 'l3c', b'pack\n' + t.read('l3c.tw', 'rb') + b'\0')
        r = run(img, A, P, checked=False, limit=BIG, stdin=l2)
        self.assertEqual((r.rc, r.out), (0, chain.step('l3p', 'l3p', l2)))

    def test_packed_l3c(self):
        """The packed l3c gives the text of language 2 of the serial l3c on texts of the tools and of a program, in pack mode."""
        img, A, P = chain.tool('l3c', pack=True)
        self.assertEqual((A, P), (20, 3))
        for name in ('seed', 'echo', 'branch'):
            src = b'pack\n' + t.hoisted(name).encode() + b'\0'
            r = run(img, A, P, checked=False, limit=BIG, stdin=src)
            self.assertEqual((r.rc, r.out), (0, chain.run_pass('l3c', src).out), name)

    def test_packed_seed(self):
        """The packed seed turns seed.l1 into the image of the seed (the first image is made by l1text, as hex0)."""
        img, P = chain.build('pack\n' + t.hoisted('seed'))
        src = t.read('seed.l1', 'rb') + b'\0'
        r = run(img, 20, P, checked=True, limit=BIG, stdin=src)
        self.assertEqual((P, r.rc, r.out), (3, 0, chain.image('seed')))


if __name__ == '__main__':
    unittest.main()
