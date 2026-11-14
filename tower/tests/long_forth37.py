"""The 37 programs of the present language on the chain, through the programs of the chain (23.11), `make check-tower-long`: every text of programs/forth37/ goes
text of language 3 -> l3c -> l2l -> seed -> image (chain.py: serial layout, and with the planner for PACKED: the word `pack` first, l3c -> l3p -> l2l -> seed) and
the image prints the expected output (expected.txt) on the checked emulator. The images, their sha256 and the runs are also frozen in tower/golden/programs.jsonl
(long_golden.py), the images are made once for both (chain.py). The packed planner (the tool l3p made by the packed chain) gives on every text of PACKED the bytes
of the serial planner. The ticks of the runs go to REPORT (the build ticks of docs/measurements/tower-forth37.md come from the checked emulator, see there).
Run: make check-tower-long  or  python3 -B tower/tests/long_forth37.py"""
import os
import sys
import time

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import chain
import common
import test_forth37 as f
from common import run

BIG = 300 * 10 ** 6
PACKED = ['return_stack', 'constant', 'pick_roll', 'execute', 'stack', 'calls', 'shifts', 'variables', 'begin_until', 'strings']
REPORT = []         # (program, layout, ticks of the run, seconds of the build and the run)


def setUpModule():
    common.ensure_built()


class Programs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.want = f.expected()

    def one(self, name, pack):
        t0 = time.time()
        img, P = chain.build(('pack\n' if pack else '') + f.source(name))
        r = run(img, 20, P, checked=True, limit=BIG)
        self.assertEqual((r.rc, r.out), (0, self.want[name]), r.err)
        REPORT.append((name, 'pack' if pack else 'serial', r.ticks, time.time() - t0))

    def test_serial_chain(self):
        for n in f.names():
            with self.subTest(n):
                self.one(n, False)

    def test_packed_chain(self):
        for n in PACKED:
            with self.subTest(n):
                self.one(n, True)

    def test_packed_planner(self):
        """The packed l3p (made by the packed chain) plans the text of l3c for every program of PACKED as the serial l3p does."""
        img, A, P = chain.tool('l3p', pack=True)
        for n in PACKED:
            with self.subTest(n):
                l2 = chain.step('l3c', 'l3c', b'pack\n' + f.source(n).encode('latin-1') + b'\0')
                r = run(img, A, P, checked=False, limit=BIG, stdin=l2)
                self.assertEqual((r.rc, r.out), (0, chain.step('l3p', 'l3p', l2)))


def tearDownModule():
    for row in REPORT:
        print('forth37 %-16s %-6s run %7d ticks  %.1f s' % row)
    for lay in ('serial', 'pack'):
        rows = [r for r in REPORT if r[1] == lay]
        if rows:
            print('forth37 %s: %d programs, run %d ticks' % (lay, len(rows), sum(r[2] for r in rows)))


if __name__ == '__main__':
    unittest.main()
