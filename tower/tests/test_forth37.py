"""The 37 programs of the present language (tower/tests/forthc_programs.py) on the chain (23.11): `programs/forth37/*.tw`, texts of
language 3 (the subset of l3c: no new word, no change of the languages), and `programs/forth37/expected.txt`, the output of each. Every program is
built by the references of the chain (l3ctext, l2ltext, l1text: text -> image) in both layouts (serial and `pack`) and the image prints the
expected bytes on the checked emulator; a few small ones are also built by the programs of the chain (l3c -> l2l -> seed on the emulator, no Python
compiler); the long runs of all 37 through the chain are in long_forth37.py. The expected output is that of the Forth program but for `bytes`
(a shift by 33 gives 0 here, the Forth language takes the amount modulo 32: the divergence is told in expected.txt and in
docs/measurements/tower-forth37.md). Its outputs are compared with expected.txt.
Run: make check-tower  or  python3 -B tower/tests/test_forth37.py"""
import os
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import l3ctext
import l5
import test_l3c as t
from common import run

DIR = os.path.join(t.PROGRAMS, 'forth37')
LIMIT = 10 ** 7
SMALL = ['return_stack', 'constant', 'pick_roll', 'execute', 'stack', 'calls']      # also built by the programs of the chain here
DIVERGENT = {'bytes'}


def names():
    return sorted(f[:-3] for f in os.listdir(DIR) if f.endswith('.tw'))


def source(name):
    with open(os.path.join(DIR, name + '.tw'), encoding='utf-8') as h:
        return h.read()


def expected():
    out = {}
    with open(os.path.join(DIR, 'expected.txt'), encoding='utf-8') as h:
        for line in h:
            if line.strip() and not line.startswith('#'):
                n, v = line.split()
                out[n] = bytes.fromhex(v)
    return out


def setUpModule():
    t.setUpModule()


class Texts(unittest.TestCase):
    def test_all_37(self):
        """37 programs, each with an output; the outputs are those of forthc_programs.py (but `bytes`)."""
        want = expected()
        self.assertEqual(len(names()), 37)
        self.assertEqual(sorted(want), names())
        ref = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, ref)
        try:
            import forthc_programs as fp
        finally:
            sys.path.remove(ref)
        self.assertEqual(sorted(n.replace('_', '-') for n in names()), sorted(set(fp.PROGRAMS) | set(fp.EXPECTED)))
        for n, (_, out) in fp.EXPECTED.items():
            if n.replace('-', '_') not in DIVERGENT:
                self.assertEqual(want[n.replace('-', '_')], out, n)

    def test_in_the_subset(self):
        """Each text is a text of the subset of l3c: the reference takes it, its image fits A = 20, the data come before the code (pack mode)."""
        for n in names():
            with self.subTest(n):
                src = source(n)
                self.assertTrue(src.startswith('# '))
                for pack in (False, True):
                    out, err = l3ctext.encode(('pack\n' if pack else '') + src)
                    self.assertIsNone(err)
                    self.assertTrue(out)


class Images(unittest.TestCase):
    """The image of each program by the references of the chain, serial and packed: it prints what is expected."""

    def run_all(self, pack):
        want = expected()
        for n in names():
            with self.subTest(n, pack=pack):
                img, P = l5.chain_image(('pack\n' if pack else '') + source(n))
                r = run(img, 20, P, checked=True, limit=LIMIT)
                self.assertEqual((r.rc, r.out), (0, want[n]), r.err)
                self.assertLess(r.ticks, LIMIT)

    def test_serial(self):
        self.run_all(False)

    def test_packed(self):
        self.run_all(True)

    def test_packed_is_cheaper(self):
        """The packed image runs in fewer ticks than the serial one (the sum over the 37 programs)."""
        ticks = {}
        for pack in (False, True):
            ticks[pack] = 0
            for n in names():
                img, P = l5.chain_image(('pack\n' if pack else '') + source(n))
                ticks[pack] += run(img, 20, P, checked=True, limit=LIMIT).ticks
        self.assertLess(ticks[True], ticks[False])


class Chain(unittest.TestCase):
    """Small programs through the programs of the chain: text of language 3 -> l3c -> l2l -> seed -> image."""

    @classmethod
    def setUpClass(cls):
        cls.l2l = t.compiled('l2l').stats
        cls.seed = t.compiled('seed').stats

    def test_small(self):
        want = expected()
        for n in SMALL:
            with self.subTest(n):
                src = source(n)
                r = t.l3c(src)
                self.assertEqual((r.rc, r.out), (0, l3ctext.encode(src)[0]), r.err)
                a = run(self.l2l['image'], self.l2l['A'], self.l2l['P'], checked=True, limit=t.LIMIT, stdin=r.out + r.out)
                self.assertEqual(a.rc, 0, a.err)
                b = run(self.seed['image'], self.seed['A'], self.seed['P'], checked=True, limit=t.LIMIT, stdin=a.out)
                self.assertEqual(b.rc, 0, b.err)
                self.assertEqual(b.out, t.image_of(r.out))
                c = run(b.out, 20, 2, checked=True, limit=LIMIT)
                self.assertEqual((c.rc, c.out), (0, want[n]))


if __name__ == '__main__':
    unittest.main()
