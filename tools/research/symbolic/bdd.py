"""Стандартная ROBDD: общая таблица узлов, ite с кэшем. Только stdlib.

Узлы — целые: 0 и 1 — константы, остальные индексы в таблице (var, lo, hi).
Порядок переменных — по возрастанию номера (меньший номер ближе к корню).
"""

TERMINAL_VAR = 1 << 30


class BDD:
    def __init__(self):
        self.nodes = [(TERMINAL_VAR, 0, 0), (TERMINAL_VAR, 1, 1)]
        self.unique = {}
        self.ite_cache = {}
        self.zero = 0
        self.one = 1

    def mk(self, var, lo, hi):
        if lo == hi:
            return lo
        key = (var, lo, hi)
        n = self.unique.get(key)
        if n is None:
            n = len(self.nodes)
            self.nodes.append(key)
            self.unique[key] = n
        return n

    def var(self, i):
        return self.mk(i, 0, 1)

    def _cof(self, n, v):
        var, lo, hi = self.nodes[n]
        if var == v:
            return lo, hi
        return n, n

    def ite(self, f, g, h):
        if f == 1:
            return g
        if f == 0:
            return h
        if g == h:
            return g
        if g == 1 and h == 0:
            return f
        key = (f, g, h)
        r = self.ite_cache.get(key)
        if r is not None:
            return r
        v = min(self.nodes[f][0], self.nodes[g][0], self.nodes[h][0])
        f0, f1 = self._cof(f, v)
        g0, g1 = self._cof(g, v)
        h0, h1 = self._cof(h, v)
        r = self.mk(v, self.ite(f0, g0, h0), self.ite(f1, g1, h1))
        self.ite_cache[key] = r
        return r

    def not_(self, f):
        return self.ite(f, 0, 1)

    def and_(self, f, g):
        return self.ite(f, g, 0)

    def or_(self, f, g):
        return self.ite(f, 1, g)

    def xor(self, f, g):
        return self.ite(f, self.not_(g), g)

    def size(self, f):
        """Число узлов функции: внутренние узлы, достижимые из f (без констант)."""
        seen = set()
        stack = [f]
        while stack:
            n = stack.pop()
            if n < 2 or n in seen:
                continue
            seen.add(n)
            _, lo, hi = self.nodes[n]
            stack.append(lo)
            stack.append(hi)
        return len(seen)

    def eval(self, f, assignment):
        """assignment: dict или последовательность, индекс — номер переменной."""
        while f >= 2:
            var, lo, hi = self.nodes[f]
            f = hi if assignment[var] else lo
        return f
