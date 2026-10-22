# Базовые замеры цены в эталоне vm2

Скрипт `tools/research/cost_baseline.py` прогоняет сценарии через `run(..., counters=True)` из `space/vm2/tests/vm2_reference.py`. Для сырых сценариев и `Program` пространство 65520 бит, 8 слотов; программы A-D, B8, B12 взяты из `tools/research/symbolic/programs.py` без входных значений; потоки `test_guest.py` собраны подменой `vm2_reference.run` обёрткой до импорта теста, сам тест не менялся.

## Определения счётчиков

Копия определений 13.6.4. За одно исполнение:

- `layers` — выполненные такты;
- `copies` — инструкции с n>0, которые изменили память или передали хотя бы один бит через канал или SYS (копии в незанятый или закрытый канал, записи, не прошедшие при `stdout_error`, и чтения 0 байт на EOF не считаются, если память не изменилась);
- `bits` — сумма n каждого копирования память-память;
- `channel_bits` — 8 * число байт, фактически переданных через каналы (чтения и успешные записи);
- `sys_bits` — биты записи запроса SYS (`max(n,120+a)`) и чтения ответа SYS (`97+z`).

Производные столбцы этого отчёта:

- `load_bits` — `channel_bits` такта 1 (загрузка образа через канал 1);
- `work_bits` — остальная цена: `bits + sys_bits + (channel_bits - load_bits)`.

## Замеры

| сценарий | layers | copies | bits | channel_bits | sys_bits | load_bits | work_bits |
|---|---|---|---|---|---|---|---|
| one-copy-and-stop (test_cost_counters 1) | 2 | 2 | 70 | 376 | 0 | 376 | 70 |
| two-endless-slots-limit4 (test_cost_counters 2) | 4 | 1 | 69 | 376 | 0 | 376 | 69 |
| stdout-write-and-nop (test_cost_counters 3) | 2 | 3 | 109 | 392 | 0 | 376 | 125 |
| prompt-echo (test_guest_cli, live prompt) | 6 | 11 | 1284 | 33568 | 0 | 376 | 34476 |
| fstat-seek (test_guest_cli, regular stdin) | 9 | 17 | 2412 | 33640 | 384 | 376 | 36060 |
| offset-ok (test_guest_cli, nonzero cursor) | 4 | 7 | 532 | 33584 | 0 | 376 | 33740 |
| A | 6 | 8 | 1051 | 4400 | 0 | 304 | 5147 |
| B | 15 | 17 | 3793 | 4400 | 0 | 304 | 7889 |
| C | 9 | 11 | 1969 | 4400 | 0 | 304 | 6065 |
| D | 6 | 8 | 1051 | 4400 | 0 | 304 | 5147 |
| B8 | 27 | 29 | 8633 | 16736 | 0 | 352 | 25017 |
| B12 | 39 | 41 | 12877 | 16736 | 0 | 352 | 29261 |
| test_guest: seed-limit-1 | 1 | 1 | 0 | 376 | 0 | 376 | 0 |
| test_guest: seed-limit-2 | 2 | 4 | 156 | 33136 | 0 | 376 | 32916 |
| test_guest: seed-limit-3 | 3 | 5 | 156 | 33512 | 0 | 376 | 33292 |
| test_guest: seed-limit-0 | 5 | 8 | 908 | 33520 | 0 | 376 | 34052 |
| test_guest: ordinary-binary-unaligned | 6 | 10 | 1297 | 33528 | 0 | 376 | 34449 |
| test_guest: destroy-current-processor-after-fetch | 4 | 9 | 320 | 33520 | 0 | 376 | 33464 |
| test_guest: random-layer-0 | 10 | 30 | 2939 | 66272 | 0 | 376 | 68835 |
| test_guest: random-layer-1 | 10 | 30 | 2816 | 66272 | 0 | 376 | 68712 |
| test_guest: random-layer-2 | 10 | 30 | 2873 | 66272 | 0 | 376 | 68769 |
| test_guest: random-layer-3 | 10 | 30 | 2954 | 66272 | 0 | 376 | 68850 |
| test_guest: random-layer-4 | 10 | 30 | 2821 | 66272 | 0 | 376 | 68717 |
| test_guest: random-layer-5 | 10 | 29 | 2825 | 66272 | 0 | 376 | 68721 |
| test_guest: random-layer-6 | 10 | 29 | 2929 | 66272 | 0 | 376 | 68825 |
| test_guest: random-layer-7 | 10 | 29 | 2944 | 66272 | 0 | 376 | 68840 |
| test_guest: concurrent-old-sys-answer | 8 | 15 | 2036 | 33736 | 360 | 376 | 35756 |
| test_guest: close-sys-preserves-old-in-closing-tick | 8 | 14 | 2036 | 33624 | 384 | 376 | 35668 |
| test_guest: short-read-fstat-eof | 8 | 15 | 2036 | 33680 | 248 | 376 | 35588 |
| test_guest: sys-op-0 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: sys-op-1 | 7 | 11 | 1660 | 33512 | 248 | 376 | 35044 |
| test_guest: sys-op-2 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: sys-op-3 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: sys-op-4 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: sys-op-99 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-65520 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-65521 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-65522 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-65523 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-65524 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-65525 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-65526 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-65535 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: fstat-map-1234 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: unbound-data-ignored | 6 | 8 | 1284 | 33512 | 0 | 376 | 34420 |
| test_guest: close-data-channel | 9 | 15 | 2412 | 33624 | 384 | 376 | 36044 |
| test_guest: exec-exit | 7 | 12 | 1660 | 33624 | 296 | 376 | 35204 |
| test_guest: exec-output | 7 | 12 | 1660 | 33624 | 336 | 376 | 35244 |
| test_guest: exec-short | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: exec-empty | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: regular-stdin-size-and-seek-set | 10 | 18 | 2788 | 33640 | 384 | 376 | 36436 |
| test_guest: seek-before-guest-start-0 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: seek-before-guest-start-1 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: seek-before-guest-start-2 | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: seek-cur-retains-logical-cursor | 8 | 14 | 2036 | 33560 | 136 | 376 | 35356 |
| test_guest: seek-end-retains-guest-origin | 7 | 12 | 1660 | 33544 | 136 | 376 | 34964 |
| test_guest: layout-30000-9 | 7 | 12 | 1084 | 30808 | 0 | 400 | 31492 |
| test_guest: layout-65519-8 | 5 | 8 | 908 | 33520 | 0 | 376 | 34052 |
| test_guest: layout-1048560-8 | 5 | 8 | 1140 | 525232 | 0 | 472 | 525900 |
| test_guest: single-slot-1024 | 2 | 2 | 0 | 40 | 0 | 32 | 8 |
| test_guest: single-slot-1041 | 2 | 2 | 0 | 40 | 0 | 32 | 8 |
| test_guest: memory-end-equals-S | 6 | 10 | 1293 | 33520 | 0 | 376 | 34437 |
| test_guest: long-copy-no-guest-source-snapshot | 10 | 6 | 210156 | 33512 | 0 | 376 | 243292 |
| test_guest: optional-output-and-stat | 8 | 15 | 2036 | 33640 | 248 | 376 | 35548 |
| test_guest: optional-absent-(1, 2, 3, 5) | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: optional-absent-(1, 2, 3, 4) | 7 | 12 | 1660 | 33624 | 248 | 376 | 35156 |
| test_guest: stdout-error-state | 8 | 13 | 2036 | 33624 | 248 | 376 | 35532 |
| test_guest: multiple-old-answer-reads | 7 | 15 | 1660 | 33736 | 496 | 376 | 35516 |
| test_guest: sys-width-30000 | 9 | 16 | 1700 | 30816 | 246 | 352 | 32410 |
| test_guest: sys-width-1048560 | 7 | 12 | 2084 | 525344 | 256 | 472 | 527212 |
| test_guest: wide-77-bit-guest | 5 | 8 | 1488 | 525528 | 0 | 616 | 526400 |
| test_guest: checkpoint-at-virtual-boundary | 5 | 8 | 908 | 33520 | 0 | 376 | 34052 |
| test_guest: checkpoint-continuation | 4 | 7 | 532 | 33520 | 0 | 376 | 33676 |
| test_guest: batch64-1-baseline | 8 | 11 | 15248 | 38776 | 0 | 3008 | 51016 |
| test_guest: batch64-1-schedule | 8 | 11 | 15248 | 38776 | 0 | 3008 | 51016 |
| test_guest: batch64-1-optimize | 8 | 11 | 15248 | 38776 | 0 | 3008 | 51016 |
| test_guest: batch64-1-parallel | 8 | 11 | 15248 | 38776 | 0 | 3008 | 51016 |
| test_guest: batch64-63-baseline | 8 | 73 | 18472 | 38776 | 0 | 3008 | 54240 |
| test_guest: batch64-63-schedule | 8 | 73 | 18472 | 38776 | 0 | 3008 | 54240 |
| test_guest: batch64-63-optimize | 8 | 73 | 18472 | 38776 | 0 | 3008 | 54240 |
| test_guest: batch64-63-parallel | 8 | 73 | 18472 | 38776 | 0 | 3008 | 54240 |
| test_guest: production-emulator | 5 | 8 | 908 | 33520 | 0 | 376 | 34052 |

Описание сценариев:

- one-copy-and-stop (test_cost_counters 1): копия 8 бит, затем обнуление слотов; останов по n=0.
- two-endless-slots-limit4 (test_cost_counters 2): два вечных слота, limit=4.
- stdout-write-and-nop (test_cost_counters 3): запись 16 бит в канал 2, NOP, останов.
- prompt-echo (test_guest_cli, live prompt): Program: вывод "go?", чтение и вывод 2 байт канала 1.
- fstat-seek (test_guest_cli, regular stdin): Program: запросы FSTAT и SEEK через канал SYS, regular=True.
- offset-ok (test_guest_cli, nonzero cursor): Program: вывод 9 байт одной копией.
- A: сложение 4 бит одной таблицей 2^8 строк (пространство 4096 бит, слотов 8).
- B: сложение 4 бит поразрядно, таблица полного сумматора (пространство 4096 бит, слотов 8).
- C: сравнение a<b, 8 бит, цепочка по таблице (пространство 4096 бит, слотов 8).
- D: как A, в строке a=3,b=5 испорчен бит (пространство 4096 бит, слотов 8).
- B8: как B, 8 бит (пространство 16384 бит, слотов 8).
- B12: как B, 12 бит (пространство 16384 бит, слотов 8).

Замечания:

- Каждый сценарий начинается с загрузки (такт 1: одно канальное копирование), поэтому `load_bits` — загрузка таблицы слотов (376 бит для сырых сценариев) или загрузочного образа; остальная цена — `work_bits`.
- В сценариях `Program`, в программах и в потоках теста почти вся цена — `load_bits`; для сравнения определений нужно смотреть `work_bits`.
- Строки `test_guest: ...` — по одной на каждый вызов эталона из `run_case` теста. Эмулятор из сборки при сборе потоков не запускается: на время импорта его ответ строится из результата эталона, поэтому цена в строках — цена эталона.
- Сверка: `copies` у A и B — 8 и 17, а в таблицах `test_programs.py` — 11 и 32. Расхождение объяснено определением 13.6.4: копии, не изменившие память и не передавшие бит, теперь не считаются; layers, bits и channel_bits совпадают с таблицами.

## Не измерено

| сценарии | почему |
|---|---|
| test_direct.py, direct_reference.py (прямое исполнение) | Использует собственный эталон `direct_reference.run` с другим форматом ввода (source, manifest, mapping), а не `vm2_reference.run`; счётчиков в нём нет. |
| test_direct_cli.py, test_core_cli.py, test_machine.py, test_schedule.py, check_local_schedules.py | Запускают внешние исполняемые файлы (vm2, эмулятор) и сверяют их вывод; в `vm2_reference.run` не подаются. |
| test_boundary.py, test_dynamic_trace.py, test_transport.py, test_checkpoint.py | Проверяют библиотеку copycode и трассировку на эмуляторе; сценарии зависят от эмулятора и отчётных модулей, а не от эталона. |
| examples/direct | Примеры в формате прямого исполнителя (не поток для `vm2_reference.run`); требуют компилятора vm2compile. |
| Сценарии с -t/-s/-p другими, чем 65520 бит и 8 слотов | Не вошли: замеры сделаны только при размере по умолчанию. |
