"""The long tier of the frozen checks of the passes (25.7.1, see test_golden.py): l3p and l4c (their images are made by the chain itself: l3c -> l2l -> seed),
and the dear inputs of the others (the tools as inputs of l3c, tables of 1024 labels). The expected values are tower/golden/<pass>.jsonl (entries marked "long").
Run: make check-tower-long  or  python3 -B tower/tests/long_golden.py"""
import os
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_golden as g


def setUpModule():
    g.setUpModule()


class LongGolden(unittest.TestCase):
    def test_seed(self):
        g.check_tier(self, 'seed', True)

    def test_l2c(self):
        g.check_tier(self, 'l2c', True)

    def test_l2l(self):
        g.check_tier(self, 'l2l', True)

    def test_l3c(self):
        g.check_tier(self, 'l3c', True)

    def test_l3p(self):
        g.check_tier(self, 'l3p', True)

    def test_l4c(self):
        g.check_tier(self, 'l4c', True)


if __name__ == '__main__':
    unittest.main()
