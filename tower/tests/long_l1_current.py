"""The texts of language 1 of l3c, l3p, l4c are what the chain makes from their .tw (25.7.3.3, see test_l1_current.py): the text of the pass, made by the
chain from <pass>.tw (l3c -> l2l on the plain emulator; the images of l3c and l2l are those which chain.py makes from l3c.l1 and l2l.l1), equals programs/<pass>.l1 byte for byte
(l3c.l1 is the fixed point of l3c: the image made from l3c.l1 turns l3c.tw into l3c.l1 again; this is checked by long_golden.py, test_fixed_points,
so the long set makes only l3p and l4c here; the update makes all three).
Update after a change of a .tw: L1_UPDATE=1 python3 -B tower/tests/long_l1_current.py (the texts and tower/programs/l1-record.txt are written; a diff of the texts is for you to read).
Run: make check-tower-long  or  python3 -B tower/tests/long_l1_current.py"""
import os
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain
import test_l1_current as cur


def setUpModule():
    import common
    common.ensure_built()


def made(name):
    """The text of language 1 of the pass made by the chain from its .tw (without the zero byte)."""
    l1 = chain.language1(chain.read(name + '.tw'))
    assert l1.endswith(b'\0')
    return l1[:-1]


class Made(unittest.TestCase):
    def test_texts(self):
        for n in ('l3p', 'l4c'):
            with self.subTest(n):
                self.assertTrue(made(n) == chain.read(n + '.l1'), '%s.l1 is not what the chain makes from %s.tw' % (n, n))


if __name__ == '__main__':
    if os.environ.get('L1_UPDATE'):
        import common
        common.ensure_built()
        for n in cur.PASSES:
            new, old = made(n), chain.read(n + '.l1')
            print('%s.l1: %s (%d -> %d bytes)' % (n, 'same' if new == old else 'CHANGED', len(old), len(new)))
            if new != old:
                with open(os.path.join(chain.PROGRAMS, n + '.l1'), 'wb') as h:
                    h.write(new)
        cur.write_record()
        print('written:', cur.RECORD)
    else:
        unittest.main()
