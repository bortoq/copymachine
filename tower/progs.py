"""Check programs written in language 3 (builders over a Program)."""
from common import bytes_value, rev
from l4 import host_pos
from l2 import norm


def hexch(p):
    return p.t_hex()


def dec9(p, n=9):
    return p.t_dec(n)


def print3(p, val9):
    """Print a number of at most 9 bits as three decimal digits and a newline (one lookup, three copies)."""
    d, buf = p.var('dig', 12), p.var('buf', 32, bytes_value(b'000\n'))
    p.lut(dec9(p, norm(val9).n), [val9], d.ref())
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


# --- 23.2: arrays, subtraction, equality, shifts, stdin

def print_hex(p, v, tag):
    """Print the nibbles of v, the most significant first."""
    v = norm(v)
    for k in range(v.n // 4 - 1, -1, -1):
        ch = p.var('%s_%d' % (tag, k), 8)
        p.lut(hexch(p), [v[4*k:4*k+4]], ch.ref())
        p.emit(ch.ref())


def array_rev(vals):
    """Write vals[i] at index 3i mod 8 (8 stores), read indexes 7..0 (a loop with a borrow), print the bytes."""
    def build(p):
        arr = p.array('arr', (3,), 8)
        tv = p.table('vals', (3,), 8, lambda i: rev(vals[i], 8))
        tp = p.table('perm', (3,), 3, lambda i: 3 * i % 8)
        lim = p.table('lt8', (4,), 1, lambda x: int(x < 8))
        i, v, ix, c = p.var('i', 5), p.var('v', 8), p.var('ix', 3), p.var('c', 1)
        j, jr, o = p.var('j', 4, 7), p.var('jr', 5), p.var('o', 8)
        one, nl = p.var('one', 4, 1), p.var('nl', 8, bytes_value(b'\n'))
        p.block('main'); p.goto('wr')
        p.block('wr')
        p.lut(tv, [i[0:3]], v.ref())
        p.lut(tp, [i[0:3]], ix.ref())
        p.store(arr, [ix.ref()], v.ref())
        p.lut(p.t_add(), [i[0:4], one.ref(), p.zero.ref()], i.ref())
        p.lut(lim, [i[0:4]], c.ref())
        p.if_(c.ref(), 'wr', 'rd')
        p.block('rd')
        p.lut(arr, [j[0:3]], o.ref())
        p.emit(o.ref())
        p.sub(j, one, jr)
        p.copy(j.ref(), jr[0:4])
        p.if_(jr[4], 'done', 'rd')
        p.block('done'); p.emit(nl.ref()); p.halt()
    return build


def arith(n, ka, kb):
    """Reads a and b (n bits each) from stdin; prints a-b (n bits), the borrow, a==b, a<<1, a>>1,
    a<<ka, a>>kb, all in hex (a==b and the borrow as a digit)."""
    def build(p):
        a, b, d, e = p.var('a', n), p.var('b', n), p.var('d', n + 1), p.var('e', n // 4)
        f1, f2 = p.var('f1', 4), p.var('f2', 4)
        s = [p.var('s%d' % k, n) for k in range(4)]
        p.block('main')
        for k in range(n // 8):
            p.key(a[8*k:8*k+8])
        for k in range(n // 8):
            p.key(b[8*k:8*k+8])
        p.sub(a, b, d)
        r = p.eq(a, b, e)
        p.shl(a, s[0], 1)
        p.shr(a, s[1], 1)
        p.shl(a, s[2], ka)
        p.shr(a, s[3], kb)
        p.copy(f1[0:1], d[n:n + 1])
        p.copy(f2[0:1], r)
        print_hex(p, d[0:n], 'd')
        print_hex(p, f1, 'f1')
        print_hex(p, f2, 'f2')
        for k in range(4):
            print_hex(p, s[k], 's%d' % k)
        p.halt()
    return build


def echo():
    """stdin to stdout up to a zero byte."""
    def build(p):
        b, z, c = p.var('b', 8), p.var('z', 8), p.var('c', 2)
        p.block('main'); p.goto('loop')
        p.block('loop')
        p.key(b.ref())
        r = p.eq(b, z, c)
        p.if_(r, 'done', 'out')
        p.block('out'); p.emit(b.ref()); p.goto('loop')
        p.block('done'); p.halt()
    return build


# --- 23.4: the long copy to and from the files `-r` and the clock of the host

def long_rw(wpos, data, rpos, n=None):
    """long! of the bytes `data` at the position wpos (if data), long@ of len(data) (or n) bytes at rpos into a
    part of space which starts as 0xff bytes; the bytes read are written to stdout."""
    def build(p):
        m = n if n is not None else len(data)
        got = p.var('got', 8 * m, bytes_value(b'\xff' * m))
        p.block('main')
        if data:
            out = p.var('out', 8 * len(data), bytes_value(data))
            p.long_put(p.var('wpos', 128, wpos), out)
        p.long_get(p.var('rpos', 128, rpos), got.ref())
        p.emit(got.ref())
        p.halt()
    return build


def long_clock():
    """Two reads of the clock (area 0, 64 bits) one after the other; both are written to stdout."""
    def build(p):
        t1, t2 = p.var('t1', 64), p.var('t2', 64)
        p.block('main')
        p.long_get(p.var('pos1', 128, host_pos(0, 0)), t1.ref())
        p.long_get(p.var('pos2', 128, host_pos(0, 0)), t2.ref())
        p.emit(t1.ref())
        p.emit(t2.ref())
        p.halt()
    return build


def long_cat(area, chunks, nbytes, start=0):
    """cat: a loop reads the file (area `area`) in chunks of nbytes bytes from the bit `start`, the position
    is added to by a 128-bit chain of `add`, every chunk goes to stdout; `chunks` (<= 15) times."""
    def build(p):
        pos, step = p.var('pos', 128, host_pos(area, start)), p.var('step', 128, 8 * nbytes)
        nxt, buf = p.var('nxt', 129), p.var('buf', 8 * nbytes, bytes_value(b'?' * nbytes))
        i, one, c = p.var('i', 5), p.var('one', 4, 1), p.var('c', 1)
        lim = p.table('lt%d' % chunks, (4,), 1, lambda x: int(x < chunks))
        p.block('main'); p.goto('loop')
        p.block('loop')
        p.long_get(pos, buf.ref())
        p.emit(buf.ref())
        p.add(pos, step, nxt)
        p.copy(pos.ref(), nxt[0:128])
        p.lut(p.t_add(), [i[0:4], one.ref(), p.zero.ref()], i.ref())
        p.lut(lim, [i[0:4]], c.ref())
        p.if_(c.ref(), 'loop', 'done')
        p.block('done'); p.halt()
    return build
