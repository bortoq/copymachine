"""Proof of a level (23.21), the large sweeps (in check-tower-long: 408 s on 12 cores; the numbers are in docs/measurements/level-proof.md): every
valid (n, d, s) of 56-bit windows at four values of A, all (d, s) of n = 0 at A=8, all overlaps of a 16-bit window, 200 000
random triples through l2c.
Run: python3 -B tower/tests/exp_level_proof.py"""
import os
import random
import sys
import time

sys.dont_write_bytecode = True
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concurrent.futures import ThreadPoolExecutor

import levelproof as L

THREADS = min(12, os.cpu_count() or 4)


def setUpModule():
    global tools
    tools = L.Tools()


def say(*a):
    print(*a, file=sys.stderr, flush=True)


class Sweeps(unittest.TestCase):
    def test_windows(self):
        """56-bit windows (valid cases: 29 000 each), ten contents each: bottom of A=8, touching S at A=9, across 2^9 at A=10 and
        across 2^11 at A=12."""
        rnd = random.Random(2321)
        for A, b in ((8, 192), (9, 2 ** 9 - 6 - 56), (10, 2 ** 9 - 28), (12, 2 ** 11 - 28)):
            t = time.time()
            n, bad = L.sweep(tools, A, b, 56, L.valid_cases(56, b), procs=THREADS, nrandom=2)
            say('A=%d S=%d b=%d W=56: %d cases x %d contents, %.0f s' % (A, 2 ** A - 6, b, n, len(L.contents(56, rnd, 2)), time.time() - t))
            self.assertEqual(bad, [])

    def test_overlaps(self):
        """All overlapping cases of a 16-bit window at A=8 (and d = s) are rejected by the checked emulator."""
        cases = list(L.overlapping_cases(16, 192)) + [(n, d, d) for n in range(1, 17) for d in range(192, 192 + 17 - n)]
        with ThreadPoolExecutor(THREADS) as ex:
            res = list(ex.map(lambda c: L.rejected(tools, 8, 192, 16, *c), cases))
        say('overlaps: %d cases' % len(cases))
        self.assertTrue(all(rc != 0 and 'overlap' in e for rc, e in res))

    def test_nop(self):
        """n = 0 for all (d, s) in [0, S]^2 at A=8: 63 001 cases, d = s = S excluded by the contract (two channel codes)."""
        S = 250
        cases = [(d, s) for d in range(S + 1) for s in range(S + 1)]
        with ThreadPoolExecutor(THREADS) as ex:
            res = list(ex.map(lambda c: L.nop_case(tools, 8, *c), cases))
        say('n = 0: %d cases' % len(cases))
        for (d, s), (rc, same) in zip(cases, res, strict=True):
            if d == s == S:
                self.assertNotEqual(rc, 0)
            else:
                self.assertEqual((rc, same), (0, True), (d, s))

    def test_l2c_numbers(self):
        """200 000 random triples of 20-bit numbers and all nibble patterns through l2c, in batches of 5 000 lines."""
        rnd = random.Random(238)
        trip = L.carry_triples() + [(rnd.getrandbits(20), rnd.getrandbits(20), rnd.getrandbits(20)) for _ in range(200000)]
        for i in range(0, len(trip), 5000):
            self.assertEqual(L.l2c_lines(tools, trip[i:i + 5000]), [])


if __name__ == '__main__':
    unittest.main()
