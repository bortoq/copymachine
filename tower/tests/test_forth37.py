"""The 37 programs of the present language (tower/tests/forthc_programs.py) on the chain (23.11): `programs/forth37/*.tw`, texts of
language 3 (the subset of l3c: no new word, no change of the languages), and `programs/forth37/expected.txt`, the output of each. Here the texts and the
expected outputs are checked against forthc_programs.py, and a few small programs are built by the chain (chain.py: l3c -> [l3p] -> l2l -> seed) in both layouts (serial
and `pack`), the image prints the expected bytes on the checked emulator (a smoke test: the images of all 37 programs in both layouts, their sha256 and runs are frozen in
tower/golden/programs.jsonl and checked by long_golden.py; the long runs through the chain are in long_forth37.py). The expected output is that of the Forth program but for
`bytes` (a shift by 33 gives 0 here, the Forth language takes the amount modulo 32: the divergence is told in expected.txt and in docs/measurements/tower-forth37.md).
Run: make check-tower  or  python3 -B tower/tests/test_forth37.py"""
import os
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, HERE)
import chain
import test_l3c as t
from common import run

DIR = os.path.join(t.PROGRAMS, 'forth37')
LIMIT = 10 ** 7
SMOKE = ['stack', 'constant', 'calls']        # built here by the chain in both layouts (the cold build of all 37 takes minutes: long_golden.py has them)
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


class Images(unittest.TestCase):
    """The image of a few programs by the chain, serial and packed: it prints what is expected."""

    def run_all(self, pack):
        want = expected()
        for n in SMOKE:
            with self.subTest(n, pack=pack):
                img, P = chain.build(('pack\n' if pack else '') + source(n))
                r = run(img, 20, P, checked=True, limit=LIMIT)
                self.assertEqual((r.rc, r.out), (0, want[n]), r.err)
                self.assertLess(r.ticks, LIMIT)

    def test_serial(self):
        self.run_all(False)

    def test_packed(self):
        self.run_all(True)

    def test_packed_is_cheaper(self):
        """The packed image runs in fewer ticks than the serial one (the sum over the programs of SMOKE)."""
        ticks = {}
        for pack in (False, True):
            ticks[pack] = 0
            for n in SMOKE:
                img, P = chain.build(('pack\n' if pack else '') + source(n))
                ticks[pack] += run(img, 20, P, checked=True, limit=LIMIT).ticks
        self.assertLess(ticks[True], ticks[False])


if __name__ == '__main__':
    unittest.main()
