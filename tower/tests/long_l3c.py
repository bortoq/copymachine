"""Long tests of the compiler of language 3 (23.9, part 2), `make check-tower-long` (not in check-fast): the tools of the chain are
compiled by l3c (text of language 3 -> l3c -> l2l -> seed -> image) and the images work. The chain tool l3c agrees with the Python reference
(l3ctext) on the texts of seed, l2c and l2l (hoisted: data outside the blocks); the seed made by the chain turns seed.l1 into the
image of the seed (the fixed point of 23.7, now through the serial layout); the label tool l2l made by the chain turns hello_names.l2
into what the Python reference gives; and 300 texts spoiled at random give the same bytes and reports in the chain and in Python.
Run: make check-tower-long  or  python3 -B tower/tests/long_l3c.py"""
import os
import random
import re
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import l1text
import l2ltext
import l3ctext
import test_l3c as t
from common import run

BIG = 200 * 10 ** 6


class Long(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t.setUpModule()
        cls.tool = t.tool()
        cls.l2l = t.compiled('l2l').stats
        cls.seed = t.compiled('seed').stats
        cls.made = {}

    def make(self, name):
        """The image of a tool made by the chain from its text of language 3 (cached)."""
        if name not in self.made:
            r = t.l3c(t.hoisted(name), limit=BIG)
            self.assertEqual(r.rc, 0, r.err)
            self.assertEqual(r.out, l3ctext.encode(t.hoisted(name))[0])
            a = run(self.l2l['image'], self.l2l['A'], self.l2l['P'], checked=True, limit=BIG, stdin=r.out + r.out)
            self.assertEqual(a.rc, 0, a.err)
            b = run(self.seed['image'], self.seed['A'], self.seed['P'], checked=True, limit=BIG, stdin=a.out)
            self.assertEqual(b.rc, 0, b.err)
            self.assertEqual(b.out, t.image_of(r.out))
            self.made[name] = b.out
        return self.made[name]

    def test_texts_of_the_tools(self):
        """l3c and the reference agree on seed.tw, l2c.tw and l2l.tw (the sizes of the layers are told in docs/measurements/tower.md)."""
        for name in ('seed', 'l2c', 'l2l'):
            with self.subTest(name):
                src = t.hoisted(name)
                r = t.l3c(src, limit=BIG)
                want, err = l3ctext.encode(src)
                self.assertIsNone(err)
                self.assertEqual((r.rc, r.out), (0, want))

    def test_seed_made_by_the_chain(self):
        """The seed compiled by l3c (serial layout) turns seed.l1 into the image of the seed: the same bytes as the seed of 23.7."""
        img = self.make('seed')
        src = t.read('seed.l1', 'rb') + b'\0'
        r = run(img, 20, 2, checked=True, limit=BIG, stdin=src)
        self.assertEqual(r.rc, 0, r.err)
        self.assertEqual(r.out, self.seed['image'])
        self.assertEqual(r.out, l1text.encode(src)[0])

    def test_l2l_made_by_the_chain(self):
        """The label tool compiled by l3c reads hello_names.l2 twice and writes what the reference writes."""
        img = self.make('l2l')
        s = t.read('hello_names.l2', 'rb')
        r = run(img, 20, 2, checked=True, limit=BIG, stdin=s + b'\0' + s + b'\0')
        self.assertEqual(r.rc, 0, r.err)
        self.assertEqual(r.out, l2ltext.encode(s, twice=True)[0])

    def test_mutations(self):
        rng = random.Random(2305)
        junk = ['&zz', '&a[', '&a[1:', '&a[3:2]', '"x', '"x"y', '1x', '0', '99999999', '&', '&a]', 'block', 'data', 'halt', 'ret', ':', '::a',
                ':1a', '#', '&main', '&a[0]', '"\\q"', '"\\n"', '&add4', '&sub4', '&hex4', 'zero', '&zero', 'data 8 0', 'table 1 1 5 6 7',
                ':zz table 1 1 1', 'call', 'if', 'lut', 'store', 'add', 'shl', 'key', 'emit']
        bases = [t.hoisted(n) for n in ('echo', 'branch', 'and_hex', 'loop_digits', 'array', 'arith8')]
        for _ in range(300):
            toks = re.split(r'(\s+)', rng.choice(bases))
            for _ in range(rng.choice((1, 1, 2, 3))):
                idx = [j for j in range(len(toks)) if toks[j].strip()]
                if not idx:
                    break
                j, m = rng.choice(idx), rng.randrange(4)
                if m == 0:
                    toks[j] = rng.choice(junk)
                elif m == 1:
                    toks[j] = ''
                elif m == 2:
                    toks.insert(j, rng.choice(junk) + ' ')
                else:
                    toks = toks[:j]
                    break
            src = ''.join(toks)
            r = t.l3c(src)
            want, err = l3ctext.encode(src)
            self.assertEqual(r.out, want, src)
            self.assertEqual('l3c: ' in r.err, err is not None, (src, r.err))


if __name__ == '__main__':
    unittest.main()
