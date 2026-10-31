# Граф определений ядра K

Сгенерировано `language/tests/reference/defgraph.py`; данные в `docs/research/definition-graph.json`.

Порядок компиляции K (из `forth/tests/test_kernel.py`): `prelude.fth`, `backend.fth`, `compute.fth`, `forthc.fth`, `main.fth`, `kernel.fth`. Прочие файлы `copycode/forth/` (группа aux) разобраны отдельно, в конце, со своим пространством имён; они не входят в K.

Правило видимости как в `forthc.fth`: имя видимо с момента `:`; ссылка идёт к последней определённой на этот момент версии. Слова без определения в исходниках (примитивы) — внешние, рёбер не создают.

## Циклы

| Охват рёбер | Тип | Узлы | Через |
|---|---|---|---|
| прямые | петля | `kn-.n` | recurse |
| прямые | петля | `aux:lay-udigits` | recurse |
| прямые+косвенные | петля | `kn-.n` | recurse |
| прямые+косвенные | петля | `aux:lay-udigits` | recurse |

Сильно связных компонент больше одного узла: 0 (прямые), 0 (все рёбра). Петель: 2 (прямые), 2 (все).

Ссылки вперёд (имя использовано до определения, но определено позже): 0.

## Косвенные ссылки

Косвенных рёбер: 31 (execute-vector: 4, vector-write: 1, xt-arg: 26).

### Векторы исполнения (переменные, исполняемые как `V @ execute` или `V @ ?dup if execute`)

Запись `['] слово ... V !` учитывается только для таких V; запись xt из стека (`... V !`) показана как «xt из стека».

| Вектор | Записывают (слово → цель) | Исполняют |
|---|---|---|
| `lay-sink` | `kn-compile` → `kn-put` | `lay-put` |
| `lay-start-cell` | `lay-finish` → xt из стека | `main~2` |
| `lay-tx` | `lay-table` → xt из стека; `lay-table2` → xt из стека | `lay-table2`; `lay-table` |

### xt-аргументы (`['] слово` передаётся принимающему слову, а не записывается в вектор)

| Слово | Передаваемый xt | Получатель (receiver) | Файл:строка |
|---|---|---|---|
| `lay-standard-tables` | `lay-add-entry` | `lay-table` | copycode/forth/compute.fth:168 |
| `lay-standard-tables` | `lay-sub-entry` | `lay-table` | copycode/forth/compute.fth:168 |
| `lay-standard-tables` | `lay-xor-entry` | `lay-table` | copycode/forth/compute.fth:169 |
| `lay-standard-tables` | `lay-or-entry` | `lay-table` | copycode/forth/compute.fth:169 |
| `lay-standard-tables` | `lay-and-entry` | `lay-table` | copycode/forth/compute.fth:170 |
| `lay-standard-tables` | `lay-or8-entry` | `lay-table` | copycode/forth/compute.fth:170 |
| `lay-standard-tables` | `lay-flags-entry` | `lay-table` | copycode/forth/compute.fth:171 |
| `lay-standard-tables` | `lay-not5-entry` | `lay-table` | copycode/forth/compute.fth:171 |
| `lay-standard-tables` | `lay-sign-entry` | `lay-table` | copycode/forth/compute.fth:172 |
| `lay-standard-tables` | `lay-fill24-entry` | `lay-table` | copycode/forth/compute.fth:172 |
| `lay-standard-tables` | `lay-fill16-entry` | `lay-table` | copycode/forth/compute.fth:173 |
| `lay-standard-tables` | `lay-inc1-entry` | `lay-table` | copycode/forth/compute.fth:173 |
| `lay-standard-tables` | `lay-inc2-entry` | `lay-table` | copycode/forth/compute.fth:174 |
| `fc-tables` | `fc-rev-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:57 |
| `fc-tables` | `fc-zero-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:58 |
| `fc-tables` | `fc-nz-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:59 |
| `fc-tables` | `fc-lt-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:60 |
| `fc-tables` | `lay-or8-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:61 |
| `fc-tables` | `fc-fault-entry` | `lay-table2` | forth/scripts/forthc/forthc.fth:62 |
| `fc-tables` | `fc-xr2-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:63 |
| `fc-tables` | `fc-ult-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:64 |
| `fc-tables` | `fc-bytepos-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:65 |
| `fc-build-mul` | `fc-mul4-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:386 |
| `fc-build-div` | `lay-sub-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:437 |
| `fc-build-div` | `fc-qsel-entry` | `lay-table` | forth/scripts/forthc/forthc.fth:438 |
| `main~2` | `kn-compile` | `catch` | forth/scripts/forthc/kernel.fth:30 |

### Прочие ссылки через `'`/`[']` (без записи в вектор)

| Слово | Цель | Файл:строка |
|---|---|---|

### Места EXECUTE

Всего 5; с видимым вектором (`V @ execute`): 5; с адресом из стека (цель не видна статически): 0.

## Число зависимых

Для слова — число слов (узлов-определений, без неявных узлов верхнего уровня), использующих его прямо или транзитивно; считается по всем рёбрам (прямые и косвенные). Столбец «только прямые рёбра» — то же без косвенных рёбер. Топ-30 по первому числовому столбцу.

| # | Слово | Вид | Файл:строка | Прямых | Транзитивно (все рёбра) | Транзитивно (только прямые рёбра) |
|---|---|---|---|---|---|---|
| 1 | `2drop` | colon | forth/scripts/forthc/prelude.fth:10 | 24 | 160 | 159 |
| 2 | `2dup` | colon | forth/scripts/forthc/prelude.fth:9 | 22 | 142 | 141 |
| 3 | `+!` | colon | forth/scripts/forthc/prelude.fth:24 | 36 | 134 | 133 |
| 4 | `u>` | colon | forth/scripts/forthc/prelude.fth:17 | 9 | 124 | 123 |
| 5 | `lay-slots` | variable | copycode/forth/backend.fth:14 | 9 | 123 | 122 |
| 6 | `>` | colon | forth/scripts/forthc/prelude.fth:16 | 13 | 116 | 115 |
| 7 | `lay-size` | variable | copycode/forth/backend.fth:14 | 5 | 116 | 115 |
| 8 | `cmove` | colon | forth/scripts/forthc/prelude.fth:33 | 10 | 111 | 110 |
| 9 | `lay-a` | variable | copycode/forth/backend.fth:14 | 7 | 110 | 109 |
| 10 | `0<` | colon | forth/scripts/forthc/prelude.fth:19 | 5 | 108 | 108 |
| 11 | `lay-inst` | colon | copycode/forth/backend.fth:23 | 3 | 107 | 106 |
| 12 | `lay-layer-bits` | colon | copycode/forth/backend.fth:24 | 5 | 105 | 104 |
| 13 | `<>` | colon | forth/scripts/forthc/prelude.fth:18 | 10 | 103 | 102 |
| 14 | `?dup` | colon | forth/scripts/forthc/prelude.fth:13 | 11 | 103 | 103 |
| 15 | `lay-rev` | create | copycode/forth/backend.fth:18 | 7 | 103 | 102 |
| 16 | `fill-cell` | variable | forth/scripts/forthc/prelude.fth:28 | 1 | 102 | 101 |
| 17 | `lay-cell-bits` | variable | copycode/forth/backend.fth:14 | 9 | 101 | 100 |
| 18 | `fill` | colon | forth/scripts/forthc/prelude.fth:29 | 6 | 101 | 100 |
| 19 | `lay-lbytes` | colon | copycode/forth/backend.fth:25 | 5 | 100 | 99 |
| 20 | `lay-rows` | create | copycode/forth/backend.fth:52 | 5 | 100 | 99 |
| 21 | `-rot` | colon | forth/scripts/forthc/prelude.fth:8 | 4 | 99 | 98 |
| 22 | `lay-dest` | variable | copycode/forth/backend.fth:16 | 4 | 99 | 98 |
| 23 | `lay-field-check` | colon | copycode/forth/backend.fth:38 | 1 | 99 | 98 |
| 24 | `lay-len` | variable | copycode/forth/backend.fth:51 | 5 | 99 | 98 |
| 25 | `lay-numeric` | colon | copycode/forth/backend.fth:29 | 6 | 99 | 98 |
| 26 | `lay-numeric4` | colon | copycode/forth/backend.fth:35 | 1 | 99 | 98 |
| 27 | `lay-start` | variable | copycode/forth/backend.fth:51 | 5 | 99 | 98 |
| 28 | `lay-chunk-buf` | variable | copycode/forth/backend.fth:15 | 4 | 98 | 97 |
| 29 | `lay-clear-rows` | colon | copycode/forth/backend.fth:55 | 3 | 98 | 97 |
| 30 | `lay-encode` | colon | copycode/forth/backend.fth:41 | 3 | 98 | 97 |

## Итог

| Показатель | Значение |
|---|---|
| Узлов-определений всего (K + aux) | 692 |
| В K | 631 (по файлам: prelude.fth 35, backend.fth 88, compute.fth 136, forthc.fth 361, main.fth 4, kernel.fth 7) |
| Виды | colon 377, constant 15, create 38, variable 262 |
| Повторно определённых имён (версия > 1) | 3 узлов |
| Они | `lay-l1~2`, `lay-l2~2`, `main~2` |
| Рёбер (прямых / косвенных) | 1947 / 31 |
| Циклы (прямые рёбра): компонент > 1 / петель | 0 / 2 |
| Циклы (все рёбра): компонент > 1 / петель | 0 / 2 |
| Мест EXECUTE | 5 |
| Внешних имён (примитивы, нет определения в исходниках) | 68 различных, 5692 использований |
| Больше всего зависимых | `2drop`: 160 транзитивно |
| Слов без зависимых | 28 из 692 |

Векторов исполнения: 3

xt-аргументов: 26

Внешние имена, чаще всего используемые: `@` 977, `!` 536, `+` 505, `if` 324, `then` 324, `dup` 275, `cells` 230, `drop` 188, `i` 160, `swap` 156, `exit` 122, `r>` 122, `r@` 116, `>r` 115, `and` 113, `throw` 100, `over` 94, `*` 92, `pick` 90, `loop` 85, `0=` 81, `else` 69, `lshift` 69, `rshift` 60, `-` 56.
