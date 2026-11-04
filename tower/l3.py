"""Language 3: lookup tables. Words: table, lut (value of a function from a table), array (a table
whose entries are written), store (write an entry by a computed index), block, goto, if, call, ret,
halt, emit (stdout), key (stdin), copy. The library over language 3 (lib.py: add, sub, band, lt, eq,
stack, push, pop, rec; shl, shr over language 2) is a mixin of Program. No registers: data are named
parts of space. The compiler lays rows out into layers so that nothing intersects in a tick
(including source with source)."""
import l1
import l2
from common import Alloc, Mem
from lib import Lib

STDOUT = object()                 # pseudo region: one stdout transfer per tick, order preserved
STDIN = object()                  # pseudo region: one stdin transfer per tick, order preserved


class Table:
    """Function tabulated at a base aligned to its span; entry i lies at base + (i << j).
    sh = sl + w must not carry into the index bits, hence w < 2**j (the stride)."""

    def __init__(self, name, ins, out, f=None, init=None):
        self.name, self.ins, self.out = name, tuple(ins), out
        self.j = out.bit_length()                      # smallest j with 2**j > out
        self.span = 1 << (self.j + sum(ins))
        j, n = self.j, 1 << sum(ins)
        def fill(mem, addr):
            for idx in range(n):
                args, v = [], idx
                for k in ins:
                    args.append(v & ((1 << k) - 1)); v >>= k
                mem.put(addr + (idx << j), f(*args), out)
        self.data = l2.Data(name, self.span, init or fill, align=self.span)


class Op:
    def __init__(self, row, reads, writes):
        self.row, self.reads, self.writes = row, reads, writes


def ivs(refs):
    return [(r.region, r.off, r.off + r.n) for r in refs]


def ov(xs, ys):
    return any(a[0] is b[0] and a[1] < b[2] and b[1] < a[2] for a in xs for b in ys)


def schedule(ops, serial=False):
    """List scheduling into ticks. Latency 1 for data; a write into the text of a row must be
    2 layers before that row (its text is fetched whole by the jump of the layer before)."""
    lay, at = [], []
    for i, o in enumerate(ops):
        lb = 0
        own = [(o.row, 0, 1 << 30)]
        for j in range(i):
            p = ops[j]
            if ov(p.writes, own):
                lb = max(lb, at[j] + 2)
            if ov(p.writes, o.reads) or ov(p.reads, o.writes) or ov(p.writes, o.writes):
                lb = max(lb, at[j] + 1)
        L = max(lb, len(lay)) if serial else lb         # serial: one row per layer, no packing
        while True:
            while L >= len(lay):
                lay.append([])
            mine = o.reads + o.writes
            if not any(ov(mine, ops[k].reads + ops[k].writes) for k in lay[L]):
                break
            L += 1
        lay[L].append(i); at.append(L)
    return lay, at


class Block:
    def __init__(self, name, word):
        self.name, self.word, self.ops, self.end = name, word, [], None
        self.last = l1.Layer()                          # last layer: holds the terminating jump
        self.layers = []


class Program(Lib):
    def __init__(self, A, serial=False):
        self.A, self.S, self.RB, self.serial = A, 2 ** A - 6, 4 * A, serial
        self.datas, self.blocks, self.cur, self.words, self.links = [], {}, None, {}, {}
        self.tables, self.lookups, self.P, self.keep = {}, 0, None, set()
        self.recs, self.stores, self.keys = {}, 0, 0
        self._zeros = self._one = None
        self.zero = self.var('zero', 1)

    # --- named parts of space
    def var(self, name, bits, init=0):
        d = l2.Data(name, bits, init)
        self.datas.append(d)
        return d

    def table(self, name, ins, out, f):
        if name not in self.tables:
            self.tables[name] = Table(name, ins, out, f)
            self.datas.append(self.tables[name].data)
        return self.tables[name]

    def array(self, name, ins, out, values=None):
        """A table whose entries are written: entry i (all args packed, first arg lowest) starts as
        values[i] (default 0). Read by lut, written by store; an index of the given bits cannot leave it."""
        n = 1 << sum(ins)
        assert name not in self.tables and (values is None or len(values) == n), name
        vals = values or [0] * n
        T = Table(name, ins, out, init=lambda mem, addr: [mem.put(addr + (i << T.j), v, out)
                                                          for i, v in enumerate(vals)])
        self.tables[name] = T
        self.datas.append(T.data)
        return T

    def zeros(self, k):
        """k bits which are always 0 (one shared part of space)."""
        if self._zeros is None:
            self._zeros = self.var('zeros', k)
        self._zeros.bits = max(self._zeros.bits, k)
        return l2.Ref(self._zeros, 0, k)

    def one(self):
        if self._one is None:
            self._one = self.var('one1', 1, 1)
        return self._one.ref()

    # --- blocks and rows
    def block(self, name, word=None):
        assert self.cur is None or self.cur.end, 'previous block has no terminator'
        word = word or (self.cur.word if self.cur else None)
        self.cur = self.blocks[name] = Block(name, word)
        return self.cur

    def rl(self, name):
        """Return link of a word: a named part of space holding a reference to the caller's layer."""
        if name not in self.words:
            self.words[name] = self.var('rl_' + name, 2 * self.A)
        return self.words[name]

    def word(self, name):
        if name not in self.recs:
            self.rl(name)
        self.block(name, name)

    def _op(self, row, reads=None, writes=None):
        reads = ivs([row.src]) if reads is None else reads
        self.cur.ops.append(Op(row, reads, ivs([row.dst]) if writes is None else writes))

    def copy(self, dst, src):
        dst, src = norm(dst), norm(src)
        assert dst.n == src.n, 'copy of different lengths'
        assert not (dst.region is src.region and dst.off < src.off + src.n and src.off < dst.off + dst.n), \
            'copy of a part of space onto itself'
        self._op(l2.copy(dst.n, dst, src))

    def emit(self, src):
        src = norm(src)
        s = src.addr
        r = l1.row(self.S + 2, self.S + 2, s, lambda: s() + src.n)
        self._op(r, ivs([src]), [(STDOUT, 0, 1)])

    def key(self, dst):
        """A byte (bytes) of stdin into dst: the stdin channel is the source of a row."""
        dst = norm(dst)
        assert dst.n % 8 == 0, 'stdin transfers whole bytes'
        d = dst.addr
        r = l1.row(d, lambda: d() + dst.n, self.S + 1, self.S + 1)
        self._op(r, [(STDIN, 0, 1)], ivs([dst]) + [(STDIN, 0, 1)])
        self.keys += 1

    def lut(self, T, args, out):
        """Value of function T at args -> out: patch the index bits into the source fields
        sl and sh of a row that copies one table entry (indirection of language 1)."""
        args, out = [norm(a) for a in args], norm(out)
        assert tuple(a.n for a in args) == T.ins and out.n == T.out, T.name
        A, base = self.A, T.data
        R = l2.copy(T.out, out, Ref0(base, T.out))
        off = 0
        for a, k in zip(args, T.ins, strict=True):
            for fld in (2 * A, 3 * A):                   # source fields sl, sh
                self.copy(l2.Ref(R, fld + T.j + off, k), a)
            off += k
        self._op(R, [(base, 0, T.span)], ivs([out]))
        self.lookups += 1

    def store(self, T, args, src):
        """T[args] = src: the same indirection on the destination side; the index bits are patched
        into the destination fields dl and dh of a row that copies src into one entry of the array."""
        args, src = [norm(a) for a in args], norm(src)
        assert tuple(a.n for a in args) == T.ins and src.n == T.out, T.name
        A, base = self.A, T.data
        R = l2.copy(T.out, Ref0(base, T.out), src)
        off = 0
        for a, k in zip(args, T.ins, strict=True):
            for fld in (0, A):                           # destination fields dl, dh
                self.copy(l2.Ref(R, fld + T.j + off, k), a)
            off += k
        self._op(R, ivs([src]), [(base, 0, T.span)])
        self.stores += 1

    # --- control: the terminator is the jump row of the last layer
    def goto(self, name):
        self.cur.end = ('goto', name)

    def halt(self):
        self.cur.end = ('halt',)

    def ret(self):
        b = self.cur
        fields = l2.Ref(b.last.jump, 2 * self.A, 2 * self.A)
        if b.word in self.recs:
            self.pop(self.recs[b.word], fields)          # the link comes from the stack
        else:
            self.copy(fields, self.rl(b.word).ref())
        b.end = ('patched',)

    def call(self, word, back):
        if word in self.recs:
            self.push(self.recs[word], self.link(back))  # the link goes to the stack
        else:
            self.copy(self.rl(word).ref(), self.link(back).ref())
        self.cur.end = ('goto', word)

    def _pair(self, name):
        """The reference to a block: (sl, sh) of a jump row that copies its entry layer."""
        def init(mem, addr):
            L = self.blocks[name].layers[0]
            mem.put(addr, L.addr, self.A)
            mem.put(addr + self.A, L.addr + self.P * self.RB, self.A)
        return init

    def if_(self, c, then, other):
        """Choose the next layer by value: table of two references, indexed by the bit c."""
        A, b = self.A, self.cur
        T = Table('if%d' % len(self.tables), (1,), 2 * A, init=lambda mem, addr: (
            self._pair(other)(mem, addr), self._pair(then)(mem, addr + (1 << T.j))))
        self.tables[T.name] = T
        self.datas.append(T.data)
        self.keep |= {then, other}
        self.lut(T, [c], l2.Ref(b.last.jump, 2 * A, 2 * A))
        b.end = ('patched',)

    def link(self, name):
        if name not in self.links:
            self.links[name] = self.var('lk_' + name, 2 * self.A, self._pair(name))
            self.keep.add(name)
        return self.links[name]

    # --- assembly
    def assemble(self):
        A, RB = self.A, self.RB
        order = list(self.blocks.values())
        for b in order:
            assert b.end, 'block %s has no terminator' % b.name
        for b in order:
            lay, at = schedule(b.ops, self.serial)
            need = max([at[i] + 3 for i, o in enumerate(b.ops) if ov(o.writes, [(b.last.jump, 0, RB)])] + [1])
            n = max(len(lay), need)
            lay += [[] for _ in range(n - len(lay))]
            b.layers = [l1.Layer([b.ops[i].row for i in lay[k]], entry=(k == 0)) for k in range(n - 1)]
            b.layers.append(b.last)
            b.last.rows, b.last.entry = [b.ops[i].row for i in lay[n - 1]], (n == 1)
            b.nlayers = n
        for b in order:
            k = b.end
            b.last.to = {'goto': lambda k=k: self.blocks[k[1]].layers[0], 'halt': lambda: 'halt',
                         'patched': lambda: None}[k[0]]()
        for nm in self.keep:                             # entry layers reached through data links
            self.blocks[nm].layers[0].keep = True
        layers = [l for b in order for l in b.layers]
        self.P = P = l1.widths(A, layers)
        alloc = Alloc(self.S)
        alloc.take(0, P * RB)
        l2.place(alloc, self.datas)
        l1.place(A, layers, alloc)
        mem = Mem()
        nops = l1.encode(A, layers, alloc, mem, P)
        l2.write(mem, self.datas)
        img, snap = l1.image(A, P, mem)
        self.layers, self.mem, self.snap = layers, mem, snap
        self.stats = dict(A=A, S=self.S, P=P, layers=len(layers), image=img, snapshot_bytes=snap,
                          boot_bytes=P * RB // 8, end=nops)
        return img


norm = l2.norm


def Ref0(data, n):
    return l2.Ref(data, 0, n)


def compile_program(build, lo=10, hi=17, serial=False):
    """Try the smallest address width A in which the program fits."""
    last = None
    for A in range(lo, hi):
        p = Program(A, serial)
        build(p)
        try:
            p.assemble()
            return p
        except MemoryError as e:
            last = e
    raise last
