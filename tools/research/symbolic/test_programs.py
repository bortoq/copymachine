#!/usr/bin/env python3
"""Тест 13.5.2: полный перебор читаемых бит через vm2_reference.run.

A, B, C совпадают с арифметикой Python на всех входах, D расходится хотя бы
на одном. Таблицы A, B, D лежат в docs/research/tables/{A,B,D}.tsv (пишутся только
если файла нет), C — в C.tsv.gz.
C по умолчанию сверяется по выборке из 4096 входов (seed 1) и со строками
сохранённой таблицы; полный перебор C (65536 входов, ~4 мин) и перезапись
C.tsv.gz — только с флагом --full.
Запуск: python3 -B tools/research/symbolic/test_programs.py [--full]
"""
import itertools
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import programs as P

TABLES = P.ROOT / 'docs/research/tables'
BUILD = {
    'A': lambda: P.build_lookup_add(4),
    'B': lambda: P.build_ripple_add(4),
    'C': lambda: P.build_less(8),
    'D': lambda: P.build_lookup_add(4, corrupt=(3, 5), name='D'),
}
DESC = {
    'A': '4-битное сложение поиском по таблице (256 строк по 8 бит)',
    'B': '4-битное сложение поразрядно, таблица полного сумматора с переносом',
    'C': '8-битное сравнение a<b без знака, цепочка по таблице (a,b,lt) по 4 бита за шаг',
    'D': 'вариант A, в строке a=3,b=5 испорчен младший бит суммы',
}


def _row(args):
    name, a, b = args
    prog = _CACHE.get(name) or _CACHE.setdefault(name, BUILD[name]())
    return a, b, P.execute(prog, a, b)


_CACHE = {}


C_SAMPLE = 4096


def full_table(name, sample=None):
    prog = BUILD[name]()
    ra, rb = (1 << w for _, _, w in prog.reads)
    if sample:
        rnd = random.Random(1)
        jobs = [(name, rnd.randrange(ra), rnd.randrange(rb)) for _ in range(sample)]
    else:
        jobs = [(name, a, b) for b in range(rb) for a in range(ra)]
    rows = list(map(_row, jobs))
    return prog, rows


def save(name, prog, rows, cost):
    TABLES.mkdir(parents=True, exist_ok=True)
    (_, pa, wa), (_, pb, wb) = prog.reads
    head = [
        f'# программа {name}: {DESC[name]}',
        f'# образ vm2: пространство {prog.size} бит, слотов {prog.slots}, рабочих слоёв {prog.layers}',
        f'# читаются: a = биты {pa}..{pa + wa - 1}, b = биты {pb}..{pb + wb - 1} (младший по младшему адресу)',
        f'# выдаются: биты {prog.outs} (младший первым)',
        '# цена одного запуска (с установкой образа через канал): ' +
        ' '.join(f'{k}={v}' for k, v in cost.items()),
        '# столбцы: a, b, out (результат vm2), expected (арифметика Python), ok',
        'a\tb\tout\texpected\tok',
    ]
    body = []
    for a, b, out in rows:
        e = prog.expected(a, b)
        body.append(f'{a}\t{b}\t{out}\t{e}\t{int(out == e)}')
    text = '\n'.join(head + body) + '\n'
    if name == 'C':
        P.write_table_gz(TABLES / 'C.tsv.gz', text)
        return
    f = TABLES / f'{name}.tsv'
    if not f.exists():          # существующие A, B, D не переписываются
        f.write_text(text, encoding='utf-8')


def main():
    full = '--full' in sys.argv[1:]
    results = {}
    if True:
        for name in 'ABCD':
            sample = C_SAMPLE if name == 'C' and not full else None
            prog, rows = full_table(name, sample)
            _, cost = P.execute(prog, 0, 0, counters=True)
            if sample:
                saved = {}
                for line in P.read_table_text(TABLES, 'C').splitlines():
                    if line and line[0] != '#' and not line.startswith('a\t'):
                        a, b, out, _, _ = line.split('\t')
                        saved[int(a), int(b)] = int(out)
                assert len(saved) == 65536, len(saved)
                assert all(saved[a, b] == o for a, b, o in rows), 'выборка C расходится с таблицей'
            else:
                save(name, prog, rows, cost)
            bad = [(a, b, o, prog.expected(a, b)) for a, b, o in rows if o != prog.expected(a, b)]
            results[name] = (len(rows), bad)
            print(name, 'inputs', len(rows), 'mismatches', len(bad), 'layers', prog.layers, cost)
    for name in 'ABC':
        n, bad = results[name]
        assert not bad, (name, bad[:5])
    n, bad = results['D']
    assert len(bad) >= 1, 'D must differ from Python arithmetic'
    assert bad == [(3, 5, 9, 8)], bad
    assert results['A'][0] == 256 and results['B'][0] == 256 and results['C'][0] == (65536 if full else C_SAMPLE)
    # параметризация шириной: B на 8 и 12 бит (выборка), A на 3 бит полностью
    import random
    rnd = random.Random(1)
    for w in (8, 12):
        b = P.build_ripple_add(w)
        for _ in range(40):
            x, y = rnd.randrange(1 << w), rnd.randrange(1 << w)
            assert P.execute(b, x, y) == x + y, (w, x, y)
        m = (1 << w) - 1
        for x, y in ((0, 0), (m, m), (m, 1), (1, m)):
            assert P.execute(b, x, y) == x + y
    a3 = P.build_lookup_add(3)
    for x, y in itertools.product(range(8), repeat=2):
        assert P.execute(a3, x, y) == x + y
    for dg in (1, 2):
        cc = P.build_less(8, digit=dg)
        for x, y in ((0, 0), (1, 0), (0, 1), (255, 254), (254, 255), (16, 15), (15, 16), (77, 77), (3, 200)):
            assert P.execute(cc, x, y) == int(x < y), (dg, x, y)
    c4 = P.build_less(4)
    for x, y in itertools.product(range(16), repeat=2):
        assert P.execute(c4, x, y) == int(x < y)
    assert len(os.listdir(TABLES)) >= 4
    print('ok')


if __name__ == '__main__':
    main()
