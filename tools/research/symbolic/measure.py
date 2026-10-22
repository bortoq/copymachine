#!/usr/bin/env python3
"""Замеры символьного исполнения против полного перебора (пункт 13.5.4).

Пишет docs/research/symbolic.md. Полный перебор через vm2_reference.run
делается, если входов не более FULL_MAX; иначе меряется выборка из SAMPLE
случайных входов (seed фиксирован), время на исполнение умножается на число
входов, результат помечается «оценка».
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
FULL_MAX = 1 << 10
SAMPLE = 400


def brute(prog):
    ranges = prog.input_ranges()
    total = 1
    for r in ranges:
        total *= r
    rnd = random.Random(1)
    if total <= FULL_MAX:
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


def measure(name, prog):
    bdd = BDD()
    t = time.perf_counter()
    m, outs = execute_symbolic(prog, bdd)
    ts = time.perf_counter() - t
    sizes = [bdd.size(f) for f in outs]
    total, n, per, full, est = brute(prog)
    return dict(name=name, bits=sum(r[2] for r in prog.reads), sizes=sizes,
                ts=ts, total=total, n=n, per=per, full=full, est=est)


def fmt_t(x):
    return f'{x:.3f} с' if x < 100 else f'{x:.0f} с ({x / 60:.1f} мин)'


def main():
    progs = [('A (таблица, 4 бит)', build_lookup_add(4)),
             ('B (цепочка, 4 бит)', build_ripple_add(4)),
             ('C (меньше, 8 бит)', build_less(8)),
             ('B8 (цепочка, 8 бит)', build_ripple_add(8)),
             ('B12 (цепочка, 12 бит)', build_ripple_add(12))]
    res = []
    for name, p in progs:
        r = measure(name, p)
        res.append(r)
        print(name, r['sizes'], r['ts'], r['full'], r['est'], flush=True)
    L = ['# Символьное исполнение: замеры', '', '## Замеры', '',
         'Узлы BDD — число внутренних узлов функции каждого выходного бита '
         '(младший первым). Время символьного исполнения — `execute_symbolic` '
         'с нуля. Перебор — `vm2_reference.run` на всех входах; '
         '«оценка» — время на одно исполнение по выборке, умноженное на число входов.', '',
         '| Программа | Бит входа | Узлы BDD по выходным битам | Всего узлов (сумма) | Символьно | Перебор: входов | Перебор: время | Способ |',
         '|---|---|---|---|---|---|---|---|']
    for r in res:
        how = (f'оценка (выборка {r["n"]}, {r["per"] * 1000:.2f} мс на исполнение)'
               if r['est'] else 'полный')
        L.append(f'| {r["name"]} | {r["bits"]} | {", ".join(map(str, r["sizes"]))} | '
                 f'{sum(r["sizes"])} | {fmt_t(r["ts"])} | {r["total"]} | {fmt_t(r["full"])} | {how} |')
    L += ['', 'Узлы разных выходов могут разделяться; сумма считает их повторно.', '',
          '## Ограничения', '',
          '- Каналы и SYS не поддерживаются: копия с концом за пределом памяти при n > 0 '
          'даёт `Unsupported`. Образ 13.5.2 берётся как уже загруженное состояние '
          '(`prog.image`), загрузка через канал не исполняется символьно.',
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
          f'- Перебор для входов свыше {FULL_MAX} заменён выборкой из {SAMPLE} случайных '
          'входов (seed 1) с экстраполяцией; такие значения помечены «оценка».',
          '- Время зависит от машины; узлы BDD зависят от порядка переменных '
          '(разряды слов чередуются a0,b0,a1,b1,...).', '']
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
