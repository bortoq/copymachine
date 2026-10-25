# Слово-генератор (14.3–14.5)

## Механизм

Генератор — запись словаря компилятора с признаком «генератор»: слово, которое
компилятор находит в исходнике и **исполняет** (как `IMMEDIATE`), а оно выдаёт
копикод слова языка. Примитивы арифметики и логики (14.3), стека, памяти и каналов (14.4), управления (14.5) стали генераторами: их ветви
`fc-is?` из `src/forthc.fth` перенесены в определения `src/primitives.fth` без
изменения алгоритмов, поэтому потоки программ прежние (`check-programs
STREAMS=equal`: побайтно равны потокам модели `space/forth/scripts/forthc/model.py`).

- **Запись словаря** (`fc-wt`, 5 ячеек): смещение имени, длина, вид, значение,
  следующая в цепочке. Вид: `0` — данные или константа (значение — литерал),
  `1` — слово (значение — ячейка входа, вызов), бит `2` — генератор (значение —
  xt слова компилятора, исполняется); биты 2–3 вида у генератора — нужные ему
  подпрограммы: `4` — умножение, `8` — деление.
- **Регистрация.** `fc-generator ( addr u xt uses -- )` создаёт запись. Слово
  `fc-generators` (`primitives.fth`) регистрирует 59 слов языка (58 генераторов; `r@` и `i` — один); его xt лежит в
  векторе `fc-gens` (`fc-install-generators` — код верхнего уровня
  `primitives.fth`). `fc-words` в начале `fc-compile` очищает словарь и исполняет
  `fc-gens`: генераторы — первые записи, программа может переопределить их имена
  (новое определение — во главе цепочки).
- **Исполнение.** Внутри определения (`fc-control-token`) и на верхнем уровне
  (`fc-top-token`) `fc-find` находит запись; у генератора исполняется xt.
- **Подпрограммы.** `fc-scan-uses` до кода ищет каждое слово исходника в словаре
  и собирает биты 2–3 вида генераторов: по ним строятся подпрограммы умножения
  (`*`) и деления (`/ mod /mod`), как раньше по `fc-is?`.

Генератор исполняется тем исполнителем, который компилирует: при буте — хостовой
pForth (`primitives.fth` загружается в него вместе с `backend`, `compute`,
`forthc`), в ядре L0 — само ядро (`primitives.fth` в определении языка между
`forthc.fth` и `main.fth`; `execute` xt — косвенный вызов в пространстве).

## Слова состояния компилятора для генераторов

| Часть состояния | Слова |
|---|---|
| Кэш стека | `fc-pop ( -- r )` снять регистр (с подкачкой из памяти), `fc-push ( r -- )` положить регистр, `fc-depth ( -- n )` глубина кэша, `fc-need ( n -- )` обеспечить n элементов в кэше, `fc-pop1 ( -- r )` снять без подкачки, `fc-reg ( -- r )` свободный регистр, `fc-pop-pinned ( -- a r )` снять a и взять регистр r ≠ a, `fc-lit? ( -- f )` вершина кэша — только что скомпилированный литерал (значение в `fc-plv`) |
| Стек управления | `fc-ctl+ ( kind cell -- )` открыть структуру (вид: 1 if, 2 else, 3 begin, 4 while, 5 do), `fc-ctl- ( -- kind cell )` закрыть, `fc-ctl-depth ( -- n )`; ячейка выхода цикла (14.5): `fc-ctl-leave ( -- cell )` у записи, снятой `fc-ctl-` (0 — нет), `fc-ctl-leave! ( cell -- )` у верхней записи, `fc-do-entry ( -- entry )` запись внутреннего цикла (иначе -22), `fc-loop-leave ( entry -- cell )` её ячейка выхода (новая, если не было) |
| Текущий слой | `cc-layer ( -- layer )` новый слой текущей последовательности, `cc-last ( -- layer )` последний слой, `cc-row ( dl dh sl sh layer -- slot )`, `fc-rows1 ( dl dh sl sh -- )` строка в новом слое |
| Константы | `fc-const ( v -- addr )` адрес 32-битной константы; известные при компиляции значения верхнего уровня: `fc-known ( -- n )`, `fc-ct- ( -- v )`, `fc-ct2 ( -- a b )`, `fc-ct+ ( v -- )` |
| Режим | `fc-fold? ( n -- f )` — истина, если известны n значений (генератор сворачивает их: `fc-ct2 + fc-ct+`); иначе `fc-code` и ложь. `fc-code ( -- )` — на верхнем уровне открывает часть кода до `MAIN` (известные значения становятся литералами), в определении ничего не делает. Генератор, который не сворачивает, начинает с `fc-code` |
| Таблицы | переменные с адресами таблиц: `cc-t-add`, `cc-t-sub`, `cc-t-and`, `cc-t-or`, `cc-t-xor` (`compute.fth`), `fc-t-zero32`, `fc-t-lt32`, `fc-t-ult32`, `fc-t-nz2`, `fc-t-rev8` … (`fc-tables`) |
| Построители | `fc-binary ( op -- )`, `fc-shift-copy ( k -- )`, `fc-inc ( table k carry -- )`, `fc-or-zero ( out r -- )`, `fc-call-helper ( entry exit -- )` с `fc-result1`/`fc-result2`, `fc-shift-lit? ( right? -- f )`, `fc-mul-lit? ( -- f )` |

Новые слова 14.3: `fc-gens`, `fc-generator`, `fc-words`, `fc-depth`,
`fc-ctl-depth`, `fc-known`, `fc-code`, `fc-fold?`, `fc-lit?`, `fc-mul-lit?`
(`fc-shift-lit?` получил аргумент `right?` вместо `fc-is?`). Удалены `fc-ct-op`
и все ветви `fc-is?` двадцати слов.

## Генераторы (`src/primitives.fth`)

| Слово языка | Генератор | Сворачивает | Код |
|---|---|---|---|
| `+ - and or xor` | `gen+ gen- gen-and gen-or gen-xor` | 2 значения | `fc-binary` 0–4 |
| `= < u<` | `gen= gen< gen-u<` | — | `fc-binary` 5–7 |
| `lshift rshift` | `gen-lshift gen-rshift` | 2 | литеральный сдвиг `fc-shift-lit?`, иначе `fc-binary` 8, 9 |
| `0=` | `gen-0=` | — | `fc-or-zero` |
| `cells 2*` | `gen-cells gen-2*` | 1 | `fc-shift-copy` 2, 1 |
| `1+ 1- cell+` | `gen-1+ gen-1- gen-cell+` | 1 | `fc-inc` |
| `*` | `gen*` (подпрограмма 1) | 2 | степень двойки — `fc-mul-lit?`, иначе вызов умножения |
| `/ mod /mod` | `gen/ gen-mod gen/mod` (подпрограмма 2) | — | вызов деления |

## Генераторы 14.4: стек, память, каналы

Слова `dup drop swap over rot pick roll >r r> r@ i j @ ! c@ c! space! spacec!
emit key` перенесены из `fc-primitive` (и четырёх строк `pick space! spacec!
roll` из `fc-word-token`) в `src/primitives.fth` без изменения алгоритмов. Новых
слов состояния компилятора нет: используются кэш стека (`fc-pop fc-pop1 fc-push
fc-need fc-reg`, переменная `fc-n` и `fc-c@` — регистр элемента кэша по
индексу), указатели стеков (`fc-sp`, `fc-rp`, `fc-rstk`), построители
`fc-r-at`, `fc-read-key`, `fc-pick-roll`, `fc-space-store`, `fc-mem-push`,
`fc-mem-pop`, `fc-popped@`, `fc-check` (проверка адреса, 0 — `@`, 1 — `!`,
2 — `c@`, 3 — `c!`), `fc-adjust`, `fc-src1`. Новых слов 14.4 нет, кроме самих
генераторов. Каждый генератор начинается с `fc-code`: на верхнем уровне он
открывает часть кода до `MAIN` и сбрасывает признак литерала (как раньше путь
слов, не найденных в словаре: `fc-open-init 0 fc-plit !`), в определении
ничего не делает.

| Слово языка | Генератор |
|---|---|
| `dup drop swap over rot` | `gen-dup gen-drop gen-swap gen-over gen-rot` |
| `pick roll` | `gen-pick gen-roll` (`fc-pick-roll`: N — литерал на вершине кэша) |
| `>r r> r@ i j` | `gen->r gen-r> gen-r@ gen-j` (`r@` и `i` — один генератор) |
| `@ ! c@ c!` | `gen-@ gen-! gen-c@ gen-c!` |
| `space! spacec!` | `gen-space! gen-spacec!` (`fc-space-store`, 32 и 8 бит) |
| `emit key` | `gen-emit gen-key` |

В `fc-primitive` остались `decimal` и `unloop` (не из этого списка) и ошибка
`-13` для неизвестного слова. Побочное отличие, как в 14.3: слово словаря,
найденное `fc-find`, идёт раньше встроенных; программа, переопределившая `dup`,
`pick` и т. п., теперь переопределяет и `pick`/`roll`/`space!`/`spacec!`
(раньше их `fc-word-token` проверял до словаря). В программах проверки такого нет.

## Генераторы 14.5: управление

Ветви `fc-is?` слов `if else then begin until while repeat again do ?do loop
leave unloop exit recurse execute ['] catch throw` перенесены из
`fc-control-token`, `fc-word-token` и `fc-primitive` (`unloop`) в
`src/primitives.fth` без изменения алгоритмов; тела `fc-qdo`, `fc-loop`,
`fc-leave` (с переменными `fc-di fc-dl fc-lv`) стали генераторами `gen-?do`,
`gen-loop`, `gen-leave`. `fc-catch` и `fc-throw` остались построителями в
`forthc.fth` (они пишут в ячейку кода `fc-code` — адрес данных, который
слово `fc-code` 14.3 перекрывает). Каждый генератор начинается с `fc-code`:
на верхнем уровне так же, как прежний путь `fc-open-init 0 fc-plit !
fc-word-token`.

Используются: кэш стека (`fc-pop fc-pop1 fc-need fc-spill`), стек управления
(таблица выше), блоки и ячейки (`fc-begin-block fc-branch fc-jump fc-end
cc-new-cell cc-new-record cc-next! cc-flush cc-seq`), стек возвратов
(`fc-srcs fc-nsrc fc-rstk fc-rp fc-mem-push fc-mem-pop fc-popped@ fc-adjust
fc-noff`), вызовы (`fc-ret fc-call fc-call-indirect fc-word`), словарь и
канал (`fc-next! fc-find fc-literal`). Новые слова состояния 14.5:
`fc-ctl-leave`, `fc-ctl-leave!`, `fc-loop-leave` (выделены из `fc-loop`,
`fc-qdo`, `fc-leave`).

| Слово языка | Генератор |
|---|---|
| `if else then` | `gen-if gen-else gen-then` |
| `begin until while repeat again` | `gen-begin gen-until gen-while gen-repeat gen-again` |
| `do ?do loop leave unloop` | `gen-do gen-?do gen-loop gen-leave gen-unloop` |
| `exit recurse execute [']` | `gen-exit gen-recurse gen-execute gen-tick` |
| `catch throw` | `gen-catch gen-throw` |

В компиляторе остались ветви `fc-is?` слов `; [char] ( ) : variable create
allot constant decimal kernel-layout` (14.6). Побочное отличие, как в 14.3 и
14.4: генератор найден `fc-find`, поэтому программа может переопределить
`exit`, `recurse`, `[']` (раньше `fc-word-token` проверял их до словаря).

## Имя слова и имя генератора

Словарное имя генератора в Forth-реализации отличается от имени слова языка
(`gen+` для `+`): хостовой pForth сам пользуется `+`, и определение `: + … ;`
заменило бы его при буте. Слово языка — это запись словаря компилятора с
именем `+`; связь имени с генератором — строка регистрации
`s" +" ['] gen+ 0 fc-generator`.

`check-closure` (`tools/check_closure.py`) читает эти строки в
`primitives.fth` и добавляет в граф узел имени языка (`+`, вид `generator`) с
ребром к генератору (`gen+`): сорок слов определены. Внешних имён было 58,
после 14.3 — 39 (внешними были 19 из 20 слов арифметики; `/mod` в определении не
используется), после 14.4 — 19 (все 20 слов 14.4 были внешними), после 14.5 — **2**
(`MAX_EXTERNAL ?= 2` в `Makefile`; внешними были 17 из 19 слов управления,
`recurse` и `[']` граф разбирал особо): `decimal kernel-layout`.

## Цифры

- 14.5: L0 14 513 255 байт, бут около 10 с; `fc-is?` в `forthc.fth` — 12
  вхождений (было 33); `check-kernel`: 37 программ компилируются и исполняются
  в пространстве ядром L0 (953 с).
- 14.4: L0 14 547 895 байт (после 14.3 — 14 586 891), бут около 10 с;
  `fc-is?` в `forthc.fth` — 33 вхождения (было 53; убрано 20: 16 в
  `fc-primitive`, 4 в `fc-word-token`); в `fc-primitive` их осталось 2.
- 14.3: L0 14 586 891 байт (было 14 596 459), около 10 с на хосте; L0 равен K0
  модели для нового текста определения (`tests/test_boot.py`).
- `check-programs STREAMS=equal`: 37 программ, потоки равны потокам модели.
- `fc-is?` в `forthc.fth`: было 95 вхождений, стало 53 (убрано 42 ветви:
  20 в `fc-primitive`, 13 в `fc-ct-op`, 4 в `fc-scan-uses`, 3 в
  `fc-word-token`, 2 в `fc-shift-lit?`).
