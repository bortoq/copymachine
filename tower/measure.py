"""Numbers for docs/measurements/tower.md: python3 -B tower/measure.py"""
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import l2
import l3
import progs
from l4 import host_pos

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
        tb = sum(d.bits for d in p.gdatas)
        live = sum((1 << sum(t.ins)) * t.out for t in p.tables.values())
        views = {id(t.data) for t in p.tables.values()}
        db = sum(d.bits for d in p.datas if id(d) not in views)
        one, two = l2.text_bits(p.A, p.layers)
        slots = sum(l.u for l in p.layers)
        used = sum(len(l.rows) + len(l.jumps) for l in p.layers)
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
    print('\nlines of code (no blanks/comments):', {f: loc(f) for f in ('common.py', 'l1.py', 'l2.py', 'l3.py', 'l4.py', 'lib.py', 'progs.py', 'tests/test_tower.py', 'tests/test_long.py')})


def minimal(build):
    def b(p):
        p.block('main')
        build(p)
        p.halt()
    return b


def main_long():
    """23.4: language 4. One long! / long@ alone, the position chain, cat, the clock."""
    d = tempfile.mkdtemp(prefix='tower-measure-')
    f = os.path.join(d, 'f')
    with open(f, 'wb') as h:
        h.write(bytes(range(1, 65)))
    pos, pos2 = host_pos(1, 8), host_pos(1, 1 << 40)
    big = [
        ('empty main + halt', minimal(lambda p: None)),
        ('long! 48 bits', minimal(lambda p: p.long_put(p.var('pos', 128, pos), p.var('d', 48, 7)))),
        ('long! 1024 bits', minimal(lambda p: p.long_put(p.var('pos', 128, pos), p.var('d', 1024, 7)))),
        ('long@ 48 bits (through the answer buffer)', minimal(lambda p: p.long_get(p.var('pos', 128, pos), p.var('d', 48)))),
        ('long@ 128 bits (direct)', minimal(lambda p: p.long_get(p.var('pos', 128, pos), p.var('d', 128)))),
        ('long@ 1024 bits (direct)', minimal(lambda p: p.long_get(p.var('pos', 128, pos), p.var('d', 1024)))),
        ('long! then long@ 48 bits', minimal(lambda p: (p.long_put(p.var('pos', 128, pos), p.var('d', 48, 7)),
                                                         p.long_get(p.var('pos2', 128, pos2), p.var('e', 48))))),
        ('128-bit add alone (position + step)', minimal(lambda p: p.add(p.var('a', 128, pos), p.var('b', 128, 64), p.var('r', 129)))),
        ('clock twice, written to stdout', progs.long_clock()),
        ('cat, 5 chunks of 8 bytes', progs.long_cat(1, 5, 8)),
        ('cat, 3 chunks of 16 bytes', progs.long_cat(1, 3, 16)),
    ]
    print('\n| program | A | P | layers | rows | lookups | tables bits | data bits | image B (boot+snap) | ticks |\n|---|---|---|---|---|---|---|---|---|---|')
    for name, b in big:
        p = l3.compile_program(b)
        st = p.stats
        r = common.run(st['image'], st['A'], st['P'], files=[f])
        assert r.rc == 0, r.err
        views = {id(t.data) for t in p.tables.values()}
        print('| %s | %d | %d | %d | %d | %d | %d | %d | %d (%d+%d) | %d |' % (
            name, p.A, st['P'], len(p.layers), sum(len(x.rows) for x in p.layers), p.lookups, sum(x.bits for x in p.gdatas),
            sum(x.bits for x in p.datas if id(x) not in views), len(st['image']), st['boot_bytes'], st['snapshot_bytes'], r.ticks))
    shutil.rmtree(d, True)


main()
main_long()
