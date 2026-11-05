"""The text of language 3 for the compiler of language 3 (host, Python, temporary): what the chain tool `programs/l3c.tw` reads, and the
Python reference of it (23.9, part 2). The tool is the compiler of language 3 as a program of the chain: stdin is a text of language 3
and a zero byte, stdout is a text of language 2 with labels (what `programs/l2l.tw` reads: `l2l` takes the text twice, and the output of
the tool ends with a zero byte, so `cat out out` is `text 0 text 0`) and a zero byte. So the chain of the build is
    text of language 3 -> l3c -> text of language 2 with labels -> l2l -> text of language 1 -> seed -> the image
The layout is SERIAL: every row of the text is a layer of its own (two slots: the row and the jump to the next layer), nothing is
packed, there is no planner (23.10 brings it back as an improvement). A is fixed, 20 (the numbers of language 2 are 20 bits), P is 2 (`common.run(image, 20, 2)`).

The subset of the text of language 3 (text.py reads more; what is left out is told below). Words, separated by blanks and line breaks
(`#` starts a comment to the end of the line):
  :name data n v          n bits (1..65536), v a number (decimal, taken modulo 2^20) or a string "..." of at most 32 bytes
  :name table K w v...    2^K values (K 1..10, w 1..64 bits), numbers or strings of w/8 bytes
  :name array K w         a table which is written (all zeros)
  copy d s   shl x r k   shr x r k   (k 0..64)   emit s   warn s   key d
  lut &T args.. out    store &T args.. src       T is a table, an array, or add4 sub4 hex4 (made at the end of the image)
  add sub band lt eq x y r                        the library over the tables above (the widths as in lib.py)
  :name block   :name word   goto b   if c b1 b2   call w b   ret   halt         (the entry block is `main`)
A part of space is `&name`, `&name[k]`, `&name[lo:hi]` (a data defined before). Names are 1..14 bytes of A-Z a-z 0-9 _ (not a digit first);
the names of blocks and words must be a-z 0-9 _ (the tool l2l takes them as labels `b<name>`, `r<name>`), `zero` is a part of space of
1 bit which is 0. Data, tables and arrays are declared outside a block; a word or a block begins after the end of the block before.
Left out (text.py has them): language 4 (long! long@), stack push pop rec, dec<n>, 0x numbers, 'c' characters, \\x escapes, the
tables with several indices of a user, the check that a copy does not cover itself, that `zero` is not written, and that a part of
space of shl/shr differs from its source; the packing of tables (every table has its own stride, w.bit_length() bits).
Errors (stderr, halt; the output is cut after the last word that was complete; there is no zero byte): `l3c: bad text` (a wrong
character or token, an unknown word, a wrong kind or number of arguments, a label where it does not belong, the text ends inside a word), `l3c: bad label` (a name repeated, not defined before, the 1021st of a user, as 1024 places are in the table of names), `l3c: bad width` (widths do not agree, a part
outside its data), `l3c: bad block` (a row outside a block, after its end, a block without an end, `ret` outside a word, a declaration in a block), `l3c: too big` (the image does not
fit A = 20). Not checked, but defined: numbers over 20 bits (modulo 2^20), a value wider than its field.
The layout (positions are bits of the snapshot): the boot layer at 0 (the row 0, the jump to `main`), 64 zero bits (`zero` is the first,
`zeros` for shl/shr), the bit `one`, then in the order of the text: data, tables and arrays (a table at a multiple of its span
2^(w.bit_length() + K)), the words of a block (a layer each; lut and store: a patch of the row for every field, a layer which has nothing
but the jump, the row), the return link of a word (40 bits before its first block), the table of `if` and the link of `call` after the last
layer of the block; at the end the tables add4 .. hex4 which were used, then zeros up to a whole byte; label `e` is the end.
Run: python3 tower/l3ctext.py -e < prog.tw > prog.l2z   (the reference of the tool)
     python3 tower/l3ctext.py -t > l3c.img                (the image of the tool: A = 20, P = 3, run it with `emulator -s 1048570 -p 3`)
     python3 tower/l3ctext.py -l < prog.tw > prog.l1      (the text of language 1 of a program: l3c, then l2l; for l3c.tw it is programs/l3c.l1)"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

A = 20
RB, JB = 4 * A, 8 * A                 # a row, a layer (the row and the jump)
S1, S2, S3 = (1 << A) - 5, (1 << A) - 4, (1 << A) - 3      # stdin, stdout, stderr (S+1 .. S+3)
M = (1 << A) - 1
LIMIT = 0xfa000
MESSAGES = {'bad': 'l3c: bad text\n', 'lab': 'l3c: bad label\n', 'wid': 'l3c: bad width\n', 'blk': 'l3c: bad block\n',
            'big': 'l3c: too big\n'}
MAXSYM = 1020                          # the symbols of a user (with add4, sub4, hex4, zero they fill the 1024 places)
MAXSTR = 32
ZERO_ADDR, ONE_ADDR, START = JB, JB + 64, JB + 65
WS = b' \t\r\n'
IDENT = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_')
DIGITS = frozenset(b'0123456789')
ESC = {ord('n'): 10, ord('t'): 9, ord('r'): 13, ord('0'): 0, ord('\\'): 92, ord('"'): 34}

# the words: kinds of the arguments (R a part of space, N a number lo..hi, V a value, B a block &name, T a table)
WORDS = ['data', 'table', 'array', 'copy', 'shl', 'shr', 'lut', 'store', 'block', 'word', 'goto', 'if', 'call', 'ret', 'halt',
         'emit', 'warn', 'key', 'add', 'sub', 'band', 'lt', 'eq']
CODE = {w: i for i, w in enumerate(WORDS)}
DEFINING = ('data', 'table', 'array', 'block', 'word')
SHAPE = {'data': ('N1:65536', 'V'), 'table': ('N1:10', 'N1:64'), 'array': ('N1:10', 'N1:64'), 'copy': ('R', 'R'),
         'shl': ('R', 'R', 'N0:64'), 'shr': ('R', 'R', 'N0:64'), 'block': (), 'word': (), 'goto': ('B',), 'if': ('R', 'B', 'B'),
         'call': ('B', 'B'), 'ret': (), 'halt': (), 'emit': ('R',), 'warn': ('R',), 'key': ('R',)}
for _w in ('add', 'sub', 'band', 'lt', 'eq'):
    SHAPE[_w] = ('R', 'R', 'R')
SHAPE['lut'] = SHAPE['store'] = ('T',)         # the rest depends on the table

# the tables the tool makes at the end: name -> (label, index widths, out, function of the indices)
BUILTIN = {
    'add4': ('ta', (4, 4, 1), 5, lambda a, b, c: a + b + c),
    'sub4': ('ts', (4, 4, 1), 5, lambda a, b, c: (a - b - c) & 31),
    'and4': ('tn', (4, 4), 4, lambda a, b: a & b),
    'lt4c': ('tl', (4, 4, 1), 1, lambda a, b, c: int(a < b or (a == b and c))),
    'eq4c': ('te', (4, 4, 1), 1, lambda a, b, c: int(a == b and c)),
    'hex4': ('th', (4,), 8, lambda x: rev8(ord('0123456789abcdef'[x]))),
}
ORDER = list(BUILTIN)
EXPLICIT = ('add4', 'sub4', 'hex4')       # the tables which a text may name (the others are made for add sub band lt eq)


def rev8(c):
    return int(format(c, '08b')[::-1], 2)


class Stop(Exception):
    def __init__(self, why):
        super().__init__(why)
        self.why = why


class Tab:
    """A table (the stride is 2^j, an entry has `out` bits, the index has the widths `ins`, `base` is a number or a label)."""

    def __init__(self, ins, out, base, array=False):
        self.ins, self.out, self.base, self.array = tuple(ins), out, base, array
        self.j = out.bit_length()
        self.K = sum(ins)


class Compiler:
    def __init__(self):
        self.out = []
        self.pos = START
        self.syms = {}                        # name -> ('data', addr, bits) | ('tab', Tab)
        self.used = set()
        self.block_open = False
        self.word = None                      # the word of the block in hand (the label of the return link)

    # --- output
    def put(self, s):
        self.out.append(s)

    def zrun(self, n):
        while n >= 255:
            self.put('z ff\n')
            n -= 255
        if n:
            self.put('z %x\n' % n)

    def align(self, bits):
        pad = -self.pos % (1 << bits)
        self.zrun(pad)
        self.pos += pad

    def check(self, need=0):
        if self.pos + need > LIMIT:
            raise Stop('big')

    def layer(self, row, target=None):
        self.put(row)
        self.put('c a0 0 %s\n' % (target if target is not None else '%x' % (self.pos + JB)))
        self.pos += JB

    def c(self, n, d, s):
        return 'c %x %s %s\n' % (n, d if isinstance(d, str) else '%x' % d, s if isinstance(s, str) else '%x' % s)

    def quad(self, a, b, c, d):
        return ''.join('d 14 %s\n' % (x if isinstance(x, str) else '%x' % x) for x in (a, b, c, d))

    GAP = 'z 50\n'

    # --- values
    def value(self, w, tok):
        kind, v = tok
        if kind == 'num':
            m = min(w, 20)
            self.put('d %x %x\n' % (m, v))
            self.zrun(w - m)
        else:
            for ch in v:
                self.put('d 8 %x\n' % rev8(ch))
            self.zrun(w - 8 * len(v))

    # --- the words
    def w_data(self, label, n, v):
        if v[0] == 'str' and 8 * len(v[1]) > n:
            raise Stop('wid')
        self.check(n)
        self.syms[label] = ('data', self.pos, n)
        self.value(n, v)
        self.pos += n

    def table_begin(self, label, K, w, array):
        t = Tab((K,), w, 0, array)
        span = 1 << (t.j + K)
        pad = -self.pos % span
        self.check(pad + span)
        self.align(t.j + K)
        t.base = self.pos
        self.syms[label] = ('tab', t)
        if array:
            self.zrun(span)
        self.pos += span
        return t

    def entry(self, t, v):
        stride = 1 << t.j
        if v[0] == 'num':
            m = min(stride, 20)
            self.put('d %x %x\n' % (m, v[1]))
            self.zrun(stride - m)
        else:
            self.value(t.out, v)
            self.zrun(stride - t.out)

    def lut_(self, t, args, out):
        m = 2 * len(args)
        ra = self.pos + (m + 1) * JB
        off = 0
        for (a, _n), k in zip(args, t.ins, strict=True):
            self.layer(self.c(k, ra + 2 * A + t.j + off, a))
            self.layer(self.c(k, ra + 3 * A + t.j + off, a))
            off += k
        self.layer(self.GAP)
        self.layer(self.c(t.out, out[0], t.base))

    def store_(self, t, args, src):
        m = 2 * len(args)
        ra = self.pos + (m + 1) * JB
        off = 0
        for (a, _n), k in zip(args, t.ins, strict=True):
            self.layer(self.c(k, ra + t.j + off, a))
            self.layer(self.c(k, ra + A + t.j + off, a))
            off += k
        self.layer(self.GAP)
        self.layer(self.c(t.out, t.base, src[0]))

    def builtin(self, name):
        lab, ins, out, _ = BUILTIN[name]
        self.used.add(name)
        return Tab(ins, out, '&' + lab)

    def lib(self, op, x, y, r):
        n = x[1]
        if n % 4 or y[1] != n:
            raise Stop('wid')
        k = n // 4
        want = {'add': n + 1, 'sub': n + 1, 'band': n, 'eq': k}.get(op)
        if (r[1] < k + 1) if op == 'lt' else (r[1] != want):
            raise Stop('wid')
        self.check()
        t = self.builtin({'add': 'add4', 'sub': 'sub4', 'band': 'and4', 'lt': 'lt4c', 'eq': 'eq4c'}[op])
        sx = lambda i: (x[0] + 4 * i, 4)   # noqa: E731
        sy = lambda i: (y[0] + 4 * i, 4)   # noqa: E731
        sr = lambda i, w: (r[0] + i, w)    # noqa: E731
        if op == 'band':
            for i in range(k):
                self.lut_(t, [sx(i), sy(i)], sr(4 * i, 4))
        elif op in ('add', 'sub'):
            self.lut_(t, [sx(0), sy(0), (ZERO_ADDR, 1)], sr(0, 5))
            for i in range(1, k):
                self.lut_(t, [sx(i), sy(i), sr(4 * i, 1)], sr(4 * i, 5))
        elif op == 'lt':
            for i in range(k):
                self.lut_(t, [sx(i), sy(i), sr(i, 1)], sr(i + 1, 1))
        else:
            self.lut_(t, [sx(0), sy(0), (ONE_ADDR, 1)], sr(0, 1))
            for i in range(1, k):
                self.lut_(t, [sx(i), sy(i), sr(i - 1, 1)], sr(i, 1))

    def shift(self, op, x, r, k):
        n = x[1]
        if r[1] != n:
            raise Stop('wid')
        self.check()
        k = min(k, n)
        if op == 'shl':
            if k < n:
                self.layer(self.c(n - k, r[0] + k, x[0]))
            if k:
                self.layer(self.c(k, r[0], ZERO_ADDR))
        else:
            if k < n:
                self.layer(self.c(n - k, r[0], x[0] + k))
            if k:
                self.layer(self.c(k, r[0] + n - k, ZERO_ADDR))

    def need_block(self, w):
        if not self.block_open:
            raise Stop('blk')
        if w == 'ret' and self.word is None:
            raise Stop('blk')

    def action(self, w, label, a):
        """Run a word whose arguments a are all there (and checked as tokens)."""
        if w == 'data':
            self.w_data(label, a[0], a[1])
        elif w == 'array':
            self.table_begin(label, a[0], a[1], True)
        elif w == 'block':
            self.put(':b%s\n' % label)
            self.block_open = True
        elif w == 'word':
            self.check()
            self.put(':r%s\nz 28\n' % label)
            self.pos += 40
            self.put(':b%s\n' % label)
            self.word, self.block_open = label, True
        elif w == 'copy':
            d, s = a
            if d[1] != s[1]:
                raise Stop('wid')
            self.check()
            self.layer(self.c(d[1], d[0], s[0]))
        elif w in ('shl', 'shr'):
            self.shift(w, a[0], a[1], a[2])
        elif w in ('emit', 'warn'):
            self.check()
            self.layer(self.quad(S2 if w == 'emit' else S3, S2 if w == 'emit' else S3, a[0][0], a[0][0] + a[0][1]))
        elif w == 'key':
            if a[0][1] % 8:
                raise Stop('wid')
            self.check()
            self.layer(self.quad(a[0][0], a[0][0] + a[0][1], S1, S1))
        elif w in ('add', 'sub', 'band', 'lt', 'eq'):
            self.lib(w, *a)
        elif w in ('lut', 'store'):
            t, rest = a[0], a[1:]
            args, last = rest[:-1], rest[-1]
            if any(x[1] != k for x, k in zip(args, t.ins, strict=True)) or last[1] != t.out:
                raise Stop('wid')
            self.check()
            (self.lut_ if w == 'lut' else self.store_)(t, args, last)
        elif w == 'goto':
            self.check()
            self.layer(self.GAP, '&b' + a[0])
            self.block_open = False
        elif w == 'halt':
            self.check()
            self.layer(self.GAP, '&e')
            self.block_open = False
        elif w == 'if':
            if a[0][1] != 1:
                raise Stop('wid')
            self.check()
            self.if_(a[0][0], a[1], a[2])
        elif w == 'call':
            self.check()
            self.layer(self.c(2 * A, '&r' + a[0], self.pos + 2 * JB))
            self.layer(self.GAP, '&b' + a[0])
            self.put('d 14 &b%s\nd 14 &b%s+a0\n' % (a[1], a[1]))
            self.pos += 2 * A
            self.block_open = False
        elif w == 'ret':
            self.check()
            self.layer(self.c(2 * A, self.pos + 2 * JB + RB + 2 * A, '&r' + self.word))
            self.layer(self.GAP)
            self.layer(self.GAP, '0')
            self.block_open = False

    def if_(self, c, then, other):
        j = (2 * A).bit_length()
        ra, last = self.pos + 3 * JB, self.pos + 5 * JB
        tab = self.pos + 6 * JB
        tab += -tab % (1 << (j + 1))
        self.layer(self.c(1, ra + 2 * A + j, c))
        self.layer(self.c(1, ra + 3 * A + j, c))
        self.layer(self.GAP)
        self.layer(self.c(2 * A, last + RB + 2 * A, tab))
        self.layer(self.GAP)
        self.layer(self.GAP, '0')
        self.align(j + 1)
        for b in (other, then):
            self.put('d 14 &b%s\nd 14 &b%s+a0\n' % (b, b))
            self.zrun((1 << j) - 2 * A)
        self.pos += 2 << j
        self.block_open = False

    def finish(self):
        for name in ORDER:
            if name in self.used:
                lab, ins, out, f = BUILTIN[name]
                t = Tab(ins, out, 0)
                self.align(t.j + t.K)
                self.put(':%s\n' % lab)
                for idx in range(1 << t.K):
                    args, v = [], idx
                    for k in ins:
                        args.append(v & ((1 << k) - 1))
                        v >>= k
                    stride = 1 << t.j
                    self.put('d %x %x\n' % (min(stride, 20), f(*args)))
                    self.zrun(stride - min(stride, 20))
                self.pos += 1 << (t.j + t.K)
        self.align(3)
        self.put(':e\n\0')


def prelude():
    return ('w 14\nd 14 0\nd 14 &e\nd 14 ffffb\nd 14 ffffb\nz 50\no\nz 50\nc a0 0 &bmain\nz 40\nd 1 1\n')


def lex(data):
    """The tokens of the text: (kind, value); kind is 'label' 'name' 'num' 'str' 'ref'. Raises Stop('bad') on a wrong token."""
    i, n = 0, len(data)
    while i < n:
        c = data[i]
        if c == 0:
            return
        if c in WS:
            i += 1
        elif c == ord('#'):
            while i < n and data[i] not in (10, 0):
                i += 1
        else:
            j = i
            if c == ord('"'):
                j, body = i + 1, bytearray()
                while True:
                    if j >= n or data[j] == 0:
                        raise Stop('bad')
                    x = data[j]
                    if x == ord('"'):
                        j += 1
                        break
                    if x == ord('\\'):
                        if j + 1 >= n or data[j + 1] not in ESC:
                            raise Stop('bad')
                        body.append(ESC[data[j + 1]])
                        j += 2
                    else:
                        body.append(x)
                        j += 1
                    if len(body) > MAXSTR:
                        raise Stop('bad')
                if j < n and data[j] != 0 and data[j] not in WS:
                    raise Stop('bad')
                yield ('str', bytes(body))
            else:
                while j < n and data[j] != 0 and data[j] not in WS:
                    j += 1
                yield classify(bytes(data[i:j]))
            i = j
    return


def name_ok(b):
    return 1 <= len(b) <= 14 and b[0] not in DIGITS and all(x in IDENT for x in b)


def classify(t):
    c = t[0]
    if c == ord(':'):
        if not name_ok(t[1:]):
            raise Stop('bad')
        return ('label', t[1:].decode())
    if c == ord('&'):
        rest = t[1:]
        k = rest.find(b'[')
        nm = rest if k < 0 else rest[:k]
        if not name_ok(nm):
            raise Stop('bad')
        lo = hi = None
        if k >= 0:
            if rest[-1:] != b']':
                raise Stop('bad')
            body = rest[k + 1:-1]
            parts = body.split(b':')
            if len(parts) > 2 or not all(p and all(x in DIGITS for x in p) for p in parts):
                raise Stop('bad')
            lo = int(parts[0]) & M
            hi = int(parts[1]) & M if len(parts) == 2 else lo + 1
        return ('ref', (nm.decode(), lo, hi))
    if c in DIGITS:
        if not all(x in DIGITS for x in t):
            raise Stop('bad')
        return ('num', int(t) & M)
    if name_ok(t):
        return ('name', t.decode())
    raise Stop('bad')


def encode(src):
    """The reference of the tool: (bytes, error or None). The bytes are cut at the error (after the last complete word)."""
    data = bytes(src) if isinstance(src, (bytes, bytearray)) else src.encode('latin-1')
    comp = Compiler()
    comp.put(prelude())
    err = None
    try:
        run(comp, data)
    except Stop as e:
        err = e.why
    out = ''.join(comp.out).encode('latin-1')
    return out, err


def resolve_ref(comp, tok, want_table=False):
    kind, v = tok
    if kind != 'ref':
        raise Stop('bad')
    name, lo, hi = v
    if want_table:
        if lo is not None:
            raise Stop('bad')
        if name in EXPLICIT:
            return comp.builtin(name)
        s = comp.syms.get(name)
        if s is None or s[0] != 'tab':
            raise Stop('lab')
        return s[1]
    if name == 'zero':
        addr, bits = ZERO_ADDR, 1
    else:
        s = comp.syms.get(name)
        if s is None or s[0] != 'data':
            raise Stop('lab')
        addr, bits = s[1], s[2]
    if lo is None:
        lo, hi = 0, bits
    if not 0 <= lo < hi <= bits:
        raise Stop('wid')
    return (addr + lo, hi - lo)


def run(comp, data):
    toks = lex(data)
    pending = None
    cur = None            # [word, args kinds list, args]
    for kind, v in toks:
        if cur is None:
            if kind == 'label':
                if pending is not None:
                    raise Stop('bad')
                pending = v
                continue
            if kind != 'name' or v not in CODE:
                raise Stop('bad')
            w = v
            if (w in DEFINING) != (pending is not None):
                raise Stop('bad')
            if w in ('data', 'table', 'array', 'block', 'word') and comp.block_open:
                raise Stop('blk')
            if w not in DEFINING:
                comp.need_block(w)
            if w in ('data', 'table', 'array'):
                if pending in EXPLICIT or pending == 'zero' or pending in comp.syms or len(comp.syms) >= MAXSYM:
                    raise Stop('lab')
            cur = [w, pending, [], {}]
            pending = None
            if not SHAPE[w]:
                comp.action(w, cur[1], [])
                cur = None
            continue
        w, label, args, extra = cur
        if w == 'table' and len(args) >= 2:      # the values of a table go out one by one
            if kind not in ('num', 'str') or (kind == 'str' and 8 * len(v) != args[1]):
                raise Stop('bad')
            comp.entry(extra['t'], (kind, v))
            extra['left'] -= 1
            if extra['left'] == 0:
                cur = None
            continue
        args.append(arg(comp, w, label, args, kind, v))
        if w == 'table' and len(args) == 2:
            extra['t'] = comp.table_begin(label, args[0], args[1], False)
            extra['left'] = 1 << args[0]
        elif w != 'table' and len(args) == nargs(w, args):
            comp.action(w, label, args)
            cur = None
    if cur is not None or pending is not None:
        raise Stop('bad')
    if comp.block_open:
        raise Stop('blk')
    comp.finish()


def nargs(w, args):
    if w in ('lut', 'store'):
        return 3 if not args else len(args[0].ins) + 2
    return len(SHAPE[w])


def arg(comp, w, label, args, kind, v):
    """Check and turn one argument token (the kind of it comes from the grammar of the word)."""
    if w in ('lut', 'store'):
        if not args:
            t = resolve_ref(comp, (kind, v), True)
            if w == 'store' and not t.array:
                raise Stop('bad')
            return t
        return resolve_ref(comp, (kind, v))
    shape = SHAPE[w][len(args)]
    if shape == 'V':
        if kind not in ('num', 'str'):
            raise Stop('bad')
        return (kind, v)
    if shape[0] == 'N':
        lo, hi = map(int, shape[1:].split(':'))
        if kind != 'num' or not lo <= v <= hi:
            raise Stop('bad')
        return v
    if shape == 'B':
        if kind != 'ref' or v[1] is not None:
            raise Stop('bad')
        return v[0]
    return resolve_ref(comp, (kind, v))


# --- the numbers of the tables of programs/l3c.tw (the text of the tool has them; a test compares)
KR, KB, KV, KT, KND, KNK, KNO, KNS = 1, 2, 3, 4, 5, 6, 7, 8
NRANGE = {KND: (1, 65536), KNK: (1, 10), KNO: (1, 64), KNS: (0, 64)}
KINDS = {'R': KR, 'B': KB, 'V': KV, 'T': KT, 'N1:65536': KND, 'N1:10': KNK, 'N1:64': KNO, 'N0:64': KNS}
LIB = {'add': 0, 'sub': 1, 'band': 2, 'lt': 3, 'eq': 4}
LIBP = {  # builtin, nins, step, odel, cdel, fc (first carry is a constant), c0 (1: one), the width of the result
    'add': (0, 3, 4, 0, 0, 1, 0, 0), 'sub': (1, 3, 4, 0, 0, 1, 0, 0), 'band': (2, 2, 4, 0, 0, 0, 0, 1),
    'lt': (3, 3, 1, 1, 1, 0, 0, 3), 'eq': (4, 3, 1, 0, 1, 1, 1, 2)}


def shape_kind(wd, na):
    w = WORDS[wd]
    if w == 'table':
        return (KNK, KNO)[na] if na < 2 else KV
    if w in ('lut', 'store'):
        return KT if na == 0 else KR
    sh = SHAPE[w]
    return KINDS[sh[na]] if na < len(sh) else 0


def tvals(vals, per=16):
    return '\n'.join('  ' + ' '.join(str(v) for v in vals[i:i + per]) for i in range(0, len(vals), per))


def istr(b):
    """A string of bytes as a text of language 3 (escapes for what is not a letter)."""
    return '"' + ''.join('\\0' if c == 0 else chr(c) for c in b) + '"'


def cls(c):
    v = 0
    ch = chr(c)
    if c == 0:
        v |= 1
    if ch in ' \t\r\n':
        v |= 2
    if ch == '\n':
        v |= 4
    v |= {'#': 8, '"': 16, '\\': 32, ':': 64, '&': 128, '[': 256, ']': 512}.get(ch, 0)
    if ch.isdigit() and c < 128:
        v |= 1024 | int(ch) << 12
    if c < 128 and (ch.isalnum() or ch == '_'):
        v |= 2048
    return v


def generated():
    """name -> (K, out, lines of values) for the tables of l3c.tw made by this module."""
    T = {}
    T['cls'] = (8, 16, tvals([cls(rev8(i)) for i in range(256)]))
    T['escv'] = (8, 9, tvals([(256 | rev8(ESC[rev8(i)])) if rev8(i) in ESC else 0 for i in range(256)]))
    kws = ['"' + '\\0' * (5 - len(w)) + w + '"' for w in WORDS] + ['"\\0\\0\\0\\0\\0"'] * (32 - len(WORDS))
    T['kw'] = (5, 40, '\n'.join('  ' + ' '.join(kws[i:i + 4]) for i in range(0, 32, 4)))
    T['shape'] = (8, 4, tvals([shape_kind(i >> 3, i & 7) if i >> 3 < len(WORDS) else 0 for i in range(256)], 8))
    T['wcl'] = (5, 4, tvals([(1 if w == 'table' else 0) | (2 if w in ('lut', 'store') else 0) | (4 if w == 'data' else 0)
                             | (8 if w == 'array' else 0) for w in WORDS + [''] * 9]))
    T['defn'] = (5, 1, tvals([int(w in DEFINING) for w in WORDS + [''] * 9]))
    T['isdecl'] = (5, 1, tvals([int(w in ('data', 'table', 'array')) for w in WORDS + [''] * 9]))
    T['ar0'] = (5, 1, tvals([int(w != '' and not SHAPE[w]) for w in WORDS + [''] * 9]))
    T['isret'] = (5, 1, tvals([int(w == 'ret') for w in WORDS + [''] * 9]))
    T['lp'] = (5, 16, tvals([(lambda p: p[0] | p[1] << 3 | p[2] << 5 | p[3] << 8 | p[4] << 9 | p[5] << 10 | p[6] << 11 | p[7] << 12)(
        LIBP[w]) if w in LIBP else 0 for w in WORDS + [''] * 9]))
    T['mm'] = (2, 20, tvals([(2 * n + 1) * JB for n in range(4)]))
    T['fa'] = (1, 20, tvals([2 * A, 0]))
    T['fb'] = (1, 20, tvals([3 * A, A]))
    T['p2e'] = (5, 20, tvals([1 << e if e < 20 else 0 for e in range(32)]))
    T['mask'] = (5, 20, tvals([(1 << e) - 1 if e < 20 else 0 for e in range(32)]))
    T['jt'] = (7, 3, tvals([min(i.bit_length(), 7) for i in range(128)]))
    T['strd'] = (3, 8, tvals([1 << j for j in range(8)]))
    T['m20'] = (3, 5, tvals([min(1 << j, 20) for j in range(8)]))
    T['nlo'] = (4, 20, tvals([NRANGE[k][0] if k in NRANGE else 0 for k in range(16)]))
    T['nhi'] = (4, 20, tvals([NRANGE[k][1] if k in NRANGE else 0 for k in range(16)]))
    T['inc8'] = (8, 8, tvals([(i + 1) & 255 for i in range(256)]))
    names = list(EXPLICIT) + ['zero']
    T['bn'] = (2, 32, '\n'.join('  ' + istr(n.encode()) for n in names))
    idx = [list(BUILTIN).index(n) for n in EXPLICIT]
    T['bk'] = (2, 3, tvals([4] * 3 + [1]))
    T['ba'] = (2, 8, tvals(idx + [ZERO_ADDR]))
    allin = [(BUILTIN[n][1], BUILTIN[n][2]) for n in BUILTIN]
    T['bi'] = (3, 19, tvals([sum(k << (4 * i) for i, k in enumerate(a)) | o << 12 for a, o in allin] + [0, 0]))
    T['bfk'] = (3, 5, tvals([sum(i[0]) for i in [(BUILTIN[n][1],) for n in BUILTIN]] + [0, 0]))
    T['bfe'] = (3, 5, tvals([sum(BUILTIN[n][1]) + BUILTIN[n][2].bit_length() for n in BUILTIN] + [0, 0]))
    T['bfw'] = (3, 5, tvals([min(1 << BUILTIN[n][2].bit_length(), 20) for n in BUILTIN] + [0, 0]))
    T['bfc'] = (3, 8, tvals([rev8(ord(BUILTIN[n][0][1])) for n in BUILTIN] + [0, 0]))
    return T


def tables_text():
    return '\n'.join(':%s table %d %d\n%s' % (n, K, w, v) for n, (K, w, v) in generated().items()) + '\n'



def hoist(src):
    """Host helper for the tests (not part of the tool): the text of text.py with its data, tables and arrays moved out of the blocks
    (to the top, in their order) and 0x numbers written in decimal. The words of the declarations are one line each, or the lines
    of a table up to the next label or word."""
    import re
    src = re.sub(r'\b0[xX]([0-9a-fA-F]+)\b', lambda m: str(int(m.group(1), 16)), src)
    decl, rest, lines, i = [], [], src.split('\n'), 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r':\w+\s+(data|table|array)\b', ln):
            decl.append(ln)
            i += 1
            while i < len(lines) and not re.match(r'\s*(:|#|[a-z!@]+\s)', lines[i]) and lines[i].strip() and not re.match(
                    r'\s*(ret|halt)\s*$', lines[i]):
                decl.append(lines[i])
                i += 1
            continue
        rest.append(ln)
        i += 1
    return '\n'.join(decl + rest)


def main():
    out, err = encode(sys.stdin.buffer.read())
    sys.stdout.buffer.write(out)
    if err:
        sys.stderr.write(MESSAGES[err])
        sys.exit(1)


def language1(src):
    """The text of language 1 (without the zero byte) which the chain l3c -> l2l gives for a text of language 3: (bytes, error or None)."""
    import l2ltext
    l2, err = encode(src)
    if err:
        return b'', err
    l1, err = l2ltext.encode(l2, twice=True)
    return l1[:-1], err


def tool_image():
    """The image of programs/l3c.tw by the Python compiler of the chain (serial layout, A = 20, P = 3; part 3 builds it by the chain)."""
    import l3
    import text
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'programs', 'l3c.tw'), encoding='utf-8') as h:
        parsed = text.parse(h.read())
    assert not parsed.errors, parsed.errors
    st = l3.compile_program(parsed.build, hi=22, serial=True).stats
    assert (st['A'], st['P']) == (20, 3), st
    return st['image']


if __name__ == '__main__':
    if sys.argv[1:2] == ['-t']:
        sys.stdout.buffer.write(tool_image())
    elif sys.argv[1:2] == ['-e']:
        main()
    elif sys.argv[1:2] == ['-l']:
        l1, e = language1(sys.stdin.buffer.read())
        sys.stdout.buffer.write(l1)
        if e:
            sys.stderr.write(MESSAGES.get(e, 'l2l: ' + e) + '\n')
            sys.exit(1)
    else:
        sys.stderr.write('\n'.join(__doc__.splitlines()[-2:]) + '\n')
        sys.exit(2)
