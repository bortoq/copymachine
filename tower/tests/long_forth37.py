"""The 37 programs of the present language on the chain, through the programs of the chain (23.11), `make check-tower-long`: every text of
programs/forth37/ goes text of language 3 -> l3c -> l2l -> seed -> image on the emulator (serial layout; no Python compiler on the path), each
step equals the Python reference byte for byte, and the image prints the expected output (expected.txt). The packed chain (the word `pack`
first, l3c -> l3p -> l2l -> seed) does the same for PACKED, the programs which the planner takes the longest for are left to the reference
(test_forth37.py runs all 37 packed images). The ticks of the runs go to REPORT (the build ticks of docs/measurements/tower-forth37.md come from the checked emulator, see there). The steps of the tools run on the plain emulator (the tools are audited on `checked` in
test_l3c.py, long_l3c.py); the images of the programs run on `checked`.
Run: make check-tower-long  or  python3 -B tower/tests/long_forth37.py"""
import os
import sys
import time

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import l3ctext
import test_forth37 as f
import test_l3c as t
import test_l3p as p
from common import run

BIG = 300 * 10 ** 6
PACKED = ['return_stack', 'constant', 'pick_roll', 'execute', 'stack', 'calls', 'shifts', 'variables', 'begin_until', 'strings']
REPORT = []         # (program, layout, ticks of the run, seconds of the build and the run)


def build(src, pack, l2l, seed, planner=None):
    """The chain on the emulator; every step equals the reference. Returns the image."""
    if pack:
        src = 'pack\n' + src
    r = run(t.tool()['image'], 20, 3, checked=False, limit=BIG, stdin=src.encode('latin-1') + b'\0')
    assert r.rc == 0, r.err
    want, err = l3ctext.encode(src)
    assert err is None and r.out == want
    l2 = r.out
    if pack:
        q = run(planner['image'], planner['A'], planner['P'], checked=False, limit=BIG, stdin=l2)
        assert q.rc == 0, q.err
        assert q.out == l3ctext.pack_pass(l2)[0]
        l2 = q.out
    a = run(l2l['image'], l2l['A'], l2l['P'], checked=False, limit=BIG, stdin=l2 + l2)
    assert a.rc == 0, a.err
    b = run(seed['image'], seed['A'], seed['P'], checked=False, limit=BIG, stdin=a.out)
    assert b.rc == 0, b.err
    assert b.out == t.image_of(l2)
    return b.out


class Programs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t.setUpModule()
        cls.l2l = t.compiled('l2l').stats
        cls.seed = t.compiled('seed').stats
        cls.want = f.expected()

    def one(self, name, pack, planner=None):
        t0 = time.time()
        img = build(f.source(name), pack, self.l2l, self.seed, planner)
        r = run(img, 20, 3 if pack else 2, checked=True, limit=BIG)
        self.assertEqual((r.rc, r.out), (0, self.want[name]), r.err)
        REPORT.append((name, 'pack' if pack else 'serial', r.ticks, time.time() - t0))

    def test_serial_chain(self):
        for n in f.names():
            with self.subTest(n):
                self.one(n, False)

    def test_packed_chain(self):
        planner = p.pass_tool()
        for n in PACKED:
            with self.subTest(n):
                self.one(n, True, planner)


def tearDownModule():
    for row in REPORT:
        print('forth37 %-16s %-6s run %7d ticks  %.1f s' % row)
    for lay in ('serial', 'pack'):
        rows = [r for r in REPORT if r[1] == lay]
        if rows:
            print('forth37 %s: %d programs, run %d ticks' % (lay, len(rows), sum(r[2] for r in rows)))


if __name__ == '__main__':
    unittest.main()
