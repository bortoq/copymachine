"""Library over languages 2 and 3 (a mixin of l3.Program; it adds no row of its own).
Over language 2 (copy, data): shl, shr. Over language 3 (lut, array, store): hex and decimal tables, add, sub, band, lt, eq
(chains over 4-bit tables with carry), stack, push, pop, rec (recursive words keep return links in a stack).
Numbers are any number of nibbles, the least significant bit first."""
from common import rev
from l2 import norm


class Stack:
    """An array of 2**k entries of w bits and a pointer of k bits (named parts of space)."""

    def __init__(self, arr, sp, inc, dec, d=1):
        self.arr, self.sp, self.inc, self.dec, self.d = arr, sp, inc, dec, d


class Lib:
    # --- over language 2: a shift by a constant is a copy with another offset
    def shl(self, a, r, k=1):
        """r = a << k (same width, high bits dropped); r is another part of space than a."""
        a, r = norm(a), norm(r)
        assert a.n == r.n and k >= 0
        k = min(k, a.n)
        if k < a.n:
            self.copy(r[k:a.n], a[0:a.n - k])
        if k:
            self.copy(r[0:k], self.zeros(k))

    def shr(self, a, r, k=1):
        """r = a >> k (same width, zeros come in); r is another part of space than a."""
        a, r = norm(a), norm(r)
        assert a.n == r.n and k >= 0
        k = min(k, a.n)
        if k < a.n:
            self.copy(r[0:a.n - k], a[k:a.n])
        if k:
            self.copy(r[a.n - k:a.n], self.zeros(k))

    # --- over language 3: n-nibble chains over 4-bit tables
    def t_add(self):
        return self.table('add4', (4, 4, 1), 5, lambda a, b, c: a + b + c)

    def t_sub(self):
        return self.table('sub4', (4, 4, 1), 5, lambda a, b, c: (a - b - c) & 31)

    def t_hex(self):
        """Hex digit of a nibble as a character (a byte in the order of the stream)."""
        return self.table('hex4', (4,), 8, lambda x: rev(ord('0123456789abcdef'[x]), 8))

    def t_dec(self, n):
        """Three decimal digits of an n-bit number (n <= 10), 4 bits each, in the order of the stream."""
        def f(x):
            return rev(x // 100, 4) | rev(x // 10 % 10, 4) << 4 | rev(x % 10, 4) << 8
        return self.table('dec%d' % n, (n,), 12, f)

    def _chain(self, t, a, b, r):
        """r[4i:4i+5] = t(a_i, b_i, r[4i]); the first carry is 0, r[n] is the last carry."""
        a, b, r = norm(a), norm(b), norm(r)
        n = a.n // 4
        assert a.n % 4 == 0 and b.n == a.n and r.n == 4 * n + 1
        self.lut(t, [a[0:4], b[0:4], self.zero.ref()], r[0:5])
        for i in range(1, n):
            self.lut(t, [a[4*i:4*i+4], b[4*i:4*i+4], r[4*i:4*i+1]], r[4*i:4*i+5])

    def add(self, a, b, r):
        self._chain(self.t_add(), a, b, r)

    def sub(self, a, b, r):
        """r = a - b modulo 2**n; r[n] = 1 when a < b (borrow)."""
        self._chain(self.t_sub(), a, b, r)

    def band(self, a, b, r):
        a, b, r = norm(a), norm(b), norm(r)
        t = self.table('and4', (4, 4), 4, lambda a, b: a & b)
        for i in range(a.n // 4):
            self.lut(t, [a[4*i:4*i+4], b[4*i:4*i+4]], r[4*i:4*i+4])

    def lt(self, a, b, c):
        """c has n+1 bits, c[0] stays 0; c[n] = (a < b)."""
        a, b, c = norm(a), norm(b), norm(c)
        t = self.table('lt4c', (4, 4, 1), 1, lambda a, b, c: int(a < b or (a == b and c)))
        for i in range(a.n // 4):
            self.lut(t, [a[4*i:4*i+4], b[4*i:4*i+4], c[i:i+1]], c[i+1:i+2])

    def eq(self, a, b, c):
        """c has n bits (n nibbles of a); c[n-1] = (a == b), which eq returns."""
        a, b, c = norm(a), norm(b), norm(c)
        n = a.n // 4
        assert a.n % 4 == 0 and b.n == a.n and c.n == n
        t = self.table('eq4c', (4, 4, 1), 1, lambda a, b, c: int(a == b and c))
        self.lut(t, [a[0:4], b[0:4], self.one()], c[0:1])
        for i in range(1, n):
            self.lut(t, [a[4*i:4*i+4], b[4*i:4*i+4], c[i-1:i]], c[i:i+1])
        return c[n-1:n]

    # --- stack as data: an array and a pointer; no bounds (the pointer wraps in its k bits)
    def stack(self, name, k, w, dup=True):
        """The pointer is kept twice (dup): [p][p] in 2k bits, both copies are sources of the patches
        of one layer; the tables inc, dec give both copies at once."""
        m = (1 << k) - 1
        d = 2 if dup else 1
        return Stack(self.array(name, (k,), w), self.var(name + '_sp', d * k),
                     self.table('inc%d_%d' % (k, d), (k,), d * k, lambda x: ((x + 1) & m) * (1 + (d - 1 << k))),
                     self.table('dec%d_%d' % (k, d), (k,), d * k, lambda x: ((x - 1) & m) * (1 + (d - 1 << k))), d)

    @staticmethod
    def _p(s):
        k = s.sp.bits // s.d
        return (s.sp[0:k], s.sp[k:2 * k]) if s.d == 2 else s.sp[0:k]

    def push(self, s, src):
        self.store(s.arr, [self._p(s)], src)
        self.lut(s.inc, [self._p(s)], s.sp.ref())

    def pop(self, s, dst):
        self.lut(s.dec, [self._p(s)], s.sp.ref())
        self.lut(s.arr, [self._p(s)], dst)

    def rec(self, name, s):
        """Declare the word `name` recursive: call pushes the return link on s, ret pops it from s."""
        assert s.arr.out == 2 * self.A and name not in self.words, name
        self.recs[name] = s
