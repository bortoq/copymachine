"""The long tier of the frozen checks of the passes (25.7.1, see test_golden.py): l3p and l4c (their images are made by the chain itself: l3c -> l2l -> seed),
and the dear inputs of the others (the tools as inputs of l3c, tables of 1024 labels). The expected values are tower/golden/<pass>.jsonl (entries marked "long").
The same for the whole chains of the programs (tower/golden/programs.jsonl, golden_programs.py) and the fixed points of l3c: the image of l3c turns l3c.tw
into l3c.l1 again; with the planner (`pack`) the packed l3c builds the same text of language 2 as the serial one (no Python on that path).
The dearest entries ("tier": "full") are in full_golden.py (make check-golden-full), not here. The images of the passes come from chain.py.
Run: make check-tower-long  or  python3 -B tower/tests/long_golden.py"""
import os
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import golden_programs
import test_golden as g


def setUpModule():
    g.setUpModule()
    golden_programs.start()


class LongGolden(unittest.TestCase):
    def test_seed(self):
        g.check_tier(self, 'seed', 'long')

    def test_l2c(self):
        g.check_tier(self, 'l2c', 'long')

    def test_l2l(self):
        g.check_tier(self, 'l2l', 'long')

    def test_l3c(self):
        g.check_tier(self, 'l3c', 'long')

    def test_l3p(self):
        g.check_tier(self, 'l3p', 'long')

    def test_l4c(self):
        g.check_tier(self, 'l4c', 'long')

    def test_programs(self):
        golden_programs.check_tier(self, 'long')

    def test_fixed_points(self):
        golden_programs.check_fixed(self)


if __name__ == '__main__':
    unittest.main()
