# Ядро языка (14.8)

Файл порождается `make -C space/language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`tools/research/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 779** (определение `:` — 384, переменная — 255, генератор — 71, данные `create` — 38, константа — 15, цифра (литерал) — 10, основание — 6).

## Основание

Основание — слова-копирования: генераторы строки (копия — приёмник и источник) и слоя (ячейка строк) из `src/backend.fth`. Определение инструкции — она сама: тело этих слов не сводится к другим словам языка, а строка и слой — сами инструкции индексного пространства.

| Слово | Что порождает | Файл:строка |
|---|---|---|
| `cc-copy` | строка: копирование n бит из источника в приёмник | src/backend.fth:119 |
| `cc-link-row` | строка: копирование ссылки на следующий слой | src/backend.fth:118 |
| `cc-row` | строка: добавляет строку в слой | src/backend.fth:181 |
| `cc-new-record` | слой: новый слой в ячейке | src/backend.fth:143 |
| `cc-lone` | слой: отдельный слой в новой ячейке | src/backend.fth:147 |
| `cc-layer` | слой: следующий слой последовательности | src/backend.fth:150 |

## Слова ядра

Вид: генератор (слово словаря, исполняемое при компиляции, `doc/generators.md`; в пояснении слово компилятора), определение `:`, переменная, константа, данные `create`, цифра (литерал, `doc/literals.md`), основание. «Исп.» — число ссылок из других слов (цифры — и из чисел определения). Повторное определение имени — «вариант N» (старое имя остаётся у прежних ссылок).

| № | Слово | Вид | Файл:строка | Исп. | Пояснение |
|---|---|---|---|---|---|
| 1 | `nip` | определение `:` | src/prelude.fth:6 | 21 |  |
| 2 | `tuck` | определение `:` | src/prelude.fth:7 | 9 |  |
| 3 | `-rot` | определение `:` | src/prelude.fth:8 | 3 |  |
| 4 | `2dup` | определение `:` | src/prelude.fth:9 | 9 |  |
| 5 | `2drop` | определение `:` | src/prelude.fth:10 | 16 |  |
| 6 | `2swap` | определение `:` | src/prelude.fth:11 | 6 |  |
| 7 | `2over` | определение `:` | src/prelude.fth:12 | 2 |  |
| 8 | `?dup` | определение `:` | src/prelude.fth:13 | 13 |  |
| 9 | `negate` | определение `:` | src/prelude.fth:14 | 5 |  |
| 10 | `invert` | определение `:` | src/prelude.fth:15 | 1 |  |
| 11 | `>` | определение `:` | src/prelude.fth:16 | 10 |  |
| 12 | `u>` | определение `:` | src/prelude.fth:17 | 5 |  |
| 13 | `<>` | определение `:` | src/prelude.fth:18 | 10 |  |
| 14 | `0<` | определение `:` | src/prelude.fth:19 | 4 |  |
| 15 | `0>` | определение `:` | src/prelude.fth:20 | 3 |  |
| 16 | `0<>` | определение `:` | src/prelude.fth:21 | 4 |  |
| 17 | `max` | определение `:` | src/prelude.fth:22 | 13 |  |
| 18 | `min` | определение `:` | src/prelude.fth:23 | 5 |  |
| 19 | `+!` | определение `:` | src/prelude.fth:24 | 44 |  |
| 20 | `2@` | определение `:` | src/prelude.fth:25 | 4 |  |
| 21 | `2!` | определение `:` | src/prelude.fth:26 | 2 |  |
| 22 | `fill-cell` | переменная | src/prelude.fth:28 | 2 |  |
| 23 | `fill` | определение `:` | src/prelude.fth:29 | 8 |  |
| 24 | `cmove` | определение `:` | src/prelude.fth:33 | 13 |  |
| 25 | `cmove>` | определение `:` | src/prelude.fth:37 | 1 |  |
| 26 | `/string` | определение `:` | src/prelude.fth:38 | 2 |  |
| 27 | `type` | определение `:` | src/prelude.fth:39 | 6 |  |
| 28 | `compare` | определение `:` | src/prelude.fth:40 | 2 |  |
| 29 | `heap-ptr` | переменная | src/prelude.fth:44 | 5 |  |
| 30 | `heap-last` | переменная | src/prelude.fth:44 | 2 |  |
| 31 | `heap-end` | константа | src/prelude.fth:44 | 1 |  |
| 32 | `allocate` | определение `:` | src/prelude.fth:45 | 13 |  |
| 33 | `free` | определение `:` | src/prelude.fth:48 | 5 |  |
| 34 | `source` | определение `:` | src/prelude.fth:50 | 2 |  |
| 35 | `>in` | переменная | src/prelude.fth:51 | 2 |  |
| 36 | `cc-size` | переменная | src/backend.fth:14 | 7 |  |
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
| 51 | `cc-layer-bits` | определение `:` | src/backend.fth:24 | 6 |  |
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
| 73 | `cc-pending` | переменная | src/backend.fth:95 | 9 |  |
| 74 | `cc-head` | переменная | src/backend.fth:95 | 6 |  |
| 75 | `cc-next-cell` | переменная | src/backend.fth:95 | 6 |  |
| 76 | `cc-seq#` | переменная | src/backend.fth:96 | 8 |  |
| 77 | `cc-seq-first` | переменная | src/backend.fth:96 | 3 |  |
| 78 | `cc-seq-entry` | переменная | src/backend.fth:96 | 2 |  |
| 79 | `cc-seq-last` | переменная | src/backend.fth:96 | 2 |  |
| 80 | `cc-foff` | данные `create` | src/backend.fth:98 | 2 |  |
| 81 | `cc-foff-init` | определение `:` | src/backend.fth:99 | 1 |  |
| 82 | `cc-machine` | определение `:` | src/backend.fth:100 | 1 |  |
| 83 | `cc-field` | определение `:` | src/backend.fth:117 | 33 |  |
| 84 | `cc-link-row` | основание | src/backend.fth:118 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 85 | `cc-copy` | основание | src/backend.fth:119 | 68 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 86 | `cc-builder` | определение `:` | src/backend.fth:121 | 1 |  |
| 87 | `cc-new-cell` | определение `:` | src/backend.fth:122 | 13 |  |
| 88 | `cc-branch-bit` | определение `:` | src/backend.fth:125 | 13 |  |
| 89 | `cc-branch-step` | определение `:` | src/backend.fth:126 | 4 |  |
| 90 | `cc-group` | определение `:` | src/backend.fth:128 | 5 |  |
| 91 | `cc-layer-cell` | определение `:` | src/backend.fth:131 | 33 |  |
| 92 | `cc-next!` | определение `:` | src/backend.fth:132 | 20 |  |
| 93 | `cc-count` | определение `:` | src/backend.fth:133 | 6 |  |
| 94 | `cc-row-addr` | определение `:` | src/backend.fth:134 | 3 |  |
| 95 | `cc-pending@` | определение `:` | src/backend.fth:135 | 4 |  |
| 96 | `cc-encode-layer` | определение `:` | src/backend.fth:136 | 1 |  |
| 97 | `cc-write` | определение `:` | src/backend.fth:141 | 2 |  |
| 98 | `cc-write-oldest` | определение `:` | src/backend.fth:142 | 1 |  |
| 99 | `cc-new-record` | основание | src/backend.fth:143 | 10 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 100 | `cc-lone` | основание | src/backend.fth:147 | 5 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 101 | `cc-seq` | определение `:` | src/backend.fth:148 | 8 |  |
| 102 | `cc-last` | определение `:` | src/backend.fth:149 | 2 |  |
| 103 | `cc-layer` | основание | src/backend.fth:150 | 69 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 104 | `cc-entry` | определение `:` | src/backend.fth:155 | 4 |  |
| 105 | `cc-jump` | определение `:` | src/backend.fth:156 | 11 |  |
| 106 | `cc-l1` | переменная | src/backend.fth:157 | 4 |  |
| 107 | `cc-h1` | переменная | src/backend.fth:157 | 3 |  |
| 108 | `cc-l2` | переменная | src/backend.fth:157 | 4 |  |
| 109 | `cc-h2` | переменная | src/backend.fth:157 | 3 |  |
| 110 | `cc-ra` | переменная | src/backend.fth:158 | 2 |  |
| 111 | `cc-rb` | переменная | src/backend.fth:158 | 2 |  |
| 112 | `cc-cur` | переменная | src/backend.fth:158 | 7 |  |
| 113 | `cc-clash?` | определение `:` | src/backend.fth:160 | 1 |  |
| 114 | `cc-row-clash?` | определение `:` | src/backend.fth:165 | 1 |  |
| 115 | `cc-new-row` | данные `create` | src/backend.fth:170 | 6 |  |
| 116 | `cc-row-set` | определение `:` | src/backend.fth:171 | 2 |  |
| 117 | `cc-full?` | определение `:` | src/backend.fth:173 | 2 |  |
| 118 | `cc-clashes?` | определение `:` | src/backend.fth:174 | 2 |  |
| 119 | `cc-fits?` | определение `:` | src/backend.fth:179 | 2 |  |
| 120 | `cc-row` | основание | src/backend.fth:181 | 67 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 121 | `cc-flush` | определение `:` | src/backend.fth:185 | 12 |  |
| 122 | `cc-finish` | определение `:` | src/backend.fth:188 | 1 |  |
| 123 | `cc-t1` | переменная | src/compute.fth:10 | 25 |  |
| 124 | `cc-t2` | переменная | src/compute.fth:10 | 13 |  |
| 125 | `cc-t3` | переменная | src/compute.fth:10 | 7 |  |
| 126 | `cc-t4` | переменная | src/compute.fth:10 | 4 |  |
| 127 | `cc-t5` | переменная | src/compute.fth:10 | 8 |  |
| 128 | `cc-lo` | переменная | src/compute.fth:11 | 5 |  |
| 129 | `cc-hi` | переменная | src/compute.fth:11 | 2 |  |
| 130 | `cc-l0` | переменная | src/compute.fth:12 | 21 |  |
| 131 | `cc-l1` | переменная | src/compute.fth:12 | 13 | вариант 2 |
| 132 | `cc-l2` | переменная | src/compute.fth:12 | 8 | вариант 2 |
| 133 | `cc-l3` | переменная | src/compute.fth:12 | 7 |  |
| 134 | `cc-l4` | переменная | src/compute.fth:12 | 7 |  |
| 135 | `cc-l5` | переменная | src/compute.fth:12 | 6 |  |
| 136 | `cc-work` | определение `:` | src/compute.fth:13 | 3 |  |
| 137 | `cc-link-slot` | определение `:` | src/compute.fth:15 | 6 |  |
| 138 | `cc-item-cells` | константа | src/compute.fth:17 | 1 |  |
| 139 | `cc-max-items` | константа | src/compute.fth:17 | 2 |  |
| 140 | `cc-items` | данные `create` | src/compute.fth:18 | 1 |  |
| 141 | `cc-nitems` | переменная | src/compute.fth:19 | 8 |  |
| 142 | `cc-item@` | определение `:` | src/compute.fth:20 | 6 |  |
| 143 | `cc-lookups-begin` | определение `:` | src/compute.fth:21 | 14 |  |
| 144 | `cc-item` | определение `:` | src/compute.fth:22 | 12 |  |
| 145 | `cc-seg` | определение `:` | src/compute.fth:27 | 18 |  |
| 146 | `cc-sl` | данные `create` | src/compute.fth:33 | 2 |  |
| 147 | `cc-sh` | данные `create` | src/compute.fth:33 | 2 |  |
| 148 | `cc-read-layer` | данные `create` | src/compute.fth:34 | 2 |  |
| 149 | `cc-read-slot` | данные `create` | src/compute.fth:34 | 2 |  |
| 150 | `cc-used` | данные `create` | src/compute.fth:35 | 2 |  |
| 151 | `cc-nused` | переменная | src/compute.fth:35 | 5 |  |
| 152 | `cc-rl` | переменная | src/compute.fth:35 | 6 |  |
| 153 | `cc-pk` | переменная | src/compute.fth:35 | 4 |  |
| 154 | `cc-pkl` | переменная | src/compute.fth:35 | 4 |  |
| 155 | `cc-npatches` | определение `:` | src/compute.fth:36 | 1 |  |
| 156 | `cc-used?` | определение `:` | src/compute.fth:37 | 1 |  |
| 157 | `cc-place-reads` | определение `:` | src/compute.fth:39 | 1 |  |
| 158 | `cc-patch` | определение `:` | src/compute.fth:51 | 1 |  |
| 159 | `cc-lookups` | определение `:` | src/compute.fth:60 | 14 |  |
| 160 | `cc-al` | данные `create` | src/compute.fth:67 | 2 |  |
| 161 | `cc-ar` | данные `create` | src/compute.fth:67 | 2 |  |
| 162 | `cc-ax` | переменная | src/compute.fth:68 | 4 |  |
| 163 | `cc-aa` | переменная | src/compute.fth:68 | 2 |  |
| 164 | `cc-ab` | переменная | src/compute.fth:68 | 2 |  |
| 165 | `cc-atab` | переменная | src/compute.fth:68 | 2 |  |
| 166 | `cc-acarry` | переменная | src/compute.fth:68 | 2 |  |
| 167 | `cc-al@` | определение `:` | src/compute.fth:69 | 8 |  |
| 168 | `cc-rd` | определение `:` | src/compute.fth:70 | 3 |  |
| 169 | `cc-adder-patch` | определение `:` | src/compute.fth:71 | 4 |  |
| 170 | `cc-adder` | определение `:` | src/compute.fth:76 | 5 |  |
| 171 | `cc-dsrc` | переменная | src/compute.fth:93 | 3 |  |
| 172 | `cc-dk` | переменная | src/compute.fth:93 | 5 |  |
| 173 | `cc-dg` | переменная | src/compute.fth:93 | 3 |  |
| 174 | `cc-dp` | переменная | src/compute.fth:93 | 3 |  |
| 175 | `cc-dx` | переменная | src/compute.fth:93 | 4 |  |
| 176 | `cc-decide` | определение `:` | src/compute.fth:94 | 2 |  |
| 177 | `cc-table-at` | переменная | src/compute.fth:102 | 4 |  |
| 178 | `cc-table-limit` | переменная | src/compute.fth:102 | 2 |  |
| 179 | `cc-tbuf` | переменная | src/compute.fth:102 | 8 |  |
| 180 | `cc-tx` | переменная | src/compute.fth:103 | 8 |  |
| 181 | `cc-tbits` | переменная | src/compute.fth:103 | 5 |  |
| 182 | `cc-ts` | переменная | src/compute.fth:103 | 6 |  |
| 183 | `cc-tsize` | переменная | src/compute.fth:103 | 7 |  |
| 184 | `cc-tbase` | переменная | src/compute.fth:103 | 4 |  |
| 185 | `cc-tper` | переменная | src/compute.fth:103 | 4 |  |
| 186 | `cc-tables` | определение `:` | src/compute.fth:104 | 2 |  |
| 187 | `cc-table-area` | определение `:` | src/compute.fth:105 | 3 |  |
| 188 | `cc-table-done` | определение `:` | src/compute.fth:113 | 3 |  |
| 189 | `cc-table` | определение `:` | src/compute.fth:116 | 24 |  |
| 190 | `cc-table2` | определение `:` | src/compute.fth:134 | 1 |  |
| 191 | `cc-add-entry` | определение `:` | src/compute.fth:141 | 1 |  |
| 192 | `cc-sub-entry` | определение `:` | src/compute.fth:143 | 2 |  |
| 193 | `cc-xor-entry` | определение `:` | src/compute.fth:145 | 1 |  |
| 194 | `cc-or-entry` | определение `:` | src/compute.fth:146 | 1 |  |
| 195 | `cc-and-entry` | определение `:` | src/compute.fth:147 | 1 |  |
| 196 | `cc-or8-entry` | определение `:` | src/compute.fth:148 | 2 |  |
| 197 | `cc-fz` | переменная | src/compute.fth:149 | 3 |  |
| 198 | `cc-fu` | переменная | src/compute.fth:149 | 4 |  |
| 199 | `cc-fs` | переменная | src/compute.fth:149 | 3 |  |
| 200 | `cc-pair` | определение `:` | src/compute.fth:150 | 6 |  |
| 201 | `cc-flags-entry` | определение `:` | src/compute.fth:151 | 1 |  |
| 202 | `cc-not5-entry` | определение `:` | src/compute.fth:158 | 1 |  |
| 203 | `cc-sign-entry` | определение `:` | src/compute.fth:159 | 1 |  |
| 204 | `cc-fill24-entry` | определение `:` | src/compute.fth:160 | 1 |  |
| 205 | `cc-fill16-entry` | определение `:` | src/compute.fth:161 | 1 |  |
| 206 | `cc-inc1-entry` | определение `:` | src/compute.fth:162 | 1 |  |
| 207 | `cc-inc2-entry` | определение `:` | src/compute.fth:163 | 1 |  |
| 208 | `cc-t-add` | переменная | src/compute.fth:164 | 6 |  |
| 209 | `cc-t-sub` | переменная | src/compute.fth:164 | 5 |  |
| 210 | `cc-t-xor` | переменная | src/compute.fth:164 | 5 |  |
| 211 | `cc-t-or` | переменная | src/compute.fth:164 | 2 |  |
| 212 | `cc-t-and` | переменная | src/compute.fth:164 | 2 |  |
| 213 | `cc-t-or8` | переменная | src/compute.fth:165 | 3 |  |
| 214 | `cc-t-flags` | переменная | src/compute.fth:165 | 2 |  |
| 215 | `cc-t-not5` | переменная | src/compute.fth:165 | 2 |  |
| 216 | `cc-t-sign32` | переменная | src/compute.fth:165 | 2 |  |
| 217 | `cc-t-fill24` | переменная | src/compute.fth:166 | 1 |  |
| 218 | `cc-t-fill16` | переменная | src/compute.fth:166 | 1 |  |
| 219 | `cc-t-inc1` | переменная | src/compute.fth:166 | 1 |  |
| 220 | `cc-t-inc2` | переменная | src/compute.fth:166 | 1 |  |
| 221 | `cc-standard-tables` | определение `:` | src/compute.fth:167 | 1 |  |
| 222 | `cc-oo` | переменная | src/compute.fth:176 | 2 |  |
| 223 | `cc-os` | переменная | src/compute.fth:176 | 2 |  |
| 224 | `cc-ol` | переменная | src/compute.fth:176 | 4 |  |
| 225 | `cc-oh` | переменная | src/compute.fth:176 | 3 |  |
| 226 | `cc-or-chunks` | определение `:` | src/compute.fth:177 | 3 |  |
| 227 | `cc-cr` | переменная | src/compute.fth:183 | 5 |  |
| 228 | `cc-ca` | переменная | src/compute.fth:183 | 4 |  |
| 229 | `cc-cb` | переменная | src/compute.fth:183 | 4 |  |
| 230 | `cc-logic` | определение `:` | src/compute.fth:190 | 4 |  |
| 231 | `cc-sres` | переменная | src/compute.fth:196 | 3 |  |
| 232 | `cc-sa` | переменная | src/compute.fth:196 | 7 |  |
| 233 | `cc-samt` | переменная | src/compute.fth:196 | 8 |  |
| 234 | `cc-sw` | переменная | src/compute.fth:196 | 9 |  |
| 235 | `cc-szero` | переменная | src/compute.fth:196 | 4 |  |
| 236 | `cc-sarg` | переменная | src/compute.fth:197 | 6 |  |
| 237 | `cc-sign` | переменная | src/compute.fth:197 | 6 |  |
| 238 | `cc-shift-row` | определение `:` | src/compute.fth:198 | 3 |  |
| 239 | `cc-shift-patch` | определение `:` | src/compute.fth:199 | 6 |  |
| 240 | `cc-shift-right` | определение `:` | src/compute.fth:201 | 1 |  |
| 241 | `cc-shift-left` | определение `:` | src/compute.fth:218 | 1 |  |
| 242 | `fc-size` | константа | src/forthc.fth:11 | 2 |  |
| 243 | `fc-cellb` | константа | src/forthc.fth:11 | 5 |  |
| 244 | `fc-l` | константа | src/forthc.fth:11 | 1 |  |
| 245 | `fc-a` | константа | src/forthc.fth:11 | 3 |  |
| 246 | `fc-d` | переменная | src/forthc.fth:16 | 2 |  |
| 247 | `fc-first` | переменная | src/forthc.fth:16 | 2 |  |
| 248 | `fc-layout` | определение `:` | src/forthc.fth:17 | 1 |  |
| 249 | `fc-d+` | определение `:` | src/forthc.fth:19 | 28 |  |
| 250 | `fc-sp` | определение `:` | src/forthc.fth:20 | 6 |  |
| 251 | `fc-rp` | определение `:` | src/forthc.fth:20 | 18 |  |
| 252 | `fc-handler` | определение `:` | src/forthc.fth:20 | 6 |  |
| 253 | `fc-code` | определение `:` | src/forthc.fth:20 | 4 |  |
| 254 | `fc-regs` | определение `:` | src/forthc.fth:21 | 2 |  |
| 255 | `fc-nregs` | константа | src/forthc.fth:21 | 2 |  |
| 256 | `fc-tmp` | определение `:` | src/forthc.fth:22 | 10 |  |
| 257 | `fc-xr` | определение `:` | src/forthc.fth:22 | 10 |  |
| 258 | `fc-z` | определение `:` | src/forthc.fth:22 | 7 |  |
| 259 | `fc-idx` | определение `:` | src/forthc.fth:22 | 4 |  |
| 260 | `fc-flt` | определение `:` | src/forthc.fth:23 | 4 |  |
| 261 | `fc-ma` | определение `:` | src/forthc.fth:24 | 6 |  |
| 262 | `fc-mb` | определение `:` | src/forthc.fth:24 | 6 |  |
| 263 | `fc-mp` | определение `:` | src/forthc.fth:24 | 2 |  |
| 264 | `fc-mq` | определение `:` | src/forthc.fth:24 | 3 |  |
| 265 | `fc-mr` | определение `:` | src/forthc.fth:24 | 3 |  |
| 266 | `fc-zero` | определение `:` | src/forthc.fth:25 | 10 |  |
| 267 | `fc-consts` | определение `:` | src/forthc.fth:25 | 3 |  |
| 268 | `fc-sw` | определение `:` | src/forthc.fth:26 | 2 |  |
| 269 | `fc-su` | определение `:` | src/forthc.fth:26 | 1 |  |
| 270 | `fc-key` | определение `:` | src/forthc.fth:26 | 3 |  |
| 271 | `fc-bp` | определение `:` | src/forthc.fth:26 | 2 |  |
| 272 | `fc-tab` | определение `:` | src/forthc.fth:27 | 1 |  |
| 273 | `fc-stk` | определение `:` | src/forthc.fth:27 | 3 |  |
| 274 | `fc-rstk` | определение `:` | src/forthc.fth:28 | 14 |  |
| 275 | `fc-scr0` | определение `:` | src/forthc.fth:28 | 1 |  |
| 276 | `fc-links` | определение `:` | src/forthc.fth:29 | 2 |  |
| 277 | `fc-max-links` | константа | src/forthc.fth:29 | 1 |  |
| 278 | `fc-link-chunk` | константа | src/forthc.fth:29 | 2 |  |
| 279 | `fc-mem` | определение `:` | src/forthc.fth:30 | 4 |  |
| 280 | `fc-mw` | константа | src/forthc.fth:30 | 5 |  |
| 281 | `fc-htab` | определение `:` | src/forthc.fth:30 | 1 |  |
| 282 | `fc-data-start` | константа | src/forthc.fth:31 | 1 |  |
| 283 | `fc-off` | данные `create` | src/forthc.fth:34 | 2 |  |
| 284 | `fc-oc` | переменная | src/forthc.fth:34 | 2 |  |
| 285 | `fc-t-rev8` | переменная | src/forthc.fth:35 | 3 |  |
| 286 | `fc-t-zero32` | переменная | src/forthc.fth:35 | 2 |  |
| 287 | `fc-t-nz2` | переменная | src/forthc.fth:35 | 2 |  |
| 288 | `fc-t-lt32` | переменная | src/forthc.fth:35 | 2 |  |
| 289 | `fc-t-or8b` | переменная | src/forthc.fth:36 | 2 |  |
| 290 | `fc-t-fault` | переменная | src/forthc.fth:36 | 2 |  |
| 291 | `fc-t-xr2` | переменная | src/forthc.fth:36 | 2 |  |
| 292 | `fc-t-ult32` | переменная | src/forthc.fth:36 | 2 |  |
| 293 | `fc-t-bytepos` | переменная | src/forthc.fth:36 | 2 |  |
| 294 | `fc-off@` | определение `:` | src/forthc.fth:37 | 3 |  |
| 295 | `fc-off-table` | определение `:` | src/forthc.fth:39 | 1 |  |
| 296 | `fc-rev-entry` | определение `:` | src/forthc.fth:42 | 1 |  |
| 297 | `fc-zero-entry` | определение `:` | src/forthc.fth:43 | 1 |  |
| 298 | `fc-nz-entry` | определение `:` | src/forthc.fth:44 | 1 |  |
| 299 | `fc-lt-entry` | определение `:` | src/forthc.fth:45 | 1 |  |
| 300 | `fc-fault-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 301 | `fc-xr2-entry` | определение `:` | src/forthc.fth:51 | 1 |  |
| 302 | `fc-ult-entry` | определение `:` | src/forthc.fth:52 | 1 |  |
| 303 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:54 | 1 |  |
| 304 | `fc-tables` | определение `:` | src/forthc.fth:55 | 1 |  |
| 305 | `fc-mul4-entry` | определение `:` | src/forthc.fth:68 | 1 |  |
| 306 | `fc-qsel-entry` | определение `:` | src/forthc.fth:71 | 1 |  |
| 307 | `fc-max-consts` | переменная | src/forthc.fth:76 | 5 | вход бута (хост) |
| 308 | `fc-ck` | переменная | src/forthc.fth:76 | 3 |  |
| 309 | `fc-nconsts` | переменная | src/forthc.fth:76 | 7 |  |
| 310 | `fc-nbuckets` | переменная | src/forthc.fth:77 | 9 | вход бута (хост) |
| 311 | `fc-cbk` | переменная | src/forthc.fth:77 | 3 |  |
| 312 | `fc-ck@` | определение `:` | src/forthc.fth:78 | 3 |  |
| 313 | `fc-chash` | определение `:` | src/forthc.fth:79 | 1 |  |
| 314 | `fc-cb` | переменная | src/forthc.fth:80 | 3 |  |
| 315 | `fc-const2` | определение `:` | src/forthc.fth:81 | 1 |  |
| 316 | `fc-const` | определение `:` | src/forthc.fth:91 | 4 |  |
| 317 | `fc-lit` | определение `:` | src/forthc.fth:99 | 3 |  |
| 318 | `fc-bit0` | определение `:` | src/forthc.fth:100 | 1 |  |
| 319 | `fc-bit1` | определение `:` | src/forthc.fth:101 | 1 |  |
| 320 | `fc-length` | определение `:` | src/forthc.fth:102 | 1 |  |
| 321 | `fc-lit-of` | определение `:` | src/forthc.fth:103 | 2 |  |
| 322 | `fc-load` | определение `:` | src/forthc.fth:107 | 2 |  |
| 323 | `fc-nlinks` | переменная | src/forthc.fth:111 | 5 |  |
| 324 | `fc-link-buf` | переменная | src/forthc.fth:111 | 4 |  |
| 325 | `fc-nbuf` | переменная | src/forthc.fth:111 | 8 |  |
| 326 | `fc-put-links` | определение `:` | src/forthc.fth:112 | 2 |  |
| 327 | `fc-link-const` | определение `:` | src/forthc.fth:116 | 4 |  |
| 328 | `fc-eight` | данные `create` | src/forthc.fth:121 | 5 |  |
| 329 | `fc-zeros` | данные `create` | src/forthc.fth:121 | 5 |  |
| 330 | `fc-put-consts` | определение `:` | src/forthc.fth:122 | 1 |  |
| 331 | `fc-cache` | данные `create` | src/forthc.fth:130 | 8 |  |
| 332 | `fc-n` | переменная | src/forthc.fth:130 | 31 |  |
| 333 | `fc-pin` | данные `create` | src/forthc.fth:131 | 7 |  |
| 334 | `fc-npin` | переменная | src/forthc.fth:131 | 17 |  |
| 335 | `fc-c@` | определение `:` | src/forthc.fth:132 | 8 |  |
| 336 | `fc-push` | определение `:` | src/forthc.fth:133 | 29 |  |
| 337 | `fc-pop1` | определение `:` | src/forthc.fth:134 | 28 |  |
| 338 | `fc-in?` | определение `:` | src/forthc.fth:135 | 3 |  |
| 339 | `fc-reg` | определение `:` | src/forthc.fth:136 | 16 |  |
| 340 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:141 | 1 |  |
| 341 | `fc-scr` | переменная | src/forthc.fth:142 | 3 |  |
| 342 | `fc-scratch` | определение `:` | src/forthc.fth:143 | 11 |  |
| 343 | `fc-offs` | данные `create` | src/forthc.fth:147 | 5 |  |
| 344 | `fc-noff` | переменная | src/forthc.fth:147 | 9 |  |
| 345 | `fc-ptr` | переменная | src/forthc.fth:147 | 4 |  |
| 346 | `fc-adjust` | определение `:` | src/forthc.fth:149 | 7 |  |
| 347 | `fc-prow` | данные `create` | src/forthc.fth:155 | 2 |  |
| 348 | `fc-nrow` | переменная | src/forthc.fth:155 | 8 |  |
| 349 | `fc-pl` | данные `create` | src/forthc.fth:156 | 2 |  |
| 350 | `fc-pslot` | данные `create` | src/forthc.fth:156 | 2 |  |
| 351 | `fc-rl` | переменная | src/forthc.fth:157 | 3 |  |
| 352 | `fc-f0` | переменная | src/forthc.fth:157 | 2 |  |
| 353 | `fc-f1` | переменная | src/forthc.fth:157 | 2 |  |
| 354 | `fc-psh` | переменная | src/forthc.fth:157 | 2 |  |
| 355 | `fc-row+` | определение `:` | src/forthc.fth:158 | 3 |  |
| 356 | `fc-4@` | определение `:` | src/forthc.fth:160 | 3 |  |
| 357 | `fc-patched` | определение `:` | src/forthc.fth:162 | 3 |  |
| 358 | `fc-popped` | данные `create` | src/forthc.fth:174 | 2 |  |
| 359 | `fc-srcs` | данные `create` | src/forthc.fth:174 | 16 |  |
| 360 | `fc-nsrc` | переменная | src/forthc.fth:174 | 21 |  |
| 361 | `fc-mbase` | переменная | src/forthc.fth:175 | 8 |  |
| 362 | `fc-mptr` | переменная | src/forthc.fth:175 | 4 |  |
| 363 | `fc-mn` | переменная | src/forthc.fth:175 | 7 |  |
| 364 | `fc-mw2` | переменная | src/forthc.fth:175 | 6 |  |
| 365 | `fc-popped@` | определение `:` | src/forthc.fth:176 | 10 |  |
| 366 | `fc-shift` | определение `:` | src/forthc.fth:177 | 4 |  |
| 367 | `fc-mem-pop` | определение `:` | src/forthc.fth:178 | 5 |  |
| 368 | `fc-push-group` | определение `:` | src/forthc.fth:186 | 2 |  |
| 369 | `fc-dup-at` | определение `:` | src/forthc.fth:194 | 1 |  |
| 370 | `fc-rest` | данные `create` | src/forthc.fth:196 | 2 |  |
| 371 | `fc-nrest` | переменная | src/forthc.fth:196 | 3 |  |
| 372 | `fc-mem-push` | определение `:` | src/forthc.fth:197 | 8 |  |
| 373 | `fc-src1` | определение `:` | src/forthc.fth:203 | 3 |  |
| 374 | `fc-need` | определение `:` | src/forthc.fth:205 | 13 |  |
| 375 | `fc-spill` | определение `:` | src/forthc.fth:212 | 19 |  |
| 376 | `fc-pop` | определение `:` | src/forthc.fth:218 | 13 |  |
| 377 | `fc-live` | переменная | src/forthc.fth:221 | 8 |  |
| 378 | `fc-tramp` | переменная | src/forthc.fth:221 | 5 |  |
| 379 | `fc-ex` | переменная | src/forthc.fth:221 | 4 |  |
| 380 | `fc-thrower` | переменная | src/forthc.fth:221 | 4 |  |
| 381 | `fc-jump` | определение `:` | src/forthc.fth:222 | 7 |  |
| 382 | `fc-end` | определение `:` | src/forthc.fth:223 | 14 |  |
| 383 | `fc-begin-block` | определение `:` | src/forthc.fth:225 | 24 |  |
| 384 | `fc-rows1` | определение `:` | src/forthc.fth:229 | 15 |  |
| 385 | `fc-nonzero` | определение `:` | src/forthc.fth:230 | 2 |  |
| 386 | `fc-branch` | определение `:` | src/forthc.fth:233 | 6 |  |
| 387 | `fc-call` | определение `:` | src/forthc.fth:234 | 4 |  |
| 388 | `fc-v0` | переменная | src/forthc.fth:237 | 2 |  |
| 389 | `fc-v1` | переменная | src/forthc.fth:237 | 2 |  |
| 390 | `fc-call-indirect` | определение `:` | src/forthc.fth:238 | 2 |  |
| 391 | `fc-push-frame` | определение `:` | src/forthc.fth:245 | 2 |  |
| 392 | `fc-restore` | определение `:` | src/forthc.fth:248 | 3 |  |
| 393 | `fc-build-thrower` | определение `:` | src/forthc.fth:250 | 1 |  |
| 394 | `fc-throw` | определение `:` | src/forthc.fth:256 | 1 |  |
| 395 | `fc-catch` | определение `:` | src/forthc.fth:259 | 1 |  |
| 396 | `fc-ret-p` | переменная | src/forthc.fth:268 | 3 |  |
| 397 | `fc-ret-l` | переменная | src/forthc.fth:268 | 4 |  |
| 398 | `fc-ret` | определение `:` | src/forthc.fth:269 | 3 |  |
| 399 | `fc-ca` | переменная | src/forthc.fth:277 | 6 |  |
| 400 | `fc-cl0` | переменная | src/forthc.fth:277 | 5 |  |
| 401 | `fc-cl1` | переменная | src/forthc.fth:277 | 5 |  |
| 402 | `fc-cr` | переменная | src/forthc.fth:277 | 7 |  |
| 403 | `fc-cg` | переменная | src/forthc.fth:277 | 4 |  |
| 404 | `fc-cx` | переменная | src/forthc.fth:277 | 4 |  |
| 405 | `fc-cv` | переменная | src/forthc.fth:278 | 3 |  |
| 406 | `fc-cres` | переменная | src/forthc.fth:278 | 6 |  |
| 407 | `fc-cslot` | переменная | src/forthc.fth:278 | 3 |  |
| 408 | `fc-csh` | переменная | src/forthc.fth:278 | 2 |  |
| 409 | `fc-chk-read` | определение `:` | src/forthc.fth:280 | 4 |  |
| 410 | `fc-chk-seg` | определение `:` | src/forthc.fth:283 | 5 |  |
| 411 | `fc-cmode` | переменная | src/forthc.fth:289 | 9 |  |
| 412 | `fc-ar` | переменная | src/forthc.fth:289 | 7 |  |
| 413 | `fc-as` | переменная | src/forthc.fth:289 | 2 |  |
| 414 | `fc-af` | переменная | src/forthc.fth:289 | 2 |  |
| 415 | `fc-al0` | переменная | src/forthc.fth:289 | 2 |  |
| 416 | `fc-al1` | переменная | src/forthc.fth:289 | 2 |  |
| 417 | `fc-apl` | переменная | src/forthc.fth:290 | 3 |  |
| 418 | `fc-afld` | переменная | src/forthc.fth:290 | 3 |  |
| 419 | `fc-access-patch` | определение `:` | src/forthc.fth:291 | 2 |  |
| 420 | `fc-access` | определение `:` | src/forthc.fth:296 | 1 |  |
| 421 | `fc-width` | определение `:` | src/forthc.fth:298 | 4 |  |
| 422 | `fc-r1l0` | переменная | src/forthc.fth:299 | 2 |  |
| 423 | `fc-r1l1` | переменная | src/forthc.fth:299 | 2 |  |
| 424 | `fc-r1r` | переменная | src/forthc.fth:299 | 2 |  |
| 425 | `fc-check` | определение `:` | src/forthc.fth:302 | 4 |  |
| 426 | `fc-ring` | константа | src/forthc.fth:328 | 6 |  |
| 427 | `fc-window` | константа | src/forthc.fth:328 | 1 |  |
| 428 | `fc-sl` | данные `create` | src/forthc.fth:329 | 2 |  |
| 429 | `fc-stabs` | переменная | src/forthc.fth:329 | 2 |  |
| 430 | `fc-slen` | переменная | src/forthc.fth:330 | 7 |  |
| 431 | `fc-slow` | переменная | src/forthc.fth:330 | 4 |  |
| 432 | `fc-sinit` | определение `:` | src/forthc.fth:331 | 2 |  |
| 433 | `fc-sbegin` | определение `:` | src/forthc.fth:332 | 2 |  |
| 434 | `fc-tabs` | определение `:` | src/forthc.fth:333 | 3 |  |
| 435 | `fc-at` | определение `:` | src/forthc.fth:334 | 4 |  |
| 436 | `fc-has?` | определение `:` | src/forthc.fth:339 | 1 |  |
| 437 | `fc-tab+` | определение `:` | src/forthc.fth:340 | 1 |  |
| 438 | `fc-prw` | данные `create` | src/forthc.fth:341 | 6 |  |
| 439 | `fc-ptab` | переменная | src/forthc.fth:341 | 5 |  |
| 440 | `fc-place` | определение `:` | src/forthc.fth:342 | 3 |  |
| 441 | `fc-scopy` | определение `:` | src/forthc.fth:352 | 9 |  |
| 442 | `fc-segs` | данные `create` | src/forthc.fth:354 | 2 |  |
| 443 | `fc-nseg` | переменная | src/forthc.fth:354 | 5 |  |
| 444 | `fc-pp` | данные `create` | src/forthc.fth:355 | 2 |  |
| 445 | `fc-npp` | переменная | src/forthc.fth:355 | 4 |  |
| 446 | `fc-latest` | переменная | src/forthc.fth:355 | 4 |  |
| 447 | `fc-sga` | переменная | src/forthc.fth:355 | 14 |  |
| 448 | `fc-ltab` | переменная | src/forthc.fth:356 | 3 |  |
| 449 | `fc-ls` | переменная | src/forthc.fth:356 | 3 |  |
| 450 | `fc-lw` | переменная | src/forthc.fth:356 | 3 |  |
| 451 | `fc-ldst` | переменная | src/forthc.fth:356 | 2 |  |
| 452 | `fc-seg+` | определение `:` | src/forthc.fth:357 | 21 |  |
| 453 | `fc-pp+` | определение `:` | src/forthc.fth:360 | 1 |  |
| 454 | `fc-slookup` | определение `:` | src/forthc.fth:361 | 8 |  |
| 455 | `fc-nx` | переменная | src/forthc.fth:380 | 3 |  |
| 456 | `fc-nv` | переменная | src/forthc.fth:380 | 2 |  |
| 457 | `fc-nt` | переменная | src/forthc.fth:380 | 3 |  |
| 458 | `fc-negate-chain` | определение `:` | src/forthc.fth:381 | 1 |  |
| 459 | `fc-gw` | переменная | src/forthc.fth:388 | 4 |  |
| 460 | `fc-gs` | переменная | src/forthc.fth:388 | 2 |  |
| 461 | `fc-gs2` | переменная | src/forthc.fth:388 | 2 |  |
| 462 | `fc-gts` | переменная | src/forthc.fth:388 | 6 |  |
| 463 | `fc-gdst` | переменная | src/forthc.fth:388 | 2 |  |
| 464 | `fc-negate-select` | определение `:` | src/forthc.fth:389 | 4 |  |
| 465 | `fc-sfinish` | определение `:` | src/forthc.fth:394 | 2 |  |
| 466 | `fc-pr` | данные `create` | src/forthc.fth:397 | 2 |  |
| 467 | `fc-xs` | данные `create` | src/forthc.fth:397 | 2 |  |
| 468 | `fc-m4` | переменная | src/forthc.fth:398 | 2 |  |
| 469 | `fc-mj` | переменная | src/forthc.fth:398 | 11 |  |
| 470 | `fc-mk` | переменная | src/forthc.fth:398 | 6 |  |
| 471 | `fc-p@` | определение `:` | src/forthc.fth:399 | 3 |  |
| 472 | `fc-p!` | определение `:` | src/forthc.fth:400 | 1 |  |
| 473 | `fc-x@` | определение `:` | src/forthc.fth:401 | 3 |  |
| 474 | `fc-x!` | определение `:` | src/forthc.fth:402 | 2 |  |
| 475 | `fc-build-mul` | определение `:` | src/forthc.fth:403 | 1 |  |
| 476 | `fc-sub` | данные `create` | src/forthc.fth:421 | 2 |  |
| 477 | `fc-qsel` | переменная | src/forthc.fth:421 | 2 |  |
| 478 | `fc-absa` | переменная | src/forthc.fth:422 | 5 |  |
| 479 | `fc-absb` | переменная | src/forthc.fth:422 | 3 |  |
| 480 | `fc-ta` | переменная | src/forthc.fth:422 | 4 |  |
| 481 | `fc-tb` | переменная | src/forthc.fth:422 | 2 |  |
| 482 | `fc-rem` | переменная | src/forthc.fth:423 | 7 |  |
| 483 | `fc-tr` | переменная | src/forthc.fth:423 | 7 |  |
| 484 | `fc-q` | переменная | src/forthc.fth:423 | 3 |  |
| 485 | `fc-tq` | переменная | src/forthc.fth:423 | 4 |  |
| 486 | `fc-k` | переменная | src/forthc.fth:423 | 5 |  |
| 487 | `fc-w` | переменная | src/forthc.fth:424 | 14 |  |
| 488 | `fc-lo` | переменная | src/forthc.fth:424 | 7 |  |
| 489 | `fc-tlo` | переменная | src/forthc.fth:424 | 7 |  |
| 490 | `fc-t0` | переменная | src/forthc.fth:424 | 4 |  |
| 491 | `fc-t1` | переменная | src/forthc.fth:424 | 4 |  |
| 492 | `fc-qr` | переменная | src/forthc.fth:424 | 4 |  |
| 493 | `fc-tqk` | переменная | src/forthc.fth:424 | 3 |  |
| 494 | `fc-sub@` | определение `:` | src/forthc.fth:425 | 7 |  |
| 495 | `fc-step` | определение `:` | src/forthc.fth:427 | 3 |  |
| 496 | `fc-div-step` | определение `:` | src/forthc.fth:434 | 1 |  |
| 497 | `fc-build-div` | определение `:` | src/forthc.fth:451 | 1 |  |
| 498 | `fc-mul-entry` | переменная | src/forthc.fth:467 | 2 |  |
| 499 | `fc-mul-exit` | переменная | src/forthc.fth:467 | 2 |  |
| 500 | `fc-div-entry` | переменная | src/forthc.fth:467 | 4 |  |
| 501 | `fc-div-exit` | переменная | src/forthc.fth:467 | 4 |  |
| 502 | `fc-hl` | переменная | src/forthc.fth:468 | 4 |  |
| 503 | `fc-hcont` | переменная | src/forthc.fth:468 | 3 |  |
| 504 | `fc-row-or-new` | определение `:` | src/forthc.fth:469 | 2 |  |
| 505 | `fc-call-helper` | определение `:` | src/forthc.fth:472 | 4 |  |
| 506 | `fc-result1` | определение `:` | src/forthc.fth:477 | 3 |  |
| 507 | `fc-s1` | переменная | src/forthc.fth:478 | 2 |  |
| 508 | `fc-s2` | переменная | src/forthc.fth:478 | 2 |  |
| 509 | `fc-r1` | переменная | src/forthc.fth:478 | 2 |  |
| 510 | `fc-result2` | определение `:` | src/forthc.fth:479 | 1 |  |
| 511 | `fc-ll` | переменная | src/forthc.fth:485 | 4 |  |
| 512 | `fc-llr` | переменная | src/forthc.fth:485 | 2 |  |
| 513 | `fc-llv` | переменная | src/forthc.fth:485 | 2 |  |
| 514 | `fc-plit` | переменная | src/forthc.fth:485 | 5 |  |
| 515 | `fc-plr` | переменная | src/forthc.fth:485 | 3 |  |
| 516 | `fc-plv` | переменная | src/forthc.fth:485 | 4 |  |
| 517 | `fc-literal` | определение `:` | src/forthc.fth:486 | 7 |  |
| 518 | `fc-or-zero` | определение `:` | src/forthc.fth:488 | 2 |  |
| 519 | `fc-ba` | переменная | src/forthc.fth:491 | 13 |  |
| 520 | `fc-bb` | переменная | src/forthc.fth:491 | 13 |  |
| 521 | `fc-br` | переменная | src/forthc.fth:491 | 9 |  |
| 522 | `fc-binary` | определение `:` | src/forthc.fth:493 | 10 |  |
| 523 | `fc-r-at` | определение `:` | src/forthc.fth:517 | 2 |  |
| 524 | `fc-pop-pinned` | определение `:` | src/forthc.fth:520 | 3 |  |
| 525 | `fc-sk` | переменная | src/forthc.fth:522 | 12 |  |
| 526 | `fc-shift-copy` | определение `:` | src/forthc.fth:523 | 2 |  |
| 527 | `fc-inc` | определение `:` | src/forthc.fth:528 | 3 |  |
| 528 | `fc-read-key` | определение `:` | src/forthc.fth:531 | 1 |  |
| 529 | `fc-text` | переменная | src/forthc.fth:537 | 10 |  |
| 530 | `fc-tlen` | переменная | src/forthc.fth:537 | 11 |  |
| 531 | `fc-pos` | переменная | src/forthc.fth:537 | 14 |  |
| 532 | `fc-text-size` | переменная | src/forthc.fth:537 | 6 | вход бута (хост) |
| 533 | `fc-tok` | данные `create` | src/forthc.fth:538 | 14 |  |
| 534 | `fc-tl` | переменная | src/forthc.fth:538 | 18 |  |
| 535 | `fc-reset` | определение `:` | src/forthc.fth:539 | 3 |  |
| 536 | `fc-append` | определение `:` | src/forthc.fth:540 | 1 |  |
| 537 | `fc\|` | определение `:` | src/forthc.fth:544 | 1 | вход бута (хост) |
| 538 | `fc-ch` | определение `:` | src/forthc.fth:545 | 5 |  |
| 539 | `fc-more?` | определение `:` | src/forthc.fth:546 | 6 |  |
| 540 | `fc-next` | определение `:` | src/forthc.fth:550 | 4 |  |
| 541 | `fc-next!` | определение `:` | src/forthc.fth:558 | 6 |  |
| 542 | `fc-is?` | определение `:` | src/forthc.fth:560 | 1 |  |
| 543 | `fc-raw` | определение `:` | src/forthc.fth:564 | 1 |  |
| 544 | `fc-string-token` | определение `:` | src/forthc.fth:566 | 1 |  |
| 545 | `fc-names-size` | переменная | src/forthc.fth:571 | 5 | вход бута (хост) |
| 546 | `fc-max-words` | переменная | src/forthc.fth:571 | 5 | вход бута (хост) |
| 547 | `fc-names` | переменная | src/forthc.fth:572 | 3 |  |
| 548 | `fc-names-used` | переменная | src/forthc.fth:572 | 5 |  |
| 549 | `fc-wt` | переменная | src/forthc.fth:573 | 3 |  |
| 550 | `fc-nwords` | переменная | src/forthc.fth:573 | 6 |  |
| 551 | `fc-wbk` | переменная | src/forthc.fth:573 | 3 |  |
| 552 | `fc-wt@` | определение `:` | src/forthc.fth:574 | 3 |  |
| 553 | `fc-hash` | определение `:` | src/forthc.fth:575 | 2 |  |
| 554 | `fc-define` | определение `:` | src/forthc.fth:577 | 5 |  |
| 555 | `fc-lookup` | определение `:` | src/forthc.fth:582 | 3 |  |
| 556 | `fc-find` | определение `:` | src/forthc.fth:586 | 4 |  |
| 557 | `fc-here` | переменная | src/forthc.fth:589 | 9 |  |
| 558 | `fc-word` | переменная | src/forthc.fth:589 | 7 |  |
| 559 | `fc-uses` | переменная | src/forthc.fth:589 | 6 |  |
| 560 | `fc-ctl` | данные `create` | src/forthc.fth:592 | 1 |  |
| 561 | `fc-nctl` | переменная | src/forthc.fth:592 | 12 |  |
| 562 | `fc-cleave` | переменная | src/forthc.fth:592 | 2 |  |
| 563 | `fc-ctl@` | определение `:` | src/forthc.fth:593 | 4 |  |
| 564 | `fc-ctl+` | определение `:` | src/forthc.fth:594 | 6 |  |
| 565 | `fc-ctl-` | определение `:` | src/forthc.fth:596 | 7 |  |
| 566 | `fc-do-entry` | определение `:` | src/forthc.fth:598 | 1 |  |
| 567 | `fc-ctl-leave` | определение `:` | src/forthc.fth:602 | 1 |  |
| 568 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:603 | 1 |  |
| 569 | `fc-loop-leave` | определение `:` | src/forthc.fth:604 | 1 |  |
| 570 | `fc-align` | определение `:` | src/forthc.fth:606 | 2 |  |
| 571 | `fc-check-here` | определение `:` | src/forthc.fth:607 | 3 |  |
| 572 | `fc-define-data` | определение `:` | src/forthc.fth:608 | 2 |  |
| 573 | `fc-sat` | переменная | src/forthc.fth:609 | 3 |  |
| 574 | `fc-store-string` | определение `:` | src/forthc.fth:610 | 1 |  |
| 575 | `fc-ct` | данные `create` | src/forthc.fth:616 | 3 |  |
| 576 | `fc-nct` | переменная | src/forthc.fth:616 | 11 |  |
| 577 | `fc-ct+` | определение `:` | src/forthc.fth:617 | 15 |  |
| 578 | `fc-ct-` | определение `:` | src/forthc.fth:618 | 9 |  |
| 579 | `fc-ct2` | определение `:` | src/forthc.fth:619 | 8 |  |
| 580 | `fc-inits` | данные `create` | src/forthc.fth:621 | 2 |  |
| 581 | `fc-ninit` | переменная | src/forthc.fth:621 | 5 |  |
| 582 | `fc-init-open` | переменная | src/forthc.fth:621 | 6 |  |
| 583 | `fc-init` | определение `:` | src/forthc.fth:622 | 1 |  |
| 584 | `fc-scan-uses` | определение `:` | src/forthc.fth:641 | 1 |  |
| 585 | `fc-const-shift` | определение `:` | src/forthc.fth:649 | 2 |  |
| 586 | `fc-lit?` | определение `:` | src/forthc.fth:660 | 2 |  |
| 587 | `fc-mul-lit?` | определение `:` | src/forthc.fth:662 | 1 |  |
| 588 | `fc-shift-lit?` | определение `:` | src/forthc.fth:667 | 2 |  |
| 589 | `fc-pick-roll` | определение `:` | src/forthc.fth:670 | 2 |  |
| 590 | `fc-stx` | переменная | src/forthc.fth:678 | 3 |  |
| 591 | `fc-stlo` | переменная | src/forthc.fth:678 | 5 |  |
| 592 | `fc-sthi` | переменная | src/forthc.fth:678 | 5 |  |
| 593 | `fc-stp` | переменная | src/forthc.fth:678 | 3 |  |
| 594 | `fc-strow` | переменная | src/forthc.fth:678 | 4 |  |
| 595 | `fc-space-store` | определение `:` | src/forthc.fth:679 | 2 |  |
| 596 | `fc-close-init` | определение `:` | src/forthc.fth:689 | 2 |  |
| 597 | `fc-open-init` | определение `:` | src/forthc.fth:692 | 1 |  |
| 598 | `fc-gens` | переменная | src/forthc.fth:708 | 3 |  |
| 599 | `fc-generator` | определение `:` | src/forthc.fth:709 | 72 |  |
| 600 | `fc-literal-name` | определение `:` | src/forthc.fth:711 | 10 |  |
| 601 | `fc-words` | определение `:` | src/forthc.fth:713 | 1 |  |
| 602 | `fc-known` | определение `:` | src/forthc.fth:722 | 1 |  |
| 603 | `fc-defining?` | определение `:` | src/forthc.fth:725 | 6 |  |
| 604 | `fc-code` | определение `:` | src/forthc.fth:728 | 49 | вариант 2 |
| 605 | `fc-fold?` | определение `:` | src/forthc.fth:731 | 13 |  |
| 606 | `fc-top-only` | определение `:` | src/forthc.fth:733 | 6 |  |
| 607 | `fc-not-found` | определение `:` | src/forthc.fth:738 | 1 |  |
| 608 | `fc-word-token` | определение `:` | src/forthc.fth:745 | 1 |  |
| 609 | `fc-compile` | определение `:` | src/forthc.fth:750 | 1 |  |
| 610 | `fc-go` | определение `:` | src/forthc.fth:765 | 3 | вход бута (хост) |
| 611 | `gen+` | определение `:` | src/primitives.fth:9 | 2 |  |
| 612 | `gen-` | определение `:` | src/primitives.fth:10 | 2 |  |
| 613 | `gen-and` | определение `:` | src/primitives.fth:11 | 2 |  |
| 614 | `gen-or` | определение `:` | src/primitives.fth:12 | 2 |  |
| 615 | `gen-xor` | определение `:` | src/primitives.fth:13 | 2 |  |
| 616 | `gen=` | определение `:` | src/primitives.fth:14 | 2 |  |
| 617 | `gen<` | определение `:` | src/primitives.fth:15 | 2 |  |
| 618 | `gen-u<` | определение `:` | src/primitives.fth:16 | 2 |  |
| 619 | `gen-lshift` | определение `:` | src/primitives.fth:17 | 2 |  |
| 620 | `gen-rshift` | определение `:` | src/primitives.fth:19 | 2 |  |
| 621 | `gen-0=` | определение `:` | src/primitives.fth:21 | 2 |  |
| 622 | `gen-cells` | определение `:` | src/primitives.fth:22 | 2 |  |
| 623 | `gen-2*` | определение `:` | src/primitives.fth:23 | 2 |  |
| 624 | `gen-1+` | определение `:` | src/primitives.fth:24 | 2 |  |
| 625 | `gen-1-` | определение `:` | src/primitives.fth:25 | 2 |  |
| 626 | `gen-cell+` | определение `:` | src/primitives.fth:26 | 2 |  |
| 627 | `gen*` | определение `:` | src/primitives.fth:28 | 2 |  |
| 628 | `gen/` | определение `:` | src/primitives.fth:31 | 2 |  |
| 629 | `gen-mod` | определение `:` | src/primitives.fth:32 | 2 |  |
| 630 | `gen/mod` | определение `:` | src/primitives.fth:33 | 2 |  |
| 631 | `gen-dup` | определение `:` | src/primitives.fth:37 | 2 |  |
| 632 | `gen-drop` | определение `:` | src/primitives.fth:38 | 2 |  |
| 633 | `gen-swap` | определение `:` | src/primitives.fth:39 | 2 |  |
| 634 | `gen-over` | определение `:` | src/primitives.fth:40 | 2 |  |
| 635 | `gen-rot` | определение `:` | src/primitives.fth:41 | 2 |  |
| 636 | `gen-pick` | определение `:` | src/primitives.fth:42 | 2 |  |
| 637 | `gen-roll` | определение `:` | src/primitives.fth:43 | 2 |  |
| 638 | `gen->r` | определение `:` | src/primitives.fth:44 | 2 |  |
| 639 | `gen-r>` | определение `:` | src/primitives.fth:45 | 2 |  |
| 640 | `gen-r@` | определение `:` | src/primitives.fth:46 | 4 |  |
| 641 | `gen-j` | определение `:` | src/primitives.fth:47 | 2 |  |
| 642 | `gen-@` | определение `:` | src/primitives.fth:48 | 2 |  |
| 643 | `gen-!` | определение `:` | src/primitives.fth:50 | 2 |  |
| 644 | `gen-c@` | определение `:` | src/primitives.fth:51 | 2 |  |
| 645 | `gen-c!` | определение `:` | src/primitives.fth:53 | 2 |  |
| 646 | `gen-space!` | определение `:` | src/primitives.fth:54 | 2 |  |
| 647 | `gen-spacec!` | определение `:` | src/primitives.fth:55 | 2 |  |
| 648 | `gen-emit` | определение `:` | src/primitives.fth:56 | 2 |  |
| 649 | `gen-key` | определение `:` | src/primitives.fth:59 | 2 |  |
| 650 | `gen-if` | определение `:` | src/primitives.fth:63 | 2 |  |
| 651 | `gen-else` | определение `:` | src/primitives.fth:64 | 2 |  |
| 652 | `gen-then` | определение `:` | src/primitives.fth:66 | 2 |  |
| 653 | `gen-begin` | определение `:` | src/primitives.fth:70 | 2 |  |
| 654 | `gen-until` | определение `:` | src/primitives.fth:71 | 2 |  |
| 655 | `gen-while` | определение `:` | src/primitives.fth:73 | 2 |  |
| 656 | `gen-repeat` | определение `:` | src/primitives.fth:74 | 2 |  |
| 657 | `gen-again` | определение `:` | src/primitives.fth:75 | 2 |  |
| 658 | `gen-do` | определение `:` | src/primitives.fth:77 | 2 |  |
| 659 | `fc-di` | переменная | src/primitives.fth:81 | 3 |  |
| 660 | `fc-dl` | переменная | src/primitives.fth:81 | 3 |  |
| 661 | `gen-?do` | определение `:` | src/primitives.fth:82 | 2 |  |
| 662 | `fc-lv` | переменная | src/primitives.fth:89 | 2 |  |
| 663 | `gen-loop` | определение `:` | src/primitives.fth:90 | 2 |  |
| 664 | `gen-leave` | определение `:` | src/primitives.fth:99 | 2 |  |
| 665 | `gen-unloop` | определение `:` | src/primitives.fth:102 | 2 |  |
| 666 | `gen-exit` | определение `:` | src/primitives.fth:105 | 2 |  |
| 667 | `gen-recurse` | определение `:` | src/primitives.fth:106 | 2 |  |
| 668 | `gen-execute` | определение `:` | src/primitives.fth:107 | 2 |  |
| 669 | `gen-tick` | определение `:` | src/primitives.fth:108 | 2 |  |
| 670 | `gen-catch` | определение `:` | src/primitives.fth:109 | 2 |  |
| 671 | `gen-throw` | определение `:` | src/primitives.fth:110 | 2 |  |
| 672 | `gen-colon` | определение `:` | src/primitives.fth:114 | 2 |  |
| 673 | `gen-semicolon` | определение `:` | src/primitives.fth:117 | 2 |  |
| 674 | `gen-variable` | определение `:` | src/primitives.fth:119 | 2 |  |
| 675 | `gen-create` | определение `:` | src/primitives.fth:120 | 2 |  |
| 676 | `gen-allot` | определение `:` | src/primitives.fth:121 | 2 |  |
| 677 | `gen-constant` | определение `:` | src/primitives.fth:122 | 2 |  |
| 678 | `gen-decimal` | определение `:` | src/primitives.fth:123 | 2 |  |
| 679 | `gen-kernel-layout` | определение `:` | src/primitives.fth:125 | 2 |  |
| 680 | `gen-backslash` | определение `:` | src/primitives.fth:128 | 2 |  |
| 681 | `gen-paren` | определение `:` | src/primitives.fth:130 | 2 |  |
| 682 | `gen-char` | определение `:` | src/primitives.fth:131 | 2 |  |
| 683 | `gen-string` | определение `:` | src/primitives.fth:132 | 2 |  |
| 684 | `fc-digit@` | определение `:` | src/primitives.fth:141 | 1 |  |
| 685 | `gen-literal` | определение `:` | src/primitives.fth:143 | 2 |  |
| 686 | `fc-name2` | определение `:` | src/primitives.fth:149 | 1 |  |
| 687 | `fc-generators` | определение `:` | src/primitives.fth:152 | 1 |  |
| 688 | `+` | генератор | src/primitives.fth:153 | 461 | слово компилятора `gen+` |
| 689 | `-` | генератор | src/primitives.fth:153 | 44 | слово компилятора `gen-` |
| 690 | `*` | генератор | src/primitives.fth:154 | 79 | слово компилятора `gen*` |
| 691 | `/` | генератор | src/primitives.fth:154 | 3 | слово компилятора `gen/` |
| 692 | `mod` | генератор | src/primitives.fth:155 | 1 | слово компилятора `gen-mod` |
| 693 | `and` | генератор | src/primitives.fth:156 | 97 | слово компилятора `gen-and` |
| 694 | `or` | генератор | src/primitives.fth:156 | 38 | слово компилятора `gen-or` |
| 695 | `xor` | генератор | src/primitives.fth:157 | 5 | слово компилятора `gen-xor` |
| 696 | `lshift` | генератор | src/primitives.fth:157 | 69 | слово компилятора `gen-lshift` |
| 697 | `rshift` | генератор | src/primitives.fth:158 | 54 | слово компилятора `gen-rshift` |
| 698 | `=` | генератор | src/primitives.fth:158 | 41 | слово компилятора `gen=` |
| 699 | `<` | генератор | src/primitives.fth:159 | 27 | слово компилятора `gen<` |
| 700 | `u<` | генератор | src/primitives.fth:159 | 11 | слово компилятора `gen-u<` |
| 701 | `0=` | генератор | src/primitives.fth:160 | 70 | слово компилятора `gen-0=` |
| 702 | `2*` | генератор | src/primitives.fth:160 | 25 | слово компилятора `gen-2*` |
| 703 | `1+` | генератор | src/primitives.fth:161 | 40 | слово компилятора `gen-1+` |
| 704 | `1-` | генератор | src/primitives.fth:161 | 42 | слово компилятора `gen-1-` |
| 705 | `cells` | генератор | src/primitives.fth:162 | 197 | слово компилятора `gen-cells` |
| 706 | `cell+` | генератор | src/primitives.fth:162 | 34 | слово компилятора `gen-cell+` |
| 707 | `dup` | генератор | src/primitives.fth:163 | 247 | слово компилятора `gen-dup` |
| 708 | `drop` | генератор | src/primitives.fth:163 | 165 | слово компилятора `gen-drop` |
| 709 | `swap` | генератор | src/primitives.fth:164 | 118 | слово компилятора `gen-swap` |
| 710 | `over` | генератор | src/primitives.fth:164 | 75 | слово компилятора `gen-over` |
| 711 | `rot` | генератор | src/primitives.fth:165 | 33 | слово компилятора `gen-rot` |
| 712 | `pick` | генератор | src/primitives.fth:165 | 45 | слово компилятора `gen-pick` |
| 713 | `roll` | генератор | src/primitives.fth:166 | 5 | слово компилятора `gen-roll` |
| 714 | `>r` | генератор | src/primitives.fth:166 | 84 | слово компилятора `gen->r` |
| 715 | `r>` | генератор | src/primitives.fth:167 | 88 | слово компилятора `gen-r>` |
| 716 | `r@` | генератор | src/primitives.fth:167 | 66 | слово компилятора `gen-r@` |
| 717 | `i` | генератор | src/primitives.fth:168 | 151 | слово компилятора `gen-r@` |
| 718 | `j` | генератор | src/primitives.fth:168 | 12 | слово компилятора `gen-j` |
| 719 | `@` | генератор | src/primitives.fth:169 | 952 | слово компилятора `gen-@` |
| 720 | `!` | генератор | src/primitives.fth:169 | 515 | слово компилятора `gen-!` |
| 721 | `c@` | генератор | src/primitives.fth:170 | 22 | слово компилятора `gen-c@` |
| 722 | `c!` | генератор | src/primitives.fth:170 | 17 | слово компилятора `gen-c!` |
| 723 | `space!` | генератор | src/primitives.fth:171 | 1 | слово компилятора `gen-space!` |
| 724 | `spacec!` | генератор | src/primitives.fth:171 | 1 | слово компилятора `gen-spacec!` |
| 725 | `emit` | генератор | src/primitives.fth:172 | 4 | слово компилятора `gen-emit` |
| 726 | `key` | генератор | src/primitives.fth:172 | 1 | слово компилятора `gen-key` |
| 727 | `if` | генератор | src/primitives.fth:173 | 206 | слово компилятора `gen-if` |
| 728 | `else` | генератор | src/primitives.fth:173 | 58 | слово компилятора `gen-else` |
| 729 | `then` | генератор | src/primitives.fth:174 | 206 | слово компилятора `gen-then` |
| 730 | `begin` | генератор | src/primitives.fth:174 | 21 | слово компилятора `gen-begin` |
| 731 | `until` | генератор | src/primitives.fth:175 | 1 | слово компилятора `gen-until` |
| 732 | `while` | генератор | src/primitives.fth:175 | 19 | слово компилятора `gen-while` |
| 733 | `repeat` | генератор | src/primitives.fth:176 | 19 | слово компилятора `gen-repeat` |
| 734 | `again` | генератор | src/primitives.fth:176 | 1 | слово компилятора `gen-again` |
| 735 | `do` | генератор | src/primitives.fth:177 | 30 | слово компилятора `gen-do` |
| 736 | `?do` | генератор | src/primitives.fth:177 | 47 | слово компилятора `gen-?do` |
| 737 | `loop` | генератор | src/primitives.fth:178 | 77 | слово компилятора `gen-loop` |
| 738 | `leave` | генератор | src/primitives.fth:178 | 1 | слово компилятора `gen-leave` |
| 739 | `unloop` | генератор | src/primitives.fth:179 | 4 | слово компилятора `gen-unloop` |
| 740 | `exit` | генератор | src/primitives.fth:179 | 48 | слово компилятора `gen-exit` |
| 741 | `recurse` | генератор | src/primitives.fth:180 | 1 | слово компилятора `gen-recurse` |
| 742 | `execute` | генератор | src/primitives.fth:180 | 8 | слово компилятора `gen-execute` |
| 743 | `[']` | генератор | src/primitives.fth:181 | 100 | слово компилятора `gen-tick` |
| 744 | `catch` | генератор | src/primitives.fth:181 | 1 | слово компилятора `gen-catch` |
| 745 | `throw` | генератор | src/primitives.fth:182 | 68 | слово компилятора `gen-throw` |
| 746 | `:` | генератор | src/primitives.fth:183 | 404 | слово компилятора `gen-colon` |
| 747 | `;` | генератор | src/primitives.fth:183 | 404 | слово компилятора `gen-semicolon` |
| 748 | `variable` | генератор | src/primitives.fth:184 | 262 | слово компилятора `gen-variable` |
| 749 | `create` | генератор | src/primitives.fth:184 | 38 | слово компилятора `gen-create` |
| 750 | `allot` | генератор | src/primitives.fth:185 | 36 | слово компилятора `gen-allot` |
| 751 | `constant` | генератор | src/primitives.fth:185 | 15 | слово компилятора `gen-constant` |
| 752 | `decimal` | генератор | src/primitives.fth:186 | 3 | слово компилятора `gen-decimal` |
| 753 | `kernel-layout` | генератор | src/primitives.fth:186 | 1 | слово компилятора `gen-kernel-layout` |
| 754 | `\` | генератор | src/primitives.fth:187 | 247 | слово компилятора `gen-backslash` |
| 755 | `(` | генератор | src/primitives.fth:187 | 381 | слово компилятора `gen-paren` |
| 756 | `[char]` | генератор | src/primitives.fth:187 | 8 | слово компилятора `gen-char` |
| 757 | `s"` | генератор | src/primitives.fth:188 | 86 | слово компилятора `gen-string` |
| 758 | `literal` | генератор | src/primitives.fth:189 | 398 | слово компилятора `gen-literal` |
| 759 | `0` | цифра (литерал) | src/primitives.fth:190 | 438 | значение 0 |
| 760 | `1` | цифра (литерал) | src/primitives.fth:190 | 348 | значение 1 |
| 761 | `2` | цифра (литерал) | src/primitives.fth:190 | 372 | значение 2 |
| 762 | `3` | цифра (литерал) | src/primitives.fth:190 | 250 | значение 3 |
| 763 | `4` | цифра (литерал) | src/primitives.fth:191 | 212 | значение 4 |
| 764 | `5` | цифра (литерал) | src/primitives.fth:191 | 95 | значение 5 |
| 765 | `6` | цифра (литерал) | src/primitives.fth:191 | 126 | значение 6 |
| 766 | `7` | цифра (литерал) | src/primitives.fth:191 | 42 | значение 7 |
| 767 | `8` | цифра (литерал) | src/primitives.fth:192 | 141 | значение 8 |
| 768 | `9` | цифра (литерал) | src/primitives.fth:192 | 31 | значение 9 |
| 769 | `fc-install-generators` | определение `:` | src/primitives.fth:193 | 1 |  |
| 770 | `heap-start` | данные `create` | src/main.fth:4 | 1 |  |
| 771 | `fc-read` | определение `:` | src/main.fth:7 | 2 |  |
| 772 | `fc-sizes` | определение `:` | src/main.fth:12 | 2 |  |
| 773 | `kn-at` | переменная | src/kernel.fth:12 | 5 |  |
| 774 | `kn-put` | определение `:` | src/kernel.fth:13 | 1 |  |
| 775 | `kn-order` | определение `:` | src/kernel.fth:23 | 1 |  |
| 776 | `kn-compile` | определение `:` | src/kernel.fth:24 | 1 |  |
| 777 | `kn-.n` | определение `:` | src/kernel.fth:25 | 1 |  |
| 778 | `main` | определение `:` | src/kernel.fth:29 | 1 | вариант 2 |
| 779 | `kn-heap-start` | данные `create` | src/kernel.fth:34 | 1 |  |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 81.

## Определены, но не использованы

Слов: 22. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

| Слово | Вид | Файл:строка |
|---|---|---|
| `cc-out` | определение `:` | src/backend.fth:120 |
| `cc-cell-bit` | определение `:` | src/compute.fth:14 |
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
| `fc-depth` | определение `:` | src/forthc.fth:720 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:721 |
| `/mod` | генератор | src/primitives.fth:155 |
| `main` (вариант 1) | определение `:` | src/main.fth:15 |

## Слова, которые при буте исполняет хост

Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки `backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках 82; все они определены в определении языка (генератором в `primitives.fth` или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: `!` `*` `+` `+!` `-` `-rot` `/` `/string` `0<` `0<>` `0=` `0>` `1+` `1-` `2!` `2*` `2@` `2drop` `2dup` `2over` `2swap` `<` `<>` `=` `>` `>in` `>r` `?do` `?dup` `@` `again` `allocate` `and` `begin` `c!` `c@` `cell+` `cells` `cmove` `cmove>` `compare` `decimal` `do` `drop` `dup` `else` `execute` `exit` `fill` `free` `i` `if` `invert` `j` `leave` `loop` `lshift` `max` `min` `negate` `nip` `or` `over` `pick` `r>` `r@` `repeat` `roll` `rot` `rshift` `source` `swap` `then` `throw` `tuck` `type` `u<` `u>` `unloop` `until` `while` `xor`.

Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро читает каналом `key`), `source` и `>in` — слова только этого пути.
