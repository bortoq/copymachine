# Базовые замеры цены в эталоне vm2

Скрипт `tools/research/cost_baseline.py` прогоняет сценарии через `run(..., counters=True)` из `space/vm2/tests/vm2_reference.py`. Размер пространства 65520 бит, 8 слотов. Код эталона не менялся.

## Определения счётчиков

За одно исполнение:

- `layers` — выполненные такты;
- `copies` — выполненные инструкции с n>0, включая канальные;
- `bits` — сумма n обычных (не канальных) копирований;
- `channel_bits` — сумма фактически переданных бит канальных копирований.

## Замеры

| сценарий | layers | copies | bits | channel_bits |
|---|---|---|---|---|
| one-copy-and-stop (test_cost_counters 1) | 2 | 3 | 70 | 376 |
| two-endless-slots-limit4 (test_cost_counters 2) | 4 | 7 | 69 | 376 |
| stdout-write-and-nop (test_cost_counters 3) | 2 | 3 | 109 | 392 |
| prompt-echo (test_guest_cli, live prompt) | 6 | 11 | 1284 | 33568 |
| fstat-seek (test_guest_cli, regular stdin) | 9 | 17 | 2412 | 33640 |
| offset-ok (test_guest_cli, nonzero cursor) | 4 | 7 | 532 | 33584 |

Описание сценариев:

- one-copy-and-stop (test_cost_counters 1): копия 8 бит, затем обнуление слотов; останов по n=0.
- two-endless-slots-limit4 (test_cost_counters 2): два вечных слота, limit=4.
- stdout-write-and-nop (test_cost_counters 3): запись 16 бит в канал 2, NOP, останов.
- prompt-echo (test_guest_cli, live prompt): Program: вывод "go?", чтение и вывод 2 байт канала 1.
- fstat-seek (test_guest_cli, regular stdin): Program: запросы FSTAT и SEEK через канал SYS, regular=True.
- offset-ok (test_guest_cli, nonzero cursor): Program: вывод 9 байт одной копией.

Замечания:

- Каждый сценарий начинается с загрузки (такт 1: одно канальное копирование), поэтому `channel_bits` включает загрузку таблицы слотов (376 бит для сырых сценариев) или загрузочного образа.
- В сценариях `Program` почти вся цена в `channel_bits` — это установка образа через канал 1, а не работа самой программы; для сравнения определений нужно вычитать общую загрузку.

## Не измерено

| сценарии | почему |
|---|---|
| test_guest.py (случайные и граничные случаи гест-компилятора) | Поток строится `vm2guest.compiler.compile_guest` и исполняется настоящим эмулятором в сборке; эталон вызывается лишь для сверки вывода. Без сборки эмулятора и запуска компилятора сценарий не получить, а подача отдельных потоков изменила бы код теста. |
| test_direct.py, direct_reference.py (прямое исполнение) | Использует собственный эталон `direct_reference.run` с другим форматом ввода (source, manifest, mapping), а не `vm2_reference.run`; счётчиков в нём нет. |
| test_direct_cli.py, test_core_cli.py, test_machine.py, test_schedule.py, check_local_schedules.py | Запускают внешние исполняемые файлы (vm2, эмулятор) и сверяют их вывод; в `vm2_reference.run` не подаются. |
| test_boundary.py, test_dynamic_trace.py, test_transport.py, test_checkpoint.py | Проверяют библиотеку copycode и трассировку на эмуляторе; сценарии зависят от эмулятора и отчётных модулей, а не от эталона. |
| examples/direct | Примеры в формате прямого исполнителя (не поток для `vm2_reference.run`); требуют компилятора vm2compile. |
| Сценарии с -t/-s/-p другими, чем 65520 бит и 8 слотов | Не вошли: замеры сделаны только при размере по умолчанию. |
