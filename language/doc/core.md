# Ядро языка (14.8)

Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 982** (определение `:` — 480, переменная — 323, генератор — 71, данные `create` — 63, константа — 29, цифра (литерал) — 10, основание — 6).

## Основание

Основание — слова-копирования: генераторы строки (копия — приёмник и источник) и слоя (ячейка строк) из `src/backend.fth`. Определение инструкции — она сама: тело этих слов не сводится к другим словам языка, а строка и слой — сами инструкции индексного пространства.

| Слово | Что порождает | Файл:строка |
|---|---|---|
| `lay-copy` | строка: копирование n бит из источника в приёмник | src/backend.fth:117 |
| `lay-link-row` | строка: копирование ссылки на следующий слой | src/backend.fth:116 |
| `lay-row` | строка: добавляет строку в слой | src/backend.fth:180 |
| `lay-new-record` | слой: новый слой в ячейке | src/backend.fth:143 |
| `lay-lone` | слой: отдельный слой в новой ячейке | src/backend.fth:147 |
| `lay-layer` | слой: следующий слой последовательности | src/backend.fth:150 |

## Слова ядра

Вид: генератор (слово словаря, исполняемое при компиляции, `doc/generators.md`; в пояснении слово компилятора), определение `:`, переменная, константа, данные `create`, цифра (литерал, `doc/literals.md`), основание. «Исп.» — число ссылок из других слов (цифры — и из чисел определения). Повторное определение имени — «вариант N» (старое имя остаётся у прежних ссылок).

| № | Слово | Вид | Файл:строка | Исп. | Пояснение |
|---|---|---|---|---|---|
| 1 | `nip` | определение `:` | src/prelude.fth:4 | 25 |  |
| 2 | `tuck` | определение `:` | src/prelude.fth:5 | 8 |  |
| 3 | `-rot` | определение `:` | src/prelude.fth:6 | 7 |  |
| 4 | `2dup` | определение `:` | src/prelude.fth:7 | 13 |  |
| 5 | `2drop` | определение `:` | src/prelude.fth:8 | 25 |  |
| 6 | `2swap` | определение `:` | src/prelude.fth:9 | 6 |  |
| 7 | `2over` | определение `:` | src/prelude.fth:10 | 2 |  |
| 8 | `?dup` | определение `:` | src/prelude.fth:11 | 19 |  |
| 9 | `negate` | определение `:` | src/prelude.fth:12 | 5 |  |
| 10 | `invert` | определение `:` | src/prelude.fth:13 | 2 |  |
| 11 | `>` | определение `:` | src/prelude.fth:14 | 9 |  |
| 12 | `u>` | определение `:` | src/prelude.fth:15 | 7 |  |
| 13 | `<>` | определение `:` | src/prelude.fth:16 | 11 |  |
| 14 | `0<` | определение `:` | src/prelude.fth:17 | 5 |  |
| 15 | `0>` | определение `:` | src/prelude.fth:18 | 3 |  |
| 16 | `0<>` | определение `:` | src/prelude.fth:19 | 4 |  |
| 17 | `max` | определение `:` | src/prelude.fth:20 | 21 |  |
| 18 | `min` | определение `:` | src/prelude.fth:21 | 5 |  |
| 19 | `+!` | определение `:` | src/prelude.fth:22 | 69 |  |
| 20 | `2@` | определение `:` | src/prelude.fth:23 | 4 |  |
| 21 | `2!` | определение `:` | src/prelude.fth:24 | 2 |  |
| 22 | `fill-cell` | переменная | src/prelude.fth:26 | 2 |  |
| 23 | `fill` | определение `:` | src/prelude.fth:27 | 11 |  |
| 24 | `cmove` | определение `:` | src/prelude.fth:31 | 18 |  |
| 25 | `cmove>` | определение `:` | src/prelude.fth:35 | 1 |  |
| 26 | `/string` | определение `:` | src/prelude.fth:36 | 2 |  |
| 27 | `type` | определение `:` | src/prelude.fth:37 | 6 |  |
| 28 | `compare` | определение `:` | src/prelude.fth:38 | 2 |  |
| 29 | `source` | определение `:` | src/prelude.fth:43 | 2 |  |
| 30 | `>in` | переменная | src/prelude.fth:44 | 2 |  |
| 31 | `fc-tok` | данные `create` | src/backend.fth:10 | 19 |  |
| 32 | `fc-tl` | переменная | src/backend.fth:10 | 24 |  |
| 33 | `fc-.n` | определение `:` | src/backend.fth:11 | 1 |  |
| 34 | `fc-reject` | определение `:` | src/backend.fth:14 | 57 |  |
| 35 | `lay-size` | переменная | src/backend.fth:15 | 18 |  |
| 36 | `lay-a` | переменная | src/backend.fth:15 | 17 |  |
| 37 | `lay-slots` | переменная | src/backend.fth:15 | 15 |  |
| 38 | `lay-cell-bits` | переменная | src/backend.fth:15 | 14 |  |
| 39 | `lay-chunk` | переменная | src/backend.fth:16 | 7 |  |
| 40 | `lay-chunk-buf` | переменная | src/backend.fth:16 | 5 |  |
| 41 | `lay-lbuf` | переменная | src/backend.fth:16 | 5 |  |
| 42 | `lay-pool` | переменная | src/backend.fth:16 | 3 |  |
| 43 | `lay-ebuf` | переменная | src/backend.fth:17 | 3 |  |
| 44 | `lay-dest` | переменная | src/backend.fth:17 | 6 |  |
| 45 | `lay-sink` | переменная | src/backend.fth:17 | 5 |  |
| 46 | `lay-start-cell` | переменная | src/backend.fth:17 | 3 |  |
| 47 | `lay-rev` | данные `create` | src/backend.fth:19 | 10 |  |
| 48 | `lay-rev-init` | определение `:` | src/backend.fth:20 | 1 |  |
| 49 | `lay-inst` | определение `:` | src/backend.fth:24 | 10 |  |
| 50 | `lay-layer-bits` | определение `:` | src/backend.fth:25 | 7 |  |
| 51 | `lay-lbytes` | определение `:` | src/backend.fth:26 | 4 |  |
| 52 | `lay-stdin` | определение `:` | src/backend.fth:27 | 4 |  |
| 53 | `lay-stdout` | определение `:` | src/backend.fth:28 | 3 |  |
| 54 | `lay-pos` | константа | src/backend.fth:34 | 5 |  |
| 55 | `lay-cells` | константа | src/backend.fth:34 | 15 |  |
| 56 | `lay-rec` | константа | src/backend.fth:35 | 11 |  |
| 57 | `lay-hdr` | константа | src/backend.fth:35 | 3 |  |
| 58 | `lay-cap` | константа | src/backend.fth:35 | 5 |  |
| 59 | `lay-req` | определение `:` | src/backend.fth:36 | 7 |  |
| 60 | `lay-bits` | определение `:` | src/backend.fth:37 | 7 |  |
| 61 | `lay-numeric` | определение `:` | src/backend.fth:38 | 7 |  |
| 62 | `lay-numeric4` | определение `:` | src/backend.fth:43 | 1 |  |
| 63 | `lay-field-check` | определение `:` | src/backend.fth:46 | 1 |  |
| 64 | `lay-encode` | определение `:` | src/backend.fth:48 | 3 |  |
| 65 | `lay-start` | переменная | src/backend.fth:58 | 8 |  |
| 66 | `lay-len` | переменная | src/backend.fth:58 | 10 |  |
| 67 | `lay-rows` | данные `create` | src/backend.fth:59 | 6 |  |
| 68 | `lay-row!` | определение `:` | src/backend.fth:60 | 7 |  |
| 69 | `lay-clear-rows` | определение `:` | src/backend.fth:62 | 3 |  |
| 70 | `lay-loader` | определение `:` | src/backend.fth:63 | 1 |  |
| 71 | `lay-stream-flush` | определение `:` | src/backend.fth:70 | 3 |  |
| 72 | `lay-begin-chunk` | определение `:` | src/backend.fth:74 | 2 |  |
| 73 | `lay-put` | определение `:` | src/backend.fth:76 | 13 |  |
| 74 | `lay-scratch` | данные `create` | src/backend.fth:94 | 2 |  |
| 75 | `lay-put-numeric` | определение `:` | src/backend.fth:95 | 3 |  |
| 76 | `lay-max-layers` | константа | src/backend.fth:99 | 3 |  |
| 77 | `lay-record` | определение `:` | src/backend.fth:100 | 1 |  |
| 78 | `lay-pending` | переменная | src/backend.fth:101 | 10 |  |
| 79 | `lay-head` | переменная | src/backend.fth:101 | 6 |  |
| 80 | `lay-next-cell` | переменная | src/backend.fth:101 | 8 |  |
| 81 | `lay-seq#` | переменная | src/backend.fth:102 | 8 |  |
| 82 | `lay-seq-first` | переменная | src/backend.fth:102 | 3 |  |
| 83 | `lay-seq-entry` | переменная | src/backend.fth:102 | 2 |  |
| 84 | `lay-seq-last` | переменная | src/backend.fth:102 | 2 |  |
| 85 | `lay-foff` | данные `create` | src/backend.fth:103 | 2 |  |
| 86 | `lay-foff-init` | определение `:` | src/backend.fth:104 | 1 |  |
| 87 | `lay-chunk-mem` | данные `create` | src/backend.fth:106 | 1 |  |
| 88 | `lay-lbuf-mem` | данные `create` | src/backend.fth:106 | 1 |  |
| 89 | `lay-ebuf-mem` | данные `create` | src/backend.fth:106 | 1 |  |
| 90 | `lay-pool-mem` | данные `create` | src/backend.fth:107 | 1 |  |
| 91 | `lay-bufs` | определение `:` | src/backend.fth:108 | 1 |  |
| 92 | `lay-machine` | определение `:` | src/backend.fth:109 | 1 |  |
| 93 | `lay-field` | определение `:` | src/backend.fth:115 | 48 |  |
| 94 | `lay-link-row` | основание | src/backend.fth:116 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 95 | `lay-copy` | основание | src/backend.fth:117 | 79 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 96 | `lay-builder` | определение `:` | src/backend.fth:119 | 1 |  |
| 97 | `lay-new-cell` | определение `:` | src/backend.fth:120 | 10 |  |
| 98 | `lay-branch-bit` | определение `:` | src/backend.fth:122 | 20 |  |
| 99 | `lay-branch-step` | определение `:` | src/backend.fth:123 | 3 |  |
| 100 | `lay-group` | определение `:` | src/backend.fth:124 | 5 |  |
| 101 | `lay-layer-cell` | определение `:` | src/backend.fth:127 | 48 |  |
| 102 | `lay-next!` | определение `:` | src/backend.fth:128 | 19 |  |
| 103 | `lay-count` | определение `:` | src/backend.fth:129 | 7 |  |
| 104 | `lay-row-addr` | определение `:` | src/backend.fth:130 | 4 |  |
| 105 | `lay-pending@` | определение `:` | src/backend.fth:131 | 5 |  |
| 106 | `lay-encode-layer` | определение `:` | src/backend.fth:132 | 1 |  |
| 107 | `lay-on-write` | переменная | src/backend.fth:138 | 6 |  |
| 108 | `lay-write` | определение `:` | src/backend.fth:139 | 2 |  |
| 109 | `lay-write-oldest` | определение `:` | src/backend.fth:142 | 1 |  |
| 110 | `lay-new-record` | основание | src/backend.fth:143 | 8 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 111 | `lay-lone` | основание | src/backend.fth:147 | 7 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 112 | `lay-seq` | определение `:` | src/backend.fth:148 | 8 |  |
| 113 | `lay-last` | определение `:` | src/backend.fth:149 | 4 |  |
| 114 | `lay-layer` | основание | src/backend.fth:150 | 89 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 115 | `lay-entry` | определение `:` | src/backend.fth:155 | 3 |  |
| 116 | `lay-jump` | определение `:` | src/backend.fth:156 | 10 |  |
| 117 | `lay-l1` | переменная | src/backend.fth:157 | 4 |  |
| 118 | `lay-h1` | переменная | src/backend.fth:157 | 3 |  |
| 119 | `lay-l2` | переменная | src/backend.fth:157 | 4 |  |
| 120 | `lay-h2` | переменная | src/backend.fth:157 | 3 |  |
| 121 | `lay-ra` | переменная | src/backend.fth:158 | 2 |  |
| 122 | `lay-rb` | переменная | src/backend.fth:158 | 2 |  |
| 123 | `lay-cur` | переменная | src/backend.fth:158 | 7 |  |
| 124 | `lay-clash?` | определение `:` | src/backend.fth:160 | 1 |  |
| 125 | `lay-row-clash?` | определение `:` | src/backend.fth:165 | 1 |  |
| 126 | `lay-new-row` | данные `create` | src/backend.fth:170 | 6 |  |
| 127 | `lay-row-set` | определение `:` | src/backend.fth:171 | 2 |  |
| 128 | `lay-full?` | определение `:` | src/backend.fth:173 | 2 |  |
| 129 | `lay-clashes?` | определение `:` | src/backend.fth:174 | 2 |  |
| 130 | `lay-fits?` | определение `:` | src/backend.fth:178 | 2 |  |
| 131 | `lay-row` | основание | src/backend.fth:180 | 88 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 132 | `lay-flush` | определение `:` | src/backend.fth:184 | 14 |  |
| 133 | `lay-finish` | определение `:` | src/backend.fth:187 | 1 |  |
| 134 | `dj-reader` | переменная | src/backend.fth:205 | 3 |  |
| 135 | `dj-bad-cell` | переменная | src/backend.fth:205 | 1 |  |
| 136 | `dj-bad-rule` | переменная | src/backend.fth:205 | 4 |  |
| 137 | `dj-bsh` | переменная | src/backend.fth:206 | 3 |  |
| 138 | `dj-csh` | переменная | src/backend.fth:206 | 6 |  |
| 139 | `dj-ssh` | переменная | src/backend.fth:206 | 2 |  |
| 140 | `dj-fsh` | переменная | src/backend.fth:206 | 2 |  |
| 141 | `dj-first` | переменная | src/backend.fth:207 | 2 |  |
| 142 | `dj-end` | переменная | src/backend.fth:207 | 2 |  |
| 143 | `dj-pa` | переменная | src/backend.fth:207 | 3 |  |
| 144 | `dj-cb` | переменная | src/backend.fth:207 | 8 |  |
| 145 | `dj-vdl` | переменная | src/backend.fth:208 | 19 |  |
| 146 | `dj-vdh` | переменная | src/backend.fth:208 | 14 |  |
| 147 | `dj-vsl` | переменная | src/backend.fth:208 | 18 |  |
| 148 | `dj-vsh` | переменная | src/backend.fth:208 | 15 |  |
| 149 | `dj-tc` | переменная | src/backend.fth:209 | 5 |  |
| 150 | `dj-ts` | переменная | src/backend.fth:209 | 6 |  |
| 151 | `dj-tf` | переменная | src/backend.fth:209 | 5 |  |
| 152 | `dj-tb` | переменная | src/backend.fth:209 | 2 |  |
| 153 | `dj-tn` | переменная | src/backend.fth:209 | 2 |  |
| 154 | `dj-tk` | переменная | src/backend.fth:209 | 7 |  |
| 155 | `dj-vt` | переменная | src/backend.fth:209 | 3 |  |
| 156 | `dj-blk` | переменная | src/backend.fth:210 | 5 |  |
| 157 | `dj-hb` | переменная | src/backend.fth:210 | 5 |  |
| 158 | `dj-he` | переменная | src/backend.fth:210 | 3 |  |
| 159 | `dj-pr` | данные `create` | src/backend.fth:211 | 2 |  |
| 160 | `dj-tr` | данные `create` | src/backend.fth:211 | 3 |  |
| 161 | `dj-narrow` | константа | src/backend.fth:212 | 1 |  |
| 162 | `dj-seen` | данные `create` | src/backend.fth:213 | 2 |  |
| 163 | `dj-nseen` | переменная | src/backend.fth:213 | 6 |  |
| 164 | `dj-get` | определение `:` | src/backend.fth:214 | 10 |  |
| 165 | `dj-fail` | определение `:` | src/backend.fth:215 | 8 |  |
| 166 | `dj-blk?` | определение `:` | src/backend.fth:216 | 7 |  |
| 167 | `dj-in?` | определение `:` | src/backend.fth:217 | 4 |  |
| 168 | `dj-row!` | определение `:` | src/backend.fth:220 | 2 |  |
| 169 | `dj-row@` | определение `:` | src/backend.fth:222 | 3 |  |
| 170 | `dj-nop?` | определение `:` | src/backend.fth:224 | 4 |  |
| 171 | `dj-load` | определение `:` | src/backend.fth:225 | 1 |  |
| 172 | `dj-sys?` | определение `:` | src/backend.fth:233 | 1 |  |
| 173 | `dj-head?` | определение `:` | src/backend.fth:235 | 1 |  |
| 174 | `dj-row-ok?` | определение `:` | src/backend.fth:238 | 1 |  |
| 175 | `dj-in-blk?` | определение `:` | src/backend.fth:247 | 2 |  |
| 176 | `dj-touches?` | определение `:` | src/backend.fth:251 | 1 |  |
| 177 | `dj-seen?` | определение `:` | src/backend.fth:252 | 1 |  |
| 178 | `dj-seen!` | определение `:` | src/backend.fth:257 | 1 |  |
| 179 | `dj-wide` | определение `:` | src/backend.fth:261 | 1 |  |
| 180 | `dj-patch` | определение `:` | src/backend.fth:277 | 1 |  |
| 181 | `dj-nn` | переменная | src/backend.fth:287 | 4 |  |
| 182 | `dj-lo` | переменная | src/backend.fth:287 | 2 |  |
| 183 | `dj-hi` | переменная | src/backend.fth:287 | 2 |  |
| 184 | `dj-scan` | определение `:` | src/backend.fth:288 | 1 |  |
| 185 | `dj-rows` | определение `:` | src/backend.fth:297 | 1 |  |
| 186 | `dj-prove` | определение `:` | src/backend.fth:304 | 3 |  |
| 187 | `lay-t1` | переменная | src/compute.fth:7 | 25 |  |
| 188 | `lay-t2` | переменная | src/compute.fth:7 | 13 |  |
| 189 | `lay-t3` | переменная | src/compute.fth:7 | 7 |  |
| 190 | `lay-t4` | переменная | src/compute.fth:7 | 4 |  |
| 191 | `lay-t5` | переменная | src/compute.fth:7 | 8 |  |
| 192 | `lay-lo` | переменная | src/compute.fth:8 | 5 |  |
| 193 | `lay-hi` | переменная | src/compute.fth:8 | 2 |  |
| 194 | `lay-l0` | переменная | src/compute.fth:9 | 21 |  |
| 195 | `lay-l1` | переменная | src/compute.fth:9 | 13 | вариант 2 |
| 196 | `lay-l2` | переменная | src/compute.fth:9 | 8 | вариант 2 |
| 197 | `lay-l3` | переменная | src/compute.fth:9 | 7 |  |
| 198 | `lay-l4` | переменная | src/compute.fth:9 | 7 |  |
| 199 | `lay-l5` | переменная | src/compute.fth:9 | 6 |  |
| 200 | `lay-work` | определение `:` | src/compute.fth:10 | 3 |  |
| 201 | `lay-cell-bit` | определение `:` | src/compute.fth:11 | 3 |  |
| 202 | `lay-link-slot` | определение `:` | src/compute.fth:12 | 6 |  |
| 203 | `lay-item-cells` | константа | src/compute.fth:13 | 1 |  |
| 204 | `lay-max-items` | константа | src/compute.fth:13 | 2 |  |
| 205 | `lay-items` | данные `create` | src/compute.fth:14 | 1 |  |
| 206 | `lay-nitems` | переменная | src/compute.fth:15 | 8 |  |
| 207 | `lay-item@` | определение `:` | src/compute.fth:16 | 6 |  |
| 208 | `lay-lookups-begin` | определение `:` | src/compute.fth:17 | 12 |  |
| 209 | `lay-item` | определение `:` | src/compute.fth:18 | 11 |  |
| 210 | `lay-seg` | определение `:` | src/compute.fth:23 | 17 |  |
| 211 | `lay-sl` | данные `create` | src/compute.fth:29 | 2 |  |
| 212 | `lay-sh` | данные `create` | src/compute.fth:29 | 2 |  |
| 213 | `lay-read-layer` | данные `create` | src/compute.fth:30 | 2 |  |
| 214 | `lay-read-slot` | данные `create` | src/compute.fth:30 | 2 |  |
| 215 | `lay-used` | данные `create` | src/compute.fth:31 | 2 |  |
| 216 | `lay-nused` | переменная | src/compute.fth:31 | 5 |  |
| 217 | `lay-rl` | переменная | src/compute.fth:31 | 6 |  |
| 218 | `lay-pk` | переменная | src/compute.fth:31 | 4 |  |
| 219 | `lay-pkl` | переменная | src/compute.fth:31 | 4 |  |
| 220 | `lay-npatches` | определение `:` | src/compute.fth:32 | 1 |  |
| 221 | `lay-used?` | определение `:` | src/compute.fth:33 | 1 |  |
| 222 | `lay-place-reads` | определение `:` | src/compute.fth:35 | 1 |  |
| 223 | `lay-patch` | определение `:` | src/compute.fth:47 | 1 |  |
| 224 | `lay-lookups` | определение `:` | src/compute.fth:56 | 12 |  |
| 225 | `lay-al` | данные `create` | src/compute.fth:62 | 2 |  |
| 226 | `lay-ar` | данные `create` | src/compute.fth:62 | 2 |  |
| 227 | `lay-ax` | переменная | src/compute.fth:63 | 4 |  |
| 228 | `lay-aa` | переменная | src/compute.fth:63 | 2 |  |
| 229 | `lay-ab` | переменная | src/compute.fth:63 | 2 |  |
| 230 | `lay-atab` | переменная | src/compute.fth:63 | 2 |  |
| 231 | `lay-acarry` | переменная | src/compute.fth:63 | 2 |  |
| 232 | `lay-al@` | определение `:` | src/compute.fth:64 | 8 |  |
| 233 | `lay-rd` | определение `:` | src/compute.fth:65 | 3 |  |
| 234 | `lay-adder-patch` | определение `:` | src/compute.fth:66 | 4 |  |
| 235 | `lay-adder` | определение `:` | src/compute.fth:71 | 6 |  |
| 236 | `lay-dsrc` | переменная | src/compute.fth:87 | 3 |  |
| 237 | `lay-dk` | переменная | src/compute.fth:87 | 5 |  |
| 238 | `lay-dg` | переменная | src/compute.fth:87 | 3 |  |
| 239 | `lay-dp` | переменная | src/compute.fth:87 | 3 |  |
| 240 | `lay-dx` | переменная | src/compute.fth:87 | 4 |  |
| 241 | `lay-decide` | определение `:` | src/compute.fth:88 | 2 |  |
| 242 | `lay-table-at` | переменная | src/compute.fth:95 | 4 |  |
| 243 | `lay-table-limit` | переменная | src/compute.fth:95 | 2 |  |
| 244 | `lay-tbuf` | переменная | src/compute.fth:95 | 6 |  |
| 245 | `lay-tx` | переменная | src/compute.fth:96 | 5 |  |
| 246 | `lay-tbits` | переменная | src/compute.fth:96 | 4 |  |
| 247 | `lay-ts` | переменная | src/compute.fth:96 | 6 |  |
| 248 | `lay-tsize` | переменная | src/compute.fth:96 | 6 |  |
| 249 | `lay-tbase` | переменная | src/compute.fth:96 | 4 |  |
| 250 | `lay-tper` | переменная | src/compute.fth:96 | 3 |  |
| 251 | `lay-tables` | определение `:` | src/compute.fth:97 | 2 |  |
| 252 | `lay-table-mem` | данные `create` | src/compute.fth:99 | 1 |  |
| 253 | `lay-table-area` | определение `:` | src/compute.fth:100 | 2 |  |
| 254 | `lay-table-done` | определение `:` | src/compute.fth:108 | 2 |  |
| 255 | `lay-table` | определение `:` | src/compute.fth:110 | 23 |  |
| 256 | `lay-add-entry` | определение `:` | src/compute.fth:127 | 1 |  |
| 257 | `lay-sub-entry` | определение `:` | src/compute.fth:129 | 2 |  |
| 258 | `lay-xor-entry` | определение `:` | src/compute.fth:131 | 1 |  |
| 259 | `lay-or-entry` | определение `:` | src/compute.fth:132 | 1 |  |
| 260 | `lay-and-entry` | определение `:` | src/compute.fth:133 | 1 |  |
| 261 | `lay-or8-entry` | определение `:` | src/compute.fth:134 | 1 |  |
| 262 | `lay-fz` | переменная | src/compute.fth:135 | 3 |  |
| 263 | `lay-fu` | переменная | src/compute.fth:135 | 4 |  |
| 264 | `lay-fs` | переменная | src/compute.fth:135 | 3 |  |
| 265 | `lay-pair` | определение `:` | src/compute.fth:136 | 6 |  |
| 266 | `lay-flags-entry` | определение `:` | src/compute.fth:137 | 1 |  |
| 267 | `lay-not5-entry` | определение `:` | src/compute.fth:144 | 1 |  |
| 268 | `lay-sign-entry` | определение `:` | src/compute.fth:145 | 1 |  |
| 269 | `lay-fill24-entry` | определение `:` | src/compute.fth:146 | 1 |  |
| 270 | `lay-fill16-entry` | определение `:` | src/compute.fth:147 | 1 |  |
| 271 | `lay-inc1-entry` | определение `:` | src/compute.fth:148 | 1 |  |
| 272 | `lay-inc2-entry` | определение `:` | src/compute.fth:149 | 1 |  |
| 273 | `lay-t-add` | переменная | src/compute.fth:150 | 7 |  |
| 274 | `lay-t-sub` | переменная | src/compute.fth:150 | 5 |  |
| 275 | `lay-t-xor` | переменная | src/compute.fth:150 | 5 |  |
| 276 | `lay-t-or` | переменная | src/compute.fth:150 | 2 |  |
| 277 | `lay-t-and` | переменная | src/compute.fth:150 | 2 |  |
| 278 | `lay-t-or8` | переменная | src/compute.fth:151 | 2 |  |
| 279 | `lay-t-flags` | переменная | src/compute.fth:151 | 2 |  |
| 280 | `lay-t-not5` | переменная | src/compute.fth:151 | 2 |  |
| 281 | `lay-t-sign32` | переменная | src/compute.fth:151 | 2 |  |
| 282 | `lay-t-fill24` | переменная | src/compute.fth:152 | 1 |  |
| 283 | `lay-t-fill16` | переменная | src/compute.fth:152 | 1 |  |
| 284 | `lay-t-inc1` | переменная | src/compute.fth:152 | 1 |  |
| 285 | `lay-t-inc2` | переменная | src/compute.fth:152 | 1 |  |
| 286 | `lay-standard-tables` | определение `:` | src/compute.fth:153 | 1 |  |
| 287 | `lay-oo` | переменная | src/compute.fth:161 | 2 |  |
| 288 | `lay-os` | переменная | src/compute.fth:161 | 2 |  |
| 289 | `lay-ol` | переменная | src/compute.fth:161 | 4 |  |
| 290 | `lay-oh` | переменная | src/compute.fth:161 | 3 |  |
| 291 | `lay-or-chunks` | определение `:` | src/compute.fth:162 | 3 |  |
| 292 | `lay-cr` | переменная | src/compute.fth:168 | 5 |  |
| 293 | `lay-ca` | переменная | src/compute.fth:168 | 4 |  |
| 294 | `lay-cb` | переменная | src/compute.fth:168 | 4 |  |
| 295 | `lay-logic` | определение `:` | src/compute.fth:175 | 4 |  |
| 296 | `lay-sres` | переменная | src/compute.fth:181 | 3 |  |
| 297 | `lay-sa` | переменная | src/compute.fth:181 | 7 |  |
| 298 | `lay-samt` | переменная | src/compute.fth:181 | 8 |  |
| 299 | `lay-sw` | переменная | src/compute.fth:181 | 9 |  |
| 300 | `lay-szero` | переменная | src/compute.fth:181 | 4 |  |
| 301 | `lay-sarg` | переменная | src/compute.fth:182 | 6 |  |
| 302 | `lay-sign` | переменная | src/compute.fth:182 | 6 |  |
| 303 | `lay-shift-row` | определение `:` | src/compute.fth:183 | 3 |  |
| 304 | `lay-shift-patch` | определение `:` | src/compute.fth:184 | 6 |  |
| 305 | `lay-shift-right` | определение `:` | src/compute.fth:186 | 1 |  |
| 306 | `lay-shift-left` | определение `:` | src/compute.fth:203 | 1 |  |
| 307 | `fc-size` | константа | src/forthc.fth:6 | 2 |  |
| 308 | `fc-cellb` | константа | src/forthc.fth:6 | 5 |  |
| 309 | `fc-l` | константа | src/forthc.fth:6 | 1 |  |
| 310 | `fc-a` | константа | src/forthc.fth:6 | 2 |  |
| 311 | `fc-d` | переменная | src/forthc.fth:8 | 3 |  |
| 312 | `fc-first` | переменная | src/forthc.fth:8 | 3 |  |
| 313 | `fc-guard` | переменная | src/forthc.fth:10 | 20 |  |
| 314 | `fc-bbits` | константа | src/forthc.fth:16 | 7 |  |
| 315 | `fc-abits` | константа | src/forthc.fth:16 | 5 |  |
| 316 | `fc-ebits` | константа | src/forthc.fth:16 | 6 |  |
| 317 | `fc-etab` | константа | src/forthc.fth:16 | 5 |  |
| 318 | `fc-rbits` | константа | src/forthc.fth:17 | 5 |  |
| 319 | `fc-rtab` | константа | src/forthc.fth:17 | 4 |  |
| 320 | `fc-layout` | определение `:` | src/forthc.fth:18 | 1 |  |
| 321 | `fc-d+` | определение `:` | src/forthc.fth:20 | 26 |  |
| 322 | `fc-sp` | определение `:` | src/forthc.fth:21 | 4 |  |
| 323 | `fc-rp` | определение `:` | src/forthc.fth:21 | 13 |  |
| 324 | `fc-code` | определение `:` | src/forthc.fth:21 | 1 |  |
| 325 | `fc-regs` | определение `:` | src/forthc.fth:22 | 2 |  |
| 326 | `fc-nregs` | константа | src/forthc.fth:22 | 2 |  |
| 327 | `fc-tmp` | определение `:` | src/forthc.fth:23 | 12 |  |
| 328 | `fc-xr` | определение `:` | src/forthc.fth:23 | 10 |  |
| 329 | `fc-z` | определение `:` | src/forthc.fth:23 | 4 |  |
| 330 | `fc-idx` | определение `:` | src/forthc.fth:23 | 5 |  |
| 331 | `fc-ma` | определение `:` | src/forthc.fth:24 | 6 |  |
| 332 | `fc-mb` | определение `:` | src/forthc.fth:24 | 6 |  |
| 333 | `fc-mp` | определение `:` | src/forthc.fth:24 | 2 |  |
| 334 | `fc-mq` | определение `:` | src/forthc.fth:24 | 3 |  |
| 335 | `fc-mr` | определение `:` | src/forthc.fth:24 | 3 |  |
| 336 | `fc-zero` | определение `:` | src/forthc.fth:25 | 12 |  |
| 337 | `fc-consts` | определение `:` | src/forthc.fth:25 | 3 |  |
| 338 | `fc-sw` | определение `:` | src/forthc.fth:26 | 2 |  |
| 339 | `fc-su` | определение `:` | src/forthc.fth:26 | 1 |  |
| 340 | `fc-key` | определение `:` | src/forthc.fth:26 | 3 |  |
| 341 | `fc-bp` | определение `:` | src/forthc.fth:26 | 2 |  |
| 342 | `fc-tab` | определение `:` | src/forthc.fth:27 | 1 |  |
| 343 | `fc-stk` | определение `:` | src/forthc.fth:27 | 3 |  |
| 344 | `fc-rstk` | определение `:` | src/forthc.fth:28 | 13 |  |
| 345 | `fc-scr0` | определение `:` | src/forthc.fth:28 | 1 |  |
| 346 | `fc-links` | определение `:` | src/forthc.fth:29 | 2 |  |
| 347 | `fc-max-links` | константа | src/forthc.fth:29 | 1 |  |
| 348 | `fc-link-chunk` | константа | src/forthc.fth:29 | 1 |  |
| 349 | `fc-mem` | определение `:` | src/forthc.fth:30 | 7 |  |
| 350 | `fc-mw` | константа | src/forthc.fth:30 | 2 |  |
| 351 | `fc-htab` | определение `:` | src/forthc.fth:30 | 1 |  |
| 352 | `fc-data-start` | константа | src/forthc.fth:31 | 1 |  |
| 353 | `fc-off` | данные `create` | src/forthc.fth:33 | 2 |  |
| 354 | `fc-oc` | переменная | src/forthc.fth:33 | 2 |  |
| 355 | `fc-t-rev8` | переменная | src/forthc.fth:34 | 3 |  |
| 356 | `fc-t-zero32` | переменная | src/forthc.fth:34 | 2 |  |
| 357 | `fc-t-nz2` | переменная | src/forthc.fth:34 | 2 |  |
| 358 | `fc-t-lt32` | переменная | src/forthc.fth:34 | 2 |  |
| 359 | `fc-t-xr2` | переменная | src/forthc.fth:35 | 2 |  |
| 360 | `fc-t-ult32` | переменная | src/forthc.fth:35 | 2 |  |
| 361 | `fc-t-bytepos` | переменная | src/forthc.fth:35 | 2 |  |
| 362 | `fc-off@` | определение `:` | src/forthc.fth:36 | 2 |  |
| 363 | `fc-off-table` | определение `:` | src/forthc.fth:37 | 1 |  |
| 364 | `fc-rev-entry` | определение `:` | src/forthc.fth:40 | 1 |  |
| 365 | `fc-zero-entry` | определение `:` | src/forthc.fth:41 | 1 |  |
| 366 | `fc-nz-entry` | определение `:` | src/forthc.fth:42 | 1 |  |
| 367 | `fc-lt-entry` | определение `:` | src/forthc.fth:43 | 1 |  |
| 368 | `fc-xr2-entry` | определение `:` | src/forthc.fth:46 | 1 |  |
| 369 | `fc-ult-entry` | определение `:` | src/forthc.fth:47 | 1 |  |
| 370 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 371 | `fc-tables` | определение `:` | src/forthc.fth:49 | 1 |  |
| 372 | `fc-mul4-entry` | определение `:` | src/forthc.fth:60 | 1 |  |
| 373 | `fc-qsel-entry` | определение `:` | src/forthc.fth:63 | 1 |  |
| 374 | `fc-max-consts` | переменная | src/forthc.fth:66 | 4 | вход бута (хост) |
| 375 | `fc-ck` | переменная | src/forthc.fth:66 | 3 |  |
| 376 | `fc-nconsts` | переменная | src/forthc.fth:66 | 7 |  |
| 377 | `fc-nbuckets` | переменная | src/forthc.fth:67 | 7 | вход бута (хост) |
| 378 | `fc-cbk` | переменная | src/forthc.fth:67 | 3 |  |
| 379 | `fc-ck@` | определение `:` | src/forthc.fth:68 | 3 |  |
| 380 | `fc-chash` | определение `:` | src/forthc.fth:69 | 1 |  |
| 381 | `fc-cb` | переменная | src/forthc.fth:70 | 3 |  |
| 382 | `fc-const2` | определение `:` | src/forthc.fth:71 | 1 |  |
| 383 | `fc-const` | определение `:` | src/forthc.fth:81 | 4 |  |
| 384 | `fc-lit` | определение `:` | src/forthc.fth:84 | 3 |  |
| 385 | `fc-bit0` | определение `:` | src/forthc.fth:85 | 1 |  |
| 386 | `fc-bit1` | определение `:` | src/forthc.fth:86 | 1 |  |
| 387 | `fc-length` | определение `:` | src/forthc.fth:87 | 1 |  |
| 388 | `fc-lit-of` | определение `:` | src/forthc.fth:88 | 1 |  |
| 389 | `fc-load` | определение `:` | src/forthc.fth:90 | 1 |  |
| 390 | `fc-nlinks` | переменная | src/forthc.fth:92 | 5 |  |
| 391 | `fc-link-buf` | переменная | src/forthc.fth:92 | 4 |  |
| 392 | `fc-nbuf` | переменная | src/forthc.fth:92 | 8 |  |
| 393 | `fc-put-links` | определение `:` | src/forthc.fth:93 | 2 |  |
| 394 | `fc-link-pair` | определение `:` | src/forthc.fth:97 | 2 |  |
| 395 | `fc-link-const` | определение `:` | src/forthc.fth:102 | 1 |  |
| 396 | `fc-eight` | данные `create` | src/forthc.fth:103 | 7 |  |
| 397 | `fc-zeros` | данные `create` | src/forthc.fth:103 | 4 |  |
| 398 | `fc-put-consts` | определение `:` | src/forthc.fth:104 | 1 |  |
| 399 | `fc-cache` | данные `create` | src/forthc.fth:111 | 8 |  |
| 400 | `fc-n` | переменная | src/forthc.fth:111 | 28 |  |
| 401 | `fc-pin` | данные `create` | src/forthc.fth:112 | 13 |  |
| 402 | `fc-npin` | переменная | src/forthc.fth:112 | 20 |  |
| 403 | `fc-c@` | определение `:` | src/forthc.fth:113 | 8 |  |
| 404 | `fc-push` | определение `:` | src/forthc.fth:114 | 28 |  |
| 405 | `fc-pop1` | определение `:` | src/forthc.fth:115 | 36 |  |
| 406 | `fc-in?` | определение `:` | src/forthc.fth:116 | 3 |  |
| 407 | `fc-reg` | определение `:` | src/forthc.fth:117 | 16 |  |
| 408 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:122 | 1 |  |
| 409 | `fc-scr` | переменная | src/forthc.fth:123 | 3 |  |
| 410 | `fc-scratch` | определение `:` | src/forthc.fth:124 | 11 |  |
| 411 | `fc-offs` | данные `create` | src/forthc.fth:127 | 5 |  |
| 412 | `fc-noff` | переменная | src/forthc.fth:127 | 9 |  |
| 413 | `fc-ptr` | переменная | src/forthc.fth:127 | 4 |  |
| 414 | `fc-iw` | переменная | src/forthc.fth:128 | 4 |  |
| 415 | `fc-adjust` | определение `:` | src/forthc.fth:129 | 7 |  |
| 416 | `fc-prow` | данные `create` | src/forthc.fth:135 | 2 |  |
| 417 | `fc-nrow` | переменная | src/forthc.fth:135 | 8 |  |
| 418 | `fc-pl` | данные `create` | src/forthc.fth:136 | 2 |  |
| 419 | `fc-pslot` | данные `create` | src/forthc.fth:136 | 2 |  |
| 420 | `fc-rl` | переменная | src/forthc.fth:137 | 3 |  |
| 421 | `fc-f0` | переменная | src/forthc.fth:137 | 2 |  |
| 422 | `fc-f1` | переменная | src/forthc.fth:137 | 2 |  |
| 423 | `fc-psh` | переменная | src/forthc.fth:137 | 2 |  |
| 424 | `fc-row+` | определение `:` | src/forthc.fth:138 | 3 |  |
| 425 | `fc-4@` | определение `:` | src/forthc.fth:140 | 3 |  |
| 426 | `fc-patched` | определение `:` | src/forthc.fth:141 | 3 |  |
| 427 | `fc-popped` | данные `create` | src/forthc.fth:152 | 2 |  |
| 428 | `fc-srcs` | данные `create` | src/forthc.fth:152 | 13 |  |
| 429 | `fc-nsrc` | переменная | src/forthc.fth:152 | 20 |  |
| 430 | `fc-mbase` | переменная | src/forthc.fth:153 | 8 |  |
| 431 | `fc-mptr` | переменная | src/forthc.fth:153 | 4 |  |
| 432 | `fc-mn` | переменная | src/forthc.fth:153 | 7 |  |
| 433 | `fc-mw2` | переменная | src/forthc.fth:153 | 6 |  |
| 434 | `fc-popped@` | определение `:` | src/forthc.fth:154 | 6 |  |
| 435 | `fc-shift` | определение `:` | src/forthc.fth:155 | 4 |  |
| 436 | `fc-mem-pop` | определение `:` | src/forthc.fth:156 | 3 |  |
| 437 | `fc-push-group` | определение `:` | src/forthc.fth:164 | 2 |  |
| 438 | `fc-dup-at` | определение `:` | src/forthc.fth:170 | 1 |  |
| 439 | `fc-rest` | данные `create` | src/forthc.fth:172 | 2 |  |
| 440 | `fc-nrest` | переменная | src/forthc.fth:172 | 3 |  |
| 441 | `fc-mem-push` | определение `:` | src/forthc.fth:173 | 7 |  |
| 442 | `fc-src1` | определение `:` | src/forthc.fth:179 | 3 |  |
| 443 | `fc-need` | определение `:` | src/forthc.fth:180 | 17 |  |
| 444 | `fc-spill` | определение `:` | src/forthc.fth:186 | 16 |  |
| 445 | `fc-pop` | определение `:` | src/forthc.fth:192 | 11 |  |
| 446 | `fc-max-log` | константа | src/forthc.fth:197 | 1 |  |
| 447 | `fc-max-notes` | константа | src/forthc.fth:197 | 3 |  |
| 448 | `fc-log` | переменная | src/forthc.fth:198 | 3 |  |
| 449 | `fc-nlog` | переменная | src/forthc.fth:198 | 5 |  |
| 450 | `fc-decs` | переменная | src/forthc.fth:198 | 2 |  |
| 451 | `fc-ndec` | переменная | src/forthc.fth:198 | 6 |  |
| 452 | `fc-calls` | переменная | src/forthc.fth:198 | 2 |  |
| 453 | `fc-ncall` | переменная | src/forthc.fth:198 | 6 |  |
| 454 | `fc-pend` | переменная | src/forthc.fth:199 | 2 |  |
| 455 | `fc-npend` | переменная | src/forthc.fth:199 | 9 |  |
| 456 | `fc-unknown` | переменная | src/forthc.fth:199 | 7 |  |
| 457 | `fc-lc` | переменная | src/forthc.fth:200 | 3 |  |
| 458 | `fc-lb` | переменная | src/forthc.fth:200 | 3 |  |
| 459 | `fc-row-n` | определение `:` | src/forthc.fth:201 | 1 |  |
| 460 | `fc-mem-row?` | определение `:` | src/forthc.fth:202 | 1 |  |
| 461 | `fc-log-layer` | определение `:` | src/forthc.fth:203 | 2 |  |
| 462 | `fc-log-begin` | определение `:` | src/forthc.fth:215 | 3 |  |
| 463 | `fc-log-end` | определение `:` | src/forthc.fth:217 | 4 |  |
| 464 | `fc-by-execution` | определение `:` | src/forthc.fth:218 | 7 |  |
| 465 | `fc-dec@` | определение `:` | src/forthc.fth:219 | 2 |  |
| 466 | `fc-call@` | определение `:` | src/forthc.fth:220 | 2 |  |
| 467 | `fc-log-decision` | определение `:` | src/forthc.fth:221 | 2 |  |
| 468 | `fc-log-call` | определение `:` | src/forthc.fth:225 | 2 |  |
| 469 | `fc-callee` | переменная | src/forthc.fth:229 | 4 |  |
| 470 | `fc-live` | переменная | src/forthc.fth:231 | 7 |  |
| 471 | `fc-tramp` | переменная | src/forthc.fth:231 | 6 |  |
| 472 | `fc-ex` | переменная | src/forthc.fth:231 | 4 |  |
| 473 | `fc-halt` | переменная | src/forthc.fth:231 | 3 |  |
| 474 | `fc-jump` | определение `:` | src/forthc.fth:232 | 8 |  |
| 475 | `fc-end` | определение `:` | src/forthc.fth:233 | 12 |  |
| 476 | `fc-begin-block` | определение `:` | src/forthc.fth:234 | 21 |  |
| 477 | `fc-rows1` | определение `:` | src/forthc.fth:238 | 12 |  |
| 478 | `fc-nonzero` | определение `:` | src/forthc.fth:239 | 2 |  |
| 479 | `fc-branch` | определение `:` | src/forthc.fth:242 | 5 |  |
| 480 | `fc-rtab-at` | определение `:` | src/forthc.fth:243 | 1 |  |
| 481 | `fc-nret` | переменная | src/forthc.fth:244 | 6 |  |
| 482 | `fc-ret-link` | определение `:` | src/forthc.fth:248 | 3 |  |
| 483 | `fc-ret-base` | определение `:` | src/forthc.fth:253 | 4 |  |
| 484 | `fc-call` | определение `:` | src/forthc.fth:254 | 4 |  |
| 485 | `fc-v0` | переменная | src/forthc.fth:258 | 4 |  |
| 486 | `fc-v1` | переменная | src/forthc.fth:258 | 4 |  |
| 487 | `fc-jw` | определение `:` | src/forthc.fth:259 | 2 |  |
| 488 | `fc-xw` | определение `:` | src/forthc.fth:260 | 2 |  |
| 489 | `fc-xoff` | определение `:` | src/forthc.fth:261 | 2 |  |
| 490 | `fc-etab-at` | определение `:` | src/forthc.fth:262 | 1 |  |
| 491 | `fc-ex-base` | определение `:` | src/forthc.fth:263 | 1 |  |
| 492 | `fc-call-indirect` | определение `:` | src/forthc.fth:264 | 1 |  |
| 493 | `fc-ret-p` | переменная | src/forthc.fth:271 | 4 |  |
| 494 | `fc-ret-l` | переменная | src/forthc.fth:271 | 6 |  |
| 495 | `fc-rs0` | переменная | src/forthc.fth:271 | 3 |  |
| 496 | `fc-rs1` | переменная | src/forthc.fth:271 | 3 |  |
| 497 | `fc-ret-m` | переменная | src/forthc.fth:271 | 3 |  |
| 498 | `fc-ret-t` | переменная | src/forthc.fth:271 | 3 |  |
| 499 | `fc-ret-patch` | определение `:` | src/forthc.fth:272 | 4 |  |
| 500 | `fc-ret-masked` | определение `:` | src/forthc.fth:274 | 1 |  |
| 501 | `fc-ret` | определение `:` | src/forthc.fth:280 | 3 |  |
| 502 | `fc-ca` | переменная | src/forthc.fth:292 | 3 |  |
| 503 | `fc-cl0` | переменная | src/forthc.fth:292 | 4 |  |
| 504 | `fc-cl1` | переменная | src/forthc.fth:292 | 4 |  |
| 505 | `fc-cr` | переменная | src/forthc.fth:292 | 4 |  |
| 506 | `fc-cslot` | переменная | src/forthc.fth:292 | 3 |  |
| 507 | `fc-csh` | переменная | src/forthc.fth:292 | 2 |  |
| 508 | `fc-cv` | переменная | src/forthc.fth:293 | 3 |  |
| 509 | `fc-cres` | переменная | src/forthc.fth:293 | 6 |  |
| 510 | `fc-cmode` | переменная | src/forthc.fth:293 | 6 |  |
| 511 | `fc-ar` | переменная | src/forthc.fth:293 | 5 |  |
| 512 | `fc-chk-read` | определение `:` | src/forthc.fth:294 | 1 |  |
| 513 | `fc-chk-seg` | определение `:` | src/forthc.fth:296 | 1 |  |
| 514 | `fc-as` | переменная | src/forthc.fth:299 | 2 |  |
| 515 | `fc-af` | переменная | src/forthc.fth:299 | 2 |  |
| 516 | `fc-al0` | переменная | src/forthc.fth:299 | 2 |  |
| 517 | `fc-al1` | переменная | src/forthc.fth:299 | 2 |  |
| 518 | `fc-apl` | переменная | src/forthc.fth:299 | 3 |  |
| 519 | `fc-afld` | переменная | src/forthc.fth:299 | 3 |  |
| 520 | `fc-access-patch` | определение `:` | src/forthc.fth:300 | 2 |  |
| 521 | `fc-access` | определение `:` | src/forthc.fth:305 | 1 |  |
| 522 | `fc-width` | определение `:` | src/forthc.fth:307 | 4 |  |
| 523 | `fc-check` | определение `:` | src/forthc.fth:308 | 4 |  |
| 524 | `fc-ring` | константа | src/forthc.fth:324 | 5 |  |
| 525 | `fc-window` | константа | src/forthc.fth:324 | 1 |  |
| 526 | `fc-sl` | данные `create` | src/forthc.fth:325 | 2 |  |
| 527 | `fc-stabs` | переменная | src/forthc.fth:325 | 2 |  |
| 528 | `fc-slen` | переменная | src/forthc.fth:326 | 7 |  |
| 529 | `fc-slow` | переменная | src/forthc.fth:326 | 4 |  |
| 530 | `fc-sinit` | определение `:` | src/forthc.fth:327 | 2 |  |
| 531 | `fc-sbegin` | определение `:` | src/forthc.fth:328 | 2 |  |
| 532 | `fc-tabs` | определение `:` | src/forthc.fth:329 | 3 |  |
| 533 | `fc-at` | определение `:` | src/forthc.fth:330 | 4 |  |
| 534 | `fc-has?` | определение `:` | src/forthc.fth:335 | 1 |  |
| 535 | `fc-tab+` | определение `:` | src/forthc.fth:336 | 1 |  |
| 536 | `fc-prw` | данные `create` | src/forthc.fth:337 | 6 |  |
| 537 | `fc-ptab` | переменная | src/forthc.fth:337 | 5 |  |
| 538 | `fc-place` | определение `:` | src/forthc.fth:338 | 3 |  |
| 539 | `fc-scopy` | определение `:` | src/forthc.fth:348 | 9 |  |
| 540 | `fc-segs` | данные `create` | src/forthc.fth:349 | 2 |  |
| 541 | `fc-nseg` | переменная | src/forthc.fth:349 | 5 |  |
| 542 | `fc-pp` | данные `create` | src/forthc.fth:350 | 2 |  |
| 543 | `fc-npp` | переменная | src/forthc.fth:350 | 4 |  |
| 544 | `fc-latest` | переменная | src/forthc.fth:350 | 4 |  |
| 545 | `fc-sga` | переменная | src/forthc.fth:350 | 14 |  |
| 546 | `fc-ltab` | переменная | src/forthc.fth:351 | 3 |  |
| 547 | `fc-ls` | переменная | src/forthc.fth:351 | 3 |  |
| 548 | `fc-lw` | переменная | src/forthc.fth:351 | 3 |  |
| 549 | `fc-ldst` | переменная | src/forthc.fth:351 | 2 |  |
| 550 | `fc-seg+` | определение `:` | src/forthc.fth:352 | 21 |  |
| 551 | `fc-pp+` | определение `:` | src/forthc.fth:355 | 1 |  |
| 552 | `fc-slookup` | определение `:` | src/forthc.fth:356 | 8 |  |
| 553 | `fc-nx` | переменная | src/forthc.fth:374 | 3 |  |
| 554 | `fc-nv` | переменная | src/forthc.fth:374 | 2 |  |
| 555 | `fc-nt` | переменная | src/forthc.fth:374 | 3 |  |
| 556 | `fc-negate-chain` | определение `:` | src/forthc.fth:375 | 1 |  |
| 557 | `fc-gw` | переменная | src/forthc.fth:381 | 4 |  |
| 558 | `fc-gs` | переменная | src/forthc.fth:381 | 2 |  |
| 559 | `fc-gs2` | переменная | src/forthc.fth:381 | 2 |  |
| 560 | `fc-gts` | переменная | src/forthc.fth:381 | 6 |  |
| 561 | `fc-gdst` | переменная | src/forthc.fth:381 | 2 |  |
| 562 | `fc-negate-select` | определение `:` | src/forthc.fth:382 | 4 |  |
| 563 | `fc-sfinish` | определение `:` | src/forthc.fth:387 | 2 |  |
| 564 | `fc-pr` | данные `create` | src/forthc.fth:390 | 2 |  |
| 565 | `fc-xs` | данные `create` | src/forthc.fth:390 | 2 |  |
| 566 | `fc-m4` | переменная | src/forthc.fth:391 | 2 |  |
| 567 | `fc-mj` | переменная | src/forthc.fth:391 | 11 |  |
| 568 | `fc-mk` | переменная | src/forthc.fth:391 | 6 |  |
| 569 | `fc-p@` | определение `:` | src/forthc.fth:392 | 3 |  |
| 570 | `fc-p!` | определение `:` | src/forthc.fth:393 | 1 |  |
| 571 | `fc-x@` | определение `:` | src/forthc.fth:394 | 3 |  |
| 572 | `fc-x!` | определение `:` | src/forthc.fth:395 | 2 |  |
| 573 | `fc-build-mul` | определение `:` | src/forthc.fth:396 | 1 |  |
| 574 | `fc-sub` | данные `create` | src/forthc.fth:414 | 2 |  |
| 575 | `fc-qsel` | переменная | src/forthc.fth:414 | 2 |  |
| 576 | `fc-absa` | переменная | src/forthc.fth:415 | 5 |  |
| 577 | `fc-absb` | переменная | src/forthc.fth:415 | 3 |  |
| 578 | `fc-ta` | переменная | src/forthc.fth:415 | 4 |  |
| 579 | `fc-tb` | переменная | src/forthc.fth:415 | 2 |  |
| 580 | `fc-rem` | переменная | src/forthc.fth:416 | 7 |  |
| 581 | `fc-tr` | переменная | src/forthc.fth:416 | 7 |  |
| 582 | `fc-q` | переменная | src/forthc.fth:416 | 3 |  |
| 583 | `fc-tq` | переменная | src/forthc.fth:416 | 4 |  |
| 584 | `fc-k` | переменная | src/forthc.fth:416 | 5 |  |
| 585 | `fc-w` | переменная | src/forthc.fth:417 | 14 |  |
| 586 | `fc-lo` | переменная | src/forthc.fth:417 | 7 |  |
| 587 | `fc-tlo` | переменная | src/forthc.fth:417 | 7 |  |
| 588 | `fc-t0` | переменная | src/forthc.fth:417 | 4 |  |
| 589 | `fc-t1` | переменная | src/forthc.fth:417 | 4 |  |
| 590 | `fc-qr` | переменная | src/forthc.fth:417 | 4 |  |
| 591 | `fc-tqk` | переменная | src/forthc.fth:417 | 3 |  |
| 592 | `fc-sub@` | определение `:` | src/forthc.fth:418 | 7 |  |
| 593 | `fc-step` | определение `:` | src/forthc.fth:419 | 3 |  |
| 594 | `fc-div-step` | определение `:` | src/forthc.fth:426 | 1 |  |
| 595 | `fc-build-div` | определение `:` | src/forthc.fth:443 | 1 |  |
| 596 | `fc-mul-entry` | переменная | src/forthc.fth:459 | 4 |  |
| 597 | `fc-mul-exit` | переменная | src/forthc.fth:459 | 2 |  |
| 598 | `fc-div-entry` | переменная | src/forthc.fth:459 | 5 |  |
| 599 | `fc-div-exit` | переменная | src/forthc.fth:459 | 4 |  |
| 600 | `fc-hl` | переменная | src/forthc.fth:460 | 5 |  |
| 601 | `fc-hcont` | переменная | src/forthc.fth:460 | 4 |  |
| 602 | `fc-mul-cost` | данные `create` | src/forthc.fth:461 | 2 |  |
| 603 | `fc-div-cost` | данные `create` | src/forthc.fth:461 | 2 |  |
| 604 | `fc-row-or-new` | определение `:` | src/forthc.fth:462 | 2 |  |
| 605 | `fc-call-helper` | определение `:` | src/forthc.fth:464 | 4 |  |
| 606 | `fc-result1` | определение `:` | src/forthc.fth:474 | 3 |  |
| 607 | `fc-s1` | переменная | src/forthc.fth:475 | 2 |  |
| 608 | `fc-s2` | переменная | src/forthc.fth:475 | 2 |  |
| 609 | `fc-r1` | переменная | src/forthc.fth:475 | 2 |  |
| 610 | `fc-result2` | определение `:` | src/forthc.fth:476 | 1 |  |
| 611 | `fc-forbid` | константа | src/forthc.fth:484 | 2 |  |
| 612 | `fc-pexit` | переменная | src/forthc.fth:485 | 2 |  |
| 613 | `fc-ptramp` | переменная | src/forthc.fth:485 | 2 |  |
| 614 | `fc-pd` | переменная | src/forthc.fth:485 | 5 |  |
| 615 | `fc-pc` | переменная | src/forthc.fth:485 | 5 |  |
| 616 | `fc-ends` | переменная | src/forthc.fth:485 | 3 |  |
| 617 | `fc-pb` | переменная | src/forthc.fth:486 | 5 |  |
| 618 | `fc-pcp` | переменная | src/forthc.fth:486 | 5 |  |
| 619 | `fc-pln` | переменная | src/forthc.fth:486 | 5 |  |
| 620 | `fc-pk` | переменная | src/forthc.fth:486 | 4 |  |
| 621 | `fc-pcall` | переменная | src/forthc.fth:486 | 3 |  |
| 622 | `fc-best` | данные `create` | src/forthc.fth:487 | 10 |  |
| 623 | `fc-pend@` | определение `:` | src/forthc.fth:488 | 7 |  |
| 624 | `fc-reach` | определение `:` | src/forthc.fth:489 | 2 |  |
| 625 | `fc-take` | определение `:` | src/forthc.fth:498 | 1 |  |
| 626 | `fc-end-path` | определение `:` | src/forthc.fth:505 | 2 |  |
| 627 | `fc-to` | определение `:` | src/forthc.fth:509 | 2 |  |
| 628 | `fc-node` | определение `:` | src/forthc.fth:513 | 1 |  |
| 629 | `fc-path` | определение `:` | src/forthc.fth:532 | 3 |  |
| 630 | `fc-cost!` | определение `:` | src/forthc.fth:541 | 4 |  |
| 631 | `fc-ll` | переменная | src/forthc.fth:543 | 8 |  |
| 632 | `fc-llr` | переменная | src/forthc.fth:543 | 4 |  |
| 633 | `fc-llv` | переменная | src/forthc.fth:543 | 4 |  |
| 634 | `fc-plit` | переменная | src/forthc.fth:543 | 7 |  |
| 635 | `fc-plr` | переменная | src/forthc.fth:543 | 5 |  |
| 636 | `fc-plv` | переменная | src/forthc.fth:543 | 7 |  |
| 637 | `fc-literal` | определение `:` | src/forthc.fth:544 | 15 |  |
| 638 | `fc-or-zero` | определение `:` | src/forthc.fth:546 | 2 |  |
| 639 | `fc-ba` | переменная | src/forthc.fth:549 | 13 |  |
| 640 | `fc-bb` | переменная | src/forthc.fth:549 | 13 |  |
| 641 | `fc-br` | переменная | src/forthc.fth:549 | 9 |  |
| 642 | `fc-binary` | определение `:` | src/forthc.fth:550 | 10 |  |
| 643 | `fc-r-at` | определение `:` | src/forthc.fth:574 | 2 |  |
| 644 | `fc-pop-pinned` | определение `:` | src/forthc.fth:577 | 3 |  |
| 645 | `fc-sk` | переменная | src/forthc.fth:578 | 12 |  |
| 646 | `fc-shift-copy` | определение `:` | src/forthc.fth:579 | 2 |  |
| 647 | `fc-inc` | определение `:` | src/forthc.fth:583 | 3 |  |
| 648 | `fc-read-key` | определение `:` | src/forthc.fth:586 | 1 |  |
| 649 | `fc-text-mem` | данные `create` | src/forthc.fth:591 | 1 |  |
| 650 | `fc-text` | переменная | src/forthc.fth:592 | 13 |  |
| 651 | `fc-tlen` | переменная | src/forthc.fth:592 | 14 |  |
| 652 | `fc-pos` | переменная | src/forthc.fth:592 | 24 |  |
| 653 | `fc-text-size` | переменная | src/forthc.fth:592 | 5 | вход бута (хост) |
| 654 | `fc-reset` | определение `:` | src/forthc.fth:593 | 3 |  |
| 655 | `fc-append` | определение `:` | src/forthc.fth:594 | 1 |  |
| 656 | `fc\|` | определение `:` | src/forthc.fth:598 | 1 | вход бута (хост) |
| 657 | `fc-ch` | определение `:` | src/forthc.fth:599 | 5 |  |
| 658 | `fc-more?` | определение `:` | src/forthc.fth:600 | 6 |  |
| 659 | `fc-next` | определение `:` | src/forthc.fth:601 | 8 |  |
| 660 | `fc-next!` | определение `:` | src/forthc.fth:609 | 10 |  |
| 661 | `fc-is?` | определение `:` | src/forthc.fth:610 | 5 |  |
| 662 | `fc-raw` | определение `:` | src/forthc.fth:613 | 1 |  |
| 663 | `fc-string-token` | определение `:` | src/forthc.fth:614 | 1 |  |
| 664 | `fc-names-size` | переменная | src/forthc.fth:619 | 4 | вход бута (хост) |
| 665 | `fc-max-words` | переменная | src/forthc.fth:619 | 4 | вход бута (хост) |
| 666 | `fc-names` | переменная | src/forthc.fth:620 | 3 |  |
| 667 | `fc-names-used` | переменная | src/forthc.fth:620 | 5 |  |
| 668 | `fc-wt` | переменная | src/forthc.fth:621 | 5 |  |
| 669 | `fc-nwords` | переменная | src/forthc.fth:621 | 12 |  |
| 670 | `fc-wbk` | переменная | src/forthc.fth:621 | 3 |  |
| 671 | `fc-wt@` | определение `:` | src/forthc.fth:624 | 6 |  |
| 672 | `fc-proved` | данные `create` | src/forthc.fth:626 | 2 |  |
| 673 | `fc-unproved` | данные `create` | src/forthc.fth:627 | 2 |  |
| 674 | `fc-mechanisms` | определение `:` | src/forthc.fth:628 | 1 |  |
| 675 | `fc-xt` | определение `:` | src/forthc.fth:633 | 5 |  |
| 676 | `fc-xtn` | определение `:` | src/forthc.fth:635 | 2 |  |
| 677 | `fc-hash` | определение `:` | src/forthc.fth:636 | 2 |  |
| 678 | `fc-define` | определение `:` | src/forthc.fth:638 | 6 |  |
| 679 | `fc-lookup` | определение `:` | src/forthc.fth:643 | 6 |  |
| 680 | `fc-find` | определение `:` | src/forthc.fth:647 | 6 |  |
| 681 | `fc-word-of` | определение `:` | src/forthc.fth:649 | 2 |  |
| 682 | `fc-cost` | определение `:` | src/forthc.fth:657 | 1 |  |
| 683 | `fc-proved?` | определение `:` | src/forthc.fth:660 | 1 |  |
| 684 | `fc-here` | переменная | src/forthc.fth:662 | 9 |  |
| 685 | `fc-word` | переменная | src/forthc.fth:662 | 13 |  |
| 686 | `fc-uses` | переменная | src/forthc.fth:662 | 17 |  |
| 687 | `fc-rt` | переменная | src/forthc.fth:663 | 7 |  |
| 688 | `fc-rta` | переменная | src/forthc.fth:663 | 7 |  |
| 689 | `fc-ctl` | данные `create` | src/forthc.fth:664 | 1 |  |
| 690 | `fc-nctl` | переменная | src/forthc.fth:664 | 12 |  |
| 691 | `fc-cleave` | переменная | src/forthc.fth:664 | 2 |  |
| 692 | `fc-ctl@` | определение `:` | src/forthc.fth:665 | 4 |  |
| 693 | `fc-ctl+` | определение `:` | src/forthc.fth:666 | 6 |  |
| 694 | `fc-ctl-` | определение `:` | src/forthc.fth:668 | 7 |  |
| 695 | `fc-do-entry` | определение `:` | src/forthc.fth:670 | 1 |  |
| 696 | `fc-ctl-leave` | определение `:` | src/forthc.fth:672 | 1 |  |
| 697 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:673 | 1 |  |
| 698 | `fc-loop-leave` | определение `:` | src/forthc.fth:674 | 1 |  |
| 699 | `fc-align` | определение `:` | src/forthc.fth:675 | 2 |  |
| 700 | `fc-check-here` | определение `:` | src/forthc.fth:676 | 3 |  |
| 701 | `fc-define-data` | определение `:` | src/forthc.fth:677 | 2 |  |
| 702 | `fc-sat` | переменная | src/forthc.fth:678 | 3 |  |
| 703 | `fc-store-string` | определение `:` | src/forthc.fth:679 | 1 |  |
| 704 | `fc-ct` | данные `create` | src/forthc.fth:684 | 3 |  |
| 705 | `fc-nct` | переменная | src/forthc.fth:684 | 11 |  |
| 706 | `fc-ct+` | определение `:` | src/forthc.fth:685 | 24 |  |
| 707 | `fc-ct-` | определение `:` | src/forthc.fth:686 | 9 |  |
| 708 | `fc-ct2` | определение `:` | src/forthc.fth:687 | 8 |  |
| 709 | `fc-inits` | данные `create` | src/forthc.fth:688 | 2 |  |
| 710 | `fc-ninit` | переменная | src/forthc.fth:688 | 5 |  |
| 711 | `fc-init-open` | переменная | src/forthc.fth:688 | 6 |  |
| 712 | `fc-ck-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 713 | `fc-stabs-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 714 | `fc-cbk-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 715 | `fc-link-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 716 | `fc-wt-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 717 | `fc-names-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 718 | `fc-wbk-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 719 | `fc-log-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 720 | `fc-decs-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 721 | `fc-calls-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 722 | `fc-pend-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 723 | `fc-init` | определение `:` | src/forthc.fth:695 | 1 |  |
| 724 | `fc-scan-uses` | определение `:` | src/forthc.fth:709 | 1 |  |
| 725 | `fc-const-shift` | определение `:` | src/forthc.fth:716 | 2 |  |
| 726 | `fc-lit?` | определение `:` | src/forthc.fth:725 | 3 |  |
| 727 | `fc-mul-lit?` | определение `:` | src/forthc.fth:727 | 1 |  |
| 728 | `fc-shift-lit?` | определение `:` | src/forthc.fth:732 | 2 |  |
| 729 | `fc-pick-roll` | определение `:` | src/forthc.fth:735 | 2 |  |
| 730 | `fc-stx` | переменная | src/forthc.fth:744 | 3 |  |
| 731 | `fc-stlo` | переменная | src/forthc.fth:744 | 11 |  |
| 732 | `fc-sthi` | переменная | src/forthc.fth:744 | 5 |  |
| 733 | `fc-stp` | переменная | src/forthc.fth:744 | 6 |  |
| 734 | `fc-strow` | переменная | src/forthc.fth:744 | 16 |  |
| 735 | `fc-stm` | переменная | src/forthc.fth:744 | 5 |  |
| 736 | `fc-ftr` | переменная | src/forthc.fth:745 | 5 |  |
| 737 | `fc-stg` | переменная | src/forthc.fth:745 | 2 |  |
| 738 | `fc-sw0` | определение `:` | src/forthc.fth:746 | 5 |  |
| 739 | `fc-sw1` | определение `:` | src/forthc.fth:747 | 3 |  |
| 740 | `fc-sbase` | определение `:` | src/forthc.fth:748 | 4 |  |
| 741 | `fc-space-end` | определение `:` | src/forthc.fth:749 | 3 |  |
| 742 | `fc-space-store` | определение `:` | src/forthc.fth:757 | 2 |  |
| 743 | `fc-space-fetch` | определение `:` | src/forthc.fth:764 | 2 |  |
| 744 | `fc-cp` | определение `:` | src/forthc.fth:775 | 4 |  |
| 745 | `fc-copy-row` | определение `:` | src/forthc.fth:777 | 1 |  |
| 746 | `fc-close-init` | определение `:` | src/forthc.fth:780 | 2 |  |
| 747 | `fc-open-init` | определение `:` | src/forthc.fth:783 | 1 |  |
| 748 | `fc-gens` | переменная | src/forthc.fth:794 | 3 |  |
| 749 | `fc-generator` | определение `:` | src/forthc.fth:795 | 88 |  |
| 750 | `fc-literal-name` | определение `:` | src/forthc.fth:797 | 10 |  |
| 751 | `fc-words` | определение `:` | src/forthc.fth:799 | 1 |  |
| 752 | `fc-known` | определение `:` | src/forthc.fth:808 | 1 |  |
| 753 | `fc-defining?` | определение `:` | src/forthc.fth:810 | 7 |  |
| 754 | `fc-code` | определение `:` | src/forthc.fth:811 | 53 | вариант 2 |
| 755 | `fc-fold?` | определение `:` | src/forthc.fth:813 | 13 |  |
| 756 | `fc-top-only` | определение `:` | src/forthc.fth:814 | 6 |  |
| 757 | `fc-not-found` | определение `:` | src/forthc.fth:816 | 1 |  |
| 758 | `fc-word-token` | определение `:` | src/forthc.fth:818 | 2 |  |
| 759 | `fc-token` | определение `:` | src/forthc.fth:823 | 2 |  |
| 760 | `fc-synonym-of` | определение `:` | src/forthc.fth:824 | 2 |  |
| 761 | `fc-synonym` | определение `:` | src/forthc.fth:825 | 10 |  |
| 762 | `fc-sy` | переменная | src/forthc.fth:828 | 2 |  |
| 763 | `fc-synonym?` | определение `:` | src/forthc.fth:829 | 1 |  |
| 764 | `fc-poke` | определение `:` | src/forthc.fth:832 | 2 |  |
| 765 | `fc-concept-record` | определение `:` | src/forthc.fth:835 | 1 |  |
| 766 | `fc-eval` | определение `:` | src/forthc.fth:840 | 77 |  |
| 767 | `fc-concepts` | определение `:` | src/forthc.fth:844 | 1 |  |
| 768 | `fc-nhost` | переменная | src/forthc.fth:851 | 5 |  |
| 769 | `fc-platform` | определение `:` | src/forthc.fth:852 | 1 |  |
| 770 | `fc-time-price` | определение `:` | src/forthc.fth:877 | 1 |  |
| 771 | `fc-replacement` | определение `:` | src/forthc.fth:887 | 1 |  |
| 772 | `fc-library` | определение `:` | src/forthc.fth:902 | 1 |  |
| 773 | `fc-forbidden` | определение `:` | src/forthc.fth:931 | 2 |  |
| 774 | `fc-num` | определение `:` | src/forthc.fth:932 | 1 |  |
| 775 | `fc-long-host` | определение `:` | src/forthc.fth:934 | 1 |  |
| 776 | `fc-ltpl` | переменная | src/forthc.fth:951 | 2 |  |
| 777 | `fc-lpos` | данные `create` | src/forthc.fth:951 | 3 |  |
| 778 | `fc-llo` | переменная | src/forthc.fth:951 | 2 |  |
| 779 | `fc-lhi` | переменная | src/forthc.fth:951 | 2 |  |
| 780 | `fc-lcn` | переменная | src/forthc.fth:951 | 4 |  |
| 781 | `fc-ldir` | переменная | src/forthc.fth:951 | 3 |  |
| 782 | `fc-lp0` | переменная | src/forthc.fth:952 | 4 |  |
| 783 | `fc-lp1` | переменная | src/forthc.fth:952 | 4 |  |
| 784 | `fc-lpl` | переменная | src/forthc.fth:952 | 6 |  |
| 785 | `fc-ltemplate` | определение `:` | src/forthc.fth:953 | 1 |  |
| 786 | `fc-lhead` | определение `:` | src/forthc.fth:957 | 2 |  |
| 787 | `fc-lsend` | определение `:` | src/forthc.fth:962 | 2 |  |
| 788 | `fc-lpop` | определение `:` | src/forthc.fth:963 | 2 |  |
| 789 | `fc-lput` | определение `:` | src/forthc.fth:965 | 1 |  |
| 790 | `fc-lget` | определение `:` | src/forthc.fth:975 | 1 |  |
| 791 | `fc-long-kernel` | определение `:` | src/forthc.fth:981 | 1 |  |
| 792 | `fc-long` | определение `:` | src/forthc.fth:991 | 1 |  |
| 793 | `fc-helpers-cost` | определение `:` | src/forthc.fth:996 | 1 |  |
| 794 | `fc-price-word` | определение `:` | src/forthc.fth:1003 | 1 |  |
| 795 | `fc-compile` | определение `:` | src/forthc.fth:1006 | 1 |  |
| 796 | `fc-go` | определение `:` | src/forthc.fth:1022 | 3 | вход бута (хост) |
| 797 | `gen+` | определение `:` | src/primitives.fth:4 | 5 |  |
| 798 | `gen-` | определение `:` | src/primitives.fth:5 | 2 |  |
| 799 | `gen-and` | определение `:` | src/primitives.fth:6 | 2 |  |
| 800 | `gen-or` | определение `:` | src/primitives.fth:7 | 2 |  |
| 801 | `gen-xor` | определение `:` | src/primitives.fth:8 | 2 |  |
| 802 | `gen=` | определение `:` | src/primitives.fth:9 | 2 |  |
| 803 | `gen<` | определение `:` | src/primitives.fth:10 | 2 |  |
| 804 | `gen-u<` | определение `:` | src/primitives.fth:11 | 2 |  |
| 805 | `gen-lshift` | определение `:` | src/primitives.fth:12 | 2 |  |
| 806 | `gen-rshift` | определение `:` | src/primitives.fth:14 | 2 |  |
| 807 | `gen-0=` | определение `:` | src/primitives.fth:16 | 2 |  |
| 808 | `gen-cells` | определение `:` | src/primitives.fth:17 | 2 |  |
| 809 | `gen-2*` | определение `:` | src/primitives.fth:18 | 2 |  |
| 810 | `gen-1+` | определение `:` | src/primitives.fth:19 | 2 |  |
| 811 | `gen-1-` | определение `:` | src/primitives.fth:20 | 2 |  |
| 812 | `gen-cell+` | определение `:` | src/primitives.fth:21 | 2 |  |
| 813 | `gen*` | определение `:` | src/primitives.fth:22 | 2 |  |
| 814 | `gen/` | определение `:` | src/primitives.fth:25 | 2 |  |
| 815 | `gen-mod` | определение `:` | src/primitives.fth:26 | 2 |  |
| 816 | `gen/mod` | определение `:` | src/primitives.fth:27 | 2 |  |
| 817 | `gen-dup` | определение `:` | src/primitives.fth:28 | 2 |  |
| 818 | `gen-drop` | определение `:` | src/primitives.fth:29 | 2 |  |
| 819 | `gen-swap` | определение `:` | src/primitives.fth:30 | 2 |  |
| 820 | `gen-over` | определение `:` | src/primitives.fth:31 | 2 |  |
| 821 | `gen-rot` | определение `:` | src/primitives.fth:32 | 2 |  |
| 822 | `gen-pick` | определение `:` | src/primitives.fth:33 | 2 |  |
| 823 | `gen-roll` | определение `:` | src/primitives.fth:34 | 2 |  |
| 824 | `gen->r` | определение `:` | src/primitives.fth:35 | 2 |  |
| 825 | `gen-r>` | определение `:` | src/primitives.fth:36 | 2 |  |
| 826 | `gen-r@` | определение `:` | src/primitives.fth:37 | 4 |  |
| 827 | `gen-j` | определение `:` | src/primitives.fth:38 | 2 |  |
| 828 | `gen-@` | определение `:` | src/primitives.fth:39 | 2 |  |
| 829 | `gen-!` | определение `:` | src/primitives.fth:41 | 2 |  |
| 830 | `gen-c@` | определение `:` | src/primitives.fth:42 | 2 |  |
| 831 | `gen-c!` | определение `:` | src/primitives.fth:44 | 2 |  |
| 832 | `gen-emit` | определение `:` | src/primitives.fth:45 | 2 |  |
| 833 | `gen-key` | определение `:` | src/primitives.fth:48 | 2 |  |
| 834 | `gen-if` | определение `:` | src/primitives.fth:50 | 2 |  |
| 835 | `gen-else` | определение `:` | src/primitives.fth:51 | 2 |  |
| 836 | `gen-then` | определение `:` | src/primitives.fth:53 | 2 |  |
| 837 | `gen-begin` | определение `:` | src/primitives.fth:57 | 2 |  |
| 838 | `gen-until` | определение `:` | src/primitives.fth:58 | 2 |  |
| 839 | `gen-while` | определение `:` | src/primitives.fth:60 | 2 |  |
| 840 | `gen-repeat` | определение `:` | src/primitives.fth:61 | 2 |  |
| 841 | `gen-again` | определение `:` | src/primitives.fth:62 | 2 |  |
| 842 | `gen-do` | определение `:` | src/primitives.fth:63 | 2 |  |
| 843 | `fc-di` | переменная | src/primitives.fth:66 | 3 |  |
| 844 | `fc-dl` | переменная | src/primitives.fth:66 | 3 |  |
| 845 | `gen-?do` | определение `:` | src/primitives.fth:67 | 2 |  |
| 846 | `fc-lv` | переменная | src/primitives.fth:73 | 2 |  |
| 847 | `gen-loop` | определение `:` | src/primitives.fth:74 | 2 |  |
| 848 | `gen-leave` | определение `:` | src/primitives.fth:83 | 2 |  |
| 849 | `gen-unloop` | определение `:` | src/primitives.fth:86 | 2 |  |
| 850 | `gen-exit` | определение `:` | src/primitives.fth:87 | 2 |  |
| 851 | `gen-bye` | определение `:` | src/primitives.fth:90 | 2 |  |
| 852 | `gen-recurse` | определение `:` | src/primitives.fth:92 | 2 |  |
| 853 | `gen-tick` | определение `:` | src/primitives.fth:93 | 2 |  |
| 854 | `gen-call` | определение `:` | src/primitives.fth:99 | 3 |  |
| 855 | `gen-space!` | определение `:` | src/primitives.fth:100 | 2 |  |
| 856 | `gen-spacec!` | определение `:` | src/primitives.fth:101 | 2 |  |
| 857 | `gen-space@` | определение `:` | src/primitives.fth:102 | 2 |  |
| 858 | `gen-spacec@` | определение `:` | src/primitives.fth:103 | 2 |  |
| 859 | `gen-execute` | определение `:` | src/primitives.fth:104 | 2 |  |
| 860 | `fc-entry-cell` | определение `:` | src/primitives.fth:110 | 1 |  |
| 861 | `fc-concept` | определение `:` | src/primitives.fth:112 | 1 |  |
| 862 | `gen-colon` | определение `:` | src/primitives.fth:119 | 2 |  |
| 863 | `gen-semicolon` | определение `:` | src/primitives.fth:125 | 2 |  |
| 864 | `gen-variable` | определение `:` | src/primitives.fth:128 | 2 |  |
| 865 | `gen-create` | определение `:` | src/primitives.fth:129 | 2 |  |
| 866 | `gen-allot` | определение `:` | src/primitives.fth:130 | 2 |  |
| 867 | `gen-constant` | определение `:` | src/primitives.fth:131 | 2 |  |
| 868 | `gen-decimal` | определение `:` | src/primitives.fth:132 | 2 |  |
| 869 | `gen-kernel-layout` | определение `:` | src/primitives.fth:133 | 2 |  |
| 870 | `gen-backslash` | определение `:` | src/primitives.fth:134 | 2 |  |
| 871 | `gen-paren` | определение `:` | src/primitives.fth:136 | 4 |  |
| 872 | `gen-char` | определение `:` | src/primitives.fth:137 | 2 |  |
| 873 | `gen-string` | определение `:` | src/primitives.fth:138 | 2 |  |
| 874 | `fc-digit@` | определение `:` | src/primitives.fth:141 | 1 |  |
| 875 | `gen-literal` | определение `:` | src/primitives.fth:143 | 2 |  |
| 876 | `fc-known-xt` | определение `:` | src/primitives.fth:150 | 2 |  |
| 877 | `gen-cost` | определение `:` | src/primitives.fth:151 | 2 |  |
| 878 | `gen-proved?` | определение `:` | src/primitives.fth:153 | 2 |  |
| 879 | `gen-library` | определение `:` | src/primitives.fth:154 | 16 |  |
| 880 | `gen-price` | определение `:` | src/primitives.fth:155 | 2 |  |
| 881 | `fc-cpos` | переменная | src/primitives.fth:160 | 4 |  |
| 882 | `fc-hn` | переменная | src/primitives.fth:160 | 2 |  |
| 883 | `fc-cdepth` | переменная | src/primitives.fth:160 | 4 |  |
| 884 | `fc-hname` | данные `create` | src/primitives.fth:160 | 2 |  |
| 885 | `fc-hb` | определение `:` | src/primitives.fth:161 | 3 |  |
| 886 | `fc-c,` | определение `:` | src/primitives.fth:162 | 17 |  |
| 887 | `fc-c1` | определение `:` | src/primitives.fth:163 | 8 |  |
| 888 | `fc-c-gen` | определение `:` | src/primitives.fth:164 | 1 |  |
| 889 | `fc-c-body` | определение `:` | src/primitives.fth:168 | 1 |  |
| 890 | `gen-host` | определение `:` | src/primitives.fth:177 | 2 |  |
| 891 | `fc-name2` | определение `:` | src/primitives.fth:194 | 1 |  |
| 892 | `fc-generators` | определение `:` | src/primitives.fth:197 | 1 |  |
| 893 | `+` | генератор | src/primitives.fth:198 | 588 | слово компилятора `gen+` |
| 894 | `-` | генератор | src/primitives.fth:198 | 68 | слово компилятора `gen-` |
| 895 | `*` | генератор | src/primitives.fth:199 | 80 | слово компилятора `gen*` |
| 896 | `/` | генератор | src/primitives.fth:199 | 4 | слово компилятора `gen/` |
| 897 | `mod` | генератор | src/primitives.fth:200 | 2 | слово компилятора `gen-mod` |
| 898 | `and` | генератор | src/primitives.fth:201 | 125 | слово компилятора `gen-and` |
| 899 | `or` | генератор | src/primitives.fth:201 | 44 | слово компилятора `gen-or` |
| 900 | `xor` | генератор | src/primitives.fth:202 | 5 | слово компилятора `gen-xor` |
| 901 | `lshift` | генератор | src/primitives.fth:202 | 101 | слово компилятора `gen-lshift` |
| 902 | `rshift` | генератор | src/primitives.fth:203 | 66 | слово компилятора `gen-rshift` |
| 903 | `=` | генератор | src/primitives.fth:203 | 89 | слово компилятора `gen=` |
| 904 | `<` | генератор | src/primitives.fth:204 | 24 | слово компилятора `gen<` |
| 905 | `u<` | генератор | src/primitives.fth:204 | 28 | слово компилятора `gen-u<` |
| 906 | `0=` | генератор | src/primitives.fth:205 | 106 | слово компилятора `gen-0=` |
| 907 | `2*` | генератор | src/primitives.fth:205 | 29 | слово компилятора `gen-2*` |
| 908 | `1+` | генератор | src/primitives.fth:206 | 45 | слово компилятора `gen-1+` |
| 909 | `1-` | генератор | src/primitives.fth:206 | 58 | слово компилятора `gen-1-` |
| 910 | `cells` | генератор | src/primitives.fth:207 | 280 | слово компилятора `gen-cells` |
| 911 | `cell+` | генератор | src/primitives.fth:207 | 56 | слово компилятора `gen-cell+` |
| 912 | `dup` | генератор | src/primitives.fth:208 | 305 | слово компилятора `gen-dup` |
| 913 | `drop` | генератор | src/primitives.fth:208 | 206 | слово компилятора `gen-drop` |
| 914 | `swap` | генератор | src/primitives.fth:209 | 140 | слово компилятора `gen-swap` |
| 915 | `over` | генератор | src/primitives.fth:209 | 86 | слово компилятора `gen-over` |
| 916 | `rot` | генератор | src/primitives.fth:210 | 39 | слово компилятора `gen-rot` |
| 917 | `pick` | генератор | src/primitives.fth:210 | 45 | слово компилятора `gen-pick` |
| 918 | `roll` | генератор | src/primitives.fth:211 | 7 | слово компилятора `gen-roll` |
| 919 | `>r` | генератор | src/primitives.fth:211 | 107 | слово компилятора `gen->r` |
| 920 | `r>` | генератор | src/primitives.fth:212 | 111 | слово компилятора `gen-r>` |
| 921 | `r@` | генератор | src/primitives.fth:212 | 108 | слово компилятора `gen-r@` |
| 922 | `i` | генератор | src/primitives.fth:213 | 178 | слово компилятора `gen-r@` |
| 923 | `j` | генератор | src/primitives.fth:213 | 12 | слово компилятора `gen-j` |
| 924 | `@` | генератор | src/primitives.fth:214 | 1299 | слово компилятора `gen-@` |
| 925 | `!` | генератор | src/primitives.fth:214 | 678 | слово компилятора `gen-!` |
| 926 | `c@` | генератор | src/primitives.fth:215 | 23 | слово компилятора `gen-c@` |
| 927 | `c!` | генератор | src/primitives.fth:215 | 18 | слово компилятора `gen-c!` |
| 928 | `space!` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-space!` |
| 929 | `spacec!` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-spacec!` |
| 930 | `space@` | генератор | src/primitives.fth:217 | 1 | слово компилятора `gen-space@` |
| 931 | `emit` | генератор | src/primitives.fth:218 | 4 | слово компилятора `gen-emit` |
| 932 | `key` | генератор | src/primitives.fth:218 | 1 | слово компилятора `gen-key` |
| 933 | `if` | генератор | src/primitives.fth:219 | 307 | слово компилятора `gen-if` |
| 934 | `else` | генератор | src/primitives.fth:219 | 83 | слово компилятора `gen-else` |
| 935 | `then` | генератор | src/primitives.fth:220 | 307 | слово компилятора `gen-then` |
| 936 | `begin` | генератор | src/primitives.fth:220 | 25 | слово компилятора `gen-begin` |
| 937 | `until` | генератор | src/primitives.fth:221 | 2 | слово компилятора `gen-until` |
| 938 | `while` | генератор | src/primitives.fth:221 | 22 | слово компилятора `gen-while` |
| 939 | `repeat` | генератор | src/primitives.fth:222 | 22 | слово компилятора `gen-repeat` |
| 940 | `again` | генератор | src/primitives.fth:222 | 1 | слово компилятора `gen-again` |
| 941 | `do` | генератор | src/primitives.fth:223 | 35 | слово компилятора `gen-do` |
| 942 | `?do` | генератор | src/primitives.fth:223 | 59 | слово компилятора `gen-?do` |
| 943 | `loop` | генератор | src/primitives.fth:224 | 94 | слово компилятора `gen-loop` |
| 944 | `leave` | генератор | src/primitives.fth:224 | 1 | слово компилятора `gen-leave` |
| 945 | `unloop` | генератор | src/primitives.fth:225 | 7 | слово компилятора `gen-unloop` |
| 946 | `exit` | генератор | src/primitives.fth:225 | 83 | слово компилятора `gen-exit` |
| 947 | `bye` | генератор | src/primitives.fth:226 | 1 | слово компилятора `gen-bye` |
| 948 | `recurse` | генератор | src/primitives.fth:227 | 2 | слово компилятора `gen-recurse` |
| 949 | `execute` | генератор | src/primitives.fth:227 | 10 | слово компилятора `gen-execute` |
| 950 | `[']` | генератор | src/primitives.fth:228 | 119 | слово компилятора `gen-tick` |
| 951 | `:` | генератор | src/primitives.fth:229 | 499 | слово компилятора `gen-colon` |
| 952 | `;` | генератор | src/primitives.fth:229 | 499 | слово компилятора `gen-semicolon` |
| 953 | `variable` | генератор | src/primitives.fth:230 | 330 | слово компилятора `gen-variable` |
| 954 | `create` | генератор | src/primitives.fth:230 | 63 | слово компилятора `gen-create` |
| 955 | `allot` | генератор | src/primitives.fth:231 | 63 | слово компилятора `gen-allot` |
| 956 | `constant` | генератор | src/primitives.fth:231 | 29 | слово компилятора `gen-constant` |
| 957 | `decimal` | генератор | src/primitives.fth:232 | 3 | слово компилятора `gen-decimal` |
| 958 | `kernel-layout` | генератор | src/primitives.fth:232 | 1 | слово компилятора `gen-kernel-layout` |
| 959 | `\` | генератор | src/primitives.fth:233 | 176 | слово компилятора `gen-backslash` |
| 960 | `(` | генератор | src/primitives.fth:233 | 479 | слово компилятора `gen-paren` |
| 961 | `[char]` | генератор | src/primitives.fth:233 | 8 | слово компилятора `gen-char` |
| 962 | `s"` | генератор | src/primitives.fth:234 | 224 | слово компилятора `gen-string` |
| 963 | `literal` | генератор | src/primitives.fth:235 | 509 | слово компилятора `gen-literal` |
| 964 | `0` | цифра (литерал) | src/primitives.fth:243 | 558 | значение 0 |
| 965 | `1` | цифра (литерал) | src/primitives.fth:243 | 481 | значение 1 |
| 966 | `2` | цифра (литерал) | src/primitives.fth:243 | 468 | значение 2 |
| 967 | `3` | цифра (литерал) | src/primitives.fth:243 | 307 | значение 3 |
| 968 | `4` | цифра (литерал) | src/primitives.fth:244 | 242 | значение 4 |
| 969 | `5` | цифра (литерал) | src/primitives.fth:244 | 112 | значение 5 |
| 970 | `6` | цифра (литерал) | src/primitives.fth:244 | 169 | значение 6 |
| 971 | `7` | цифра (литерал) | src/primitives.fth:244 | 75 | значение 7 |
| 972 | `8` | цифра (литерал) | src/primitives.fth:245 | 163 | значение 8 |
| 973 | `9` | цифра (литерал) | src/primitives.fth:245 | 43 | значение 9 |
| 974 | `fc-install-generators` | определение `:` | src/primitives.fth:246 | 1 |  |
| 975 | `fc-read` | определение `:` | src/main.fth:3 | 2 |  |
| 976 | `fc-sizes` | определение `:` | src/main.fth:8 | 2 |  |
| 977 | `kn-at` | переменная | src/kernel.fth:7 | 5 |  |
| 978 | `kn-put` | определение `:` | src/kernel.fth:8 | 1 |  |
| 979 | `kn-order` | определение `:` | src/kernel.fth:16 | 1 |  |
| 980 | `kn-get` | определение `:` | src/kernel.fth:18 | 1 |  |
| 981 | `kn-compile` | определение `:` | src/kernel.fth:19 | 1 |  |
| 982 | `main` | определение `:` | src/kernel.fth:25 | 1 | вариант 2 |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 99.

## Определены, но не использованы

Слов: 34. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

| Слово | Вид | Файл:строка |
|---|---|---|
| `lay-out` | определение `:` | src/backend.fth:118 |
| `lay-cz` | переменная | src/compute.fth:168 |
| `lay-cf` | переменная | src/compute.fth:168 |
| `lay-compare` | определение `:` | src/compute.fth:169 |
| `lay-fc` | переменная | src/compute.fth:215 |
| `lay-ff` | переменная | src/compute.fth:215 |
| `lay-flag-exit` | определение `:` | src/compute.fth:216 |
| `lay-exit-layers` | определение `:` | src/compute.fth:224 |
| `lay-ce` | переменная | src/compute.fth:228 |
| `lay-cl` | переменная | src/compute.fth:228 |
| `lay-ch` | переменная | src/compute.fth:228 |
| `lay-call-rows` | определение `:` | src/compute.fth:229 |
| `lay-halt-begin` | определение `:` | src/compute.fth:233 |
| `lay-halt-region` | определение `:` | src/compute.fth:234 |
| `lay-halt-end` | определение `:` | src/compute.fth:235 |
| `lay-stub-on` | определение `:` | src/compute.fth:236 |
| `lay-stub` | определение `:` | src/compute.fth:237 |
| `fc-depth` | определение `:` | src/forthc.fth:806 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:807 |
| `/mod` | генератор | src/primitives.fth:200 |
| `spacec@` | генератор | src/primitives.fth:217 |
| `cost` | генератор | src/primitives.fth:236 |
| `price` | генератор | src/primitives.fth:236 |
| `proved?` | генератор | src/primitives.fth:237 |
| `check-table` | генератор | src/primitives.fth:238 |
| `accuracy` | генератор | src/primitives.fth:238 |
| `replace` | генератор | src/primitives.fth:239 |
| `long!` | генератор | src/primitives.fth:240 |
| `long@` | генератор | src/primitives.fth:240 |
| `host` | генератор | src/primitives.fth:241 |
| `time` | генератор | src/primitives.fth:241 |
| `platform` | генератор | src/primitives.fth:242 |
| `platform-of` | генератор | src/primitives.fth:242 |
| `main` (вариант 1) | определение `:` | src/main.fth:11 |

## Слова, которые при буте исполняет хост

Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки `backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках 82; все они определены в определении языка (генератором в `primitives.fth` или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: `!` `*` `+` `+!` `-` `-rot` `/` `/string` `0<` `0<>` `0=` `0>` `1+` `1-` `2!` `2*` `2@` `2drop` `2dup` `2over` `2swap` `<` `<>` `=` `>` `>in` `>r` `?do` `?dup` `@` `again` `and` `begin` `bye` `c!` `c@` `cell+` `cells` `cmove` `cmove>` `compare` `decimal` `do` `drop` `dup` `else` `emit` `execute` `exit` `fill` `i` `if` `invert` `j` `leave` `loop` `lshift` `max` `min` `mod` `negate` `nip` `or` `over` `pick` `r>` `r@` `repeat` `roll` `rot` `rshift` `source` `swap` `then` `tuck` `type` `u<` `u>` `unloop` `until` `while` `xor`.

Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро читает каналом `key`), `source` и `>in` — слова только этого пути.
