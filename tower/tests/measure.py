"""Numbers for docs/measurements/tower.md: python3 -B tower/tests/measure.py"""
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import l1
import l3
import l5
import progs
import text
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
]


def loc(name):
    n = 0
    for line in open(os.path.join(common.HERE, name if '/' in name else 'tests/' + name), encoding='utf-8'):
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
        two = l5.text_bits(p.A, p.layers)
        one = sum(l.u for l in p.layers) * 4 * p.A
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
    print('\nlines of code (no blanks/comments):', {f: loc(f) for f in ('common.py', 'l1.py', 'l2.py', 'l3.py', 'l4.py', 'l5.py', 'lib.py', 'progs.py', 'tests/test_tower.py', 'tests/test_long.py', 'tests/test_price.py', 'text.py', 'tests/test_text.py')})


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


def main_price():
    """23.5: language 5. The price of every word of languages 1-4 (one word + halt, less the empty main)."""
    import test_price as tp
    pos = host_pos(1, 8)
    ctx = [
        ('1', 'row (one raw row)', minimal(lambda p: p._op(l1.row(0, 0, 0, 0), [], []))),
        ('2', 'copy 8 bits', minimal(lambda p: p.copy(p.var('d', 8), p.var('s', 8, 5)))),
        ('2', 'data (a named part of space)', minimal(lambda p: p.var('d', 64))),
        ('3', 'table + lut, 1 arg', tp.CONSTRUCTS['lut, 1 arg'][0]),
        ('3', 'lut add4, 3 args', tp.CONSTRUCTS['lut add4, 3 args'][0]),
        ('3', 'array + store', tp.CONSTRUCTS['store'][0]),
        ('3', 'block, goto (empty block)', lambda p: (p.block('main'), p.goto('b'), p.block('b'), p.halt())),
        ('3', 'if', tp.CONSTRUCTS['if'][0]),
        ('3', 'word, call, ret', tp.CONSTRUCTS['call + ret'][0]),
        ('3', 'emit 8 bits', minimal(lambda p: p.emit(p.var('d', 8, 5)))),
        ('3', 'key 8 bits', minimal(lambda p: p.key(p.var('d', 8)))),
        ('lib', 'shl 8 bits by 1', minimal(lambda p: p.shl(p.var('a', 8), p.var('r', 8), 1))),
        ('lib', 'shr 8 bits by 3', minimal(lambda p: p.shr(p.var('a', 8), p.var('r', 8), 3))),
        ('lib', 'add 4 bits', minimal(lambda p: p.add(p.var('a', 4), p.var('b', 4), p.var('r', 5)))),
        ('lib', 'add 8 bits', minimal(lambda p: p.add(p.var('a', 8), p.var('b', 8), p.var('r', 9)))),
        ('lib', 'add 16 bits', minimal(lambda p: p.add(p.var('a', 16), p.var('b', 16), p.var('r', 17)))),
        ('lib', 'add 32 bits', minimal(lambda p: p.add(p.var('a', 32), p.var('b', 32), p.var('r', 33)))),
        ('lib', 'sub 8 bits', minimal(lambda p: p.sub(p.var('a', 8), p.var('b', 8), p.var('r', 9)))),
        ('lib', 'band 8 bits', minimal(lambda p: p.band(p.var('a', 8), p.var('b', 8), p.var('r', 8)))),
        ('lib', 'lt 8 bits', minimal(lambda p: p.lt(p.var('a', 8), p.var('b', 8), p.var('c', 3)))),
        ('lib', 'eq 8 bits', minimal(lambda p: p.eq(p.var('a', 8), p.var('b', 8), p.var('c', 2)))),
        ('4', 'long! 48 bits', tp.CONSTRUCTS['long! 48'][0]),
        ('4', 'long@ 48 bits (buffer)', tp.CONSTRUCTS['long@ 48 (buffer)'][0]),
        ('4', 'long@ 128 bits (direct)', tp.CONSTRUCTS['long@ 128 (direct)'][0]),
        ('4', 'position + step, add 128 bits', minimal(lambda p: p.add(p.var('a', 128, pos), p.var('b', 128, 64), p.var('r', 129)))),
    ]
    e = l5.cost(l3.compile_program(minimal(lambda p: None)))
    print('\n| lang | word (program: one word + halt) | rows | layers | text bits | ticks | price |\n|---|---|---|---|---|---|---|')
    for lang, name, b in ctx:
        p = l3.compile_program(b)
        c = l5.cost(p)
        d = l5.Cost(c.rows - e.rows, c.layers - e.layers, c.bits, c.ticks - e.ticks if c.ticks < l5.FORBID else l5.FORBID)
        print('| %s | %s | %+d | %+d | %d | %s | %s |' % (lang, name, d.rows, d.layers, c.bits,
              ('%+d' % d.ticks) if d.ticks < l5.FORBID else 'FORBID', l5.price(c) if d.ticks < l5.FORBID else 'FORBID'))
    print('\nempty main + halt: rows %d, layers %d, text bits %d (A=10), ticks %d, price %d' % (*e, l5.price(e)))


def main_text():
    """23.6: the text of programs. Words per level, the lines of every program, the dictionary on the chain."""
    levels = {}
    for w, (lv, _, _) in text.WORDS.items():
        levels.setdefault(lv, []).append(w)
    print('\nwords by language:', {lv: len(ws) for lv, ws in sorted(levels.items())}, 'total', len(text.WORDS))
    print('\n| program | lines of text (no blanks, no comments) | tokens | image B | same image as the builder |\n|---|---|---|---|---|')
    pdir = os.path.join(common.HERE, 'programs')
    for f in sorted(x for x in os.listdir(pdir) if x.endswith('.tw') and os.path.isfile(os.path.join(pdir, x))):
        src = open(os.path.join(pdir, f), encoding='utf-8').read()
        n = sum(1 for x in src.split('\n') if x.strip() and not x.strip().startswith('#'))
        p = text.compile_text(src)[0]
        if p is None:
            continue
        print('| %s | %d | %d | %d | %s |' % (f, n, len(list(text.tokens(src))), len(p.stats['image']), 'yes' if f[:-3] in progs_by_name() else 'no builder: text only'))
    src = open(os.path.join(pdir, 'dict.tw'), encoding='utf-8').read()
    p = text.compile_text(src, level=3)[0]
    st = p.stats
    views = {id(t.data) for t in p.tables.values()}
    print('\ndict.tw: A %d, P %d, layers %d, rows %d, lookups %d, tables bits %d, data bits %d, image %d B (boot %d + snapshot %d)' % (
        p.A, st['P'], len(p.layers), sum(len(x.rows) for x in p.layers), p.lookups, sum(x.bits for x in p.gdatas),
        sum(x.bits for x in p.datas if id(x) not in views), len(st['image']), st['boot_bytes'], st['snapshot_bytes']))
    base = common.run(st['image'], st['A'], st['P'], stdin=b'\x00', limit=2000000).ticks
    print('ticks of an empty text (one zero byte): %d' % base)
    print('\n| input (repeated 10 times, one space after each) | ticks per word |\n|---|---|')
    per = {}
    for label, w in (('first word of the dictionary: copy', b'copy'), ('last word of the dictionary: stack', b'stack'),
                     ('not in the dictionary: zzz', b'zzz'), ('number 7', b'7'), ('number 65535', b'65535')):
        r = common.run(st['image'], st['A'], st['P'], stdin=(w + b' ') * 10 + b'\x00', limit=2000000)
        assert r.rc == 0
        per[w] = (r.ticks - base) / 10
        print('| %s | %.1f |' % (label, per[w]))
    t = lambda w: common.run(st['image'], st['A'], st['P'], stdin=w + b' \x00', limit=2000000).ticks
    print('\nticks per separator byte (spaces only) %.1f; per further letter of a word %.1f; per further digit %.1f' % (
        (common.run(st['image'], st['A'], st['P'], stdin=b' ' * 6 + b'\x00', limit=2000000).ticks - base) / 6,
        (t(b'zzzzz') - t(b'z')) / 4, (t(b'11111') - t(b'1')) / 4))
    print('search: %.1f ticks per dictionary entry compared' % ((per[b'stack'] - per[b'copy']) / 15))


def progs_by_name():
    return {'add', 'branch', 'loop_digits', 'loop_sum', 'calls', 'and_hex', 'add16_hex', 'array', 'arith8', 'arith16',
            'echo', 'long_rw', 'long_read', 'long_clock', 'long_cat'}


main()
main_long()
main_price()
main_text()
