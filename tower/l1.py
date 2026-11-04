"""Language 1: indexed copying. One word: row dl dh sl sh (copy [sl,sh) to [dl,dh)).
A program is a sequence of layers (rows executed in one tick). Every layer ends with an
implicit jump row: a row copying the text of the next layer into the processor. A halt
is a jump to a layer of NOPs. Row fields are numbers or thunks (resolved at layout)."""
from common import Mem


class Row:
    def __init__(self, dl, dh, sl, sh):
        self.f, self.addr, self.kind, self.n = [dl, dh, sl, sh], None, 'raw', None
        self.paddr = None                 # position in the processor (slot * 4A), when the row is in a layer


def row(dl, dh, sl, sh):
    return Row(dl, dh, sl, sh)


class Layer:
    """to: 'next' | 'halt' | Layer | None (jump row is filled by the program: patched)."""

    def __init__(self, rows=(), to='next', entry=False):
        self.rows, self.to, self.entry = list(rows), to, entry
        self.jump, self.addr, self.u, self.keep = Row(0, 0, 0, 0), None, None, False
        self.jump.kind = 'jump'
        self.jumps = [self.jump]          # the jump is one row, or several when the next layer has holes
        self.holes = []                   # (bit offset, bits) of this layer's text which are written
                                          # straight into the processor one tick earlier (not by the jump)


def val(x):
    return x() if callable(x) else x


def pieces(holes, end):
    """The text [0, end) without the holes: the parts which a jump copies."""
    out, pos = [], 0
    for lo, n in sorted(holes):
        if lo > pos:
            out.append((pos, lo))
        pos = max(pos, lo + n)
    return out + [(pos, end)]


def widths(A, layers):
    """Stored width u of every layer (slots) and P, the processor width (even if bytes need it).
    A jump has one row per part of the next layer's text which is not a hole."""
    for i, l in enumerate(layers):
        nxt = layers[i + 1] if l.to == 'next' else None
        n = len(pieces(nxt.holes, 1)) if nxt is not None else 1
        l.jumps = [l.jump] + [Row(0, 0, 0, 0) for _ in range(n - 1)]
        for r in l.jumps:
            r.kind = 'jump'
    W = max(len(l.rows) + len(l.jumps) for l in layers)
    P = W + (W % 2 and A % 2)
    for i, l in enumerate(layers):
        w = len(l.rows) + len(l.jumps)
        if l.entry:
            l.u = P
        else:
            assert layers[i - 1].to == 'next'
            l.u = max(w, len(layers[i - 1].rows) + len(layers[i - 1].jumps))
    return P


def place(A, layers, alloc):
    """Put the stored texts of layers in free space (the boot layer only if something jumps to it)."""
    RB = 4 * A
    used = {id(l.to) for l in layers if isinstance(l.to, Layer)}
    for i, l in enumerate(layers):
        if i == 0 and id(l) not in used and not l.keep:
            continue                           # the boot layer is only in the snapshot at 0
        l.addr = alloc.alloc(l.u * RB)


def encode(A, layers, alloc, mem, P):
    RB, S = 4 * A, 2 ** A - 6
    nops = alloc.end()
    alloc.take(nops, P * RB)
    if nops + P * RB > S:
        raise MemoryError('nops layer does not fit')
    for l in layers:
        for slot, r in enumerate(l.rows + l.jumps):
            r.addr = None if l.addr is None else l.addr + slot * RB
            r.paddr = slot * RB
    for i, l in enumerate(layers):
        t = l.to
        if t == 'next':
            t = layers[i + 1]
        if isinstance(t, Layer):
            ps = pieces(t.holes, t.u * RB)
            assert len(ps) == len(l.jumps), 'jump pieces and rows differ'
            for r, (lo, hi) in zip(l.jumps, ps, strict=True):
                r.f = [lo, hi, t.addr + lo, t.addr + hi]
            continue
        elif t == 'halt':
            f = (0, l.u * RB, nops, nops + l.u * RB)
        else:
            f = (0, P * RB, nops, nops + P * RB)
        l.jump.f = list(f)
    for i, l in enumerate(layers):
        for base in ([l.addr] if l.addr is not None else []) + ([0] if i == 0 else []):
            for slot, r in enumerate(l.rows + l.jumps):
                for k, x in enumerate(r.f):
                    mem.put(base + slot * RB + k * A, val(x), A)
    return nops


def image(A, P, mem):
    """Boot packet: the seed layer (P slots, slot 0 = stdin copy over the snapshot), then the snapshot."""
    RB, S = 4 * A, 2 ** A - 6
    snap = mem.trimmed(P * RB)
    b0 = Mem()
    for k, x in enumerate((0, len(snap) * 8, S + 1, S + 1)):
        b0.put(k * A, x, A)
    return b0.trimmed(P * RB) + snap, len(snap)
