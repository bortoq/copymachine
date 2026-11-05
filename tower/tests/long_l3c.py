"""Long tests of the compiler of language 3 (23.9, part 2), `make check-tower-long` (not in check-fast): the tools of the chain are
compiled by l3c (text of language 3 -> l3c -> l2l -> seed -> image) and the images work. The chain tool l3c agrees with the Python reference
(l3ctext) on the texts of seed, l2c and l2l (hoisted: data outside the blocks); the seed made by the chain turns seed.l1 into the
image of the seed (the fixed point of 23.7, now through the serial layout); the label tool l2l made by the chain turns hello_names.l2
into what the Python reference gives; 300 texts spoiled at random give the same bytes and reports in the chain and in Python; and
the FIXED POINT (23.9, part 3): l3c compiles its own text. The seed and the label tool are built on the emulator from seed.l1 and
l2l.l1 (no Python compiler on that path); the text of language 1 of l3c (programs/l3c.l1, made once with the Python image of the tool
and the chain) gives the image of l3c, and that image (l3c -> l2l -> seed) builds from l3c.tw the same text l3c.l1 and the same image, byte for
byte; the text of language 2 which it writes is what the reference gives, and so is the Python image. The names of l3c fill its table (1020 places) and the 1021st is bad label.
Run: make check-tower-long  or  python3 -B tower/tests/long_l3c.py"""
import os
import random
import re
import sys
import time

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
REPORT = []         # (step, ticks, seconds) of the fixed point, printed at the end of the run (the numbers of docs/measurements/tower.md)


def step(name, image, A, P, stdin):
    """One run on the checked emulator: the output; the ticks and the seconds go to REPORT."""
    t0 = time.time()
    r = run(image, A, P, checked=True, limit=BIG, stdin=stdin)
    REPORT.append((name, r.ticks, time.time() - t0))
    assert r.rc == 0 and r.ticks < BIG, (name, r.err)
    return r.out


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


class FixedPoint(unittest.TestCase):
    """23.9, part 3: l3c builds itself (text of language 3 -> l3c -> l2l -> seed -> image) and the image it builds is the one that built it."""

    @classmethod
    def tearDownClass(cls):
        for name, ticks, sec in REPORT:
            sys.stderr.write('%-28s %12d ticks %7.1f s\n' % (name, ticks, sec))

    def chain(self, tag, l3c, P, src):
        """text of language 3 -> l3c (A = 20, P) -> l2l (the text twice) -> seed -> the image; returns the three outputs."""
        l2 = step(tag + ' l3c', l3c, 20, P, src + b'\0')
        l1 = step(tag + ' l2l', self.l2l_img, self.l2l_st['A'], self.l2l_st['P'], l2 + l2)
        return l2, l1, step(tag + ' seed', self.seed_img, self.seed_st['A'], self.seed_st['P'], l1)

    def test_fixed_point(self):
        src = t.read('l3c.tw', 'rb')
        want = l3ctext.encode(src)
        self.assertIsNone(want[1])
        l3c_l1 = t.read('l3c.l1', 'rb') + b'\0'
        # no Python on this path: seed.img(l3c.l1) is the image of l3c (A = 20, P = 2, serial layout); it builds l3c.l1 again and the same image
        img1 = step('seed on l3c.l1', self.seed_img, self.seed_st['A'], self.seed_st['P'], l3c_l1)
        self.assertLess(len(img1) * 8, 1 << 20)
        l2, l1, img2 = self.chain('l3c (chain image)', img1, 2, src)
        self.assertEqual(l2, want[0])
        self.assertEqual(l1, l3c_l1)
        self.assertEqual(img2, img1)
        # the Python image of l3c (packed layout, P = 3) writes the same text of language 2: the first image was made by it
        self.assertEqual(step('l3c (Python image) l3c', l3ctext.tool_image(), 20, 3, src + b'\0'), want[0])
        # the tool the chain built works as the tool of Python: a few texts
        for name in ('echo', 'branch', 'array'):
            text = t.hoisted(name).encode()
            self.assertEqual(step('chain l3c on ' + name, img1, 20, 2, text + b'\0'), l3ctext.encode(text)[0])

    def test_all_the_names(self):
        """1020 names of a user fit in the table of l3c (and 4 of the tool), the 1021st is bad label: the same bytes as the reference."""
        for n, bad in ((1020, False), (1021, True)):
            src = ''.join(':a%d data 1 0\n' % i for i in range(n)) + ':main block\nhalt\n'
            r = run(self.tool_image, 20, 3, checked=False, limit=BIG, stdin=src.encode() + b'\0')
            want, err = l3ctext.encode(src)
            self.assertEqual(r.out, want)
            self.assertEqual((err, 'l3c: bad label' in r.err), ('lab', True) if bad else (None, False))

    @classmethod
    def setUpClass(cls):
        t.setUpModule()
        cls.tool_image = t.tool()['image']
        # the seed and the label tool without Python compilers: seed.l1 -> (the Python encoder, once) seed.img; l2l.l1 -> seed -> l2l.img
        cls.seed_st, cls.l2l_st = t.compiled('seed').stats, t.compiled('l2l').stats
        cls.seed_img = l1text.encode(t.read('seed.l1', 'rb') + b'\0')[0]
        assert cls.seed_img == cls.seed_st['image']
        cls.l2l_img = step('seed on l2l.l1', cls.seed_img, cls.seed_st['A'], cls.seed_st['P'], t.read('l2l.l1', 'rb') + b'\0')
        assert cls.l2l_img == cls.l2l_st['image']


if __name__ == '__main__':
    unittest.main()
