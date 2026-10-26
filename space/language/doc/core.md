# Ядро языка (14.8)

Файл порождается `make -C space/language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`tools/research/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 851** (определение `:` — 424, переменная — 280, генератор — 71, данные `create` — 43, константа — 17, цифра (литерал) — 10, основание — 6).

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
| 4 | `2dup` | определение `:` | src/prelude.fth:9 | 9 |  |
| 5 | `2drop` | определение `:` | src/prelude.fth:10 | 21 |  |
| 6 | `2swap` | определение `:` | src/prelude.fth:11 | 6 |  |
| 7 | `2over` | определение `:` | src/prelude.fth:12 | 2 |  |
| 8 | `?dup` | определение `:` | src/prelude.fth:13 | 18 |  |
| 9 | `negate` | определение `:` | src/prelude.fth:14 | 5 |  |
| 10 | `invert` | определение `:` | src/prelude.fth:15 | 1 |  |
| 11 | `>` | определение `:` | src/prelude.fth:16 | 10 |  |
| 12 | `u>` | определение `:` | src/prelude.fth:17 | 5 |  |
| 13 | `<>` | определение `:` | src/prelude.fth:18 | 12 |  |
| 14 | `0<` | определение `:` | src/prelude.fth:19 | 5 |  |
| 15 | `0>` | определение `:` | src/prelude.fth:20 | 3 |  |
| 16 | `0<>` | определение `:` | src/prelude.fth:21 | 4 |  |
| 17 | `max` | определение `:` | src/prelude.fth:22 | 20 |  |
| 18 | `min` | определение `:` | src/prelude.fth:23 | 5 |  |
| 19 | `+!` | определение `:` | src/prelude.fth:24 | 59 |  |
| 20 | `2@` | определение `:` | src/prelude.fth:25 | 4 |  |
| 21 | `2!` | определение `:` | src/prelude.fth:26 | 2 |  |
| 22 | `fill-cell` | переменная | src/prelude.fth:28 | 2 |  |
| 23 | `fill` | определение `:` | src/prelude.fth:29 | 11 |  |
| 24 | `cmove` | определение `:` | src/prelude.fth:33 | 14 |  |
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
| 38 | `cc-slots` | переменная | src/backend.fth:14 | 13 |  |
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
| 51 | `cc-layer-bits` | определение `:` | src/backend.fth:24 | 8 |  |
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
| 68 | `cc-put` | определение `:` | src/backend.fth:69 | 10 |  |
| 69 | `cc-scratch` | данные `create` | src/backend.fth:87 | 2 |  |
| 70 | `cc-put-numeric` | определение `:` | src/backend.fth:88 | 1 |  |
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
| 83 | `cc-field` | определение `:` | src/backend.fth:117 | 36 |  |
| 84 | `cc-link-row` | основание | src/backend.fth:118 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 85 | `cc-copy` | основание | src/backend.fth:119 | 73 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 86 | `cc-builder` | определение `:` | src/backend.fth:121 | 1 |  |
| 87 | `cc-new-cell` | определение `:` | src/backend.fth:122 | 13 |  |
| 88 | `cc-branch-bit` | определение `:` | src/backend.fth:125 | 14 |  |
| 89 | `cc-branch-step` | определение `:` | src/backend.fth:126 | 4 |  |
| 90 | `cc-group` | определение `:` | src/backend.fth:128 | 5 |  |
| 91 | `cc-layer-cell` | определение `:` | src/backend.fth:131 | 38 |  |
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
| 102 | `cc-seq` | определение `:` | src/backend.fth:153 | 8 |  |
| 103 | `cc-last` | определение `:` | src/backend.fth:154 | 5 |  |
| 104 | `cc-layer` | основание | src/backend.fth:155 | 72 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 105 | `cc-entry` | определение `:` | src/backend.fth:160 | 4 |  |
| 106 | `cc-jump` | определение `:` | src/backend.fth:161 | 11 |  |
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
| 121 | `cc-row` | основание | src/backend.fth:186 | 72 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 122 | `cc-flush` | определение `:` | src/backend.fth:190 | 12 |  |
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
| 250 | `fc-guard` | переменная | src/forthc.fth:19 | 8 |  |
| 251 | `fc-layout` | определение `:` | src/forthc.fth:20 | 1 |  |
| 252 | `fc-d+` | определение `:` | src/forthc.fth:22 | 29 |  |
| 253 | `fc-sp` | определение `:` | src/forthc.fth:23 | 6 |  |
| 254 | `fc-rp` | определение `:` | src/forthc.fth:23 | 18 |  |
| 255 | `fc-handler` | определение `:` | src/forthc.fth:23 | 6 |  |
| 256 | `fc-code` | определение `:` | src/forthc.fth:23 | 4 |  |
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
| 283 | `fc-mem` | определение `:` | src/forthc.fth:34 | 4 |  |
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
| 332 | `fc-eight` | данные `create` | src/forthc.fth:125 | 5 |  |
| 333 | `fc-zeros` | данные `create` | src/forthc.fth:125 | 5 |  |
| 334 | `fc-put-consts` | определение `:` | src/forthc.fth:126 | 1 |  |
| 335 | `fc-cache` | данные `create` | src/forthc.fth:134 | 8 |  |
| 336 | `fc-n` | переменная | src/forthc.fth:134 | 31 |  |
| 337 | `fc-pin` | данные `create` | src/forthc.fth:135 | 10 |  |
| 338 | `fc-npin` | переменная | src/forthc.fth:135 | 21 |  |
| 339 | `fc-c@` | определение `:` | src/forthc.fth:136 | 8 |  |
| 340 | `fc-push` | определение `:` | src/forthc.fth:137 | 30 |  |
| 341 | `fc-pop1` | определение `:` | src/forthc.fth:138 | 31 |  |
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
| 378 | `fc-need` | определение `:` | src/forthc.fth:209 | 14 |  |
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
| 397 | `fc-log-begin` | определение `:` | src/forthc.fth:249 | 2 |  |
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
| 566 | `fc-literal` | определение `:` | src/forthc.fth:610 | 14 |  |
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
| 578 | `fc-text` | переменная | src/forthc.fth:661 | 10 |  |
| 579 | `fc-tlen` | переменная | src/forthc.fth:661 | 11 |  |
| 580 | `fc-pos` | переменная | src/forthc.fth:661 | 14 |  |
| 581 | `fc-text-size` | переменная | src/forthc.fth:661 | 6 | вход бута (хост) |
| 582 | `fc-tok` | данные `create` | src/forthc.fth:662 | 14 |  |
| 583 | `fc-tl` | переменная | src/forthc.fth:662 | 18 |  |
| 584 | `fc-reset` | определение `:` | src/forthc.fth:663 | 3 |  |
| 585 | `fc-append` | определение `:` | src/forthc.fth:664 | 1 |  |
| 586 | `fc\|` | определение `:` | src/forthc.fth:668 | 1 | вход бута (хост) |
| 587 | `fc-ch` | определение `:` | src/forthc.fth:669 | 5 |  |
| 588 | `fc-more?` | определение `:` | src/forthc.fth:670 | 6 |  |
| 589 | `fc-next` | определение `:` | src/forthc.fth:674 | 4 |  |
| 590 | `fc-next!` | определение `:` | src/forthc.fth:682 | 6 |  |
| 591 | `fc-is?` | определение `:` | src/forthc.fth:684 | 1 |  |
| 592 | `fc-raw` | определение `:` | src/forthc.fth:688 | 1 |  |
| 593 | `fc-string-token` | определение `:` | src/forthc.fth:690 | 1 |  |
| 594 | `fc-names-size` | переменная | src/forthc.fth:695 | 5 | вход бута (хост) |
| 595 | `fc-max-words` | переменная | src/forthc.fth:695 | 5 | вход бута (хост) |
| 596 | `fc-names` | переменная | src/forthc.fth:696 | 3 |  |
| 597 | `fc-names-used` | переменная | src/forthc.fth:696 | 5 |  |
| 598 | `fc-wt` | переменная | src/forthc.fth:697 | 3 |  |
| 599 | `fc-nwords` | переменная | src/forthc.fth:697 | 7 |  |
| 600 | `fc-wbk` | переменная | src/forthc.fth:697 | 3 |  |
| 601 | `fc-wt@` | определение `:` | src/forthc.fth:705 | 4 |  |
| 602 | `fc-proved` | данные `create` | src/forthc.fth:709 | 2 |  |
| 603 | `fc-unproved` | данные `create` | src/forthc.fth:710 | 2 |  |
| 604 | `fc-mechanisms` | определение `:` | src/forthc.fth:713 | 1 |  |
| 605 | `fc-xt` | определение `:` | src/forthc.fth:718 | 5 |  |
| 606 | `fc-hash` | определение `:` | src/forthc.fth:719 | 2 |  |
| 607 | `fc-define` | определение `:` | src/forthc.fth:721 | 5 |  |
| 608 | `fc-lookup` | определение `:` | src/forthc.fth:726 | 3 |  |
| 609 | `fc-find` | определение `:` | src/forthc.fth:730 | 4 |  |
| 610 | `fc-word-of` | определение `:` | src/forthc.fth:732 | 2 |  |
| 611 | `fc-cost` | определение `:` | src/forthc.fth:736 | 1 |  |
| 612 | `fc-proved?` | определение `:` | src/forthc.fth:739 | 1 |  |
| 613 | `fc-here` | переменная | src/forthc.fth:742 | 9 |  |
| 614 | `fc-word` | переменная | src/forthc.fth:742 | 8 |  |
| 615 | `fc-uses` | переменная | src/forthc.fth:742 | 10 |  |
| 616 | `fc-ctl` | данные `create` | src/forthc.fth:745 | 1 |  |
| 617 | `fc-nctl` | переменная | src/forthc.fth:745 | 12 |  |
| 618 | `fc-cleave` | переменная | src/forthc.fth:745 | 2 |  |
| 619 | `fc-ctl@` | определение `:` | src/forthc.fth:746 | 4 |  |
| 620 | `fc-ctl+` | определение `:` | src/forthc.fth:747 | 6 |  |
| 621 | `fc-ctl-` | определение `:` | src/forthc.fth:749 | 7 |  |
| 622 | `fc-do-entry` | определение `:` | src/forthc.fth:751 | 1 |  |
| 623 | `fc-ctl-leave` | определение `:` | src/forthc.fth:755 | 1 |  |
| 624 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:756 | 1 |  |
| 625 | `fc-loop-leave` | определение `:` | src/forthc.fth:757 | 1 |  |
| 626 | `fc-align` | определение `:` | src/forthc.fth:759 | 2 |  |
| 627 | `fc-check-here` | определение `:` | src/forthc.fth:760 | 3 |  |
| 628 | `fc-define-data` | определение `:` | src/forthc.fth:761 | 2 |  |
| 629 | `fc-sat` | переменная | src/forthc.fth:762 | 3 |  |
| 630 | `fc-store-string` | определение `:` | src/forthc.fth:763 | 1 |  |
| 631 | `fc-ct` | данные `create` | src/forthc.fth:769 | 3 |  |
| 632 | `fc-nct` | переменная | src/forthc.fth:769 | 11 |  |
| 633 | `fc-ct+` | определение `:` | src/forthc.fth:770 | 15 |  |
| 634 | `fc-ct-` | определение `:` | src/forthc.fth:771 | 9 |  |
| 635 | `fc-ct2` | определение `:` | src/forthc.fth:772 | 8 |  |
| 636 | `fc-inits` | данные `create` | src/forthc.fth:774 | 2 |  |
| 637 | `fc-ninit` | переменная | src/forthc.fth:774 | 5 |  |
| 638 | `fc-init-open` | переменная | src/forthc.fth:774 | 6 |  |
| 639 | `fc-init` | определение `:` | src/forthc.fth:775 | 1 |  |
| 640 | `fc-scan-uses` | определение `:` | src/forthc.fth:794 | 1 |  |
| 641 | `fc-const-shift` | определение `:` | src/forthc.fth:802 | 2 |  |
| 642 | `fc-lit?` | определение `:` | src/forthc.fth:813 | 3 |  |
| 643 | `fc-mul-lit?` | определение `:` | src/forthc.fth:815 | 1 |  |
| 644 | `fc-shift-lit?` | определение `:` | src/forthc.fth:820 | 2 |  |
| 645 | `fc-pick-roll` | определение `:` | src/forthc.fth:823 | 3 |  |
| 646 | `fc-stx` | переменная | src/forthc.fth:831 | 3 |  |
| 647 | `fc-stlo` | переменная | src/forthc.fth:831 | 11 |  |
| 648 | `fc-sthi` | переменная | src/forthc.fth:831 | 11 |  |
| 649 | `fc-stp` | переменная | src/forthc.fth:831 | 6 |  |
| 650 | `fc-strow` | переменная | src/forthc.fth:831 | 9 |  |
| 651 | `fc-space-store` | определение `:` | src/forthc.fth:832 | 2 |  |
| 652 | `fc-ftr` | переменная | src/forthc.fth:845 | 4 |  |
| 653 | `fc-space-fetch` | определение `:` | src/forthc.fth:846 | 3 |  |
| 654 | `fc-close-init` | определение `:` | src/forthc.fth:859 | 2 |  |
| 655 | `fc-open-init` | определение `:` | src/forthc.fth:862 | 1 |  |
| 656 | `fc-gens` | переменная | src/forthc.fth:878 | 3 |  |
| 657 | `fc-generator` | определение `:` | src/forthc.fth:879 | 77 |  |
| 658 | `fc-literal-name` | определение `:` | src/forthc.fth:881 | 10 |  |
| 659 | `fc-words` | определение `:` | src/forthc.fth:883 | 1 |  |
| 660 | `fc-known` | определение `:` | src/forthc.fth:894 | 1 |  |
| 661 | `fc-defining?` | определение `:` | src/forthc.fth:897 | 6 |  |
| 662 | `fc-code` | определение `:` | src/forthc.fth:900 | 52 | вариант 2 |
| 663 | `fc-fold?` | определение `:` | src/forthc.fth:903 | 13 |  |
| 664 | `fc-top-only` | определение `:` | src/forthc.fth:905 | 6 |  |
| 665 | `fc-not-found` | определение `:` | src/forthc.fth:910 | 1 |  |
| 666 | `fc-word-token` | определение `:` | src/forthc.fth:917 | 1 |  |
| 667 | `fc-helpers-cost` | определение `:` | src/forthc.fth:924 | 1 |  |
| 668 | `fc-price-word` | определение `:` | src/forthc.fth:931 | 1 |  |
| 669 | `fc-compile` | определение `:` | src/forthc.fth:934 | 1 |  |
| 670 | `fc-go` | определение `:` | src/forthc.fth:951 | 3 | вход бута (хост) |
| 671 | `gen+` | определение `:` | src/primitives.fth:9 | 6 |  |
| 672 | `gen-` | определение `:` | src/primitives.fth:10 | 3 |  |
| 673 | `gen-and` | определение `:` | src/primitives.fth:11 | 4 |  |
| 674 | `gen-or` | определение `:` | src/primitives.fth:12 | 5 |  |
| 675 | `gen-xor` | определение `:` | src/primitives.fth:13 | 5 |  |
| 676 | `gen=` | определение `:` | src/primitives.fth:14 | 2 |  |
| 677 | `gen<` | определение `:` | src/primitives.fth:15 | 2 |  |
| 678 | `gen-u<` | определение `:` | src/primitives.fth:16 | 2 |  |
| 679 | `gen-lshift` | определение `:` | src/primitives.fth:17 | 2 |  |
| 680 | `gen-rshift` | определение `:` | src/primitives.fth:19 | 4 |  |
| 681 | `gen-0=` | определение `:` | src/primitives.fth:21 | 2 |  |
| 682 | `gen-cells` | определение `:` | src/primitives.fth:22 | 2 |  |
| 683 | `gen-2*` | определение `:` | src/primitives.fth:23 | 2 |  |
| 684 | `gen-1+` | определение `:` | src/primitives.fth:24 | 2 |  |
| 685 | `gen-1-` | определение `:` | src/primitives.fth:25 | 3 |  |
| 686 | `gen-cell+` | определение `:` | src/primitives.fth:26 | 2 |  |
| 687 | `gen*` | определение `:` | src/primitives.fth:28 | 2 |  |
| 688 | `gen/` | определение `:` | src/primitives.fth:31 | 2 |  |
| 689 | `gen-mod` | определение `:` | src/primitives.fth:32 | 2 |  |
| 690 | `gen/mod` | определение `:` | src/primitives.fth:33 | 2 |  |
| 691 | `gen-dup` | определение `:` | src/primitives.fth:37 | 4 |  |
| 692 | `gen-drop` | определение `:` | src/primitives.fth:38 | 2 |  |
| 693 | `gen-swap` | определение `:` | src/primitives.fth:39 | 3 |  |
| 694 | `gen-over` | определение `:` | src/primitives.fth:40 | 5 |  |
| 695 | `gen-rot` | определение `:` | src/primitives.fth:41 | 2 |  |
| 696 | `gen-pick` | определение `:` | src/primitives.fth:42 | 2 |  |
| 697 | `gen-roll` | определение `:` | src/primitives.fth:43 | 2 |  |
| 698 | `gen->r` | определение `:` | src/primitives.fth:44 | 2 |  |
| 699 | `gen-r>` | определение `:` | src/primitives.fth:45 | 2 |  |
| 700 | `gen-r@` | определение `:` | src/primitives.fth:46 | 4 |  |
| 701 | `gen-j` | определение `:` | src/primitives.fth:47 | 2 |  |
| 702 | `gen-@` | определение `:` | src/primitives.fth:48 | 2 |  |
| 703 | `gen-!` | определение `:` | src/primitives.fth:50 | 2 |  |
| 704 | `gen-c@` | определение `:` | src/primitives.fth:51 | 2 |  |
| 705 | `gen-c!` | определение `:` | src/primitives.fth:53 | 2 |  |
| 706 | `gen-emit` | определение `:` | src/primitives.fth:54 | 2 |  |
| 707 | `gen-key` | определение `:` | src/primitives.fth:57 | 2 |  |
| 708 | `gen-if` | определение `:` | src/primitives.fth:61 | 4 |  |
| 709 | `gen-else` | определение `:` | src/primitives.fth:62 | 2 |  |
| 710 | `gen-then` | определение `:` | src/primitives.fth:64 | 4 |  |
| 711 | `gen-begin` | определение `:` | src/primitives.fth:68 | 2 |  |
| 712 | `gen-until` | определение `:` | src/primitives.fth:69 | 2 |  |
| 713 | `gen-while` | определение `:` | src/primitives.fth:71 | 2 |  |
| 714 | `gen-repeat` | определение `:` | src/primitives.fth:72 | 2 |  |
| 715 | `gen-again` | определение `:` | src/primitives.fth:73 | 2 |  |
| 716 | `gen-do` | определение `:` | src/primitives.fth:75 | 2 |  |
| 717 | `fc-di` | переменная | src/primitives.fth:79 | 3 |  |
| 718 | `fc-dl` | переменная | src/primitives.fth:79 | 3 |  |
| 719 | `gen-?do` | определение `:` | src/primitives.fth:80 | 2 |  |
| 720 | `fc-lv` | переменная | src/primitives.fth:87 | 2 |  |
| 721 | `gen-loop` | определение `:` | src/primitives.fth:88 | 2 |  |
| 722 | `gen-leave` | определение `:` | src/primitives.fth:97 | 2 |  |
| 723 | `gen-unloop` | определение `:` | src/primitives.fth:100 | 2 |  |
| 724 | `gen-exit` | определение `:` | src/primitives.fth:103 | 2 |  |
| 725 | `gen-recurse` | определение `:` | src/primitives.fth:106 | 2 |  |
| 726 | `gen-tick` | определение `:` | src/primitives.fth:107 | 2 |  |
| 727 | `gen-throw` | определение `:` | src/primitives.fth:110 | 4 |  |
| 728 | `gen-call` | определение `:` | src/primitives.fth:117 | 28 |  |
| 729 | `gen-lit` | определение `:` | src/primitives.fth:118 | 10 |  |
| 730 | `gen-pick-n` | определение `:` | src/primitives.fth:120 | 3 |  |
| 731 | `gen-check-range` | определение `:` | src/primitives.fth:124 | 4 |  |
| 732 | `fc-mark-entry` | определение `:` | src/primitives.fth:133 | 1 |  |
| 733 | `gen-space!` | определение `:` | src/primitives.fth:134 | 2 |  |
| 734 | `gen-spacec!` | определение `:` | src/primitives.fth:135 | 2 |  |
| 735 | `gen-space@` | определение `:` | src/primitives.fth:136 | 2 |  |
| 736 | `gen-spacec@` | определение `:` | src/primitives.fth:137 | 2 |  |
| 737 | `gen-check-entry` | определение `:` | src/primitives.fth:141 | 2 |  |
| 738 | `gen-execute` | определение `:` | src/primitives.fth:147 | 2 |  |
| 739 | `gen-catch` | определение `:` | src/primitives.fth:149 | 2 |  |
| 740 | `gen-colon` | определение `:` | src/primitives.fth:153 | 2 |  |
| 741 | `gen-semicolon` | определение `:` | src/primitives.fth:156 | 2 |  |
| 742 | `gen-variable` | определение `:` | src/primitives.fth:158 | 2 |  |
| 743 | `gen-create` | определение `:` | src/primitives.fth:159 | 2 |  |
| 744 | `gen-allot` | определение `:` | src/primitives.fth:160 | 2 |  |
| 745 | `gen-constant` | определение `:` | src/primitives.fth:161 | 2 |  |
| 746 | `gen-decimal` | определение `:` | src/primitives.fth:162 | 2 |  |
| 747 | `gen-kernel-layout` | определение `:` | src/primitives.fth:164 | 2 |  |
| 748 | `gen-backslash` | определение `:` | src/primitives.fth:167 | 2 |  |
| 749 | `gen-paren` | определение `:` | src/primitives.fth:169 | 2 |  |
| 750 | `gen-char` | определение `:` | src/primitives.fth:170 | 2 |  |
| 751 | `gen-string` | определение `:` | src/primitives.fth:171 | 2 |  |
| 752 | `fc-digit@` | определение `:` | src/primitives.fth:180 | 1 |  |
| 753 | `gen-literal` | определение `:` | src/primitives.fth:182 | 2 |  |
| 754 | `fc-known-xt` | определение `:` | src/primitives.fth:191 | 2 |  |
| 755 | `gen-cost` | определение `:` | src/primitives.fth:192 | 2 |  |
| 756 | `gen-proved?` | определение `:` | src/primitives.fth:194 | 2 |  |
| 757 | `gen-price` | определение `:` | src/primitives.fth:195 | 2 |  |
| 758 | `fc-name2` | определение `:` | src/primitives.fth:197 | 1 |  |
| 759 | `fc-generators` | определение `:` | src/primitives.fth:200 | 1 |  |
| 760 | `+` | генератор | src/primitives.fth:201 | 513 | слово компилятора `gen+` |
| 761 | `-` | генератор | src/primitives.fth:201 | 48 | слово компилятора `gen-` |
| 762 | `*` | генератор | src/primitives.fth:202 | 79 | слово компилятора `gen*` |
| 763 | `/` | генератор | src/primitives.fth:202 | 3 | слово компилятора `gen/` |
| 764 | `mod` | генератор | src/primitives.fth:203 | 1 | слово компилятора `gen-mod` |
| 765 | `and` | генератор | src/primitives.fth:204 | 102 | слово компилятора `gen-and` |
| 766 | `or` | генератор | src/primitives.fth:204 | 42 | слово компилятора `gen-or` |
| 767 | `xor` | генератор | src/primitives.fth:205 | 5 | слово компилятора `gen-xor` |
| 768 | `lshift` | генератор | src/primitives.fth:205 | 79 | слово компилятора `gen-lshift` |
| 769 | `rshift` | генератор | src/primitives.fth:206 | 55 | слово компилятора `gen-rshift` |
| 770 | `=` | генератор | src/primitives.fth:206 | 59 | слово компилятора `gen=` |
| 771 | `<` | генератор | src/primitives.fth:207 | 29 | слово компилятора `gen<` |
| 772 | `u<` | генератор | src/primitives.fth:207 | 13 | слово компилятора `gen-u<` |
| 773 | `0=` | генератор | src/primitives.fth:208 | 78 | слово компилятора `gen-0=` |
| 774 | `2*` | генератор | src/primitives.fth:208 | 28 | слово компилятора `gen-2*` |
| 775 | `1+` | генератор | src/primitives.fth:209 | 42 | слово компилятора `gen-1+` |
| 776 | `1-` | генератор | src/primitives.fth:209 | 43 | слово компилятора `gen-1-` |
| 777 | `cells` | генератор | src/primitives.fth:210 | 251 | слово компилятора `gen-cells` |
| 778 | `cell+` | генератор | src/primitives.fth:210 | 53 | слово компилятора `gen-cell+` |
| 779 | `dup` | генератор | src/primitives.fth:211 | 281 | слово компилятора `gen-dup` |
| 780 | `drop` | генератор | src/primitives.fth:211 | 188 | слово компилятора `gen-drop` |
| 781 | `swap` | генератор | src/primitives.fth:212 | 126 | слово компилятора `gen-swap` |
| 782 | `over` | генератор | src/primitives.fth:212 | 82 | слово компилятора `gen-over` |
| 783 | `rot` | генератор | src/primitives.fth:213 | 38 | слово компилятора `gen-rot` |
| 784 | `pick` | генератор | src/primitives.fth:213 | 49 | слово компилятора `gen-pick` |
| 785 | `roll` | генератор | src/primitives.fth:214 | 5 | слово компилятора `gen-roll` |
| 786 | `>r` | генератор | src/primitives.fth:214 | 100 | слово компилятора `gen->r` |
| 787 | `r>` | генератор | src/primitives.fth:215 | 104 | слово компилятора `gen-r>` |
| 788 | `r@` | генератор | src/primitives.fth:215 | 94 | слово компилятора `gen-r@` |
| 789 | `i` | генератор | src/primitives.fth:216 | 160 | слово компилятора `gen-r@` |
| 790 | `j` | генератор | src/primitives.fth:216 | 12 | слово компилятора `gen-j` |
| 791 | `@` | генератор | src/primitives.fth:217 | 1098 | слово компилятора `gen-@` |
| 792 | `!` | генератор | src/primitives.fth:217 | 599 | слово компилятора `gen-!` |
| 793 | `c@` | генератор | src/primitives.fth:218 | 22 | слово компилятора `gen-c@` |
| 794 | `c!` | генератор | src/primitives.fth:218 | 17 | слово компилятора `gen-c!` |
| 795 | `space!` | генератор | src/primitives.fth:219 | 1 | слово компилятора `gen-space!` |
| 796 | `spacec!` | генератор | src/primitives.fth:219 | 1 | слово компилятора `gen-spacec!` |
| 797 | `emit` | генератор | src/primitives.fth:221 | 4 | слово компилятора `gen-emit` |
| 798 | `key` | генератор | src/primitives.fth:221 | 1 | слово компилятора `gen-key` |
| 799 | `if` | генератор | src/primitives.fth:222 | 253 | слово компилятора `gen-if` |
| 800 | `else` | генератор | src/primitives.fth:222 | 64 | слово компилятора `gen-else` |
| 801 | `then` | генератор | src/primitives.fth:223 | 253 | слово компилятора `gen-then` |
| 802 | `begin` | генератор | src/primitives.fth:223 | 22 | слово компилятора `gen-begin` |
| 803 | `until` | генератор | src/primitives.fth:224 | 1 | слово компилятора `gen-until` |
| 804 | `while` | генератор | src/primitives.fth:224 | 20 | слово компилятора `gen-while` |
| 805 | `repeat` | генератор | src/primitives.fth:225 | 20 | слово компилятора `gen-repeat` |
| 806 | `again` | генератор | src/primitives.fth:225 | 1 | слово компилятора `gen-again` |
| 807 | `do` | генератор | src/primitives.fth:226 | 30 | слово компилятора `gen-do` |
| 808 | `?do` | генератор | src/primitives.fth:226 | 53 | слово компилятора `gen-?do` |
| 809 | `loop` | генератор | src/primitives.fth:227 | 83 | слово компилятора `gen-loop` |
| 810 | `leave` | генератор | src/primitives.fth:227 | 1 | слово компилятора `gen-leave` |
| 811 | `unloop` | генератор | src/primitives.fth:228 | 6 | слово компилятора `gen-unloop` |
| 812 | `exit` | генератор | src/primitives.fth:228 | 65 | слово компилятора `gen-exit` |
| 813 | `recurse` | генератор | src/primitives.fth:229 | 1 | слово компилятора `gen-recurse` |
| 814 | `execute` | генератор | src/primitives.fth:229 | 10 | слово компилятора `gen-execute` |
| 815 | `[']` | генератор | src/primitives.fth:230 | 134 | слово компилятора `gen-tick` |
| 816 | `catch` | генератор | src/primitives.fth:230 | 1 | слово компилятора `gen-catch` |
| 817 | `throw` | генератор | src/primitives.fth:231 | 74 | слово компилятора `gen-throw` |
| 818 | `:` | генератор | src/primitives.fth:232 | 443 | слово компилятора `gen-colon` |
| 819 | `;` | генератор | src/primitives.fth:232 | 443 | слово компилятора `gen-semicolon` |
| 820 | `variable` | генератор | src/primitives.fth:233 | 287 | слово компилятора `gen-variable` |
| 821 | `create` | генератор | src/primitives.fth:233 | 43 | слово компилятора `gen-create` |
| 822 | `allot` | генератор | src/primitives.fth:234 | 41 | слово компилятора `gen-allot` |
| 823 | `constant` | генератор | src/primitives.fth:234 | 17 | слово компилятора `gen-constant` |
| 824 | `decimal` | генератор | src/primitives.fth:235 | 3 | слово компилятора `gen-decimal` |
| 825 | `kernel-layout` | генератор | src/primitives.fth:235 | 1 | слово компилятора `gen-kernel-layout` |
| 826 | `\` | генератор | src/primitives.fth:236 | 326 | слово компилятора `gen-backslash` |
| 827 | `(` | генератор | src/primitives.fth:236 | 419 | слово компилятора `gen-paren` |
| 828 | `[char]` | генератор | src/primitives.fth:236 | 8 | слово компилятора `gen-char` |
| 829 | `s"` | генератор | src/primitives.fth:237 | 91 | слово компилятора `gen-string` |
| 830 | `literal` | генератор | src/primitives.fth:238 | 445 | слово компилятора `gen-literal` |
| 831 | `0` | цифра (литерал) | src/primitives.fth:241 | 497 | значение 0 |
| 832 | `1` | цифра (литерал) | src/primitives.fth:241 | 397 | значение 1 |
| 833 | `2` | цифра (литерал) | src/primitives.fth:241 | 427 | значение 2 |
| 834 | `3` | цифра (литерал) | src/primitives.fth:241 | 277 | значение 3 |
| 835 | `4` | цифра (литерал) | src/primitives.fth:242 | 222 | значение 4 |
| 836 | `5` | цифра (литерал) | src/primitives.fth:242 | 99 | значение 5 |
| 837 | `6` | цифра (литерал) | src/primitives.fth:242 | 133 | значение 6 |
| 838 | `7` | цифра (литерал) | src/primitives.fth:242 | 42 | значение 7 |
| 839 | `8` | цифра (литерал) | src/primitives.fth:243 | 147 | значение 8 |
| 840 | `9` | цифра (литерал) | src/primitives.fth:243 | 39 | значение 9 |
| 841 | `fc-install-generators` | определение `:` | src/primitives.fth:244 | 1 |  |
| 842 | `heap-start` | данные `create` | src/main.fth:4 | 1 |  |
| 843 | `fc-read` | определение `:` | src/main.fth:7 | 2 |  |
| 844 | `fc-sizes` | определение `:` | src/main.fth:12 | 2 |  |
| 845 | `kn-at` | переменная | src/kernel.fth:12 | 5 |  |
| 846 | `kn-put` | определение `:` | src/kernel.fth:13 | 1 |  |
| 847 | `kn-order` | определение `:` | src/kernel.fth:23 | 1 |  |
| 848 | `kn-compile` | определение `:` | src/kernel.fth:24 | 1 |  |
| 849 | `kn-.n` | определение `:` | src/kernel.fth:25 | 1 |  |
| 850 | `main` | определение `:` | src/kernel.fth:29 | 1 | вариант 2 |
| 851 | `kn-heap-start` | данные `create` | src/kernel.fth:34 | 1 |  |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 84.

## Определены, но не использованы

Слов: 26. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

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
| `fc-depth` | определение `:` | src/forthc.fth:892 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:893 |
| `/mod` | генератор | src/primitives.fth:203 |
| `space@` | генератор | src/primitives.fth:220 |
| `spacec@` | генератор | src/primitives.fth:220 |
| `cost` | генератор | src/primitives.fth:239 |
| `price` | генератор | src/primitives.fth:239 |
| `proved?` | генератор | src/primitives.fth:240 |
| `main` (вариант 1) | определение `:` | src/main.fth:15 |

## Слова, которые при буте исполняет хост

Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки `backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках 82; все они определены в определении языка (генератором в `primitives.fth` или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: `!` `*` `+` `+!` `-` `-rot` `/` `/string` `0<` `0<>` `0=` `0>` `1+` `1-` `2!` `2*` `2@` `2drop` `2dup` `2over` `2swap` `<` `<>` `=` `>` `>in` `>r` `?do` `?dup` `@` `again` `allocate` `and` `begin` `c!` `c@` `cell+` `cells` `cmove` `cmove>` `compare` `decimal` `do` `drop` `dup` `else` `execute` `exit` `fill` `free` `i` `if` `invert` `j` `leave` `loop` `lshift` `max` `min` `negate` `nip` `or` `over` `pick` `r>` `r@` `repeat` `roll` `rot` `rshift` `source` `swap` `then` `throw` `tuck` `type` `u<` `u>` `unloop` `until` `while` `xor`.

Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро читает каналом `key`), `source` и `>in` — слова только этого пути.
