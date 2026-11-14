"""The text of language 3 for the compiler of language 3 (host, Python, temporary): what the chain tool `programs/l3c.tw` reads, and the
Python reference of it (23.9, part 2). The tool is the compiler of language 3 as a program of the chain: stdin is a text of language 3
and a zero byte, stdout is a text of language 2 with labels (what `programs/l2l.tw` reads: `l2l` takes the text twice, and the output of
the tool ends with a zero byte, so `cat out out` is `text 0 text 0`) and a zero byte. So the chain of the build is
    text of language 3 -> l3c -> text of language 2 with labels -> l2l -> text of language 1 -> seed -> the image
The layout is SERIAL: every row of the text is a layer of its own (two slots: the row and the jump to the next layer), nothing is
packed. A is fixed, 20 (the numbers of language 2 are 20 bits), P is 2 (`common.run(image, 20, 2)`).
PACK MODE (23.10, the planner as an improvement of the economical language): the text begins with the word `pack` (alone, first). Then the
processor has three slots (P = 3: the boot layer and the first layer of a block have three, the data begin 80 bits later, `zero` and `one`
are at 240 and 304), the pairs of references to a block end in +f0 (the width of a first layer), before every pad of an alignment there is the
line `# a <k> <pad>` (hex), and data, tables and arrays must stand before the first block (else `bad block`). The output is the same serial layout
for the pass over it, `pack_pass` below (the tool programs/l3p.tw does the same on the chain: l3c -> l3p -> l2l -> seed); without the pass it
is not a program (its first layer has two slots).

The subset of the text of language 3 (text.py reads more; what is left out is told below). Words, separated by blanks and line breaks
(`#` starts a comment to the end of the line):
  :name data n v          n bits (1..65536), v a number (decimal, taken modulo 2^20) or a string "..." of at most 32 bytes
  :name table K w v...    2^K values (K 1..10, w 1..64 bits), numbers or strings of w/8 bytes
  :name array K w         a table which is written (all zeros)
  copy d s   (an address of a channel, a decimal number S .. 2^A - 1, has no width: the other side gives it)   shl x r k   shr x r k   (k 0..64)   emit s   warn s   key d
  lut &T args.. out    store &T args.. src       T is a table, an array, or add4 sub4 hex4 (made at the end of the image)
  add sub band lt eq x y r                        the library over the tables above (the widths as in lib.py)
  :name block   :name word   goto b   if c b1 b2   call w b   ret   halt         (the entry block is `main`)
A part of space is `&name`, `&name[k]`, `&name[lo:hi]` (a data defined before). Names are 1..14 bytes of A-Z a-z 0-9 _ (not a digit first);
the names of blocks and words must be a-z 0-9 _ (the tool l2l takes them as labels `b<name>`, `r<name>`), `zero` is a part of space of
1 bit which is 0. Data, tables and arrays are declared outside a block; a word or a block begins after the end of the block before.
Left out (text.py has them): stack push pop rec, dec<n>, 0x numbers, 'c' characters, \\x escapes, the
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
     python3 tower/l3ctext.py -x < prog.tw4 > prog.tw     (the reference of the pass l4c.tw: the copies with the address of the host of language 4)
     python3 tower/l3ctext.py -p < prog.l2z > prog.l2p    (the reference of the planner l3p.tw, 23.10: the pass over the output of pack mode)
     python3 tower/l3ctext.py -t > l3c.img                (the image of the tool: A = 20, P = 3, run it with `emulator -s 1048570 -p 3`)
     python3 tower/l3ctext.py -l < prog.tw > prog.l1      (the text of language 1 of a program: l3c, then l2l; for l3c.tw it is programs/l3c.l1; -l -4: the pass l4c first)"""
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
PMESSAGES = {'bad': 'l3p: bad text\n', 'big': 'l3p: too big\n'}
MAXSYM = 1020                          # the symbols of a user (with add4, sub4, hex4, zero they fill the 1024 places)
MAXSTR = 32
ZERO_ADDR, ONE_ADDR, START = JB, JB + 64, JB + 65
SYSC = (1 << A) - 6                   # the channel SYS (language 4)
PACK_P = 3                            # slots of the processor of a packed program (pack mode)
HEAD = PACK_P * RB                    # the width of a block's first layer, and of the layer the processor takes at a jump
PZERO, PONE, PSTART = HEAD, HEAD + 64, HEAD + 65
WS = b' \t\r\n'
IDENT = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_')
DIGITS = frozenset(b'0123456789')
ESC = {ord('n'): 10, ord('t'): 9, ord('r'): 13, ord('0'): 0, ord('\\'): 92, ord('"'): 34}

# the words: kinds of the arguments (R a part of space, N a number lo..hi, V a value, B a block &name, T a table)
WORDS = ['data', 'table', 'array', 'copy', 'shl', 'shr', 'lut', 'store', 'block', 'word', 'goto', 'if', 'call', 'ret', 'halt',
         'emit', 'warn', 'key', 'add', 'sub', 'band', 'lt', 'eq', 'pack']
CODE = {w: i for i, w in enumerate(WORDS)}
DEFINING = ('data', 'table', 'array', 'block', 'word')
SHAPE = {'data': ('N1:65536', 'V'), 'table': ('N1:10', 'N1:64'), 'array': ('N1:10', 'N1:64'), 'copy': ('R', 'R'),
         'shl': ('R', 'R', 'N0:64'), 'shr': ('R', 'R', 'N0:64'), 'block': (), 'word': (), 'goto': ('B',), 'if': ('R', 'B', 'B'),
         'call': ('B', 'B'), 'ret': (), 'halt': (), 'emit': ('R',), 'warn': ('R',), 'key': ('R',)}
for _w in ('add', 'sub', 'band', 'lt', 'eq'):
    SHAPE[_w] = ('R', 'R', 'R')
SHAPE['pack'] = ()
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
    def __init__(self, pack=False):
        self.out = []
        self.pack = pack                      # pack mode: the processor has PACK_P slots, the output is for the pass `pack_pass` (23.10)
        self.zero, self.one, self.pos = (PZERO, PONE, PSTART) if pack else (ZERO_ADDR, ONE_ADDR, START)
        self.plus = '+f0\n' if pack else '+a0\n'      # the second half of a pair of references to a layer: the width of the first layer
        self.coded = False                    # a block was begun (in pack mode data, tables and arrays come before the first block)
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
        if self.pack:
            self.put('# a %x %x\n' % (bits, pad))          # the pass recounts the pad when the layers before it get shorter
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
            self.lut_(t, [sx(0), sy(0), (self.zero, 1)], sr(0, 5))
            for i in range(1, k):
                self.lut_(t, [sx(i), sy(i), sr(4 * i, 1)], sr(4 * i, 5))
        elif op == 'lt':
            for i in range(k):
                self.lut_(t, [sx(i), sy(i), sr(i, 1)], sr(i + 1, 1))
        else:
            self.lut_(t, [sx(0), sy(0), (self.one, 1)], sr(0, 1))
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
                self.layer(self.c(k, r[0], self.zero))
        else:
            if k < n:
                self.layer(self.c(n - k, r[0], x[0] + k))
            if k:
                self.layer(self.c(k, r[0] + n - k, self.zero))

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
            self.block_open = self.coded = True
        elif w == 'word':
            self.check()
            self.put(':r%s\nz 28\n' % label)
            self.pos += 40
            self.put(':b%s\n' % label)
            self.word, self.block_open, self.coded = label, True, True
        elif w == 'copy':
            d, s = a
            if d[1] != s[1]:
                # an address of a channel (a number, 0 bits) has the width of the other side: the row of emit (the destination) or key (the source)
                if d[1] == 0:
                    row = self.quad(d[0], d[0], s[0], s[0] + s[1])
                elif s[1] == 0:
                    row = self.quad(d[0], d[0] + d[1], s[0], s[0])
                else:
                    raise Stop('wid')
                self.check()
                self.layer(row)
            else:
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
            self.put('d 14 &b%s\nd 14 &b%s%s' % (a[1], a[1], self.plus))
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
            self.put('d 14 &b%s\nd 14 &b%s%s' % (b, b, self.plus))
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


def prelude(pack=False):
    if pack:      # the boot layer and the first layer have PACK_P slots; the jump to main takes a whole first layer
        return 'w 14\nd 14 0\nd 14 &e\nd 14 ffffb\nd 14 ffffb\nz 50\nz 50\no\nz 50\nc f0 0 &bmain\nz 50\nz 40\nd 1 1\n'
    return 'w 14\nd 14 0\nd 14 &e\nd 14 ffffb\nd 14 ffffb\nz 50\no\nz 50\nc a0 0 &bmain\nz 40\nd 1 1\n'


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


def iter_tokens(data):
    """The first token of a text (or nothing when the text begins with a wrong token)."""
    try:
        yield from lex(data)
    except Stop:
        return


def is_pack(src):
    """Does the text begin with the word `pack` (the pack mode: the output is for the pass of the planner)?"""
    data = bytes(src) if isinstance(src, (bytes, bytearray)) else src.encode('latin-1')
    return next(iter_tokens(data), None) == ('name', 'pack')


def encode(src):
    """The reference of the tool: (bytes, error or None). The bytes are cut at the error (after the last complete word)."""
    data = bytes(src) if isinstance(src, (bytes, bytearray)) else src.encode('latin-1')
    pack = is_pack(data)
    comp = Compiler(pack)
    comp.put(prelude(pack))
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
        addr, bits = comp.zero, 1
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
    first = True
    for kind, v in toks:
        if first and (kind, v) == ('name', 'pack'):      # the word of the pack mode (the prelude was written for it), only first
            first = False
            continue
        first = False
        if cur is None:
            if kind == 'label':
                if pending is not None:
                    raise Stop('bad')
                pending = v
                continue
            if kind != 'name' or v not in CODE or v == 'pack':
                raise Stop('bad')
            w = v
            if (w in DEFINING) != (pending is not None):
                raise Stop('bad')
            if w in ('data', 'table', 'array', 'block', 'word') and comp.block_open:
                raise Stop('blk')
            if w in ('data', 'table', 'array') and comp.pack and comp.coded:
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
    if w == 'copy' and kind == 'num':          # the address of a channel, S .. 2^A - 1: it has no width (the other side gives it)
        if v < SYSC:
            raise Stop('bad')
        return (v, 0)
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
    return '"' + ''.join('\\0' if c == 0 else '\\n' if c == 10 else chr(c) for c in b) + '"'


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
                             | (8 if w == 'array' else 0) for w in WORDS + [''] * (32 - len(WORDS))]))
    T['defn'] = (5, 1, tvals([int(w in DEFINING) for w in WORDS + [''] * (32 - len(WORDS))]))
    T['isdecl'] = (5, 1, tvals([int(w in ('data', 'table', 'array')) for w in WORDS + [''] * (32 - len(WORDS))]))
    T['ar0'] = (5, 1, tvals([int(w != '' and not SHAPE[w]) for w in WORDS + [''] * (32 - len(WORDS))]))
    T['isret'] = (5, 1, tvals([int(w == 'ret') for w in WORDS + [''] * (32 - len(WORDS))]))
    T['isp'] = (5, 1, tvals([int(w == 'pack') for w in WORDS + [''] * (32 - len(WORDS))]))
    T['lp'] = (5, 16, tvals([(lambda p: p[0] | p[1] << 3 | p[2] << 5 | p[3] << 8 | p[4] << 9 | p[5] << 10 | p[6] << 11 | p[7] << 12)(
        LIBP[w]) if w in LIBP else 0 for w in WORDS + [''] * (32 - len(WORDS))]))
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


def p_generated():
    """name -> (K, out, lines of values) for the tables of programs/l3p.tw made by this module (the pass of 23.10)."""
    T = {}
    T['cls'] = (8, 4, tvals([(1 if c == 0 else 0) | (2 if c == 32 else 0) | (4 if c == 10 else 0) | (8 if c == 38 else 0) for c in map(rev8, range(256))]))
    T['hexv'] = (8, 5, tvals([(int(chr(c), 16) | 16) if chr(c) in '0123456789abcdef' else 0 for c in map(rev8, range(256))]))
    T['fcl'] = (8, 3, tvals([{0: 7, ord(':'): 1, ord('#'): 2, ord('o'): 3, ord('c'): 4, ord('z'): 5, ord('d'): 6}.get(c, 0) for c in map(rev8, range(256))]))
    T['tbase'] = (8, 20, tvals([TBASE + 0x1000 * TNUM[chr(c)] if chr(c) in TNUM else 0 for c in map(rev8, range(256))]))
    T['mu'] = (2, 20, tvals([80 * i for i in range(4)]))
    T['mask'] = (5, 20, tvals([(1 << e) - 1 if e < 20 else 0 for e in range(32)]))
    T['p2e'] = (5, 20, tvals([1 << e if e < 20 else 0 for e in range(32)]))
    T['inc8'] = (8, 8, tvals([(i + 1) & 255 for i in range(256)]))
    return T


def cc(c):
    """The class of a byte for programs/l4c.tw: bits 0 zero byte, 1 blank, 2 #, 3 ", 4 \\, 5 line break, 6 letter digit or _, 7 digit."""
    v = int(c == 0) | int(c in WS) << 1 | int(c == 35) << 2 | int(c == 34) << 3 | int(c == 92) << 4 | int(c == 10) << 5
    v |= int(c in IDENT) << 6 | int(c in DIGITS) << 7
    return v


def x_generated():
    """name -> (K, out, lines of values) for the tables of programs/l4c.tw made by this module (the pass of language 4)."""
    T = {}
    T['cc'] = (8, 8, tvals([cc(c) for c in map(rev8, range(256))]))
    T['hexv'] = (8, 5, tvals([(int(chr(c), 16) | 16) if chr(c) in '0123456789abcdefABCDEF' else 0 for c in map(rev8, range(256))]))
    # the text of a nibble source `&l4n1[4:8]`, a byte at an index k + 16 v (v: the nibble, k: the place in the text), 0 after its end
    T['nsrc'] = (8, 8, '\n'.join('  ' + ' '.join(istr(bytes([_nib(v)[k].encode()[0]])) if k < len(_nib(v)) else '0' for k in range(16)) for v in range(16)))
    T['tlok'] = (7, 1, tvals([int(i < MAXTOK) for i in range(128)]))
    return T


def x_tables_text():
    return '\n'.join(':%s table %d %d\n%s' % (n, K, w, v) for n, (K, w, v) in x_generated().items()) + '\n'


def p_tables_text():
    return '\n'.join(':%s table %d %d\n%s' % (n, K, w, v) for n, (K, w, v) in p_generated().items()) + '\n'


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


def main(planner=False):
    if planner:
        out, err = pack_pass(sys.stdin.buffer.read())
    else:
        out, err = encode(sys.stdin.buffer.read())
    sys.stdout.buffer.write(out)
    if err:
        sys.stderr.write((PMESSAGES if planner else MESSAGES)[err])
        sys.exit(1)


# --- the pass of 23.10: the planner (the serial layers of a block packed into fewer layers)
# The text of language 2 of pack mode (`pack` is its first word) is serial: a layer is a row and a jump of 160 bits, the data and the
# tables stand before the first block, the processor has PACK_P = 3 slots. The pass (the tool programs/l3p.tw does the same on the
# chain) takes each block, the layers from its label to the jump which leaves it (a label, or the patched 0), forgets the empty rows
# (the waits of lut, if, ret) and lays the rows out again into layers of at most PACK_P - 1 rows. It is the list scheduler of l3.py
# with direct = False: the rows in the text order, every row into the first layer, from the earliest the rows before it allow, where
# there is room and no bits are touched twice in the layer (source with source too). After a row which touches the same bits (it
# writes what this reads or writes, or reads what this writes) it goes 1 layer later; after a row which writes into its text, or into
# the text of the jump of the last layer, 2 layers later (the jump takes the whole next layer one tick before it runs). Only the
# last WINDOW rows before it are looked at; farther back it goes 2 layers after them all. A copy that writes into the text of the block is a
# patch: the bits it patches in the sl (dl) field of a row tell the span 2^E of the table the row reads (writes). A reference to a
# table of the library (&t.) is a span at a place of its own above the memory; a reference to the link of a word (&r...) touches
# nothing else. key writes from its destination to the channel. The first layer of a block and the layer a jump takes have PACK_P
# slots (the jump copies PACK_P * RB bits); a layer in the middle has as many slots as it needs, not fewer than the layer before it.
# The data and the tables stay where they are; what follows the last jump of a block (the table of `if`, the pair of `call`) moves
# with the block's end, and the pad of an alignment (`# a<k> <pad>`) is counted anew; the markers go.
S1, S2, S3 = (1 << A) - 5, (1 << A) - 4, (1 << A) - 3
TBASE = 0xfa000                          # the place of the table of the library 'ta ts tn tl te th' (a, s, n, l, e, h): +0x1000 * its number
TNUM = {'a': 0, 's': 1, 'n': 2, 'l': 3, 'e': 4, 'h': 5}
WINDOW = 8
CHEND = (1 << A) - 1                     # every access to a channel writes [S, S+5): two of them touch the same bits and keep the order of the text (the rows of
                                         # different channels are not ordered by data; S+5 is the end of the space and is not a number of A bits: no word uses S+4, S+5)
STATS = {}                               # (rows, layers, bits) of the blocks of the last pass, laid out serially and packed


def _field(t):
    """A field of a row: (label text or None, number); a reference to a table of the library is a number of its place above the memory."""
    if t[0] != '&':
        return (None, int(t, 16), 0)
    if t[1] == 't' and len(t) >= 3:           # &ta, and &ta+30 of the nibbles of the long copy: the whole table is one place
        return (t, TBASE + 0x1000 * TNUM[t[2]], 1)
    return (t, 0, 2)


def _fmt(f, v):
    return '%x' % v if f[0] is None else f[0]


def _size(line):
    """Bits of a line of the text (after `o`)."""
    w = line.split()
    if not w or line[0] in ':#':
        return 0
    if w[0] == 'c':
        return 80
    if w[0] in ('d', 'z'):
        return int(w[1], 16)
    return 0


def _get(lines, j):
    """lines[j] as the tool reads a line: at most 63 characters and 4 tokens (else bad)."""
    ln = lines[j]
    if len(ln) > 63 or len(ln.split()) > 4:
        raise Stop('bad')
    return ln


def _marker(ln):
    """(k, pad) if the line is a marker `# a <k> <pad>`; None if it is another comment; bad if it is a marker without its numbers."""
    tk = ln.split()
    if ln[:1] != '#' or len(tk) < 2 or tk[1] != 'a' or len(tk[0]) != 1:
        return None
    if len(tk) != 4:
        raise Stop('bad')
    return int(tk[2], 16), int(tk[3], 16)


def _ov(a, b):
    return a[0] < b[1] and b[0] < a[1]


def _z(n):
    out = []
    while n >= 255:
        out.append('z ff')
        n -= 255
    if n:
        out.append('z %x' % n)
    return out


class _Op:
    pass


def _plan(ops, jump):
    """The layer of every op and the number of layers. Every op has r, w (the intervals read and written), own (the interval of its row's text)."""
    at, pm, lay, need = [], [], [], 1
    for i, o in enumerate(ops):
        lb = pm[i - WINDOW - 1] + 2 if i > WINDOW else 0
        for j in range(max(0, i - WINDOW), i):
            p = ops[j]
            if _ov(p.w, o.own):
                lb = max(lb, at[j] + 2)
            if _ov(p.w, o.r) or _ov(p.r, o.w) or _ov(p.w, o.w):
                lb = max(lb, at[j] + 1)
        L = lb
        while True:
            while L >= len(lay):
                lay.append([])
            if len(lay[L]) < PACK_P - 1 and not any(
                    _ov(o.r, ops[k].r) or _ov(o.r, ops[k].w) or _ov(o.w, ops[k].r) or _ov(o.w, ops[k].w) for k in lay[L]):
                break
            L += 1
        lay[L].append(i)
        at.append(L)
        pm.append(max(pm[-1], L) if pm else L)
        if _ov(o.w, jump):
            need = max(need, L + 3)
    n = max(len(lay), need)
    return lay + [[] for _ in range(n - len(lay))]


def _block(lines, i, po, pn):
    """The block that begins at lines[i] (':b...'): (its lines packed, the index of the line after its last jump, po, pn after it)."""
    bs = po
    j, units = i + 1, []

    def line(j, first, ntok=0):
        """lines[j] if it is a line (not the zero byte or the end of a line cut) of the class `first` with at least ntok tokens."""
        if j >= len(lines) - 1 or not lines[j] or lines[j][0] not in first or len(lines[j].split()) < ntok:
            raise Stop('bad')
        return _get(lines, j)

    while True:                                          # the layers: a row and a jump
        ln = line(j, 'zcd')
        if ln[0] == 'd':
            row = [line(j + k, 'd', 3) for k in range(4)]
            if any(r.split()[1] != '14' for r in row):
                raise Stop('bad')
            j += 4
        else:
            if ln[0] == 'z' and int(line(j, 'z', 2).split()[1], 16) != 0x50:
                raise Stop('bad')
            row = [line(j, 'c', 4) if ln[0] == 'c' else ln]
            j += 1
        tgt = line(j, 'c', 4).split()[3]
        j += 1
        units.append((row, tgt))
        if tgt == '0' or tgt[0] == '&':
            break
        if len(units) == 254:
            raise Stop('big')
    if j >= len(lines):
        raise Stop('bad')
    if j == len(lines) - 1 and lines[j] != '':
        raise Stop('bad')
    _get(lines, j)
    be = bs + 160 * len(units)
    jump = (be - 80, be)
    ops, uop = [], {}
    for k, (row, _) in enumerate(units):
        if row == ['z 50']:
            continue
        o = _Op()
        o.row, o.own = row, (bs + 160 * k, bs + 160 * k + 80)
        if row[0].startswith('d 14'):
            o.q = [int(x.split()[2], 16) for x in row]
        else:
            t = row[0].split()
            o.q, o.n, o.d, o.s = None, int(t[1], 16), _field(t[2]), _field(t[3])
        uop[k] = len(ops)
        ops.append(o)
    es, ed = [0] * len(ops), [0] * len(ops)              # the spans of the tables: the bits patched into sl (dl) of a row
    for o in ops:
        o.patch = o.q is None and o.d[2] == 0 and bs <= o.d[1] < be
        if o.patch and o.d[1] < be - 80:
            t, off = divmod(o.d[1] - bs, 160)
            if t not in uop:
                raise Stop('bad')                         # a patch into an empty row
            x = uop[t]
            if 40 <= off < 60:
                es[x] = max(es[x], off - 40 + o.n)
            elif off < 20:
                ed[x] = max(ed[x], off + o.n)
    for x, o in enumerate(ops):
        if o.q is None and o.s[2] == 0 and bs <= o.s[1] < be:
            raise Stop('bad')                                 # a row does not read the text of its block
        if o.q is not None:
            if o.q[2] in (S1, SYSC):                      # key, the read of the answer of SYS: the channel is read, from the destination to the channels written
                o.r, o.w = (o.q[2], o.q[2] + 1), (o.q[0], CHEND)
            else:                                         # emit, warn, the request of SYS: the channels are written
                o.r, o.w = (o.q[2], o.q[3]), (SYSC, CHEND)
        else:
            o.r = (o.s[1], o.s[1] + ((1 << es[x]) if es[x] else o.n)) if o.s[2] != 2 else (0, 0)
            o.w = (o.d[1], o.d[1] + ((1 << ed[x]) if ed[x] else o.n)) if o.d[2] != 2 else (0, 0)
    lay = _plan(ops, jump)
    n = len(lay)
    w = [len(l) + 1 for l in lay]
    u = [PACK_P] + [max(w[k], w[k - 1]) for k in range(1, n)]
    for key, (r, l, b) in (('serial', (len(ops) + len(units), len(units), 160 * len(units))), ('packed', (len(ops) + n, n, 80 * sum(u)))):
        STATS[key] = tuple(x + y for x, y in zip(STATS.get(key, (0, 0, 0)), (r, l, b), strict=True))
    start = [pn]
    for k in range(n):
        start.append(start[-1] + u[k] * 80)
    where = {}
    for k, l in enumerate(lay):
        for sl, x in enumerate(l):
            where[x] = start[k] + sl * 80
    be_new = start[n]
    old_pad = new_pad = 0                                 # a pad that follows the block at once: the table of `if`
    try:
        mk = _marker(lines[j])                           # (a marker that is wrong is found when the line is read again)
    except Stop:
        mk = None
    if mk:
        old_pad = mk[1]
        new_pad = -be_new % (1 << mk[0])
    shift = (be_new + new_pad) - (be + old_pad)

    def addr(f, v):
        if f[0] is not None:
            return v
        if bs <= v < be:
            t, off = divmod(v - bs, 160)
            if off < 80:
                if t not in uop:
                    raise Stop('bad')
                return where[uop[t]] + off
            return start[n - 1] + (len(lay[n - 1])) * 80 + off - 80
        return v + shift if be <= v < TBASE else v

    out = [lines[i]]
    for k in range(n):
        for x in lay[k]:
            o = ops[x]
            out.extend(o.row if o.q is not None else ['c %x %s %s' % (o.n, _fmt(o.d, addr(o.d, o.d[1])), _fmt(o.s, addr(o.s, o.s[1])))])
        out.append('c %x 0 %x' % (u[k + 1] * 80, start[k + 1]) if k < n - 1 else 'c %x 0 %s' % (HEAD, units[-1][1]))
        out.extend(['z 50'] * (u[k] - w[k]))
    return out, j, be, be_new


def pack_pass(data):
    """The pass over the text of language 2 of pack mode (see above); data ends with a zero byte, and so does the result."""
    STATS.clear()
    text = data.decode('latin-1')
    assert text.endswith('\0')
    lines = text[:-1].split('\n')                        # the last piece is empty (the zero byte comes at the start of a line) or a line cut
    out, i, po, pn = [], 0, 0, 0
    try:
        while i < len(lines) - 1:
            ln = _get(lines, i)
            if ln.startswith(':b'):
                out.append(ln)
                ls, i, po, pn = _block(lines, i, po, pn)
                out.extend(ls[1:])
            elif _marker(ln):
                k, pad = _marker(ln)
                i += 1
                left = pad
                while left:
                    if i >= len(lines) - 1 or not lines[i].startswith('z ') or len(_get(lines, i).split()) < 2:
                        raise Stop('bad')
                    left -= int(lines[i].split()[1], 16)
                    i += 1
                if left < 0:
                    raise Stop('bad')
                npad = -pn % (1 << k)
                out.extend(_z(npad))
                po += pad
                pn += npad
            else:
                if ln == 'o':
                    po = pn = 0
                else:
                    po += _size(ln)
                    pn += _size(ln)
                out.append(ln)
                i += 1
        if lines[-1] != '':
            raise Stop('bad')
    except Stop as e:
        return ''.join(x + '\n' for x in out).encode('latin-1'), e.why
    return ('\n'.join(out) + '\n\0').encode('latin-1'), None


# --- the compiler of language 4 (the pass over a text of language 3; the tool programs/l4c.tw does the same on the chain: l4c -> l3c -> [l3p] ->
# l2l -> seed). Language 4 is language 3 in which `copy` may have the address of the host, a number of the form 0x1..., 33 hex digits: 2^128 plus the
# position pos = area * 2^96 + bit (the area in the top 32 bits, 0 the clock, 1.. the files `-r`; the 128 bits of the request SYS LONG of the emulator).
# The pass gives the text as it is, and makes of `copy &x 0x...` (get: the host is the source) and `copy 0x... &x` (put) the words of language 3
# and of the copy with the address of a channel (1048570, S: the channel SYS): the buffer of the request is the data l4q (the prelude of the pass, put after
# the word `pack` if it stands first), the record op:8 chan:20 flags:16 arg:32 off:128 (bits 0, 8, 28, 44, 76; 204 in all) and the data after it is made of
# copies: the header is zeroed (from l4z), the nonzero nibbles of op (6), flags (1: get), arg (n, the width of &x) and pos are copied from the constants l4n0..l4n3
# (five nibbles each, the nibble v is the bits 4(v % 5) .. +4 of l4n<v / 5>), the data are copied after the record; the row to SYS is `copy 1048570 &l4q[0:204+n]`
# (put) or `copy 1048570 &l4q[0:204]`, the read of the answer `copy &l4q[204:204+max(n,117)] 1048570` (117 = 97 + A: a whole record of the answer, the contract of the
# emulator) and the copy of n bits into &x (get). The width n is that of `&x[lo:hi]` (hi - lo), `&x[k]` (1) or of `&x` whole (the data declared before: the pass
# remembers the widths of `:name data n ...`); a copy which has no host address, or has two, or a width that is not known or not 1..NBUF, goes out unchanged (l3c reports it).
# Not a word, not an address: the rest goes through as it is (tokens as l3c reads them: blanks, `#` comments, strings "..." with escapes); but the blanks
# between `copy` and its operands are not put out (the copy goes out as `copy a b` or as the words of language 3, the blank after the second operand follows it).
# The address of a channel in `copy` may be written from the end of the space: `+k` (k 0..5) is S + k, the number 104857k of l3c, so that the text does not depend on A
# (the channels are the codes at the end of the space: +1 stdin, +2 stdout, +3 stderr, +0 SYS); `copy +2 &x` is `emit &x`, `copy &x +1` is `key &x`. Not a word: a form of the address.
# The far copy (26.4, 25.8): an address 0x2 and 32 hex digits (far_copy below) is translated by its link: 0 the requests of the neighbour, 1 the same with the check and the repeat
# (the word l4ask), 2 the common file of the host (the words l4flag, l4fget); the forms which are not as told go out as they were.
# No errors, no report.
NBUF = 2048                           # the bits of data of a long copy (the buffer l4q has 204 + NBUF)
L4Q, L4Z = 'l4q', 'l4z'
L4N = (274960, 624485, 974010, 15)    # the nibbles 0..4, 5..9, 10..14, 15 (20 bits, a nibble in 4 bits, low first)
MAXTOK = 120                          # a longer token is cut (l3c takes none so long)
MAXNAME = 14
MAXW = 1024                           # the widths of data the pass remembers (and K, w of table and array: the value w + 128 K, kind 1 and 2; 25.4)
NOTRACK = (0, None, 0, 0)
SYSTEXT = str(SYSC)


def l4c_prelude():
    return '\n:%s data %d 0\n:%s data 204 0\n' % (L4Q, 204 + NBUF, L4Z) + ''.join(':l4n%d data 20 %d\n' % (i, v) for i, v in enumerate(L4N))


def _nib(v):
    return '&l4n%d[%d:%d]' % (v // 5, 4 * (v % 5), 4 * (v % 5) + 4)


def _name_of(tok, i):
    """The name in tok from i: (name, index after it) or None (not 1..14 bytes of A-Z a-z 0-9 _, a digit first)."""
    j = i
    while j < len(tok) and tok[j] in IDENT:
        j += 1
    name = tok[i:j]
    if not 1 <= len(name) <= MAXNAME or name[0] in DIGITS:
        return None
    return name, j


def _decimal(b):
    v = 0
    for c in b:
        v = (v * 10 + c - 48) & M
    return v


def _host_digits(tok):
    """The hex digits of an address of the host `0x...` (list of values), or None."""
    if len(tok) < 3 or tok[:2] != b'0x' or any(c not in b'0123456789abcdefABCDEF' for c in tok[2:]):
        return None
    return [int(chr(c), 16) for c in tok[2:]]


def _part(tok, syms):
    """The part of space `tok` (&name, &name[k], &name[lo:hi]) as (the end of the name in tok, lo, the width) or None."""
    if tok[:1] != b'&':
        return None
    nm = _name_of(tok, 1)
    if nm is None:
        return None
    name, j = nm
    rest = tok[j:]
    if not rest:
        e = next((e for e in syms if e[0] == name), None)
        return None if e is None or e[2] else (j, 0, e[1])
    if rest[:1] != b'[' or rest[-1:] != b']':
        return None
    parts = rest[1:-1].split(b':')
    if len(parts) > 2 or not all(p and all(c in DIGITS for c in p) for p in parts):
        return None
    if len(parts) == 1:
        return j, _decimal(parts[0]), 1
    lo, hi = _decimal(parts[0]), _decimal(parts[1])
    return (j, lo, hi - lo) if hi > lo else None


def _width(tok, syms):
    """The width of the part of space `tok` (&name, &name[k], &name[lo:hi]) or None."""
    r = _part(tok, syms)
    return None if r is None else r[2]


def _chan(tok):
    """An operand `+k` (k 0..5) is the address of a channel from the end of the space, S + k (stdin +1, stdout +2, stderr +3, SYS +0): the number of l3c; the rest as it is."""
    if len(tok) == 2 and tok[:1] == b'+' and tok[1:] in (b'0', b'1', b'2', b'3', b'4', b'5'):
        return str(SYSC + tok[1] - 48).encode()
    return tok


def _comp(tok):
    """A computed address `&t@&i` (4th form of the address of `copy`, 25.4): the table or the array `&t` and, after the sign @, the cell of the index (a part of space: &i,
    &i[k], &i[lo:hi]). Returns the place of the sign @ in tok, or None (no name of 1..14 bytes after the & and then @)."""
    if tok[:1] != b'&':
        return None
    nm = _name_of(tok, 1)
    return nm[1] if nm is not None and tok[nm[1]:nm[1] + 1] == b'@' else None


def comp_copy(a, b, syms):
    """The text of language 3 for a copy with a computed address (one operand is `&t@&i`, the other a part of space with a known width): `copy &x &t@&i` is `lut &t &i &x`
    (the read of the record by the value of the cell), `copy &t@&i &x` is `store &t &i &x` (the write; &t is an array). The widths are those of lut and store: the index is
    exactly the K bits of the table (table K w), &x is w bits. The names are those of table and array before the copy. None: the name is not a table (an array for the write),
    the widths are not those, the other operand is not a part of space with a known width (the reasons for the tool l4c: `at name`, `at width`)."""
    ja, jb = _comp(a), _comp(b)
    if ja is not None and jb is not None:
        return None
    put = ja is not None
    addr, other, j = (a, b, ja) if put else (b, a, jb)
    e = next((e for e in syms if e[0] == addr[1:j]), None)
    if e is None or not e[2] or (put and e[2] != 2):
        return None
    if _width(other, syms) != e[1] & 127 or _width(addr[j + 1:], syms) != e[1] >> 7:
        return None
    return (b'store ' if put else b'lut ') + addr[:j] + b' ' + addr[j + 1:] + b' ' + other


def host_head(put, n, digits):
    """The header of a long copy of n bits at the position of the hex `digits`: the buffer is zeroed, the nonzero nibbles of op, flags (get), n and the position are copied."""
    out = ['copy &%s[0:204] &%s[0:204]\n' % (L4Q, L4Z), 'copy &%s[0:4] %s\n' % (L4Q, _nib(6))]
    if not put:
        out.append('copy &%s[28:32] %s\n' % (L4Q, _nib(1)))
    for i in range(5):
        if n >> 4 * i & 15:
            out.append('copy &%s[%d:%d] %s\n' % (L4Q, 44 + 4 * i, 48 + 4 * i, _nib(n >> 4 * i & 15)))
    for j in range(min(len(digits), 32)):
        v = digits[len(digits) - 1 - j]
        if v:
            out.append('copy &%s[%d:%d] %s\n' % (L4Q, 76 + 4 * j, 80 + 4 * j, _nib(v)))
    return ''.join(out)


def host_copy(put, other, n, digits):
    """The text of language 3 for a long copy of n bits (the part of space `other`) to (put) or from the host, at the position of the hex `digits`."""
    out = [host_head(put, n, digits)]
    x = other.decode('latin-1')
    if put:
        out += ['copy &%s[204:%d] %s\n' % (L4Q, 204 + n, x), 'copy %s &%s[0:%d]\n' % (SYSTEXT, L4Q, 204 + n)]
    else:
        r = max(n, 117)
        out += ['copy %s &%s[0:204]\n' % (SYSTEXT, L4Q), 'copy &%s[204:%d] %s\n' % (L4Q, 204 + r, SYSTEXT), 'copy %s &%s[204:%d]\n' % (x, L4Q, 204 + n)]
    return ''.join(out)


FARMAX = 64                           # the bits of a far copy (whole bytes: 8 .. 64)
FARLAB = 2048                         # the labels l4f<c> of the far gets: past this number a far copy is not translated
FARLO = 9900                          # the position of a part &x[lo:hi] of a far copy: lo < 9900 (the numbers of the text are written by putdec, under 10000)
FARQ = 48                             # the record of a far request: op 8 bits, pos 32 bits (the number of the byte), dat 8 bits: the bits 0..48 of l4q


def _far(tok):
    """An address of the far space `0x2` and 32 hex digits (the link in the top 32 bits, the position in the low 96) or None."""
    return tok if len(tok) == 35 and tok[:3] == b'0x2' and _host_digits(tok) is not None else None


def far_pos(tok):
    """The link and the number of the byte of a far address as (the link, 8 nibbles, the low first), or None: the link (the top 8 digits) is 0 (the neighbour by stdin
    and stdout), 1 (the same, the check and the repeat) or 2 (the common file); the position is a multiple of 8 bits and under 2^32, the byte is the position / 8."""
    d = _host_digits(tok)[1:]                  # the 32 digits after the 2
    if any(d[:7]) or d[7] > 2 or any(d[8:24]) or d[31] & 7:
        return None
    bits = [(d[31 - j] >> i) & 1 for j in range(9) for i in range(4)]
    return d[7], [bits[4 * t + 3] | bits[4 * t + 4] << 1 | bits[4 * t + 5] << 2 | bits[4 * t + 6] << 3 for t in range(8)]


FARASK = (':l4ask word\ncopy &l4q[400:404] &l4z[0:4]\ngoto &l4a1\n:l4a1 block\ncopy &l4q[56:72] &l4z[0:16]\n'
          'add &l4q[0:8] &l4q[8:16] &l4q[410:419]\nadd &l4q[410:418] &l4q[16:24] &l4q[420:429]\nadd &l4q[420:428] &l4q[24:32] &l4q[430:439]\n'
          'add &l4q[430:438] &l4q[32:40] &l4q[440:449]\nadd &l4q[440:448] &l4q[40:48] &l4q[450:459]\ncopy &l4q[48:56] &l4q[450:458]\n'
          'emit &l4q[0:56]\nkey &l4q[56:72]\ngoto &l4a2\n:l4a2 block\ncopy &l4q[460:464] &l4n3[0:4]\ncopy &l4q[464:468] &l4n3[0:4]\n'
          'add &l4q[56:64] &l4q[64:72] &l4q[470:479]\neq &l4q[470:478] &l4q[460:468] &l4q[480:482]\nif &l4q[481] &l4a3 &l4a4\n:l4a3 block\nret\n'
          ':l4a4 block\nadd &l4q[400:404] &l4n0[4:8] &l4q[490:495]\ncopy &l4q[400:404] &l4q[490:494]\nlt &l4q[400:404] &l4n0[16:20] &l4q[500:502]\n'
          'if &l4q[501] &l4a1 &l4a5\n:l4a5 block\ncopy &l4q[56:60] &l4n3[0:4]\ncopy &l4q[60:64] &l4n3[0:4]\nret\n')
FARFLAG = (':l4flag word\ncopy &l4q[44:64] &l4z[0:20]\ncopy &l4q[44:48] &l4n0[16:20]\ncopy &l4q[82] &l4n0[4]\ncopy &l4q[204:208] &l4n0[4:8]\n'
           'copy 1048570 &l4q[0:208]\nret\n')
FARGET = (':l4fget word\ncopy &l4q[420:440] &l4q[44:64]\ncopy &l4q[44:64] &l4z[0:20]\ncopy &l4q[44:48] &l4n0[16:20]\ncopy &l4q[82] &l4n0[4]\n'
          'copy &l4q[400:420] &l4z[0:20]\ncopy &l4q[440:460] &l4z[0:20]\ncopy &l4q[440:444] &l4n0[4:8]\ncopy &l4q[460:480] &l4z[0:20]\n'
          'copy &l4q[476:480] &l4n0[16:20]\ngoto &l4g1\n:l4g1 block\ncopy 1048570 &l4q[0:204]\ncopy &l4q[204:321] 1048570\n'
          'if &l4q[204] &l4g2 &l4g3\n:l4g2 block\ncopy &l4q[44:64] &l4q[420:440]\ncopy &l4q[82] &l4z[0]\ncopy 1048570 &l4q[0:204]\n'
          'copy &l4q[204:321] 1048570\nret\n:l4g3 block\nadd &l4q[400:420] &l4q[440:460] &l4q[490:511]\ncopy &l4q[400:420] &l4q[490:510]\n'
          'lt &l4q[400:420] &l4q[460:480] &l4q[520:526]\nif &l4q[525] &l4g1 &l4g4\n:l4g4 block\ncopy &l4q[204:208] &l4n3[0:4]\n'
          'copy &l4q[208:212] &l4q[204:208]\ncopy &l4q[212:220] &l4q[204:212]\ncopy &l4q[220:236] &l4q[204:220]\ncopy &l4q[236:268] &l4q[204:236]\nret\n')
FARWORDS = (FARASK, FARFLAG, FARGET)         # the words of the links 1 and 2, put once at the end of the text if a far copy used them (in this order)


def far_copy(put, other, syms, tok, label):
    """The text of language 3 for a far copy (the far space is the neighbour of stdin and stdout, which answers by the protocol of far_serve.tw: the link 0; by the protocol
    of far_serve_ck.tw with the check and the repeat: the link 1; or the common file of the host: the link 2). The link 0: one request of 6 bytes
    (op 8 bits, the number of the byte 32 bits, dat 8 bits) for a byte of the part `other` (a width of 8 .. 64 bits, whole bytes). The record is the bits 0..48 of l4q.
    get: the request goes out, then (after a goto: a read must not stand before the write that it answers) the byte is read into its place in `other`, the number of
    the byte is increased (the nibbles which change are copied from the constants: the carry stops the copies) and the request of the next byte goes out;
    put: the byte is copied into dat and the request goes out, the number of the byte is increased. The labels are l4f<label>, l4f<label + 1> ...
    The link 1: the same record and the same increase, but the request goes out by the word l4ask (FARASK, at the end of the text): `call &l4ask &l4f<k>`, which sends the
    record with the sum (7 bytes), reads the answer of 2 bytes (the value and its complement), asks again up to 4 times and leaves the value in the bits 56..64 of l4q (ones if
    the tries are out); the get copies it into `other`, the put goes on.
    The link 2: the common file (the area 1 of the host). The position P (a multiple of 8 bits) names a cell of 128 bits at the bit 16 P = 128 (P / 8) of the area: the data
    (n bits, at most 64) at its start and the flag of readiness (4 bits, the value 1) at its bit 64. put: the long copy of the data to the file (host_copy), then
    `call &l4flag &l4f<label>` (the flag is a copy of its own after a tick boundary: the data are in the file before the flag is); get: the header of the long copy of the data,
    then `call &l4fget &l4f<label>` (the word polls the flag by the same request with the flag bit, up to 2^18 failed polls, then sends the request of the data; the
    answer is in l4q[204:204 + n], ones if the flag did not come), then the copy of the data into `other`. A cell is written once (the file is zero at the start).
    Returns (the text, the labels used, the number of the word used: 0 none, 1 l4ask, 2 l4flag, 3 l4fget) or None (the width is not 8 .. 64 whole bytes, the position or the link
    is not as told, lo >= FARLO, no more labels)."""
    r = _part(other, syms)
    fp = far_pos(tok)
    if r is None or fp is None or r[2] % 8 or not 8 <= r[2] <= FARMAX or r[1] >= FARLO or label >= FARLAB:
        return None
    link, pos = fp
    j, lo, n = r
    name = other[:j].decode('latin-1')
    if link == 2:
        d = _host_digits(tok)[1:]
        digits = [1, 0, 0, 0, 0, 0, 0, 0, 1] + d[9:] + [0]            # the area 1, the position 16 P
        if put:
            return host_copy(True, other, n, digits) + 'call &l4flag &l4f%d\n:l4f%d block\n' % (label, label), 1, 2
        return host_head(False, n, digits) + 'call &l4fget &l4f%d\n:l4f%d block\ncopy %s &%s[204:%d]\n' % (label, label, other.decode('latin-1'), L4Q, 204 + n), 1, 3
    out = ['copy &%s[0:204] &%s[0:204]\n' % (L4Q, L4Z), 'copy &%s[0:4] %s\n' % (L4Q, _nib(2 if put else 1))]
    for i in range(8):
        if pos[i]:
            out.append('copy &%s[%d:%d] %s\n' % (L4Q, 8 + 4 * i, 12 + 4 * i, _nib(pos[i])))
    req = 'emit &%s[0:48]\n' % L4Q
    if not put and not link:
        out.append(req)
    for k in range(n // 8):
        part = '%s[%d:%d]' % (name, lo + 8 * k, lo + 8 * k + 8)
        if put:
            out.append('copy &%s[40:48] %s\n' % (L4Q, part))
            out.append(req if not link else 'call &l4ask &l4f%d\n:l4f%d block\n' % (label + k, label + k))
        elif link:
            out.append('call &l4ask &l4f%d\n:l4f%d block\ncopy %s &%s[56:64]\n' % (label + k, label + k, part, L4Q))
        else:
            out.append('goto &l4f%d\n:l4f%d block\nkey %s\n' % (label + k, label + k, part))
        if k < n // 8 - 1:
            for i in range(8):                      # the number of the byte + 1: the nibbles up to the end of the carry
                v = pos[i] + 1
                pos[i] = v & 15
                out.append('copy &%s[%d:%d] %s\n' % (L4Q, 8 + 4 * i, 12 + 4 * i, _nib(pos[i])))
                if v < 16:
                    break
            if not put and not link:
                out.append(req)
    return ''.join(out), (0 if put and not link else n // 8), 1 if link else 0


def l4c(data):
    """The pass: data is a text of language 4 and a zero byte (a byte string); returns (the text of language 3 and a zero byte, None)."""
    out, tok, syms, prelude, first, label = [], bytearray(), [], False, True, 0
    words = [False, False, False]           # the words of the links 1 and 2 (FARWORDS) which a far copy used
    state = 'idle'                          # idle, tok, str (in a string), com
    esc = False
    copy_ops = None                         # None, or the list of the operands read after `copy` (0, 1 or 2 of them)
    track = NOTRACK                         # (0: nothing; 1: after :name; 2: a number follows, the width of data or w of table, array; 3: K follows), the name, the kind (0 data, 1 table, 2 array), K
    i = 0

    def put(s):
        out.append(s if isinstance(s, str) else s.decode('latin-1'))

    def pre():
        nonlocal prelude
        if not prelude:
            prelude = True
            put(l4c_prelude())

    def end_token(t, sep):
        nonlocal first, copy_ops, track, label
        t = bytes(t)
        if copy_ops is not None:
            copy_ops.append(t)
            track = NOTRACK
            if len(copy_ops) < 2:
                return
            a, b = copy_ops
            copy_ops = None
            ha, hb = _host_digits(a), _host_digits(b)
            if _comp(a) is not None or _comp(b) is not None:      # a computed address: lut or store, or the copy as it was
                c = comp_copy(a, b, syms)
                if c is not None:
                    put(c)
                    return
            elif (ha is None) != (hb is None):
                other, digits = (b, ha) if ha is not None else (a, hb)
                addr = a if ha is not None else b
                if _far(addr):                  # the far space: its own translation, never the host's (an address which is not as told goes out unchanged)
                    f = far_copy(ha is not None, other, syms, addr, label)
                    if f is not None:
                        put(f[0])
                        label += f[1]
                        if f[2]:
                            words[f[2] - 1] = True
                        return
                else:
                    n = _width(other, syms)
                    if n is not None and 1 <= n <= NBUF:
                        put(host_copy(ha is not None, other, n, digits))
                        return
            put(b'copy ' + _chan(a) + b' ' + _chan(b))
            return
        if first:
            first = False
            if t == b'pack':
                put(t)
                pre()
                return
            pre()
        if t == b'copy':
            copy_ops = []
            track = NOTRACK
            return
        put(t)
        k, name, kind, kk = track
        num = bool(t) and all(c in DIGITS for c in t)
        if k == 2:
            if t and num and len(syms) < MAXW:
                syms.append((name, (_decimal(t) & 127 | kk << 7) if kind else _decimal(t), kind))
            track = NOTRACK
        elif k == 3:
            track = (2, name, kind, _decimal(t) & 15) if num else NOTRACK
        elif k == 1 and t == b'data':
            track = (2, name, 0, 0)
        elif k == 1 and t in (b'table', b'array'):
            track = (3, name, 1 if t == b'table' else 2, 0)
        elif t[:1] == b':':
            nm = _name_of(t, 1)
            track = (1, nm[0], 0, 0) if nm and nm[1] == len(t) else NOTRACK
        else:
            track = NOTRACK

    while True:
        c = data[i]
        i += 1
        if c == 0:
            if state in ('tok', 'str'):
                end_token(tok, None)
                tok = bytearray()
            pre()
            if copy_ops is not None:
                put(b'copy' + b''.join(b' ' + x for x in copy_ops))
            for w, text in zip(words, FARWORDS, strict=True):
                if w:
                    put('\n' + text)
            break
        if state == 'idle':
            if c in WS:
                if copy_ops is None:
                    put(bytes([c]))
            elif c == ord('#'):
                state = 'com'
                put(bytes([c]))
            else:
                state = 'str' if c == ord('"') else 'tok'
                esc = False
                tok = bytearray([c])
        elif state == 'com':
            put(bytes([c]))
            if c == 10:
                state = 'idle'
        elif state == 'str':
            if len(tok) < MAXTOK:
                tok.append(c)
            if esc:
                esc = False
            elif c == ord('\\'):
                esc = True
            elif c == ord('"'):
                state = 'tok'
        else:
            if c in WS:
                end_token(tok, c)
                tok = bytearray()
                state = 'idle'
                if copy_ops is None:
                    put(bytes([c]))
            elif len(tok) < MAXTOK:
                tok.append(c)
    return ''.join(out).encode('latin-1') + b'\0', None


def language1(src, lang4=False):
    """The text of language 1 (without the zero byte) which the chain l3c -> l2l gives for a text of language 3 (for a text of language 4 with the pass l4c
    before l3c, lang4): (bytes, error or None)."""
    import l2ltext
    if lang4:
        src = l4c(src.encode('latin-1') + b'\0' if isinstance(src, str) else bytes(src) + b'\0')[0][:-1]
    l2, err = encode(src)
    if err:
        return b'', err
    if is_pack(src):                      # pack mode: the pass of the planner stands between l3c and l2l
        l2, err = pack_pass(l2)
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
    elif sys.argv[1:2] == ['-p']:
        main(True)
    elif sys.argv[1:2] == ['-x']:
        sys.stdout.buffer.write(l4c(sys.stdin.buffer.read())[0])
    elif sys.argv[1:2] == ['-l']:
        l1, e = language1(sys.stdin.buffer.read(), '-4' in sys.argv[2:])
        sys.stdout.buffer.write(l1)
        if e:
            sys.stderr.write(MESSAGES.get(e, 'l2l: ' + e) + '\n')
            sys.exit(1)
    else:
        sys.stderr.write('\n'.join(__doc__.splitlines()[-2:]) + '\n')
        sys.exit(2)
