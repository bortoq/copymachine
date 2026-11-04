# Бут языка через хостовой pForth (14.1)

## Что это

`language/` — определение языка (`src/*.fth`, происхождение в `PROVENANCE.json`) и бут — его первая
компиляция. Исполнитель первого бута — хостовой 32-битный pForth (`boot/`): он исполняет
текст определения (`COMPILER_FILES` из `tools/paths.py`: `prelude`, `backend`, `compute`, `forthc`,
`primitives`, `main`; для ядра добавляется `kernel`; генераторы примитивов — `doc/generators.md`) и выдаёт
поток L0 — ядро языка в индексном коде.

## Как устроен бут (`make -C language boot`)

1. `tools/host.py` собирает хостовой pForth по рецепту `boot/common.py`
   (ядро pForth, порт, подготовленный словарь, i386 без libc), но с пулом
   `ALLOCATE` 16 МиБ вместо 64 КиБ. Результат — `language/build/build/host/pforth32`.
   Причина: определение языка компилируется с размерами из `fc-sizes` (`main.fth`):
   текст 128 КиБ, 4096 констант, 2048 слов, таблицы имён и корзин. Рабочие буферы компилятора
   постоянные (`create ... allot`, около 440 КиБ данных; `allocate`/`free` в определении
   нет), поэтому хост получает 1 МиБ свободного кода словаря вместо 256 КиБ
   (`EXTRA_CODE` в `tools/host.py`). Ошибка компиляции — `fc-reject`: печатает
   `error N at WORD` и останавливает исполнение словом `bye` (на хосте — слово хоста,
   в компиляторе как программе — переход в ячейку останова).
2. `tools/boot.py` подаёт хосту на stdin: библиотеки компилятора (`backend.fth`,
   `compute.fth`, `forthc.fth`, с 14.3 и `primitives.fth`) как исходник pForth, строку размеров
   (`131072 fc-text-size ! 4096 fc-max-consts ! 2048 fc-max-words ! 32768 fc-names-size ! 1024 fc-nbuckets !`),
   затем весь текст определения построчно как `fc| <строка>` и `fc-go bye`.
   Компилятор (`forthc.fth`, исполняемый pForth) читает текст определения, а не
   Python-модель; поток на выходе хоста — L0 (последний `\n` — вывод самого хоста,
   в L0 не входит).
3. L0 пишется в `language/build/L0.boot` (выход компонента, рядом с `build/`
   компонента; `output_dir` даёт `language/build/build`, остальное — туда),
   сводка — `language/build/build/boot.json`.

Сверка: `tools/k0_path.py` печатает путь к потоку K0 — тому, что строит модель
`language/tests/reference/model.py` из тех же файлов `src/` (модель — только
эталон; K0 кэшируется в `language/build/build/K0-<хеш>.boot`, строится за
несколько секунд). До изменений определения L0 равен K0 побайтно (`cmp`, `tests/test_boot.py`).

## Цели make

| Цель | Что делает |
|---|---|
| `boot` | бут, L0 |
| `space` | собирает эмулятор из текста определения слова «пространство» (`emulator/src`) в `language/build/space/emulator`; `EMULATOR=<бинарь>` у `check-programs`, `check-kernel` и `check-self` выбирает исполнителя вместо рабочего (`make -C emulator checked`, `emulator/`) |
| `check-programs` | 37 программ `forthc_programs.py` компилируются определением на хосте, поток исполняется на checked-emulator; вывод — ожидаемый (для `PROGRAMS` — вывод того же текста на хостовом pForth, для `EXPECTED` — заданный); `STREAMS=equal` добавляет побайтное равенство потоку модели |
| `check-closure` | граф определения (по `language/tests/reference/defgraph.py`, порядок K): печатает `external N` и имена и (14.8) записывает ядро языка в `doc/core.md`; код 0, если `N <= MAX_EXTERNAL` |
| `check-kernel` | L0 на emulator компилирует и запускает те же программы внутри своего пространства (`test_kernel.py --programs-only`); `tools/check_kernel.py --rebuild` — ещё и пересборка (около полутора часов) |
| `check-self` | (14.15) L0 на emulator компилирует определение языка (шаг 4 `test_kernel.py`: stdin — L0, исходники компилятора, нулевой байт, исходники языка); поток L1 равен L0 побайтно; запускать с `--file-mib 64` (L0 больше 16 МиБ) |
| `check-language-md` | (14.9) `tools/language_md.py --check`: `doc/language.md` синхронизирован с ядром языка — запись на каждое слово ядра, файл, строка и хеш определения совпадают |
| `check` | `check-programs`, `check-closure`, `tests/` (происхождение, замкнутость, бут = K0, с 14.7 — литералы `test_literals.py`, с 14.9 — `test_language_md.py`, с 14.11 — запись слова и цена `test_word.py`), с 14.9 — `check-language-md` |

## Цифры (2026-11-04)

- L0: **16 174 606** байта, равен K0 модели (`tests/test_boot.py`).
- Бут на хостовом pForth: около минуты (47 с на машине автора, один ядровой процесс; модель K0 — несколько секунд).
- Внешних имён определения (`MAX_EXTERNAL`): **0** (`make check-closure`, [closure.md](closure.md)); ядро — 982 слова ([core.md](core.md)).
- `make check` — около 9 минут.
- Самосборка (`check-self`, `tools/check_self.py`): L0 на emulator читает определение языка (`COMPILER_FILES`, нулевой байт, `KERNEL_FILES`) и пишет поток L1; L1 = L0 побайтно (`cmp` внутри инструмента); около 20–30 минут (1716 с при загруженной машине, 18,15 млрд тактов), лимит `SELF_SECONDS` 14000 с; при расхождении инструмент печатает размеры и номер первого отличающегося байта. Запускать через `limited_run.py ... --file-mib 64`; макрос `limit` в Makefile тоже задаёт `--file-mib 64`.
- Для сравнения: бут на хосте — около минуты, самосборка на эмуляторе — около 20 минут.

История размера L0 по этапам (14.1: 14,6 МБ; 14.11: 16,5 МБ; 15: 16,97 МБ; 17: 17,56 МБ; 18.25: 15,81 МБ) — в журнале `docs/journal/roadmap.md`; замеры этапов 14–15 до уборки 2026-10-30 — в теге `archive-2026-10-30`.
