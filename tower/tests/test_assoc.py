"""Tests of the associative space (25.2, 7.2.43): the programs tower/programs/assoc/assoc_hash.tw and assoc_tree.tw (language 3) keep
a small space of cells: the direct table key -> the top version, the stack of versions, the reverse table value -> key (the top
version), the ring of synonyms (two links: next and previous); there is "no such key / value" = the prohibitive price (all ones),
and a write which cannot be done (no free cell, the key or the value all ones) answers it too. The tests run them on the emulator
and compare every answer with a simple model (a dictionary of stacks of values), then read the whole space back (every key,
every value, every cell) and check the consistency: the value at the cell p is what the key of p gives and what the search of this
value finds, the stack goes down the cells to the first version, the synonyms are exactly the keys with the same top value.
Python is here only: the programs are language 3.
Run: make check-tower  or  python3 -B tower/tests/test_assoc.py"""
import os
import random
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, HERE)
import chain
import common
import text
from common import rev, stream
from golden_programs import hoist

STOP, W, K, V, R, P, Q, S = range(8)
PROGRAMS = os.path.join(HERE, '..', 'programs', 'assoc')
SIZE = (8, 8, 4)                                      # key bits, value bits, cell bits: the committed programs have one size (16 cells, 8-bit keys and values)
_CACHE = {}


def setUpModule():
    common.ensure_built()


def source(method):
    with open(os.path.join(PROGRAMS, 'assoc_%s.tw' % method), encoding='utf-8') as h:
        return h.read()


class Space:
    """The committed program of the method (the size SIZE); session() runs a list of commands and decodes the answers."""

    def __init__(self, method, kb=8, vb=8, c=4):
        self.method, self.kb, self.vb, self.c = method, kb, vb, c
        self.n = (1 << c) - 1                          # cells 1..n
        self.onesk, self.onesv = (1 << kb) - 1, (1 << vb) - 1
        p, errs = text.compile_text(source(method))
        assert not errs, errs
        self.prog, self.stats = p, p.stats

    @staticmethod
    def get(method):
        if method not in _CACHE:
            _CACHE[method] = Space(method, *SIZE)
        return _CACHE[method]

    def encode(self, ops):
        out = bytearray()
        for op in ops:
            out += stream(op[0], 8)
            if op[0] == W:
                out += stream(op[1], self.kb) + stream(op[2], self.vb)
            elif op[0] in (K, R, P, S):
                out += stream(op[1], self.kb)
            elif op[0] == V:
                out += stream(op[1], self.vb)
            elif op[0] == Q:
                out += stream(op[1], 8)
        return bytes(out) + stream(STOP, 8)

    def sizes(self, op):
        """The bytes of the answer to op (a write always answers: the cell, or all ones if it cannot be done)."""
        return {W: 1, K: self.vb // 8, V: self.kb // 8, S: self.kb // 8, P: 1, Q: self.kb // 8 + self.vb // 8 + 3}.get(op[0], 0)

    def number(self, bs):
        return sum(rev(b, 8) << 8 * i for i, b in enumerate(bs))

    def session(self, ops, checked=False):
        st = self.stats
        limit = 3000 * (len(ops) + 1) + 100000                 # far above the work of a command: a hang is an error
        r = common.run(st['image'], st['A'], st['P'], checked=checked, stdin=self.encode(ops), limit=limit)
        assert r.rc == 0, (r.rc, r.err)
        assert len(r.out) == sum(self.sizes(op) for op in ops), 'the program did not stop in time or answers wrongly'
        i, res = 0, []
        for op in ops:
            n = self.sizes(op)
            b = r.out[i:i + n]
            i += n
            if op[0] == Q:
                kb, vb = self.kb // 8, self.vb // 8
                res.append((self.number(b[:kb]), self.number(b[kb:kb + vb])) + tuple(rev(x, 8) for x in b[kb + vb:kb + vb + 3]))
            else:
                res.append(self.number(b) if n else None)           # W: the cell of the new version or 255
        assert i == len(r.out), 'extra output'
        return res, r


class Model:
    """The dictionary of stacks. A write is refused (nothing changes, the answer is the prohibitive price) if the key or the value is
    all ones or if all cells are in use."""

    def __init__(self, sp):
        self.sp, self.st, self.used = sp, {}, 0
        self.cells = {}                                # key -> the cells of its versions, as the program answered the writes (known after the run)

    def refuses(self, k, v):
        return k == self.sp.onesk or v == self.sp.onesv or self.used >= self.sp.n

    def write(self, k, v, cell=None):
        if self.refuses(k, v):
            return
        self.st.setdefault(k, []).append(v)
        self.cells.setdefault(k, []).append(cell)
        self.used += 1

    def roll(self, k):
        if k in self.st:
            self.st[k].pop()
            self.cells[k].pop()
            self.used -= 1
            if not self.st[k]:
                del self.st[k]
                del self.cells[k]

    def value(self, k):
        return self.st[k][-1] if k in self.st else self.sp.onesv

    def keys_of(self, v):
        return sorted(k for k, s in self.st.items() if s[-1] == v)


def apply(m, op, got=None):
    if op[0] == W:
        m.write(op[1], op[2], got)
    elif op[0] == R:
        m.roll(op[1])


def check_inline(tc, m, op, got):
    """The answer to one command against the model before the command (the commands which change the model are applied after)."""
    sp = m.sp
    if op[0] == W:                                      # a write always answers: the cell of the new version (a free one), or all ones if it is refused
        if m.refuses(op[1], op[2]):
            tc.assertEqual(got, 255, op)
        else:
            tc.assertTrue(1 <= got <= sp.n, (op, got))
            tc.assertNotIn(got, [c for cs in m.cells.values() for c in cs], (op, got))
    elif op[0] == K:
        tc.assertEqual(got, m.value(op[1]), op)
    elif op[0] == V:
        ks = m.keys_of(op[1])
        tc.assertTrue(got in ks if ks else got == sp.onesk, (op, got, ks))
    elif op[0] == S:
        if op[1] in m.st:
            tc.assertIn(got, m.keys_of(m.value(op[1])), op)
        else:
            tc.assertEqual(got, sp.onesk, op)
    elif op[0] == P:
        tc.assertEqual(got == 255, op[1] not in m.st, op)
        tc.assertTrue(got == 255 or 1 <= got <= sp.n, (op, got))
    elif op[0] == Q:
        tc.assertEqual(len(got), 5)


def sweep_ops(sp, keys, values=None):
    ops = [(K, k) for k in keys] + [(P, k) for k in keys] + [(S, k) for k in keys]
    ops += [(V, v) for v in (range(1 << sp.vb) if values is None else values)] + [(Q, p) for p in range(sp.n + 1)]
    return ops


def check_sweep(tc, m, sp, keys, values, res):
    """The consistency of the whole space against the model: res are the answers to sweep_ops(sp, keys, values)."""
    nk, nv = len(keys), len(values)
    kk, pp, ss = res[:nk], res[nk:2 * nk], res[2 * nk:3 * nk]
    vv, qq = res[3 * nk:3 * nk + nv], res[3 * nk + nv:]
    pos = {}
    for i, k in enumerate(keys):
        tc.assertEqual(kk[i], m.value(k), ('K', k))                       # the value of the key
        if k not in m.st:
            tc.assertEqual((pp[i], ss[i]), (255, sp.onesk), k)             # no key: the prohibitive price
            continue
        p = pp[i]
        tc.assertTrue(1 <= p <= sp.n, (k, p))
        tc.assertEqual(p, m.cells[k][-1], ('the cell answered by the write', k))
        tc.assertNotIn(p, pos)
        pos[p] = k
        tc.assertEqual(qq[p][:2], (k, m.value(k)), ('Q', k, p))            # the cell p holds the key and its value
        stack, cells, q, seen = [], [], p, set()
        while q:                                                          # the stack of versions: down the cells to the first
            tc.assertNotIn(q, seen)
            seen.add(q)
            tc.assertEqual(qq[q][0], k, (k, q))
            stack.append(qq[q][1])
            cells.append(q)
            q = qq[q][2]
        tc.assertEqual(stack[::-1], m.st[k], ('stack', k))
        tc.assertEqual(cells[::-1], m.cells[k], ('cells of the stack', k))
        ring, q = [], k                                                   # the synonyms: the ring of the keys with the same value
        for _ in range(sp.n + 1):
            ring.append(q)
            q = ss[keys.index(q)] if q in keys else None
            if q is None or q == k:
                break
        tc.assertEqual(q, k, ('ring', k, ring))
        tc.assertEqual(sorted(ring), m.keys_of(m.value(k)), ('ring', k))
    for p, k in pos.items():                                              # the ring has two links: next and previous agree
        nx, pr = qq[p][3], qq[p][4]
        tc.assertEqual(pos.get(nx), ss[keys.index(k)], ('next', k))
        tc.assertEqual((qq[nx][4], qq[pr][3]), (p, p), ('links', k))
        tc.assertEqual((qq[nx][1], qq[pr][1]), (qq[p][1], qq[p][1]), ('values', k))
    for i, v in enumerate(values):
        ks = m.keys_of(v)
        if ks:                                                            # the search of a value finds a key whose top version is it
            tc.assertIn(vv[i], ks, ('V', v))
            if vv[i] in keys:
                tc.assertEqual(qq[pp[keys.index(vv[i])]][1], v, ('V', v))
        else:
            tc.assertEqual(vv[i], sp.onesk, ('V', v))


def pools(rng, sp):
    """Keys and values with collisions: the same low bits (the hash), the same upper parts (the tree), equal values."""
    h = sp.c
    ks = set()
    base = rng.randrange(sp.onesk)
    for j in range(3):
        ks.add(base ^ (j << h) & sp.onesk)                                 # same low H bits
    for j in range(3):
        ks.add(base ^ (j + 1) & sp.onesk)                                  # differ in the lowest part only
    while len(ks) < 12:
        ks.add(rng.randrange(sp.onesk))
    vs = [rng.randrange(sp.onesv) for _ in range(5)]
    vs += [vs[0] ^ (1 << h) & sp.onesv, vs[1] ^ 1]
    return sorted(ks - {sp.onesk}), sorted(set(vs) - {sp.onesv})


def random_ops(rng, sp, n):
    ks, vs = pools(rng, sp)
    ops = []
    for _ in range(n):
        k = rng.choice(ks) if rng.random() < 0.85 else rng.randrange(1 << sp.kb)
        v = rng.choice(vs) if rng.random() < 0.85 else rng.randrange(1 << sp.vb)
        x = rng.random()
        if x < 0.5:
            ops.append((W, k, v))
        elif x < 0.7:
            ops.append((R, k))
        elif x < 0.8:
            ops.append((K, k))
        elif x < 0.88:
            ops.append((V, v))
        elif x < 0.93:
            ops.append((S, k))
        elif x < 0.97:
            ops.append((P, k))
        else:
            ops.append((Q, rng.randrange(sp.n + 1)))
    return ops


def run_checked(tc, sp, ops, checked=False, only=None):
    """The commands, then the sweep of the whole space (every key, every value, every cell); all answers against the model."""
    m = Model(sp)
    for op in ops:
        apply(m, op)
    keys = list(range(1 << sp.kb)) if only is None else sorted(set(only) | set(m.st) | {sp.onesk})
    values = list(range(1 << sp.vb))
    res, r = sp.session(list(ops) + sweep_ops(sp, keys, values), checked=checked)
    m = Model(sp)
    for op, got in zip(ops, res[:len(ops)], strict=True):
        check_inline(tc, m, op, got)
        apply(m, op, got)
    check_sweep(tc, m, sp, keys, values, res[len(ops):])
    return r


class Programs(unittest.TestCase):
    def test_same_text_but_the_index(self):
        """The two programs share everything but the index (the tables of the hash or of the tree and the words around them)."""
        def part(method):
            src = source(method)
            return src[src.index(':main block'):src.index('# --- the index')]
        self.assertEqual(part('hash'), part('tree'))

    def test_hello(self):
        for method in ('hash', 'tree'):
            sp = Space.get(method)
            res, r = sp.session([(W, 5, 7), (W, 6, 7), (K, 5), (V, 7), (S, 5), (W, 5, 9), (K, 5), (V, 7), (V, 9), (R, 5), (K, 5), (V, 9),
                                 (K, 200), (V, 100), (W, 255, 5), (W, 5, 255), (K, 5), (W, 6, 8), (K, 6)], checked=True)
            self.assertEqual(res[2], 7)
            self.assertIn(res[3], (5, 6))
            self.assertEqual(res[4], 6)
            self.assertEqual((res[6], res[7], res[8], res[10], res[11]), (9, 6, 5, 7, 255))
            self.assertEqual((res[12], res[13]), (255, 255))
            self.assertEqual((res[14], res[15], res[16], res[18]), (255, 255, 7, 8))   # the refused writes answer all ones, the others a cell
            self.assertEqual(len({res[0], res[1], res[5]}), 3)                       # three writes with nothing taken back: three different cells
            self.assertTrue(all(1 <= x <= sp.n for x in (res[0], res[1], res[5], res[17])))
            self.assertLess(r.ticks, 5000)

    def test_the_chain_compiler_reads_them(self):
        """The texts are in the subset of l3c (the compiler of the chain accepts them); its image (A=20, serial layout) gives the same answers."""
        for method in ('hash', 'tree'):
            with self.subTest(method):
                sp = Space.get(method)
                img = chain.build(hoist(source(method)))[0]            # a refusal of a pass of the chain is an AssertionError
                ops = random_ops(random.Random(3), sp, 60) + sweep_ops(sp, range(0, 256, 5), range(0, 256, 5))
                a = common.run(img, 20, 2, checked=True, limit=200 * 10 ** 6, stdin=sp.encode(ops))
                b = common.run(sp.stats['image'], sp.stats['A'], sp.stats['P'], checked=True, limit=200 * 10 ** 6, stdin=sp.encode(ops))
                self.assertEqual((a.rc, b.rc), (0, 0))
                self.assertEqual(a.out, b.out)
                self.assertGreater(len(a.out), 100)


class Random(unittest.TestCase):
    def test_random_sessions(self):
        """Random sessions with colliding keys, repeated values, absent keys and rollbacks; the first two of every kind on the checked emulator."""
        for method in ('hash', 'tree'):
            sp = Space.get(method)
            rng = random.Random(25 * 1000 + SIZE[0] * 10 + SIZE[2])
            for i in range(14):
                with self.subTest(method=method, i=i):
                    run_checked(self, sp, random_ops(rng, sp, rng.choice([40, 90, 160])), checked=i < 2)

    def test_pool_and_cells_are_full(self):
        """Every cell in use (distinct keys with nothing in common, repeated rounds), then everything is taken back: nothing is lost."""
        for method in ('hash', 'tree'):
            sp = Space.get(method)
            rng = random.Random(11)
            ops = []
            for _ in range(4):
                ks = rng.sample(range(sp.onesk), sp.n + 2)
                vs = rng.sample(range(sp.onesv), sp.n + 2)
                ops += [(W, k, v) for k, v in zip(ks, vs, strict=True)]          # two writes over the capacity are refused
                ops += [(R, k) for k in ks[::2]] + [(W, k, vs[0]) for k in ks[1::2]]
                ops += [(R, k) for k in ks] + [(R, k) for k in ks]
            with self.subTest(method=method):
                run_checked(self, sp, ops, checked=True)

    def test_full_space_refuses_the_write(self):
        """With every cell in use a write answers the prohibitive price (all ones) and changes nothing; after a rollback it is done and answers a cell."""
        for method in ('hash', 'tree'):
            sp = Space.get(method)
            ops = [(W, j, j) for j in range(1, sp.n + 1)] + [(W, 100, 5), (W, 3, 5), (K, 100), (K, 3), (R, 3), (W, 100, 5), (K, 100), (K, 3)]
            with self.subTest(method=method):
                res, _ = sp.session(ops, checked=True)
                self.assertEqual(sorted(res[:sp.n]), list(range(1, sp.n + 1)))        # the cells 1..n, each once
                self.assertEqual(res[sp.n:sp.n + 4], [255, 255, sp.onesv, 3])
                self.assertEqual((res[sp.n + 4], res[sp.n + 5], res[sp.n + 6], res[sp.n + 7]), (None, res[2], 5, 255))   # the cell of the key 3 is free again
                run_checked(self, sp, ops, checked=True)

    def test_ring_length_does_not_cost_ticks(self):
        """The ring of synonyms has two links: a rollback and an overwrite of a key (W over a top version) take no more ticks in a
        ring of 12 cells than in a ring of 2 (the first written key, the farthest from its predecessor in a ring with one link)."""
        sp = Space.get('tree')

        def cost(length, last):
            ks = [17 * j % 251 + 1 for j in range(length)]
            pre = [(W, k, 7) for k in ks]
            base = sp.session(pre, checked=True)[1].ticks
            return sp.session(pre + [last(ks[0])], checked=True)[1].ticks - base
        for last in (lambda k: (R, k), lambda k: (W, k, 9)):
            self.assertLessEqual(cost(12, last), cost(2, last), last(0))

    def test_same_value_and_same_bucket(self):
        """The long chains and rings: all keys with the same value (the ring), all keys and values with the same low bits (the hash chain)."""
        for method in ('hash', 'tree'):
            sp = Space.get(method)
            kk, vv = (lambda j, sp=sp: ((j << sp.c) + 3) & sp.onesk), (lambda j, sp=sp: ((j << sp.c) + 5) & sp.onesv)
            ops = [(W, kk(j), 9) for j in range(1, sp.n + 1)] + [(R, kk(3)), (R, kk(5)), (W, 7, 9), (W, 7, 17)]
            ops += [(W, kk(j), vv(j)) for j in range(1, 5)] + [(R, 7), (R, 7), (R, kk(1))]
            with self.subTest(method=method):
                run_checked(self, sp, ops, checked=True)


class Exhaustive(unittest.TestCase):
    def test_every_key_and_every_value(self):
        """The 8-bit keys: for every key k and every value v a fresh space: a background, then k written twice, v written
        under another key, a rollback; the whole space is read back and compared with the model."""
        for method in ('hash', 'tree'):
            sp = Space.get(method)
            bg = [(W, 17, 4), (W, 33, 4), (W, 1, 200), (W, 18, 4)]
            for i in range(0, 255):
                k, v = i, 254 - i
                ops = bg + [(W, k, v), (W, k, i), (W, 100, v), (R, k), (W, k, 4), (R, 17), (W, v, k)]
                with self.subTest(method=method, i=i):
                    run_checked(self, sp, ops, only=[17, 33, 1, 18, 100, 7, k, v])


if __name__ == '__main__':
    unittest.main()
