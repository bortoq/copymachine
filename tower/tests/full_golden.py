"""The full tier of the frozen checks (25.7.3.2): the dearest entries of tower/golden (the field "tier": "full" with "long": true) which are not in the nightly run
(long_golden.py has the rest of the long tier): the programs whose images are 8000 bytes or more or whose run is cut at 10 ** 7 ticks (programs.jsonl) and the tables of
1020 and 1021 labels in the pass l3c (l3c.jsonl). Nothing is dropped from tower/golden: the entries only live here. Their images are made by the chain itself (chain.py).
Run: make check-golden-full  or  python3 -B tower/tests/full_golden.py   (not in check-fast, check-tower-long or the nightly run; about 4 minutes on one CPU)"""
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
    golden_programs.start(with_fixed=False)


class FullGolden(unittest.TestCase):
    def test_l3c(self):
        g.check_tier(self, 'l3c', 'full')

    def test_programs(self):
        golden_programs.check_tier(self, 'full')


if __name__ == '__main__':
    unittest.main()
