# Бут языка через хостовой pForth (14.1)

## Что это

`space/language/` — компонент эксперимента: определение языка (`src/*.fth`, копия
исходников ядра K, происхождение в `PROVENANCE.json`) и бут — его первая
компиляция. Исполнитель первого бута — хостовой 32-битный pForth: он исполняет
текст определения (`prelude`, `backend`, `compute`, `forthc`, `main`, `kernel`,
в порядке `KERNEL` из `space/forth/tests/test_kernel.py`; с 14.3 после `forthc` —
`primitives`, генераторы примитивов, `doc/generators.md`) и выдаёт поток L0 —
ядро языка в индексном коде. Рабочий путь (`space/forth`, корневой Makefile,
выпуски) не менялся: исходники скопированы, `host32.py` и `common.py` только
импортируются.

## Как устроен бут (`make -C space/language boot`)

1. `tools/host.py` собирает хостовой pForth по рецепту `space/forth/scripts/pforth/host32.py`
   (те же ядро pForth, порт, подготовленный словарь, i386 без libc), но с пулом
   `ALLOCATE` 16 МиБ вместо 64 КиБ. Результат — `build/space/language/build/host/pforth32`.
   Причина: определение языка компилируется с размерами из `fc-sizes` (`main.fth`):
   текст 128 КиБ, 4096 констант, 2048 слов, таблицы имён и корзин; на стандартном
   хосте `ALLOCATE` не хватает памяти (ABORT, код -1). Размер словаря (имена и код
   самого pForth) не менялся — его хватает.
2. `tools/boot.py` подаёт хосту на stdin: библиотеки компилятора (`backend.fth`,
   `compute.fth`, `forthc.fth`, с 14.3 и `primitives.fth`) как исходник pForth, строку размеров
   (`131072 fc-text-size ! 4096 fc-max-consts ! 2048 fc-max-words ! 32768 fc-names-size ! 1024 fc-nbuckets !`),
   затем весь текст определения построчно как `fc| <строка>` и `fc-go bye`.
   Компилятор (`forthc.fth`, исполняемый pForth) читает текст определения, а не
   Python-модель; поток на выходе хоста — L0 (последний `\n` — вывод самого хоста,
   в L0 не входит).
3. L0 пишется в `build/space/language/L0.boot` (выход компонента, рядом с `build/`
   компонента; `output_dir` даёт `build/space/language/build`, остальное — туда),
   сводка — `build/space/language/build/boot.json`.

Сверка: `tools/k0_path.py` печатает путь к потоку K0 — тому, что строит модель
`space/forth/scripts/forthc/model.py` из тех же файлов `src/` (модель — только
эталон; K0 кэшируется в `build/space/language/build/K0-<хеш>.boot`, строится за
несколько секунд). До изменений определения L0 равен K0 побайтно (`cmp`, `tests/test_boot.py`).

## Цели make

| Цель | Что делает |
|---|---|
| `boot` | бут, L0 |
| `space` | собирает эмулятор из текста определения слова «пространство» (`emulator/src`) в `build/space/language/space/emulator`; `EMULATOR=<бинарь>` у `check-programs`, `check-kernel` и `check-self` выбирает исполнителя вместо рабочего (`make -C emulator checked`, `emulator/`) |
| `check-programs` | 37 программ `forthc_programs.py` компилируются определением на хосте, поток исполняется на checked-emulator; вывод — ожидаемый (для `PROGRAMS` — вывод того же текста на хостовом pForth, для `EXPECTED` — заданный); `STREAMS=equal` добавляет побайтное равенство потоку модели |
| `check-closure` | граф определения (по `tools/research/defgraph.py`, порядок K): печатает `external N` и имена и (14.8) записывает ядро языка в `doc/core.md`; код 0, если `N <= MAX_EXTERNAL` |
| `check-kernel` | L0 на emulator компилирует и запускает те же программы внутри своего пространства (`test_kernel.py --programs-only`); `tools/check_kernel.py --rebuild` — ещё и пересборка (около полутора часов) |
| `check-self` | (14.15) L0 на emulator компилирует определение языка (шаг 4 `test_kernel.py`: stdin — L0, исходники компилятора, нулевой байт, исходники языка); поток L1 равен L0 побайтно; запускать с `--file-mib 64` (L0 больше 16 МиБ) |
| `check-language-md` | (14.9) `tools/language_md.py --check`: `doc/language.md` синхронизирован с ядром языка — запись на каждое слово ядра, файл, строка и хеш определения совпадают |
| `check` | `check-programs`, `check-closure`, `tests/` (происхождение, замкнутость, бут = K0, с 14.7 — литералы `test_literals.py`, с 14.9 — `test_language_md.py`, с 14.11 — запись слова и цена `test_word.py`), с 14.9 — `check-language-md` |

## Цифры (этот прогон)

- Время бута: около 10–13 с (хостовой pForth, 1 ядро; K0 моделью — около 3 с).
- Размер L0: 14 596 459 байт (14.6 МБ), sha256 `700f91fb26f13bd7…`; равен K0.
- Определений в языке: 635 (слова и данные по графу `check-closure`).
- Внешних имён (`MAX_EXTERNAL`): **58**.
- После 14.3 (генераторы): L0 14 586 891 байт, равен K0 модели для нового текста;
  определений 687; внешних имён **39** (`doc/generators.md`).
- После 14.11 (запись слова, цена при компиляции): L0 16 529 105 байт (после 14.10 — 14 973 769),
  равен K0; бут около 12 с (`doc/word.md`).

## Число внешних имён: 58, а не 68

В `docs/research/definition-graph.md` указано 68 внешних имён — это граф K вместе с
группой aux (`integers`, `bitfields`, `format`, `arena`, `instructions`,
`operations`, `evaluate` из `space/copycode/forth/`), не входящей в K. Определение
языка — только K, и в нём 58 внешних имён (4925 использований). Десять лишних —
имена только aux: `2>r`, `2r>`, `base`, `d+`, `interpret`, `pop-source-id`,
`push-source-id`, `set-source`, `space`, `um/mod`. `MAX_EXTERNAL = 58` записан в
`Makefile`; его можно понизить, но не повышать (14.3: 39).

Внешние имена: `@ ! + if then dup cells drop i exit swap and r> >r * loop over
lshift 0= r@ throw else rshift ?do - = or pick 1- 1+ cell+ rot do < c@ 2* begin
repeat while c! j u< execute roll unloop xor emit / decimal again catch
kernel-layout key leave mod space! spacec! until` (слова управления и
стековые примитивы, которые компилятор строит сам, плюс шесть слов ядра:
`kernel-layout`, `space!`, `spacec!`, `key`, `emit`, `decimal`).

## Язык компилирует себя (14.15)

`make -C space/language check-self` (`tools/check_self.py`): L0 на emulator читает определение языка
(исходники `COMPILER_FILES`, нулевой байт, исходники `KERNEL_FILES`) и пишет поток L1.

- Результат: L1 = 16 967 309 байт, равен L0 побайтно (`cmp` внутри инструмента), с первого прогона.
- Время: 5792 с (1 ч 36 мин 32 с по `time`), один ядровой процесс, лимит 14400 с с запасом.
- Для сравнения: бут на хостовом pForth около 12 с, то есть язык на emulator в сотни раз медленнее хоста.
- При расхождении инструмент печатает размеры и номер первого отличающегося байта.
- Запускать через `limited_run.py ... --file-mib 64`; макрос `limit` в Makefile тоже задаёт `--file-mib 64`.
