"""Language 3: lookup tables. Words: table, lut (value of a function from a table), array (a table
whose entries are written), store (write an entry by a computed index), block, goto, if, call, ret,
halt, emit (stdout), warn (stderr), key (stdin), copy. The library over language 3 (lib.py: add, sub, band, lt, eq,
stack, push, pop, rec; shl, shr over language 2) is a mixin of Program. No registers: data are named
parts of space. The compiler lays rows out into layers so that nothing intersects in a tick
(including source with source)."""
import l1
import l2
from common import Alloc, Mem
from l4 import Long
from lib import Lib

STDOUT = object()                 # pseudo region: one stdout transfer per tick, order preserved
STDIN = object()                  # pseudo region: one stdin transfer per tick, order preserved
STDERR = object()                 # pseudo region: one stderr transfer per tick, order preserved


class Table:
    """Function tabulated at a base aligned to its span; entry i lies at base + off + (i << j).
    sh = sl + w must not carry into the index bits, hence off + w < 2**j (the stride). Several tables
    may share the stride (the plan of the program: j, off, group), then they share the base."""

    def __init__(self, name, ins, out, f=None, init=None, ent=None):
        self.name, self.ins, self.out = name, tuple(ins), out
        self.K, self.j0 = sum(ins), out.bit_length()   # j0: smallest j with 2**j > out
        self.j, self.off, self.gid = ent if ent else (self.j0, 0, name)
        self.span = 1 << (self.j + self.K)
        self.f, self.init = f, init
        self.data = l2.Data(name, self.span)           # a view: its address is the group's + off

    def fill(self, mem, addr):
        base, j, n = addr + self.off, self.j, 1 << self.K
        if self.init:
            return self.init(mem, base)
        for idx in range(n):
            args, v = [], idx
            for k in self.ins:
                args.append(v & ((1 << k) - 1)); v >>= k
            mem.put(base + (idx << j), self.f(*args), self.out)


def pack_tables(tabs, bump=True):
    """The plan of the layout of tables: tables go into the stride of another one when the widths
    fit (sum of widths < 2**j) and the index is not wider. Returns {name: (j, off, group)}.
    Chooses by the total span (depth-first over the stride of the leader: j0 or j0 + 1)."""
    order = sorted(tabs, key=lambda T: (-T.K, -T.out, T.name))
    best = [None, None]

    def go(i, groups, cost):
        if best[0] is not None and cost >= best[0]:
            return
        if i == len(order):
            best[0], best[1] = cost, [dict(g, mem=list(g['mem'])) for g in groups]
            return
        T = order[i]
        for g in groups:
            if T.K <= g['K'] and g['used'] + T.out <= (1 << g['j']) - 1:
                g['mem'].append((T, g['used'])); g['used'] += T.out
                go(i + 1, groups, cost)
                g['used'] -= T.out; g['mem'].pop()
                return                                   # first fit
        for j in ((T.j0, T.j0 + 1) if bump and len(order) <= 14 else (T.j0,)):
            g = dict(j=j, K=T.K, used=T.out, mem=[(T, 0)])
            groups.append(g)
            go(i + 1, groups, cost + (1 << (j + T.K)))
            groups.pop()

    go(0, [], 0)
    return {T.name: (g['j'], off, k) for k, g in enumerate(best[1]) for T, off in g['mem']}


class Op:
    def __init__(self, row, reads, writes):
        self.row, self.reads, self.writes = row, reads, writes


def ivs(refs):
    return [(r.region, r.off, r.off + r.n) for r in refs]


def ov(xs, ys):
    return any(a[0] is b[0] and a[1] < b[2] and b[1] < a[2] for a in xs for b in ys)


def schedule(ops, serial=False, direct=True):
    """List scheduling into ticks. Latency 1 for data and for a write into the text of a row
    (the write goes to the processor itself, in the tick before the row runs; the jump of that
    tick does not copy these bits: they are holes of its text). With direct=False the text of a
    row is fetched whole by the jump of the layer before: a write must be 2 layers before the row."""
    lay, at = [], []
    for i, o in enumerate(ops):
        lb = 0
        own = [(o.row, 0, 1 << 30)]
        for j in range(i):
            p = ops[j]
            if ov(p.writes, own):
                lb = max(lb, at[j] + (1 if direct else 2))
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


class Program(Lib, Long):
    def __init__(self, A, serial=False, plan=None, direct=True):
        self.A, self.S, self.RB, self.serial, self.plan, self.direct = A, 2 ** A - 6, 4 * A, serial, plan or {}, direct
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
            self.tables[name] = Table(name, ins, out, f, ent=self.plan.get(name))
            self.datas.append(self.tables[name].data)
        return self.tables[name]

    def array(self, name, ins, out, values=None):
        """A table whose entries are written: entry i (all args packed, first arg lowest) starts as
        values[i] (default 0). Read by lut, written by store; an index of the given bits cannot leave it."""
        n = 1 << sum(ins)
        assert name not in self.tables and (values is None or len(values) == n), name
        vals = values or [0] * n
        T = Table(name, ins, out, ent=self.plan.get(name),
                  init=lambda mem, addr: [mem.put(addr + (i << T.j), v, out) for i, v in enumerate(vals)])
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
        self._out(src, 2, STDOUT)

    def warn(self, src):
        """A message to stderr (the channel S+3): how a program reports a wrong input text (7.2.28)."""
        self._out(src, 3, STDERR)

    def _out(self, src, chan, region):
        src = norm(src)
        s = src.addr
        r = l1.row(self.S + chan, self.S + chan, s, lambda: s() + src.n)
        self._op(r, ivs([src]), [(region, 0, 1)])

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
        args, out = [pair(a) for a in args], norm(out)
        assert tuple(a[0].n for a in args) == T.ins and out.n == T.out, T.name
        A, base = self.A, T.data
        R = l2.copy(T.out, out, Ref0(base, T.out))
        off = 0
        for a, k in zip(args, T.ins, strict=True):
            for fld, x in zip((2 * A, 3 * A), a, strict=True):         # source fields sl, sh
                self.copy(l2.Ref(R, fld + T.j + off, k), x)
            off += k
        self._op(R, [(base, 0, T.span)], ivs([out]))
        self.lookups += 1

    def store(self, T, args, src):
        """T[args] = src: the same indirection on the destination side; the index bits are patched
        into the destination fields dl and dh of a row that copies src into one entry of the array."""
        args, src = [pair(a) for a in args], norm(src)
        assert tuple(a[0].n for a in args) == T.ins and src.n == T.out, T.name
        A, base = self.A, T.data
        R = l2.copy(T.out, Ref0(base, T.out), src)
        off = 0
        for a, k in zip(args, T.ins, strict=True):
            for fld, x in zip((0, A), a, strict=True):                # destination fields dl, dh
                self.copy(l2.Ref(R, fld + T.j + off, k), x)
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
        nm = 'if%d' % len(self.tables)
        T = Table(nm, (1,), 2 * A, ent=self.plan.get(nm), init=lambda mem, addr: (
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
    def make_plan(self):
        """After a first run of the builder: the layout of tables (stride shared by several tables)."""
        return pack_tables(list(self.tables.values()))

    def _group(self, ts):
        K, j = max(T.K for T in ts), ts[0].j
        assert all(T.j == j for T in ts)

        def gaps():
            out = []
            for idx in range(1 << K):
                pos = 0
                for a, b in sorted((T.off, T.off + T.out) for T in ts if idx < 1 << T.K):
                    out.append(((idx << j) + pos, a - pos)); pos = b
                out.append(((idx << j) + pos, (1 << j) - pos))
            return [(o, n) for o, n in out if n > 0]
        bits = 1 << (j + K)
        return l2.Data('grp_' + str(ts[0].gid), bits, lambda mem, addr: [T.fill(mem, addr) for T in ts],
                       align=bits, gaps=gaps), ts

    def assemble(self):
        A, RB = self.A, self.RB
        order = list(self.blocks.values())
        for b in order:
            assert b.end, 'block %s has no terminator' % b.name
        for b in order:
            lay, at = schedule(b.ops, self.serial, self.direct)
            lat = 1 if self.direct else 2
            need = max([at[i] + lat + 1 for i, o in enumerate(b.ops) if ov(o.writes, [(b.last.jump, 0, RB)])] + [1])
            n = max(len(lay), need)
            lay += [[] for _ in range(n - len(lay))]
            b.layers = [l1.Layer([b.ops[i].row for i in lay[k]], entry=(k == 0)) for k in range(n - 1)]
            b.layers.append(b.last)
            b.last.rows, b.last.entry = [b.ops[i].row for i in lay[n - 1]], (n == 1)
            b.nlayers = n
            loc = {id(r): (k, s) for k, L in enumerate(b.layers) for s, r in enumerate(L.rows + [L.jump])}
            for i, o in enumerate(b.ops):                # writes into the text of a row of the next layer
                for reg, lo, hi in o.writes:
                    if isinstance(reg, l1.Row) and id(reg) in loc and loc[id(reg)][0] - at[i] == 1:
                        k, s = loc[id(reg)]
                        assert o.row.dst.region is reg and k > 0
                        o.row.dst.direct = True
                        b.layers[k].holes.append((s * RB + lo, hi - lo))
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
        groups = {}
        for T in self.tables.values():
            groups.setdefault(T.gid, []).append(T)
        gd = [self._group(ts) for ts in groups.values()]
        views = {id(T.data) for T in self.tables.values()}
        l2.place(alloc, [d for d in self.datas if id(d) not in views] + [d for d, _ in gd])
        for d, ts in gd:
            for T in ts:
                T.data.addr = d.addr + T.off
        l1.place(A, layers, alloc)
        mem = Mem()
        nops = l1.encode(A, layers, alloc, mem, P)
        l2.write(mem, self.datas + [d for d, _ in gd])
        self.gdatas = [d for d, _ in gd]
        img, snap = l1.image(A, P, mem)
        self.layers, self.mem, self.snap = layers, mem, snap
        self.stats = dict(A=A, S=self.S, P=P, layers=len(layers), image=img, snapshot_bytes=snap,
                          boot_bytes=P * RB // 8, end=nops)
        return img


norm = l2.norm


def pair(a):
    """An argument of lut/store: a part of space, or a pair of parts holding the same value (two
    sources: the fields sl and sh, dl and dh, are patched in one layer, not in two)."""
    return tuple(norm(x) for x in a) if isinstance(a, tuple) else (norm(a),) * 2


def Ref0(data, n):
    return l2.Ref(data, 0, n)


def compile_program(build, lo=10, hi=17, serial=False, plan=True, direct=True):
    """Try the smallest address width A in which the program fits (two runs of the builder at every
    A: the first collects the tables, the second lays them out into shared strides)."""
    last = None
    for A in range(lo, hi):
        pl = None
        if plan:
            p0 = Program(A, serial)
            build(p0)
            pl = p0.make_plan()
        p = Program(A, serial, pl, direct)
        build(p)
        try:
            p.assemble()
            return p
        except MemoryError as e:
            last = e
    raise last
