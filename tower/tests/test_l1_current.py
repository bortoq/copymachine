"""The texts of language 1 of the passes which are made by the chain itself (l3c.l1, l3p.l1, l4c.l1) are current (25.7.3.3). chain.py makes the images of these passes
from the texts (the seed turns them into the images, in seconds), the long set (long_l1_current.py) makes them again from <pass>.tw by the chain
(l3c -> l2l, 15-20 s each) and compares byte for byte. Here, in the fast set, is the cheap part: tower/programs/l1-record.txt keeps for every pass
    <pass> <sha256 of the recipe> <sha256 of <pass>.l1>
where the recipe is what the text is made from: <pass>.tw and the texts of the passes which make it (l3c.l1, l2l.l1, seed.l1), so a change of the text of
a pass, or of a text below it, without a new .l1 and a new record fails here (the text is made again by the long set: L1_UPDATE=1 python3 -B tower/tests/long_l1_current.py writes
the texts and the record). The texts seed.l1, l2c.l1, l2l.l1 are made from their .tw by l1text (the checks are in test_seed.py, test_l2c.py, test_labels.py).
Run: make check-tower  or  python3 -B tower/tests/test_l1_current.py"""
import os
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain

PASSES = ('l3c', 'l3p', 'l4c')
RECORD = os.path.join(chain.PROGRAMS, 'l1-record.txt')


def recipe(name):
    """The hash of what the text of language 1 of the pass is made from: its .tw and the texts of language 1 of l3c, l2l and the seed."""
    return chain.sha(name.encode(), chain.read(name + '.tw'), chain.read('l3c.l1'), chain.read('l2l.l1'), chain.read('seed.l1'))


def record():
    """{pass: (recipe, hash of the .l1)} as the files are now."""
    return {n: (recipe(n), chain.sha(chain.read(n + '.l1'))) for n in PASSES}


def stored():
    out = {}
    with open(RECORD, encoding='utf-8') as h:
        for line in h:
            if line.strip() and not line.startswith('#'):
                n, r, t = line.split()
                out[n] = (r, t)
    return out


def write_record():
    with open(RECORD, 'w', encoding='utf-8') as h:
        h.write('# <pass> <sha256 of the recipe: <pass>.tw, l3c.l1, l2l.l1, seed.l1> <sha256 of <pass>.l1>; see tower/tests/test_l1_current.py; made by\n'
                '# L1_UPDATE=1 python3 -B tower/tests/long_l1_current.py (the texts are made again by the chain from the .tw)\n')
        for n, (r, t) in record().items():
            h.write('%s %s %s\n' % (n, r, t))


class Current(unittest.TestCase):
    def test_record(self):
        want, now = stored(), record()
        self.assertEqual(sorted(want), sorted(PASSES))
        for n in PASSES:
            with self.subTest(n):
                self.assertEqual(now[n][0], want[n][0], '%s.tw or a text below it changed: make the .l1 again (L1_UPDATE=1 python3 -B tower/tests/long_l1_current.py)' % n)
                self.assertEqual(now[n][1], want[n][1], '%s.l1 is not the text the record was made for' % n)

    def test_images_are_made_from_the_texts(self):
        """chain.py takes the images of these passes from the texts of language 1 (the seed makes them), not from the .tw."""
        for n in PASSES:
            self.assertIn(n, chain.FROM_L1)
            self.assertTrue(chain.read(n + '.l1'))


if __name__ == '__main__':
    unittest.main()
