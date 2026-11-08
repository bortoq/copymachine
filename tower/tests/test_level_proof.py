"""Proof of a level (23.21, 7.2.35): the word `copy n d s` of language 2 keeps its promise (tests/levelproof.py, the report
docs/measurements/level-proof.md). The chain l2c -> seed -> checked emulator runs every case; small windows here, the large
sweeps are in exp_level_proof.py.
Run: make check-tower  or  python3 -B tower/tests/test_level_proof.py"""
import os
import random
import sys

sys.dont_write_bytecode = True
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import levelproof as L


def setUpModule():
    global tools
    tools = L.Tools()


class Level(unittest.TestCase):
    def test_exhaustive_windows(self):
        """All 744 valid (n, d, s) of a 16-bit window, at the bottom of A=8, touching S at A=9, across 2^9 at A=10; the
        routing of every output bit is read off six contents (zeros, ones, four planes of the position number)."""
        for A, b in ((8, 192), (9, 2 ** 9 - 6 - 16), (10, 2 ** 9 - 8)):
            with self.subTest(A=A, b=b):
                n, bad = L.sweep(tools, A, b, 16, L.valid_cases(16, b))
                self.assertEqual((n, bad), (744, []))

    def test_every_width(self):
        """The same chain at every A from 8 to 20 (S up to 1 048 570): windows at the bottom, in the middle (2^(A-1)) and at
        the top (touching S), 6 random cases each; two random contents besides the routing."""
        rnd = random.Random(2321)
        for A in range(8, 21):
            S = 2 ** A - 6
            for b in sorted({24 * A, max(24 * A, 2 ** (A - 1) - 8), S - 24}):
                cases = rnd.sample(list(L.valid_cases(24, b)), 6)
                n, bad = L.sweep(tools, A, b, 24, cases, rnd=rnd, nrandom=2)
                self.assertEqual((A, b, n, bad), (A, b, 6, []))

    def test_overlap_is_not_in_the_domain(self):
        """The checked emulator rejects what the promise excludes: overlapping intervals and d = s (n > 0)."""
        for n, d, s in list(L.overlapping_cases(16, 192))[::53] + [(3, 200, 200), (1, 193, 193)]:
            rc, err = L.rejected(tools, 8, 192, 16, n, d, s)
            self.assertNotEqual(rc, 0, (n, d, s))
            self.assertIn('overlap', err)

    def test_nop(self):
        """n = 0 changes nothing for d, s at the edges of the space (processor, texts, S-1); d = s = S is two channel codes."""
        S = 250
        edge = (0, 1, 31, 32, 63, 64, 191, 192, 193, 247, 248, 249, S - 1, S)
        for d in edge:
            for s in edge:
                rc, same = L.nop_case(tools, 8, d, s)
                if d == s == S:
                    self.assertNotEqual(rc, 0)
                else:
                    self.assertEqual((rc, same), (0, True), (d, s))

    def test_definition_text(self):
        """What l2c writes for `c n d s` is `r d d+n s s+n` for every pattern of a nibble step at each of the five
        positions (the digits and the carry), and for random numbers (sums modulo 2^20)."""
        rnd = random.Random(238)
        trip = L.carry_triples() + [(rnd.getrandbits(20), rnd.getrandbits(20), rnd.getrandbits(20)) for _ in range(300)]
        trip += [(0, 0, 0), (1, 0xfffff, 0), (0xfffff, 1, 0xfffff), (0x10000, 0xf0000, 0xfffff)]
        self.assertEqual(L.l2c_lines(tools, trip), [])
        # a one-line check, as the text of the word
        self.assertEqual(tools.l2('c 8 10 20\n'), b'r 10 18 20 28\n\0')

    def test_seed_encoding(self):
        """The seed writes each field as the low A bits, the lowest first, for A = 1..24."""
        self.assertEqual(L.seed_encoding(tools, random.Random(7)), [])

    def test_wrong_words_are_found(self):
        """The test sees a wrong definition: a shifted destination or source, a shorter or longer copy, swapped sides."""
        n, d, s = 3, 196, 204
        for m in ((3, 197, 204), (2, 196, 204), (3, 196, 205), (4, 196, 204), (3, 204, 196)):
            self.assertIsNotNone(L.check_case(tools, 8, 192, 16, n, d, s, text=L.program(8, 192, 16, *m)), m)
        self.assertIsNone(L.check_case(tools, 8, 192, 16, n, d, s))


if __name__ == '__main__':
    unittest.main()
