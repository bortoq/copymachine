# Использование SYS и каналов в гестовом коде (факты)

Источники: `emulator/src/proto.def`, `emulator/doc/emulator-contract.md` (разделы «Memory operations, channels and NOP», «SYS records»), поиск по `space/` (Python, C, .fth). Таблица порождена `tools/research/sys_usage.py`.

Факты о протоколе:

- Операции SYS: NONE=0, CLOSE=1, SEEK=2, FSTAT=3, IOCTL=4 (ответ ENOTTY), EXEC=5. Запрос `op:8 chan:A flags:16 arg:32 off:64`, ответ `op:8 status:8 flags:16 size:64 moved:A eof:1`.
- Каналы: S - SYS (запрос записью, ответ чтением), S+1 stdin (чтение), S+2 stdout (запись), S+3 stderr/debug (запись), S+4 fd 3/status (запись), S+5 fd 4/snapshot (запись).
- Обозначения операций в таблице: ЧТ и ЗП - копирование из канала данных и в канал данных; ОТВ - чтение ответа из канала S; CLOSE, SEEK, FSTAT, IOCTL, EXEC - запись запроса с этим кодом в канал S. Строки с пометкой «тест-программа» - гест-программы, собранные внутри самих тестов.
- «Место» - одна строка таблицы: непрерывный фрагмент файла (или набор строк одной функции), где гестовый код или его генератор формирует запрос SYS либо копирует из/в канал S..S+5. Хостовые пути (Popen, os.fstat, seek на файлах хоста) не учитываются, кроме явно помеченных.

Границы поиска: пути `space/vm2/tools/*.py` и `space/vm2/tests/test_{boundary,checkpoint,dynamic_trace,machine,schedule,transport}.py` - тонкие обёртки над кодом и тестами copycode (`COPYCODE_COMPAT`), отдельных мест не добавляют; `space/forth/third_party/` (исходники pForth), `space/vm2/tests/reference/` и `test_sys.c`, `test_engine.c` проверяют сам эмулятор на хосте на C и гестовым кодом не являются.

## Таблица

Пути относительно корня репозитория; тесты - относительно `space/`.

| № | Компонент | Файл:строка | Операция | Каналы | Назначение | Тесты |
|---|---|---|---|---|---|---|
| 1 | vm2 | `space/vm2/vm2guest/compiler.py:86-89` | SEEK | S, S+1 | начальная установка логического смещения stdin (запрос SEEK на канал stdin хоста) | vm2/tests/test_guest_cli.py (смещение 4); vm2/tests/test_guest.py:116-128 |
| 2 | vm2 | `space/vm2/vm2guest/compiler.py:93-95` | FSTAT, ОТВ | S, S+1 | FSTAT stdin при старте: размер файла и признак seekable | vm2/tests/test_guest.py:116-120; vm2/tests/test_guest_cli.py:32-58 |
| 3 | vm2 | `space/vm2/vm2guest/compiler.py:157-167` | ЗП | S..S+5 | разбор копирования гест-инструкции: приёмник-канал; S ведёт к виртуальному запросу, остальные к записи данных | vm2/tests/test_guest.py:23-56,146-150; vm2/tests/test_direct.py:59-62 |
| 4 | vm2 | `space/vm2/vm2guest/compiler.py:168-173` | ЧТ | S..S+5 | то же для источника-канала: S ведёт к виртуальному ответу, остальные к чтению данных | vm2/tests/test_guest.py:23-56,146-150; vm2/tests/test_direct.py:59-62 |
| 5 | vm2 | `space/vm2/vm2guest/compiler.py:174-180` | FSTAT, ОТВ | S, S+1 | после каждого чтения stdin: FSTAT для приращения логического курсора | vm2/tests/test_guest.py:116-128; vm2/tests/test_guest_cli.py:32-58 |
| 6 | vm2 | `space/vm2/vm2guest/compiler.py:182-183` | ОТВ | S | виртуальный ответ SYS: ответ, зафиксированный до такта | vm2/tests/test_guest.py:94-110,151-152 |
| 7 | vm2 | `space/vm2/vm2guest/compiler.py:184-189` | CLOSE | S | виртуальный запрос SYS; CLOSE канала S гасит только виртуальный SYS, но не закрывает хостовый | vm2/tests/test_guest.py:98-100 |
| 8 | vm2 | `space/vm2/vm2guest/compiler.py:190-206,234-238` | SEEK | S, S+1 | перенос номера канала в хостовый; SEEK stdin пересчитывается в абсолютный SEEK_SET с учётом префикса загрузчика; курсор обновляется по ответу | vm2/tests/test_guest.py:116-128; vm2/tests/test_guest_cli.py:32-58 |
| 9 | vm2 | `space/vm2/vm2guest/compiler.py:207-219` | EXEC | S | EXEC: поле chan обнуляется, команда копируется вслед за записью, проверка длины | vm2/tests/test_guest.py:111-115 |
| 10 | vm2 | `space/vm2/vm2guest/compiler.py:220-232` | FSTAT, ОТВ | S, S+1 | пересылка запроса хосту, чтение ответа; для FSTAT stdin вычитается префикс загрузчика | vm2/tests/test_guest.py:101-107,116-120 |
| 11 | vm2 | `space/vm2/vm2guest/compiler.py:252,257` | ЗП | S+5, S+4 | по остановке: снимок памяти гестa в S+5, отчёт VM2R в S+4 | vm2/tests/test_guest.py:46-53,162 |
| 12 | vm2 | `space/vm2/vm2compile/compiler.py:13,55-57` | ЧТ, ЗП | S..S+5 | таблица имён каналов sys/stdin/stdout/debug/status/snapshot и перевод имени в позицию S+i | vm2/tests/test_direct.py:59-62; vm2/tests/test_direct_cli.py:39,70 |
| 13 | vm2 | `space/vm2/vm2compile/compiler.py:169-171,275-287` | ЧТ, ЗП, ОТВ | S..S+5 | ширина записи SYS (120+A запрос, 97+A ответ); длина передачи по каналу округляется до байта, у S берётся длина записи | vm2/tests/test_direct.py:51-62,101-109,132-149 |
| 14 | vm2 | `space/vm2/vm2compile/compiler.py:347,386` | ЗП | S+5 | снимок слоя продолжения и памяти в S+5 при checkpoint | vm2/tests/test_direct.py:151-160; rv32i/tests/test_monitor.py |
| 15 | vm2 | `space/vm2/vm2compile/sdk.py:14-31` | любой код (API) | S | интерфейс построения записей запроса/ответа SYS и копирований request/response; stdin_position для SEEK | vm2/tests/test_direct.py:132-149; vm2/tests/test_direct_cli.py |
| 16 | vm2 | `space/vm2/vm2compile/model.py:17,28; vm2compile/legacy.py:8,40,73` | ЧТ, ЗП | S..S+5 | типы Channel и SysWidth в промежуточном представлении; копирования с каналом помечаются «непрозрачными» для планировщика | vm2/tests/test_direct.py; rv32i/tests/test_schedule.py |
| 17 | vm2 | `space/vm2/tests/test_guest.py:91-150 (тест-программы)` | NONE, CLOSE, SEEK, FSTAT, IOCTL, EXEC, ЧТ, ЗП, ОТВ | S..S+5 | записи запросов, собранные в тестовых гест-программах: все коды операций (в т.ч. 0 и 99), каналы 65520-65526, 65535, 1234 | сам тест |
| 18 | vm2 | `space/vm2/tests/test_direct.py:132-149 (тест-программы)` | NONE, FSTAT, IOCTL, CLOSE, SEEK, ЧТ, ЗП | S..S+5 | запросы через sys_record/request/response, CLOSE канала S, FSTAT stdin/stdout, SEEK с stdin_position | сам тест |
| 19 | vm2 | `space/vm2/tests/test_guest_cli.py:35-37 (тест-программа)` | FSTAT, SEEK | S, S+1 | FSTAT и SEEK stdin при запуске с обычным файлом | сам тест |
| 20 | rv32i | `space/rv32i/modules/direct_target.py:38-70` | ЧТ, ЗП | S+1, S+2 | ECALL 63/64: копирование между памятью геста и stdin/stdout (приёмник и источник канала задаются полями n, dst/src) | rv32i/tests/test_direct.py:90-95 (read-short, read-eof, write, bad-fd, bad-pointer, zero-count, write-error); rv32i/tests/test_translate.py |
| 21 | rv32i | `space/rv32i/modules/direct_target.py:117-127` | FSTAT, ОТВ | S, S+1, S+2 | после каждой передачи: запись FSTAT на канал данных, чтение ответа, перенос moved и status в результат ECALL | rv32i/tests/test_direct.py:90-95 (short read, EOF, ошибка записи EIO) |
| 22 | rv32i | `space/rv32i/modules/direct_target.py:128` | ЗП | S+3 | построчный дамп 1088 бит состояния регистров в debug (frames) | rv32i/tests/test_monitor.py:16-28 |
| 23 | rv32i | `space/rv32i/modules/rv32i.py:541-577` | ЧТ, ЗП | позиции IN/OUT-слотов | прежний профиль ECALL read/write (io=True) на модели слотов; позиции каналов подставляются линковкой, запросов SYS нет | нет (Image(io=True) вызывается только из CLI в rv32i.py:700) |
| 24 | rv32i | `space/rv32i/modules/rv32i.py:161` | ЗП | позиция OUT-слота | вывод отчёта состояния report_out | нет прямого теста |
| 25 | rv32i | `space/rv32i/modules/translate.py:23,39,72` | ЗП | S+1, S+2 | константы STDIN/STDOUT, out(); halt записывает 1088 бит состояния и память в stdout через copycode.vm1.compute | rv32i/tests/test_translate.py:31-37,60-62 |
| 26 | rv32i | `space/rv32i/runtime/rv32i/runtime.c:15-28` | ЧТ, ЗП | S+1, S+2 (через ECALL) | cs_read(63)/cs_write(64)/cs_exit(93): единственные три вызова гестового кода; нет CLOSE, SEEK, FSTAT, IOCTL, EXEC | rv32i/tests/test_direct.py:94-99 (compiled-c: examples/rv32i/smoke.c) |
| 27 | rv32i | `space/rv32i/examples/rv32i/sum.c:16,28,61; examples/rv32i/smoke.c:5` | ЧТ, ЗП | S+1, S+2 (через ECALL) | примеры C: cs_read/cs_write | smoke.c: rv32i/tests/test_direct.py:97-99; rv32i/tools/benchmark.py:16; sum.c: нет |
| 28 | rv32i | `space/rv32i/tests/fixtures/rv32i/{io_read_once,io_binary_sum,io_memory,large_layout,large_memory}.c` | ЧТ, ЗП | S+1, S+2 (через ECALL) | C-образцы ввода-вывода (4 вызова cs_read и 13 cs_write в файлах строк) | ни один тест дерева не вызывает; перечислены в PROVENANCE.json:98-124 |
| 29 | forth/pForth | `space/forth/runtime/pforth/custom.c:8-15` | ЧТ, ЗП | S+1, S+2 (через ECALL) | слова pForth: чтение/запись блока байт памяти через cs_read/cs_write | forth/tests/test_instructions.py, test_bitfields.py, test_direct.py, test_native_audit.py |
| 30 | forth/pForth | `space/forth/runtime/pforth/custom.c:82-90` | ЧТ, ЗП | S+1, S+2 (через ECALL) | терминал pForth: sdTerminalOut/sdTerminalIn по одному байту | forth/tests/test_direct.py:22-25 (/dev/full, EISDIR на stdin); test_native_audit.py:14-18 |
| 31 | forth/pForth | `space/forth/runtime/pforth/main.c:35` | ЧТ | S+1 (через ECALL) | цикл REPL: чтение строки по одному байту | forth/tests/test_direct.py, test_instructions.py, test_bitfields.py |
| 32 | forth/pForth | `space/forth/runtime/pforth/bootstrap/export.c:7,21,39-45; bootstrap/linux32.c:13-14` | ЧТ, ЗП | fd 0, fd 1 хоста (Linux i386 syscalls) | сборочный инструмент: cs_read/cs_write реализованы системными вызовами хоста; к каналам S..S+5 не обращается | forth/tests/test_forthc_forth.py (host32), forth/scripts/pforth/prepare.py |
| 33 | forth/pForth | `space/forth/tests/guest_support.py:53-58,87-90` | ЧТ, ЗП | S+1, S+2 (хост подаёт и читает) | хостовая обвязка запуска гест-библиотек через stdin/stdout; сам запрос SYS не формируется | forth/tests/test_backend.py, test_compute.py, test_bitfields.py |
| 34 | ядро K | `space/forth/scripts/forthc/forthc.fth:513-516 (fc-read-key), 654` | ЧТ | S+1 | слово KEY: обнуление байта и копирование 8 бит из stdin | forth/tests/test_forthc_self.py, test_kernel.py |
| 35 | ядро K | `space/forth/scripts/forthc/forthc.fth:676-678` | ЗП | S+2 | слово EMIT: копирование байта в stdout с обращением порядка бит | forth/tests/test_forthc.py, test_forthc_self.py, test_kernel.py |
| 36 | ядро K | `space/forth/scripts/forthc/model.py:496-497` | ЧТ | S+1 | модель KEY (эталон Python) | forth/tests/test_forthc.py, test_forthc_forth.py, test_forthc_self.py |
| 37 | ядро K | `space/forth/scripts/forthc/model.py:559-562` | ЗП | S+2 | модель EMIT (эталон Python) | forth/tests/test_forthc.py, test_forthc_forth.py, test_forthc_self.py |
| 38 | ядро K | `space/forth/scripts/forthc/main.fth:7-10` | ЧТ | S+1 | fc-read: KEY до нуля или конца ввода, исходник компилируется целиком | forth/tests/test_forthc_self.py:31-35 |
| 39 | ядро K | `space/forth/scripts/forthc/kernel.fth:24,29-32` | ЧТ, ЗП | S+1, S+2 | ядро: чтение программы из stdin; сообщение об ошибке «error N at WORD» через TYPE/EMIT | forth/tests/test_kernel.py:37-46 |
| 40 | ядро K | `space/copycode/forth/backend.fth:26-27,57,60,120` | ЧТ, ЗП | S+1, S+2 | номера каналов stdin/stdout (cc-size+1, +2); загрузчик cc-loader читает stdin; cc-out даёт строку копирования в stdout | forth/tests/test_backend.py:23,51-60; test_compute.py |
| 41 | ядро K | `space/copycode/forth/compute.fth:253` | ЗП | S+2 | cc-halt-region: область памяти в stdout при остановке | forth/tests/test_compute.py:78,117-122 |
| 42 | copycode | `space/copycode/src/copycode/vm2/sys_gen.py:62-67` | FSTAT, ОТВ, ЗП | S, S+2 | внутрипространственный драйвер: построение записи FSTAT копированиями, запрос в S, чтение ответа из S, вывод ответа в stdout (3 раза плюс нулевой ответ) | vm2/tests/copycode/sys_driver.sh (run_tests.sh:50) |
| 43 | copycode | `space/copycode/src/copycode/vm2/driver_gen.py:60,65,88-89` | ЗП, ЧТ | S+1, S+2 | генераторы --write (запись в stdout) и --echo (чтение из stdin и запись в stdout) | vm2/tests/sys_e2e.sh (run_tests.sh:23) |
| 44 | copycode | `space/copycode/src/copycode/vm2/boundary.py:104,107,116` | ЧТ | S+1 | установщик образа: копирование из stdin порциями | copycode/tests/vm2/test_boundary.py:34,49-57; copycode/tests/vm2/test_transport.py |
| 45 | copycode | `space/copycode/src/copycode/vm2/boundary.py:182-184,272-273` | ЗП | S+2, S+3 | output_region: вывод области в stdout или debug; сброс памяти в stdout | copycode/tests/vm2/test_boundary.py; copycode/tests/vm2/test_transport.py |
| 46 | copycode | `space/copycode/src/copycode/vm2/boundary.py:158,225,242,257,298` | ЗП | S+3 | журнал трассы в debug: заголовок PCS1, префикс шага, метка статуса, признак остановки | copycode/tests/vm2/test_boundary.py:99-110; copycode/tests/vm2/test_dynamic_trace.py |
| 47 | copycode | `space/copycode/src/copycode/vm2/boundary.py:228,233,237-242` | FSTAT, ОТВ, ЗП | S, S+3, канал приложения | трасса: снимок слоя в debug; после шага с каналом данных FSTAT этого канала, чтение ответа и вывод в debug | copycode/tests/vm2/test_boundary.py:101-110; copycode/tests/vm2/test_dynamic_trace.py |
| 48 | copycode | `space/copycode/src/copycode/vm2/dynamic_trace.py:92-109,117-118,160,170-171,183,187` | FSTAT, ОТВ, ЗП | S, S+3, канал приложения | динамический монитор: шаблон FSTAT на первый канал данных слоя, опрос ответа, потоки PCS2 и метки фаз в debug | copycode/tests/vm2/test_dynamic_trace.py:96-113 |
| 49 | copycode | `space/copycode/src/copycode/vm2/terminal.py:97-106,138-140` | ЗП | S+3, S+4, S+5 | терминальный дамп: метки PHT1 в debug, запись слоя продолжения и памяти в snapshot, запись статуса в status | copycode/tests/vm2/test_boundary.py:99-110; copycode/tests/vm2/test_transport.py; copycode/tests/vm2/test_checkpoint.py |
| 50 | copycode | `space/copycode/src/copycode/vm1/sys.py:30-31` | FSTAT, ОТВ | S | библиотека гест-программы: запрос FSTAT и чтение ответа в отдельных слоях | copycode/tests/test_vm1.py:118-123 |
| 51 | copycode | `space/copycode/src/copycode/vm1/monitor.py:6,11` | ЗП | S+3, S+4 | emit: копирование области в debug/status; status() пишет VMS1 и код выхода | copycode/tests/test_vm1.py:108-114 |
| 52 | copycode | `space/copycode/src/copycode/vm1/checkpoint.py:8,10` | ЗП | S+5 | raw-снимок памяти с продолжением в snapshot | copycode/tests/test_vm1.py:108-114,133-160 |
| 53 | copycode | `space/copycode/src/copycode/vm1/boot.py:21,23; vm1/backend.py:38-40,86-87` | ЧТ | S+1 | загрузчик образа читает stdin; свойства Machine.stdin/stdout | copycode/tests/test_vm1.py:81-83; forth/tests/test_backend.py |
| 54 | copycode | `space/copycode/src/copycode/vm1/compute.py:169` | ЗП | S+2 | halt: одна область stdout на слой | forth/tests/test_compute.py; rv32i/tests/test_translate.py |
| 55 | copycode | `space/copycode/src/copycode/vm1/machine.py:38` | ЧТ, ЗП, ОТВ | S..S+5 | таблица каналов sys/stdin/stdout/debug/status/snapshot = size..size+5 | copycode/tests/test_vm1.py:71-83 |
| 56 | copycode | `space/copycode/forth/operations.fth:17,40-65` | ЧТ, ЗП, ОТВ | S..S+5 | гест-слова классификации операции (kind 1 канал данных, 2 запрос SYS, 3 ответ SYS); запросов не формируют | forth/tests/test_operations.py |
| 57 | copycode | `space/copycode/tests/test_vm1.py:118-123 (тест-программа)` | FSTAT | S, S+1 | FSTAT stdin после короткого чтения, проверка moved и eof | сам тест |
| 58 | copycode | `space/copycode/tests/vm2/test_dynamic_trace.py:98-113 (тест-программа)` | CLOSE, ОТВ | S, S+2 | CLOSE канала stdout и проверка EBADF в FSTAT монитора | сам тест |

## Сводка по компонентам

Число мест - число строк таблицы компонента; в скобках - из них тест-программы. Столбцы операций - число строк, где операция встречается.

| Компонент | Мест | ЧТ | ЗП | ОТВ | CLOSE | SEEK | FSTAT | IOCTL | EXEC | Тесты, доходящие до мест |
|---|---|---|---|---|---|---|---|---|---|---|
| vm2 | 19 (3) | 6 | 8 | 6 | 3 | 5 | 6 | 2 | 2 | test_guest.py, test_guest_cli.py, test_direct.py, test_direct_cli.py |
| rv32i | 9 (0) | 5 | 8 | 1 | 0 | 0 | 1 | 0 | 0 | test_direct.py, test_translate.py, test_monitor.py |
| forth/pForth | 5 (0) | 5 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | test_direct.py, test_instructions.py, test_bitfields.py, test_native_audit.py |
| ядро K | 8 (0) | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | test_forthc.py, test_forthc_forth.py, test_forthc_self.py, test_kernel.py, test_backend.py, test_compute.py |
| copycode | 17 (2) | 5 | 12 | 7 | 1 | 0 | 5 | 0 | 0 | copycode/tests/test_vm1.py, tests/vm2/test_{boundary,dynamic_trace,transport,checkpoint}.py, sys_driver.sh, sys_e2e.sh |
| Всего | 58 (5) | 26 | 37 | 14 | 4 | 5 | 12 | 2 | 2 | |

Операции вне тест-программ (число мест): ЧТ 24, ЗП 35, ОТВ 12, CLOSE 1, SEEK 2, FSTAT 8, IOCTL 0, EXEC 1.

## Итог

- Всего мест: 58; в рабочем коде и примерах 53, в тест-программах 5.
- Запросы SYS в рабочем коде (число мест): FSTAT 8, SEEK 2, CLOSE 1, EXEC 1, IOCTL 0. SEEK, CLOSE и EXEC встречаются только в vm2guest (перевод запросов вложенного геста и начальная установка смещения stdin). IOCTL формируют только тест-программы vm2.
- FSTAT формируют: vm2guest (stdin), rv32i (stdin/stdout после каждого ECALL read/write), copycode (sys_gen, boundary и dynamic_trace для трассы, vm1/sys.py).
- Данные идут преимущественно по S+1 (stdin) и S+2 (stdout). S+3, S+4, S+5 используют copycode (debug-трасса, status, snapshot), vm2guest/vm2compile (снимок S+5, отчёт S+4, checkpoint) и rv32i (кадры состояния в S+3).
- pForth и ядро K запросов SYS сами не формируют. pForth достигает каналов тремя вызовами ECALL RV32I (63, 64, 93); ядро K - словами KEY и EMIT (копирование из S+1 и в S+2). Результат передачи (moved, ошибка) для pForth возвращает FSTAT, вставленный rv32i; ядро K его не читает.
- Мест вне покрытия тестами дерева: `rv32i/modules/rv32i.py:541-577` и `:161`, `rv32i/examples/rv32i/sum.c`, пять C-образцов в `rv32i/tests/fixtures/rv32i/` (перечислены только в `PROVENANCE.json`).
