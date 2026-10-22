#!/usr/bin/env python3
"""Замеры символьного исполнения против полного перебора (пункт 13.5.4).

Без флагов: считает и печатает только детерминированные столбцы (узлы BDD,
варианты поля, пик узлов), сверяет их с EXPECT и с числом строк таблиц;
перебор не запускает и файлов не пишет. С флагом --write: добавляет перебор и
переписывает docs/research/symbolic.md. Полный перебор через
vm2_reference.run делается, если входов не более FULL_MAX и программа не из
ESTIMATE; иначе меряется выборка из SAMPLE случайных входов (seed фиксирован),
время на исполнение умножается на число входов, результат помечается «оценка».
"""
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bdd import BDD
from programs import build_lookup_add, build_ripple_add, build_less, execute
from symexec import execute_symbolic

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'docs', 'research', 'symbolic.md')
TABLES = os.path.join(ROOT, 'docs', 'research', 'tables')
FULL_MAX = 1 << 16
SAMPLE = 400
ESTIMATE = ('B8', 'B12')      # полный перебор слишком долог (B8: ~14 мин)
# Детерминированные значения: (узлы по выходным битам, вариантов поля, пик узлов)
EXPECT = {
    'A': ([3, 6, 9, 12, 11], 256, 2115),
    'B': ([3, 6, 9, 12, 11], 28, 268),
    'C': ([23], 768, 10342),
    'B8': ([3, 6, 9, 12, 15, 18, 21, 24, 23], 60, 1242),
    'B12': ([3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 35], 92, 2936),
}


def brute(key, prog):
    ranges = prog.input_ranges()
    total = 1
    for r in ranges:
        total *= r
    rnd = random.Random(1)
    if total <= FULL_MAX and key not in ESTIMATE:
        import itertools
        inputs = list(itertools.product(*[range(r) for r in ranges]))
        est = False
    else:
        inputs = [tuple(rnd.randrange(r) for r in ranges) for _ in range(SAMPLE)]
        est = True
    t = time.perf_counter()
    for v in inputs:
        execute(prog, *v)
    dt = time.perf_counter() - t
    per = dt / len(inputs)
    return total, len(inputs), per, per * total, est


def measure(key, name, prog, write):
    bdd = BDD()
    t = time.perf_counter()
    m, outs = execute_symbolic(prog, bdd)
    ts = time.perf_counter() - t
    sizes = [bdd.size(f) for f in outs]
    r = dict(key=key, name=name, bits=sum(r[2] for r in prog.reads), sizes=sizes,
             ts=ts, variants=m.cost['variants'], peak=len(bdd.nodes))
    total = 1
    for x in prog.input_ranges():
        total *= x
    r['total'] = total
    if write:
        r.update(zip(('total', 'n', 'per', 'full', 'est'), brute(key, prog)))
    return r


def check_tables(res):
    """Число строк таблиц A, B, C (.tsv или .tsv.gz) равно числу входов."""
    from programs import read_table_text
    for r in res:
        if r['key'] in 'ABC':
            rows = [l for l in read_table_text(TABLES, r['key']).splitlines()
                    if l and l[0] != '#' and not l.startswith('a\t')]
            assert len(rows) == r['total'], (r['key'], len(rows), r['total'])


def fmt_t(x):
    return f'{x:.3f} с' if x < 100 else f'{x:.0f} с ({x / 60:.1f} мин)'


def main():
    write = '--write' in sys.argv[1:]
    progs = [('A', 'A (таблица, 4 бит)', build_lookup_add(4)),
             ('B', 'B (цепочка, 4 бит)', build_ripple_add(4)),
             ('C', 'C (меньше, 8 бит)', build_less(8)),
             ('B8', 'B8 (цепочка, 8 бит)', build_ripple_add(8)),
             ('B12', 'B12 (цепочка, 12 бит)', build_ripple_add(12))]
    res = []
    for key, name, p in progs:
        r = measure(key, name, p, write)
        res.append(r)
        print(key, r['sizes'], 'вариантов поля', r['variants'], 'пик узлов', r['peak'],
              f'{r["ts"]:.3f} с', *((fmt_t(r['full']), 'оценка' if r['est'] else 'полный') if write else ()),
              flush=True)
    for r in res:
        got = (r['sizes'], r['variants'], r['peak'])
        assert EXPECT.get(r['key']) == got, (r['key'], got, EXPECT.get(r['key']))
    check_tables(res)
    if not write:
        print('детерминированные столбцы совпали; файлы не записаны (отчёт: --write)')
        return
    L = ['# Символьное исполнение: замеры', '', '## Замеры', '',
         'Узлы BDD — число внутренних узлов функции каждого выходного бита '
         '(младший первым). «вариантов поля» — сумма по инструкциям числа различных '
         'троек (n,dst,src) за всё исполнение; «пик узлов» — `len(bdd.nodes)` в конце '
         '(включая два терминала). Время символьного исполнения — `execute_symbolic` '
         'с нуля. Перебор — `vm2_reference.run` на всех входах; '
         '«оценка» — время на одно исполнение по выборке, умноженное на число входов '
         '(только B8 и B12); «полный» — все входы перебраны.', '',
         '| Программа | Описание | Бит входа | Узлы BDD по выходным битам | Всего узлов (сумма) | Вариантов поля | Пик узлов | Символьно | Перебор: входов | Перебор: время | Способ |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in res:
        how = (f'оценка (выборка {r["n"]}, {r["per"] * 1000:.2f} мс на исполнение)'
               if r['est'] else 'полный')
        L.append(f'| {r["key"]} | {r["name"]} | {r["bits"]} | {", ".join(map(str, r["sizes"]))} | '
                 f'{sum(r["sizes"])} | {r["variants"]} | {r["peak"]} | {fmt_t(r["ts"])} | '
                 f'{r["total"]} | {fmt_t(r["full"])} | {how} |')
    L += ['', 'Узлы разных выходов могут разделяться; сумма считает их повторно.', '',
          '## Ограничения', '',
          '- Каналы и SYS не поддерживаются: копия с концом за пределом памяти при n > 0 '
          'даёт `Unsupported`. Образ 13.5.2 берётся как уже загруженное состояние '
          '(`prog.image`), загрузка через канал не исполняется символьно.',
          '- `layers` символьного исполнителя (3 у A) считает только рабочие такты '
          'программы: загрузка образа через канал и останов в него не входят. '
          '`layers` эталона (6 у A, `P.execute(..., counters=True)`) включает загрузку и останов, '
          'поэтому числа 3 и 6 для одной программы не противоречат друг другу.',
          '- Останов, зависящий от переменных, не поддерживается (`Unsupported`); '
          'конец исполнения — такт, где все n равны 0, лимит 1000 тактов.',
          '- Предел 2^12 относится к числу различных троек (n,dst,src) после разложения '
          'по переменным, а не к 2^(числу переменных). Поле инструкции, зависящее от '
          'многих переменных, но принимающее мало значений, укладывается в предел; '
          'превышение даёт `TooLarge`.',
          '- Ширины: генераторы A, B, C параметризуются шириной (A — `build_lookup_add(w)`, '
          'B — `build_ripple_add(w)`, C — `build_less(w)`); замеры сделаны для A и B на 4 бита, '
          'C на 8 бит, B на 8 и 12 бит. Таблица A растёт как 2^(2w) строк, поэтому '
          'A на 8 и 12 бит не замерялась.',
          f'- Полный перебор — для программ с числом входов не более {FULL_MAX} '
          f'(C: 65536 входов). Для {" и ".join(ESTIMATE)} перебор заменён выборкой из {SAMPLE} '
          'случайных входов (seed 1) с экстраполяцией; такие значения помечены «оценка».',
          '- Время зависит от машины; узлы BDD, варианты поля и пик узлов от машины не зависят, '
          'но зависят от порядка переменных (разряды слов чередуются a0,b0,a1,b1,...).', '']
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
