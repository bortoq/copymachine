"""Language 1: indexed copying. One word: row dl dh sl sh (copy [sl,sh) to [dl,dh)).
A program is a sequence of layers (rows executed in one tick). Every layer ends with an
implicit jump row: a row copying the text of the next layer into the processor. A halt
is a jump to a layer of NOPs. Row fields are numbers or thunks (resolved at layout)."""
from common import Mem


class Row:
    def __init__(self, dl, dh, sl, sh):
        self.f, self.addr, self.kind, self.n = [dl, dh, sl, sh], None, 'raw', None


def row(dl, dh, sl, sh):
    return Row(dl, dh, sl, sh)


class Layer:
    """to: 'next' | 'halt' | Layer | None (jump row is filled by the program: patched)."""

    def __init__(self, rows=(), to='next', entry=False):
        self.rows, self.to, self.entry = list(rows), to, entry
        self.jump, self.addr, self.u, self.keep = Row(0, 0, 0, 0), None, None, False
        self.jump.kind = 'jump'


def val(x):
    return x() if callable(x) else x


def widths(A, layers):
    """Stored width u of every layer (slots) and P, the processor width (even if bytes need it)."""
    W = max(len(l.rows) + 1 for l in layers)
    P = W + (W % 2 and A % 2)
    for i, l in enumerate(layers):
        w = len(l.rows) + 1
        if l.entry:
            l.u = P
        else:
            assert layers[i - 1].to == 'next'
            l.u = max(w, len(layers[i - 1].rows) + 1)
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
        for slot, r in enumerate(l.rows + [l.jump]):
            r.addr = None if l.addr is None else l.addr + slot * RB
    for i, l in enumerate(layers):
        t = l.to
        if t == 'next':
            t = layers[i + 1]
        if isinstance(t, Layer):
            f = (0, t.u * RB, t.addr, t.addr + t.u * RB)
        elif t == 'halt':
            f = (0, l.u * RB, nops, nops + l.u * RB)
        else:
            f = (0, P * RB, nops, nops + P * RB)
        l.jump.f = list(f)
    for i, l in enumerate(layers):
        for base in ([l.addr] if l.addr is not None else []) + ([0] if i == 0 else []):
            for slot, r in enumerate(l.rows + [l.jump]):
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
