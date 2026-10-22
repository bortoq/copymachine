#!/usr/bin/env python3
"""Тест 13.5.3: символьный исполнитель копимашины.

(1) для A, B, C BDD выходных бит на каждом наборе читаемых бит совпадает со
    столбцом out таблицы docs/research/tables/X.tsv или X.tsv.gz (и с expected);
(2) выходы A и B — одни и те же узлы (равенство реализаций сложения);
(3) выходы A и D — разные узлы;
дополнительно: полное состояние памяти после исполнения совпадает с эталоном
vm2_reference.run на выборке входов; слишком большой перебор и канал дают
исключения.
Запуск: python3 -B tools/research/symbolic/test_symexec.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import programs as P
import symexec as S
from bdd import BDD
from vm2_reference import run, put, get
from copycode.vm2.boundary import boot_stream

BUILD = {
    'A': lambda: P.build_lookup_add(4),
    'B': lambda: P.build_ripple_add(4),
    'C': lambda: P.build_less(8),
    'D': lambda: P.build_lookup_add(4, corrupt=(3, 5), name='D'),
}
TABLES = P.ROOT / 'docs/research/tables'


def read_table(name):
    rows = []
    for line in P.read_table_text(TABLES, name).splitlines():
        if line.startswith('#') or line.startswith('a\t') or not line.strip():
            continue
        a, b, out, exp, ok = line.split('\t')
        rows.append((int(a), int(b), int(out), int(exp)))
    return rows


def assignment(prog, values):
    asg = {}
    for (name, _, width), v in zip(prog.reads, values):
        for j in range(width):
            asg[S.var_index(prog, name, j)] = v >> j & 1
    return asg


def out_value(bdd, nodes, asg):
    return sum(bdd.eval(n, asg) << j for j, n in enumerate(nodes))


def main():
    bdd = BDD()
    progs, outs = {}, {}
    for name in 'ABCD':
        progs[name] = BUILD[name]()
        m, outs[name] = S.execute_symbolic(progs[name], bdd)
        print(f'{name}: тактов {m.cost["layers"]}, копий {m.cost["copies"]}, '
              f'вариантов поля {m.cost["variants"]}, узлов выхода '
              f'{[bdd.size(n) for n in outs[name]]}')
        assert m.cost['layers'] == progs[name].layers, (name, m.cost)

    # (1) все наборы читаемых бит против таблиц
    for name in 'ABC':
        prog, rows = progs[name], read_table(name)
        ra, rb = prog.input_ranges()
        assert len(rows) == ra * rb, (name, len(rows))
        for a, b, out, exp in rows:
            got = out_value(bdd, outs[name], assignment(prog, (a, b)))
            assert got == out == exp, (name, a, b, got, out, exp)
        print(f'(1) {name}: {len(rows)} наборов совпали с таблицей')

    # (2) A и B — одни и те же узлы; (3) A и D — разные
    assert len(outs['A']) == len(outs['B']) == 5
    assert outs['A'] == outs['B'], (outs['A'], outs['B'])
    print('(2) выходы A и B: узлы', outs['A'])
    assert outs['A'] != outs['D']
    diff = [j for j in range(5) if outs['A'][j] != outs['D'][j]]
    assert diff == [0], diff
    print('(3) выходы A и D различаются в битах', diff)

    # D тоже совпадает со своей таблицей
    prog, rows = progs['D'], read_table('D')
    for a, b, out, _ in rows:
        assert out_value(bdd, outs['D'], assignment(prog, (a, b))) == out, (a, b)

    # полное состояние памяти против эталона (константные подстановки)
    rnd = random.Random(1)
    for name in 'ABCD':
        prog = progs[name]
        ra, rb = prog.input_ranges()
        m = S.SymExec.from_prog(prog, bdd)
        m.run()
        for a, b in [(0, 0), (ra - 1, rb - 1), (3, 5)] + [(rnd.randrange(ra), rnd.randrange(rb)) for _ in range(5)]:
            img = bytearray(prog.image)
            for (_, pos, w), v in zip(prog.reads, (a, b)):
                put(img, pos, w, v)
            r = run(boot_stream(bytes(img), prog.size, prog.slots), prog.size, prog.slots)
            asg = assignment(prog, (a, b))
            for p in range(prog.size):
                assert bdd.eval(m.mem[p], asg) == get(r['memory'], p, 1), (name, a, b, p)
        print(f'память {name}: полное состояние совпало с эталоном')

    # границы: слишком большой перебор, канал
    big = S.SymExec(BDD(), [0] * 4096, 4096, 8)
    b2 = big.bdd
    for k in range(13):                      # поле src: 13 независимых переменных, 2^13 значений
        big.mem[25 + k] = b2.var(k)
    big.mem[0:12] = [1] + [0] * 11            # n = 1
    try:
        big.step()
        raise SystemExit('ожидалось TooLarge')
    except S.TooLarge as e:
        print('TooLarge:', e)
    ch = S.SymExec(BDD(), [0] * 4096, 4096, 8)
    ch.mem[0:12] = [1] + [0] * 11
    for k in range(13):                      # dst = 4096 (канал)
        ch.mem[12 + k] = 1 if k == 12 else 0
    try:
        ch.step()
        raise SystemExit('ожидалось Unsupported')
    except S.Unsupported as e:
        print('Unsupported:', e)
    # пересекающиеся копии: эталон и символьный исполнитель отвергают одинаково
    prog = progs['B']
    size, slots = prog.size, prog.slots
    a = size.bit_length()
    z, isz = a - 1, 3 * a - 1
    img = bytearray(prog.image)
    for k, (n, d, s) in enumerate([(4, 3000, 2000), (4, 2002, 3500)]):   # src 2000..2004 и dst 2002..2006
        for off, w, v in ((0, z, n), (z, a, d), (z + a, a, s)):
            put(img, k * isz + off, w, v)
    try:
        run(boot_stream(bytes(img), size, slots), size, slots)
        raise SystemExit('эталон должен отвергнуть пересечение')
    except AssertionError as e:
        ref_err = type(e)
    mem = [(img[i // 8] >> (7 - i % 8)) & 1 for i in range(size)]
    try:
        S.SymExec(BDD(), mem, size, slots).step()
        raise SystemExit('символьный исполнитель должен отвергнуть пересечение')
    except AssertionError as e:
        assert type(e) is ref_err
    print('пересечение: эталон и символьный исполнитель дали AssertionError')
    print('OK')


if __name__ == '__main__':
    main()
