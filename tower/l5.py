"""Language 5: the price. Words: cost (the tuple of a word, a block or a program), price (one number from
the tuple), replace (the cheaper of several definitions of one word with the same results).
The price is computed ONLY from the finished output of the lower languages (the layers and their rows after
the layout, the memory image of the links); languages 1-4 know nothing about it and have no hooks for it.
cost = (rows, layers, bits, ticks): rows - rows of the stored layers with the jump rows; layers - stored
layers; bits - bits of the text of those layers (3A per copy or jump row, NOP padding included); ticks - the
layers executed on the path (a layer is a tick; boot adds BOOT_TICKS to a program). rows, layers, bits are
stored once however often a word runs. A call costs the callee (its stored part once, its ticks per call)
plus the call and return rows, which lie in the layers of the caller and of the callee. A path with an unknown
number of passes (a loop over data, recursion) costs FORBID: the unsolved is solved at a prohibitive price,
cheapened by giving `passes`. A branch costs its dearer arm.
The choice of the layout of a program of the chain (serial or `pack`) by the same price is made on the chain itself: tower/tests/layout.py."""
from collections import namedtuple

import common
import l1
import l2
import l3

FORBID = 2 ** 24                      # the prohibitive price (as fc-forbid of the present language)
INFEASIBLE = -1                       # a path which cannot be taken (inside ticks)
BOOT_TICKS = 2                        # a program runs 2 ticks more than its layers (boot packet, nops)
PRICE_W = (32, 32, 1, 64)             # weights of (rows, layers, bits, ticks) in price: change here


class Cost(namedtuple('Cost', 'rows layers bits ticks')):
    def __add__(self, o):
        return Cost(*(min(x + y, FORBID) for x, y in zip(self, o, strict=True)))


ZERO = Cost(0, 0, 0, 0)


def price(c, w=PRICE_W):
    """One number from the tuple of cost: the weighted sum; FORBID when any part is prohibitive."""
    if max(c) >= FORBID:
        return FORBID
    return sum(a * b for a, b in zip(w, c, strict=True))


def text_bits(A, layers):
    """Bits of the stored text of layers: 3A per copy or jump row, 4A per other row, free slots are NOPs."""
    n = 0
    for l in layers:
        rows = l.rows + l.jumps
        n += sum(3 * A if r.kind in ('copy', 'jump') else 4 * A for r in rows) + (l.u - len(rows)) * 3 * A
    return n


def own(p, b):
    """The stored cost of one block, from its layers."""
    return Cost(sum(len(l.rows) + len(l.jumps) for l in b.layers), len(b.layers), text_bits(p.A, b.layers), 0)


class _Shape:
    """What the layers of a program say about its control: the block of every layer, the kind of the end of
    every block (halt, goto, call with its return block, ret, if with its two arms, unknown)."""

    def __init__(self, p):
        self.p = p
        self.of = {id(l): b for b in p.blocks.values() for l in b.layers}
        self.at = {b.layers[0].addr: b for b in p.blocks.values() if b.layers[0].addr is not None}
        self.end = {b.name: self._end(b) for b in p.blocks.values()}

    def _block(self, a):
        return self.at.get(a)

    def _link(self, b):
        """The return block of a call: a copy of 2A bits from a part of space which holds (entry, entry + P rows)."""
        p = self.p
        for l in b.layers:
            for r in l.rows:
                if r.kind == 'copy' and r.n == 2 * p.A and isinstance(r.src.region, l2.Data):
                    a = p.mem.get(r.src.addr(), p.A)
                    if self._block(a) is not None and p.mem.get(r.src.addr() + p.A, p.A) == a + p.P * p.RB:
                        return self._block(a)

    def _arms(self, b, src):
        """The two arms of an if: the table of references (a table of 2A bits holding entries of blocks)."""
        p = self.p
        for T in p.tables.values():
            if T.data is src.region and T.out == 2 * p.A and T.K == 1:
                arms = [self._block(p.mem.get(T.data.addr + (i << T.j), p.A)) for i in (0, 1)]
                return arms if None not in arms else None

    def _end(self, b):
        t = b.last.to
        if t == 'halt':
            return ('halt',)
        if isinstance(t, l1.Layer):
            nb = self.of[id(t)]
            back = self._link(b) if nb.word != b.word else None
            return ('call', nb, back) if back else ('goto', nb)
        for l in b.layers:                              # the jump row is patched: by a copy (ret) or by a lookup
            for r in l.rows:
                if r.kind == 'copy' and isinstance(r.dst.region, l1.Row) and r.dst.region is b.last.jump:
                    if any(T.data is r.src.region for T in self.p.tables.values()):
                        arms = self._arms(b, r.src)
                        return ('if', *arms) if arms else ('unknown',)
                    return ('ret',)
        return ('unknown',)


def ticks(p, entry=None, passes=None):
    """Ticks of the path from the block `entry` (the first block) until halt or, in a word, ret.
    passes: {name of the block with the back edge of a loop (its if, or its goto to the head of the loop):
    the number of times that block runs}."""
    sh, passes = _Shape(p), passes or {}
    first = p.blocks[entry] if entry else next(iter(p.blocks.values()))

    def walk(b, acc, path, rets, spent=frozenset()):
        path = path + [(b, acc)]
        acc += len(b.layers)
        e = sh.end[b.name]
        if e[0] == 'halt':
            return acc
        if e[0] == 'goto':
            k = next((i for i, (q, _) in enumerate(path) if q is e[1]), None)
            if k is None:
                return walk(e[1], acc, path, rets, spent)
            if b.name not in passes:
                return FORBID                             # a loop over data: the number of passes is unknown
            if b.name in spent:
                return INFEASIBLE                         # the last pass leaves the loop by the other arm
            return walk(e[1], acc + (passes[b.name] - 1) * (acc - path[k][1]), path[:k], rets, spent | {b.name})
        if e[0] == 'call':
            return walk(e[1], acc, path, rets + [(e[2], path)], spent)
        if e[0] == 'ret':
            return walk(rets[-1][0], acc, rets[-1][1], rets[:-1], spent) if rets else acc
        if e[0] == 'if':
            on = [q for q in e[1:] if any(q is x for x, _ in path)]
            if len(on) == 1:
                n = passes.get(b.name)
                if n is None:
                    return FORBID                         # a loop over data: the number of passes is unknown
                start = next(a for x, a in path if x is on[0])
                out = e[1] if on[0] is e[2] else e[2]
                return walk(out, acc + (n - 1) * (acc - start), path, rets, spent)
            if on:
                return FORBID
            return max(walk(q, acc, path, rets, spent) for q in e[1:])
        return FORBID                                     # unknown end (the stack of recursion)
    return min(walk(first, 0, [], []), FORBID)


def _callees(p, sh, w):
    """The words which the word w calls, directly or not."""
    seen, todo = set(), [w]
    while todo:
        v = todo.pop()
        for b in p.blocks.values():
            e = sh.end[b.name]
            if b.word == v and e[0] == 'call' and e[1].word not in seen | {w}:
                seen.add(e[1].word)
                todo.append(e[1].word)
    return seen


def cost(p, word=None, passes=None):
    """The cost of the program (word=None; it also holds the words) or of a word: its stored blocks and those
    of the words it calls, once; its ticks along its path. p is an assembled l3.Program."""
    sh = _Shape(p)
    if word is None:
        c = sum((own(p, b) for b in p.blocks.values()), ZERO)
        return c + Cost(0, 0, 0, min(ticks(p, None, passes) + BOOT_TICKS, FORBID))
    ws = {word} | _callees(p, sh, word)
    c = sum((own(p, b) for b in p.blocks.values() if b.word in ws), ZERO)
    return c + Cost(0, 0, 0, ticks(p, word, passes))


def parts(p):
    """The stored cost of every word (the key None is the main part); their sum is the program's."""
    out = {}
    for b in p.blocks.values():
        out[b.word] = out.get(b.word, ZERO) + own(p, b)
    return out


Choice = namedtuple('Choice', 'index prices program')


def replace(*defs, inputs=(b'',)):
    """The cheaper of several definitions of one word. A definition is a builder build(p) of a whole program
    (its main uses the word) or (build, options), the options are those of l3.compile_program (serial, plan,
    direct) and `passes`. All definitions must give the same result on every input of `inputs` (the whole
    table of a small word, or a set of runs); a different result is rejected (ValueError). The check is made
    here, on the host, once; the chosen program has none. Returns Choice(index, prices, program)."""
    made = []
    for d in defs:
        build, opts = d if isinstance(d, tuple) else (d, {})
        opts = dict(opts)
        passes = opts.pop('passes', None)
        made.append((l3.compile_program(build, **opts), passes))
    want = None
    for p, _ in made:
        got = []
        for inp in inputs:
            r = common.run(p.stats['image'], p.stats['A'], p.stats['P'], checked=False, stdin=inp)
            got.append((r.rc, r.out))
        if want is None:
            want = got
        elif got != want:
            raise ValueError('definitions give different results')
    prices = [price(cost(p, passes=ps)) for p, ps in made]
    i = prices.index(min(prices))
    return Choice(i, prices, made[i][0])
