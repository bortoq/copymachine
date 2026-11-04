"""Language 2: shortened instruction. Word: copy n d s  ==  row d d+n s s+n (3 fields, not 4).
Also named parts of space (data) and references into them; the compiler places them."""
import l1


class Data:
    """A named part of space: bits, initial value (int or fn(mem, addr)), alignment."""

    def __init__(self, name, bits, init=0, align=1, gaps=None):
        self.name, self.bits, self.init, self.align, self.addr = name, bits, init, align, None
        self.gaps = gaps                      # fn() -> [(off, n)] parts of it which are free for others

    def __getitem__(self, k):
        if isinstance(k, slice):
            lo = k.start or 0
            return Ref(self, lo, (self.bits if k.stop is None else k.stop) - lo)
        return Ref(self, k, 1)

    def ref(self):
        return Ref(self, 0, self.bits)


class Ref:
    """n bits at offset off of a Data or of a Row's text (a row field can be a destination)."""

    def __init__(self, region, off, n):
        self.region, self.off, self.n = region, off, n
        self.direct = False         # a field of a row of the next layer, written in the processor itself

    def addr(self):
        return (self.region.paddr if self.direct else self.region.addr) + self.off

    def __getitem__(self, k):
        lo = k.start or 0
        return Ref(self.region, self.off + lo, (self.n if k.stop is None else k.stop) - lo)


def norm(x):
    return x.ref() if isinstance(x, Data) else x


def copy(n, dst, src):
    d, s = dst.addr, src.addr
    r = l1.row(d, lambda: d() + n, s, lambda: s() + n)
    r.kind, r.n, r.dst, r.src = 'copy', n, dst, src
    return r


def place(alloc, datas):
    """Tables (big alignment) first, then the rest by size."""
    for d in sorted(datas, key=lambda d: (-d.align, -d.bits)):
        d.addr = alloc.alloc(d.bits, d.align)
        if d.gaps:
            alloc.release([(d.addr + o, n) for o, n in d.gaps()])


def write(mem, datas):
    for d in datas:
        if callable(d.init):
            d.init(mem, d.addr)
        elif d.init:
            mem.put(d.addr, d.init, d.bits)


