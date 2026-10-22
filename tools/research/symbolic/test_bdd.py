import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bdd import BDD


def check(b, f, fn, n):
    for vals in itertools.product((0, 1), repeat=n):
        assert b.eval(f, vals) == fn(*vals), (vals,)


def main():
    b = BDD()
    a, bb, c = b.var(0), b.var(1), b.var(2)
    funcs3 = {
        "and": (b.and_(b.and_(a, bb), c), lambda x, y, z: x & y & z),
        "or": (b.or_(b.or_(a, bb), c), lambda x, y, z: x | y | z),
        "xor": (b.xor(b.xor(a, bb), c), lambda x, y, z: x ^ y ^ z),
        "maj": (b.or_(b.or_(b.and_(a, bb), b.and_(a, c)), b.and_(bb, c)),
                lambda x, y, z: (x & y) | (x & z) | (y & z)),
        "mux": (b.ite(a, bb, c), lambda x, y, z: y if x else z),
    }
    for name, (f, fn) in funcs3.items():
        check(b, f, fn, 3)
    # константы, не
    assert b.not_(0) == 1 and b.not_(1) == 0 and b.not_(b.not_(a)) == a

    # две записи одной функции — один узел
    f1 = b.xor(a, bb)
    f2 = b.or_(b.and_(a, b.not_(bb)), b.and_(b.not_(a), bb))
    assert f1 == f2
    assert b.size(f1) == 3
    # де Морган
    assert b.not_(b.and_(a, bb)) == b.or_(b.not_(a), b.not_(bb))
    # тавтология / противоречие
    assert b.or_(a, b.not_(a)) == 1 and b.and_(a, b.not_(a)) == 0
    # maj другой записью
    maj2 = b.ite(a, b.or_(bb, c), b.and_(bb, c))
    assert maj2 == funcs3["maj"][0]

    # случайные формулы от 6 переменных
    rng = random.Random(20240613)
    n = 6
    vs = [b.var(i) for i in range(n)]

    def rand(depth):
        # возвращает (узел, python-функция)
        if depth == 0 or rng.random() < 0.15:
            i = rng.randrange(n)
            return vs[i], (lambda v, i=i: v[i])
        op = rng.choice(["and", "or", "xor", "not", "ite"])
        if op == "not":
            f, pf = rand(depth - 1)
            return b.not_(f), (lambda v: 1 - pf(v))
        if op == "ite":
            f, pf = rand(depth - 1)
            g, pg = rand(depth - 1)
            h, ph = rand(depth - 1)
            return b.ite(f, g, h), (lambda v: pg(v) if pf(v) else ph(v))
        f, pf = rand(depth - 1)
        g, pg = rand(depth - 1)
        if op == "and":
            return b.and_(f, g), (lambda v: pf(v) & pg(v))
        if op == "or":
            return b.or_(f, g), (lambda v: pf(v) | pg(v))
        return b.xor(f, g), (lambda v: pf(v) ^ pg(v))

    tables = {}
    for _ in range(200):
        f, pf = rand(5)
        tt = []
        for vals in itertools.product((0, 1), repeat=n):
            r = b.eval(f, vals)
            assert r == pf(vals)
            tt.append(r)
        tt = tuple(tt)
        # каноничность: одна таблица истинности — один узел
        assert tables.setdefault(tt, f) == f
    print("ok: %d random formulas, %d distinct functions, %d nodes"
          % (200, len(tables), len(b.nodes)))


main()
