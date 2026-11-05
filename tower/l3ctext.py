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
  copy d s   shl x r k   shr x r k   (k 0..64)   emit s   warn s   key d
  lut &T args.. out    store &T args.. src       T is a table, an array, or add4 sub4 hex4 (made at the end of the image)
  add sub band lt eq x y r                        the library over the tables above (the widths as in lib.py)
  long! &pos &src   long@ &pos &dst               language 4, the long copy (pos: 128 bits; src, dst: at most NMAX bits)
  :name block   :name word   goto b   if c b1 b2   call w b   ret   halt         (the entry block is `main`)
A part of space is `&name`, `&name[k]`, `&name[lo:hi]` (a data defined before). Names are 1..14 bytes of A-Z a-z 0-9 _ (not a digit first);
the names of blocks and words must be a-z 0-9 _ (the tool l2l takes them as labels `b<name>`, `r<name>`; `!` and `@` stand only in the words long! long@), `zero` is a part of space of
1 bit which is 0. Data, tables and arrays are declared outside a block; a word or a block begins after the end of the block before.
Left out (text.py has them): stack push pop rec, dec<n>, 0x numbers, 'c' characters, \\x escapes, the
tables with several indices of a user, the check that a copy does not cover itself, that `zero` is not written, and that a part of
space of shl/shr differs from its source; the packing of tables (every table has its own stride, w.bit_length() bits).
Errors (stderr, halt; the output is cut after the last word that was complete; there is no zero byte): `l3c: bad text` (a wrong
character or token, an unknown word, a wrong kind or number of arguments, a label where it does not belong, the text ends inside a word), `l3c: bad label` (a name repeated, not defined before, the 1021st of a user, as 1024 places are in the table of names), `l3c: bad width` (widths do not agree, a part
outside its data), `l3c: bad block` (a row outside a block, after its end, a block without an end, `ret` outside a word, a declaration in a block), `l3c: too big` (the image does not
fit A = 20: also a datum of long! long@ over NMAX bits, the buffer of the request is above every image). Not checked, but defined: numbers over 20 bits (modulo 2^20), a value wider than its field.
The layout (positions are bits of the snapshot): the boot layer at 0 (the row 0, the jump to `main`), 64 zero bits (`zero` is the first,
`zeros` for shl/shr), the bit `one`, then in the order of the text: data, tables and arrays (a table at a multiple of its span
2^(w.bit_length() + K)), the words of a block (a layer each; lut and store: a patch of the row for every field, a layer which has nothing
but the jump, the row), the return link of a word (40 bits before its first block), the table of `if` and the link of `call` after the last
layer of the block; at the end the tables add4 .. hex4 which were used, then zeros up to a whole byte; label `e` is the end.
Run: python3 tower/l3ctext.py -e < prog.tw > prog.l2z   (the reference of the tool)
     python3 tower/l3ctext.py -x < prog.l2z > prog.l2x    (the reference of the pass l4p.tw, 23.17: the layers of the words long! long@)
     python3 tower/l3ctext.py -p < prog.l2z > prog.l2p    (the reference of the planner l3p.tw, 23.10: the pass over the output of pack mode)
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
PMESSAGES = {'bad': 'l3p: bad text\n', 'big': 'l3p: too big\n'}
MAXSYM = 1020                          # the symbols of a user (with add4, sub4, hex4, zero they fill the 1024 places)
MAXSTR = 32
ZERO_ADDR, ONE_ADDR, START = JB, JB + 64, JB + 65
SYSC = (1 << A) - 6                   # the channel SYS (language 4)
QB, NMAX = 0xfd200, 11566             # the request buffer of the long copy: above every image (tables of the library included); S - QB - 204 bits of data
LONGL = 11                            # layers of a long copy after the pass l4p (the placeholder is one layer, l3c moves the position by 10 more)
PACK_P = 3                            # slots of the processor of a packed program (pack mode)
HEAD = PACK_P * RB                    # the width of a block's first layer, and of the layer the processor takes at a jump
PZERO, PONE, PSTART = HEAD, HEAD + 64, HEAD + 65
WS = b' \t\r\n'
IDENT = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_')
DIGITS = frozenset(b'0123456789')
ESC = {ord('n'): 10, ord('t'): 9, ord('r'): 13, ord('0'): 0, ord('\\'): 92, ord('"'): 34}

# the words: kinds of the arguments (R a part of space, N a number lo..hi, V a value, B a block &name, T a table)
WORDS = ['data', 'table', 'array', 'copy', 'shl', 'shr', 'lut', 'store', 'block', 'word', 'goto', 'if', 'call', 'ret', 'halt',
         'emit', 'warn', 'key', 'add', 'sub', 'band', 'lt', 'eq', 'pack', 'long!', 'long@']
CODE = {w: i for i, w in enumerate(WORDS)}
DEFINING = ('data', 'table', 'array', 'block', 'word')
SHAPE = {'data': ('N1:65536', 'V'), 'table': ('N1:10', 'N1:64'), 'array': ('N1:10', 'N1:64'), 'copy': ('R', 'R'),
         'shl': ('R', 'R', 'N0:64'), 'shr': ('R', 'R', 'N0:64'), 'block': (), 'word': (), 'goto': ('B',), 'if': ('R', 'B', 'B'),
         'call': ('B', 'B'), 'ret': (), 'halt': (), 'emit': ('R',), 'warn': ('R',), 'key': ('R',)}
for _w in ('add', 'sub', 'band', 'lt', 'eq'):
    SHAPE[_w] = ('R', 'R', 'R')
SHAPE['pack'] = ()
SHAPE['long!'] = SHAPE['long@'] = ('R', 'R')
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
        elif w in ('long!', 'long@'):
            # the placeholder: the line `long`, a layer whose row is the four numbers (bits of the data + 2^19 for long@, the address of the position, the
            # address of the data, the position of the layer); the pass l4p (long_pass) makes LONGL layers of it
            (p, pb), (d, db) = a
            if pb != 128:
                raise Stop('wid')
            if db > NMAX:
                raise Stop('big')
            self.check()
            self.used.add('add4')
            self.put('long\n')
            self.layer(self.quad(db | (w == 'long@') << 19, p, d, self.pos))
            self.pos += (LONGL - 1) * JB
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
    if name_ok(t) or t in (b'long!', b'long@'):
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
    if ch in '!@':
        v |= 65536                      # a character of the words long! long@ (a word only, not of a label or a reference)
    return v


def generated():
    """name -> (K, out, lines of values) for the tables of l3c.tw made by this module."""
    T = {}
    T['cls'] = (8, 17, tvals([cls(rev8(i)) for i in range(256)]))
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


def x_generated():
    """name -> (K, out, lines of values) for the tables of programs/l4p.tw made by this module (the pass of 23.17)."""
    T = {}
    T['hexv'] = (8, 5, tvals([(int(chr(c), 16) | 16) if chr(c) in '0123456789abcdef' else 0 for c in map(rev8, range(256))]))
    T['qd'] = (3, 40, '  ' + ' '.join(istr(('%x' % (QB + o)).encode()) for o in (0, 0x1c, 0x2c, 0x30, 0x34, 0x38, 0x3c, 0x4c)))
    pat = b'long\n'
    T['pat'] = (4, 8, '  ' + ' '.join([istr(bytes([c])) for c in pat] + ['0'] * (16 - len(pat))))
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
            if o.q[2] in (S1, SYSC):                      # key, the read of the answer of SYS: the channel is read, from the destination to it written
                o.r, o.w = (o.q[2], o.q[2] + 1), (o.q[0], o.q[2] + 1)
            else:                                         # emit, warn: the channel is written
                o.r, o.w = (o.q[2], o.q[3]), (o.q[0], o.q[0] + 1)
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


# --- the pass of 23.17: language 4 (the tool programs/l4p.tw does the same on the chain: l3c -> l4p -> [l3p] -> l2l -> seed)
# l3c has no room for the long copy (98 % of A = 20): `long! &pos &src` and `long@ &pos &dst` it checks (pos has 128 bits, the data at most NMAX), and writes
# the line `long` and a layer whose row is the four numbers n (+ 2^19 for long@), the address of pos, the address of the data, the position of the layer;
# it moves the position by 10 layers more and marks the table add4 as used. The pass puts LONGL = 11 layers there. The request of the SYS channel is built
# of copies only (no row of the program writes a record by itself): at QB, above the image and its tables, the record op:8 chan:20 flags:16 arg:32
# off:128 (bits 0, 8, 28, 44, 76) and the data after it (204); the numbers op (6), flags (the direction) and arg (the bits of the data) are made of
# 4 bits copied from the table add4, whose entry (v, 0, 0) at 8v is the number v; the bits not written stay zeros.
# long!: the nibbles (7 layers), pos (128 bits), the data (n bits), the row to SYS, a layer of nothing. long@: the same without the data, the row to
# SYS, the row which reads max(n, 117) bits of the answer from SYS to QB+204 (117 = 97 + A: a whole record of the answer, the contract of the
# emulator), the copy of n bits into the data. The pass copies the text as it is; the line `long` is followed by five lines (the four numbers and the
# jump `c a0 0 X`): the value of a line is its last blank-separated token, in hex, mod 2^20 (a character that is not a hex digit, a blank, or the line
# break, or the end of the text inside the five lines: `l4p: bad text`, the output stops before the placeholder). A layer is 160 bits. Without the pass
# the line `long` is not a line of language 2: l2l (and l3p) stop with a report.
LPMESSAGES = {'bad': 'l4p: bad text\n'}


def _last_hex(line):
    tok = line.rsplit(' ', 1)[-1]
    if any(c not in '0123456789abcdef ' for c in line):
        raise Stop('bad')
    return int(tok, 16) & M if tok else 0


def long_text(put, n, p, d, first):
    """The 11 layers of a long copy (put or get of n bits, the position at p, the data at d), the first at `first`."""
    q = lambda o: '%x' % (QB + o)      # noqa: E731
    rows = ['c 4 %s &ta+30\n' % q(0), 'c 4 %s &ta+%x\n' % (q(0x1c), 0 if put else 8)]
    rows += ['c 4 %s &ta+%x\n' % (q(0x2c + 4 * i), 8 * (n >> 4 * i & 15)) for i in range(5)]
    rows.append('c 80 %s %x\n' % (q(0x4c), p))
    row = lambda *v: ''.join('d 14 %x\n' % (x & M) for x in v)      # noqa: E731
    if put:
        rows += ['c %x %s %x\n' % (n, q(0xcc), d), row(SYSC, SYSC, QB, QB + 0xcc + n), 'z 50\n']
    else:
        rows += [row(SYSC, SYSC, QB, QB + 0xcc), row(QB + 0xcc, QB + 0xcc + max(n, 0x75), SYSC, SYSC), 'c %x %x %s\n' % (n, d, q(0xcc))]
    return ''.join(r + 'c a0 0 %x\n' % ((first + JB * (j + 1)) & M) for j, r in enumerate(rows))


def long_pass(data):
    """The pass over the text of language 2 of l3c (see above); data ends with a zero byte, and so does the result: (bytes, error or None)."""
    text = data.decode('latin-1')
    assert text.endswith('\0')
    lines = text[:-1].split('\n')                        # the last piece is empty (the zero byte comes at the start of a line) or a line cut
    out, i = [], 0
    try:
        while i < len(lines) - 1:
            if lines[i] == 'long':
                if i + 5 >= len(lines) - 1:
                    raise Stop('bad')
                n, p, d, first, _ = (_last_hex(lines[i + k]) for k in range(1, 6))
                out.append(long_text(not n >> 19 & 1, n & 0x7ffff, p, d, first))
                i += 6
            else:
                out.append(lines[i] + '\n')
                i += 1
    except Stop as e:
        return ''.join(out).encode('latin-1'), e.why
    return (''.join(out) + lines[-1] + '\0').encode('latin-1'), None


def language1(src):
    """The text of language 1 (without the zero byte) which the chain l3c -> l4p -> l2l gives for a text of language 3: (bytes, error or None)."""
    import l2ltext
    l2, err = encode(src)
    if err:
        return b'', err
    l2, err = long_pass(l2)
    if err:
        return b'', 'l4p'
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
        out, err = long_pass(sys.stdin.buffer.read())
        sys.stdout.buffer.write(out)
        if err:
            sys.stderr.write(LPMESSAGES[err])
            sys.exit(1)
    elif sys.argv[1:2] == ['-l']:
        l1, e = language1(sys.stdin.buffer.read())
        sys.stdout.buffer.write(l1)
        if e:
            sys.stderr.write((LPMESSAGES['bad'] if e == 'l4p' else MESSAGES.get(e, 'l2l: ' + e)) + '\n')
            sys.exit(1)
    else:
        sys.stderr.write('\n'.join(__doc__.splitlines()[-2:]) + '\n')
        sys.exit(2)
