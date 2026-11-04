"""Tests of language 5 (cost, price, replace): the price is computed from the finished layers of languages 1-4
and matches the measurements of docs/measurements/tower.md (sections 8, 9) and the ticks of the emulator.
Run: make check-tower  or  python3 -B tower/tests/test_price.py"""
import os
import re
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import common
import l3
import l5
import progs
from common import stream
from l4 import host_pos


def setUpModule():
    common.ensure_built()


def minimal(f):
    def build(p):
        p.block('main')
        f(p)
        p.halt()
    return build


def ticks_of(p, stdin=b''):
    r = common.run(p.stats['image'], p.stats['A'], p.stats['P'], stdin=stdin)
    assert r.rc == 0, r.err
    return r.ticks


def if_prog(p):
    p.block('main')
    p.if_(p.var('c', 1).ref(), 'yes', 'no')
    p.block('yes')
    p.halt()
    p.block('no')
    p.halt()


def call_prog(rec):
    def build(p):
        if rec:
            p.rec('w', p.stack('st', 3, 2 * p.A))
        p.block('main')
        p.call('w', 'back')
        p.block('back')
        p.halt()
        p.word('w')
        p.ret()
    return build


def stack_prog(op):
    def build(p):
        s, v = p.stack('st', 3, 8), p.var('v', 8)
        p.block('main')
        (p.push if op == 'push' else p.pop)(s, v.ref())
        p.halt()
    return build


POS = host_pos(1, 8)
# construct: (builder, layers, ticks): sections 8.3 and 9.1 of docs/measurements/tower.md, after the changes of 23.3
CONSTRUCTS = {
    'empty main': (minimal(lambda p: None), 1, 3),
    'lut add4, 3 args': (minimal(lambda p: p.lut(p.t_add(), [p.var('a', 4), p.var('b', 4), p.zero.ref()], p.var('r', 5).ref())), 3, 5),
    'lut, 1 arg': (minimal(lambda p: p.lut(p.table('t1', (4,), 8, lambda x: x), [p.var('a', 4)], p.var('r', 8).ref())), 3, 5),
    'store': (minimal(lambda p: p.store(p.array('arr', (3,), 8), [p.var('i', 3)], p.var('v', 8).ref())), 3, 5),
    'if': (if_prog, 6, 7),
    'call + ret': (call_prog(False), 4, 6),
    'push': (stack_prog('push'), 3, 5),
    'pop': (stack_prog('pop'), 4, 6),
    'long! 48': (minimal(lambda p: p.long_put(p.var('pos', 128, POS), p.var('d', 48, 7))), 2, 4),
    'long@ 48 (buffer)': (minimal(lambda p: p.long_get(p.var('pos', 128, POS), p.var('d', 48))), 4, 6),
    'long@ 128 (direct)': (minimal(lambda p: p.long_get(p.var('pos', 128, POS), p.var('d', 128))), 3, 5),
    'long@ 1024 (direct)': (minimal(lambda p: p.long_get(p.var('pos', 128, POS), p.var('d', 1024))), 3, 5),
}
# program: (builder, passes of its loops, stdin)
PROGRAMS = {
    'add': (progs.add_print(200, 100), None, b''),
    'branch': (progs.branch(3, 9), None, b''),
    'loop digits': (progs.loop_digits(), {'loop': 10}, b''),
    'loop sum': (progs.loop_sum(), {'loop': 10}, b''),
    'calls': (progs.calls(), None, b''),
    'array': (progs.array_rev([65, 10, 255, 0, 128, 127, 19, 196]), {'wr': 8, 'rd': 8}, b''),
    'echo': (progs.echo(), {'out': 13}, b'hello, world\n\x00'),
    'arith 16': (progs.arith(16, 7, 9), None, stream(40000, 16) + stream(1234, 16)),
}


class Cost(unittest.TestCase):
    def test_constructs_match_measurements(self):
        for name, (build, layers, ticks) in CONSTRUCTS.items():
            p = l3.compile_program(build)
            c = l5.cost(p)
            self.assertEqual((c.layers, c.ticks), (layers, ticks), name)
            self.assertEqual(c.ticks, ticks_of(p), name)                    # and the emulator agrees
            self.assertEqual(c.rows, sum(len(l.rows) + len(l.jumps) for l in p.layers), name)

    def test_recursion_is_forbidden_but_stored(self):
        p = l3.compile_program(call_prog(True))        # 23.3: call + ret recursive, 9 layers (the ticks: 11)
        c = l5.cost(p)
        self.assertEqual(c.layers, 9)
        self.assertEqual(c.ticks, l5.FORBID)
        self.assertEqual(l5.price(c), l5.FORBID)
        q = l3.compile_program(progs.fib())            # fib(10) recursion: 53 layers (23.3)
        self.assertEqual((l5.cost(q).layers, l5.cost(q).ticks), (53, l5.FORBID))

    def test_ticks_of_programs(self):
        for name, (build, passes, stdin) in PROGRAMS.items():
            p = l3.compile_program(build)
            c = l5.cost(p, passes=passes)
            self.assertEqual(c.ticks, ticks_of(p, stdin), name)

    def test_program_is_sum_of_parts(self):
        for name, (build, passes, _) in PROGRAMS.items():
            p = l3.compile_program(build)
            c, parts = l5.cost(p, passes=passes), l5.parts(p)
            s = sum(parts.values(), l5.ZERO)
            self.assertEqual((s.rows, s.layers, s.bits), (c.rows, c.layers, c.bits), name)
            self.assertEqual(c.layers, len(p.layers), name)
            self.assertEqual(c.bits, l5.text_bits(p.A, p.layers), name)
            self.assertEqual(s.ticks, 0)
            self.assertEqual(c.ticks, l5.ticks(p, None, passes) + l5.BOOT_TICKS)

    def test_call_is_callee_plus_call_rows(self):
        p = l3.compile_program(progs.calls())          # show; pair calls show twice; main calls show twice and pair
        parts, show, pair = l5.parts(p), l5.cost(p, 'show'), l5.cost(p, 'pair')
        self.assertEqual(show[:3], parts['show'][:3])
        self.assertEqual(pair[:3], (parts['pair'] + parts['show'])[:3])           # the callee is stored once
        self.assertEqual(pair.ticks, parts['pair'].layers + 2 * show.ticks)       # and runs once per call
        whole = l5.cost(p)
        self.assertEqual(whole.ticks, l5.BOOT_TICKS + parts[None].layers + 2 * show.ticks + pair.ticks)
        self.assertEqual(whole.ticks, ticks_of(p))
        lone = l3.compile_program(minimal(lambda q: None))
        self.assertGreater(parts[None].layers, l5.cost(lone).layers)               # the call rows lie in the caller

    def test_unknown_passes_are_forbidden(self):
        p = l3.compile_program(progs.loop_digits())
        c = l5.cost(p)
        self.assertEqual((c.ticks, l5.price(c)), (l5.FORBID, l5.FORBID))
        self.assertEqual(l5.cost(p, passes={'loop': 10}).ticks, 124)           # by the formula of passes
        t = [l5.cost(p, passes={'loop': n}).ticks for n in (1, 2, 3, 10)]
        self.assertEqual(t[2] - t[1], t[1] - t[0])                                 # linear in the passes
        self.assertEqual(t[3] - t[2], 7 * (t[1] - t[0]))
        e = l3.compile_program(progs.echo())                                       # a loop closed by goto
        self.assertEqual(l5.cost(e).ticks, l5.FORBID)
        self.assertLess(l5.cost(e, passes={'out': 13}).ticks, l5.FORBID)

    def test_forbid_sums_and_stays(self):
        a = l5.Cost(1, 2, 3, l5.FORBID)
        self.assertEqual((a + a).ticks, l5.FORBID)
        self.assertEqual(l5.price(a + l5.Cost(1, 1, 1, 1)), l5.FORBID)
        self.assertEqual(l5.price(l5.Cost(0, 0, 0, 0)), 0)


class Price(unittest.TestCase):
    def test_formula(self):
        c = l5.Cost(10, 4, 408, 4)
        self.assertEqual(l5.price(c), 32 * 10 + 32 * 4 + 408 + 64 * 4)
        self.assertEqual(l5.price(c, (0, 0, 0, 1)), 4)
        self.assertEqual(l5.price(c, (1, 0, 0, 0)), 10)
        self.assertLess(l5.price(l5.Cost(5, 2, 100, 2)), l5.price(c))


def nibble(twice):
    """Reads a byte from stdin, doubles its low nibble by `twice(p, a, r)` and prints r in hex."""
    def build(p):
        v, r, ch = p.var('v', 8), p.var('r', 5), p.var('ch', 8)
        p.block('main')
        p.key(v.ref())
        twice(p, v[0:4], r)
        p.lut(progs.hexch(p), [r[0:4]], ch.ref())
        p.emit(ch.ref())
        p.halt()
    return build


def by_add(p, a, r):
    p.add(a, a, r)


def by_shl(p, a, r):
    p.shl(a, r[0:4], 1)


def by_shl2(p, a, r):
    p.shl(a, r[0:4], 2)


NIBBLES = [stream(i, 8) for i in range(16)]       # the whole table of the small word


class Replace(unittest.TestCase):
    def test_cheaper_definition_of_a_word(self):
        ch = l5.replace(nibble(by_add), nibble(by_shl), inputs=NIBBLES)       # same result on all 16 inputs
        self.assertEqual(ch.index, 1)
        self.assertLess(ch.prices[1], ch.prices[0])
        self.assertEqual(ch.prices, [l5.price(l5.cost(l3.compile_program(nibble(f)))) for f in (by_add, by_shl)])
        self.assertEqual(l5.replace(nibble(by_shl), nibble(by_add), inputs=NIBBLES).index, 0)

    def test_cheaper_layout(self):
        build = progs.loop_sum()
        passes = {'loop': 10}
        ch = l5.replace((build, dict(serial=True, passes=passes)), (build, dict(passes=passes)), inputs=[b''])
        self.assertEqual(ch.index, 1)                                          # the planner beats one row per layer
        self.assertLess(ch.prices[1], ch.prices[0])
        ch = l5.replace((build, dict(direct=False, passes=passes)), (build, dict(direct=True, passes=passes)))
        self.assertEqual(ch.index, 1)                                          # 23.3 d: fewer layers and ticks
        ch = l5.replace((build, dict(plan=False, passes=passes)), (build, dict(plan=True, passes=passes)))
        self.assertLessEqual(ch.prices[1], ch.prices[0])                       # shared strides never add to the text

    def test_different_results_are_rejected(self):
        with self.assertRaises(ValueError):
            l5.replace(nibble(by_shl), nibble(by_shl2), inputs=NIBBLES)

    def test_chosen_program_runs_alone(self):
        ch = l5.replace(nibble(by_add), nibble(by_shl), inputs=NIBBLES)
        p = ch.program
        r = common.run(p.stats['image'], p.stats['A'], p.stats['P'], stdin=stream(7, 8))
        self.assertEqual((r.rc, r.out), (0, b'e'))


class Isolation(unittest.TestCase):
    def test_lower_languages_do_not_know_the_price(self):
        for f in ('common.py', 'l1.py', 'l2.py', 'l3.py', 'l4.py', 'lib.py'):
            with open(os.path.join(HERE, '..', f), encoding='utf-8') as h:
                text = h.read()
            self.assertIsNone(re.search(r'\bl5\b|\bprice\b|FORBID', text), f)
            self.assertNotIn('text_bits', text, f)


if __name__ == '__main__':
    unittest.main()
