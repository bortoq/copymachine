"""The 37 programs of the present language as Forth texts on the chain (23.15, part 1), `make check-tower-long`: every text of
programs/forth37/*.fs goes Forth text -> forth -> l3c -> l2l -> seed -> image on the emulator (every tool is made by the chain from its text of
language 1; no Python compiler and no Python reference on the path), and the image prints the expected output (expected.txt) on the checked
emulator. Also: the compiler of Forth made from forth.tw by the chain (l3c -> l2l) is the text of language 1 forth.l1 and gives the same image
(after a change of forth.tw it is made again, see tower/README.md). The ticks of the runs and the sizes of the images go to REPORT.
Run: make check-tower-long  or  python3 -B tower/tests/long_forth.py"""
import os
import sys
import time

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import test_forth as tf
import test_forth37 as f
import test_l3c as t
from common import run

REPORT = []         # (program, ticks of the run, bytes of the image, seconds of the build and the run)


class Programs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tf.tools()
        cls.want = f.expected()

    def test_forth_l1_is_current(self):
        """forth.tw -> l3c -> l2l gives forth.l1, and the seed turns it into the image of the compiler (the chain made it, no Python)."""
        tl = tf.tools()
        l2 = tf.step('l3c', tl['l3c'], t.read('forth.tw', 'rb') + b'\0').out
        l1 = tf.step('l2l', tl['l2l'], l2 + l2).out
        self.assertEqual(l1[:-1], t.read('forth.l1', 'rb'))
        self.assertEqual(tf.step('seed', tl['seed'], l1).out, tl['forth'][0])
        self.assertLess(len(tl['forth'][0]) * 8, 1 << 20)

    def test_forthgen_l1_is_current(self):
        """forthgen.tw -> l3c -> l2l gives forthgen.l1 (the tables of forth.tw are made by the chain, no awk, no Python)."""
        tl = tf.tools()
        l2 = tf.step('l3c', tl['l3c'], t.read('forthgen.tw', 'rb') + b'\0').out
        l1 = tf.step('l2l', tl['l2l'], l2 + l2).out
        self.assertEqual(l1[:-1], t.read('forthgen.l1', 'rb'))
        self.assertLess(len(tf.step('seed', tl['seed'], l1).out) * 8, 1 << 20)

    def test_all_37(self):
        for n in tf.names():
            with self.subTest(n):
                t0 = time.time()
                img = tf.build(tf.source(n))
                r = run(img, 20, 2, checked=True, limit=tf.BIG)
                self.assertEqual((r.rc, r.out), (0, self.want[n]), r.err)
                REPORT.append((n, r.ticks, len(img), time.time() - t0))


def tearDownModule():
    for row in REPORT:
        print('forth %-16s run %7d ticks  image %6d bytes  %.1f s' % row)
    if REPORT:
        print('forth: %d programs, run %d ticks' % (len(REPORT), sum(r[1] for r in REPORT)))


if __name__ == '__main__':
    unittest.main()
