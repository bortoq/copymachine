# Ядро языка (14.8)

Файл порождается `make -C space/language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`tools/research/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 882** (определение `:` — 447, переменная — 287, генератор — 71, данные `create` — 44, константа — 17, цифра (литерал) — 10, основание — 6).

## Основание

Основание — слова-копирования: генераторы строки (копия — приёмник и источник) и слоя (ячейка строк) из `src/backend.fth`. Определение инструкции — она сама: тело этих слов не сводится к другим словам языка, а строка и слой — сами инструкции индексного пространства.

| Слово | Что порождает | Файл:строка |
|---|---|---|
| `cc-copy` | строка: копирование n бит из источника в приёмник | src/backend.fth:119 |
| `cc-link-row` | строка: копирование ссылки на следующий слой | src/backend.fth:118 |
| `cc-row` | строка: добавляет строку в слой | src/backend.fth:186 |
| `cc-new-record` | слой: новый слой в ячейке | src/backend.fth:148 |
| `cc-lone` | слой: отдельный слой в новой ячейке | src/backend.fth:152 |
| `cc-layer` | слой: следующий слой последовательности | src/backend.fth:155 |

## Слова ядра

Вид: генератор (слово словаря, исполняемое при компиляции, `doc/generators.md`; в пояснении слово компилятора), определение `:`, переменная, константа, данные `create`, цифра (литерал, `doc/literals.md`), основание. «Исп.» — число ссылок из других слов (цифры — и из чисел определения). Повторное определение имени — «вариант N» (старое имя остаётся у прежних ссылок).

| № | Слово | Вид | Файл:строка | Исп. | Пояснение |
|---|---|---|---|---|---|
| 1 | `nip` | определение `:` | src/prelude.fth:6 | 25 |  |
| 2 | `tuck` | определение `:` | src/prelude.fth:7 | 9 |  |
| 3 | `-rot` | определение `:` | src/prelude.fth:8 | 3 |  |
| 4 | `2dup` | определение `:` | src/prelude.fth:9 | 10 |  |
| 5 | `2drop` | определение `:` | src/prelude.fth:10 | 23 |  |
| 6 | `2swap` | определение `:` | src/prelude.fth:11 | 6 |  |
| 7 | `2over` | определение `:` | src/prelude.fth:12 | 2 |  |
| 8 | `?dup` | определение `:` | src/prelude.fth:13 | 20 |  |
| 9 | `negate` | определение `:` | src/prelude.fth:14 | 5 |  |
| 10 | `invert` | определение `:` | src/prelude.fth:15 | 1 |  |
| 11 | `>` | определение `:` | src/prelude.fth:16 | 10 |  |
| 12 | `u>` | определение `:` | src/prelude.fth:17 | 6 |  |
| 13 | `<>` | определение `:` | src/prelude.fth:18 | 12 |  |
| 14 | `0<` | определение `:` | src/prelude.fth:19 | 5 |  |
| 15 | `0>` | определение `:` | src/prelude.fth:20 | 3 |  |
| 16 | `0<>` | определение `:` | src/prelude.fth:21 | 4 |  |
| 17 | `max` | определение `:` | src/prelude.fth:22 | 20 |  |
| 18 | `min` | определение `:` | src/prelude.fth:23 | 5 |  |
| 19 | `+!` | определение `:` | src/prelude.fth:24 | 65 |  |
| 20 | `2@` | определение `:` | src/prelude.fth:25 | 4 |  |
| 21 | `2!` | определение `:` | src/prelude.fth:26 | 2 |  |
| 22 | `fill-cell` | переменная | src/prelude.fth:28 | 2 |  |
| 23 | `fill` | определение `:` | src/prelude.fth:29 | 11 |  |
| 24 | `cmove` | определение `:` | src/prelude.fth:33 | 18 |  |
| 25 | `cmove>` | определение `:` | src/prelude.fth:37 | 1 |  |
| 26 | `/string` | определение `:` | src/prelude.fth:38 | 2 |  |
| 27 | `type` | определение `:` | src/prelude.fth:39 | 6 |  |
| 28 | `compare` | определение `:` | src/prelude.fth:40 | 2 |  |
| 29 | `heap-ptr` | переменная | src/prelude.fth:44 | 5 |  |
| 30 | `heap-last` | переменная | src/prelude.fth:44 | 2 |  |
| 31 | `heap-end` | константа | src/prelude.fth:44 | 1 |  |
| 32 | `allocate` | определение `:` | src/prelude.fth:45 | 17 |  |
| 33 | `free` | определение `:` | src/prelude.fth:48 | 5 |  |
| 34 | `source` | определение `:` | src/prelude.fth:50 | 2 |  |
| 35 | `>in` | переменная | src/prelude.fth:51 | 2 |  |
| 36 | `cc-size` | переменная | src/backend.fth:14 | 9 |  |
| 37 | `cc-a` | переменная | src/backend.fth:14 | 15 |  |
| 38 | `cc-slots` | переменная | src/backend.fth:14 | 14 |  |
| 39 | `cc-cell-bits` | переменная | src/backend.fth:14 | 13 |  |
| 40 | `cc-chunk` | переменная | src/backend.fth:15 | 8 |  |
| 41 | `cc-chunk-buf` | переменная | src/backend.fth:15 | 6 |  |
| 42 | `cc-lbuf` | переменная | src/backend.fth:15 | 6 |  |
| 43 | `cc-pool` | переменная | src/backend.fth:15 | 5 |  |
| 44 | `cc-ebuf` | переменная | src/backend.fth:16 | 4 |  |
| 45 | `cc-dest` | переменная | src/backend.fth:16 | 6 |  |
| 46 | `cc-sink` | переменная | src/backend.fth:16 | 5 |  |
| 47 | `cc-start-cell` | переменная | src/backend.fth:16 | 3 |  |
| 48 | `cc-rev` | данные `create` | src/backend.fth:18 | 10 |  |
| 49 | `cc-rev-init` | определение `:` | src/backend.fth:19 | 1 |  |
| 50 | `cc-inst` | определение `:` | src/backend.fth:23 | 8 |  |
| 51 | `cc-layer-bits` | определение `:` | src/backend.fth:24 | 9 |  |
| 52 | `cc-lbytes` | определение `:` | src/backend.fth:25 | 6 |  |
| 53 | `cc-stdin` | определение `:` | src/backend.fth:26 | 3 |  |
| 54 | `cc-stdout` | определение `:` | src/backend.fth:27 | 2 |  |
| 55 | `cc-bits` | определение `:` | src/backend.fth:28 | 3 |  |
| 56 | `cc-numeric` | определение `:` | src/backend.fth:29 | 9 |  |
| 57 | `cc-numeric4` | определение `:` | src/backend.fth:35 | 1 |  |
| 58 | `cc-field-check` | определение `:` | src/backend.fth:38 | 1 |  |
| 59 | `cc-encode` | определение `:` | src/backend.fth:41 | 3 |  |
| 60 | `cc-start` | переменная | src/backend.fth:51 | 8 |  |
| 61 | `cc-len` | переменная | src/backend.fth:51 | 10 |  |
| 62 | `cc-rows` | данные `create` | src/backend.fth:52 | 6 |  |
| 63 | `cc-row!` | определение `:` | src/backend.fth:53 | 7 |  |
| 64 | `cc-clear-rows` | определение `:` | src/backend.fth:55 | 3 |  |
| 65 | `cc-loader` | определение `:` | src/backend.fth:56 | 1 |  |
| 66 | `cc-stream-flush` | определение `:` | src/backend.fth:63 | 3 |  |
| 67 | `cc-begin-chunk` | определение `:` | src/backend.fth:67 | 2 |  |
| 68 | `cc-put` | определение `:` | src/backend.fth:69 | 14 |  |
| 69 | `cc-scratch` | данные `create` | src/backend.fth:87 | 2 |  |
| 70 | `cc-put-numeric` | определение `:` | src/backend.fth:88 | 3 |  |
| 71 | `cc-max-layers` | константа | src/backend.fth:93 | 4 |  |
| 72 | `cc-record` | определение `:` | src/backend.fth:94 | 2 |  |
| 73 | `cc-pending` | переменная | src/backend.fth:95 | 10 |  |
| 74 | `cc-head` | переменная | src/backend.fth:95 | 6 |  |
| 75 | `cc-next-cell` | переменная | src/backend.fth:95 | 7 |  |
| 76 | `cc-seq#` | переменная | src/backend.fth:96 | 8 |  |
| 77 | `cc-seq-first` | переменная | src/backend.fth:96 | 3 |  |
| 78 | `cc-seq-entry` | переменная | src/backend.fth:96 | 2 |  |
| 79 | `cc-seq-last` | переменная | src/backend.fth:96 | 2 |  |
| 80 | `cc-foff` | данные `create` | src/backend.fth:98 | 2 |  |
| 81 | `cc-foff-init` | определение `:` | src/backend.fth:99 | 1 |  |
| 82 | `cc-machine` | определение `:` | src/backend.fth:100 | 1 |  |
| 83 | `cc-field` | определение `:` | src/backend.fth:117 | 38 |  |
| 84 | `cc-link-row` | основание | src/backend.fth:118 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 85 | `cc-copy` | основание | src/backend.fth:119 | 74 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 86 | `cc-builder` | определение `:` | src/backend.fth:121 | 1 |  |
| 87 | `cc-new-cell` | определение `:` | src/backend.fth:122 | 13 |  |
| 88 | `cc-branch-bit` | определение `:` | src/backend.fth:125 | 14 |  |
| 89 | `cc-branch-step` | определение `:` | src/backend.fth:126 | 4 |  |
| 90 | `cc-group` | определение `:` | src/backend.fth:128 | 6 |  |
| 91 | `cc-layer-cell` | определение `:` | src/backend.fth:131 | 39 |  |
| 92 | `cc-next!` | определение `:` | src/backend.fth:132 | 20 |  |
| 93 | `cc-count` | определение `:` | src/backend.fth:133 | 7 |  |
| 94 | `cc-row-addr` | определение `:` | src/backend.fth:134 | 4 |  |
| 95 | `cc-pending@` | определение `:` | src/backend.fth:135 | 5 |  |
| 96 | `cc-encode-layer` | определение `:` | src/backend.fth:136 | 1 |  |
| 97 | `cc-on-write` | переменная | src/backend.fth:143 | 6 |  |
| 98 | `cc-write` | определение `:` | src/backend.fth:144 | 2 |  |
| 99 | `cc-write-oldest` | определение `:` | src/backend.fth:147 | 1 |  |
| 100 | `cc-new-record` | основание | src/backend.fth:148 | 10 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 101 | `cc-lone` | основание | src/backend.fth:152 | 5 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 102 | `cc-seq` | определение `:` | src/backend.fth:153 | 9 |  |
| 103 | `cc-last` | определение `:` | src/backend.fth:154 | 5 |  |
| 104 | `cc-layer` | основание | src/backend.fth:155 | 79 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 105 | `cc-entry` | определение `:` | src/backend.fth:160 | 4 |  |
| 106 | `cc-jump` | определение `:` | src/backend.fth:161 | 12 |  |
| 107 | `cc-l1` | переменная | src/backend.fth:162 | 4 |  |
| 108 | `cc-h1` | переменная | src/backend.fth:162 | 3 |  |
| 109 | `cc-l2` | переменная | src/backend.fth:162 | 4 |  |
| 110 | `cc-h2` | переменная | src/backend.fth:162 | 3 |  |
| 111 | `cc-ra` | переменная | src/backend.fth:163 | 2 |  |
| 112 | `cc-rb` | переменная | src/backend.fth:163 | 2 |  |
| 113 | `cc-cur` | переменная | src/backend.fth:163 | 7 |  |
| 114 | `cc-clash?` | определение `:` | src/backend.fth:165 | 1 |  |
| 115 | `cc-row-clash?` | определение `:` | src/backend.fth:170 | 1 |  |
| 116 | `cc-new-row` | данные `create` | src/backend.fth:175 | 6 |  |
| 117 | `cc-row-set` | определение `:` | src/backend.fth:176 | 2 |  |
| 118 | `cc-full?` | определение `:` | src/backend.fth:178 | 2 |  |
| 119 | `cc-clashes?` | определение `:` | src/backend.fth:179 | 2 |  |
| 120 | `cc-fits?` | определение `:` | src/backend.fth:184 | 2 |  |
| 121 | `cc-row` | основание | src/backend.fth:186 | 74 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 122 | `cc-flush` | определение `:` | src/backend.fth:190 | 13 |  |
| 123 | `cc-finish` | определение `:` | src/backend.fth:193 | 1 |  |
| 124 | `cc-t1` | переменная | src/compute.fth:10 | 25 |  |
| 125 | `cc-t2` | переменная | src/compute.fth:10 | 13 |  |
| 126 | `cc-t3` | переменная | src/compute.fth:10 | 7 |  |
| 127 | `cc-t4` | переменная | src/compute.fth:10 | 4 |  |
| 128 | `cc-t5` | переменная | src/compute.fth:10 | 8 |  |
| 129 | `cc-lo` | переменная | src/compute.fth:11 | 5 |  |
| 130 | `cc-hi` | переменная | src/compute.fth:11 | 2 |  |
| 131 | `cc-l0` | переменная | src/compute.fth:12 | 21 |  |
| 132 | `cc-l1` | переменная | src/compute.fth:12 | 13 | вариант 2 |
| 133 | `cc-l2` | переменная | src/compute.fth:12 | 8 | вариант 2 |
| 134 | `cc-l3` | переменная | src/compute.fth:12 | 7 |  |
| 135 | `cc-l4` | переменная | src/compute.fth:12 | 7 |  |
| 136 | `cc-l5` | переменная | src/compute.fth:12 | 6 |  |
| 137 | `cc-work` | определение `:` | src/compute.fth:13 | 3 |  |
| 138 | `cc-cell-bit` | определение `:` | src/compute.fth:14 | 1 |  |
| 139 | `cc-link-slot` | определение `:` | src/compute.fth:15 | 6 |  |
| 140 | `cc-item-cells` | константа | src/compute.fth:17 | 1 |  |
| 141 | `cc-max-items` | константа | src/compute.fth:17 | 2 |  |
| 142 | `cc-items` | данные `create` | src/compute.fth:18 | 1 |  |
| 143 | `cc-nitems` | переменная | src/compute.fth:19 | 8 |  |
| 144 | `cc-item@` | определение `:` | src/compute.fth:20 | 6 |  |
| 145 | `cc-lookups-begin` | определение `:` | src/compute.fth:21 | 14 |  |
| 146 | `cc-item` | определение `:` | src/compute.fth:22 | 12 |  |
| 147 | `cc-seg` | определение `:` | src/compute.fth:27 | 18 |  |
| 148 | `cc-sl` | данные `create` | src/compute.fth:33 | 2 |  |
| 149 | `cc-sh` | данные `create` | src/compute.fth:33 | 2 |  |
| 150 | `cc-read-layer` | данные `create` | src/compute.fth:34 | 2 |  |
| 151 | `cc-read-slot` | данные `create` | src/compute.fth:34 | 2 |  |
| 152 | `cc-used` | данные `create` | src/compute.fth:35 | 2 |  |
| 153 | `cc-nused` | переменная | src/compute.fth:35 | 5 |  |
| 154 | `cc-rl` | переменная | src/compute.fth:35 | 6 |  |
| 155 | `cc-pk` | переменная | src/compute.fth:35 | 4 |  |
| 156 | `cc-pkl` | переменная | src/compute.fth:35 | 4 |  |
| 157 | `cc-npatches` | определение `:` | src/compute.fth:36 | 1 |  |
| 158 | `cc-used?` | определение `:` | src/compute.fth:37 | 1 |  |
| 159 | `cc-place-reads` | определение `:` | src/compute.fth:39 | 1 |  |
| 160 | `cc-patch` | определение `:` | src/compute.fth:51 | 1 |  |
| 161 | `cc-lookups` | определение `:` | src/compute.fth:60 | 14 |  |
| 162 | `cc-al` | данные `create` | src/compute.fth:67 | 2 |  |
| 163 | `cc-ar` | данные `create` | src/compute.fth:67 | 2 |  |
| 164 | `cc-ax` | переменная | src/compute.fth:68 | 4 |  |
| 165 | `cc-aa` | переменная | src/compute.fth:68 | 2 |  |
| 166 | `cc-ab` | переменная | src/compute.fth:68 | 2 |  |
| 167 | `cc-atab` | переменная | src/compute.fth:68 | 2 |  |
| 168 | `cc-acarry` | переменная | src/compute.fth:68 | 2 |  |
| 169 | `cc-al@` | определение `:` | src/compute.fth:69 | 8 |  |
| 170 | `cc-rd` | определение `:` | src/compute.fth:70 | 3 |  |
| 171 | `cc-adder-patch` | определение `:` | src/compute.fth:71 | 4 |  |
| 172 | `cc-adder` | определение `:` | src/compute.fth:76 | 5 |  |
| 173 | `cc-dsrc` | переменная | src/compute.fth:93 | 3 |  |
| 174 | `cc-dk` | переменная | src/compute.fth:93 | 5 |  |
| 175 | `cc-dg` | переменная | src/compute.fth:93 | 3 |  |
| 176 | `cc-dp` | переменная | src/compute.fth:93 | 3 |  |
| 177 | `cc-dx` | переменная | src/compute.fth:93 | 4 |  |
| 178 | `cc-decide` | определение `:` | src/compute.fth:94 | 2 |  |
| 179 | `cc-table-at` | переменная | src/compute.fth:102 | 4 |  |
| 180 | `cc-table-limit` | переменная | src/compute.fth:102 | 2 |  |
| 181 | `cc-tbuf` | переменная | src/compute.fth:102 | 8 |  |
| 182 | `cc-tx` | переменная | src/compute.fth:103 | 8 |  |
| 183 | `cc-tbits` | переменная | src/compute.fth:103 | 5 |  |
| 184 | `cc-ts` | переменная | src/compute.fth:103 | 6 |  |
| 185 | `cc-tsize` | переменная | src/compute.fth:103 | 7 |  |
| 186 | `cc-tbase` | переменная | src/compute.fth:103 | 4 |  |
| 187 | `cc-tper` | переменная | src/compute.fth:103 | 4 |  |
| 188 | `cc-tables` | определение `:` | src/compute.fth:104 | 2 |  |
| 189 | `cc-table-area` | определение `:` | src/compute.fth:105 | 3 |  |
| 190 | `cc-table-done` | определение `:` | src/compute.fth:113 | 3 |  |
| 191 | `cc-table` | определение `:` | src/compute.fth:116 | 24 |  |
| 192 | `cc-table2` | определение `:` | src/compute.fth:134 | 1 |  |
| 193 | `cc-add-entry` | определение `:` | src/compute.fth:141 | 1 |  |
| 194 | `cc-sub-entry` | определение `:` | src/compute.fth:143 | 2 |  |
| 195 | `cc-xor-entry` | определение `:` | src/compute.fth:145 | 1 |  |
| 196 | `cc-or-entry` | определение `:` | src/compute.fth:146 | 1 |  |
| 197 | `cc-and-entry` | определение `:` | src/compute.fth:147 | 1 |  |
| 198 | `cc-or8-entry` | определение `:` | src/compute.fth:148 | 2 |  |
| 199 | `cc-fz` | переменная | src/compute.fth:149 | 3 |  |
| 200 | `cc-fu` | переменная | src/compute.fth:149 | 4 |  |
| 201 | `cc-fs` | переменная | src/compute.fth:149 | 3 |  |
| 202 | `cc-pair` | определение `:` | src/compute.fth:150 | 6 |  |
| 203 | `cc-flags-entry` | определение `:` | src/compute.fth:151 | 1 |  |
| 204 | `cc-not5-entry` | определение `:` | src/compute.fth:158 | 1 |  |
| 205 | `cc-sign-entry` | определение `:` | src/compute.fth:159 | 1 |  |
| 206 | `cc-fill24-entry` | определение `:` | src/compute.fth:160 | 1 |  |
| 207 | `cc-fill16-entry` | определение `:` | src/compute.fth:161 | 1 |  |
| 208 | `cc-inc1-entry` | определение `:` | src/compute.fth:162 | 1 |  |
| 209 | `cc-inc2-entry` | определение `:` | src/compute.fth:163 | 1 |  |
| 210 | `cc-t-add` | переменная | src/compute.fth:164 | 6 |  |
| 211 | `cc-t-sub` | переменная | src/compute.fth:164 | 5 |  |
| 212 | `cc-t-xor` | переменная | src/compute.fth:164 | 5 |  |
| 213 | `cc-t-or` | переменная | src/compute.fth:164 | 2 |  |
| 214 | `cc-t-and` | переменная | src/compute.fth:164 | 2 |  |
| 215 | `cc-t-or8` | переменная | src/compute.fth:165 | 3 |  |
| 216 | `cc-t-flags` | переменная | src/compute.fth:165 | 2 |  |
| 217 | `cc-t-not5` | переменная | src/compute.fth:165 | 2 |  |
| 218 | `cc-t-sign32` | переменная | src/compute.fth:165 | 2 |  |
| 219 | `cc-t-fill24` | переменная | src/compute.fth:166 | 1 |  |
| 220 | `cc-t-fill16` | переменная | src/compute.fth:166 | 1 |  |
| 221 | `cc-t-inc1` | переменная | src/compute.fth:166 | 1 |  |
| 222 | `cc-t-inc2` | переменная | src/compute.fth:166 | 1 |  |
| 223 | `cc-standard-tables` | определение `:` | src/compute.fth:167 | 1 |  |
| 224 | `cc-oo` | переменная | src/compute.fth:176 | 2 |  |
| 225 | `cc-os` | переменная | src/compute.fth:176 | 2 |  |
| 226 | `cc-ol` | переменная | src/compute.fth:176 | 4 |  |
| 227 | `cc-oh` | переменная | src/compute.fth:176 | 3 |  |
| 228 | `cc-or-chunks` | определение `:` | src/compute.fth:177 | 3 |  |
| 229 | `cc-cr` | переменная | src/compute.fth:183 | 5 |  |
| 230 | `cc-ca` | переменная | src/compute.fth:183 | 4 |  |
| 231 | `cc-cb` | переменная | src/compute.fth:183 | 4 |  |
| 232 | `cc-logic` | определение `:` | src/compute.fth:190 | 4 |  |
| 233 | `cc-sres` | переменная | src/compute.fth:196 | 3 |  |
| 234 | `cc-sa` | переменная | src/compute.fth:196 | 7 |  |
| 235 | `cc-samt` | переменная | src/compute.fth:196 | 8 |  |
| 236 | `cc-sw` | переменная | src/compute.fth:196 | 9 |  |
| 237 | `cc-szero` | переменная | src/compute.fth:196 | 4 |  |
| 238 | `cc-sarg` | переменная | src/compute.fth:197 | 6 |  |
| 239 | `cc-sign` | переменная | src/compute.fth:197 | 6 |  |
| 240 | `cc-shift-row` | определение `:` | src/compute.fth:198 | 3 |  |
| 241 | `cc-shift-patch` | определение `:` | src/compute.fth:199 | 6 |  |
| 242 | `cc-shift-right` | определение `:` | src/compute.fth:201 | 1 |  |
| 243 | `cc-shift-left` | определение `:` | src/compute.fth:218 | 1 |  |
| 244 | `fc-size` | константа | src/forthc.fth:11 | 2 |  |
| 245 | `fc-cellb` | константа | src/forthc.fth:11 | 7 |  |
| 246 | `fc-l` | константа | src/forthc.fth:11 | 1 |  |
| 247 | `fc-a` | константа | src/forthc.fth:11 | 3 |  |
| 248 | `fc-d` | переменная | src/forthc.fth:16 | 2 |  |
| 249 | `fc-first` | переменная | src/forthc.fth:16 | 2 |  |
| 250 | `fc-guard` | переменная | src/forthc.fth:19 | 11 |  |
| 251 | `fc-layout` | определение `:` | src/forthc.fth:20 | 1 |  |
| 252 | `fc-d+` | определение `:` | src/forthc.fth:22 | 29 |  |
| 253 | `fc-sp` | определение `:` | src/forthc.fth:23 | 6 |  |
| 254 | `fc-rp` | определение `:` | src/forthc.fth:23 | 18 |  |
| 255 | `fc-handler` | определение `:` | src/forthc.fth:23 | 6 |  |
| 256 | `fc-code` | определение `:` | src/forthc.fth:23 | 5 |  |
| 257 | `fc-regs` | определение `:` | src/forthc.fth:24 | 2 |  |
| 258 | `fc-nregs` | константа | src/forthc.fth:24 | 2 |  |
| 259 | `fc-tmp` | определение `:` | src/forthc.fth:25 | 10 |  |
| 260 | `fc-xr` | определение `:` | src/forthc.fth:25 | 10 |  |
| 261 | `fc-z` | определение `:` | src/forthc.fth:25 | 7 |  |
| 262 | `fc-idx` | определение `:` | src/forthc.fth:25 | 4 |  |
| 263 | `fc-flt` | определение `:` | src/forthc.fth:26 | 4 |  |
| 264 | `fc-ma` | определение `:` | src/forthc.fth:27 | 6 |  |
| 265 | `fc-mb` | определение `:` | src/forthc.fth:27 | 6 |  |
| 266 | `fc-mp` | определение `:` | src/forthc.fth:27 | 2 |  |
| 267 | `fc-mq` | определение `:` | src/forthc.fth:27 | 3 |  |
| 268 | `fc-mr` | определение `:` | src/forthc.fth:27 | 3 |  |
| 269 | `fc-zero` | определение `:` | src/forthc.fth:28 | 12 |  |
| 270 | `fc-consts` | определение `:` | src/forthc.fth:28 | 3 |  |
| 271 | `fc-mark` | определение `:` | src/forthc.fth:29 | 2 |  |
| 272 | `fc-sw` | определение `:` | src/forthc.fth:30 | 2 |  |
| 273 | `fc-su` | определение `:` | src/forthc.fth:30 | 1 |  |
| 274 | `fc-key` | определение `:` | src/forthc.fth:30 | 3 |  |
| 275 | `fc-bp` | определение `:` | src/forthc.fth:30 | 2 |  |
| 276 | `fc-tab` | определение `:` | src/forthc.fth:31 | 1 |  |
| 277 | `fc-stk` | определение `:` | src/forthc.fth:31 | 3 |  |
| 278 | `fc-rstk` | определение `:` | src/forthc.fth:32 | 14 |  |
| 279 | `fc-scr0` | определение `:` | src/forthc.fth:32 | 1 |  |
| 280 | `fc-links` | определение `:` | src/forthc.fth:33 | 2 |  |
| 281 | `fc-max-links` | константа | src/forthc.fth:33 | 1 |  |
| 282 | `fc-link-chunk` | константа | src/forthc.fth:33 | 2 |  |
| 283 | `fc-mem` | определение `:` | src/forthc.fth:34 | 5 |  |
| 284 | `fc-mw` | константа | src/forthc.fth:34 | 5 |  |
| 285 | `fc-htab` | определение `:` | src/forthc.fth:34 | 1 |  |
| 286 | `fc-data-start` | константа | src/forthc.fth:35 | 1 |  |
| 287 | `fc-off` | данные `create` | src/forthc.fth:38 | 2 |  |
| 288 | `fc-oc` | переменная | src/forthc.fth:38 | 2 |  |
| 289 | `fc-t-rev8` | переменная | src/forthc.fth:39 | 3 |  |
| 290 | `fc-t-zero32` | переменная | src/forthc.fth:39 | 2 |  |
| 291 | `fc-t-nz2` | переменная | src/forthc.fth:39 | 2 |  |
| 292 | `fc-t-lt32` | переменная | src/forthc.fth:39 | 2 |  |
| 293 | `fc-t-or8b` | переменная | src/forthc.fth:40 | 2 |  |
| 294 | `fc-t-fault` | переменная | src/forthc.fth:40 | 2 |  |
| 295 | `fc-t-xr2` | переменная | src/forthc.fth:40 | 2 |  |
| 296 | `fc-t-ult32` | переменная | src/forthc.fth:40 | 2 |  |
| 297 | `fc-t-bytepos` | переменная | src/forthc.fth:40 | 2 |  |
| 298 | `fc-off@` | определение `:` | src/forthc.fth:41 | 3 |  |
| 299 | `fc-off-table` | определение `:` | src/forthc.fth:43 | 1 |  |
| 300 | `fc-rev-entry` | определение `:` | src/forthc.fth:46 | 1 |  |
| 301 | `fc-zero-entry` | определение `:` | src/forthc.fth:47 | 1 |  |
| 302 | `fc-nz-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 303 | `fc-lt-entry` | определение `:` | src/forthc.fth:49 | 1 |  |
| 304 | `fc-fault-entry` | определение `:` | src/forthc.fth:52 | 1 |  |
| 305 | `fc-xr2-entry` | определение `:` | src/forthc.fth:55 | 1 |  |
| 306 | `fc-ult-entry` | определение `:` | src/forthc.fth:56 | 1 |  |
| 307 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:58 | 1 |  |
| 308 | `fc-tables` | определение `:` | src/forthc.fth:59 | 1 |  |
| 309 | `fc-mul4-entry` | определение `:` | src/forthc.fth:72 | 1 |  |
| 310 | `fc-qsel-entry` | определение `:` | src/forthc.fth:75 | 1 |  |
| 311 | `fc-max-consts` | переменная | src/forthc.fth:80 | 5 | вход бута (хост) |
| 312 | `fc-ck` | переменная | src/forthc.fth:80 | 3 |  |
| 313 | `fc-nconsts` | переменная | src/forthc.fth:80 | 7 |  |
| 314 | `fc-nbuckets` | переменная | src/forthc.fth:81 | 9 | вход бута (хост) |
| 315 | `fc-cbk` | переменная | src/forthc.fth:81 | 3 |  |
| 316 | `fc-ck@` | определение `:` | src/forthc.fth:82 | 3 |  |
| 317 | `fc-chash` | определение `:` | src/forthc.fth:83 | 1 |  |
| 318 | `fc-cb` | переменная | src/forthc.fth:84 | 3 |  |
| 319 | `fc-const2` | определение `:` | src/forthc.fth:85 | 1 |  |
| 320 | `fc-const` | определение `:` | src/forthc.fth:95 | 4 |  |
| 321 | `fc-lit` | определение `:` | src/forthc.fth:103 | 3 |  |
| 322 | `fc-bit0` | определение `:` | src/forthc.fth:104 | 1 |  |
| 323 | `fc-bit1` | определение `:` | src/forthc.fth:105 | 1 |  |
| 324 | `fc-length` | определение `:` | src/forthc.fth:106 | 1 |  |
| 325 | `fc-lit-of` | определение `:` | src/forthc.fth:107 | 2 |  |
| 326 | `fc-load` | определение `:` | src/forthc.fth:111 | 2 |  |
| 327 | `fc-nlinks` | переменная | src/forthc.fth:115 | 5 |  |
| 328 | `fc-link-buf` | переменная | src/forthc.fth:115 | 4 |  |
| 329 | `fc-nbuf` | переменная | src/forthc.fth:115 | 8 |  |
| 330 | `fc-put-links` | определение `:` | src/forthc.fth:116 | 2 |  |
| 331 | `fc-link-const` | определение `:` | src/forthc.fth:120 | 4 |  |
| 332 | `fc-eight` | данные `create` | src/forthc.fth:125 | 7 |  |
| 333 | `fc-zeros` | данные `create` | src/forthc.fth:125 | 5 |  |
| 334 | `fc-put-consts` | определение `:` | src/forthc.fth:126 | 1 |  |
| 335 | `fc-cache` | данные `create` | src/forthc.fth:134 | 8 |  |
| 336 | `fc-n` | переменная | src/forthc.fth:134 | 31 |  |
| 337 | `fc-pin` | данные `create` | src/forthc.fth:135 | 10 |  |
| 338 | `fc-npin` | переменная | src/forthc.fth:135 | 21 |  |
| 339 | `fc-c@` | определение `:` | src/forthc.fth:136 | 8 |  |
| 340 | `fc-push` | определение `:` | src/forthc.fth:137 | 30 |  |
| 341 | `fc-pop1` | определение `:` | src/forthc.fth:138 | 32 |  |
| 342 | `fc-in?` | определение `:` | src/forthc.fth:139 | 3 |  |
| 343 | `fc-reg` | определение `:` | src/forthc.fth:140 | 18 |  |
| 344 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:145 | 1 |  |
| 345 | `fc-scr` | переменная | src/forthc.fth:146 | 3 |  |
| 346 | `fc-scratch` | определение `:` | src/forthc.fth:147 | 11 |  |
| 347 | `fc-offs` | данные `create` | src/forthc.fth:151 | 5 |  |
| 348 | `fc-noff` | переменная | src/forthc.fth:151 | 9 |  |
| 349 | `fc-ptr` | переменная | src/forthc.fth:151 | 4 |  |
| 350 | `fc-adjust` | определение `:` | src/forthc.fth:153 | 7 |  |
| 351 | `fc-prow` | данные `create` | src/forthc.fth:159 | 2 |  |
| 352 | `fc-nrow` | переменная | src/forthc.fth:159 | 8 |  |
| 353 | `fc-pl` | данные `create` | src/forthc.fth:160 | 2 |  |
| 354 | `fc-pslot` | данные `create` | src/forthc.fth:160 | 2 |  |
| 355 | `fc-rl` | переменная | src/forthc.fth:161 | 3 |  |
| 356 | `fc-f0` | переменная | src/forthc.fth:161 | 2 |  |
| 357 | `fc-f1` | переменная | src/forthc.fth:161 | 2 |  |
| 358 | `fc-psh` | переменная | src/forthc.fth:161 | 2 |  |
| 359 | `fc-row+` | определение `:` | src/forthc.fth:162 | 3 |  |
| 360 | `fc-4@` | определение `:` | src/forthc.fth:164 | 3 |  |
| 361 | `fc-patched` | определение `:` | src/forthc.fth:166 | 3 |  |
| 362 | `fc-popped` | данные `create` | src/forthc.fth:178 | 2 |  |
| 363 | `fc-srcs` | данные `create` | src/forthc.fth:178 | 16 |  |
| 364 | `fc-nsrc` | переменная | src/forthc.fth:178 | 21 |  |
| 365 | `fc-mbase` | переменная | src/forthc.fth:179 | 8 |  |
| 366 | `fc-mptr` | переменная | src/forthc.fth:179 | 4 |  |
| 367 | `fc-mn` | переменная | src/forthc.fth:179 | 7 |  |
| 368 | `fc-mw2` | переменная | src/forthc.fth:179 | 6 |  |
| 369 | `fc-popped@` | определение `:` | src/forthc.fth:180 | 10 |  |
| 370 | `fc-shift` | определение `:` | src/forthc.fth:181 | 4 |  |
| 371 | `fc-mem-pop` | определение `:` | src/forthc.fth:182 | 5 |  |
| 372 | `fc-push-group` | определение `:` | src/forthc.fth:190 | 2 |  |
| 373 | `fc-dup-at` | определение `:` | src/forthc.fth:198 | 1 |  |
| 374 | `fc-rest` | данные `create` | src/forthc.fth:200 | 2 |  |
| 375 | `fc-nrest` | переменная | src/forthc.fth:200 | 3 |  |
| 376 | `fc-mem-push` | определение `:` | src/forthc.fth:201 | 8 |  |
| 377 | `fc-src1` | определение `:` | src/forthc.fth:207 | 3 |  |
| 378 | `fc-need` | определение `:` | src/forthc.fth:209 | 15 |  |
| 379 | `fc-spill` | определение `:` | src/forthc.fth:216 | 19 |  |
| 380 | `fc-pop` | определение `:` | src/forthc.fth:222 | 13 |  |
| 381 | `fc-max-log` | константа | src/forthc.fth:230 | 2 |  |
| 382 | `fc-max-notes` | константа | src/forthc.fth:230 | 6 |  |
| 383 | `fc-log` | переменная | src/forthc.fth:231 | 3 |  |
| 384 | `fc-nlog` | переменная | src/forthc.fth:231 | 5 |  |
| 385 | `fc-decs` | переменная | src/forthc.fth:231 | 2 |  |
| 386 | `fc-ndec` | переменная | src/forthc.fth:231 | 6 |  |
| 387 | `fc-calls` | переменная | src/forthc.fth:231 | 2 |  |
| 388 | `fc-ncall` | переменная | src/forthc.fth:231 | 6 |  |
| 389 | `fc-pend` | переменная | src/forthc.fth:232 | 2 |  |
| 390 | `fc-npend` | переменная | src/forthc.fth:232 | 9 |  |
| 391 | `fc-unknown` | переменная | src/forthc.fth:232 | 7 |  |
| 392 | `fc-lc` | переменная | src/forthc.fth:233 | 3 |  |
| 393 | `fc-lb` | переменная | src/forthc.fth:233 | 3 |  |
| 394 | `fc-row-n` | определение `:` | src/forthc.fth:236 | 1 |  |
| 395 | `fc-mem-row?` | определение `:` | src/forthc.fth:237 | 1 |  |
| 396 | `fc-log-layer` | определение `:` | src/forthc.fth:238 | 2 |  |
| 397 | `fc-log-begin` | определение `:` | src/forthc.fth:249 | 3 |  |
| 398 | `fc-log-end` | определение `:` | src/forthc.fth:251 | 4 |  |
| 399 | `fc-by-execution` | определение `:` | src/forthc.fth:253 | 8 |  |
| 400 | `fc-dec@` | определение `:` | src/forthc.fth:254 | 2 |  |
| 401 | `fc-call@` | определение `:` | src/forthc.fth:255 | 2 |  |
| 402 | `fc-log-decision` | определение `:` | src/forthc.fth:257 | 3 |  |
| 403 | `fc-log-call` | определение `:` | src/forthc.fth:263 | 2 |  |
| 404 | `fc-callee` | переменная | src/forthc.fth:267 | 4 |  |
| 405 | `fc-live` | переменная | src/forthc.fth:270 | 8 |  |
| 406 | `fc-tramp` | переменная | src/forthc.fth:270 | 6 |  |
| 407 | `fc-ex` | переменная | src/forthc.fth:270 | 4 |  |
| 408 | `fc-thrower` | переменная | src/forthc.fth:270 | 5 |  |
| 409 | `fc-jump` | определение `:` | src/forthc.fth:271 | 7 |  |
| 410 | `fc-end` | определение `:` | src/forthc.fth:272 | 14 |  |
| 411 | `fc-begin-block` | определение `:` | src/forthc.fth:274 | 24 |  |
| 412 | `fc-rows1` | определение `:` | src/forthc.fth:278 | 16 |  |
| 413 | `fc-nonzero` | определение `:` | src/forthc.fth:279 | 2 |  |
| 414 | `fc-branch` | определение `:` | src/forthc.fth:282 | 6 |  |
| 415 | `fc-call` | определение `:` | src/forthc.fth:284 | 4 |  |
| 416 | `fc-v0` | переменная | src/forthc.fth:288 | 2 |  |
| 417 | `fc-v1` | переменная | src/forthc.fth:288 | 2 |  |
| 418 | `fc-call-indirect` | определение `:` | src/forthc.fth:289 | 2 |  |
| 419 | `fc-push-frame` | определение `:` | src/forthc.fth:296 | 2 |  |
| 420 | `fc-restore` | определение `:` | src/forthc.fth:299 | 3 |  |
| 421 | `fc-build-thrower` | определение `:` | src/forthc.fth:301 | 1 |  |
| 422 | `fc-throw` | определение `:` | src/forthc.fth:307 | 1 |  |
| 423 | `fc-catch` | определение `:` | src/forthc.fth:310 | 1 |  |
| 424 | `fc-ret-p` | переменная | src/forthc.fth:319 | 3 |  |
| 425 | `fc-ret-l` | переменная | src/forthc.fth:319 | 4 |  |
| 426 | `fc-ret` | определение `:` | src/forthc.fth:320 | 3 |  |
| 427 | `fc-ca` | переменная | src/forthc.fth:328 | 6 |  |
| 428 | `fc-cl0` | переменная | src/forthc.fth:328 | 5 |  |
| 429 | `fc-cl1` | переменная | src/forthc.fth:328 | 5 |  |
| 430 | `fc-cr` | переменная | src/forthc.fth:328 | 7 |  |
| 431 | `fc-cg` | переменная | src/forthc.fth:328 | 4 |  |
| 432 | `fc-cx` | переменная | src/forthc.fth:328 | 4 |  |
| 433 | `fc-cv` | переменная | src/forthc.fth:329 | 3 |  |
| 434 | `fc-cres` | переменная | src/forthc.fth:329 | 6 |  |
| 435 | `fc-cslot` | переменная | src/forthc.fth:329 | 3 |  |
| 436 | `fc-csh` | переменная | src/forthc.fth:329 | 2 |  |
| 437 | `fc-chk-read` | определение `:` | src/forthc.fth:331 | 4 |  |
| 438 | `fc-chk-seg` | определение `:` | src/forthc.fth:334 | 5 |  |
| 439 | `fc-cmode` | переменная | src/forthc.fth:340 | 9 |  |
| 440 | `fc-ar` | переменная | src/forthc.fth:340 | 7 |  |
| 441 | `fc-as` | переменная | src/forthc.fth:340 | 2 |  |
| 442 | `fc-af` | переменная | src/forthc.fth:340 | 2 |  |
| 443 | `fc-al0` | переменная | src/forthc.fth:340 | 2 |  |
| 444 | `fc-al1` | переменная | src/forthc.fth:340 | 2 |  |
| 445 | `fc-apl` | переменная | src/forthc.fth:341 | 3 |  |
| 446 | `fc-afld` | переменная | src/forthc.fth:341 | 3 |  |
| 447 | `fc-access-patch` | определение `:` | src/forthc.fth:342 | 2 |  |
| 448 | `fc-access` | определение `:` | src/forthc.fth:347 | 1 |  |
| 449 | `fc-width` | определение `:` | src/forthc.fth:349 | 4 |  |
| 450 | `fc-r1l0` | переменная | src/forthc.fth:350 | 2 |  |
| 451 | `fc-r1l1` | переменная | src/forthc.fth:350 | 2 |  |
| 452 | `fc-r1r` | переменная | src/forthc.fth:350 | 2 |  |
| 453 | `fc-check` | определение `:` | src/forthc.fth:353 | 4 |  |
| 454 | `fc-ring` | константа | src/forthc.fth:379 | 6 |  |
| 455 | `fc-window` | константа | src/forthc.fth:379 | 1 |  |
| 456 | `fc-sl` | данные `create` | src/forthc.fth:380 | 2 |  |
| 457 | `fc-stabs` | переменная | src/forthc.fth:380 | 2 |  |
| 458 | `fc-slen` | переменная | src/forthc.fth:381 | 7 |  |
| 459 | `fc-slow` | переменная | src/forthc.fth:381 | 4 |  |
| 460 | `fc-sinit` | определение `:` | src/forthc.fth:382 | 2 |  |
| 461 | `fc-sbegin` | определение `:` | src/forthc.fth:383 | 2 |  |
| 462 | `fc-tabs` | определение `:` | src/forthc.fth:384 | 3 |  |
| 463 | `fc-at` | определение `:` | src/forthc.fth:385 | 4 |  |
| 464 | `fc-has?` | определение `:` | src/forthc.fth:390 | 1 |  |
| 465 | `fc-tab+` | определение `:` | src/forthc.fth:391 | 1 |  |
| 466 | `fc-prw` | данные `create` | src/forthc.fth:392 | 6 |  |
| 467 | `fc-ptab` | переменная | src/forthc.fth:392 | 5 |  |
| 468 | `fc-place` | определение `:` | src/forthc.fth:393 | 3 |  |
| 469 | `fc-scopy` | определение `:` | src/forthc.fth:403 | 9 |  |
| 470 | `fc-segs` | данные `create` | src/forthc.fth:405 | 2 |  |
| 471 | `fc-nseg` | переменная | src/forthc.fth:405 | 5 |  |
| 472 | `fc-pp` | данные `create` | src/forthc.fth:406 | 2 |  |
| 473 | `fc-npp` | переменная | src/forthc.fth:406 | 4 |  |
| 474 | `fc-latest` | переменная | src/forthc.fth:406 | 4 |  |
| 475 | `fc-sga` | переменная | src/forthc.fth:406 | 14 |  |
| 476 | `fc-ltab` | переменная | src/forthc.fth:407 | 3 |  |
| 477 | `fc-ls` | переменная | src/forthc.fth:407 | 3 |  |
| 478 | `fc-lw` | переменная | src/forthc.fth:407 | 3 |  |
| 479 | `fc-ldst` | переменная | src/forthc.fth:407 | 2 |  |
| 480 | `fc-seg+` | определение `:` | src/forthc.fth:408 | 21 |  |
| 481 | `fc-pp+` | определение `:` | src/forthc.fth:411 | 1 |  |
| 482 | `fc-slookup` | определение `:` | src/forthc.fth:412 | 8 |  |
| 483 | `fc-nx` | переменная | src/forthc.fth:431 | 3 |  |
| 484 | `fc-nv` | переменная | src/forthc.fth:431 | 2 |  |
| 485 | `fc-nt` | переменная | src/forthc.fth:431 | 3 |  |
| 486 | `fc-negate-chain` | определение `:` | src/forthc.fth:432 | 1 |  |
| 487 | `fc-gw` | переменная | src/forthc.fth:439 | 4 |  |
| 488 | `fc-gs` | переменная | src/forthc.fth:439 | 2 |  |
| 489 | `fc-gs2` | переменная | src/forthc.fth:439 | 2 |  |
| 490 | `fc-gts` | переменная | src/forthc.fth:439 | 6 |  |
| 491 | `fc-gdst` | переменная | src/forthc.fth:439 | 2 |  |
| 492 | `fc-negate-select` | определение `:` | src/forthc.fth:440 | 4 |  |
| 493 | `fc-sfinish` | определение `:` | src/forthc.fth:445 | 2 |  |
| 494 | `fc-pr` | данные `create` | src/forthc.fth:448 | 2 |  |
| 495 | `fc-xs` | данные `create` | src/forthc.fth:448 | 2 |  |
| 496 | `fc-m4` | переменная | src/forthc.fth:449 | 2 |  |
| 497 | `fc-mj` | переменная | src/forthc.fth:449 | 11 |  |
| 498 | `fc-mk` | переменная | src/forthc.fth:449 | 6 |  |
| 499 | `fc-p@` | определение `:` | src/forthc.fth:450 | 3 |  |
| 500 | `fc-p!` | определение `:` | src/forthc.fth:451 | 1 |  |
| 501 | `fc-x@` | определение `:` | src/forthc.fth:452 | 3 |  |
| 502 | `fc-x!` | определение `:` | src/forthc.fth:453 | 2 |  |
| 503 | `fc-build-mul` | определение `:` | src/forthc.fth:454 | 1 |  |
| 504 | `fc-sub` | данные `create` | src/forthc.fth:472 | 2 |  |
| 505 | `fc-qsel` | переменная | src/forthc.fth:472 | 2 |  |
| 506 | `fc-absa` | переменная | src/forthc.fth:473 | 5 |  |
| 507 | `fc-absb` | переменная | src/forthc.fth:473 | 3 |  |
| 508 | `fc-ta` | переменная | src/forthc.fth:473 | 4 |  |
| 509 | `fc-tb` | переменная | src/forthc.fth:473 | 2 |  |
| 510 | `fc-rem` | переменная | src/forthc.fth:474 | 7 |  |
| 511 | `fc-tr` | переменная | src/forthc.fth:474 | 7 |  |
| 512 | `fc-q` | переменная | src/forthc.fth:474 | 3 |  |
| 513 | `fc-tq` | переменная | src/forthc.fth:474 | 4 |  |
| 514 | `fc-k` | переменная | src/forthc.fth:474 | 5 |  |
| 515 | `fc-w` | переменная | src/forthc.fth:475 | 14 |  |
| 516 | `fc-lo` | переменная | src/forthc.fth:475 | 7 |  |
| 517 | `fc-tlo` | переменная | src/forthc.fth:475 | 7 |  |
| 518 | `fc-t0` | переменная | src/forthc.fth:475 | 4 |  |
| 519 | `fc-t1` | переменная | src/forthc.fth:475 | 4 |  |
| 520 | `fc-qr` | переменная | src/forthc.fth:475 | 4 |  |
| 521 | `fc-tqk` | переменная | src/forthc.fth:475 | 3 |  |
| 522 | `fc-sub@` | определение `:` | src/forthc.fth:476 | 7 |  |
| 523 | `fc-step` | определение `:` | src/forthc.fth:478 | 3 |  |
| 524 | `fc-div-step` | определение `:` | src/forthc.fth:485 | 1 |  |
| 525 | `fc-build-div` | определение `:` | src/forthc.fth:502 | 1 |  |
| 526 | `fc-mul-entry` | переменная | src/forthc.fth:518 | 4 |  |
| 527 | `fc-mul-exit` | переменная | src/forthc.fth:518 | 2 |  |
| 528 | `fc-div-entry` | переменная | src/forthc.fth:518 | 5 |  |
| 529 | `fc-div-exit` | переменная | src/forthc.fth:518 | 4 |  |
| 530 | `fc-hl` | переменная | src/forthc.fth:519 | 4 |  |
| 531 | `fc-hcont` | переменная | src/forthc.fth:519 | 4 |  |
| 532 | `fc-mul-cost` | данные `create` | src/forthc.fth:521 | 2 |  |
| 533 | `fc-div-cost` | данные `create` | src/forthc.fth:521 | 2 |  |
| 534 | `fc-row-or-new` | определение `:` | src/forthc.fth:522 | 2 |  |
| 535 | `fc-call-helper` | определение `:` | src/forthc.fth:525 | 4 |  |
| 536 | `fc-result1` | определение `:` | src/forthc.fth:531 | 3 |  |
| 537 | `fc-s1` | переменная | src/forthc.fth:532 | 2 |  |
| 538 | `fc-s2` | переменная | src/forthc.fth:532 | 2 |  |
| 539 | `fc-r1` | переменная | src/forthc.fth:532 | 2 |  |
| 540 | `fc-result2` | определение `:` | src/forthc.fth:533 | 1 |  |
| 541 | `fc-pexit` | переменная | src/forthc.fth:543 | 2 |  |
| 542 | `fc-ptramp` | переменная | src/forthc.fth:543 | 2 |  |
| 543 | `fc-pd` | переменная | src/forthc.fth:543 | 5 |  |
| 544 | `fc-pc` | переменная | src/forthc.fth:543 | 5 |  |
| 545 | `fc-ends` | переменная | src/forthc.fth:543 | 3 |  |
| 546 | `fc-pb` | переменная | src/forthc.fth:544 | 5 |  |
| 547 | `fc-pcp` | переменная | src/forthc.fth:544 | 5 |  |
| 548 | `fc-pln` | переменная | src/forthc.fth:544 | 5 |  |
| 549 | `fc-pk` | переменная | src/forthc.fth:544 | 4 |  |
| 550 | `fc-pcall` | переменная | src/forthc.fth:544 | 3 |  |
| 551 | `fc-best` | данные `create` | src/forthc.fth:545 | 10 |  |
| 552 | `fc-pend@` | определение `:` | src/forthc.fth:546 | 7 |  |
| 553 | `fc-reach` | определение `:` | src/forthc.fth:548 | 2 |  |
| 554 | `fc-take` | определение `:` | src/forthc.fth:558 | 1 |  |
| 555 | `fc-end-path` | определение `:` | src/forthc.fth:566 | 1 |  |
| 556 | `fc-to` | определение `:` | src/forthc.fth:571 | 2 |  |
| 557 | `fc-node` | определение `:` | src/forthc.fth:576 | 1 |  |
| 558 | `fc-path` | определение `:` | src/forthc.fth:596 | 3 |  |
| 559 | `fc-cost!` | определение `:` | src/forthc.fth:605 | 3 |  |
| 560 | `fc-ll` | переменная | src/forthc.fth:609 | 8 |  |
| 561 | `fc-llr` | переменная | src/forthc.fth:609 | 4 |  |
| 562 | `fc-llv` | переменная | src/forthc.fth:609 | 4 |  |
| 563 | `fc-plit` | переменная | src/forthc.fth:609 | 7 |  |
| 564 | `fc-plr` | переменная | src/forthc.fth:609 | 5 |  |
| 565 | `fc-plv` | переменная | src/forthc.fth:609 | 7 |  |
| 566 | `fc-literal` | определение `:` | src/forthc.fth:610 | 15 |  |
| 567 | `fc-or-zero` | определение `:` | src/forthc.fth:612 | 2 |  |
| 568 | `fc-ba` | переменная | src/forthc.fth:615 | 13 |  |
| 569 | `fc-bb` | переменная | src/forthc.fth:615 | 13 |  |
| 570 | `fc-br` | переменная | src/forthc.fth:615 | 9 |  |
| 571 | `fc-binary` | определение `:` | src/forthc.fth:617 | 10 |  |
| 572 | `fc-r-at` | определение `:` | src/forthc.fth:641 | 2 |  |
| 573 | `fc-pop-pinned` | определение `:` | src/forthc.fth:644 | 3 |  |
| 574 | `fc-sk` | переменная | src/forthc.fth:646 | 12 |  |
| 575 | `fc-shift-copy` | определение `:` | src/forthc.fth:647 | 2 |  |
| 576 | `fc-inc` | определение `:` | src/forthc.fth:652 | 3 |  |
| 577 | `fc-read-key` | определение `:` | src/forthc.fth:655 | 1 |  |
| 578 | `fc-text` | переменная | src/forthc.fth:661 | 13 |  |
| 579 | `fc-tlen` | переменная | src/forthc.fth:661 | 14 |  |
| 580 | `fc-pos` | переменная | src/forthc.fth:661 | 24 |  |
| 581 | `fc-text-size` | переменная | src/forthc.fth:661 | 6 | вход бута (хост) |
| 582 | `fc-tok` | данные `create` | src/forthc.fth:662 | 19 |  |
| 583 | `fc-tl` | переменная | src/forthc.fth:662 | 24 |  |
| 584 | `fc-reset` | определение `:` | src/forthc.fth:663 | 3 |  |
| 585 | `fc-append` | определение `:` | src/forthc.fth:664 | 1 |  |
| 586 | `fc\|` | определение `:` | src/forthc.fth:668 | 1 | вход бута (хост) |
| 587 | `fc-ch` | определение `:` | src/forthc.fth:669 | 5 |  |
| 588 | `fc-more?` | определение `:` | src/forthc.fth:670 | 6 |  |
| 589 | `fc-next` | определение `:` | src/forthc.fth:674 | 8 |  |
| 590 | `fc-next!` | определение `:` | src/forthc.fth:682 | 10 |  |
| 591 | `fc-is?` | определение `:` | src/forthc.fth:684 | 5 |  |
| 592 | `fc-raw` | определение `:` | src/forthc.fth:688 | 1 |  |
| 593 | `fc-string-token` | определение `:` | src/forthc.fth:690 | 1 |  |
| 594 | `fc-names-size` | переменная | src/forthc.fth:695 | 5 | вход бута (хост) |
| 595 | `fc-max-words` | переменная | src/forthc.fth:695 | 5 | вход бута (хост) |
| 596 | `fc-names` | переменная | src/forthc.fth:696 | 3 |  |
| 597 | `fc-names-used` | переменная | src/forthc.fth:696 | 5 |  |
| 598 | `fc-wt` | переменная | src/forthc.fth:697 | 4 |  |
| 599 | `fc-nwords` | переменная | src/forthc.fth:697 | 8 |  |
| 600 | `fc-wbk` | переменная | src/forthc.fth:697 | 3 |  |
| 601 | `fc-wt@` | определение `:` | src/forthc.fth:705 | 5 |  |
| 602 | `fc-proved` | данные `create` | src/forthc.fth:709 | 2 |  |
| 603 | `fc-unproved` | данные `create` | src/forthc.fth:710 | 2 |  |
| 604 | `fc-mechanisms` | определение `:` | src/forthc.fth:713 | 1 |  |
| 605 | `fc-xt` | определение `:` | src/forthc.fth:718 | 5 |  |
| 606 | `fc-hash` | определение `:` | src/forthc.fth:719 | 2 |  |
| 607 | `fc-define` | определение `:` | src/forthc.fth:721 | 6 |  |
| 608 | `fc-lookup` | определение `:` | src/forthc.fth:726 | 5 |  |
| 609 | `fc-find` | определение `:` | src/forthc.fth:730 | 6 |  |
| 610 | `fc-word-of` | определение `:` | src/forthc.fth:732 | 2 |  |
| 611 | `fc-cost` | определение `:` | src/forthc.fth:736 | 1 |  |
| 612 | `fc-proved?` | определение `:` | src/forthc.fth:739 | 1 |  |
| 613 | `fc-here` | переменная | src/forthc.fth:742 | 9 |  |
| 614 | `fc-word` | переменная | src/forthc.fth:742 | 12 |  |
| 615 | `fc-uses` | переменная | src/forthc.fth:742 | 16 |  |
| 616 | `fc-rt` | переменная | src/forthc.fth:745 | 6 |  |
| 617 | `fc-rta` | переменная | src/forthc.fth:745 | 5 |  |
| 618 | `fc-ctl` | данные `create` | src/forthc.fth:748 | 1 |  |
| 619 | `fc-nctl` | переменная | src/forthc.fth:748 | 12 |  |
| 620 | `fc-cleave` | переменная | src/forthc.fth:748 | 2 |  |
| 621 | `fc-ctl@` | определение `:` | src/forthc.fth:749 | 4 |  |
| 622 | `fc-ctl+` | определение `:` | src/forthc.fth:750 | 6 |  |
| 623 | `fc-ctl-` | определение `:` | src/forthc.fth:752 | 7 |  |
| 624 | `fc-do-entry` | определение `:` | src/forthc.fth:754 | 1 |  |
| 625 | `fc-ctl-leave` | определение `:` | src/forthc.fth:758 | 1 |  |
| 626 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:759 | 1 |  |
| 627 | `fc-loop-leave` | определение `:` | src/forthc.fth:760 | 1 |  |
| 628 | `fc-align` | определение `:` | src/forthc.fth:762 | 2 |  |
| 629 | `fc-check-here` | определение `:` | src/forthc.fth:763 | 3 |  |
| 630 | `fc-define-data` | определение `:` | src/forthc.fth:764 | 2 |  |
| 631 | `fc-sat` | переменная | src/forthc.fth:765 | 3 |  |
| 632 | `fc-store-string` | определение `:` | src/forthc.fth:766 | 1 |  |
| 633 | `fc-ct` | данные `create` | src/forthc.fth:772 | 3 |  |
| 634 | `fc-nct` | переменная | src/forthc.fth:772 | 11 |  |
| 635 | `fc-ct+` | определение `:` | src/forthc.fth:773 | 15 |  |
| 636 | `fc-ct-` | определение `:` | src/forthc.fth:774 | 9 |  |
| 637 | `fc-ct2` | определение `:` | src/forthc.fth:775 | 8 |  |
| 638 | `fc-inits` | данные `create` | src/forthc.fth:777 | 2 |  |
| 639 | `fc-ninit` | переменная | src/forthc.fth:777 | 5 |  |
| 640 | `fc-init-open` | переменная | src/forthc.fth:777 | 6 |  |
| 641 | `fc-init` | определение `:` | src/forthc.fth:778 | 1 |  |
| 642 | `fc-scan-uses` | определение `:` | src/forthc.fth:797 | 1 |  |
| 643 | `fc-const-shift` | определение `:` | src/forthc.fth:805 | 2 |  |
| 644 | `fc-lit?` | определение `:` | src/forthc.fth:816 | 3 |  |
| 645 | `fc-mul-lit?` | определение `:` | src/forthc.fth:818 | 1 |  |
| 646 | `fc-shift-lit?` | определение `:` | src/forthc.fth:823 | 2 |  |
| 647 | `fc-pick-roll` | определение `:` | src/forthc.fth:826 | 3 |  |
| 648 | `fc-stx` | переменная | src/forthc.fth:834 | 3 |  |
| 649 | `fc-stlo` | переменная | src/forthc.fth:834 | 11 |  |
| 650 | `fc-sthi` | переменная | src/forthc.fth:834 | 11 |  |
| 651 | `fc-stp` | переменная | src/forthc.fth:834 | 6 |  |
| 652 | `fc-strow` | переменная | src/forthc.fth:834 | 9 |  |
| 653 | `fc-space-store` | определение `:` | src/forthc.fth:835 | 2 |  |
| 654 | `fc-ftr` | переменная | src/forthc.fth:848 | 4 |  |
| 655 | `fc-space-fetch` | определение `:` | src/forthc.fth:849 | 3 |  |
| 656 | `fc-cp` | определение `:` | src/forthc.fth:866 | 4 |  |
| 657 | `fc-copy-row` | определение `:` | src/forthc.fth:868 | 1 |  |
| 658 | `fc-close-init` | определение `:` | src/forthc.fth:871 | 2 |  |
| 659 | `fc-open-init` | определение `:` | src/forthc.fth:874 | 1 |  |
| 660 | `fc-gens` | переменная | src/forthc.fth:890 | 3 |  |
| 661 | `fc-generator` | определение `:` | src/forthc.fth:891 | 87 |  |
| 662 | `fc-literal-name` | определение `:` | src/forthc.fth:893 | 12 |  |
| 663 | `fc-words` | определение `:` | src/forthc.fth:895 | 1 |  |
| 664 | `fc-known` | определение `:` | src/forthc.fth:906 | 1 |  |
| 665 | `fc-defining?` | определение `:` | src/forthc.fth:909 | 7 |  |
| 666 | `fc-code` | определение `:` | src/forthc.fth:912 | 52 | вариант 2 |
| 667 | `fc-fold?` | определение `:` | src/forthc.fth:915 | 13 |  |
| 668 | `fc-top-only` | определение `:` | src/forthc.fth:917 | 6 |  |
| 669 | `fc-not-found` | определение `:` | src/forthc.fth:922 | 1 |  |
| 670 | `fc-word-token` | определение `:` | src/forthc.fth:929 | 2 |  |
| 671 | `fc-token` | определение `:` | src/forthc.fth:936 | 2 |  |
| 672 | `fc-synonym-of` | определение `:` | src/forthc.fth:939 | 2 |  |
| 673 | `fc-synonym` | определение `:` | src/forthc.fth:941 | 10 |  |
| 674 | `fc-sy` | переменная | src/forthc.fth:944 | 2 |  |
| 675 | `fc-synonym?` | определение `:` | src/forthc.fth:945 | 1 |  |
| 676 | `fc-poke` | определение `:` | src/forthc.fth:950 | 2 |  |
| 677 | `fc-concept-record` | определение `:` | src/forthc.fth:955 | 1 |  |
| 678 | `fc-eval` | определение `:` | src/forthc.fth:961 | 55 |  |
| 679 | `fc-concepts` | определение `:` | src/forthc.fth:967 | 1 |  |
| 680 | `fc-nhost` | переменная | src/forthc.fth:983 | 5 |  |
| 681 | `fc-platform` | определение `:` | src/forthc.fth:984 | 1 |  |
| 682 | `fc-time-price` | определение `:` | src/forthc.fth:1010 | 1 |  |
| 683 | `fc-replacement` | определение `:` | src/forthc.fth:1023 | 1 |  |
| 684 | `fc-library` | определение `:` | src/forthc.fth:1039 | 1 |  |
| 685 | `fc-long` | определение `:` | src/forthc.fth:1063 | 1 |  |
| 686 | `fc-helpers-cost` | определение `:` | src/forthc.fth:1073 | 1 |  |
| 687 | `fc-price-word` | определение `:` | src/forthc.fth:1081 | 1 |  |
| 688 | `fc-compile` | определение `:` | src/forthc.fth:1084 | 1 |  |
| 689 | `fc-go` | определение `:` | src/forthc.fth:1101 | 3 | вход бута (хост) |
| 690 | `gen+` | определение `:` | src/primitives.fth:9 | 6 |  |
| 691 | `gen-` | определение `:` | src/primitives.fth:10 | 3 |  |
| 692 | `gen-and` | определение `:` | src/primitives.fth:11 | 4 |  |
| 693 | `gen-or` | определение `:` | src/primitives.fth:12 | 5 |  |
| 694 | `gen-xor` | определение `:` | src/primitives.fth:13 | 5 |  |
| 695 | `gen=` | определение `:` | src/primitives.fth:14 | 2 |  |
| 696 | `gen<` | определение `:` | src/primitives.fth:15 | 2 |  |
| 697 | `gen-u<` | определение `:` | src/primitives.fth:16 | 2 |  |
| 698 | `gen-lshift` | определение `:` | src/primitives.fth:17 | 2 |  |
| 699 | `gen-rshift` | определение `:` | src/primitives.fth:19 | 4 |  |
| 700 | `gen-0=` | определение `:` | src/primitives.fth:21 | 2 |  |
| 701 | `gen-cells` | определение `:` | src/primitives.fth:22 | 2 |  |
| 702 | `gen-2*` | определение `:` | src/primitives.fth:23 | 2 |  |
| 703 | `gen-1+` | определение `:` | src/primitives.fth:24 | 2 |  |
| 704 | `gen-1-` | определение `:` | src/primitives.fth:25 | 3 |  |
| 705 | `gen-cell+` | определение `:` | src/primitives.fth:26 | 2 |  |
| 706 | `gen*` | определение `:` | src/primitives.fth:28 | 2 |  |
| 707 | `gen/` | определение `:` | src/primitives.fth:31 | 2 |  |
| 708 | `gen-mod` | определение `:` | src/primitives.fth:32 | 2 |  |
| 709 | `gen/mod` | определение `:` | src/primitives.fth:33 | 2 |  |
| 710 | `gen-dup` | определение `:` | src/primitives.fth:37 | 4 |  |
| 711 | `gen-drop` | определение `:` | src/primitives.fth:38 | 2 |  |
| 712 | `gen-swap` | определение `:` | src/primitives.fth:39 | 3 |  |
| 713 | `gen-over` | определение `:` | src/primitives.fth:40 | 5 |  |
| 714 | `gen-rot` | определение `:` | src/primitives.fth:41 | 2 |  |
| 715 | `gen-pick` | определение `:` | src/primitives.fth:42 | 2 |  |
| 716 | `gen-roll` | определение `:` | src/primitives.fth:43 | 2 |  |
| 717 | `gen->r` | определение `:` | src/primitives.fth:44 | 2 |  |
| 718 | `gen-r>` | определение `:` | src/primitives.fth:45 | 2 |  |
| 719 | `gen-r@` | определение `:` | src/primitives.fth:46 | 4 |  |
| 720 | `gen-j` | определение `:` | src/primitives.fth:47 | 2 |  |
| 721 | `gen-@` | определение `:` | src/primitives.fth:48 | 2 |  |
| 722 | `gen-!` | определение `:` | src/primitives.fth:50 | 2 |  |
| 723 | `gen-c@` | определение `:` | src/primitives.fth:51 | 2 |  |
| 724 | `gen-c!` | определение `:` | src/primitives.fth:53 | 2 |  |
| 725 | `gen-emit` | определение `:` | src/primitives.fth:54 | 2 |  |
| 726 | `gen-key` | определение `:` | src/primitives.fth:57 | 2 |  |
| 727 | `gen-if` | определение `:` | src/primitives.fth:61 | 4 |  |
| 728 | `gen-else` | определение `:` | src/primitives.fth:62 | 2 |  |
| 729 | `gen-then` | определение `:` | src/primitives.fth:64 | 4 |  |
| 730 | `gen-begin` | определение `:` | src/primitives.fth:68 | 2 |  |
| 731 | `gen-until` | определение `:` | src/primitives.fth:69 | 2 |  |
| 732 | `gen-while` | определение `:` | src/primitives.fth:71 | 2 |  |
| 733 | `gen-repeat` | определение `:` | src/primitives.fth:72 | 2 |  |
| 734 | `gen-again` | определение `:` | src/primitives.fth:73 | 2 |  |
| 735 | `gen-do` | определение `:` | src/primitives.fth:75 | 2 |  |
| 736 | `fc-di` | переменная | src/primitives.fth:79 | 3 |  |
| 737 | `fc-dl` | переменная | src/primitives.fth:79 | 3 |  |
| 738 | `gen-?do` | определение `:` | src/primitives.fth:80 | 2 |  |
| 739 | `fc-lv` | переменная | src/primitives.fth:87 | 2 |  |
| 740 | `gen-loop` | определение `:` | src/primitives.fth:88 | 2 |  |
| 741 | `gen-leave` | определение `:` | src/primitives.fth:97 | 2 |  |
| 742 | `gen-unloop` | определение `:` | src/primitives.fth:100 | 2 |  |
| 743 | `gen-exit` | определение `:` | src/primitives.fth:103 | 2 |  |
| 744 | `gen-recurse` | определение `:` | src/primitives.fth:106 | 2 |  |
| 745 | `gen-tick` | определение `:` | src/primitives.fth:107 | 2 |  |
| 746 | `gen-throw` | определение `:` | src/primitives.fth:110 | 4 |  |
| 747 | `gen-call` | определение `:` | src/primitives.fth:117 | 28 |  |
| 748 | `gen-lit` | определение `:` | src/primitives.fth:118 | 10 |  |
| 749 | `gen-pick-n` | определение `:` | src/primitives.fth:120 | 3 |  |
| 750 | `gen-check-range` | определение `:` | src/primitives.fth:124 | 4 |  |
| 751 | `fc-mark-entry` | определение `:` | src/primitives.fth:133 | 2 |  |
| 752 | `gen-space!` | определение `:` | src/primitives.fth:134 | 2 |  |
| 753 | `gen-spacec!` | определение `:` | src/primitives.fth:135 | 2 |  |
| 754 | `gen-space@` | определение `:` | src/primitives.fth:136 | 2 |  |
| 755 | `gen-spacec@` | определение `:` | src/primitives.fth:137 | 2 |  |
| 756 | `gen-check-entry` | определение `:` | src/primitives.fth:141 | 2 |  |
| 757 | `gen-execute` | определение `:` | src/primitives.fth:147 | 2 |  |
| 758 | `gen-catch` | определение `:` | src/primitives.fth:149 | 2 |  |
| 759 | `fc-concept` | определение `:` | src/primitives.fth:157 | 1 |  |
| 760 | `gen-colon` | определение `:` | src/primitives.fth:162 | 2 |  |
| 761 | `gen-semicolon` | определение `:` | src/primitives.fth:167 | 2 |  |
| 762 | `gen-variable` | определение `:` | src/primitives.fth:170 | 2 |  |
| 763 | `gen-create` | определение `:` | src/primitives.fth:171 | 2 |  |
| 764 | `gen-allot` | определение `:` | src/primitives.fth:172 | 2 |  |
| 765 | `gen-constant` | определение `:` | src/primitives.fth:173 | 2 |  |
| 766 | `gen-decimal` | определение `:` | src/primitives.fth:174 | 2 |  |
| 767 | `gen-kernel-layout` | определение `:` | src/primitives.fth:176 | 2 |  |
| 768 | `gen-backslash` | определение `:` | src/primitives.fth:179 | 2 |  |
| 769 | `gen-paren` | определение `:` | src/primitives.fth:181 | 4 |  |
| 770 | `gen-char` | определение `:` | src/primitives.fth:182 | 2 |  |
| 771 | `gen-string` | определение `:` | src/primitives.fth:183 | 2 |  |
| 772 | `fc-digit@` | определение `:` | src/primitives.fth:192 | 1 |  |
| 773 | `gen-literal` | определение `:` | src/primitives.fth:194 | 2 |  |
| 774 | `fc-known-xt` | определение `:` | src/primitives.fth:203 | 2 |  |
| 775 | `gen-cost` | определение `:` | src/primitives.fth:204 | 2 |  |
| 776 | `gen-proved?` | определение `:` | src/primitives.fth:206 | 2 |  |
| 777 | `gen-library` | определение `:` | src/primitives.fth:207 | 16 |  |
| 778 | `gen-price` | определение `:` | src/primitives.fth:208 | 2 |  |
| 779 | `fc-cpos` | переменная | src/primitives.fth:216 | 4 |  |
| 780 | `fc-hn` | переменная | src/primitives.fth:216 | 2 |  |
| 781 | `fc-cdepth` | переменная | src/primitives.fth:216 | 4 |  |
| 782 | `fc-hname` | данные `create` | src/primitives.fth:216 | 2 |  |
| 783 | `fc-hb` | определение `:` | src/primitives.fth:217 | 3 |  |
| 784 | `fc-c,` | определение `:` | src/primitives.fth:218 | 17 |  |
| 785 | `fc-c1` | определение `:` | src/primitives.fth:219 | 8 |  |
| 786 | `fc-c-gen` | определение `:` | src/primitives.fth:220 | 1 |  |
| 787 | `fc-c-body` | определение `:` | src/primitives.fth:224 | 1 |  |
| 788 | `gen-host` | определение `:` | src/primitives.fth:233 | 2 |  |
| 789 | `fc-name2` | определение `:` | src/primitives.fth:251 | 1 |  |
| 790 | `fc-generators` | определение `:` | src/primitives.fth:256 | 1 |  |
| 791 | `+` | генератор | src/primitives.fth:257 | 529 | слово компилятора `gen+` |
| 792 | `-` | генератор | src/primitives.fth:257 | 54 | слово компилятора `gen-` |
| 793 | `*` | генератор | src/primitives.fth:258 | 81 | слово компилятора `gen*` |
| 794 | `/` | генератор | src/primitives.fth:258 | 4 | слово компилятора `gen/` |
| 795 | `mod` | генератор | src/primitives.fth:259 | 2 | слово компилятора `gen-mod` |
| 796 | `and` | генератор | src/primitives.fth:260 | 112 | слово компилятора `gen-and` |
| 797 | `or` | генератор | src/primitives.fth:260 | 43 | слово компилятора `gen-or` |
| 798 | `xor` | генератор | src/primitives.fth:261 | 5 | слово компилятора `gen-xor` |
| 799 | `lshift` | генератор | src/primitives.fth:261 | 81 | слово компилятора `gen-lshift` |
| 800 | `rshift` | генератор | src/primitives.fth:262 | 57 | слово компилятора `gen-rshift` |
| 801 | `=` | генератор | src/primitives.fth:262 | 65 | слово компилятора `gen=` |
| 802 | `<` | генератор | src/primitives.fth:263 | 29 | слово компилятора `gen<` |
| 803 | `u<` | генератор | src/primitives.fth:263 | 15 | слово компилятора `gen-u<` |
| 804 | `0=` | генератор | src/primitives.fth:264 | 83 | слово компилятора `gen-0=` |
| 805 | `2*` | генератор | src/primitives.fth:264 | 28 | слово компилятора `gen-2*` |
| 806 | `1+` | генератор | src/primitives.fth:265 | 43 | слово компилятора `gen-1+` |
| 807 | `1-` | генератор | src/primitives.fth:265 | 45 | слово компилятора `gen-1-` |
| 808 | `cells` | генератор | src/primitives.fth:266 | 263 | слово компилятора `gen-cells` |
| 809 | `cell+` | генератор | src/primitives.fth:266 | 53 | слово компилятора `gen-cell+` |
| 810 | `dup` | генератор | src/primitives.fth:267 | 297 | слово компилятора `gen-dup` |
| 811 | `drop` | генератор | src/primitives.fth:267 | 199 | слово компилятора `gen-drop` |
| 812 | `swap` | генератор | src/primitives.fth:268 | 133 | слово компилятора `gen-swap` |
| 813 | `over` | генератор | src/primitives.fth:268 | 84 | слово компилятора `gen-over` |
| 814 | `rot` | генератор | src/primitives.fth:269 | 38 | слово компилятора `gen-rot` |
| 815 | `pick` | генератор | src/primitives.fth:269 | 50 | слово компилятора `gen-pick` |
| 816 | `roll` | генератор | src/primitives.fth:270 | 6 | слово компилятора `gen-roll` |
| 817 | `>r` | генератор | src/primitives.fth:270 | 108 | слово компилятора `gen->r` |
| 818 | `r>` | генератор | src/primitives.fth:271 | 112 | слово компилятора `gen-r>` |
| 819 | `r@` | генератор | src/primitives.fth:271 | 95 | слово компилятора `gen-r@` |
| 820 | `i` | генератор | src/primitives.fth:272 | 161 | слово компилятора `gen-r@` |
| 821 | `j` | генератор | src/primitives.fth:272 | 12 | слово компилятора `gen-j` |
| 822 | `@` | генератор | src/primitives.fth:273 | 1145 | слово компилятора `gen-@` |
| 823 | `!` | генератор | src/primitives.fth:273 | 621 | слово компилятора `gen-!` |
| 824 | `c@` | генератор | src/primitives.fth:274 | 23 | слово компилятора `gen-c@` |
| 825 | `c!` | генератор | src/primitives.fth:274 | 18 | слово компилятора `gen-c!` |
| 826 | `space!` | генератор | src/primitives.fth:275 | 1 | слово компилятора `gen-space!` |
| 827 | `spacec!` | генератор | src/primitives.fth:275 | 1 | слово компилятора `gen-spacec!` |
| 828 | `emit` | генератор | src/primitives.fth:277 | 4 | слово компилятора `gen-emit` |
| 829 | `key` | генератор | src/primitives.fth:277 | 1 | слово компилятора `gen-key` |
| 830 | `if` | генератор | src/primitives.fth:278 | 282 | слово компилятора `gen-if` |
| 831 | `else` | генератор | src/primitives.fth:278 | 72 | слово компилятора `gen-else` |
| 832 | `then` | генератор | src/primitives.fth:279 | 282 | слово компилятора `gen-then` |
| 833 | `begin` | генератор | src/primitives.fth:279 | 25 | слово компилятора `gen-begin` |
| 834 | `until` | генератор | src/primitives.fth:280 | 2 | слово компилятора `gen-until` |
| 835 | `while` | генератор | src/primitives.fth:280 | 22 | слово компилятора `gen-while` |
| 836 | `repeat` | генератор | src/primitives.fth:281 | 22 | слово компилятора `gen-repeat` |
| 837 | `again` | генератор | src/primitives.fth:281 | 1 | слово компилятора `gen-again` |
| 838 | `do` | генератор | src/primitives.fth:282 | 31 | слово компилятора `gen-do` |
| 839 | `?do` | генератор | src/primitives.fth:282 | 53 | слово компилятора `gen-?do` |
| 840 | `loop` | генератор | src/primitives.fth:283 | 84 | слово компилятора `gen-loop` |
| 841 | `leave` | генератор | src/primitives.fth:283 | 1 | слово компилятора `gen-leave` |
| 842 | `unloop` | генератор | src/primitives.fth:284 | 6 | слово компилятора `gen-unloop` |
| 843 | `exit` | генератор | src/primitives.fth:284 | 67 | слово компилятора `gen-exit` |
| 844 | `recurse` | генератор | src/primitives.fth:285 | 2 | слово компилятора `gen-recurse` |
| 845 | `execute` | генератор | src/primitives.fth:285 | 10 | слово компилятора `gen-execute` |
| 846 | `[']` | генератор | src/primitives.fth:286 | 145 | слово компилятора `gen-tick` |
| 847 | `catch` | генератор | src/primitives.fth:286 | 1 | слово компилятора `gen-catch` |
| 848 | `throw` | генератор | src/primitives.fth:287 | 83 | слово компилятора `gen-throw` |
| 849 | `:` | генератор | src/primitives.fth:288 | 466 | слово компилятора `gen-colon` |
| 850 | `;` | генератор | src/primitives.fth:288 | 466 | слово компилятора `gen-semicolon` |
| 851 | `variable` | генератор | src/primitives.fth:289 | 294 | слово компилятора `gen-variable` |
| 852 | `create` | генератор | src/primitives.fth:289 | 44 | слово компилятора `gen-create` |
| 853 | `allot` | генератор | src/primitives.fth:290 | 42 | слово компилятора `gen-allot` |
| 854 | `constant` | генератор | src/primitives.fth:290 | 17 | слово компилятора `gen-constant` |
| 855 | `decimal` | генератор | src/primitives.fth:291 | 3 | слово компилятора `gen-decimal` |
| 856 | `kernel-layout` | генератор | src/primitives.fth:291 | 1 | слово компилятора `gen-kernel-layout` |
| 857 | `\` | генератор | src/primitives.fth:292 | 400 | слово компилятора `gen-backslash` |
| 858 | `(` | генератор | src/primitives.fth:292 | 442 | слово компилятора `gen-paren` |
| 859 | `[char]` | генератор | src/primitives.fth:292 | 8 | слово компилятора `gen-char` |
| 860 | `s"` | генератор | src/primitives.fth:293 | 201 | слово компилятора `gen-string` |
| 861 | `literal` | генератор | src/primitives.fth:294 | 502 | слово компилятора `gen-literal` |
| 862 | `0` | цифра (литерал) | src/primitives.fth:302 | 529 | значение 0 |
| 863 | `1` | цифра (литерал) | src/primitives.fth:302 | 442 | значение 1 |
| 864 | `2` | цифра (литерал) | src/primitives.fth:302 | 456 | значение 2 |
| 865 | `3` | цифра (литерал) | src/primitives.fth:302 | 302 | значение 3 |
| 866 | `4` | цифра (литерал) | src/primitives.fth:303 | 243 | значение 4 |
| 867 | `5` | цифра (литерал) | src/primitives.fth:303 | 106 | значение 5 |
| 868 | `6` | цифра (литерал) | src/primitives.fth:303 | 153 | значение 6 |
| 869 | `7` | цифра (литерал) | src/primitives.fth:303 | 57 | значение 7 |
| 870 | `8` | цифра (литерал) | src/primitives.fth:304 | 159 | значение 8 |
| 871 | `9` | цифра (литерал) | src/primitives.fth:304 | 44 | значение 9 |
| 872 | `fc-install-generators` | определение `:` | src/primitives.fth:305 | 1 |  |
| 873 | `heap-start` | данные `create` | src/main.fth:4 | 1 |  |
| 874 | `fc-read` | определение `:` | src/main.fth:7 | 2 |  |
| 875 | `fc-sizes` | определение `:` | src/main.fth:12 | 2 |  |
| 876 | `kn-at` | переменная | src/kernel.fth:12 | 5 |  |
| 877 | `kn-put` | определение `:` | src/kernel.fth:13 | 1 |  |
| 878 | `kn-order` | определение `:` | src/kernel.fth:23 | 1 |  |
| 879 | `kn-compile` | определение `:` | src/kernel.fth:24 | 1 |  |
| 880 | `kn-.n` | определение `:` | src/kernel.fth:25 | 1 |  |
| 881 | `main` | определение `:` | src/kernel.fth:29 | 1 | вариант 2 |
| 882 | `kn-heap-start` | данные `create` | src/kernel.fth:34 | 1 |  |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 94.

## Определены, но не использованы

Слов: 35. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

| Слово | Вид | Файл:строка |
|---|---|---|
| `cc-out` | определение `:` | src/backend.fth:120 |
| `cc-cz` | переменная | src/compute.fth:183 |
| `cc-cf` | переменная | src/compute.fth:183 |
| `cc-compare` | определение `:` | src/compute.fth:184 |
| `cc-fc` | переменная | src/compute.fth:231 |
| `cc-ff` | переменная | src/compute.fth:231 |
| `cc-flag-exit` | определение `:` | src/compute.fth:232 |
| `cc-exit-layers` | определение `:` | src/compute.fth:241 |
| `cc-ce` | переменная | src/compute.fth:246 |
| `cc-cl` | переменная | src/compute.fth:246 |
| `cc-ch` | переменная | src/compute.fth:246 |
| `cc-call-rows` | определение `:` | src/compute.fth:247 |
| `cc-halt-begin` | определение `:` | src/compute.fth:252 |
| `cc-halt-region` | определение `:` | src/compute.fth:253 |
| `cc-halt-end` | определение `:` | src/compute.fth:254 |
| `cc-stub-on` | определение `:` | src/compute.fth:255 |
| `cc-stub` | определение `:` | src/compute.fth:256 |
| `fc-depth` | определение `:` | src/forthc.fth:904 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:905 |
| `/mod` | генератор | src/primitives.fth:259 |
| `space@` | генератор | src/primitives.fth:276 |
| `spacec@` | генератор | src/primitives.fth:276 |
| `cost` | генератор | src/primitives.fth:295 |
| `price` | генератор | src/primitives.fth:295 |
| `proved?` | генератор | src/primitives.fth:296 |
| `check-table` | генератор | src/primitives.fth:297 |
| `accuracy` | генератор | src/primitives.fth:297 |
| `replace` | генератор | src/primitives.fth:298 |
| `long!` | генератор | src/primitives.fth:299 |
| `long@` | генератор | src/primitives.fth:299 |
| `host` | генератор | src/primitives.fth:300 |
| `time` | генератор | src/primitives.fth:300 |
| `platform` | генератор | src/primitives.fth:301 |
| `platform-of` | генератор | src/primitives.fth:301 |
| `main` (вариант 1) | определение `:` | src/main.fth:15 |

## Слова, которые при буте исполняет хост

Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки `backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках 83; все они определены в определении языка (генератором в `primitives.fth` или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: `!` `*` `+` `+!` `-` `-rot` `/` `/string` `0<` `0<>` `0=` `0>` `1+` `1-` `2!` `2*` `2@` `2drop` `2dup` `2over` `2swap` `<` `<>` `=` `>` `>in` `>r` `?do` `?dup` `@` `again` `allocate` `and` `begin` `c!` `c@` `cell+` `cells` `cmove` `cmove>` `compare` `decimal` `do` `drop` `dup` `else` `execute` `exit` `fill` `free` `i` `if` `invert` `j` `leave` `loop` `lshift` `max` `min` `mod` `negate` `nip` `or` `over` `pick` `r>` `r@` `repeat` `roll` `rot` `rshift` `source` `swap` `then` `throw` `tuck` `type` `u<` `u>` `unloop` `until` `while` `xor`.

Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро читает каналом `key`), `source` и `>in` — слова только этого пути.
