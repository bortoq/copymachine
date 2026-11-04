"""Tests of the tower seed: levels 1, 2, 3 on the emulator in checked mode (no network).
Run: make check-tower  or  python3 -m pytest tower  or  python3 -B tower/tests/test_tower.py"""
import os
import sys

sys.dont_write_bytecode = True
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import common
import l1
import l2
import l3
import l5
import progs
from common import Alloc, Mem, bytes_value, run, stream


def go(build, plain=True, stdin=b''):
    p = l3.compile_program(build)
    return p, once(p, plain, stdin)


def once(p, plain=False, stdin=b''):
    st = p.stats
    r = run(st['image'], st['A'], st['P'], checked=True, stdin=stdin)
    assert r.rc == 0, (r.rc, r.err)
    assert r.ticks < 200000, 'tick limit reached'
    if plain:                                  # the production emulator gives the same output
        q = run(st['image'], st['A'], st['P'], checked=False, stdin=stdin)
        assert q.out == r.out
    return r


def intervals(p):
    """Independent host audit: absolute intervals of every stored layer are pairwise disjoint."""
    for l in p.layers:
        iv = []
        for r in l.rows + l.jumps:
            f = [l1.val(x) for x in r.f]
            if f[0] == f[1] and f[0] >= p.S:
                iv.append((f[2], f[3]))
            elif f[2] == f[3] and f[2] >= p.S:
                iv.append((f[0], f[1]))
            elif f[2] != f[3]:
                iv += [(f[0], f[1]), (f[2], f[3])]
        for i in range(len(iv)):
            for j in range(i + 1, len(iv)):
                assert iv[i][1] <= iv[j][0] or iv[j][1] <= iv[i][0], (iv[i], iv[j])


def setUpModule():
    common.ensure_built()


def arith_want(n, ka, kb, a, b):
    m, h = (1 << n) - 1, n // 4
    return ('%0*x%x%x%0*x%0*x%0*x%0*x' % (h, (a - b) & m, int(a < b), int(a == b), h, a << 1 & m, h, a >> 1,
                                           h, a << ka & m, h, a >> kb)).encode()


def fibs(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class Level1(unittest.TestCase):
    def test_write_byte(self):
        """Two layers by hand: print 'H', then halt (a layer of NOPs)."""
        common.ensure_built()
        A = 12
        S = 2 ** A - 6
        buf = 2000
        mem, alloc = Mem(), Alloc(S)
        layers = [l1.Layer([l1.row(S + 2, S + 2, buf, buf + 8)], to='halt', entry=True)]
        P = l1.widths(A, layers)
        alloc.take(0, P * 4 * A)
        alloc.take(buf, 8)
        l1.place(A, layers, alloc)
        l1.encode(A, layers, alloc, mem, P)
        mem.put(buf, bytes_value(b'H'), 8)
        img, _ = l1.image(A, P, mem)
        r = run(img, A, P)
        self.assertEqual((r.rc, r.out), (0, b'H'))
        self.assertEqual(r.ticks, 3)           # seed, snapshot loader, print+halt... then all-NOP stop

    def test_indirection(self):
        """A row patches a field of another row: select a byte by value (the base of lookups)."""
        common.ensure_built()
        A = 12
        S = 2 ** A - 6
        mem, alloc = Mem(), Alloc(S)
        tab, x = 1024, 1500            # two bytes at stride 16 from 1024, selector bits at 1500, 1501
        R = l1.row(S + 2, S + 2, tab, tab + 8)    # prints the byte at tab (+16 if patched)
        for sel in (0, 1):
            mem, alloc = Mem(), Alloc(S)
            patch = l1.row(lambda: R.addr + 2 * A + 4, lambda: R.addr + 2 * A + 5, x, x + 1)
            patch2 = l1.row(lambda: R.addr + 3 * A + 4, lambda: R.addr + 3 * A + 5, x + 1, x + 2)
            layers = [l1.Layer([patch], entry=True), l1.Layer([patch2]), l1.Layer([]),
                      l1.Layer([R], to='halt')]
            P = l1.widths(A, layers)
            alloc.take(0, P * 4 * A)
            for lo, n in ((tab, 32), (x, 2)):
                alloc.take(lo, n)
            l1.place(A, layers, alloc)
            l1.encode(A, layers, alloc, mem, P)
            mem.put(tab, bytes_value(b'A'), 8); mem.put(tab + 16, bytes_value(b'B'), 8)
            mem.put(x, sel, 1); mem.put(x + 1, sel, 1)
            # entries are 8 bits at stride 16: the selector is bit 4 of sl and of sh = sl + 8 (bit 3 set)
            img, _ = l1.image(A, P, mem)
            r = run(img, A, P)
            self.assertEqual(r.out, b'AB'[sel:sel + 1])


class Level2(unittest.TestCase):
    def test_copy_is_row(self):
        r = l2.copy(5, l2.Ref(_D(100), 0, 5), l2.Ref(_D(200), 0, 5))
        self.assertEqual([l1.val(x) for x in r.f], [100, 105, 200, 205])

    def test_saving(self):
        p, _ = go(progs.add_print(1, 2), plain=False)
        two = l5.text_bits(p.A, p.layers)
        one = sum(l.u for l in p.layers) * 4 * p.A
        self.assertLess(two, one)
        self.assertGreater(1 - two / one, 0.20)


class _D:
    def __init__(self, a): self.addr = a


class Level3(unittest.TestCase):
    def test_add_print(self):
        for a, b in ((200, 100), (0, 0), (255, 255), (7, 9), (128, 127), (15, 1), (240, 16)):
            p, r = go(progs.add_print(a, b), plain=(a == 200))
            self.assertEqual(r.out, b'%03d\n' % (a + b), (a, b))
        intervals(p)

    def test_branch(self):
        for a, b in ((3, 9), (9, 3), (5, 5), (16, 15), (15, 16), (0, 255), (255, 0), (0x80, 0x7f)):
            p, r = go(progs.branch(a, b), plain=False)
            self.assertEqual(r.out, (b'Y' if a < b else b'N') + b'\n', (a, b))

    def test_and(self):
        for a, b in ((0xac, 0x3f), (0xff, 0x0f), (0, 0xff)):
            p, r = go(progs.and_hex(a, b), plain=False)
            self.assertEqual(r.out, b'%02x' % (a & b))

    def test_add16(self):
        for a, b in ((0x1234, 0x0fff), (0xffff, 1), (40000, 25000), (0, 0)):
            p, r = go(progs.add16_hex(a, b), plain=False)
            self.assertEqual(r.out, b'%04x' % ((a + b) & 0xffff), (a, b))

    def test_loop_digits(self):
        p, r = go(progs.loop_digits())
        self.assertEqual(r.out, b'0123456789\n')
        intervals(p)

    def test_loop_sum(self):
        p, r = go(progs.loop_sum())
        self.assertEqual(r.out, b'055\n')

    def test_calls(self):
        p, r = go(progs.calls())
        self.assertEqual(r.out, b'3ac3\n')
        intervals(p)

    def test_random(self):
        """Seeded random operands: add, compare, 16-bit add (each compiled once per value: constants differ)."""
        import random
        rnd = random.Random(23)
        for _ in range(12):
            a, b = rnd.randrange(256), rnd.randrange(256)
            self.assertEqual(go(progs.add_print(a, b), plain=False)[1].out, b'%03d\n' % (a + b))
            self.assertEqual(go(progs.branch(a, b), plain=False)[1].out, (b'Y' if a < b else b'N') + b'\n')
        for _ in range(6):
            a, b = rnd.randrange(65536), rnd.randrange(65536)
            self.assertEqual(go(progs.add16_hex(a, b), plain=False)[1].out, b'%04x' % ((a + b) & 0xffff))

    def test_array(self):
        """8 stores by a computed index (3i mod 8), 8 reads by a counted-down index, bytes out."""
        import random
        rnd = random.Random(232)
        sets = [[65, 10, 255, 0, 128, 127, 19, 196]] + [[rnd.randrange(256) for _ in range(8)] for _ in range(3)]
        for k, vals in enumerate(sets):
            p, r = go(progs.array_rev(vals), plain=(k == 0))
            a = [0] * 8
            for i in range(8):
                a[3 * i % 8] = vals[i]
            self.assertEqual(r.out, bytes(a[j] for j in range(7, -1, -1)) + b'\n', vals)
            self.assertEqual(p.stores, 1)
            intervals(p)

    def test_arith(self):
        """sub, eq, shl, shr on 8 and 16 bits, edge and seeded random operands read from stdin."""
        import random
        rnd = random.Random(2322)
        for n, ka, kb in ((8, 3, 5), (16, 7, 9)):
            p = l3.compile_program(progs.arith(n, ka, kb))
            m = (1 << n) - 1
            edge = [0, 1, 2, m, m - 1, 1 << (n - 1), (1 << (n - 1)) - 1, 0x55 * (m // 0xff), 0xa5 * (m // 0xff)]
            cases = [(a, b) for a in edge for b in edge]
            cases += [(rnd.randrange(m + 1), rnd.randrange(m + 1)) for _ in range(12)]
            for k, (a, b) in enumerate(cases):
                r = once(p, plain=(k == 0), stdin=stream(a, n) + stream(b, n))
                self.assertEqual(r.out, arith_want(n, ka, kb, a, b), (n, a, b))
            self.assertEqual(sum(1 for a, b in cases if a == b) > 8, True)
            intervals(p)

    def test_echo(self):
        """stdin to stdout up to a zero byte: bytes of any value, empty input, text after the zero stays."""
        p = l3.compile_program(progs.echo())
        for k, text in enumerate((b'hello, world\n', b'', b'a\xff\x01\x80z', bytes(range(1, 256)))):
            r = once(p, plain=(k == 0), stdin=text + b'\x00tail')
            self.assertEqual(r.out, text)
        intervals(p)

    def test_recursion(self):
        """Fibonacci by double recursion: return links and saved values in two stacks."""
        p = l3.compile_program(progs.fib())
        for k, n in enumerate((10, 0, 1, 2, 3, 7, 11)):
            r = once(p, plain=(k == 0), stdin=stream(n, 8))
            self.assertEqual(r.out, b'%03d\n' % fibs(n), n)
        intervals(p)

    def test_grammar(self):
        """Built right by construction: what has no meaning cannot be written."""
        def shift_in_place(p):
            a = p.var('a', 8)
            p.block('main'); p.shl(a, a, 1)
        with self.assertRaises(AssertionError):
            l3.compile_program(shift_in_place)
        def odd_key(p):
            p.block('main'); p.key(p.var('k', 4))
        with self.assertRaises(AssertionError):
            l3.compile_program(odd_key)
        def wide_index(p):
            arr = p.array('arr', (3,), 8)
            p.block('main'); p.store(arr, [p.var('i', 4)], p.var('v', 8))
        with self.assertRaises(AssertionError):
            l3.compile_program(wide_index)

    def test_serial(self):
        """Without packing (one row per layer) the same programs give the same output."""
        for build, out in ((progs.loop_sum(), b'055\n'), (progs.calls(), b'3ac3\n'), (progs.branch(2, 1), b'N\n'),
                           (progs.array_rev([1, 2, 3, 4, 5, 6, 7, 8]), bytes([6, 3, 8, 5, 2, 7, 4, 1]) + b'\n')):
            p = l3.compile_program(build, serial=True)
            r = run(p.stats['image'], p.stats['A'], p.stats['P'])
            self.assertEqual((r.rc, r.out), (0, out))

    def test_variants(self):
        """The three savings of 23.3 are switches: without them the same programs give the same output,
        with them there are fewer layers (writes into the processor), shared strides, a pair of sources."""
        for build, out, inp in ((progs.loop_sum(), b'055\n', b''), (progs.calls(), b'3ac3\n', b''),
                                (progs.array_rev([1, 2, 3, 4, 5, 6, 7, 8]), bytes([6, 3, 8, 5, 2, 7, 4, 1]) + b'\n', b''),
                                (progs.fib(), b'055\n', stream(10, 8))):
            by = {}
            for plan in (False, True):
                for direct in (False, True):
                    p = l3.compile_program(build, plan=plan, direct=direct)
                    r = run(p.stats['image'], p.stats['A'], p.stats['P'], stdin=inp)
                    self.assertEqual((r.rc, r.out), (0, out), (plan, direct))
                    intervals(p)
                    by[plan, direct] = (len(p.layers), r.ticks, len(p.stats['image']))
            self.assertLess(by[False, True][0], by[False, False][0])      # a write into the next layer: fewer layers
            self.assertLess(by[False, True][1], by[False, False][1])
            self.assertLessEqual(by[True, False][2], by[False, False][2])  # shared strides never add bits

    def test_shared_stride_and_holes(self):
        """Tables with their widths summing to less than the stride share it; the jump before a row
        patched in the processor is split around the patch (holes), and the audit covers every jump row."""
        p, r = go(progs.arith(8, 3, 5), stdin=stream(200, 8) + stream(77, 8))
        groups = {}
        for t in p.tables.values():
            groups.setdefault(t.gid, []).append(t)
        self.assertTrue(any(len(g) > 1 for g in groups.values()))
        for g in groups.values():                                   # entries of one stride do not overlap
            self.assertLess(sum(t.out for t in g), 1 << g[0].j)
        self.assertTrue(any(len(l.jumps) > 1 for l in p.layers))
        self.assertTrue(all(l.jumps[0].kind == 'jump' for l in p.layers))
        intervals(p)

    def test_checked_catches_overlap(self):
        """Control: the audit really fires on an intersecting layer."""
        common.ensure_built()
        A = 12
        S = 2 ** A - 6
        mem, alloc = Mem(), Alloc(S)
        layers = [l1.Layer([l1.row(1000, 1008, 2000, 2008), l1.Layer and l1.row(1004, 1012, 2100, 2108)],
                           to='halt', entry=True)]
        P = l1.widths(A, layers)
        alloc.take(0, P * 4 * A)
        l1.place(A, layers, alloc)
        l1.encode(A, layers, alloc, mem, P)
        img, _ = l1.image(A, P, mem)
        r = run(img, A, P)
        self.assertNotEqual(r.rc, 0)
        self.assertIn('AUDIT', r.err)


if __name__ == '__main__':
    common.ensure_built()
    unittest.main()
