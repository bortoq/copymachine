# Граф определений ядра K

Сгенерировано `tools/research/defgraph.py`; данные в `docs/research/definition-graph.json`.

Порядок компиляции K (из `space/forth/tests/test_kernel.py`): `prelude.fth`, `backend.fth`, `compute.fth`, `forthc.fth`, `main.fth`, `kernel.fth`. Прочие файлы `space/copycode/forth/` (группа aux) разобраны отдельно, в конце, со своим пространством имён; они не входят в K.

Правило видимости как в `forthc.fth`: имя видимо с момента `:`; ссылка идёт к последней определённой на этот момент версии. Слова без определения в исходниках (примитивы) — внешние, рёбер не создают.

## Циклы

| Охват рёбер | Тип | Узлы | Через |
|---|---|---|---|
| прямые | петля | `kn-.n` | recurse |
| прямые | петля | `aux:cc-udigits` | recurse |
| прямые+косвенные | петля | `kn-.n` | recurse |
| прямые+косвенные | петля | `aux:cc-udigits` | recurse |

Сильно связных компонент больше одного узла: 0 (прямые), 0 (все рёбра). Петель: 2 (прямые), 2 (все).

Ссылки вперёд (имя использовано до определения, но определено позже): 0.

## Косвенные ссылки

Косвенных рёбер: 31 (execute-vector: 4, tick: 1, vector-write: 26).

### Переменные-векторы (запись `['] слово ... вектор !`, исполнение `вектор @ execute`)

| Вектор | Записывают (слово → цель) | Исполняют |
|---|---|---|
| `cc-sink` | `kn-compile` → `kn-put` | `cc-put` |
| `cc-start-cell` | — | `main~2` |
| `cc-t-add` | `cc-standard-tables` → `cc-add-entry` | — |
| `cc-t-and` | `cc-standard-tables` → `cc-and-entry` | — |
| `cc-t-fill16` | `cc-standard-tables` → `cc-fill16-entry` | — |
| `cc-t-fill24` | `cc-standard-tables` → `cc-fill24-entry` | — |
| `cc-t-flags` | `cc-standard-tables` → `cc-flags-entry` | — |
| `cc-t-inc1` | `cc-standard-tables` → `cc-inc1-entry` | — |
| `cc-t-inc2` | `cc-standard-tables` → `cc-inc2-entry` | — |
| `cc-t-not5` | `cc-standard-tables` → `cc-not5-entry` | — |
| `cc-t-or` | `cc-standard-tables` → `cc-or-entry` | — |
| `cc-t-or8` | `cc-standard-tables` → `cc-or8-entry` | — |
| `cc-t-sign32` | `cc-standard-tables` → `cc-sign-entry` | — |
| `cc-t-sub` | `cc-standard-tables` → `cc-sub-entry` | — |
| `cc-t-xor` | `cc-standard-tables` → `cc-xor-entry` | — |
| `cc-tx` | — | `cc-table2`; `cc-table` |
| `fc-m4` | `fc-build-mul` → `fc-mul4-entry` | — |
| `fc-qsel` | `fc-build-div` → `fc-qsel-entry` | — |
| `fc-sub` | `fc-build-div` → `cc-sub-entry` | — |
| `fc-t-bytepos` | `fc-tables` → `fc-bytepos-entry` | — |
| `fc-t-fault` | `fc-tables` → `fc-fault-entry` | — |
| `fc-t-lt32` | `fc-tables` → `fc-lt-entry` | — |
| `fc-t-nz2` | `fc-tables` → `fc-nz-entry` | — |
| `fc-t-or8b` | `fc-tables` → `cc-or8-entry` | — |
| `fc-t-rev8` | `fc-tables` → `fc-rev-entry` | — |
| `fc-t-ult32` | `fc-tables` → `fc-ult-entry` | — |
| `fc-t-xr2` | `fc-tables` → `fc-xr2-entry` | — |
| `fc-t-zero32` | `fc-tables` → `fc-zero-entry` | — |

### Прочие ссылки через `'`/`[']` (без записи в вектор)

| Слово | Цель | Файл:строка |
|---|---|---|
| `main~2` | `kn-compile` | forth/scripts/forthc/kernel.fth:30 |

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
| 5 | `cc-slots` | variable | copycode/forth/backend.fth:14 | 9 | 123 | 122 |
| 6 | `>` | colon | forth/scripts/forthc/prelude.fth:16 | 13 | 116 | 115 |
| 7 | `cc-size` | variable | copycode/forth/backend.fth:14 | 5 | 116 | 115 |
| 8 | `cmove` | colon | forth/scripts/forthc/prelude.fth:33 | 10 | 111 | 110 |
| 9 | `cc-a` | variable | copycode/forth/backend.fth:14 | 7 | 110 | 109 |
| 10 | `0<` | colon | forth/scripts/forthc/prelude.fth:19 | 5 | 108 | 108 |
| 11 | `cc-inst` | colon | copycode/forth/backend.fth:23 | 3 | 107 | 106 |
| 12 | `cc-layer-bits` | colon | copycode/forth/backend.fth:24 | 5 | 105 | 104 |
| 13 | `<>` | colon | forth/scripts/forthc/prelude.fth:18 | 10 | 103 | 102 |
| 14 | `?dup` | colon | forth/scripts/forthc/prelude.fth:13 | 11 | 103 | 103 |
| 15 | `cc-rev` | create | copycode/forth/backend.fth:18 | 7 | 103 | 102 |
| 16 | `fill-cell` | variable | forth/scripts/forthc/prelude.fth:28 | 1 | 102 | 101 |
| 17 | `cc-cell-bits` | variable | copycode/forth/backend.fth:14 | 9 | 101 | 100 |
| 18 | `fill` | colon | forth/scripts/forthc/prelude.fth:29 | 6 | 101 | 100 |
| 19 | `cc-lbytes` | colon | copycode/forth/backend.fth:25 | 5 | 100 | 99 |
| 20 | `cc-rows` | create | copycode/forth/backend.fth:52 | 5 | 100 | 99 |
| 21 | `-rot` | colon | forth/scripts/forthc/prelude.fth:8 | 4 | 99 | 98 |
| 22 | `cc-dest` | variable | copycode/forth/backend.fth:16 | 4 | 99 | 98 |
| 23 | `cc-field-check` | colon | copycode/forth/backend.fth:38 | 1 | 99 | 98 |
| 24 | `cc-len` | variable | copycode/forth/backend.fth:51 | 5 | 99 | 98 |
| 25 | `cc-numeric` | colon | copycode/forth/backend.fth:29 | 6 | 99 | 98 |
| 26 | `cc-numeric4` | colon | copycode/forth/backend.fth:35 | 1 | 99 | 98 |
| 27 | `cc-start` | variable | copycode/forth/backend.fth:51 | 5 | 99 | 98 |
| 28 | `cc-chunk-buf` | variable | copycode/forth/backend.fth:15 | 4 | 98 | 97 |
| 29 | `cc-clear-rows` | colon | copycode/forth/backend.fth:55 | 3 | 98 | 97 |
| 30 | `cc-encode` | colon | copycode/forth/backend.fth:41 | 3 | 98 | 97 |

## Итог

| Показатель | Значение |
|---|---|
| Узлов-определений всего (K + aux) | 692 |
| В K | 631 (по файлам: prelude.fth 35, backend.fth 88, compute.fth 136, forthc.fth 361, main.fth 4, kernel.fth 7) |
| Виды | colon 377, constant 15, create 38, variable 262 |
| Повторно определённых имён (версия > 1) | 3 узлов |
| Они | `cc-l1~2`, `cc-l2~2`, `main~2` |
| Рёбер (прямых / косвенных) | 1947 / 31 |
| Циклы (прямые рёбра): компонент > 1 / петель | 0 / 2 |
| Циклы (все рёбра): компонент > 1 / петель | 0 / 2 |
| Векторов (переменных, в которые пишут `[']`-ссылки) | 26 |
| Мест EXECUTE | 5 |
| Внешних имён (примитивы, нет определения в исходниках) | 68 различных, 5692 использований |
| Больше всего зависимых | `2drop`: 160 транзитивно |
| Слов без зависимых | 28 из 692 |

Внешние имена, чаще всего используемые: `@` 977, `!` 536, `+` 505, `if` 324, `then` 324, `dup` 275, `cells` 230, `drop` 188, `i` 160, `swap` 156, `exit` 122, `r>` 122, `r@` 116, `>r` 115, `and` 113, `throw` 100, `over` 94, `*` 92, `pick` 90, `loop` 85, `0=` 81, `else` 69, `lshift` 69, `rshift` 60, `-` 56.
