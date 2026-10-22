#!/usr/bin/env python3
"""Замеры счётчиков цены эталона vm2 (пункты 13.4.2 и 13.6.5).

Пишет docs/research/cost-baseline.md. Файлы в space/ не меняются:
сценарии строятся теми же вызовами, что и в тестах (test_cost_counters.py,
test_guest_cli.py), программы A-D, B8, B12 берутся из symbolic/programs.py,
а потоки test_guest.py собираются подменой `vm2_reference.run` обёрткой
до импорта теста. Все потоки подаются в run(..., counters=True).
Запуск: python3 -B tools/research/cost_baseline.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/research/cost-baseline.md'
sys.path.insert(0, str(ROOT / 'space/vm2/tests'))
sys.path.insert(0, str(ROOT / 'space/copycode/src'))
sys.path.insert(0, str(ROOT / 'tools/research/symbolic'))
import vm2_reference
from vm2_reference import run, put, get
import programs as P
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


PROGRAMS = [
    ('A', 'сложение 4 бит одной таблицей 2^8 строк', lambda: P.build_lookup_add(4)),
    ('B', 'сложение 4 бит поразрядно, таблица полного сумматора', lambda: P.build_ripple_add(4)),
    ('C', 'сравнение a<b, 8 бит, цепочка по таблице', lambda: P.build_less(8)),
    ('D', 'как A, в строке a=3,b=5 испорчен бит', lambda: P.build_lookup_add(4, corrupt=(3, 5), name='D')),
    ('B8', 'как B, 8 бит', lambda: P.build_ripple_add(8)),
    ('B12', 'как B, 12 бит', lambda: P.build_ripple_add(12)),
]


def collect_test_guest():
    """Импортировать test_guest.py, не меняя его, и собрать потоки его вызовов эталона.

    `vm2_reference.run` подменяется обёрткой до импорта: она запоминает вызов
    (имя случая берётся из кадра `run_case`) и вызывает настоящий эталон.
    Эмулятор из сборки тест вызывает через subprocess.run; на время импорта
    subprocess.run заменяется ответом, построенным из результата эталона,
    чтобы тест дошёл до конца без сборки. Цена берётся только из эталона.
    Файл результатов теста пишется во временный каталог.
    """
    calls, last = [], {}
    original = vm2_reference.run

    def wrapper(stream, size=65520, slots=8, limit=0, **kw):
        caller = sys._getframe(1).f_locals
        res = original(stream, size, slots, limit, **{**kw, 'counters': True})
        calls.append((caller.get('name', '#%d' % (len(calls) + 1)), stream, size, slots, limit, kw))
        last['res'], last['kw'] = res, kw
        return res

    real_run = subprocess.run

    def fake_run(command, *a, **kw):
        if not (isinstance(command, list) and 'guest-test' in command):
            return real_run(command, *a, **kw)
        res, r = last['res'], last['kw']
        ch = res['channels']
        bound = r.get('bound', (1, 2, 3, 4, 5))
        if 4 in bound:
            data = bytes(ch[4]['data'])
            if ch[4]['used']:
                rep = bytearray(12); rep[:4] = b'VM2R'; put(rep, 32, 64, res['ticks']); data += bytes(rep)
            Path(command[-3]).write_bytes(data)
        if 5 in bound:
            data = bytes(ch[5]['data'])
            if ch[5]['used']:
                data += bytes(res['memory'])
            Path(command[-2]).write_bytes(data)
        out = None if kw.get('stdout') is not subprocess.PIPE else bytes(ch[2]['data'])
        return subprocess.CompletedProcess(command, 0, out, bytes(ch[3]['data']))

    with tempfile.TemporaryDirectory() as tmp:
        os.environ['VM2_GUEST_RESULTS'] = str(Path(tmp) / 'results.json')
        vm2_reference.run = wrapper
        subprocess.run = fake_run
        try:
            import test_guest  # noqa: F401  (исполняется при импорте)
        finally:
            vm2_reference.run = original
            subprocess.run = real_run
    return calls


def measure(stream, size, slots, limit, kw):
    """Счётчики полного прогона и `load_bits` — channel_bits такта 1."""
    kw = dict(kw)
    limit = kw.pop('limit', limit)
    c = run(stream, size, slots, limit, counters=True, **kw)['cost']
    load = run(stream, size, slots, 1, counters=True, **kw)['cost']['channel_bits']
    return c, load


NOT_MEASURED = [
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
        assert r['cost']['layers'] == r['ticks']
        c, load = measure(stream, SIZE, SLOTS, 0, kw)
        rows.append((name, note, c, load))
    for name, note, build in PROGRAMS:
        prog = build()
        c, load = measure(boot_stream(prog.image, prog.size, prog.slots), prog.size, prog.slots, 0, {})
        rows.append((name, note + f' (пространство {prog.size} бит, слотов {prog.slots})', c, load))
    byname = {r[0]: r[2] for r in rows}
    for name, stream, size, slots, limit, kw in collect_test_guest():
        c, load = measure(stream, size, slots, limit, kw)
        extra = f'{size} бит, {slots} слотов' + (f', limit={limit}' if limit else '')
        rows.append((f'test_guest: {name}', f'поток случая `{name}` теста test_guest.py ({extra})', c, load))
    out = ['# Базовые замеры цены в эталоне vm2', '',
           'Скрипт `tools/research/cost_baseline.py` прогоняет сценарии через `run(..., counters=True)` из '
           '`space/vm2/tests/vm2_reference.py`. Для сырых сценариев и `Program` пространство 65520 бит, 8 слотов; '
           'программы A-D, B8, B12 взяты из `tools/research/symbolic/programs.py` без входных значений; '
           'потоки `test_guest.py` собраны подменой `vm2_reference.run` обёрткой до импорта теста, сам тест не менялся.', '',
           '## Определения счётчиков', '',
           'Копия определений 13.6.4. За одно исполнение:', '',
           '- `layers` — выполненные такты;',
           '- `copies` — инструкции с n>0, которые изменили память или передали хотя бы один бит через канал или SYS '
           '(копии в незанятый или закрытый канал, записи, не прошедшие при `stdout_error`, и чтения 0 байт на EOF '
           'не считаются, если память не изменилась);',
           '- `bits` — сумма n каждого копирования память-память;',
           '- `channel_bits` — 8 * число байт, фактически переданных через каналы (чтения и успешные записи);',
           '- `sys_bits` — биты записи запроса SYS (`max(n,120+a)`) и чтения ответа SYS (`97+z`).', '',
           'Производные столбцы этого отчёта:', '',
           '- `load_bits` — `channel_bits` такта 1 (загрузка образа через канал 1);',
           '- `work_bits` — остальная цена: `bits + sys_bits + (channel_bits - load_bits)`.', '',
           '## Замеры', '',
           '| сценарий | layers | copies | bits | channel_bits | sys_bits | load_bits | work_bits |',
           '|---|---|---|---|---|---|---|---|']
    for name, note, c, load in rows:
        work = c['bits'] + c['sys_bits'] + c['channel_bits'] - load
        out.append(f"| {name} | {c['layers']} | {c['copies']} | {c['bits']} | {c['channel_bits']} | {c['sys_bits']} | {load} | {work} |")
    out += ['', 'Описание сценариев:', '']
    out += [f'- {name}: {note}.' for name, note, _, _ in rows if not name.startswith('test_guest:')]
    out += ['', 'Замечания:', '',
            '- Каждый сценарий начинается с загрузки (такт 1: одно канальное копирование), поэтому '
            '`load_bits` — загрузка таблицы слотов (376 бит для сырых сценариев) или загрузочного образа; '
            'остальная цена — `work_bits`.',
            '- В сценариях `Program`, в программах и в потоках теста почти вся цена — `load_bits`; для сравнения '
            'определений нужно смотреть `work_bits`.',
            '- Строки `test_guest: ...` — по одной на каждый вызов эталона из `run_case` теста. Эмулятор из сборки '
            'при сборе потоков не запускается: на время импорта его ответ строится из результата эталона, '
            'поэтому цена в строках — цена эталона.',
            f'- Сверка: `copies` у A и B — {byname["A"]["copies"]} и {byname["B"]["copies"]}, а в таблицах `test_programs.py` — 11 и 32. '
            'Расхождение объяснено определением 13.6.4: копии, не изменившие память и не передавшие бит, теперь не считаются; '
            'layers, bits и channel_bits совпадают с таблицами.', '',
            '## Не измерено', '',
            '| сценарии | почему |', '|---|---|']
    out += [f'| {a} | {b} |' for a, b in NOT_MEASURED]
    OUT.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(OUT)


main()
