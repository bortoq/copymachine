#!/usr/bin/env python3
"""Замеры счётчиков цены эталона vm2 на имеющихся сценариях (пункт 13.4.2).

Пишет docs/research/cost-baseline.md. Код эталона и space/ не меняется:
сценарии строятся теми же вызовами, что и в тестах (test_cost_counters.py,
test_guest_cli.py), и подаются в run(..., counters=True).
Запуск: python3 -B tools/research/cost_baseline.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/research/cost-baseline.md'
sys.path.insert(0, str(ROOT / 'space/vm2/tests'))
sys.path.insert(0, str(ROOT / 'space/copycode/src'))
from vm2_reference import run, put
from copycode.vm2.boundary import Format, Program, boot_stream, protocol, record

SIZE, SLOTS = 65520, 8
A = SIZE.bit_length(); Z = A - 1; I = 3 * A - 1; L = I * SLOTS


def raw(slots):
    """Таблица слотов в виде потока канала 1 (как в test_cost_counters.py)."""
    buf = bytearray(L // 8)
    for i, (n, d, s) in enumerate(slots):
        put(buf, i * I, Z, n); put(buf, i * I + Z, A, d); put(buf, i * I + Z + A, A, s)
    return bytes(buf)


def prompt_echo():
    p = Program(code_base=8192); at = p.allocate(b'go?'); p.step([(24, 65522, at)])
    p.step([(16, 1024, 65521)]); p.step([(16, 65522, 1024)])
    return boot_stream(p.finish(), SIZE, SLOTS) + b'ABtail', {}


def fstat_seek():
    ops, q, rsp = protocol(SIZE)
    p = Program(code_base=8192)
    stat = p.allocate(record(q, dict(op=3, chan=65521)))
    seek = p.allocate(record(q, dict(op=2, chan=65521, arg=0, off=0)))
    p.layer([(q[1], 65520, stat)]); p.layer([(rsp[1], 1024, 65520)])
    p.layer([(rsp[1], 65522, 1024)]); p.layer([(q[1], 65520, seek)])
    p.layer([(8, 1200, 65521)]); p.layer([(8, 65522, 1200)])
    return boot_stream(p.finish(), SIZE, SLOTS), dict(regular=True)


def offset_ok():
    p = Program(code_base=8192); at = p.allocate(b'offset-ok'); p.step([(72, 65522, at)])
    return boot_stream(p.finish(), SIZE, SLOTS), {}


SCENARIOS = [
    ('one-copy-and-stop (test_cost_counters 1)', 'копия 8 бит, затем обнуление слотов; останов по n=0',
     lambda: (raw([(8, 1100, 1000), (62, 0, 2000)]), {})),
    ('two-endless-slots-limit4 (test_cost_counters 2)', 'два вечных слота, limit=4',
     lambda: (raw([(8, 1100, 1000), (15, 2000, 3000)]), dict(limit=4))),
    ('stdout-write-and-nop (test_cost_counters 3)', 'запись 16 бит в канал 2, NOP, останов',
     lambda: (raw([(16, SIZE + 2, 1000), (0, 0, 0), (109, 0, 2000)]), {})),
    ('prompt-echo (test_guest_cli, live prompt)', 'Program: вывод "go?", чтение и вывод 2 байт канала 1',
     prompt_echo),
    ('fstat-seek (test_guest_cli, regular stdin)', 'Program: запросы FSTAT и SEEK через канал SYS, regular=True',
     fstat_seek),
    ('offset-ok (test_guest_cli, nonzero cursor)', 'Program: вывод 9 байт одной копией',
     offset_ok),
]

NOT_MEASURED = [
    ('test_guest.py (случайные и граничные случаи гест-компилятора)',
     'Поток строится `vm2guest.compiler.compile_guest` и исполняется настоящим эмулятором в сборке; эталон вызывается лишь для сверки вывода. Без сборки эмулятора и запуска компилятора сценарий не получить, а подача отдельных потоков изменила бы код теста.'),
    ('test_direct.py, direct_reference.py (прямое исполнение)',
     'Использует собственный эталон `direct_reference.run` с другим форматом ввода (source, manifest, mapping), а не `vm2_reference.run`; счётчиков в нём нет.'),
    ('test_direct_cli.py, test_core_cli.py, test_machine.py, test_schedule.py, check_local_schedules.py',
     'Запускают внешние исполняемые файлы (vm2, эмулятор) и сверяют их вывод; в `vm2_reference.run` не подаются.'),
    ('test_boundary.py, test_dynamic_trace.py, test_transport.py, test_checkpoint.py',
     'Проверяют библиотеку copycode и трассировку на эмуляторе; сценарии зависят от эмулятора и отчётных модулей, а не от эталона.'),
    ('examples/direct',
     'Примеры в формате прямого исполнителя (не поток для `vm2_reference.run`); требуют компилятора vm2compile.'),
    ('Сценарии с -t/-s/-p другими, чем 65520 бит и 8 слотов',
     'Не вошли: замеры сделаны только при размере по умолчанию.'),
]


def main():
    rows = []
    for name, note, build in SCENARIOS:
        stream, kw = build()
        r = run(stream, SIZE, SLOTS, counters=True, **kw)
        c = r['cost']
        assert c['layers'] == r['ticks']
        rows.append((name, note, c))
    out = ['# Базовые замеры цены в эталоне vm2', '',
           'Скрипт `tools/research/cost_baseline.py` прогоняет сценарии через `run(..., counters=True)` из '
           '`space/vm2/tests/vm2_reference.py`. Размер пространства 65520 бит, 8 слотов. Код эталона не менялся.', '',
           '## Определения счётчиков', '',
           'За одно исполнение:', '',
           '- `layers` — выполненные такты;',
           '- `copies` — выполненные инструкции с n>0, включая канальные;',
           '- `bits` — сумма n обычных (не канальных) копирований;',
           '- `channel_bits` — сумма фактически переданных бит канальных копирований.', '',
           '## Замеры', '',
           '| сценарий | layers | copies | bits | channel_bits |',
           '|---|---|---|---|---|']
    for name, note, c in rows:
        out.append(f"| {name} | {c['layers']} | {c['copies']} | {c['bits']} | {c['channel_bits']} |")
    out += ['', 'Описание сценариев:', '']
    out += [f'- {name}: {note}.' for name, note, _ in rows]
    out += ['', 'Замечания:', '',
            '- Каждый сценарий начинается с загрузки (такт 1: одно канальное копирование), поэтому '
            '`channel_bits` включает загрузку таблицы слотов (376 бит для сырых сценариев) или загрузочного образа.',
            '- В сценариях `Program` почти вся цена в `channel_bits` — это установка образа через канал 1, '
            'а не работа самой программы; для сравнения определений нужно вычитать общую загрузку.', '',
            '## Не измерено', '',
            '| сценарии | почему |', '|---|---|']
    out += [f'| {a} | {b} |' for a, b in NOT_MEASURED]
    OUT.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(OUT)


main()
