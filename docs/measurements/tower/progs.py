"""Check programs written in language 3 (builders over a Program)."""
from common import bytes_value, rev


def hexch(p):
    return p.table('hex4', (4,), 8, lambda x: rev(ord('0123456789abcdef'[x]), 8))


def dec9(p):
    def f(x):
        return rev(x // 100, 4) | rev(x // 10 % 10, 4) << 4 | rev(x % 10, 4) << 8
    return p.table('dec9', (9,), 12, f)


def print3(p, val9):
    """Print a 9-bit number as three decimal digits and a newline (one lookup, three copies)."""
    d, buf = p.var('dig', 12), p.var('buf', 32, bytes_value(b'000\n'))
    p.lut(dec9(p), [val9], d.ref())
    for i in range(3):
        p.copy(buf[8*i+4:8*i+8], d[4*i:4*i+4])
    p.emit(buf.ref())


def add_print(a, b):
    def build(p):
        ra, rb, r = p.var('a', 8, a), p.var('b', 8, b), p.var('r', 9)
        p.block('main')
        p.add(ra, rb, r)
        print3(p, r.ref())
        p.halt()
    return build


def branch(a, b):
    def build(p):
        ra, rb, c = p.var('a', 8, a), p.var('b', 8, b), p.var('c', 3)
        y, n, nl = (p.var(k, 8, bytes_value(v)) for k, v in (('y', b'Y'), ('n', b'N'), ('nl', b'\n')))
        p.block('main')
        p.lt(ra, rb, c)
        p.if_(c[2], 'yes', 'no')
        p.block('yes'); p.emit(y.ref()); p.goto('end')
        p.block('no'); p.emit(n.ref()); p.goto('end')
        p.block('end'); p.emit(nl.ref()); p.halt()
    return build


def loop_digits(build_limit=10):
    def build(p):
        i, ch, c = p.var('i', 5, 0), p.var('ch', 8), p.var('c', 1)
        one, nl = p.var('one', 4, 1), p.var('nl', 8, bytes_value(b'\n'))
        lim = p.table('lt%d' % build_limit, (4,), 1, lambda x: int(x < build_limit))
        p.block('main'); p.goto('loop')
        p.block('loop')
        p.lut(hexch(p), [i[0:4]], ch.ref())
        p.emit(ch.ref())
        p.lut(p.t_add(), [i[0:4], one.ref(), p.zero.ref()], i.ref())
        p.lut(lim, [i[0:4]], c.ref())
        p.if_(c.ref(), 'loop', 'done')
        p.block('done'); p.emit(nl.ref()); p.halt()
    return build


def loop_sum():
    """Sum 1..10 in an 8-bit variable and print it in decimal."""
    def build(p):
        i, s, r = p.var('i', 8, 1), p.var('s', 9, 0), p.var('r', 9)
        c, one = p.var('c', 1), p.var('one', 4, 1)
        lim = p.table('lt11', (4,), 1, lambda x: int(x < 11))
        p.block('main'); p.goto('loop')
        p.block('loop')
        p.add(s[0:8], i.ref(), r.ref())
        p.copy(s[0:8], r[0:8])
        p.lut(p.t_add(), [i[0:4], one.ref(), p.zero.ref()], i[0:5])
        p.lut(lim, [i[0:4]], c.ref())
        p.if_(c.ref(), 'loop', 'done')
        p.block('done'); print3(p, s.ref()); p.halt()
    return build


def calls():
    """Word show prints a hex digit of x; called from four places (two directly, two via pair)."""
    def build(p):
        x, ch = p.var('x', 4), p.var('ch', 8)
        k3, k10, k12 = p.var('k3', 4, 3), p.var('k10', 4, 10), p.var('k12', 4, 12)
        nl = p.var('nl', 8, bytes_value(b'\n'))
        p.block('main'); p.copy(x.ref(), k3.ref()); p.call('show', 'm1')
        p.block('m1'); p.copy(x.ref(), k10.ref()); p.call('show', 'm2')
        p.block('m2'); p.call('pair', 'm3')
        p.block('m3'); p.emit(nl.ref()); p.halt()
        p.word('show')
        p.lut(hexch(p), [x.ref()], ch.ref()); p.emit(ch.ref()); p.ret()
        p.word('pair')
        p.copy(x.ref(), k12.ref()); p.call('show', 'p1')
        p.block('p1'); p.copy(x.ref(), k3.ref()); p.call('show', 'p2')
        p.block('p2'); p.ret()
    return build


def and_hex(a, b):
    def build(p):
        ra, rb, r = p.var('a', 8, a), p.var('b', 8, b), p.var('r', 8)
        ch = p.var('ch', 8)
        p.block('main')
        p.band(ra, rb, r)
        for k in (1, 0):
            p.lut(hexch(p), [r[4*k:4*k+4]], ch.ref())
            p.emit(ch.ref())
        p.halt()
    return build


def add16_hex(a, b):
    def build(p):
        ra, rb, r = p.var('a', 16, a), p.var('b', 16, b), p.var('r', 17)
        chs = [p.var('ch%d' % k, 8) for k in range(4)]
        p.block('main')
        p.add(ra, rb, r)
        for k in range(4):
            p.lut(hexch(p), [r[4*(3-k):4*(3-k)+4]], chs[k].ref())
        for k in range(4):
            p.emit(chs[k].ref())
        p.halt()
    return build
