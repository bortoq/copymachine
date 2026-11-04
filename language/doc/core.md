# Ядро языка (14.8)

Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 995** (определение `:` — 487, переменная — 329, генератор — 71, данные `create` — 63, константа — 29, цифра (литерал) — 10, основание — 6).

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
| 4 | `2dup` | определение `:` | src/prelude.fth:7 | 14 |  |
| 5 | `2drop` | определение `:` | src/prelude.fth:8 | 27 |  |
| 6 | `2swap` | определение `:` | src/prelude.fth:9 | 6 |  |
| 7 | `2over` | определение `:` | src/prelude.fth:10 | 2 |  |
| 8 | `?dup` | определение `:` | src/prelude.fth:11 | 19 |  |
| 9 | `negate` | определение `:` | src/prelude.fth:12 | 5 |  |
| 10 | `invert` | определение `:` | src/prelude.fth:13 | 2 |  |
| 11 | `>` | определение `:` | src/prelude.fth:14 | 9 |  |
| 12 | `u>` | определение `:` | src/prelude.fth:15 | 9 |  |
| 13 | `<>` | определение `:` | src/prelude.fth:16 | 11 |  |
| 14 | `0<` | определение `:` | src/prelude.fth:17 | 5 |  |
| 15 | `0>` | определение `:` | src/prelude.fth:18 | 3 |  |
| 16 | `0<>` | определение `:` | src/prelude.fth:19 | 4 |  |
| 17 | `max` | определение `:` | src/prelude.fth:20 | 20 |  |
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
| 37 | `lay-slots` | переменная | src/backend.fth:15 | 16 |  |
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
| 56 | `lay-rec` | константа | src/backend.fth:35 | 12 |  |
| 57 | `lay-hdr` | константа | src/backend.fth:35 | 3 |  |
| 58 | `lay-cap` | константа | src/backend.fth:35 | 5 |  |
| 59 | `lay-req` | определение `:` | src/backend.fth:36 | 9 |  |
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
| 93 | `lay-field` | определение `:` | src/backend.fth:115 | 50 |  |
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
| 134 | `dj-reader` | переменная | src/backend.fth:213 | 3 |  |
| 135 | `dj-bad-cell` | переменная | src/backend.fth:213 | 1 |  |
| 136 | `dj-bad-rule` | переменная | src/backend.fth:213 | 4 |  |
| 137 | `dj-bsh` | переменная | src/backend.fth:214 | 3 |  |
| 138 | `dj-csh` | переменная | src/backend.fth:214 | 9 |  |
| 139 | `dj-ssh` | переменная | src/backend.fth:214 | 2 |  |
| 140 | `dj-fsh` | переменная | src/backend.fth:214 | 2 |  |
| 141 | `dj-first` | переменная | src/backend.fth:215 | 2 |  |
| 142 | `dj-end` | переменная | src/backend.fth:215 | 2 |  |
| 143 | `dj-pa` | переменная | src/backend.fth:215 | 3 |  |
| 144 | `dj-cb` | переменная | src/backend.fth:215 | 8 |  |
| 145 | `dj-vdl` | переменная | src/backend.fth:216 | 25 |  |
| 146 | `dj-vdh` | переменная | src/backend.fth:216 | 19 |  |
| 147 | `dj-vsl` | переменная | src/backend.fth:216 | 19 |  |
| 148 | `dj-vsh` | переменная | src/backend.fth:216 | 17 |  |
| 149 | `dj-tc` | переменная | src/backend.fth:217 | 6 |  |
| 150 | `dj-ts` | переменная | src/backend.fth:217 | 6 |  |
| 151 | `dj-tf` | переменная | src/backend.fth:217 | 11 |  |
| 152 | `dj-tb` | переменная | src/backend.fth:217 | 2 |  |
| 153 | `dj-tn` | переменная | src/backend.fth:217 | 2 |  |
| 154 | `dj-tk` | переменная | src/backend.fth:217 | 9 |  |
| 155 | `dj-vt` | переменная | src/backend.fth:217 | 6 |  |
| 156 | `dj-blk` | переменная | src/backend.fth:218 | 5 |  |
| 157 | `dj-hb` | переменная | src/backend.fth:218 | 6 |  |
| 158 | `dj-he` | переменная | src/backend.fth:218 | 5 |  |
| 159 | `dj-hw` | переменная | src/backend.fth:218 | 3 |  |
| 160 | `dj-hz` | переменная | src/backend.fth:218 | 4 |  |
| 161 | `dj-cur` | переменная | src/backend.fth:219 | 4 |  |
| 162 | `dj-hc` | переменная | src/backend.fth:219 | 5 |  |
| 163 | `dj-wb` | переменная | src/backend.fth:219 | 2 |  |
| 164 | `dj-we` | переменная | src/backend.fth:219 | 2 |  |
| 165 | `dj-pr` | данные `create` | src/backend.fth:220 | 2 |  |
| 166 | `dj-tr` | данные `create` | src/backend.fth:220 | 2 |  |
| 167 | `dj-narrow` | константа | src/backend.fth:221 | 3 |  |
| 168 | `dj-seen` | данные `create` | src/backend.fth:222 | 2 |  |
| 169 | `dj-nseen` | переменная | src/backend.fth:222 | 6 |  |
| 170 | `dj-get` | определение `:` | src/backend.fth:223 | 12 |  |
| 171 | `dj-fail` | определение `:` | src/backend.fth:224 | 11 |  |
| 172 | `dj-blk?` | определение `:` | src/backend.fth:225 | 10 |  |
| 173 | `dj-in?` | определение `:` | src/backend.fth:226 | 4 |  |
| 174 | `dj-meets?` | определение `:` | src/backend.fth:229 | 4 |  |
| 175 | `dj-row!` | определение `:` | src/backend.fth:231 | 2 |  |
| 176 | `dj-row@` | определение `:` | src/backend.fth:233 | 2 |  |
| 177 | `dj-nop?` | определение `:` | src/backend.fth:235 | 4 |  |
| 178 | `dj-load` | определение `:` | src/backend.fth:236 | 1 |  |
| 179 | `dj-sys?` | определение `:` | src/backend.fth:244 | 1 |  |
| 180 | `dj-chain?` | определение `:` | src/backend.fth:246 | 1 |  |
| 181 | `dj-head?` | определение `:` | src/backend.fth:252 | 1 |  |
| 182 | `dj-req-ok?` | определение `:` | src/backend.fth:255 | 1 |  |
| 183 | `dj-row-ok?` | определение `:` | src/backend.fth:261 | 1 |  |
| 184 | `dj-in-blk?` | определение `:` | src/backend.fth:279 | 2 |  |
| 185 | `dj-touches?` | определение `:` | src/backend.fth:283 | 1 |  |
| 186 | `dj-seen?` | определение `:` | src/backend.fth:284 | 1 |  |
| 187 | `dj-seen!` | определение `:` | src/backend.fth:289 | 1 |  |
| 188 | `dj-field` | определение `:` | src/backend.fth:293 | 4 |  |
| 189 | `dj-dest-ok?` | определение `:` | src/backend.fth:295 | 1 |  |
| 190 | `dj-reach` | определение `:` | src/backend.fth:300 | 2 |  |
| 191 | `dj-wide` | определение `:` | src/backend.fth:308 | 1 |  |
| 192 | `dj-near` | определение `:` | src/backend.fth:318 | 1 |  |
| 193 | `dj-patch` | определение `:` | src/backend.fth:321 | 1 |  |
| 194 | `dj-nn` | переменная | src/backend.fth:332 | 4 |  |
| 195 | `dj-lo` | переменная | src/backend.fth:332 | 2 |  |
| 196 | `dj-hi` | переменная | src/backend.fth:332 | 2 |  |
| 197 | `dj-scan` | определение `:` | src/backend.fth:333 | 1 |  |
| 198 | `dj-rows` | определение `:` | src/backend.fth:342 | 1 |  |
| 199 | `dj-prove` | определение `:` | src/backend.fth:349 | 3 |  |
| 200 | `lay-t1` | переменная | src/compute.fth:7 | 25 |  |
| 201 | `lay-t2` | переменная | src/compute.fth:7 | 13 |  |
| 202 | `lay-t3` | переменная | src/compute.fth:7 | 7 |  |
| 203 | `lay-t4` | переменная | src/compute.fth:7 | 4 |  |
| 204 | `lay-t5` | переменная | src/compute.fth:7 | 8 |  |
| 205 | `lay-lo` | переменная | src/compute.fth:8 | 5 |  |
| 206 | `lay-hi` | переменная | src/compute.fth:8 | 2 |  |
| 207 | `lay-l0` | переменная | src/compute.fth:9 | 21 |  |
| 208 | `lay-l1` | переменная | src/compute.fth:9 | 13 | вариант 2 |
| 209 | `lay-l2` | переменная | src/compute.fth:9 | 8 | вариант 2 |
| 210 | `lay-l3` | переменная | src/compute.fth:9 | 7 |  |
| 211 | `lay-l4` | переменная | src/compute.fth:9 | 7 |  |
| 212 | `lay-l5` | переменная | src/compute.fth:9 | 6 |  |
| 213 | `lay-work` | определение `:` | src/compute.fth:10 | 3 |  |
| 214 | `lay-cell-bit` | определение `:` | src/compute.fth:11 | 3 |  |
| 215 | `lay-link-slot` | определение `:` | src/compute.fth:12 | 6 |  |
| 216 | `lay-item-cells` | константа | src/compute.fth:13 | 1 |  |
| 217 | `lay-max-items` | константа | src/compute.fth:13 | 2 |  |
| 218 | `lay-items` | данные `create` | src/compute.fth:14 | 1 |  |
| 219 | `lay-nitems` | переменная | src/compute.fth:15 | 8 |  |
| 220 | `lay-item@` | определение `:` | src/compute.fth:16 | 6 |  |
| 221 | `lay-lookups-begin` | определение `:` | src/compute.fth:17 | 12 |  |
| 222 | `lay-item` | определение `:` | src/compute.fth:18 | 11 |  |
| 223 | `lay-seg` | определение `:` | src/compute.fth:23 | 17 |  |
| 224 | `lay-sl` | данные `create` | src/compute.fth:29 | 2 |  |
| 225 | `lay-sh` | данные `create` | src/compute.fth:29 | 2 |  |
| 226 | `lay-read-layer` | данные `create` | src/compute.fth:30 | 2 |  |
| 227 | `lay-read-slot` | данные `create` | src/compute.fth:30 | 2 |  |
| 228 | `lay-used` | данные `create` | src/compute.fth:31 | 2 |  |
| 229 | `lay-nused` | переменная | src/compute.fth:31 | 5 |  |
| 230 | `lay-rl` | переменная | src/compute.fth:31 | 6 |  |
| 231 | `lay-pk` | переменная | src/compute.fth:31 | 4 |  |
| 232 | `lay-pkl` | переменная | src/compute.fth:31 | 4 |  |
| 233 | `lay-npatches` | определение `:` | src/compute.fth:32 | 1 |  |
| 234 | `lay-used?` | определение `:` | src/compute.fth:33 | 1 |  |
| 235 | `lay-place-reads` | определение `:` | src/compute.fth:35 | 1 |  |
| 236 | `lay-patch` | определение `:` | src/compute.fth:47 | 1 |  |
| 237 | `lay-lookups` | определение `:` | src/compute.fth:56 | 12 |  |
| 238 | `lay-al` | данные `create` | src/compute.fth:62 | 2 |  |
| 239 | `lay-ar` | данные `create` | src/compute.fth:62 | 2 |  |
| 240 | `lay-ax` | переменная | src/compute.fth:63 | 4 |  |
| 241 | `lay-aa` | переменная | src/compute.fth:63 | 2 |  |
| 242 | `lay-ab` | переменная | src/compute.fth:63 | 2 |  |
| 243 | `lay-atab` | переменная | src/compute.fth:63 | 2 |  |
| 244 | `lay-acarry` | переменная | src/compute.fth:63 | 2 |  |
| 245 | `lay-al@` | определение `:` | src/compute.fth:64 | 8 |  |
| 246 | `lay-rd` | определение `:` | src/compute.fth:65 | 3 |  |
| 247 | `lay-adder-patch` | определение `:` | src/compute.fth:66 | 4 |  |
| 248 | `lay-adder` | определение `:` | src/compute.fth:71 | 6 |  |
| 249 | `lay-dsrc` | переменная | src/compute.fth:87 | 3 |  |
| 250 | `lay-dk` | переменная | src/compute.fth:87 | 5 |  |
| 251 | `lay-dg` | переменная | src/compute.fth:87 | 3 |  |
| 252 | `lay-dp` | переменная | src/compute.fth:87 | 3 |  |
| 253 | `lay-dx` | переменная | src/compute.fth:87 | 4 |  |
| 254 | `lay-decide` | определение `:` | src/compute.fth:88 | 2 |  |
| 255 | `lay-table-at` | переменная | src/compute.fth:95 | 4 |  |
| 256 | `lay-table-limit` | переменная | src/compute.fth:95 | 2 |  |
| 257 | `lay-tbuf` | переменная | src/compute.fth:95 | 6 |  |
| 258 | `lay-tx` | переменная | src/compute.fth:96 | 5 |  |
| 259 | `lay-tbits` | переменная | src/compute.fth:96 | 4 |  |
| 260 | `lay-ts` | переменная | src/compute.fth:96 | 6 |  |
| 261 | `lay-tsize` | переменная | src/compute.fth:96 | 6 |  |
| 262 | `lay-tbase` | переменная | src/compute.fth:96 | 4 |  |
| 263 | `lay-tper` | переменная | src/compute.fth:96 | 3 |  |
| 264 | `lay-tables` | определение `:` | src/compute.fth:97 | 2 |  |
| 265 | `lay-table-mem` | данные `create` | src/compute.fth:99 | 1 |  |
| 266 | `lay-table-area` | определение `:` | src/compute.fth:100 | 2 |  |
| 267 | `lay-table-done` | определение `:` | src/compute.fth:108 | 2 |  |
| 268 | `lay-table` | определение `:` | src/compute.fth:110 | 23 |  |
| 269 | `lay-add-entry` | определение `:` | src/compute.fth:127 | 1 |  |
| 270 | `lay-sub-entry` | определение `:` | src/compute.fth:129 | 2 |  |
| 271 | `lay-xor-entry` | определение `:` | src/compute.fth:131 | 1 |  |
| 272 | `lay-or-entry` | определение `:` | src/compute.fth:132 | 1 |  |
| 273 | `lay-and-entry` | определение `:` | src/compute.fth:133 | 1 |  |
| 274 | `lay-or8-entry` | определение `:` | src/compute.fth:134 | 1 |  |
| 275 | `lay-fz` | переменная | src/compute.fth:135 | 3 |  |
| 276 | `lay-fu` | переменная | src/compute.fth:135 | 4 |  |
| 277 | `lay-fs` | переменная | src/compute.fth:135 | 3 |  |
| 278 | `lay-pair` | определение `:` | src/compute.fth:136 | 6 |  |
| 279 | `lay-flags-entry` | определение `:` | src/compute.fth:137 | 1 |  |
| 280 | `lay-not5-entry` | определение `:` | src/compute.fth:144 | 1 |  |
| 281 | `lay-sign-entry` | определение `:` | src/compute.fth:145 | 1 |  |
| 282 | `lay-fill24-entry` | определение `:` | src/compute.fth:146 | 1 |  |
| 283 | `lay-fill16-entry` | определение `:` | src/compute.fth:147 | 1 |  |
| 284 | `lay-inc1-entry` | определение `:` | src/compute.fth:148 | 1 |  |
| 285 | `lay-inc2-entry` | определение `:` | src/compute.fth:149 | 1 |  |
| 286 | `lay-t-add` | переменная | src/compute.fth:150 | 7 |  |
| 287 | `lay-t-sub` | переменная | src/compute.fth:150 | 5 |  |
| 288 | `lay-t-xor` | переменная | src/compute.fth:150 | 5 |  |
| 289 | `lay-t-or` | переменная | src/compute.fth:150 | 2 |  |
| 290 | `lay-t-and` | переменная | src/compute.fth:150 | 2 |  |
| 291 | `lay-t-or8` | переменная | src/compute.fth:151 | 2 |  |
| 292 | `lay-t-flags` | переменная | src/compute.fth:151 | 2 |  |
| 293 | `lay-t-not5` | переменная | src/compute.fth:151 | 2 |  |
| 294 | `lay-t-sign32` | переменная | src/compute.fth:151 | 2 |  |
| 295 | `lay-t-fill24` | переменная | src/compute.fth:152 | 1 |  |
| 296 | `lay-t-fill16` | переменная | src/compute.fth:152 | 1 |  |
| 297 | `lay-t-inc1` | переменная | src/compute.fth:152 | 1 |  |
| 298 | `lay-t-inc2` | переменная | src/compute.fth:152 | 1 |  |
| 299 | `lay-standard-tables` | определение `:` | src/compute.fth:153 | 1 |  |
| 300 | `lay-oo` | переменная | src/compute.fth:161 | 2 |  |
| 301 | `lay-os` | переменная | src/compute.fth:161 | 2 |  |
| 302 | `lay-ol` | переменная | src/compute.fth:161 | 4 |  |
| 303 | `lay-oh` | переменная | src/compute.fth:161 | 3 |  |
| 304 | `lay-or-chunks` | определение `:` | src/compute.fth:162 | 3 |  |
| 305 | `lay-cr` | переменная | src/compute.fth:168 | 5 |  |
| 306 | `lay-ca` | переменная | src/compute.fth:168 | 4 |  |
| 307 | `lay-cb` | переменная | src/compute.fth:168 | 4 |  |
| 308 | `lay-logic` | определение `:` | src/compute.fth:175 | 4 |  |
| 309 | `lay-sres` | переменная | src/compute.fth:181 | 3 |  |
| 310 | `lay-sa` | переменная | src/compute.fth:181 | 7 |  |
| 311 | `lay-samt` | переменная | src/compute.fth:181 | 8 |  |
| 312 | `lay-sw` | переменная | src/compute.fth:181 | 9 |  |
| 313 | `lay-szero` | переменная | src/compute.fth:181 | 4 |  |
| 314 | `lay-sarg` | переменная | src/compute.fth:182 | 6 |  |
| 315 | `lay-sign` | переменная | src/compute.fth:182 | 6 |  |
| 316 | `lay-shift-row` | определение `:` | src/compute.fth:183 | 3 |  |
| 317 | `lay-shift-patch` | определение `:` | src/compute.fth:184 | 6 |  |
| 318 | `lay-shift-right` | определение `:` | src/compute.fth:186 | 1 |  |
| 319 | `lay-shift-left` | определение `:` | src/compute.fth:203 | 1 |  |
| 320 | `fc-size` | константа | src/forthc.fth:6 | 2 |  |
| 321 | `fc-cellb` | константа | src/forthc.fth:6 | 5 |  |
| 322 | `fc-l` | константа | src/forthc.fth:6 | 1 |  |
| 323 | `fc-a` | константа | src/forthc.fth:6 | 2 |  |
| 324 | `fc-d` | переменная | src/forthc.fth:8 | 3 |  |
| 325 | `fc-first` | переменная | src/forthc.fth:8 | 3 |  |
| 326 | `fc-guard` | переменная | src/forthc.fth:10 | 20 |  |
| 327 | `fc-bbits` | константа | src/forthc.fth:16 | 7 |  |
| 328 | `fc-abits` | константа | src/forthc.fth:16 | 5 |  |
| 329 | `fc-ebits` | константа | src/forthc.fth:16 | 6 |  |
| 330 | `fc-etab` | константа | src/forthc.fth:16 | 5 |  |
| 331 | `fc-rbits` | константа | src/forthc.fth:17 | 5 |  |
| 332 | `fc-rtab` | константа | src/forthc.fth:17 | 4 |  |
| 333 | `fc-layout` | определение `:` | src/forthc.fth:18 | 1 |  |
| 334 | `fc-d+` | определение `:` | src/forthc.fth:20 | 26 |  |
| 335 | `fc-sp` | определение `:` | src/forthc.fth:21 | 4 |  |
| 336 | `fc-rp` | определение `:` | src/forthc.fth:21 | 13 |  |
| 337 | `fc-code` | определение `:` | src/forthc.fth:21 | 1 |  |
| 338 | `fc-regs` | определение `:` | src/forthc.fth:22 | 2 |  |
| 339 | `fc-nregs` | константа | src/forthc.fth:22 | 2 |  |
| 340 | `fc-tmp` | определение `:` | src/forthc.fth:23 | 12 |  |
| 341 | `fc-xr` | определение `:` | src/forthc.fth:23 | 10 |  |
| 342 | `fc-z` | определение `:` | src/forthc.fth:23 | 4 |  |
| 343 | `fc-idx` | определение `:` | src/forthc.fth:23 | 5 |  |
| 344 | `fc-ma` | определение `:` | src/forthc.fth:24 | 6 |  |
| 345 | `fc-mb` | определение `:` | src/forthc.fth:24 | 6 |  |
| 346 | `fc-mp` | определение `:` | src/forthc.fth:24 | 2 |  |
| 347 | `fc-mq` | определение `:` | src/forthc.fth:24 | 3 |  |
| 348 | `fc-mr` | определение `:` | src/forthc.fth:24 | 3 |  |
| 349 | `fc-zero` | определение `:` | src/forthc.fth:25 | 12 |  |
| 350 | `fc-consts` | определение `:` | src/forthc.fth:25 | 3 |  |
| 351 | `fc-sw` | определение `:` | src/forthc.fth:26 | 2 |  |
| 352 | `fc-su` | определение `:` | src/forthc.fth:26 | 1 |  |
| 353 | `fc-key` | определение `:` | src/forthc.fth:26 | 3 |  |
| 354 | `fc-bp` | определение `:` | src/forthc.fth:26 | 2 |  |
| 355 | `fc-tab` | определение `:` | src/forthc.fth:27 | 1 |  |
| 356 | `fc-stk` | определение `:` | src/forthc.fth:27 | 3 |  |
| 357 | `fc-rstk` | определение `:` | src/forthc.fth:28 | 13 |  |
| 358 | `fc-scr0` | определение `:` | src/forthc.fth:28 | 1 |  |
| 359 | `fc-links` | определение `:` | src/forthc.fth:29 | 2 |  |
| 360 | `fc-max-links` | константа | src/forthc.fth:29 | 1 |  |
| 361 | `fc-link-chunk` | константа | src/forthc.fth:29 | 1 |  |
| 362 | `fc-mem` | определение `:` | src/forthc.fth:30 | 7 |  |
| 363 | `fc-mw` | константа | src/forthc.fth:30 | 2 |  |
| 364 | `fc-htab` | определение `:` | src/forthc.fth:30 | 1 |  |
| 365 | `fc-data-start` | константа | src/forthc.fth:31 | 1 |  |
| 366 | `fc-off` | данные `create` | src/forthc.fth:33 | 2 |  |
| 367 | `fc-oc` | переменная | src/forthc.fth:33 | 2 |  |
| 368 | `fc-t-rev8` | переменная | src/forthc.fth:34 | 3 |  |
| 369 | `fc-t-zero32` | переменная | src/forthc.fth:34 | 2 |  |
| 370 | `fc-t-nz2` | переменная | src/forthc.fth:34 | 2 |  |
| 371 | `fc-t-lt32` | переменная | src/forthc.fth:34 | 2 |  |
| 372 | `fc-t-xr2` | переменная | src/forthc.fth:35 | 2 |  |
| 373 | `fc-t-ult32` | переменная | src/forthc.fth:35 | 2 |  |
| 374 | `fc-t-bytepos` | переменная | src/forthc.fth:35 | 2 |  |
| 375 | `fc-off@` | определение `:` | src/forthc.fth:36 | 2 |  |
| 376 | `fc-off-table` | определение `:` | src/forthc.fth:37 | 1 |  |
| 377 | `fc-rev-entry` | определение `:` | src/forthc.fth:40 | 1 |  |
| 378 | `fc-zero-entry` | определение `:` | src/forthc.fth:41 | 1 |  |
| 379 | `fc-nz-entry` | определение `:` | src/forthc.fth:42 | 1 |  |
| 380 | `fc-lt-entry` | определение `:` | src/forthc.fth:43 | 1 |  |
| 381 | `fc-xr2-entry` | определение `:` | src/forthc.fth:46 | 1 |  |
| 382 | `fc-ult-entry` | определение `:` | src/forthc.fth:47 | 1 |  |
| 383 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 384 | `fc-tables` | определение `:` | src/forthc.fth:49 | 1 |  |
| 385 | `fc-mul4-entry` | определение `:` | src/forthc.fth:60 | 1 |  |
| 386 | `fc-qsel-entry` | определение `:` | src/forthc.fth:63 | 1 |  |
| 387 | `fc-max-consts` | переменная | src/forthc.fth:66 | 4 | вход бута (хост) |
| 388 | `fc-ck` | переменная | src/forthc.fth:66 | 3 |  |
| 389 | `fc-nconsts` | переменная | src/forthc.fth:66 | 7 |  |
| 390 | `fc-nbuckets` | переменная | src/forthc.fth:67 | 7 | вход бута (хост) |
| 391 | `fc-cbk` | переменная | src/forthc.fth:67 | 3 |  |
| 392 | `fc-ck@` | определение `:` | src/forthc.fth:68 | 3 |  |
| 393 | `fc-chash` | определение `:` | src/forthc.fth:69 | 1 |  |
| 394 | `fc-cb` | переменная | src/forthc.fth:70 | 3 |  |
| 395 | `fc-const2` | определение `:` | src/forthc.fth:71 | 1 |  |
| 396 | `fc-const` | определение `:` | src/forthc.fth:81 | 4 |  |
| 397 | `fc-lit` | определение `:` | src/forthc.fth:84 | 3 |  |
| 398 | `fc-bit0` | определение `:` | src/forthc.fth:85 | 1 |  |
| 399 | `fc-bit1` | определение `:` | src/forthc.fth:86 | 1 |  |
| 400 | `fc-length` | определение `:` | src/forthc.fth:87 | 1 |  |
| 401 | `fc-lit-of` | определение `:` | src/forthc.fth:88 | 1 |  |
| 402 | `fc-load` | определение `:` | src/forthc.fth:90 | 1 |  |
| 403 | `fc-nlinks` | переменная | src/forthc.fth:92 | 5 |  |
| 404 | `fc-link-buf` | переменная | src/forthc.fth:92 | 4 |  |
| 405 | `fc-nbuf` | переменная | src/forthc.fth:92 | 8 |  |
| 406 | `fc-put-links` | определение `:` | src/forthc.fth:93 | 2 |  |
| 407 | `fc-link-pair` | определение `:` | src/forthc.fth:97 | 2 |  |
| 408 | `fc-link-const` | определение `:` | src/forthc.fth:102 | 1 |  |
| 409 | `fc-eight` | данные `create` | src/forthc.fth:103 | 7 |  |
| 410 | `fc-zeros` | данные `create` | src/forthc.fth:103 | 4 |  |
| 411 | `fc-put-consts` | определение `:` | src/forthc.fth:104 | 1 |  |
| 412 | `fc-cache` | данные `create` | src/forthc.fth:111 | 8 |  |
| 413 | `fc-n` | переменная | src/forthc.fth:111 | 28 |  |
| 414 | `fc-pin` | данные `create` | src/forthc.fth:112 | 13 |  |
| 415 | `fc-npin` | переменная | src/forthc.fth:112 | 20 |  |
| 416 | `fc-c@` | определение `:` | src/forthc.fth:113 | 8 |  |
| 417 | `fc-push` | определение `:` | src/forthc.fth:114 | 28 |  |
| 418 | `fc-pop1` | определение `:` | src/forthc.fth:115 | 36 |  |
| 419 | `fc-in?` | определение `:` | src/forthc.fth:116 | 3 |  |
| 420 | `fc-reg` | определение `:` | src/forthc.fth:117 | 16 |  |
| 421 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:122 | 1 |  |
| 422 | `fc-scr` | переменная | src/forthc.fth:123 | 3 |  |
| 423 | `fc-scratch` | определение `:` | src/forthc.fth:124 | 11 |  |
| 424 | `fc-offs` | данные `create` | src/forthc.fth:127 | 5 |  |
| 425 | `fc-noff` | переменная | src/forthc.fth:127 | 9 |  |
| 426 | `fc-ptr` | переменная | src/forthc.fth:127 | 4 |  |
| 427 | `fc-iw` | переменная | src/forthc.fth:128 | 4 |  |
| 428 | `fc-adjust` | определение `:` | src/forthc.fth:129 | 7 |  |
| 429 | `fc-prow` | данные `create` | src/forthc.fth:135 | 2 |  |
| 430 | `fc-nrow` | переменная | src/forthc.fth:135 | 8 |  |
| 431 | `fc-pl` | данные `create` | src/forthc.fth:136 | 2 |  |
| 432 | `fc-pslot` | данные `create` | src/forthc.fth:136 | 2 |  |
| 433 | `fc-rl` | переменная | src/forthc.fth:137 | 3 |  |
| 434 | `fc-f0` | переменная | src/forthc.fth:137 | 2 |  |
| 435 | `fc-f1` | переменная | src/forthc.fth:137 | 2 |  |
| 436 | `fc-psh` | переменная | src/forthc.fth:137 | 2 |  |
| 437 | `fc-row+` | определение `:` | src/forthc.fth:138 | 3 |  |
| 438 | `fc-4@` | определение `:` | src/forthc.fth:140 | 3 |  |
| 439 | `fc-patched` | определение `:` | src/forthc.fth:141 | 3 |  |
| 440 | `fc-popped` | данные `create` | src/forthc.fth:152 | 2 |  |
| 441 | `fc-srcs` | данные `create` | src/forthc.fth:152 | 13 |  |
| 442 | `fc-nsrc` | переменная | src/forthc.fth:152 | 20 |  |
| 443 | `fc-mbase` | переменная | src/forthc.fth:153 | 8 |  |
| 444 | `fc-mptr` | переменная | src/forthc.fth:153 | 4 |  |
| 445 | `fc-mn` | переменная | src/forthc.fth:153 | 7 |  |
| 446 | `fc-mw2` | переменная | src/forthc.fth:153 | 6 |  |
| 447 | `fc-popped@` | определение `:` | src/forthc.fth:154 | 6 |  |
| 448 | `fc-shift` | определение `:` | src/forthc.fth:155 | 4 |  |
| 449 | `fc-mem-pop` | определение `:` | src/forthc.fth:156 | 3 |  |
| 450 | `fc-push-group` | определение `:` | src/forthc.fth:164 | 2 |  |
| 451 | `fc-dup-at` | определение `:` | src/forthc.fth:170 | 1 |  |
| 452 | `fc-rest` | данные `create` | src/forthc.fth:172 | 2 |  |
| 453 | `fc-nrest` | переменная | src/forthc.fth:172 | 3 |  |
| 454 | `fc-mem-push` | определение `:` | src/forthc.fth:173 | 7 |  |
| 455 | `fc-src1` | определение `:` | src/forthc.fth:179 | 3 |  |
| 456 | `fc-need` | определение `:` | src/forthc.fth:180 | 17 |  |
| 457 | `fc-spill` | определение `:` | src/forthc.fth:186 | 16 |  |
| 458 | `fc-pop` | определение `:` | src/forthc.fth:192 | 11 |  |
| 459 | `fc-max-log` | константа | src/forthc.fth:197 | 1 |  |
| 460 | `fc-max-notes` | константа | src/forthc.fth:197 | 3 |  |
| 461 | `fc-log` | переменная | src/forthc.fth:198 | 3 |  |
| 462 | `fc-nlog` | переменная | src/forthc.fth:198 | 5 |  |
| 463 | `fc-decs` | переменная | src/forthc.fth:198 | 2 |  |
| 464 | `fc-ndec` | переменная | src/forthc.fth:198 | 6 |  |
| 465 | `fc-calls` | переменная | src/forthc.fth:198 | 2 |  |
| 466 | `fc-ncall` | переменная | src/forthc.fth:198 | 6 |  |
| 467 | `fc-pend` | переменная | src/forthc.fth:199 | 2 |  |
| 468 | `fc-npend` | переменная | src/forthc.fth:199 | 9 |  |
| 469 | `fc-unknown` | переменная | src/forthc.fth:199 | 7 |  |
| 470 | `fc-lc` | переменная | src/forthc.fth:200 | 3 |  |
| 471 | `fc-lb` | переменная | src/forthc.fth:200 | 3 |  |
| 472 | `fc-row-n` | определение `:` | src/forthc.fth:201 | 1 |  |
| 473 | `fc-mem-row?` | определение `:` | src/forthc.fth:202 | 1 |  |
| 474 | `fc-log-layer` | определение `:` | src/forthc.fth:203 | 2 |  |
| 475 | `fc-log-begin` | определение `:` | src/forthc.fth:215 | 3 |  |
| 476 | `fc-log-end` | определение `:` | src/forthc.fth:217 | 4 |  |
| 477 | `fc-by-execution` | определение `:` | src/forthc.fth:218 | 7 |  |
| 478 | `fc-dec@` | определение `:` | src/forthc.fth:219 | 2 |  |
| 479 | `fc-call@` | определение `:` | src/forthc.fth:220 | 2 |  |
| 480 | `fc-log-decision` | определение `:` | src/forthc.fth:221 | 2 |  |
| 481 | `fc-log-call` | определение `:` | src/forthc.fth:225 | 2 |  |
| 482 | `fc-callee` | переменная | src/forthc.fth:229 | 4 |  |
| 483 | `fc-live` | переменная | src/forthc.fth:231 | 7 |  |
| 484 | `fc-tramp` | переменная | src/forthc.fth:231 | 6 |  |
| 485 | `fc-ex` | переменная | src/forthc.fth:231 | 4 |  |
| 486 | `fc-halt` | переменная | src/forthc.fth:231 | 3 |  |
| 487 | `fc-jump` | определение `:` | src/forthc.fth:232 | 8 |  |
| 488 | `fc-end` | определение `:` | src/forthc.fth:233 | 12 |  |
| 489 | `fc-begin-block` | определение `:` | src/forthc.fth:234 | 21 |  |
| 490 | `fc-rows1` | определение `:` | src/forthc.fth:238 | 12 |  |
| 491 | `fc-nonzero` | определение `:` | src/forthc.fth:239 | 2 |  |
| 492 | `fc-branch` | определение `:` | src/forthc.fth:242 | 5 |  |
| 493 | `fc-rtab-at` | определение `:` | src/forthc.fth:243 | 1 |  |
| 494 | `fc-nret` | переменная | src/forthc.fth:244 | 6 |  |
| 495 | `fc-ret-link` | определение `:` | src/forthc.fth:248 | 3 |  |
| 496 | `fc-ret-base` | определение `:` | src/forthc.fth:253 | 4 |  |
| 497 | `fc-call` | определение `:` | src/forthc.fth:254 | 4 |  |
| 498 | `fc-v0` | переменная | src/forthc.fth:258 | 4 |  |
| 499 | `fc-v1` | переменная | src/forthc.fth:258 | 4 |  |
| 500 | `fc-jw` | определение `:` | src/forthc.fth:259 | 2 |  |
| 501 | `fc-xw` | определение `:` | src/forthc.fth:260 | 2 |  |
| 502 | `fc-xoff` | определение `:` | src/forthc.fth:261 | 2 |  |
| 503 | `fc-etab-at` | определение `:` | src/forthc.fth:262 | 1 |  |
| 504 | `fc-ex-base` | определение `:` | src/forthc.fth:263 | 1 |  |
| 505 | `fc-call-indirect` | определение `:` | src/forthc.fth:264 | 1 |  |
| 506 | `fc-ret-p` | переменная | src/forthc.fth:271 | 4 |  |
| 507 | `fc-ret-l` | переменная | src/forthc.fth:271 | 6 |  |
| 508 | `fc-rs0` | переменная | src/forthc.fth:271 | 3 |  |
| 509 | `fc-rs1` | переменная | src/forthc.fth:271 | 3 |  |
| 510 | `fc-ret-m` | переменная | src/forthc.fth:271 | 3 |  |
| 511 | `fc-ret-t` | переменная | src/forthc.fth:271 | 3 |  |
| 512 | `fc-ret-patch` | определение `:` | src/forthc.fth:272 | 4 |  |
| 513 | `fc-ret-masked` | определение `:` | src/forthc.fth:274 | 1 |  |
| 514 | `fc-ret` | определение `:` | src/forthc.fth:280 | 3 |  |
| 515 | `fc-ca` | переменная | src/forthc.fth:292 | 3 |  |
| 516 | `fc-cl0` | переменная | src/forthc.fth:292 | 4 |  |
| 517 | `fc-cl1` | переменная | src/forthc.fth:292 | 4 |  |
| 518 | `fc-cr` | переменная | src/forthc.fth:292 | 4 |  |
| 519 | `fc-cslot` | переменная | src/forthc.fth:292 | 3 |  |
| 520 | `fc-csh` | переменная | src/forthc.fth:292 | 2 |  |
| 521 | `fc-cv` | переменная | src/forthc.fth:293 | 3 |  |
| 522 | `fc-cres` | переменная | src/forthc.fth:293 | 6 |  |
| 523 | `fc-cmode` | переменная | src/forthc.fth:293 | 6 |  |
| 524 | `fc-ar` | переменная | src/forthc.fth:293 | 5 |  |
| 525 | `fc-chk-read` | определение `:` | src/forthc.fth:294 | 1 |  |
| 526 | `fc-chk-seg` | определение `:` | src/forthc.fth:296 | 1 |  |
| 527 | `fc-as` | переменная | src/forthc.fth:299 | 2 |  |
| 528 | `fc-af` | переменная | src/forthc.fth:299 | 2 |  |
| 529 | `fc-al0` | переменная | src/forthc.fth:299 | 2 |  |
| 530 | `fc-al1` | переменная | src/forthc.fth:299 | 2 |  |
| 531 | `fc-apl` | переменная | src/forthc.fth:299 | 3 |  |
| 532 | `fc-afld` | переменная | src/forthc.fth:299 | 3 |  |
| 533 | `fc-access-patch` | определение `:` | src/forthc.fth:300 | 2 |  |
| 534 | `fc-access` | определение `:` | src/forthc.fth:305 | 1 |  |
| 535 | `fc-width` | определение `:` | src/forthc.fth:307 | 4 |  |
| 536 | `fc-check` | определение `:` | src/forthc.fth:308 | 4 |  |
| 537 | `fc-ring` | константа | src/forthc.fth:324 | 5 |  |
| 538 | `fc-window` | константа | src/forthc.fth:324 | 1 |  |
| 539 | `fc-sl` | данные `create` | src/forthc.fth:325 | 2 |  |
| 540 | `fc-stabs` | переменная | src/forthc.fth:325 | 2 |  |
| 541 | `fc-slen` | переменная | src/forthc.fth:326 | 7 |  |
| 542 | `fc-slow` | переменная | src/forthc.fth:326 | 4 |  |
| 543 | `fc-sinit` | определение `:` | src/forthc.fth:327 | 2 |  |
| 544 | `fc-sbegin` | определение `:` | src/forthc.fth:328 | 2 |  |
| 545 | `fc-tabs` | определение `:` | src/forthc.fth:329 | 3 |  |
| 546 | `fc-at` | определение `:` | src/forthc.fth:330 | 4 |  |
| 547 | `fc-has?` | определение `:` | src/forthc.fth:335 | 1 |  |
| 548 | `fc-tab+` | определение `:` | src/forthc.fth:336 | 1 |  |
| 549 | `fc-prw` | данные `create` | src/forthc.fth:337 | 6 |  |
| 550 | `fc-ptab` | переменная | src/forthc.fth:337 | 5 |  |
| 551 | `fc-place` | определение `:` | src/forthc.fth:338 | 3 |  |
| 552 | `fc-scopy` | определение `:` | src/forthc.fth:348 | 9 |  |
| 553 | `fc-segs` | данные `create` | src/forthc.fth:349 | 2 |  |
| 554 | `fc-nseg` | переменная | src/forthc.fth:349 | 5 |  |
| 555 | `fc-pp` | данные `create` | src/forthc.fth:350 | 2 |  |
| 556 | `fc-npp` | переменная | src/forthc.fth:350 | 4 |  |
| 557 | `fc-latest` | переменная | src/forthc.fth:350 | 4 |  |
| 558 | `fc-sga` | переменная | src/forthc.fth:350 | 14 |  |
| 559 | `fc-ltab` | переменная | src/forthc.fth:351 | 3 |  |
| 560 | `fc-ls` | переменная | src/forthc.fth:351 | 3 |  |
| 561 | `fc-lw` | переменная | src/forthc.fth:351 | 3 |  |
| 562 | `fc-ldst` | переменная | src/forthc.fth:351 | 2 |  |
| 563 | `fc-seg+` | определение `:` | src/forthc.fth:352 | 21 |  |
| 564 | `fc-pp+` | определение `:` | src/forthc.fth:355 | 1 |  |
| 565 | `fc-slookup` | определение `:` | src/forthc.fth:356 | 8 |  |
| 566 | `fc-nx` | переменная | src/forthc.fth:374 | 3 |  |
| 567 | `fc-nv` | переменная | src/forthc.fth:374 | 2 |  |
| 568 | `fc-nt` | переменная | src/forthc.fth:374 | 3 |  |
| 569 | `fc-negate-chain` | определение `:` | src/forthc.fth:375 | 1 |  |
| 570 | `fc-gw` | переменная | src/forthc.fth:381 | 4 |  |
| 571 | `fc-gs` | переменная | src/forthc.fth:381 | 2 |  |
| 572 | `fc-gs2` | переменная | src/forthc.fth:381 | 2 |  |
| 573 | `fc-gts` | переменная | src/forthc.fth:381 | 6 |  |
| 574 | `fc-gdst` | переменная | src/forthc.fth:381 | 2 |  |
| 575 | `fc-negate-select` | определение `:` | src/forthc.fth:382 | 4 |  |
| 576 | `fc-sfinish` | определение `:` | src/forthc.fth:387 | 2 |  |
| 577 | `fc-pr` | данные `create` | src/forthc.fth:390 | 2 |  |
| 578 | `fc-xs` | данные `create` | src/forthc.fth:390 | 2 |  |
| 579 | `fc-m4` | переменная | src/forthc.fth:391 | 2 |  |
| 580 | `fc-mj` | переменная | src/forthc.fth:391 | 11 |  |
| 581 | `fc-mk` | переменная | src/forthc.fth:391 | 6 |  |
| 582 | `fc-p@` | определение `:` | src/forthc.fth:392 | 3 |  |
| 583 | `fc-p!` | определение `:` | src/forthc.fth:393 | 1 |  |
| 584 | `fc-x@` | определение `:` | src/forthc.fth:394 | 3 |  |
| 585 | `fc-x!` | определение `:` | src/forthc.fth:395 | 2 |  |
| 586 | `fc-build-mul` | определение `:` | src/forthc.fth:396 | 1 |  |
| 587 | `fc-sub` | данные `create` | src/forthc.fth:414 | 2 |  |
| 588 | `fc-qsel` | переменная | src/forthc.fth:414 | 2 |  |
| 589 | `fc-absa` | переменная | src/forthc.fth:415 | 5 |  |
| 590 | `fc-absb` | переменная | src/forthc.fth:415 | 3 |  |
| 591 | `fc-ta` | переменная | src/forthc.fth:415 | 4 |  |
| 592 | `fc-tb` | переменная | src/forthc.fth:415 | 2 |  |
| 593 | `fc-rem` | переменная | src/forthc.fth:416 | 7 |  |
| 594 | `fc-tr` | переменная | src/forthc.fth:416 | 7 |  |
| 595 | `fc-q` | переменная | src/forthc.fth:416 | 3 |  |
| 596 | `fc-tq` | переменная | src/forthc.fth:416 | 4 |  |
| 597 | `fc-k` | переменная | src/forthc.fth:416 | 5 |  |
| 598 | `fc-w` | переменная | src/forthc.fth:417 | 14 |  |
| 599 | `fc-lo` | переменная | src/forthc.fth:417 | 7 |  |
| 600 | `fc-tlo` | переменная | src/forthc.fth:417 | 7 |  |
| 601 | `fc-t0` | переменная | src/forthc.fth:417 | 4 |  |
| 602 | `fc-t1` | переменная | src/forthc.fth:417 | 4 |  |
| 603 | `fc-qr` | переменная | src/forthc.fth:417 | 4 |  |
| 604 | `fc-tqk` | переменная | src/forthc.fth:417 | 3 |  |
| 605 | `fc-sub@` | определение `:` | src/forthc.fth:418 | 7 |  |
| 606 | `fc-step` | определение `:` | src/forthc.fth:419 | 3 |  |
| 607 | `fc-div-step` | определение `:` | src/forthc.fth:426 | 1 |  |
| 608 | `fc-build-div` | определение `:` | src/forthc.fth:443 | 1 |  |
| 609 | `fc-mul-entry` | переменная | src/forthc.fth:459 | 4 |  |
| 610 | `fc-mul-exit` | переменная | src/forthc.fth:459 | 2 |  |
| 611 | `fc-div-entry` | переменная | src/forthc.fth:459 | 5 |  |
| 612 | `fc-div-exit` | переменная | src/forthc.fth:459 | 4 |  |
| 613 | `fc-hl` | переменная | src/forthc.fth:460 | 5 |  |
| 614 | `fc-hcont` | переменная | src/forthc.fth:460 | 4 |  |
| 615 | `fc-mul-cost` | данные `create` | src/forthc.fth:461 | 2 |  |
| 616 | `fc-div-cost` | данные `create` | src/forthc.fth:461 | 2 |  |
| 617 | `fc-row-or-new` | определение `:` | src/forthc.fth:462 | 2 |  |
| 618 | `fc-call-helper` | определение `:` | src/forthc.fth:464 | 4 |  |
| 619 | `fc-result1` | определение `:` | src/forthc.fth:474 | 3 |  |
| 620 | `fc-s1` | переменная | src/forthc.fth:475 | 2 |  |
| 621 | `fc-s2` | переменная | src/forthc.fth:475 | 2 |  |
| 622 | `fc-r1` | переменная | src/forthc.fth:475 | 2 |  |
| 623 | `fc-result2` | определение `:` | src/forthc.fth:476 | 1 |  |
| 624 | `fc-forbid` | константа | src/forthc.fth:484 | 2 |  |
| 625 | `fc-pexit` | переменная | src/forthc.fth:485 | 2 |  |
| 626 | `fc-ptramp` | переменная | src/forthc.fth:485 | 2 |  |
| 627 | `fc-pd` | переменная | src/forthc.fth:485 | 5 |  |
| 628 | `fc-pc` | переменная | src/forthc.fth:485 | 5 |  |
| 629 | `fc-ends` | переменная | src/forthc.fth:485 | 3 |  |
| 630 | `fc-pb` | переменная | src/forthc.fth:486 | 5 |  |
| 631 | `fc-pcp` | переменная | src/forthc.fth:486 | 5 |  |
| 632 | `fc-pln` | переменная | src/forthc.fth:486 | 5 |  |
| 633 | `fc-pk` | переменная | src/forthc.fth:486 | 4 |  |
| 634 | `fc-pcall` | переменная | src/forthc.fth:486 | 3 |  |
| 635 | `fc-best` | данные `create` | src/forthc.fth:487 | 10 |  |
| 636 | `fc-pend@` | определение `:` | src/forthc.fth:488 | 7 |  |
| 637 | `fc-reach` | определение `:` | src/forthc.fth:489 | 2 |  |
| 638 | `fc-take` | определение `:` | src/forthc.fth:498 | 1 |  |
| 639 | `fc-end-path` | определение `:` | src/forthc.fth:505 | 2 |  |
| 640 | `fc-to` | определение `:` | src/forthc.fth:509 | 2 |  |
| 641 | `fc-node` | определение `:` | src/forthc.fth:513 | 1 |  |
| 642 | `fc-path` | определение `:` | src/forthc.fth:532 | 3 |  |
| 643 | `fc-cost!` | определение `:` | src/forthc.fth:541 | 4 |  |
| 644 | `fc-ll` | переменная | src/forthc.fth:543 | 8 |  |
| 645 | `fc-llr` | переменная | src/forthc.fth:543 | 4 |  |
| 646 | `fc-llv` | переменная | src/forthc.fth:543 | 4 |  |
| 647 | `fc-plit` | переменная | src/forthc.fth:543 | 7 |  |
| 648 | `fc-plr` | переменная | src/forthc.fth:543 | 5 |  |
| 649 | `fc-plv` | переменная | src/forthc.fth:543 | 7 |  |
| 650 | `fc-literal` | определение `:` | src/forthc.fth:544 | 15 |  |
| 651 | `fc-or-zero` | определение `:` | src/forthc.fth:546 | 2 |  |
| 652 | `fc-ba` | переменная | src/forthc.fth:549 | 13 |  |
| 653 | `fc-bb` | переменная | src/forthc.fth:549 | 13 |  |
| 654 | `fc-br` | переменная | src/forthc.fth:549 | 9 |  |
| 655 | `fc-binary` | определение `:` | src/forthc.fth:550 | 10 |  |
| 656 | `fc-r-at` | определение `:` | src/forthc.fth:574 | 2 |  |
| 657 | `fc-pop-pinned` | определение `:` | src/forthc.fth:577 | 3 |  |
| 658 | `fc-sk` | переменная | src/forthc.fth:578 | 12 |  |
| 659 | `fc-shift-copy` | определение `:` | src/forthc.fth:579 | 2 |  |
| 660 | `fc-inc` | определение `:` | src/forthc.fth:583 | 3 |  |
| 661 | `fc-read-key` | определение `:` | src/forthc.fth:586 | 1 |  |
| 662 | `fc-text-mem` | данные `create` | src/forthc.fth:591 | 1 |  |
| 663 | `fc-text` | переменная | src/forthc.fth:592 | 13 |  |
| 664 | `fc-tlen` | переменная | src/forthc.fth:592 | 14 |  |
| 665 | `fc-pos` | переменная | src/forthc.fth:592 | 24 |  |
| 666 | `fc-text-size` | переменная | src/forthc.fth:592 | 5 | вход бута (хост) |
| 667 | `fc-reset` | определение `:` | src/forthc.fth:593 | 3 |  |
| 668 | `fc-append` | определение `:` | src/forthc.fth:594 | 1 |  |
| 669 | `fc\|` | определение `:` | src/forthc.fth:598 | 1 | вход бута (хост) |
| 670 | `fc-ch` | определение `:` | src/forthc.fth:599 | 5 |  |
| 671 | `fc-more?` | определение `:` | src/forthc.fth:600 | 6 |  |
| 672 | `fc-next` | определение `:` | src/forthc.fth:601 | 8 |  |
| 673 | `fc-next!` | определение `:` | src/forthc.fth:609 | 10 |  |
| 674 | `fc-is?` | определение `:` | src/forthc.fth:610 | 5 |  |
| 675 | `fc-raw` | определение `:` | src/forthc.fth:613 | 1 |  |
| 676 | `fc-string-token` | определение `:` | src/forthc.fth:614 | 1 |  |
| 677 | `fc-names-size` | переменная | src/forthc.fth:619 | 4 | вход бута (хост) |
| 678 | `fc-max-words` | переменная | src/forthc.fth:619 | 4 | вход бута (хост) |
| 679 | `fc-names` | переменная | src/forthc.fth:620 | 3 |  |
| 680 | `fc-names-used` | переменная | src/forthc.fth:620 | 5 |  |
| 681 | `fc-wt` | переменная | src/forthc.fth:621 | 5 |  |
| 682 | `fc-nwords` | переменная | src/forthc.fth:621 | 12 |  |
| 683 | `fc-wbk` | переменная | src/forthc.fth:621 | 3 |  |
| 684 | `fc-wt@` | определение `:` | src/forthc.fth:624 | 6 |  |
| 685 | `fc-proved` | данные `create` | src/forthc.fth:626 | 2 |  |
| 686 | `fc-unproved` | данные `create` | src/forthc.fth:627 | 2 |  |
| 687 | `fc-mechanisms` | определение `:` | src/forthc.fth:628 | 1 |  |
| 688 | `fc-xt` | определение `:` | src/forthc.fth:633 | 5 |  |
| 689 | `fc-xtn` | определение `:` | src/forthc.fth:635 | 2 |  |
| 690 | `fc-hash` | определение `:` | src/forthc.fth:636 | 2 |  |
| 691 | `fc-define` | определение `:` | src/forthc.fth:638 | 6 |  |
| 692 | `fc-lookup` | определение `:` | src/forthc.fth:643 | 6 |  |
| 693 | `fc-find` | определение `:` | src/forthc.fth:647 | 6 |  |
| 694 | `fc-word-of` | определение `:` | src/forthc.fth:649 | 2 |  |
| 695 | `fc-cost` | определение `:` | src/forthc.fth:657 | 1 |  |
| 696 | `fc-proved?` | определение `:` | src/forthc.fth:660 | 1 |  |
| 697 | `fc-here` | переменная | src/forthc.fth:662 | 9 |  |
| 698 | `fc-word` | переменная | src/forthc.fth:662 | 13 |  |
| 699 | `fc-uses` | переменная | src/forthc.fth:662 | 17 |  |
| 700 | `fc-rt` | переменная | src/forthc.fth:663 | 7 |  |
| 701 | `fc-rta` | переменная | src/forthc.fth:663 | 7 |  |
| 702 | `fc-ctl` | данные `create` | src/forthc.fth:664 | 1 |  |
| 703 | `fc-nctl` | переменная | src/forthc.fth:664 | 12 |  |
| 704 | `fc-cleave` | переменная | src/forthc.fth:664 | 2 |  |
| 705 | `fc-ctl@` | определение `:` | src/forthc.fth:665 | 4 |  |
| 706 | `fc-ctl+` | определение `:` | src/forthc.fth:666 | 6 |  |
| 707 | `fc-ctl-` | определение `:` | src/forthc.fth:668 | 7 |  |
| 708 | `fc-do-entry` | определение `:` | src/forthc.fth:670 | 1 |  |
| 709 | `fc-ctl-leave` | определение `:` | src/forthc.fth:672 | 1 |  |
| 710 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:673 | 1 |  |
| 711 | `fc-loop-leave` | определение `:` | src/forthc.fth:674 | 1 |  |
| 712 | `fc-align` | определение `:` | src/forthc.fth:675 | 2 |  |
| 713 | `fc-check-here` | определение `:` | src/forthc.fth:676 | 3 |  |
| 714 | `fc-define-data` | определение `:` | src/forthc.fth:677 | 2 |  |
| 715 | `fc-sat` | переменная | src/forthc.fth:678 | 3 |  |
| 716 | `fc-store-string` | определение `:` | src/forthc.fth:679 | 1 |  |
| 717 | `fc-ct` | данные `create` | src/forthc.fth:684 | 3 |  |
| 718 | `fc-nct` | переменная | src/forthc.fth:684 | 11 |  |
| 719 | `fc-ct+` | определение `:` | src/forthc.fth:685 | 24 |  |
| 720 | `fc-ct-` | определение `:` | src/forthc.fth:686 | 9 |  |
| 721 | `fc-ct2` | определение `:` | src/forthc.fth:687 | 8 |  |
| 722 | `fc-inits` | данные `create` | src/forthc.fth:688 | 2 |  |
| 723 | `fc-ninit` | переменная | src/forthc.fth:688 | 5 |  |
| 724 | `fc-init-open` | переменная | src/forthc.fth:688 | 6 |  |
| 725 | `fc-ck-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 726 | `fc-stabs-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 727 | `fc-cbk-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 728 | `fc-link-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 729 | `fc-wt-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 730 | `fc-names-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 731 | `fc-wbk-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 732 | `fc-log-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 733 | `fc-decs-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 734 | `fc-calls-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 735 | `fc-pend-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 736 | `fc-init` | определение `:` | src/forthc.fth:695 | 1 |  |
| 737 | `fc-scan-uses` | определение `:` | src/forthc.fth:709 | 1 |  |
| 738 | `fc-const-shift` | определение `:` | src/forthc.fth:716 | 2 |  |
| 739 | `fc-lit?` | определение `:` | src/forthc.fth:725 | 3 |  |
| 740 | `fc-mul-lit?` | определение `:` | src/forthc.fth:727 | 1 |  |
| 741 | `fc-shift-lit?` | определение `:` | src/forthc.fth:732 | 2 |  |
| 742 | `fc-pick-roll` | определение `:` | src/forthc.fth:735 | 2 |  |
| 743 | `fc-stx` | переменная | src/forthc.fth:744 | 3 |  |
| 744 | `fc-stlo` | переменная | src/forthc.fth:744 | 11 |  |
| 745 | `fc-sthi` | переменная | src/forthc.fth:744 | 5 |  |
| 746 | `fc-stp` | переменная | src/forthc.fth:744 | 6 |  |
| 747 | `fc-strow` | переменная | src/forthc.fth:744 | 16 |  |
| 748 | `fc-stm` | переменная | src/forthc.fth:744 | 5 |  |
| 749 | `fc-ftr` | переменная | src/forthc.fth:745 | 5 |  |
| 750 | `fc-stg` | переменная | src/forthc.fth:745 | 2 |  |
| 751 | `fc-sw0` | определение `:` | src/forthc.fth:746 | 5 |  |
| 752 | `fc-sw1` | определение `:` | src/forthc.fth:747 | 3 |  |
| 753 | `fc-sbase` | определение `:` | src/forthc.fth:748 | 4 |  |
| 754 | `fc-space-end` | определение `:` | src/forthc.fth:749 | 3 |  |
| 755 | `fc-space-store` | определение `:` | src/forthc.fth:757 | 2 |  |
| 756 | `fc-space-fetch` | определение `:` | src/forthc.fth:764 | 2 |  |
| 757 | `fc-cp` | определение `:` | src/forthc.fth:775 | 4 |  |
| 758 | `fc-copy-row` | определение `:` | src/forthc.fth:777 | 1 |  |
| 759 | `fc-close-init` | определение `:` | src/forthc.fth:780 | 2 |  |
| 760 | `fc-open-init` | определение `:` | src/forthc.fth:783 | 1 |  |
| 761 | `fc-gens` | переменная | src/forthc.fth:794 | 3 |  |
| 762 | `fc-generator` | определение `:` | src/forthc.fth:795 | 88 |  |
| 763 | `fc-literal-name` | определение `:` | src/forthc.fth:797 | 10 |  |
| 764 | `fc-words` | определение `:` | src/forthc.fth:799 | 1 |  |
| 765 | `fc-known` | определение `:` | src/forthc.fth:808 | 1 |  |
| 766 | `fc-defining?` | определение `:` | src/forthc.fth:810 | 7 |  |
| 767 | `fc-code` | определение `:` | src/forthc.fth:811 | 53 | вариант 2 |
| 768 | `fc-fold?` | определение `:` | src/forthc.fth:813 | 13 |  |
| 769 | `fc-top-only` | определение `:` | src/forthc.fth:814 | 6 |  |
| 770 | `fc-not-found` | определение `:` | src/forthc.fth:816 | 1 |  |
| 771 | `fc-word-token` | определение `:` | src/forthc.fth:818 | 2 |  |
| 772 | `fc-token` | определение `:` | src/forthc.fth:823 | 2 |  |
| 773 | `fc-synonym-of` | определение `:` | src/forthc.fth:824 | 2 |  |
| 774 | `fc-synonym` | определение `:` | src/forthc.fth:825 | 10 |  |
| 775 | `fc-sy` | переменная | src/forthc.fth:828 | 2 |  |
| 776 | `fc-synonym?` | определение `:` | src/forthc.fth:829 | 1 |  |
| 777 | `fc-poke` | определение `:` | src/forthc.fth:832 | 2 |  |
| 778 | `fc-concept-record` | определение `:` | src/forthc.fth:835 | 1 |  |
| 779 | `fc-eval` | определение `:` | src/forthc.fth:840 | 77 |  |
| 780 | `fc-concepts` | определение `:` | src/forthc.fth:844 | 1 |  |
| 781 | `fc-nhost` | переменная | src/forthc.fth:851 | 5 |  |
| 782 | `fc-platform` | определение `:` | src/forthc.fth:852 | 1 |  |
| 783 | `fc-time-price` | определение `:` | src/forthc.fth:877 | 1 |  |
| 784 | `fc-replacement` | определение `:` | src/forthc.fth:887 | 1 |  |
| 785 | `fc-library` | определение `:` | src/forthc.fth:902 | 1 |  |
| 786 | `fc-forbidden` | определение `:` | src/forthc.fth:931 | 2 |  |
| 787 | `fc-num` | определение `:` | src/forthc.fth:932 | 1 |  |
| 788 | `fc-long-host` | определение `:` | src/forthc.fth:934 | 1 |  |
| 789 | `fc-ltpl` | переменная | src/forthc.fth:951 | 2 |  |
| 790 | `fc-lpos` | данные `create` | src/forthc.fth:951 | 3 |  |
| 791 | `fc-llo` | переменная | src/forthc.fth:951 | 2 |  |
| 792 | `fc-lhi` | переменная | src/forthc.fth:951 | 2 |  |
| 793 | `fc-lcn` | переменная | src/forthc.fth:951 | 4 |  |
| 794 | `fc-ldir` | переменная | src/forthc.fth:951 | 3 |  |
| 795 | `fc-lp0` | переменная | src/forthc.fth:952 | 4 |  |
| 796 | `fc-lp1` | переменная | src/forthc.fth:952 | 4 |  |
| 797 | `fc-lpl` | переменная | src/forthc.fth:952 | 6 |  |
| 798 | `fc-ltemplate` | определение `:` | src/forthc.fth:953 | 1 |  |
| 799 | `fc-lhead` | определение `:` | src/forthc.fth:957 | 2 |  |
| 800 | `fc-lsend` | определение `:` | src/forthc.fth:962 | 2 |  |
| 801 | `fc-lpop` | определение `:` | src/forthc.fth:963 | 2 |  |
| 802 | `fc-lput` | определение `:` | src/forthc.fth:965 | 1 |  |
| 803 | `fc-lget` | определение `:` | src/forthc.fth:975 | 1 |  |
| 804 | `fc-long-kernel` | определение `:` | src/forthc.fth:981 | 1 |  |
| 805 | `fc-long` | определение `:` | src/forthc.fth:991 | 1 |  |
| 806 | `fc-helpers-cost` | определение `:` | src/forthc.fth:996 | 1 |  |
| 807 | `fc-price-word` | определение `:` | src/forthc.fth:1003 | 1 |  |
| 808 | `fc-compile` | определение `:` | src/forthc.fth:1006 | 1 |  |
| 809 | `fc-go` | определение `:` | src/forthc.fth:1022 | 3 | вход бута (хост) |
| 810 | `gen+` | определение `:` | src/primitives.fth:4 | 5 |  |
| 811 | `gen-` | определение `:` | src/primitives.fth:5 | 2 |  |
| 812 | `gen-and` | определение `:` | src/primitives.fth:6 | 2 |  |
| 813 | `gen-or` | определение `:` | src/primitives.fth:7 | 2 |  |
| 814 | `gen-xor` | определение `:` | src/primitives.fth:8 | 2 |  |
| 815 | `gen=` | определение `:` | src/primitives.fth:9 | 2 |  |
| 816 | `gen<` | определение `:` | src/primitives.fth:10 | 2 |  |
| 817 | `gen-u<` | определение `:` | src/primitives.fth:11 | 2 |  |
| 818 | `gen-lshift` | определение `:` | src/primitives.fth:12 | 2 |  |
| 819 | `gen-rshift` | определение `:` | src/primitives.fth:14 | 2 |  |
| 820 | `gen-0=` | определение `:` | src/primitives.fth:16 | 2 |  |
| 821 | `gen-cells` | определение `:` | src/primitives.fth:17 | 2 |  |
| 822 | `gen-2*` | определение `:` | src/primitives.fth:18 | 2 |  |
| 823 | `gen-1+` | определение `:` | src/primitives.fth:19 | 2 |  |
| 824 | `gen-1-` | определение `:` | src/primitives.fth:20 | 2 |  |
| 825 | `gen-cell+` | определение `:` | src/primitives.fth:21 | 2 |  |
| 826 | `gen*` | определение `:` | src/primitives.fth:22 | 2 |  |
| 827 | `gen/` | определение `:` | src/primitives.fth:25 | 2 |  |
| 828 | `gen-mod` | определение `:` | src/primitives.fth:26 | 2 |  |
| 829 | `gen/mod` | определение `:` | src/primitives.fth:27 | 2 |  |
| 830 | `gen-dup` | определение `:` | src/primitives.fth:28 | 2 |  |
| 831 | `gen-drop` | определение `:` | src/primitives.fth:29 | 2 |  |
| 832 | `gen-swap` | определение `:` | src/primitives.fth:30 | 2 |  |
| 833 | `gen-over` | определение `:` | src/primitives.fth:31 | 2 |  |
| 834 | `gen-rot` | определение `:` | src/primitives.fth:32 | 2 |  |
| 835 | `gen-pick` | определение `:` | src/primitives.fth:33 | 2 |  |
| 836 | `gen-roll` | определение `:` | src/primitives.fth:34 | 2 |  |
| 837 | `gen->r` | определение `:` | src/primitives.fth:35 | 2 |  |
| 838 | `gen-r>` | определение `:` | src/primitives.fth:36 | 2 |  |
| 839 | `gen-r@` | определение `:` | src/primitives.fth:37 | 4 |  |
| 840 | `gen-j` | определение `:` | src/primitives.fth:38 | 2 |  |
| 841 | `gen-@` | определение `:` | src/primitives.fth:39 | 2 |  |
| 842 | `gen-!` | определение `:` | src/primitives.fth:41 | 2 |  |
| 843 | `gen-c@` | определение `:` | src/primitives.fth:42 | 2 |  |
| 844 | `gen-c!` | определение `:` | src/primitives.fth:44 | 2 |  |
| 845 | `gen-emit` | определение `:` | src/primitives.fth:45 | 2 |  |
| 846 | `gen-key` | определение `:` | src/primitives.fth:48 | 2 |  |
| 847 | `gen-if` | определение `:` | src/primitives.fth:50 | 2 |  |
| 848 | `gen-else` | определение `:` | src/primitives.fth:51 | 2 |  |
| 849 | `gen-then` | определение `:` | src/primitives.fth:53 | 2 |  |
| 850 | `gen-begin` | определение `:` | src/primitives.fth:57 | 2 |  |
| 851 | `gen-until` | определение `:` | src/primitives.fth:58 | 2 |  |
| 852 | `gen-while` | определение `:` | src/primitives.fth:60 | 2 |  |
| 853 | `gen-repeat` | определение `:` | src/primitives.fth:61 | 2 |  |
| 854 | `gen-again` | определение `:` | src/primitives.fth:62 | 2 |  |
| 855 | `gen-do` | определение `:` | src/primitives.fth:63 | 2 |  |
| 856 | `fc-di` | переменная | src/primitives.fth:66 | 3 |  |
| 857 | `fc-dl` | переменная | src/primitives.fth:66 | 3 |  |
| 858 | `gen-?do` | определение `:` | src/primitives.fth:67 | 2 |  |
| 859 | `fc-lv` | переменная | src/primitives.fth:73 | 2 |  |
| 860 | `gen-loop` | определение `:` | src/primitives.fth:74 | 2 |  |
| 861 | `gen-leave` | определение `:` | src/primitives.fth:83 | 2 |  |
| 862 | `gen-unloop` | определение `:` | src/primitives.fth:86 | 2 |  |
| 863 | `gen-exit` | определение `:` | src/primitives.fth:87 | 2 |  |
| 864 | `gen-bye` | определение `:` | src/primitives.fth:90 | 2 |  |
| 865 | `gen-recurse` | определение `:` | src/primitives.fth:92 | 2 |  |
| 866 | `gen-tick` | определение `:` | src/primitives.fth:93 | 2 |  |
| 867 | `gen-call` | определение `:` | src/primitives.fth:99 | 3 |  |
| 868 | `gen-space!` | определение `:` | src/primitives.fth:100 | 2 |  |
| 869 | `gen-spacec!` | определение `:` | src/primitives.fth:101 | 2 |  |
| 870 | `gen-space@` | определение `:` | src/primitives.fth:102 | 2 |  |
| 871 | `gen-spacec@` | определение `:` | src/primitives.fth:103 | 2 |  |
| 872 | `gen-execute` | определение `:` | src/primitives.fth:104 | 2 |  |
| 873 | `fc-entry-cell` | определение `:` | src/primitives.fth:110 | 1 |  |
| 874 | `fc-concept` | определение `:` | src/primitives.fth:112 | 1 |  |
| 875 | `gen-colon` | определение `:` | src/primitives.fth:119 | 2 |  |
| 876 | `gen-semicolon` | определение `:` | src/primitives.fth:125 | 2 |  |
| 877 | `gen-variable` | определение `:` | src/primitives.fth:128 | 2 |  |
| 878 | `gen-create` | определение `:` | src/primitives.fth:129 | 2 |  |
| 879 | `gen-allot` | определение `:` | src/primitives.fth:130 | 2 |  |
| 880 | `gen-constant` | определение `:` | src/primitives.fth:131 | 2 |  |
| 881 | `gen-decimal` | определение `:` | src/primitives.fth:132 | 2 |  |
| 882 | `gen-kernel-layout` | определение `:` | src/primitives.fth:133 | 2 |  |
| 883 | `gen-backslash` | определение `:` | src/primitives.fth:134 | 2 |  |
| 884 | `gen-paren` | определение `:` | src/primitives.fth:136 | 4 |  |
| 885 | `gen-char` | определение `:` | src/primitives.fth:137 | 2 |  |
| 886 | `gen-string` | определение `:` | src/primitives.fth:138 | 2 |  |
| 887 | `fc-digit@` | определение `:` | src/primitives.fth:141 | 1 |  |
| 888 | `gen-literal` | определение `:` | src/primitives.fth:143 | 2 |  |
| 889 | `fc-known-xt` | определение `:` | src/primitives.fth:150 | 2 |  |
| 890 | `gen-cost` | определение `:` | src/primitives.fth:151 | 2 |  |
| 891 | `gen-proved?` | определение `:` | src/primitives.fth:153 | 2 |  |
| 892 | `gen-library` | определение `:` | src/primitives.fth:154 | 16 |  |
| 893 | `gen-price` | определение `:` | src/primitives.fth:155 | 2 |  |
| 894 | `fc-cpos` | переменная | src/primitives.fth:160 | 4 |  |
| 895 | `fc-hn` | переменная | src/primitives.fth:160 | 2 |  |
| 896 | `fc-cdepth` | переменная | src/primitives.fth:160 | 4 |  |
| 897 | `fc-hname` | данные `create` | src/primitives.fth:160 | 2 |  |
| 898 | `fc-hb` | определение `:` | src/primitives.fth:161 | 3 |  |
| 899 | `fc-c,` | определение `:` | src/primitives.fth:162 | 17 |  |
| 900 | `fc-c1` | определение `:` | src/primitives.fth:163 | 8 |  |
| 901 | `fc-c-gen` | определение `:` | src/primitives.fth:164 | 1 |  |
| 902 | `fc-c-body` | определение `:` | src/primitives.fth:168 | 1 |  |
| 903 | `gen-host` | определение `:` | src/primitives.fth:177 | 2 |  |
| 904 | `fc-name2` | определение `:` | src/primitives.fth:194 | 1 |  |
| 905 | `fc-generators` | определение `:` | src/primitives.fth:197 | 1 |  |
| 906 | `+` | генератор | src/primitives.fth:198 | 589 | слово компилятора `gen+` |
| 907 | `-` | генератор | src/primitives.fth:198 | 71 | слово компилятора `gen-` |
| 908 | `*` | генератор | src/primitives.fth:199 | 80 | слово компилятора `gen*` |
| 909 | `/` | генератор | src/primitives.fth:199 | 4 | слово компилятора `gen/` |
| 910 | `mod` | генератор | src/primitives.fth:200 | 2 | слово компилятора `gen-mod` |
| 911 | `and` | генератор | src/primitives.fth:201 | 136 | слово компилятора `gen-and` |
| 912 | `or` | генератор | src/primitives.fth:201 | 45 | слово компилятора `gen-or` |
| 913 | `xor` | генератор | src/primitives.fth:202 | 5 | слово компилятора `gen-xor` |
| 914 | `lshift` | генератор | src/primitives.fth:202 | 104 | слово компилятора `gen-lshift` |
| 915 | `rshift` | генератор | src/primitives.fth:203 | 66 | слово компилятора `gen-rshift` |
| 916 | `=` | генератор | src/primitives.fth:203 | 97 | слово компилятора `gen=` |
| 917 | `<` | генератор | src/primitives.fth:204 | 24 | слово компилятора `gen<` |
| 918 | `u<` | генератор | src/primitives.fth:204 | 36 | слово компилятора `gen-u<` |
| 919 | `0=` | генератор | src/primitives.fth:205 | 123 | слово компилятора `gen-0=` |
| 920 | `2*` | генератор | src/primitives.fth:205 | 29 | слово компилятора `gen-2*` |
| 921 | `1+` | генератор | src/primitives.fth:206 | 47 | слово компилятора `gen-1+` |
| 922 | `1-` | генератор | src/primitives.fth:206 | 60 | слово компилятора `gen-1-` |
| 923 | `cells` | генератор | src/primitives.fth:207 | 280 | слово компилятора `gen-cells` |
| 924 | `cell+` | генератор | src/primitives.fth:207 | 56 | слово компилятора `gen-cell+` |
| 925 | `dup` | генератор | src/primitives.fth:208 | 308 | слово компилятора `gen-dup` |
| 926 | `drop` | генератор | src/primitives.fth:208 | 211 | слово компилятора `gen-drop` |
| 927 | `swap` | генератор | src/primitives.fth:209 | 141 | слово компилятора `gen-swap` |
| 928 | `over` | генератор | src/primitives.fth:209 | 87 | слово компилятора `gen-over` |
| 929 | `rot` | генератор | src/primitives.fth:210 | 39 | слово компилятора `gen-rot` |
| 930 | `pick` | генератор | src/primitives.fth:210 | 45 | слово компилятора `gen-pick` |
| 931 | `roll` | генератор | src/primitives.fth:211 | 7 | слово компилятора `gen-roll` |
| 932 | `>r` | генератор | src/primitives.fth:211 | 108 | слово компилятора `gen->r` |
| 933 | `r>` | генератор | src/primitives.fth:212 | 112 | слово компилятора `gen-r>` |
| 934 | `r@` | генератор | src/primitives.fth:212 | 108 | слово компилятора `gen-r@` |
| 935 | `i` | генератор | src/primitives.fth:213 | 181 | слово компилятора `gen-r@` |
| 936 | `j` | генератор | src/primitives.fth:213 | 12 | слово компилятора `gen-j` |
| 937 | `@` | генератор | src/primitives.fth:214 | 1345 | слово компилятора `gen-@` |
| 938 | `!` | генератор | src/primitives.fth:214 | 685 | слово компилятора `gen-!` |
| 939 | `c@` | генератор | src/primitives.fth:215 | 23 | слово компилятора `gen-c@` |
| 940 | `c!` | генератор | src/primitives.fth:215 | 18 | слово компилятора `gen-c!` |
| 941 | `space!` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-space!` |
| 942 | `spacec!` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-spacec!` |
| 943 | `space@` | генератор | src/primitives.fth:217 | 1 | слово компилятора `gen-space@` |
| 944 | `emit` | генератор | src/primitives.fth:218 | 4 | слово компилятора `gen-emit` |
| 945 | `key` | генератор | src/primitives.fth:218 | 1 | слово компилятора `gen-key` |
| 946 | `if` | генератор | src/primitives.fth:219 | 324 | слово компилятора `gen-if` |
| 947 | `else` | генератор | src/primitives.fth:219 | 88 | слово компилятора `gen-else` |
| 948 | `then` | генератор | src/primitives.fth:220 | 324 | слово компилятора `gen-then` |
| 949 | `begin` | генератор | src/primitives.fth:220 | 25 | слово компилятора `gen-begin` |
| 950 | `until` | генератор | src/primitives.fth:221 | 2 | слово компилятора `gen-until` |
| 951 | `while` | генератор | src/primitives.fth:221 | 22 | слово компилятора `gen-while` |
| 952 | `repeat` | генератор | src/primitives.fth:222 | 22 | слово компилятора `gen-repeat` |
| 953 | `again` | генератор | src/primitives.fth:222 | 1 | слово компилятора `gen-again` |
| 954 | `do` | генератор | src/primitives.fth:223 | 35 | слово компилятора `gen-do` |
| 955 | `?do` | генератор | src/primitives.fth:223 | 60 | слово компилятора `gen-?do` |
| 956 | `loop` | генератор | src/primitives.fth:224 | 95 | слово компилятора `gen-loop` |
| 957 | `leave` | генератор | src/primitives.fth:224 | 1 | слово компилятора `gen-leave` |
| 958 | `unloop` | генератор | src/primitives.fth:225 | 7 | слово компилятора `gen-unloop` |
| 959 | `exit` | генератор | src/primitives.fth:225 | 94 | слово компилятора `gen-exit` |
| 960 | `bye` | генератор | src/primitives.fth:226 | 1 | слово компилятора `gen-bye` |
| 961 | `recurse` | генератор | src/primitives.fth:227 | 2 | слово компилятора `gen-recurse` |
| 962 | `execute` | генератор | src/primitives.fth:227 | 10 | слово компилятора `gen-execute` |
| 963 | `[']` | генератор | src/primitives.fth:228 | 119 | слово компилятора `gen-tick` |
| 964 | `:` | генератор | src/primitives.fth:229 | 506 | слово компилятора `gen-colon` |
| 965 | `;` | генератор | src/primitives.fth:229 | 506 | слово компилятора `gen-semicolon` |
| 966 | `variable` | генератор | src/primitives.fth:230 | 336 | слово компилятора `gen-variable` |
| 967 | `create` | генератор | src/primitives.fth:230 | 63 | слово компилятора `gen-create` |
| 968 | `allot` | генератор | src/primitives.fth:231 | 63 | слово компилятора `gen-allot` |
| 969 | `constant` | генератор | src/primitives.fth:231 | 29 | слово компилятора `gen-constant` |
| 970 | `decimal` | генератор | src/primitives.fth:232 | 3 | слово компилятора `gen-decimal` |
| 971 | `kernel-layout` | генератор | src/primitives.fth:232 | 1 | слово компилятора `gen-kernel-layout` |
| 972 | `\` | генератор | src/primitives.fth:233 | 192 | слово компилятора `gen-backslash` |
| 973 | `(` | генератор | src/primitives.fth:233 | 485 | слово компилятора `gen-paren` |
| 974 | `[char]` | генератор | src/primitives.fth:233 | 8 | слово компилятора `gen-char` |
| 975 | `s"` | генератор | src/primitives.fth:234 | 224 | слово компилятора `gen-string` |
| 976 | `literal` | генератор | src/primitives.fth:235 | 515 | слово компилятора `gen-literal` |
| 977 | `0` | цифра (литерал) | src/primitives.fth:243 | 569 | значение 0 |
| 978 | `1` | цифра (литерал) | src/primitives.fth:243 | 487 | значение 1 |
| 979 | `2` | цифра (литерал) | src/primitives.fth:243 | 476 | значение 2 |
| 980 | `3` | цифра (литерал) | src/primitives.fth:243 | 311 | значение 3 |
| 981 | `4` | цифра (литерал) | src/primitives.fth:244 | 242 | значение 4 |
| 982 | `5` | цифра (литерал) | src/primitives.fth:244 | 112 | значение 5 |
| 983 | `6` | цифра (литерал) | src/primitives.fth:244 | 169 | значение 6 |
| 984 | `7` | цифра (литерал) | src/primitives.fth:244 | 75 | значение 7 |
| 985 | `8` | цифра (литерал) | src/primitives.fth:245 | 163 | значение 8 |
| 986 | `9` | цифра (литерал) | src/primitives.fth:245 | 43 | значение 9 |
| 987 | `fc-install-generators` | определение `:` | src/primitives.fth:246 | 1 |  |
| 988 | `fc-read` | определение `:` | src/main.fth:3 | 2 |  |
| 989 | `fc-sizes` | определение `:` | src/main.fth:8 | 2 |  |
| 990 | `kn-at` | переменная | src/kernel.fth:7 | 5 |  |
| 991 | `kn-put` | определение `:` | src/kernel.fth:8 | 1 |  |
| 992 | `kn-order` | определение `:` | src/kernel.fth:16 | 1 |  |
| 993 | `kn-get` | определение `:` | src/kernel.fth:18 | 1 |  |
| 994 | `kn-compile` | определение `:` | src/kernel.fth:19 | 1 |  |
| 995 | `main` | определение `:` | src/kernel.fth:25 | 1 | вариант 2 |

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
