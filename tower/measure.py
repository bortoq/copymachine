"""Numbers for docs/measurements/tower.md: python3 -B tower/measure.py"""
import os
import sys

sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import l2
import l3
import progs

PROGS = [
    ('add 200+100, decimal', progs.add_print(200, 100), b''),
    ('branch 3<9', progs.branch(3, 9), b''),
    ('loop digits 0..9', progs.loop_digits(), b''),
    ('loop sum 1..10, decimal', progs.loop_sum(), b''),
    ('two words, four calls', progs.calls(), b''),
    ('and 8-bit, hex', progs.and_hex(0xac, 0x3f), b''),
    ('add 16-bit, hex', progs.add16_hex(0x1234, 0xfff), b''),
    ('array, 8 stores + 8 reads', progs.array_rev([65, 10, 255, 0, 128, 127, 19, 196]), b''),
    ('sub eq shl shr 8-bit (stdin)', progs.arith(8, 3, 5), common.stream(200, 8) + common.stream(77, 8)),
    ('sub eq shl shr 16-bit (stdin)', progs.arith(16, 7, 9), common.stream(40000, 16) + common.stream(1234, 16)),
    ('echo, 13 bytes (stdin)', progs.echo(), b'hello, world\n\x00'),
    ('fib(10) recursion (stdin)', progs.fib(), common.stream(10, 8)),
]


def loc(name):
    n = 0
    for line in open(os.path.join(common.HERE, name), encoding='utf-8'):
        s = line.strip()
        if s and not s.startswith('#'):
            n += 1
    return n


def main():
    common.ensure_built()
    print('| program | A | P | blocks | layers | rows | lookups | tables bits | data bits | text bits | image B (boot+snap) | ticks | text L2/L1 |')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    tot1 = tot2 = 0
    extra = []
    for name, b, inp in PROGS:
        p = l3.compile_program(b)
        st = p.stats
        r = common.run(st['image'], st['A'], st['P'], stdin=inp)
        assert r.rc == 0
        rows = sum(len(l.rows) for l in p.layers)
        tb = sum(t.span for t in p.tables.values())
        live = sum((1 << sum(t.ins)) * t.out for t in p.tables.values())
        db = sum(d.bits for d in p.datas) - tb
        one, two = l2.text_bits(p.A, p.layers)
        slots = sum(l.u for l in p.layers)
        used = sum(len(l.rows) + 1 for l in p.layers)
        tot1 += one; tot2 += two
        print('| %s | %d | %d | %d | %d | %d | %d | %d (%d live) | %d | %d | %d (%d+%d) | %d | %.3f |' % (
            name, p.A, st['P'], len(p.blocks), len(p.layers), rows, p.lookups, tb, live, db, one,
            len(st['image']), st['boot_bytes'], st['snapshot_bytes'], r.ticks, two / one))
        extra.append((name, slots, used, one, two, len(st['image']) * 8, sum(len(o) for o in [p.layers])))
    print('\n| program | stored slots | used (rows+jump) | text L1 bits | text L2 bits | saved bits | saved % of image |\n|---|---|---|---|---|---|---|')
    for name, slots, used, one, two, ib, _ in extra:
        print('| %s | %d | %d | %d | %d | %d | %.1f%% |' % (name, slots, used, one, two, one - two, 100 * (one - two) / ib))
    print('\n| program | layers packed / serial | rows | ticks packed / serial | image B packed / serial |\n|---|---|---|---|---|')
    for name, b, inp in PROGS:
        p, q = l3.compile_program(b), l3.compile_program(b, serial=True)
        rp, rq = (common.run(x.stats['image'], x.stats['A'], x.stats['P'], stdin=inp) for x in (p, q))
        assert rq.rc == 0 and rq.out == rp.out
        print('| %s | %d / %d | %d | %d / %d | %d / %d |' % (name, len(p.layers), len(q.layers), sum(len(l.rows) for l in p.layers),
              rp.ticks, rq.ticks, len(p.stats['image']), len(q.stats['image'])))
    print('\nL2 text / L1 text over all programs: %.4f' % (tot2 / tot1))
    print('\nlines of code (no blanks/comments):', {f: loc(f) for f in ('common.py', 'l1.py', 'l2.py', 'l3.py', 'lib.py', 'progs.py', 'tests/test_tower.py')})


main()
