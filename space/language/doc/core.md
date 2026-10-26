# Ядро языка (14.8)

Файл порождается `make -C space/language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`tools/research/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 791** (определение `:` — 394, переменная — 257, генератор — 71, данные `create` — 38, константа — 15, цифра (литерал) — 10, основание — 6).

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
| 83 | `cc-field` | определение `:` | src/backend.fth:117 | 36 |  |
| 84 | `cc-link-row` | основание | src/backend.fth:118 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 85 | `cc-copy` | основание | src/backend.fth:119 | 73 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 86 | `cc-builder` | определение `:` | src/backend.fth:121 | 1 |  |
| 87 | `cc-new-cell` | определение `:` | src/backend.fth:122 | 13 |  |
| 88 | `cc-branch-bit` | определение `:` | src/backend.fth:125 | 13 |  |
| 89 | `cc-branch-step` | определение `:` | src/backend.fth:126 | 4 |  |
| 90 | `cc-group` | определение `:` | src/backend.fth:128 | 5 |  |
| 91 | `cc-layer-cell` | определение `:` | src/backend.fth:131 | 35 |  |
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
| 102 | `cc-last` | определение `:` | src/backend.fth:149 | 3 |  |
| 103 | `cc-layer` | основание | src/backend.fth:150 | 72 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
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
| 120 | `cc-row` | основание | src/backend.fth:181 | 72 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
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
| 248 | `fc-guard` | переменная | src/forthc.fth:19 | 8 |  |
| 249 | `fc-layout` | определение `:` | src/forthc.fth:20 | 1 |  |
| 250 | `fc-d+` | определение `:` | src/forthc.fth:22 | 29 |  |
| 251 | `fc-sp` | определение `:` | src/forthc.fth:23 | 6 |  |
| 252 | `fc-rp` | определение `:` | src/forthc.fth:23 | 18 |  |
| 253 | `fc-handler` | определение `:` | src/forthc.fth:23 | 6 |  |
| 254 | `fc-code` | определение `:` | src/forthc.fth:23 | 4 |  |
| 255 | `fc-regs` | определение `:` | src/forthc.fth:24 | 2 |  |
| 256 | `fc-nregs` | константа | src/forthc.fth:24 | 2 |  |
| 257 | `fc-tmp` | определение `:` | src/forthc.fth:25 | 10 |  |
| 258 | `fc-xr` | определение `:` | src/forthc.fth:25 | 10 |  |
| 259 | `fc-z` | определение `:` | src/forthc.fth:25 | 7 |  |
| 260 | `fc-idx` | определение `:` | src/forthc.fth:25 | 4 |  |
| 261 | `fc-flt` | определение `:` | src/forthc.fth:26 | 4 |  |
| 262 | `fc-ma` | определение `:` | src/forthc.fth:27 | 6 |  |
| 263 | `fc-mb` | определение `:` | src/forthc.fth:27 | 6 |  |
| 264 | `fc-mp` | определение `:` | src/forthc.fth:27 | 2 |  |
| 265 | `fc-mq` | определение `:` | src/forthc.fth:27 | 3 |  |
| 266 | `fc-mr` | определение `:` | src/forthc.fth:27 | 3 |  |
| 267 | `fc-zero` | определение `:` | src/forthc.fth:28 | 12 |  |
| 268 | `fc-consts` | определение `:` | src/forthc.fth:28 | 3 |  |
| 269 | `fc-mark` | определение `:` | src/forthc.fth:29 | 2 |  |
| 270 | `fc-sw` | определение `:` | src/forthc.fth:30 | 2 |  |
| 271 | `fc-su` | определение `:` | src/forthc.fth:30 | 1 |  |
| 272 | `fc-key` | определение `:` | src/forthc.fth:30 | 3 |  |
| 273 | `fc-bp` | определение `:` | src/forthc.fth:30 | 2 |  |
| 274 | `fc-tab` | определение `:` | src/forthc.fth:31 | 1 |  |
| 275 | `fc-stk` | определение `:` | src/forthc.fth:31 | 3 |  |
| 276 | `fc-rstk` | определение `:` | src/forthc.fth:32 | 14 |  |
| 277 | `fc-scr0` | определение `:` | src/forthc.fth:32 | 1 |  |
| 278 | `fc-links` | определение `:` | src/forthc.fth:33 | 2 |  |
| 279 | `fc-max-links` | константа | src/forthc.fth:33 | 1 |  |
| 280 | `fc-link-chunk` | константа | src/forthc.fth:33 | 2 |  |
| 281 | `fc-mem` | определение `:` | src/forthc.fth:34 | 4 |  |
| 282 | `fc-mw` | константа | src/forthc.fth:34 | 5 |  |
| 283 | `fc-htab` | определение `:` | src/forthc.fth:34 | 1 |  |
| 284 | `fc-data-start` | константа | src/forthc.fth:35 | 1 |  |
| 285 | `fc-off` | данные `create` | src/forthc.fth:38 | 2 |  |
| 286 | `fc-oc` | переменная | src/forthc.fth:38 | 2 |  |
| 287 | `fc-t-rev8` | переменная | src/forthc.fth:39 | 3 |  |
| 288 | `fc-t-zero32` | переменная | src/forthc.fth:39 | 2 |  |
| 289 | `fc-t-nz2` | переменная | src/forthc.fth:39 | 2 |  |
| 290 | `fc-t-lt32` | переменная | src/forthc.fth:39 | 2 |  |
| 291 | `fc-t-or8b` | переменная | src/forthc.fth:40 | 2 |  |
| 292 | `fc-t-fault` | переменная | src/forthc.fth:40 | 2 |  |
| 293 | `fc-t-xr2` | переменная | src/forthc.fth:40 | 2 |  |
| 294 | `fc-t-ult32` | переменная | src/forthc.fth:40 | 2 |  |
| 295 | `fc-t-bytepos` | переменная | src/forthc.fth:40 | 2 |  |
| 296 | `fc-off@` | определение `:` | src/forthc.fth:41 | 3 |  |
| 297 | `fc-off-table` | определение `:` | src/forthc.fth:43 | 1 |  |
| 298 | `fc-rev-entry` | определение `:` | src/forthc.fth:46 | 1 |  |
| 299 | `fc-zero-entry` | определение `:` | src/forthc.fth:47 | 1 |  |
| 300 | `fc-nz-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 301 | `fc-lt-entry` | определение `:` | src/forthc.fth:49 | 1 |  |
| 302 | `fc-fault-entry` | определение `:` | src/forthc.fth:52 | 1 |  |
| 303 | `fc-xr2-entry` | определение `:` | src/forthc.fth:55 | 1 |  |
| 304 | `fc-ult-entry` | определение `:` | src/forthc.fth:56 | 1 |  |
| 305 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:58 | 1 |  |
| 306 | `fc-tables` | определение `:` | src/forthc.fth:59 | 1 |  |
| 307 | `fc-mul4-entry` | определение `:` | src/forthc.fth:72 | 1 |  |
| 308 | `fc-qsel-entry` | определение `:` | src/forthc.fth:75 | 1 |  |
| 309 | `fc-max-consts` | переменная | src/forthc.fth:80 | 5 | вход бута (хост) |
| 310 | `fc-ck` | переменная | src/forthc.fth:80 | 3 |  |
| 311 | `fc-nconsts` | переменная | src/forthc.fth:80 | 7 |  |
| 312 | `fc-nbuckets` | переменная | src/forthc.fth:81 | 9 | вход бута (хост) |
| 313 | `fc-cbk` | переменная | src/forthc.fth:81 | 3 |  |
| 314 | `fc-ck@` | определение `:` | src/forthc.fth:82 | 3 |  |
| 315 | `fc-chash` | определение `:` | src/forthc.fth:83 | 1 |  |
| 316 | `fc-cb` | переменная | src/forthc.fth:84 | 3 |  |
| 317 | `fc-const2` | определение `:` | src/forthc.fth:85 | 1 |  |
| 318 | `fc-const` | определение `:` | src/forthc.fth:95 | 4 |  |
| 319 | `fc-lit` | определение `:` | src/forthc.fth:103 | 3 |  |
| 320 | `fc-bit0` | определение `:` | src/forthc.fth:104 | 1 |  |
| 321 | `fc-bit1` | определение `:` | src/forthc.fth:105 | 1 |  |
| 322 | `fc-length` | определение `:` | src/forthc.fth:106 | 1 |  |
| 323 | `fc-lit-of` | определение `:` | src/forthc.fth:107 | 2 |  |
| 324 | `fc-load` | определение `:` | src/forthc.fth:111 | 2 |  |
| 325 | `fc-nlinks` | переменная | src/forthc.fth:115 | 5 |  |
| 326 | `fc-link-buf` | переменная | src/forthc.fth:115 | 4 |  |
| 327 | `fc-nbuf` | переменная | src/forthc.fth:115 | 8 |  |
| 328 | `fc-put-links` | определение `:` | src/forthc.fth:116 | 2 |  |
| 329 | `fc-link-const` | определение `:` | src/forthc.fth:120 | 4 |  |
| 330 | `fc-eight` | данные `create` | src/forthc.fth:125 | 5 |  |
| 331 | `fc-zeros` | данные `create` | src/forthc.fth:125 | 5 |  |
| 332 | `fc-put-consts` | определение `:` | src/forthc.fth:126 | 1 |  |
| 333 | `fc-cache` | данные `create` | src/forthc.fth:134 | 8 |  |
| 334 | `fc-n` | переменная | src/forthc.fth:134 | 31 |  |
| 335 | `fc-pin` | данные `create` | src/forthc.fth:135 | 10 |  |
| 336 | `fc-npin` | переменная | src/forthc.fth:135 | 21 |  |
| 337 | `fc-c@` | определение `:` | src/forthc.fth:136 | 8 |  |
| 338 | `fc-push` | определение `:` | src/forthc.fth:137 | 30 |  |
| 339 | `fc-pop1` | определение `:` | src/forthc.fth:138 | 30 |  |
| 340 | `fc-in?` | определение `:` | src/forthc.fth:139 | 3 |  |
| 341 | `fc-reg` | определение `:` | src/forthc.fth:140 | 18 |  |
| 342 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:145 | 1 |  |
| 343 | `fc-scr` | переменная | src/forthc.fth:146 | 3 |  |
| 344 | `fc-scratch` | определение `:` | src/forthc.fth:147 | 11 |  |
| 345 | `fc-offs` | данные `create` | src/forthc.fth:151 | 5 |  |
| 346 | `fc-noff` | переменная | src/forthc.fth:151 | 9 |  |
| 347 | `fc-ptr` | переменная | src/forthc.fth:151 | 4 |  |
| 348 | `fc-adjust` | определение `:` | src/forthc.fth:153 | 7 |  |
| 349 | `fc-prow` | данные `create` | src/forthc.fth:159 | 2 |  |
| 350 | `fc-nrow` | переменная | src/forthc.fth:159 | 8 |  |
| 351 | `fc-pl` | данные `create` | src/forthc.fth:160 | 2 |  |
| 352 | `fc-pslot` | данные `create` | src/forthc.fth:160 | 2 |  |
| 353 | `fc-rl` | переменная | src/forthc.fth:161 | 3 |  |
| 354 | `fc-f0` | переменная | src/forthc.fth:161 | 2 |  |
| 355 | `fc-f1` | переменная | src/forthc.fth:161 | 2 |  |
| 356 | `fc-psh` | переменная | src/forthc.fth:161 | 2 |  |
| 357 | `fc-row+` | определение `:` | src/forthc.fth:162 | 3 |  |
| 358 | `fc-4@` | определение `:` | src/forthc.fth:164 | 3 |  |
| 359 | `fc-patched` | определение `:` | src/forthc.fth:166 | 3 |  |
| 360 | `fc-popped` | данные `create` | src/forthc.fth:178 | 2 |  |
| 361 | `fc-srcs` | данные `create` | src/forthc.fth:178 | 16 |  |
| 362 | `fc-nsrc` | переменная | src/forthc.fth:178 | 21 |  |
| 363 | `fc-mbase` | переменная | src/forthc.fth:179 | 8 |  |
| 364 | `fc-mptr` | переменная | src/forthc.fth:179 | 4 |  |
| 365 | `fc-mn` | переменная | src/forthc.fth:179 | 7 |  |
| 366 | `fc-mw2` | переменная | src/forthc.fth:179 | 6 |  |
| 367 | `fc-popped@` | определение `:` | src/forthc.fth:180 | 10 |  |
| 368 | `fc-shift` | определение `:` | src/forthc.fth:181 | 4 |  |
| 369 | `fc-mem-pop` | определение `:` | src/forthc.fth:182 | 5 |  |
| 370 | `fc-push-group` | определение `:` | src/forthc.fth:190 | 2 |  |
| 371 | `fc-dup-at` | определение `:` | src/forthc.fth:198 | 1 |  |
| 372 | `fc-rest` | данные `create` | src/forthc.fth:200 | 2 |  |
| 373 | `fc-nrest` | переменная | src/forthc.fth:200 | 3 |  |
| 374 | `fc-mem-push` | определение `:` | src/forthc.fth:201 | 8 |  |
| 375 | `fc-src1` | определение `:` | src/forthc.fth:207 | 3 |  |
| 376 | `fc-need` | определение `:` | src/forthc.fth:209 | 14 |  |
| 377 | `fc-spill` | определение `:` | src/forthc.fth:216 | 19 |  |
| 378 | `fc-pop` | определение `:` | src/forthc.fth:222 | 13 |  |
| 379 | `fc-live` | переменная | src/forthc.fth:225 | 8 |  |
| 380 | `fc-tramp` | переменная | src/forthc.fth:225 | 5 |  |
| 381 | `fc-ex` | переменная | src/forthc.fth:225 | 4 |  |
| 382 | `fc-thrower` | переменная | src/forthc.fth:225 | 4 |  |
| 383 | `fc-jump` | определение `:` | src/forthc.fth:226 | 7 |  |
| 384 | `fc-end` | определение `:` | src/forthc.fth:227 | 14 |  |
| 385 | `fc-begin-block` | определение `:` | src/forthc.fth:229 | 24 |  |
| 386 | `fc-rows1` | определение `:` | src/forthc.fth:233 | 16 |  |
| 387 | `fc-nonzero` | определение `:` | src/forthc.fth:234 | 2 |  |
| 388 | `fc-branch` | определение `:` | src/forthc.fth:237 | 6 |  |
| 389 | `fc-call` | определение `:` | src/forthc.fth:238 | 4 |  |
| 390 | `fc-v0` | переменная | src/forthc.fth:241 | 2 |  |
| 391 | `fc-v1` | переменная | src/forthc.fth:241 | 2 |  |
| 392 | `fc-call-indirect` | определение `:` | src/forthc.fth:242 | 2 |  |
| 393 | `fc-push-frame` | определение `:` | src/forthc.fth:249 | 2 |  |
| 394 | `fc-restore` | определение `:` | src/forthc.fth:252 | 3 |  |
| 395 | `fc-build-thrower` | определение `:` | src/forthc.fth:254 | 1 |  |
| 396 | `fc-throw` | определение `:` | src/forthc.fth:260 | 1 |  |
| 397 | `fc-catch` | определение `:` | src/forthc.fth:263 | 1 |  |
| 398 | `fc-ret-p` | переменная | src/forthc.fth:272 | 3 |  |
| 399 | `fc-ret-l` | переменная | src/forthc.fth:272 | 4 |  |
| 400 | `fc-ret` | определение `:` | src/forthc.fth:273 | 3 |  |
| 401 | `fc-ca` | переменная | src/forthc.fth:281 | 6 |  |
| 402 | `fc-cl0` | переменная | src/forthc.fth:281 | 5 |  |
| 403 | `fc-cl1` | переменная | src/forthc.fth:281 | 5 |  |
| 404 | `fc-cr` | переменная | src/forthc.fth:281 | 7 |  |
| 405 | `fc-cg` | переменная | src/forthc.fth:281 | 4 |  |
| 406 | `fc-cx` | переменная | src/forthc.fth:281 | 4 |  |
| 407 | `fc-cv` | переменная | src/forthc.fth:282 | 3 |  |
| 408 | `fc-cres` | переменная | src/forthc.fth:282 | 6 |  |
| 409 | `fc-cslot` | переменная | src/forthc.fth:282 | 3 |  |
| 410 | `fc-csh` | переменная | src/forthc.fth:282 | 2 |  |
| 411 | `fc-chk-read` | определение `:` | src/forthc.fth:284 | 4 |  |
| 412 | `fc-chk-seg` | определение `:` | src/forthc.fth:287 | 5 |  |
| 413 | `fc-cmode` | переменная | src/forthc.fth:293 | 9 |  |
| 414 | `fc-ar` | переменная | src/forthc.fth:293 | 7 |  |
| 415 | `fc-as` | переменная | src/forthc.fth:293 | 2 |  |
| 416 | `fc-af` | переменная | src/forthc.fth:293 | 2 |  |
| 417 | `fc-al0` | переменная | src/forthc.fth:293 | 2 |  |
| 418 | `fc-al1` | переменная | src/forthc.fth:293 | 2 |  |
| 419 | `fc-apl` | переменная | src/forthc.fth:294 | 3 |  |
| 420 | `fc-afld` | переменная | src/forthc.fth:294 | 3 |  |
| 421 | `fc-access-patch` | определение `:` | src/forthc.fth:295 | 2 |  |
| 422 | `fc-access` | определение `:` | src/forthc.fth:300 | 1 |  |
| 423 | `fc-width` | определение `:` | src/forthc.fth:302 | 4 |  |
| 424 | `fc-r1l0` | переменная | src/forthc.fth:303 | 2 |  |
| 425 | `fc-r1l1` | переменная | src/forthc.fth:303 | 2 |  |
| 426 | `fc-r1r` | переменная | src/forthc.fth:303 | 2 |  |
| 427 | `fc-check` | определение `:` | src/forthc.fth:306 | 4 |  |
| 428 | `fc-ring` | константа | src/forthc.fth:332 | 6 |  |
| 429 | `fc-window` | константа | src/forthc.fth:332 | 1 |  |
| 430 | `fc-sl` | данные `create` | src/forthc.fth:333 | 2 |  |
| 431 | `fc-stabs` | переменная | src/forthc.fth:333 | 2 |  |
| 432 | `fc-slen` | переменная | src/forthc.fth:334 | 7 |  |
| 433 | `fc-slow` | переменная | src/forthc.fth:334 | 4 |  |
| 434 | `fc-sinit` | определение `:` | src/forthc.fth:335 | 2 |  |
| 435 | `fc-sbegin` | определение `:` | src/forthc.fth:336 | 2 |  |
| 436 | `fc-tabs` | определение `:` | src/forthc.fth:337 | 3 |  |
| 437 | `fc-at` | определение `:` | src/forthc.fth:338 | 4 |  |
| 438 | `fc-has?` | определение `:` | src/forthc.fth:343 | 1 |  |
| 439 | `fc-tab+` | определение `:` | src/forthc.fth:344 | 1 |  |
| 440 | `fc-prw` | данные `create` | src/forthc.fth:345 | 6 |  |
| 441 | `fc-ptab` | переменная | src/forthc.fth:345 | 5 |  |
| 442 | `fc-place` | определение `:` | src/forthc.fth:346 | 3 |  |
| 443 | `fc-scopy` | определение `:` | src/forthc.fth:356 | 9 |  |
| 444 | `fc-segs` | данные `create` | src/forthc.fth:358 | 2 |  |
| 445 | `fc-nseg` | переменная | src/forthc.fth:358 | 5 |  |
| 446 | `fc-pp` | данные `create` | src/forthc.fth:359 | 2 |  |
| 447 | `fc-npp` | переменная | src/forthc.fth:359 | 4 |  |
| 448 | `fc-latest` | переменная | src/forthc.fth:359 | 4 |  |
| 449 | `fc-sga` | переменная | src/forthc.fth:359 | 14 |  |
| 450 | `fc-ltab` | переменная | src/forthc.fth:360 | 3 |  |
| 451 | `fc-ls` | переменная | src/forthc.fth:360 | 3 |  |
| 452 | `fc-lw` | переменная | src/forthc.fth:360 | 3 |  |
| 453 | `fc-ldst` | переменная | src/forthc.fth:360 | 2 |  |
| 454 | `fc-seg+` | определение `:` | src/forthc.fth:361 | 21 |  |
| 455 | `fc-pp+` | определение `:` | src/forthc.fth:364 | 1 |  |
| 456 | `fc-slookup` | определение `:` | src/forthc.fth:365 | 8 |  |
| 457 | `fc-nx` | переменная | src/forthc.fth:384 | 3 |  |
| 458 | `fc-nv` | переменная | src/forthc.fth:384 | 2 |  |
| 459 | `fc-nt` | переменная | src/forthc.fth:384 | 3 |  |
| 460 | `fc-negate-chain` | определение `:` | src/forthc.fth:385 | 1 |  |
| 461 | `fc-gw` | переменная | src/forthc.fth:392 | 4 |  |
| 462 | `fc-gs` | переменная | src/forthc.fth:392 | 2 |  |
| 463 | `fc-gs2` | переменная | src/forthc.fth:392 | 2 |  |
| 464 | `fc-gts` | переменная | src/forthc.fth:392 | 6 |  |
| 465 | `fc-gdst` | переменная | src/forthc.fth:392 | 2 |  |
| 466 | `fc-negate-select` | определение `:` | src/forthc.fth:393 | 4 |  |
| 467 | `fc-sfinish` | определение `:` | src/forthc.fth:398 | 2 |  |
| 468 | `fc-pr` | данные `create` | src/forthc.fth:401 | 2 |  |
| 469 | `fc-xs` | данные `create` | src/forthc.fth:401 | 2 |  |
| 470 | `fc-m4` | переменная | src/forthc.fth:402 | 2 |  |
| 471 | `fc-mj` | переменная | src/forthc.fth:402 | 11 |  |
| 472 | `fc-mk` | переменная | src/forthc.fth:402 | 6 |  |
| 473 | `fc-p@` | определение `:` | src/forthc.fth:403 | 3 |  |
| 474 | `fc-p!` | определение `:` | src/forthc.fth:404 | 1 |  |
| 475 | `fc-x@` | определение `:` | src/forthc.fth:405 | 3 |  |
| 476 | `fc-x!` | определение `:` | src/forthc.fth:406 | 2 |  |
| 477 | `fc-build-mul` | определение `:` | src/forthc.fth:407 | 1 |  |
| 478 | `fc-sub` | данные `create` | src/forthc.fth:425 | 2 |  |
| 479 | `fc-qsel` | переменная | src/forthc.fth:425 | 2 |  |
| 480 | `fc-absa` | переменная | src/forthc.fth:426 | 5 |  |
| 481 | `fc-absb` | переменная | src/forthc.fth:426 | 3 |  |
| 482 | `fc-ta` | переменная | src/forthc.fth:426 | 4 |  |
| 483 | `fc-tb` | переменная | src/forthc.fth:426 | 2 |  |
| 484 | `fc-rem` | переменная | src/forthc.fth:427 | 7 |  |
| 485 | `fc-tr` | переменная | src/forthc.fth:427 | 7 |  |
| 486 | `fc-q` | переменная | src/forthc.fth:427 | 3 |  |
| 487 | `fc-tq` | переменная | src/forthc.fth:427 | 4 |  |
| 488 | `fc-k` | переменная | src/forthc.fth:427 | 5 |  |
| 489 | `fc-w` | переменная | src/forthc.fth:428 | 14 |  |
| 490 | `fc-lo` | переменная | src/forthc.fth:428 | 7 |  |
| 491 | `fc-tlo` | переменная | src/forthc.fth:428 | 7 |  |
| 492 | `fc-t0` | переменная | src/forthc.fth:428 | 4 |  |
| 493 | `fc-t1` | переменная | src/forthc.fth:428 | 4 |  |
| 494 | `fc-qr` | переменная | src/forthc.fth:428 | 4 |  |
| 495 | `fc-tqk` | переменная | src/forthc.fth:428 | 3 |  |
| 496 | `fc-sub@` | определение `:` | src/forthc.fth:429 | 7 |  |
| 497 | `fc-step` | определение `:` | src/forthc.fth:431 | 3 |  |
| 498 | `fc-div-step` | определение `:` | src/forthc.fth:438 | 1 |  |
| 499 | `fc-build-div` | определение `:` | src/forthc.fth:455 | 1 |  |
| 500 | `fc-mul-entry` | переменная | src/forthc.fth:471 | 2 |  |
| 501 | `fc-mul-exit` | переменная | src/forthc.fth:471 | 2 |  |
| 502 | `fc-div-entry` | переменная | src/forthc.fth:471 | 4 |  |
| 503 | `fc-div-exit` | переменная | src/forthc.fth:471 | 4 |  |
| 504 | `fc-hl` | переменная | src/forthc.fth:472 | 4 |  |
| 505 | `fc-hcont` | переменная | src/forthc.fth:472 | 3 |  |
| 506 | `fc-row-or-new` | определение `:` | src/forthc.fth:473 | 2 |  |
| 507 | `fc-call-helper` | определение `:` | src/forthc.fth:476 | 4 |  |
| 508 | `fc-result1` | определение `:` | src/forthc.fth:481 | 3 |  |
| 509 | `fc-s1` | переменная | src/forthc.fth:482 | 2 |  |
| 510 | `fc-s2` | переменная | src/forthc.fth:482 | 2 |  |
| 511 | `fc-r1` | переменная | src/forthc.fth:482 | 2 |  |
| 512 | `fc-result2` | определение `:` | src/forthc.fth:483 | 1 |  |
| 513 | `fc-ll` | переменная | src/forthc.fth:489 | 8 |  |
| 514 | `fc-llr` | переменная | src/forthc.fth:489 | 4 |  |
| 515 | `fc-llv` | переменная | src/forthc.fth:489 | 4 |  |
| 516 | `fc-plit` | переменная | src/forthc.fth:489 | 7 |  |
| 517 | `fc-plr` | переменная | src/forthc.fth:489 | 5 |  |
| 518 | `fc-plv` | переменная | src/forthc.fth:489 | 6 |  |
| 519 | `fc-literal` | определение `:` | src/forthc.fth:490 | 8 |  |
| 520 | `fc-or-zero` | определение `:` | src/forthc.fth:492 | 2 |  |
| 521 | `fc-ba` | переменная | src/forthc.fth:495 | 13 |  |
| 522 | `fc-bb` | переменная | src/forthc.fth:495 | 13 |  |
| 523 | `fc-br` | переменная | src/forthc.fth:495 | 9 |  |
| 524 | `fc-binary` | определение `:` | src/forthc.fth:497 | 10 |  |
| 525 | `fc-r-at` | определение `:` | src/forthc.fth:521 | 2 |  |
| 526 | `fc-pop-pinned` | определение `:` | src/forthc.fth:524 | 3 |  |
| 527 | `fc-sk` | переменная | src/forthc.fth:526 | 12 |  |
| 528 | `fc-shift-copy` | определение `:` | src/forthc.fth:527 | 2 |  |
| 529 | `fc-inc` | определение `:` | src/forthc.fth:532 | 3 |  |
| 530 | `fc-read-key` | определение `:` | src/forthc.fth:535 | 1 |  |
| 531 | `fc-text` | переменная | src/forthc.fth:541 | 10 |  |
| 532 | `fc-tlen` | переменная | src/forthc.fth:541 | 11 |  |
| 533 | `fc-pos` | переменная | src/forthc.fth:541 | 14 |  |
| 534 | `fc-text-size` | переменная | src/forthc.fth:541 | 6 | вход бута (хост) |
| 535 | `fc-tok` | данные `create` | src/forthc.fth:542 | 14 |  |
| 536 | `fc-tl` | переменная | src/forthc.fth:542 | 18 |  |
| 537 | `fc-reset` | определение `:` | src/forthc.fth:543 | 3 |  |
| 538 | `fc-append` | определение `:` | src/forthc.fth:544 | 1 |  |
| 539 | `fc\|` | определение `:` | src/forthc.fth:548 | 1 | вход бута (хост) |
| 540 | `fc-ch` | определение `:` | src/forthc.fth:549 | 5 |  |
| 541 | `fc-more?` | определение `:` | src/forthc.fth:550 | 6 |  |
| 542 | `fc-next` | определение `:` | src/forthc.fth:554 | 4 |  |
| 543 | `fc-next!` | определение `:` | src/forthc.fth:562 | 6 |  |
| 544 | `fc-is?` | определение `:` | src/forthc.fth:564 | 1 |  |
| 545 | `fc-raw` | определение `:` | src/forthc.fth:568 | 1 |  |
| 546 | `fc-string-token` | определение `:` | src/forthc.fth:570 | 1 |  |
| 547 | `fc-names-size` | переменная | src/forthc.fth:575 | 5 | вход бута (хост) |
| 548 | `fc-max-words` | переменная | src/forthc.fth:575 | 5 | вход бута (хост) |
| 549 | `fc-names` | переменная | src/forthc.fth:576 | 3 |  |
| 550 | `fc-names-used` | переменная | src/forthc.fth:576 | 5 |  |
| 551 | `fc-wt` | переменная | src/forthc.fth:577 | 3 |  |
| 552 | `fc-nwords` | переменная | src/forthc.fth:577 | 6 |  |
| 553 | `fc-wbk` | переменная | src/forthc.fth:577 | 3 |  |
| 554 | `fc-wt@` | определение `:` | src/forthc.fth:578 | 3 |  |
| 555 | `fc-hash` | определение `:` | src/forthc.fth:579 | 2 |  |
| 556 | `fc-define` | определение `:` | src/forthc.fth:581 | 5 |  |
| 557 | `fc-lookup` | определение `:` | src/forthc.fth:586 | 3 |  |
| 558 | `fc-find` | определение `:` | src/forthc.fth:590 | 4 |  |
| 559 | `fc-here` | переменная | src/forthc.fth:593 | 9 |  |
| 560 | `fc-word` | переменная | src/forthc.fth:593 | 7 |  |
| 561 | `fc-uses` | переменная | src/forthc.fth:593 | 6 |  |
| 562 | `fc-ctl` | данные `create` | src/forthc.fth:596 | 1 |  |
| 563 | `fc-nctl` | переменная | src/forthc.fth:596 | 12 |  |
| 564 | `fc-cleave` | переменная | src/forthc.fth:596 | 2 |  |
| 565 | `fc-ctl@` | определение `:` | src/forthc.fth:597 | 4 |  |
| 566 | `fc-ctl+` | определение `:` | src/forthc.fth:598 | 6 |  |
| 567 | `fc-ctl-` | определение `:` | src/forthc.fth:600 | 7 |  |
| 568 | `fc-do-entry` | определение `:` | src/forthc.fth:602 | 1 |  |
| 569 | `fc-ctl-leave` | определение `:` | src/forthc.fth:606 | 1 |  |
| 570 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:607 | 1 |  |
| 571 | `fc-loop-leave` | определение `:` | src/forthc.fth:608 | 1 |  |
| 572 | `fc-align` | определение `:` | src/forthc.fth:610 | 2 |  |
| 573 | `fc-check-here` | определение `:` | src/forthc.fth:611 | 3 |  |
| 574 | `fc-define-data` | определение `:` | src/forthc.fth:612 | 2 |  |
| 575 | `fc-sat` | переменная | src/forthc.fth:613 | 3 |  |
| 576 | `fc-store-string` | определение `:` | src/forthc.fth:614 | 1 |  |
| 577 | `fc-ct` | данные `create` | src/forthc.fth:620 | 3 |  |
| 578 | `fc-nct` | переменная | src/forthc.fth:620 | 11 |  |
| 579 | `fc-ct+` | определение `:` | src/forthc.fth:621 | 15 |  |
| 580 | `fc-ct-` | определение `:` | src/forthc.fth:622 | 9 |  |
| 581 | `fc-ct2` | определение `:` | src/forthc.fth:623 | 8 |  |
| 582 | `fc-inits` | данные `create` | src/forthc.fth:625 | 2 |  |
| 583 | `fc-ninit` | переменная | src/forthc.fth:625 | 5 |  |
| 584 | `fc-init-open` | переменная | src/forthc.fth:625 | 6 |  |
| 585 | `fc-init` | определение `:` | src/forthc.fth:626 | 1 |  |
| 586 | `fc-scan-uses` | определение `:` | src/forthc.fth:645 | 1 |  |
| 587 | `fc-const-shift` | определение `:` | src/forthc.fth:653 | 2 |  |
| 588 | `fc-lit?` | определение `:` | src/forthc.fth:664 | 2 |  |
| 589 | `fc-mul-lit?` | определение `:` | src/forthc.fth:666 | 1 |  |
| 590 | `fc-shift-lit?` | определение `:` | src/forthc.fth:671 | 2 |  |
| 591 | `fc-pick-roll` | определение `:` | src/forthc.fth:674 | 3 |  |
| 592 | `fc-stx` | переменная | src/forthc.fth:682 | 3 |  |
| 593 | `fc-stlo` | переменная | src/forthc.fth:682 | 11 |  |
| 594 | `fc-sthi` | переменная | src/forthc.fth:682 | 11 |  |
| 595 | `fc-stp` | переменная | src/forthc.fth:682 | 6 |  |
| 596 | `fc-strow` | переменная | src/forthc.fth:682 | 9 |  |
| 597 | `fc-space-store` | определение `:` | src/forthc.fth:683 | 2 |  |
| 598 | `fc-ftr` | переменная | src/forthc.fth:696 | 4 |  |
| 599 | `fc-space-fetch` | определение `:` | src/forthc.fth:697 | 3 |  |
| 600 | `fc-close-init` | определение `:` | src/forthc.fth:710 | 2 |  |
| 601 | `fc-open-init` | определение `:` | src/forthc.fth:713 | 1 |  |
| 602 | `fc-gens` | переменная | src/forthc.fth:729 | 3 |  |
| 603 | `fc-generator` | определение `:` | src/forthc.fth:730 | 74 |  |
| 604 | `fc-literal-name` | определение `:` | src/forthc.fth:732 | 10 |  |
| 605 | `fc-words` | определение `:` | src/forthc.fth:734 | 1 |  |
| 606 | `fc-known` | определение `:` | src/forthc.fth:743 | 1 |  |
| 607 | `fc-defining?` | определение `:` | src/forthc.fth:746 | 6 |  |
| 608 | `fc-code` | определение `:` | src/forthc.fth:749 | 52 | вариант 2 |
| 609 | `fc-fold?` | определение `:` | src/forthc.fth:752 | 13 |  |
| 610 | `fc-top-only` | определение `:` | src/forthc.fth:754 | 6 |  |
| 611 | `fc-not-found` | определение `:` | src/forthc.fth:759 | 1 |  |
| 612 | `fc-word-token` | определение `:` | src/forthc.fth:766 | 1 |  |
| 613 | `fc-compile` | определение `:` | src/forthc.fth:771 | 1 |  |
| 614 | `fc-go` | определение `:` | src/forthc.fth:786 | 3 | вход бута (хост) |
| 615 | `gen+` | определение `:` | src/primitives.fth:9 | 3 |  |
| 616 | `gen-` | определение `:` | src/primitives.fth:10 | 3 |  |
| 617 | `gen-and` | определение `:` | src/primitives.fth:11 | 4 |  |
| 618 | `gen-or` | определение `:` | src/primitives.fth:12 | 5 |  |
| 619 | `gen-xor` | определение `:` | src/primitives.fth:13 | 5 |  |
| 620 | `gen=` | определение `:` | src/primitives.fth:14 | 2 |  |
| 621 | `gen<` | определение `:` | src/primitives.fth:15 | 2 |  |
| 622 | `gen-u<` | определение `:` | src/primitives.fth:16 | 2 |  |
| 623 | `gen-lshift` | определение `:` | src/primitives.fth:17 | 2 |  |
| 624 | `gen-rshift` | определение `:` | src/primitives.fth:19 | 4 |  |
| 625 | `gen-0=` | определение `:` | src/primitives.fth:21 | 2 |  |
| 626 | `gen-cells` | определение `:` | src/primitives.fth:22 | 2 |  |
| 627 | `gen-2*` | определение `:` | src/primitives.fth:23 | 2 |  |
| 628 | `gen-1+` | определение `:` | src/primitives.fth:24 | 2 |  |
| 629 | `gen-1-` | определение `:` | src/primitives.fth:25 | 3 |  |
| 630 | `gen-cell+` | определение `:` | src/primitives.fth:26 | 2 |  |
| 631 | `gen*` | определение `:` | src/primitives.fth:28 | 2 |  |
| 632 | `gen/` | определение `:` | src/primitives.fth:31 | 2 |  |
| 633 | `gen-mod` | определение `:` | src/primitives.fth:32 | 2 |  |
| 634 | `gen/mod` | определение `:` | src/primitives.fth:33 | 2 |  |
| 635 | `gen-dup` | определение `:` | src/primitives.fth:37 | 4 |  |
| 636 | `gen-drop` | определение `:` | src/primitives.fth:38 | 2 |  |
| 637 | `gen-swap` | определение `:` | src/primitives.fth:39 | 3 |  |
| 638 | `gen-over` | определение `:` | src/primitives.fth:40 | 5 |  |
| 639 | `gen-rot` | определение `:` | src/primitives.fth:41 | 2 |  |
| 640 | `gen-pick` | определение `:` | src/primitives.fth:42 | 2 |  |
| 641 | `gen-roll` | определение `:` | src/primitives.fth:43 | 2 |  |
| 642 | `gen->r` | определение `:` | src/primitives.fth:44 | 2 |  |
| 643 | `gen-r>` | определение `:` | src/primitives.fth:45 | 2 |  |
| 644 | `gen-r@` | определение `:` | src/primitives.fth:46 | 4 |  |
| 645 | `gen-j` | определение `:` | src/primitives.fth:47 | 2 |  |
| 646 | `gen-@` | определение `:` | src/primitives.fth:48 | 2 |  |
| 647 | `gen-!` | определение `:` | src/primitives.fth:50 | 2 |  |
| 648 | `gen-c@` | определение `:` | src/primitives.fth:51 | 2 |  |
| 649 | `gen-c!` | определение `:` | src/primitives.fth:53 | 2 |  |
| 650 | `gen-emit` | определение `:` | src/primitives.fth:54 | 2 |  |
| 651 | `gen-key` | определение `:` | src/primitives.fth:57 | 2 |  |
| 652 | `gen-if` | определение `:` | src/primitives.fth:61 | 4 |  |
| 653 | `gen-else` | определение `:` | src/primitives.fth:62 | 2 |  |
| 654 | `gen-then` | определение `:` | src/primitives.fth:64 | 4 |  |
| 655 | `gen-begin` | определение `:` | src/primitives.fth:68 | 2 |  |
| 656 | `gen-until` | определение `:` | src/primitives.fth:69 | 2 |  |
| 657 | `gen-while` | определение `:` | src/primitives.fth:71 | 2 |  |
| 658 | `gen-repeat` | определение `:` | src/primitives.fth:72 | 2 |  |
| 659 | `gen-again` | определение `:` | src/primitives.fth:73 | 2 |  |
| 660 | `gen-do` | определение `:` | src/primitives.fth:75 | 2 |  |
| 661 | `fc-di` | переменная | src/primitives.fth:79 | 3 |  |
| 662 | `fc-dl` | переменная | src/primitives.fth:79 | 3 |  |
| 663 | `gen-?do` | определение `:` | src/primitives.fth:80 | 2 |  |
| 664 | `fc-lv` | переменная | src/primitives.fth:87 | 2 |  |
| 665 | `gen-loop` | определение `:` | src/primitives.fth:88 | 2 |  |
| 666 | `gen-leave` | определение `:` | src/primitives.fth:97 | 2 |  |
| 667 | `gen-unloop` | определение `:` | src/primitives.fth:100 | 2 |  |
| 668 | `gen-exit` | определение `:` | src/primitives.fth:103 | 2 |  |
| 669 | `gen-recurse` | определение `:` | src/primitives.fth:104 | 2 |  |
| 670 | `gen-tick` | определение `:` | src/primitives.fth:105 | 2 |  |
| 671 | `gen-throw` | определение `:` | src/primitives.fth:106 | 4 |  |
| 672 | `gen-call` | определение `:` | src/primitives.fth:113 | 25 |  |
| 673 | `gen-lit` | определение `:` | src/primitives.fth:114 | 10 |  |
| 674 | `gen-pick-n` | определение `:` | src/primitives.fth:116 | 3 |  |
| 675 | `gen-check-range` | определение `:` | src/primitives.fth:120 | 4 |  |
| 676 | `fc-mark-entry` | определение `:` | src/primitives.fth:129 | 1 |  |
| 677 | `gen-space!` | определение `:` | src/primitives.fth:130 | 2 |  |
| 678 | `gen-spacec!` | определение `:` | src/primitives.fth:131 | 2 |  |
| 679 | `gen-space@` | определение `:` | src/primitives.fth:132 | 2 |  |
| 680 | `gen-spacec@` | определение `:` | src/primitives.fth:133 | 2 |  |
| 681 | `gen-check-entry` | определение `:` | src/primitives.fth:137 | 2 |  |
| 682 | `gen-execute` | определение `:` | src/primitives.fth:143 | 2 |  |
| 683 | `gen-catch` | определение `:` | src/primitives.fth:145 | 2 |  |
| 684 | `gen-colon` | определение `:` | src/primitives.fth:149 | 2 |  |
| 685 | `gen-semicolon` | определение `:` | src/primitives.fth:152 | 2 |  |
| 686 | `gen-variable` | определение `:` | src/primitives.fth:154 | 2 |  |
| 687 | `gen-create` | определение `:` | src/primitives.fth:155 | 2 |  |
| 688 | `gen-allot` | определение `:` | src/primitives.fth:156 | 2 |  |
| 689 | `gen-constant` | определение `:` | src/primitives.fth:157 | 2 |  |
| 690 | `gen-decimal` | определение `:` | src/primitives.fth:158 | 2 |  |
| 691 | `gen-kernel-layout` | определение `:` | src/primitives.fth:160 | 2 |  |
| 692 | `gen-backslash` | определение `:` | src/primitives.fth:163 | 2 |  |
| 693 | `gen-paren` | определение `:` | src/primitives.fth:165 | 2 |  |
| 694 | `gen-char` | определение `:` | src/primitives.fth:166 | 2 |  |
| 695 | `gen-string` | определение `:` | src/primitives.fth:167 | 2 |  |
| 696 | `fc-digit@` | определение `:` | src/primitives.fth:176 | 1 |  |
| 697 | `gen-literal` | определение `:` | src/primitives.fth:178 | 2 |  |
| 698 | `fc-name2` | определение `:` | src/primitives.fth:184 | 1 |  |
| 699 | `fc-generators` | определение `:` | src/primitives.fth:187 | 1 |  |
| 700 | `+` | генератор | src/primitives.fth:188 | 463 | слово компилятора `gen+` |
| 701 | `-` | генератор | src/primitives.fth:188 | 45 | слово компилятора `gen-` |
| 702 | `*` | генератор | src/primitives.fth:189 | 79 | слово компилятора `gen*` |
| 703 | `/` | генератор | src/primitives.fth:189 | 3 | слово компилятора `gen/` |
| 704 | `mod` | генератор | src/primitives.fth:190 | 1 | слово компилятора `gen-mod` |
| 705 | `and` | генератор | src/primitives.fth:191 | 97 | слово компилятора `gen-and` |
| 706 | `or` | генератор | src/primitives.fth:191 | 38 | слово компилятора `gen-or` |
| 707 | `xor` | генератор | src/primitives.fth:192 | 5 | слово компилятора `gen-xor` |
| 708 | `lshift` | генератор | src/primitives.fth:192 | 71 | слово компилятора `gen-lshift` |
| 709 | `rshift` | генератор | src/primitives.fth:193 | 54 | слово компилятора `gen-rshift` |
| 710 | `=` | генератор | src/primitives.fth:193 | 43 | слово компилятора `gen=` |
| 711 | `<` | генератор | src/primitives.fth:194 | 27 | слово компилятора `gen<` |
| 712 | `u<` | генератор | src/primitives.fth:194 | 11 | слово компилятора `gen-u<` |
| 713 | `0=` | генератор | src/primitives.fth:195 | 70 | слово компилятора `gen-0=` |
| 714 | `2*` | генератор | src/primitives.fth:195 | 25 | слово компилятора `gen-2*` |
| 715 | `1+` | генератор | src/primitives.fth:196 | 40 | слово компилятора `gen-1+` |
| 716 | `1-` | генератор | src/primitives.fth:196 | 42 | слово компилятора `gen-1-` |
| 717 | `cells` | генератор | src/primitives.fth:197 | 197 | слово компилятора `gen-cells` |
| 718 | `cell+` | генератор | src/primitives.fth:197 | 35 | слово компилятора `gen-cell+` |
| 719 | `dup` | генератор | src/primitives.fth:198 | 248 | слово компилятора `gen-dup` |
| 720 | `drop` | генератор | src/primitives.fth:198 | 171 | слово компилятора `gen-drop` |
| 721 | `swap` | генератор | src/primitives.fth:199 | 118 | слово компилятора `gen-swap` |
| 722 | `over` | генератор | src/primitives.fth:199 | 75 | слово компилятора `gen-over` |
| 723 | `rot` | генератор | src/primitives.fth:200 | 34 | слово компилятора `gen-rot` |
| 724 | `pick` | генератор | src/primitives.fth:200 | 46 | слово компилятора `gen-pick` |
| 725 | `roll` | генератор | src/primitives.fth:201 | 5 | слово компилятора `gen-roll` |
| 726 | `>r` | генератор | src/primitives.fth:201 | 86 | слово компилятора `gen->r` |
| 727 | `r>` | генератор | src/primitives.fth:202 | 90 | слово компилятора `gen-r>` |
| 728 | `r@` | генератор | src/primitives.fth:202 | 68 | слово компилятора `gen-r@` |
| 729 | `i` | генератор | src/primitives.fth:203 | 151 | слово компилятора `gen-r@` |
| 730 | `j` | генератор | src/primitives.fth:203 | 12 | слово компилятора `gen-j` |
| 731 | `@` | генератор | src/primitives.fth:204 | 983 | слово компилятора `gen-@` |
| 732 | `!` | генератор | src/primitives.fth:204 | 537 | слово компилятора `gen-!` |
| 733 | `c@` | генератор | src/primitives.fth:205 | 22 | слово компилятора `gen-c@` |
| 734 | `c!` | генератор | src/primitives.fth:205 | 17 | слово компилятора `gen-c!` |
| 735 | `space!` | генератор | src/primitives.fth:206 | 1 | слово компилятора `gen-space!` |
| 736 | `spacec!` | генератор | src/primitives.fth:206 | 1 | слово компилятора `gen-spacec!` |
| 737 | `emit` | генератор | src/primitives.fth:208 | 4 | слово компилятора `gen-emit` |
| 738 | `key` | генератор | src/primitives.fth:208 | 1 | слово компилятора `gen-key` |
| 739 | `if` | генератор | src/primitives.fth:209 | 216 | слово компилятора `gen-if` |
| 740 | `else` | генератор | src/primitives.fth:209 | 58 | слово компилятора `gen-else` |
| 741 | `then` | генератор | src/primitives.fth:210 | 216 | слово компилятора `gen-then` |
| 742 | `begin` | генератор | src/primitives.fth:210 | 21 | слово компилятора `gen-begin` |
| 743 | `until` | генератор | src/primitives.fth:211 | 1 | слово компилятора `gen-until` |
| 744 | `while` | генератор | src/primitives.fth:211 | 19 | слово компилятора `gen-while` |
| 745 | `repeat` | генератор | src/primitives.fth:212 | 19 | слово компилятора `gen-repeat` |
| 746 | `again` | генератор | src/primitives.fth:212 | 1 | слово компилятора `gen-again` |
| 747 | `do` | генератор | src/primitives.fth:213 | 30 | слово компилятора `gen-do` |
| 748 | `?do` | генератор | src/primitives.fth:213 | 47 | слово компилятора `gen-?do` |
| 749 | `loop` | генератор | src/primitives.fth:214 | 77 | слово компилятора `gen-loop` |
| 750 | `leave` | генератор | src/primitives.fth:214 | 1 | слово компилятора `gen-leave` |
| 751 | `unloop` | генератор | src/primitives.fth:215 | 4 | слово компилятора `gen-unloop` |
| 752 | `exit` | генератор | src/primitives.fth:215 | 48 | слово компилятора `gen-exit` |
| 753 | `recurse` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-recurse` |
| 754 | `execute` | генератор | src/primitives.fth:216 | 9 | слово компилятора `gen-execute` |
| 755 | `[']` | генератор | src/primitives.fth:217 | 127 | слово компилятора `gen-tick` |
| 756 | `catch` | генератор | src/primitives.fth:217 | 1 | слово компилятора `gen-catch` |
| 757 | `throw` | генератор | src/primitives.fth:218 | 69 | слово компилятора `gen-throw` |
| 758 | `:` | генератор | src/primitives.fth:219 | 414 | слово компилятора `gen-colon` |
| 759 | `;` | генератор | src/primitives.fth:219 | 414 | слово компилятора `gen-semicolon` |
| 760 | `variable` | генератор | src/primitives.fth:220 | 264 | слово компилятора `gen-variable` |
| 761 | `create` | генератор | src/primitives.fth:220 | 38 | слово компилятора `gen-create` |
| 762 | `allot` | генератор | src/primitives.fth:221 | 36 | слово компилятора `gen-allot` |
| 763 | `constant` | генератор | src/primitives.fth:221 | 15 | слово компилятора `gen-constant` |
| 764 | `decimal` | генератор | src/primitives.fth:222 | 3 | слово компилятора `gen-decimal` |
| 765 | `kernel-layout` | генератор | src/primitives.fth:222 | 1 | слово компилятора `gen-kernel-layout` |
| 766 | `\` | генератор | src/primitives.fth:223 | 269 | слово компилятора `gen-backslash` |
| 767 | `(` | генератор | src/primitives.fth:223 | 390 | слово компилятора `gen-paren` |
| 768 | `[char]` | генератор | src/primitives.fth:223 | 8 | слово компилятора `gen-char` |
| 769 | `s"` | генератор | src/primitives.fth:224 | 88 | слово компилятора `gen-string` |
| 770 | `literal` | генератор | src/primitives.fth:225 | 417 | слово компилятора `gen-literal` |
| 771 | `0` | цифра (литерал) | src/primitives.fth:226 | 450 | значение 0 |
| 772 | `1` | цифра (литерал) | src/primitives.fth:226 | 351 | значение 1 |
| 773 | `2` | цифра (литерал) | src/primitives.fth:226 | 396 | значение 2 |
| 774 | `3` | цифра (литерал) | src/primitives.fth:226 | 262 | значение 3 |
| 775 | `4` | цифра (литерал) | src/primitives.fth:227 | 214 | значение 4 |
| 776 | `5` | цифра (литерал) | src/primitives.fth:227 | 97 | значение 5 |
| 777 | `6` | цифра (литерал) | src/primitives.fth:227 | 127 | значение 6 |
| 778 | `7` | цифра (литерал) | src/primitives.fth:227 | 42 | значение 7 |
| 779 | `8` | цифра (литерал) | src/primitives.fth:228 | 146 | значение 8 |
| 780 | `9` | цифра (литерал) | src/primitives.fth:228 | 37 | значение 9 |
| 781 | `fc-install-generators` | определение `:` | src/primitives.fth:229 | 1 |  |
| 782 | `heap-start` | данные `create` | src/main.fth:4 | 1 |  |
| 783 | `fc-read` | определение `:` | src/main.fth:7 | 2 |  |
| 784 | `fc-sizes` | определение `:` | src/main.fth:12 | 2 |  |
| 785 | `kn-at` | переменная | src/kernel.fth:12 | 5 |  |
| 786 | `kn-put` | определение `:` | src/kernel.fth:13 | 1 |  |
| 787 | `kn-order` | определение `:` | src/kernel.fth:23 | 1 |  |
| 788 | `kn-compile` | определение `:` | src/kernel.fth:24 | 1 |  |
| 789 | `kn-.n` | определение `:` | src/kernel.fth:25 | 1 |  |
| 790 | `main` | определение `:` | src/kernel.fth:29 | 1 | вариант 2 |
| 791 | `kn-heap-start` | данные `create` | src/kernel.fth:34 | 1 |  |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 82.

## Определены, но не использованы

Слов: 24. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

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
| `fc-depth` | определение `:` | src/forthc.fth:741 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:742 |
| `/mod` | генератор | src/primitives.fth:190 |
| `space@` | генератор | src/primitives.fth:207 |
| `spacec@` | генератор | src/primitives.fth:207 |
| `main` (вариант 1) | определение `:` | src/main.fth:15 |

## Слова, которые при буте исполняет хост

Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки `backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках 82; все они определены в определении языка (генератором в `primitives.fth` или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: `!` `*` `+` `+!` `-` `-rot` `/` `/string` `0<` `0<>` `0=` `0>` `1+` `1-` `2!` `2*` `2@` `2drop` `2dup` `2over` `2swap` `<` `<>` `=` `>` `>in` `>r` `?do` `?dup` `@` `again` `allocate` `and` `begin` `c!` `c@` `cell+` `cells` `cmove` `cmove>` `compare` `decimal` `do` `drop` `dup` `else` `execute` `exit` `fill` `free` `i` `if` `invert` `j` `leave` `loop` `lshift` `max` `min` `negate` `nip` `or` `over` `pick` `r>` `r@` `repeat` `roll` `rot` `rshift` `source` `swap` `then` `throw` `tuck` `type` `u<` `u>` `unloop` `until` `while` `xor`.

Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро читает каналом `key`), `source` и `>in` — слова только этого пути.
