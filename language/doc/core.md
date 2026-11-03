# Ядро языка (14.8)

Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 978** (определение `:` — 478, переменная — 324, генератор — 71, данные `create` — 62, константа — 27, цифра (литерал) — 10, основание — 6).

## Основание

Основание — слова-копирования: генераторы строки (копия — приёмник и источник) и слоя (ячейка строк) из `src/backend.fth`. Определение инструкции — она сама: тело этих слов не сводится к другим словам языка, а строка и слой — сами инструкции индексного пространства.

| Слово | Что порождает | Файл:строка |
|---|---|---|
| `lay-copy` | строка: копирование n бит из источника в приёмник | src/backend.fth:114 |
| `lay-link-row` | строка: копирование ссылки на следующий слой | src/backend.fth:113 |
| `lay-row` | строка: добавляет строку в слой | src/backend.fth:177 |
| `lay-new-record` | слой: новый слой в ячейке | src/backend.fth:140 |
| `lay-lone` | слой: отдельный слой в новой ячейке | src/backend.fth:144 |
| `lay-layer` | слой: следующий слой последовательности | src/backend.fth:147 |

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
| 54 | `lay-rec` | константа | src/backend.fth:32 | 3 |  |
| 55 | `lay-hdr` | константа | src/backend.fth:32 | 3 |  |
| 56 | `lay-cap` | константа | src/backend.fth:32 | 5 |  |
| 57 | `lay-req` | определение `:` | src/backend.fth:33 | 7 |  |
| 58 | `lay-bits` | определение `:` | src/backend.fth:34 | 7 |  |
| 59 | `lay-numeric` | определение `:` | src/backend.fth:35 | 7 |  |
| 60 | `lay-numeric4` | определение `:` | src/backend.fth:40 | 1 |  |
| 61 | `lay-field-check` | определение `:` | src/backend.fth:43 | 1 |  |
| 62 | `lay-encode` | определение `:` | src/backend.fth:45 | 3 |  |
| 63 | `lay-start` | переменная | src/backend.fth:55 | 8 |  |
| 64 | `lay-len` | переменная | src/backend.fth:55 | 10 |  |
| 65 | `lay-rows` | данные `create` | src/backend.fth:56 | 6 |  |
| 66 | `lay-row!` | определение `:` | src/backend.fth:57 | 7 |  |
| 67 | `lay-clear-rows` | определение `:` | src/backend.fth:59 | 3 |  |
| 68 | `lay-loader` | определение `:` | src/backend.fth:60 | 1 |  |
| 69 | `lay-stream-flush` | определение `:` | src/backend.fth:67 | 3 |  |
| 70 | `lay-begin-chunk` | определение `:` | src/backend.fth:71 | 2 |  |
| 71 | `lay-put` | определение `:` | src/backend.fth:73 | 13 |  |
| 72 | `lay-scratch` | данные `create` | src/backend.fth:91 | 2 |  |
| 73 | `lay-put-numeric` | определение `:` | src/backend.fth:92 | 3 |  |
| 74 | `lay-max-layers` | константа | src/backend.fth:96 | 3 |  |
| 75 | `lay-record` | определение `:` | src/backend.fth:97 | 1 |  |
| 76 | `lay-pending` | переменная | src/backend.fth:98 | 10 |  |
| 77 | `lay-head` | переменная | src/backend.fth:98 | 6 |  |
| 78 | `lay-next-cell` | переменная | src/backend.fth:98 | 8 |  |
| 79 | `lay-seq#` | переменная | src/backend.fth:99 | 8 |  |
| 80 | `lay-seq-first` | переменная | src/backend.fth:99 | 3 |  |
| 81 | `lay-seq-entry` | переменная | src/backend.fth:99 | 2 |  |
| 82 | `lay-seq-last` | переменная | src/backend.fth:99 | 2 |  |
| 83 | `lay-foff` | данные `create` | src/backend.fth:100 | 2 |  |
| 84 | `lay-foff-init` | определение `:` | src/backend.fth:101 | 1 |  |
| 85 | `lay-chunk-mem` | данные `create` | src/backend.fth:103 | 1 |  |
| 86 | `lay-lbuf-mem` | данные `create` | src/backend.fth:103 | 1 |  |
| 87 | `lay-ebuf-mem` | данные `create` | src/backend.fth:103 | 1 |  |
| 88 | `lay-pool-mem` | данные `create` | src/backend.fth:104 | 1 |  |
| 89 | `lay-bufs` | определение `:` | src/backend.fth:105 | 1 |  |
| 90 | `lay-machine` | определение `:` | src/backend.fth:106 | 1 |  |
| 91 | `lay-field` | определение `:` | src/backend.fth:112 | 48 |  |
| 92 | `lay-link-row` | основание | src/backend.fth:113 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 93 | `lay-copy` | основание | src/backend.fth:114 | 79 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 94 | `lay-builder` | определение `:` | src/backend.fth:116 | 1 |  |
| 95 | `lay-new-cell` | определение `:` | src/backend.fth:117 | 10 |  |
| 96 | `lay-branch-bit` | определение `:` | src/backend.fth:119 | 20 |  |
| 97 | `lay-branch-step` | определение `:` | src/backend.fth:120 | 3 |  |
| 98 | `lay-group` | определение `:` | src/backend.fth:121 | 5 |  |
| 99 | `lay-layer-cell` | определение `:` | src/backend.fth:124 | 48 |  |
| 100 | `lay-next!` | определение `:` | src/backend.fth:125 | 19 |  |
| 101 | `lay-count` | определение `:` | src/backend.fth:126 | 7 |  |
| 102 | `lay-row-addr` | определение `:` | src/backend.fth:127 | 4 |  |
| 103 | `lay-pending@` | определение `:` | src/backend.fth:128 | 5 |  |
| 104 | `lay-encode-layer` | определение `:` | src/backend.fth:129 | 1 |  |
| 105 | `lay-on-write` | переменная | src/backend.fth:135 | 6 |  |
| 106 | `lay-write` | определение `:` | src/backend.fth:136 | 2 |  |
| 107 | `lay-write-oldest` | определение `:` | src/backend.fth:139 | 1 |  |
| 108 | `lay-new-record` | основание | src/backend.fth:140 | 8 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 109 | `lay-lone` | основание | src/backend.fth:144 | 7 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 110 | `lay-seq` | определение `:` | src/backend.fth:145 | 8 |  |
| 111 | `lay-last` | определение `:` | src/backend.fth:146 | 4 |  |
| 112 | `lay-layer` | основание | src/backend.fth:147 | 89 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 113 | `lay-entry` | определение `:` | src/backend.fth:152 | 3 |  |
| 114 | `lay-jump` | определение `:` | src/backend.fth:153 | 10 |  |
| 115 | `lay-l1` | переменная | src/backend.fth:154 | 4 |  |
| 116 | `lay-h1` | переменная | src/backend.fth:154 | 3 |  |
| 117 | `lay-l2` | переменная | src/backend.fth:154 | 4 |  |
| 118 | `lay-h2` | переменная | src/backend.fth:154 | 3 |  |
| 119 | `lay-ra` | переменная | src/backend.fth:155 | 2 |  |
| 120 | `lay-rb` | переменная | src/backend.fth:155 | 2 |  |
| 121 | `lay-cur` | переменная | src/backend.fth:155 | 7 |  |
| 122 | `lay-clash?` | определение `:` | src/backend.fth:157 | 1 |  |
| 123 | `lay-row-clash?` | определение `:` | src/backend.fth:162 | 1 |  |
| 124 | `lay-new-row` | данные `create` | src/backend.fth:167 | 6 |  |
| 125 | `lay-row-set` | определение `:` | src/backend.fth:168 | 2 |  |
| 126 | `lay-full?` | определение `:` | src/backend.fth:170 | 2 |  |
| 127 | `lay-clashes?` | определение `:` | src/backend.fth:171 | 2 |  |
| 128 | `lay-fits?` | определение `:` | src/backend.fth:175 | 2 |  |
| 129 | `lay-row` | основание | src/backend.fth:177 | 88 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 130 | `lay-flush` | определение `:` | src/backend.fth:181 | 14 |  |
| 131 | `lay-finish` | определение `:` | src/backend.fth:184 | 1 |  |
| 132 | `dj-reader` | переменная | src/backend.fth:202 | 3 |  |
| 133 | `dj-bad-cell` | переменная | src/backend.fth:202 | 1 |  |
| 134 | `dj-bad-rule` | переменная | src/backend.fth:202 | 4 |  |
| 135 | `dj-bsh` | переменная | src/backend.fth:203 | 3 |  |
| 136 | `dj-csh` | переменная | src/backend.fth:203 | 6 |  |
| 137 | `dj-ssh` | переменная | src/backend.fth:203 | 2 |  |
| 138 | `dj-fsh` | переменная | src/backend.fth:203 | 2 |  |
| 139 | `dj-first` | переменная | src/backend.fth:204 | 2 |  |
| 140 | `dj-end` | переменная | src/backend.fth:204 | 2 |  |
| 141 | `dj-pa` | переменная | src/backend.fth:204 | 3 |  |
| 142 | `dj-cb` | переменная | src/backend.fth:204 | 8 |  |
| 143 | `dj-vdl` | переменная | src/backend.fth:205 | 19 |  |
| 144 | `dj-vdh` | переменная | src/backend.fth:205 | 14 |  |
| 145 | `dj-vsl` | переменная | src/backend.fth:205 | 18 |  |
| 146 | `dj-vsh` | переменная | src/backend.fth:205 | 15 |  |
| 147 | `dj-tc` | переменная | src/backend.fth:206 | 5 |  |
| 148 | `dj-ts` | переменная | src/backend.fth:206 | 6 |  |
| 149 | `dj-tf` | переменная | src/backend.fth:206 | 5 |  |
| 150 | `dj-tb` | переменная | src/backend.fth:206 | 2 |  |
| 151 | `dj-tn` | переменная | src/backend.fth:206 | 2 |  |
| 152 | `dj-tk` | переменная | src/backend.fth:206 | 7 |  |
| 153 | `dj-vt` | переменная | src/backend.fth:206 | 3 |  |
| 154 | `dj-blk` | переменная | src/backend.fth:207 | 5 |  |
| 155 | `dj-hb` | переменная | src/backend.fth:207 | 5 |  |
| 156 | `dj-he` | переменная | src/backend.fth:207 | 3 |  |
| 157 | `dj-pr` | данные `create` | src/backend.fth:208 | 2 |  |
| 158 | `dj-tr` | данные `create` | src/backend.fth:208 | 3 |  |
| 159 | `dj-narrow` | константа | src/backend.fth:209 | 1 |  |
| 160 | `dj-seen` | данные `create` | src/backend.fth:210 | 2 |  |
| 161 | `dj-nseen` | переменная | src/backend.fth:210 | 6 |  |
| 162 | `dj-get` | определение `:` | src/backend.fth:211 | 10 |  |
| 163 | `dj-fail` | определение `:` | src/backend.fth:212 | 8 |  |
| 164 | `dj-blk?` | определение `:` | src/backend.fth:213 | 7 |  |
| 165 | `dj-in?` | определение `:` | src/backend.fth:214 | 4 |  |
| 166 | `dj-row!` | определение `:` | src/backend.fth:217 | 2 |  |
| 167 | `dj-row@` | определение `:` | src/backend.fth:219 | 3 |  |
| 168 | `dj-nop?` | определение `:` | src/backend.fth:221 | 4 |  |
| 169 | `dj-load` | определение `:` | src/backend.fth:222 | 1 |  |
| 170 | `dj-sys?` | определение `:` | src/backend.fth:230 | 1 |  |
| 171 | `dj-head?` | определение `:` | src/backend.fth:232 | 1 |  |
| 172 | `dj-row-ok?` | определение `:` | src/backend.fth:235 | 1 |  |
| 173 | `dj-in-blk?` | определение `:` | src/backend.fth:244 | 2 |  |
| 174 | `dj-touches?` | определение `:` | src/backend.fth:248 | 1 |  |
| 175 | `dj-seen?` | определение `:` | src/backend.fth:249 | 1 |  |
| 176 | `dj-seen!` | определение `:` | src/backend.fth:254 | 1 |  |
| 177 | `dj-wide` | определение `:` | src/backend.fth:258 | 1 |  |
| 178 | `dj-patch` | определение `:` | src/backend.fth:274 | 1 |  |
| 179 | `dj-nn` | переменная | src/backend.fth:284 | 4 |  |
| 180 | `dj-lo` | переменная | src/backend.fth:284 | 2 |  |
| 181 | `dj-hi` | переменная | src/backend.fth:284 | 2 |  |
| 182 | `dj-scan` | определение `:` | src/backend.fth:285 | 1 |  |
| 183 | `dj-rows` | определение `:` | src/backend.fth:294 | 1 |  |
| 184 | `dj-prove` | определение `:` | src/backend.fth:301 | 3 |  |
| 185 | `lay-t1` | переменная | src/compute.fth:7 | 25 |  |
| 186 | `lay-t2` | переменная | src/compute.fth:7 | 13 |  |
| 187 | `lay-t3` | переменная | src/compute.fth:7 | 7 |  |
| 188 | `lay-t4` | переменная | src/compute.fth:7 | 4 |  |
| 189 | `lay-t5` | переменная | src/compute.fth:7 | 8 |  |
| 190 | `lay-lo` | переменная | src/compute.fth:8 | 5 |  |
| 191 | `lay-hi` | переменная | src/compute.fth:8 | 2 |  |
| 192 | `lay-l0` | переменная | src/compute.fth:9 | 21 |  |
| 193 | `lay-l1` | переменная | src/compute.fth:9 | 13 | вариант 2 |
| 194 | `lay-l2` | переменная | src/compute.fth:9 | 8 | вариант 2 |
| 195 | `lay-l3` | переменная | src/compute.fth:9 | 7 |  |
| 196 | `lay-l4` | переменная | src/compute.fth:9 | 7 |  |
| 197 | `lay-l5` | переменная | src/compute.fth:9 | 6 |  |
| 198 | `lay-work` | определение `:` | src/compute.fth:10 | 3 |  |
| 199 | `lay-cell-bit` | определение `:` | src/compute.fth:11 | 3 |  |
| 200 | `lay-link-slot` | определение `:` | src/compute.fth:12 | 6 |  |
| 201 | `lay-item-cells` | константа | src/compute.fth:13 | 1 |  |
| 202 | `lay-max-items` | константа | src/compute.fth:13 | 2 |  |
| 203 | `lay-items` | данные `create` | src/compute.fth:14 | 1 |  |
| 204 | `lay-nitems` | переменная | src/compute.fth:15 | 8 |  |
| 205 | `lay-item@` | определение `:` | src/compute.fth:16 | 6 |  |
| 206 | `lay-lookups-begin` | определение `:` | src/compute.fth:17 | 12 |  |
| 207 | `lay-item` | определение `:` | src/compute.fth:18 | 11 |  |
| 208 | `lay-seg` | определение `:` | src/compute.fth:23 | 17 |  |
| 209 | `lay-sl` | данные `create` | src/compute.fth:29 | 2 |  |
| 210 | `lay-sh` | данные `create` | src/compute.fth:29 | 2 |  |
| 211 | `lay-read-layer` | данные `create` | src/compute.fth:30 | 2 |  |
| 212 | `lay-read-slot` | данные `create` | src/compute.fth:30 | 2 |  |
| 213 | `lay-used` | данные `create` | src/compute.fth:31 | 2 |  |
| 214 | `lay-nused` | переменная | src/compute.fth:31 | 5 |  |
| 215 | `lay-rl` | переменная | src/compute.fth:31 | 6 |  |
| 216 | `lay-pk` | переменная | src/compute.fth:31 | 4 |  |
| 217 | `lay-pkl` | переменная | src/compute.fth:31 | 4 |  |
| 218 | `lay-npatches` | определение `:` | src/compute.fth:32 | 1 |  |
| 219 | `lay-used?` | определение `:` | src/compute.fth:33 | 1 |  |
| 220 | `lay-place-reads` | определение `:` | src/compute.fth:35 | 1 |  |
| 221 | `lay-patch` | определение `:` | src/compute.fth:47 | 1 |  |
| 222 | `lay-lookups` | определение `:` | src/compute.fth:56 | 12 |  |
| 223 | `lay-al` | данные `create` | src/compute.fth:62 | 2 |  |
| 224 | `lay-ar` | данные `create` | src/compute.fth:62 | 2 |  |
| 225 | `lay-ax` | переменная | src/compute.fth:63 | 4 |  |
| 226 | `lay-aa` | переменная | src/compute.fth:63 | 2 |  |
| 227 | `lay-ab` | переменная | src/compute.fth:63 | 2 |  |
| 228 | `lay-atab` | переменная | src/compute.fth:63 | 2 |  |
| 229 | `lay-acarry` | переменная | src/compute.fth:63 | 2 |  |
| 230 | `lay-al@` | определение `:` | src/compute.fth:64 | 8 |  |
| 231 | `lay-rd` | определение `:` | src/compute.fth:65 | 3 |  |
| 232 | `lay-adder-patch` | определение `:` | src/compute.fth:66 | 4 |  |
| 233 | `lay-adder` | определение `:` | src/compute.fth:71 | 6 |  |
| 234 | `lay-dsrc` | переменная | src/compute.fth:87 | 3 |  |
| 235 | `lay-dk` | переменная | src/compute.fth:87 | 5 |  |
| 236 | `lay-dg` | переменная | src/compute.fth:87 | 3 |  |
| 237 | `lay-dp` | переменная | src/compute.fth:87 | 3 |  |
| 238 | `lay-dx` | переменная | src/compute.fth:87 | 4 |  |
| 239 | `lay-decide` | определение `:` | src/compute.fth:88 | 2 |  |
| 240 | `lay-table-at` | переменная | src/compute.fth:95 | 4 |  |
| 241 | `lay-table-limit` | переменная | src/compute.fth:95 | 2 |  |
| 242 | `lay-tbuf` | переменная | src/compute.fth:95 | 6 |  |
| 243 | `lay-tx` | переменная | src/compute.fth:96 | 5 |  |
| 244 | `lay-tbits` | переменная | src/compute.fth:96 | 4 |  |
| 245 | `lay-ts` | переменная | src/compute.fth:96 | 6 |  |
| 246 | `lay-tsize` | переменная | src/compute.fth:96 | 6 |  |
| 247 | `lay-tbase` | переменная | src/compute.fth:96 | 4 |  |
| 248 | `lay-tper` | переменная | src/compute.fth:96 | 3 |  |
| 249 | `lay-tables` | определение `:` | src/compute.fth:97 | 2 |  |
| 250 | `lay-table-mem` | данные `create` | src/compute.fth:99 | 1 |  |
| 251 | `lay-table-area` | определение `:` | src/compute.fth:100 | 2 |  |
| 252 | `lay-table-done` | определение `:` | src/compute.fth:108 | 2 |  |
| 253 | `lay-table` | определение `:` | src/compute.fth:110 | 23 |  |
| 254 | `lay-add-entry` | определение `:` | src/compute.fth:127 | 1 |  |
| 255 | `lay-sub-entry` | определение `:` | src/compute.fth:129 | 2 |  |
| 256 | `lay-xor-entry` | определение `:` | src/compute.fth:131 | 1 |  |
| 257 | `lay-or-entry` | определение `:` | src/compute.fth:132 | 1 |  |
| 258 | `lay-and-entry` | определение `:` | src/compute.fth:133 | 1 |  |
| 259 | `lay-or8-entry` | определение `:` | src/compute.fth:134 | 1 |  |
| 260 | `lay-fz` | переменная | src/compute.fth:135 | 3 |  |
| 261 | `lay-fu` | переменная | src/compute.fth:135 | 4 |  |
| 262 | `lay-fs` | переменная | src/compute.fth:135 | 3 |  |
| 263 | `lay-pair` | определение `:` | src/compute.fth:136 | 6 |  |
| 264 | `lay-flags-entry` | определение `:` | src/compute.fth:137 | 1 |  |
| 265 | `lay-not5-entry` | определение `:` | src/compute.fth:144 | 1 |  |
| 266 | `lay-sign-entry` | определение `:` | src/compute.fth:145 | 1 |  |
| 267 | `lay-fill24-entry` | определение `:` | src/compute.fth:146 | 1 |  |
| 268 | `lay-fill16-entry` | определение `:` | src/compute.fth:147 | 1 |  |
| 269 | `lay-inc1-entry` | определение `:` | src/compute.fth:148 | 1 |  |
| 270 | `lay-inc2-entry` | определение `:` | src/compute.fth:149 | 1 |  |
| 271 | `lay-t-add` | переменная | src/compute.fth:150 | 7 |  |
| 272 | `lay-t-sub` | переменная | src/compute.fth:150 | 5 |  |
| 273 | `lay-t-xor` | переменная | src/compute.fth:150 | 5 |  |
| 274 | `lay-t-or` | переменная | src/compute.fth:150 | 2 |  |
| 275 | `lay-t-and` | переменная | src/compute.fth:150 | 2 |  |
| 276 | `lay-t-or8` | переменная | src/compute.fth:151 | 2 |  |
| 277 | `lay-t-flags` | переменная | src/compute.fth:151 | 2 |  |
| 278 | `lay-t-not5` | переменная | src/compute.fth:151 | 2 |  |
| 279 | `lay-t-sign32` | переменная | src/compute.fth:151 | 2 |  |
| 280 | `lay-t-fill24` | переменная | src/compute.fth:152 | 1 |  |
| 281 | `lay-t-fill16` | переменная | src/compute.fth:152 | 1 |  |
| 282 | `lay-t-inc1` | переменная | src/compute.fth:152 | 1 |  |
| 283 | `lay-t-inc2` | переменная | src/compute.fth:152 | 1 |  |
| 284 | `lay-standard-tables` | определение `:` | src/compute.fth:153 | 1 |  |
| 285 | `lay-oo` | переменная | src/compute.fth:161 | 2 |  |
| 286 | `lay-os` | переменная | src/compute.fth:161 | 2 |  |
| 287 | `lay-ol` | переменная | src/compute.fth:161 | 4 |  |
| 288 | `lay-oh` | переменная | src/compute.fth:161 | 3 |  |
| 289 | `lay-or-chunks` | определение `:` | src/compute.fth:162 | 3 |  |
| 290 | `lay-cr` | переменная | src/compute.fth:168 | 5 |  |
| 291 | `lay-ca` | переменная | src/compute.fth:168 | 4 |  |
| 292 | `lay-cb` | переменная | src/compute.fth:168 | 4 |  |
| 293 | `lay-logic` | определение `:` | src/compute.fth:175 | 4 |  |
| 294 | `lay-sres` | переменная | src/compute.fth:181 | 3 |  |
| 295 | `lay-sa` | переменная | src/compute.fth:181 | 7 |  |
| 296 | `lay-samt` | переменная | src/compute.fth:181 | 8 |  |
| 297 | `lay-sw` | переменная | src/compute.fth:181 | 9 |  |
| 298 | `lay-szero` | переменная | src/compute.fth:181 | 4 |  |
| 299 | `lay-sarg` | переменная | src/compute.fth:182 | 6 |  |
| 300 | `lay-sign` | переменная | src/compute.fth:182 | 6 |  |
| 301 | `lay-shift-row` | определение `:` | src/compute.fth:183 | 3 |  |
| 302 | `lay-shift-patch` | определение `:` | src/compute.fth:184 | 6 |  |
| 303 | `lay-shift-right` | определение `:` | src/compute.fth:186 | 1 |  |
| 304 | `lay-shift-left` | определение `:` | src/compute.fth:203 | 1 |  |
| 305 | `fc-size` | константа | src/forthc.fth:6 | 2 |  |
| 306 | `fc-cellb` | константа | src/forthc.fth:6 | 5 |  |
| 307 | `fc-l` | константа | src/forthc.fth:6 | 1 |  |
| 308 | `fc-a` | константа | src/forthc.fth:6 | 2 |  |
| 309 | `fc-d` | переменная | src/forthc.fth:8 | 3 |  |
| 310 | `fc-first` | переменная | src/forthc.fth:8 | 3 |  |
| 311 | `fc-guard` | переменная | src/forthc.fth:10 | 20 |  |
| 312 | `fc-bbits` | константа | src/forthc.fth:16 | 7 |  |
| 313 | `fc-abits` | константа | src/forthc.fth:16 | 5 |  |
| 314 | `fc-ebits` | константа | src/forthc.fth:16 | 6 |  |
| 315 | `fc-etab` | константа | src/forthc.fth:16 | 5 |  |
| 316 | `fc-rbits` | константа | src/forthc.fth:17 | 5 |  |
| 317 | `fc-rtab` | константа | src/forthc.fth:17 | 4 |  |
| 318 | `fc-layout` | определение `:` | src/forthc.fth:18 | 1 |  |
| 319 | `fc-d+` | определение `:` | src/forthc.fth:20 | 26 |  |
| 320 | `fc-sp` | определение `:` | src/forthc.fth:21 | 4 |  |
| 321 | `fc-rp` | определение `:` | src/forthc.fth:21 | 13 |  |
| 322 | `fc-code` | определение `:` | src/forthc.fth:21 | 1 |  |
| 323 | `fc-regs` | определение `:` | src/forthc.fth:22 | 2 |  |
| 324 | `fc-nregs` | константа | src/forthc.fth:22 | 2 |  |
| 325 | `fc-tmp` | определение `:` | src/forthc.fth:23 | 12 |  |
| 326 | `fc-xr` | определение `:` | src/forthc.fth:23 | 10 |  |
| 327 | `fc-z` | определение `:` | src/forthc.fth:23 | 4 |  |
| 328 | `fc-idx` | определение `:` | src/forthc.fth:23 | 5 |  |
| 329 | `fc-ma` | определение `:` | src/forthc.fth:24 | 6 |  |
| 330 | `fc-mb` | определение `:` | src/forthc.fth:24 | 6 |  |
| 331 | `fc-mp` | определение `:` | src/forthc.fth:24 | 2 |  |
| 332 | `fc-mq` | определение `:` | src/forthc.fth:24 | 3 |  |
| 333 | `fc-mr` | определение `:` | src/forthc.fth:24 | 3 |  |
| 334 | `fc-zero` | определение `:` | src/forthc.fth:25 | 12 |  |
| 335 | `fc-consts` | определение `:` | src/forthc.fth:25 | 3 |  |
| 336 | `fc-sw` | определение `:` | src/forthc.fth:26 | 2 |  |
| 337 | `fc-su` | определение `:` | src/forthc.fth:26 | 1 |  |
| 338 | `fc-key` | определение `:` | src/forthc.fth:26 | 3 |  |
| 339 | `fc-bp` | определение `:` | src/forthc.fth:26 | 2 |  |
| 340 | `fc-tab` | определение `:` | src/forthc.fth:27 | 1 |  |
| 341 | `fc-stk` | определение `:` | src/forthc.fth:27 | 3 |  |
| 342 | `fc-rstk` | определение `:` | src/forthc.fth:28 | 13 |  |
| 343 | `fc-scr0` | определение `:` | src/forthc.fth:28 | 1 |  |
| 344 | `fc-links` | определение `:` | src/forthc.fth:29 | 2 |  |
| 345 | `fc-max-links` | константа | src/forthc.fth:29 | 1 |  |
| 346 | `fc-link-chunk` | константа | src/forthc.fth:29 | 1 |  |
| 347 | `fc-mem` | определение `:` | src/forthc.fth:30 | 7 |  |
| 348 | `fc-mw` | константа | src/forthc.fth:30 | 2 |  |
| 349 | `fc-htab` | определение `:` | src/forthc.fth:30 | 1 |  |
| 350 | `fc-data-start` | константа | src/forthc.fth:31 | 1 |  |
| 351 | `fc-off` | данные `create` | src/forthc.fth:33 | 2 |  |
| 352 | `fc-oc` | переменная | src/forthc.fth:33 | 2 |  |
| 353 | `fc-t-rev8` | переменная | src/forthc.fth:34 | 3 |  |
| 354 | `fc-t-zero32` | переменная | src/forthc.fth:34 | 2 |  |
| 355 | `fc-t-nz2` | переменная | src/forthc.fth:34 | 2 |  |
| 356 | `fc-t-lt32` | переменная | src/forthc.fth:34 | 2 |  |
| 357 | `fc-t-xr2` | переменная | src/forthc.fth:35 | 2 |  |
| 358 | `fc-t-ult32` | переменная | src/forthc.fth:35 | 2 |  |
| 359 | `fc-t-bytepos` | переменная | src/forthc.fth:35 | 2 |  |
| 360 | `fc-off@` | определение `:` | src/forthc.fth:36 | 2 |  |
| 361 | `fc-off-table` | определение `:` | src/forthc.fth:37 | 1 |  |
| 362 | `fc-rev-entry` | определение `:` | src/forthc.fth:40 | 1 |  |
| 363 | `fc-zero-entry` | определение `:` | src/forthc.fth:41 | 1 |  |
| 364 | `fc-nz-entry` | определение `:` | src/forthc.fth:42 | 1 |  |
| 365 | `fc-lt-entry` | определение `:` | src/forthc.fth:43 | 1 |  |
| 366 | `fc-xr2-entry` | определение `:` | src/forthc.fth:46 | 1 |  |
| 367 | `fc-ult-entry` | определение `:` | src/forthc.fth:47 | 1 |  |
| 368 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 369 | `fc-tables` | определение `:` | src/forthc.fth:49 | 1 |  |
| 370 | `fc-mul4-entry` | определение `:` | src/forthc.fth:60 | 1 |  |
| 371 | `fc-qsel-entry` | определение `:` | src/forthc.fth:63 | 1 |  |
| 372 | `fc-max-consts` | переменная | src/forthc.fth:66 | 4 | вход бута (хост) |
| 373 | `fc-ck` | переменная | src/forthc.fth:66 | 3 |  |
| 374 | `fc-nconsts` | переменная | src/forthc.fth:66 | 7 |  |
| 375 | `fc-nbuckets` | переменная | src/forthc.fth:67 | 7 | вход бута (хост) |
| 376 | `fc-cbk` | переменная | src/forthc.fth:67 | 3 |  |
| 377 | `fc-ck@` | определение `:` | src/forthc.fth:68 | 3 |  |
| 378 | `fc-chash` | определение `:` | src/forthc.fth:69 | 1 |  |
| 379 | `fc-cb` | переменная | src/forthc.fth:70 | 3 |  |
| 380 | `fc-const2` | определение `:` | src/forthc.fth:71 | 1 |  |
| 381 | `fc-const` | определение `:` | src/forthc.fth:81 | 4 |  |
| 382 | `fc-lit` | определение `:` | src/forthc.fth:84 | 3 |  |
| 383 | `fc-bit0` | определение `:` | src/forthc.fth:85 | 1 |  |
| 384 | `fc-bit1` | определение `:` | src/forthc.fth:86 | 1 |  |
| 385 | `fc-length` | определение `:` | src/forthc.fth:87 | 1 |  |
| 386 | `fc-lit-of` | определение `:` | src/forthc.fth:88 | 1 |  |
| 387 | `fc-load` | определение `:` | src/forthc.fth:90 | 1 |  |
| 388 | `fc-nlinks` | переменная | src/forthc.fth:92 | 5 |  |
| 389 | `fc-link-buf` | переменная | src/forthc.fth:92 | 4 |  |
| 390 | `fc-nbuf` | переменная | src/forthc.fth:92 | 8 |  |
| 391 | `fc-put-links` | определение `:` | src/forthc.fth:93 | 2 |  |
| 392 | `fc-link-pair` | определение `:` | src/forthc.fth:97 | 2 |  |
| 393 | `fc-link-const` | определение `:` | src/forthc.fth:102 | 1 |  |
| 394 | `fc-eight` | данные `create` | src/forthc.fth:103 | 7 |  |
| 395 | `fc-zeros` | данные `create` | src/forthc.fth:103 | 4 |  |
| 396 | `fc-put-consts` | определение `:` | src/forthc.fth:104 | 1 |  |
| 397 | `fc-cache` | данные `create` | src/forthc.fth:111 | 8 |  |
| 398 | `fc-n` | переменная | src/forthc.fth:111 | 28 |  |
| 399 | `fc-pin` | данные `create` | src/forthc.fth:112 | 13 |  |
| 400 | `fc-npin` | переменная | src/forthc.fth:112 | 20 |  |
| 401 | `fc-c@` | определение `:` | src/forthc.fth:113 | 8 |  |
| 402 | `fc-push` | определение `:` | src/forthc.fth:114 | 28 |  |
| 403 | `fc-pop1` | определение `:` | src/forthc.fth:115 | 37 |  |
| 404 | `fc-in?` | определение `:` | src/forthc.fth:116 | 3 |  |
| 405 | `fc-reg` | определение `:` | src/forthc.fth:117 | 16 |  |
| 406 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:122 | 1 |  |
| 407 | `fc-scr` | переменная | src/forthc.fth:123 | 3 |  |
| 408 | `fc-scratch` | определение `:` | src/forthc.fth:124 | 11 |  |
| 409 | `fc-offs` | данные `create` | src/forthc.fth:127 | 5 |  |
| 410 | `fc-noff` | переменная | src/forthc.fth:127 | 9 |  |
| 411 | `fc-ptr` | переменная | src/forthc.fth:127 | 4 |  |
| 412 | `fc-iw` | переменная | src/forthc.fth:128 | 4 |  |
| 413 | `fc-adjust` | определение `:` | src/forthc.fth:129 | 7 |  |
| 414 | `fc-prow` | данные `create` | src/forthc.fth:135 | 2 |  |
| 415 | `fc-nrow` | переменная | src/forthc.fth:135 | 8 |  |
| 416 | `fc-pl` | данные `create` | src/forthc.fth:136 | 2 |  |
| 417 | `fc-pslot` | данные `create` | src/forthc.fth:136 | 2 |  |
| 418 | `fc-rl` | переменная | src/forthc.fth:137 | 3 |  |
| 419 | `fc-f0` | переменная | src/forthc.fth:137 | 2 |  |
| 420 | `fc-f1` | переменная | src/forthc.fth:137 | 2 |  |
| 421 | `fc-psh` | переменная | src/forthc.fth:137 | 2 |  |
| 422 | `fc-row+` | определение `:` | src/forthc.fth:138 | 3 |  |
| 423 | `fc-4@` | определение `:` | src/forthc.fth:140 | 3 |  |
| 424 | `fc-patched` | определение `:` | src/forthc.fth:141 | 3 |  |
| 425 | `fc-popped` | данные `create` | src/forthc.fth:152 | 2 |  |
| 426 | `fc-srcs` | данные `create` | src/forthc.fth:152 | 13 |  |
| 427 | `fc-nsrc` | переменная | src/forthc.fth:152 | 20 |  |
| 428 | `fc-mbase` | переменная | src/forthc.fth:153 | 8 |  |
| 429 | `fc-mptr` | переменная | src/forthc.fth:153 | 4 |  |
| 430 | `fc-mn` | переменная | src/forthc.fth:153 | 7 |  |
| 431 | `fc-mw2` | переменная | src/forthc.fth:153 | 6 |  |
| 432 | `fc-popped@` | определение `:` | src/forthc.fth:154 | 6 |  |
| 433 | `fc-shift` | определение `:` | src/forthc.fth:155 | 4 |  |
| 434 | `fc-mem-pop` | определение `:` | src/forthc.fth:156 | 3 |  |
| 435 | `fc-push-group` | определение `:` | src/forthc.fth:164 | 2 |  |
| 436 | `fc-dup-at` | определение `:` | src/forthc.fth:170 | 1 |  |
| 437 | `fc-rest` | данные `create` | src/forthc.fth:172 | 2 |  |
| 438 | `fc-nrest` | переменная | src/forthc.fth:172 | 3 |  |
| 439 | `fc-mem-push` | определение `:` | src/forthc.fth:173 | 7 |  |
| 440 | `fc-src1` | определение `:` | src/forthc.fth:179 | 3 |  |
| 441 | `fc-need` | определение `:` | src/forthc.fth:180 | 17 |  |
| 442 | `fc-spill` | определение `:` | src/forthc.fth:186 | 16 |  |
| 443 | `fc-pop` | определение `:` | src/forthc.fth:192 | 11 |  |
| 444 | `fc-max-log` | константа | src/forthc.fth:197 | 1 |  |
| 445 | `fc-max-notes` | константа | src/forthc.fth:197 | 3 |  |
| 446 | `fc-log` | переменная | src/forthc.fth:198 | 3 |  |
| 447 | `fc-nlog` | переменная | src/forthc.fth:198 | 5 |  |
| 448 | `fc-decs` | переменная | src/forthc.fth:198 | 2 |  |
| 449 | `fc-ndec` | переменная | src/forthc.fth:198 | 6 |  |
| 450 | `fc-calls` | переменная | src/forthc.fth:198 | 2 |  |
| 451 | `fc-ncall` | переменная | src/forthc.fth:198 | 6 |  |
| 452 | `fc-pend` | переменная | src/forthc.fth:199 | 2 |  |
| 453 | `fc-npend` | переменная | src/forthc.fth:199 | 9 |  |
| 454 | `fc-unknown` | переменная | src/forthc.fth:199 | 7 |  |
| 455 | `fc-lc` | переменная | src/forthc.fth:200 | 3 |  |
| 456 | `fc-lb` | переменная | src/forthc.fth:200 | 3 |  |
| 457 | `fc-row-n` | определение `:` | src/forthc.fth:201 | 1 |  |
| 458 | `fc-mem-row?` | определение `:` | src/forthc.fth:202 | 1 |  |
| 459 | `fc-log-layer` | определение `:` | src/forthc.fth:203 | 2 |  |
| 460 | `fc-log-begin` | определение `:` | src/forthc.fth:215 | 3 |  |
| 461 | `fc-log-end` | определение `:` | src/forthc.fth:217 | 4 |  |
| 462 | `fc-by-execution` | определение `:` | src/forthc.fth:218 | 7 |  |
| 463 | `fc-dec@` | определение `:` | src/forthc.fth:219 | 2 |  |
| 464 | `fc-call@` | определение `:` | src/forthc.fth:220 | 2 |  |
| 465 | `fc-log-decision` | определение `:` | src/forthc.fth:221 | 2 |  |
| 466 | `fc-log-call` | определение `:` | src/forthc.fth:225 | 2 |  |
| 467 | `fc-callee` | переменная | src/forthc.fth:229 | 4 |  |
| 468 | `fc-live` | переменная | src/forthc.fth:231 | 7 |  |
| 469 | `fc-tramp` | переменная | src/forthc.fth:231 | 6 |  |
| 470 | `fc-ex` | переменная | src/forthc.fth:231 | 4 |  |
| 471 | `fc-halt` | переменная | src/forthc.fth:231 | 3 |  |
| 472 | `fc-jump` | определение `:` | src/forthc.fth:232 | 8 |  |
| 473 | `fc-end` | определение `:` | src/forthc.fth:233 | 12 |  |
| 474 | `fc-begin-block` | определение `:` | src/forthc.fth:234 | 21 |  |
| 475 | `fc-rows1` | определение `:` | src/forthc.fth:238 | 12 |  |
| 476 | `fc-nonzero` | определение `:` | src/forthc.fth:239 | 2 |  |
| 477 | `fc-branch` | определение `:` | src/forthc.fth:242 | 5 |  |
| 478 | `fc-rtab-at` | определение `:` | src/forthc.fth:243 | 1 |  |
| 479 | `fc-nret` | переменная | src/forthc.fth:244 | 6 |  |
| 480 | `fc-ret-link` | определение `:` | src/forthc.fth:248 | 3 |  |
| 481 | `fc-ret-base` | определение `:` | src/forthc.fth:253 | 4 |  |
| 482 | `fc-call` | определение `:` | src/forthc.fth:254 | 4 |  |
| 483 | `fc-v0` | переменная | src/forthc.fth:258 | 4 |  |
| 484 | `fc-v1` | переменная | src/forthc.fth:258 | 4 |  |
| 485 | `fc-jw` | определение `:` | src/forthc.fth:259 | 2 |  |
| 486 | `fc-xw` | определение `:` | src/forthc.fth:260 | 2 |  |
| 487 | `fc-xoff` | определение `:` | src/forthc.fth:261 | 2 |  |
| 488 | `fc-etab-at` | определение `:` | src/forthc.fth:262 | 1 |  |
| 489 | `fc-ex-base` | определение `:` | src/forthc.fth:263 | 1 |  |
| 490 | `fc-call-indirect` | определение `:` | src/forthc.fth:264 | 1 |  |
| 491 | `fc-ret-p` | переменная | src/forthc.fth:271 | 4 |  |
| 492 | `fc-ret-l` | переменная | src/forthc.fth:271 | 6 |  |
| 493 | `fc-rs0` | переменная | src/forthc.fth:271 | 3 |  |
| 494 | `fc-rs1` | переменная | src/forthc.fth:271 | 3 |  |
| 495 | `fc-ret-m` | переменная | src/forthc.fth:271 | 3 |  |
| 496 | `fc-ret-t` | переменная | src/forthc.fth:271 | 3 |  |
| 497 | `fc-ret-patch` | определение `:` | src/forthc.fth:272 | 4 |  |
| 498 | `fc-ret-masked` | определение `:` | src/forthc.fth:274 | 1 |  |
| 499 | `fc-ret` | определение `:` | src/forthc.fth:280 | 3 |  |
| 500 | `fc-ca` | переменная | src/forthc.fth:292 | 3 |  |
| 501 | `fc-cl0` | переменная | src/forthc.fth:292 | 4 |  |
| 502 | `fc-cl1` | переменная | src/forthc.fth:292 | 4 |  |
| 503 | `fc-cr` | переменная | src/forthc.fth:292 | 4 |  |
| 504 | `fc-cslot` | переменная | src/forthc.fth:292 | 3 |  |
| 505 | `fc-csh` | переменная | src/forthc.fth:292 | 2 |  |
| 506 | `fc-cv` | переменная | src/forthc.fth:293 | 3 |  |
| 507 | `fc-cres` | переменная | src/forthc.fth:293 | 6 |  |
| 508 | `fc-cmode` | переменная | src/forthc.fth:293 | 6 |  |
| 509 | `fc-ar` | переменная | src/forthc.fth:293 | 5 |  |
| 510 | `fc-chk-read` | определение `:` | src/forthc.fth:294 | 1 |  |
| 511 | `fc-chk-seg` | определение `:` | src/forthc.fth:296 | 1 |  |
| 512 | `fc-as` | переменная | src/forthc.fth:299 | 2 |  |
| 513 | `fc-af` | переменная | src/forthc.fth:299 | 2 |  |
| 514 | `fc-al0` | переменная | src/forthc.fth:299 | 2 |  |
| 515 | `fc-al1` | переменная | src/forthc.fth:299 | 2 |  |
| 516 | `fc-apl` | переменная | src/forthc.fth:299 | 3 |  |
| 517 | `fc-afld` | переменная | src/forthc.fth:299 | 3 |  |
| 518 | `fc-access-patch` | определение `:` | src/forthc.fth:300 | 2 |  |
| 519 | `fc-access` | определение `:` | src/forthc.fth:305 | 1 |  |
| 520 | `fc-width` | определение `:` | src/forthc.fth:307 | 4 |  |
| 521 | `fc-check` | определение `:` | src/forthc.fth:308 | 4 |  |
| 522 | `fc-ring` | константа | src/forthc.fth:324 | 5 |  |
| 523 | `fc-window` | константа | src/forthc.fth:324 | 1 |  |
| 524 | `fc-sl` | данные `create` | src/forthc.fth:325 | 2 |  |
| 525 | `fc-stabs` | переменная | src/forthc.fth:325 | 2 |  |
| 526 | `fc-slen` | переменная | src/forthc.fth:326 | 7 |  |
| 527 | `fc-slow` | переменная | src/forthc.fth:326 | 4 |  |
| 528 | `fc-sinit` | определение `:` | src/forthc.fth:327 | 2 |  |
| 529 | `fc-sbegin` | определение `:` | src/forthc.fth:328 | 2 |  |
| 530 | `fc-tabs` | определение `:` | src/forthc.fth:329 | 3 |  |
| 531 | `fc-at` | определение `:` | src/forthc.fth:330 | 4 |  |
| 532 | `fc-has?` | определение `:` | src/forthc.fth:335 | 1 |  |
| 533 | `fc-tab+` | определение `:` | src/forthc.fth:336 | 1 |  |
| 534 | `fc-prw` | данные `create` | src/forthc.fth:337 | 6 |  |
| 535 | `fc-ptab` | переменная | src/forthc.fth:337 | 5 |  |
| 536 | `fc-place` | определение `:` | src/forthc.fth:338 | 3 |  |
| 537 | `fc-scopy` | определение `:` | src/forthc.fth:348 | 9 |  |
| 538 | `fc-segs` | данные `create` | src/forthc.fth:349 | 2 |  |
| 539 | `fc-nseg` | переменная | src/forthc.fth:349 | 5 |  |
| 540 | `fc-pp` | данные `create` | src/forthc.fth:350 | 2 |  |
| 541 | `fc-npp` | переменная | src/forthc.fth:350 | 4 |  |
| 542 | `fc-latest` | переменная | src/forthc.fth:350 | 4 |  |
| 543 | `fc-sga` | переменная | src/forthc.fth:350 | 14 |  |
| 544 | `fc-ltab` | переменная | src/forthc.fth:351 | 3 |  |
| 545 | `fc-ls` | переменная | src/forthc.fth:351 | 3 |  |
| 546 | `fc-lw` | переменная | src/forthc.fth:351 | 3 |  |
| 547 | `fc-ldst` | переменная | src/forthc.fth:351 | 2 |  |
| 548 | `fc-seg+` | определение `:` | src/forthc.fth:352 | 21 |  |
| 549 | `fc-pp+` | определение `:` | src/forthc.fth:355 | 1 |  |
| 550 | `fc-slookup` | определение `:` | src/forthc.fth:356 | 8 |  |
| 551 | `fc-nx` | переменная | src/forthc.fth:374 | 3 |  |
| 552 | `fc-nv` | переменная | src/forthc.fth:374 | 2 |  |
| 553 | `fc-nt` | переменная | src/forthc.fth:374 | 3 |  |
| 554 | `fc-negate-chain` | определение `:` | src/forthc.fth:375 | 1 |  |
| 555 | `fc-gw` | переменная | src/forthc.fth:381 | 4 |  |
| 556 | `fc-gs` | переменная | src/forthc.fth:381 | 2 |  |
| 557 | `fc-gs2` | переменная | src/forthc.fth:381 | 2 |  |
| 558 | `fc-gts` | переменная | src/forthc.fth:381 | 6 |  |
| 559 | `fc-gdst` | переменная | src/forthc.fth:381 | 2 |  |
| 560 | `fc-negate-select` | определение `:` | src/forthc.fth:382 | 4 |  |
| 561 | `fc-sfinish` | определение `:` | src/forthc.fth:387 | 2 |  |
| 562 | `fc-pr` | данные `create` | src/forthc.fth:390 | 2 |  |
| 563 | `fc-xs` | данные `create` | src/forthc.fth:390 | 2 |  |
| 564 | `fc-m4` | переменная | src/forthc.fth:391 | 2 |  |
| 565 | `fc-mj` | переменная | src/forthc.fth:391 | 11 |  |
| 566 | `fc-mk` | переменная | src/forthc.fth:391 | 6 |  |
| 567 | `fc-p@` | определение `:` | src/forthc.fth:392 | 3 |  |
| 568 | `fc-p!` | определение `:` | src/forthc.fth:393 | 1 |  |
| 569 | `fc-x@` | определение `:` | src/forthc.fth:394 | 3 |  |
| 570 | `fc-x!` | определение `:` | src/forthc.fth:395 | 2 |  |
| 571 | `fc-build-mul` | определение `:` | src/forthc.fth:396 | 1 |  |
| 572 | `fc-sub` | данные `create` | src/forthc.fth:414 | 2 |  |
| 573 | `fc-qsel` | переменная | src/forthc.fth:414 | 2 |  |
| 574 | `fc-absa` | переменная | src/forthc.fth:415 | 5 |  |
| 575 | `fc-absb` | переменная | src/forthc.fth:415 | 3 |  |
| 576 | `fc-ta` | переменная | src/forthc.fth:415 | 4 |  |
| 577 | `fc-tb` | переменная | src/forthc.fth:415 | 2 |  |
| 578 | `fc-rem` | переменная | src/forthc.fth:416 | 7 |  |
| 579 | `fc-tr` | переменная | src/forthc.fth:416 | 7 |  |
| 580 | `fc-q` | переменная | src/forthc.fth:416 | 3 |  |
| 581 | `fc-tq` | переменная | src/forthc.fth:416 | 4 |  |
| 582 | `fc-k` | переменная | src/forthc.fth:416 | 5 |  |
| 583 | `fc-w` | переменная | src/forthc.fth:417 | 14 |  |
| 584 | `fc-lo` | переменная | src/forthc.fth:417 | 7 |  |
| 585 | `fc-tlo` | переменная | src/forthc.fth:417 | 7 |  |
| 586 | `fc-t0` | переменная | src/forthc.fth:417 | 4 |  |
| 587 | `fc-t1` | переменная | src/forthc.fth:417 | 4 |  |
| 588 | `fc-qr` | переменная | src/forthc.fth:417 | 4 |  |
| 589 | `fc-tqk` | переменная | src/forthc.fth:417 | 3 |  |
| 590 | `fc-sub@` | определение `:` | src/forthc.fth:418 | 7 |  |
| 591 | `fc-step` | определение `:` | src/forthc.fth:419 | 3 |  |
| 592 | `fc-div-step` | определение `:` | src/forthc.fth:426 | 1 |  |
| 593 | `fc-build-div` | определение `:` | src/forthc.fth:443 | 1 |  |
| 594 | `fc-mul-entry` | переменная | src/forthc.fth:459 | 4 |  |
| 595 | `fc-mul-exit` | переменная | src/forthc.fth:459 | 2 |  |
| 596 | `fc-div-entry` | переменная | src/forthc.fth:459 | 5 |  |
| 597 | `fc-div-exit` | переменная | src/forthc.fth:459 | 4 |  |
| 598 | `fc-hl` | переменная | src/forthc.fth:460 | 5 |  |
| 599 | `fc-hcont` | переменная | src/forthc.fth:460 | 4 |  |
| 600 | `fc-mul-cost` | данные `create` | src/forthc.fth:461 | 2 |  |
| 601 | `fc-div-cost` | данные `create` | src/forthc.fth:461 | 2 |  |
| 602 | `fc-row-or-new` | определение `:` | src/forthc.fth:462 | 2 |  |
| 603 | `fc-call-helper` | определение `:` | src/forthc.fth:464 | 4 |  |
| 604 | `fc-result1` | определение `:` | src/forthc.fth:474 | 3 |  |
| 605 | `fc-s1` | переменная | src/forthc.fth:475 | 2 |  |
| 606 | `fc-s2` | переменная | src/forthc.fth:475 | 2 |  |
| 607 | `fc-r1` | переменная | src/forthc.fth:475 | 2 |  |
| 608 | `fc-result2` | определение `:` | src/forthc.fth:476 | 1 |  |
| 609 | `fc-forbid` | константа | src/forthc.fth:484 | 2 |  |
| 610 | `fc-pexit` | переменная | src/forthc.fth:485 | 2 |  |
| 611 | `fc-ptramp` | переменная | src/forthc.fth:485 | 2 |  |
| 612 | `fc-pd` | переменная | src/forthc.fth:485 | 5 |  |
| 613 | `fc-pc` | переменная | src/forthc.fth:485 | 5 |  |
| 614 | `fc-ends` | переменная | src/forthc.fth:485 | 3 |  |
| 615 | `fc-pb` | переменная | src/forthc.fth:486 | 5 |  |
| 616 | `fc-pcp` | переменная | src/forthc.fth:486 | 5 |  |
| 617 | `fc-pln` | переменная | src/forthc.fth:486 | 5 |  |
| 618 | `fc-pk` | переменная | src/forthc.fth:486 | 4 |  |
| 619 | `fc-pcall` | переменная | src/forthc.fth:486 | 3 |  |
| 620 | `fc-best` | данные `create` | src/forthc.fth:487 | 10 |  |
| 621 | `fc-pend@` | определение `:` | src/forthc.fth:488 | 7 |  |
| 622 | `fc-reach` | определение `:` | src/forthc.fth:489 | 2 |  |
| 623 | `fc-take` | определение `:` | src/forthc.fth:498 | 1 |  |
| 624 | `fc-end-path` | определение `:` | src/forthc.fth:505 | 2 |  |
| 625 | `fc-to` | определение `:` | src/forthc.fth:509 | 2 |  |
| 626 | `fc-node` | определение `:` | src/forthc.fth:513 | 1 |  |
| 627 | `fc-path` | определение `:` | src/forthc.fth:532 | 3 |  |
| 628 | `fc-cost!` | определение `:` | src/forthc.fth:541 | 4 |  |
| 629 | `fc-ll` | переменная | src/forthc.fth:543 | 6 |  |
| 630 | `fc-llr` | переменная | src/forthc.fth:543 | 3 |  |
| 631 | `fc-llv` | переменная | src/forthc.fth:543 | 3 |  |
| 632 | `fc-plit` | переменная | src/forthc.fth:543 | 6 |  |
| 633 | `fc-plr` | переменная | src/forthc.fth:543 | 4 |  |
| 634 | `fc-plv` | переменная | src/forthc.fth:543 | 6 |  |
| 635 | `fc-literal` | определение `:` | src/forthc.fth:544 | 14 |  |
| 636 | `fc-or-zero` | определение `:` | src/forthc.fth:546 | 2 |  |
| 637 | `fc-ba` | переменная | src/forthc.fth:549 | 13 |  |
| 638 | `fc-bb` | переменная | src/forthc.fth:549 | 13 |  |
| 639 | `fc-br` | переменная | src/forthc.fth:549 | 9 |  |
| 640 | `fc-binary` | определение `:` | src/forthc.fth:550 | 10 |  |
| 641 | `fc-r-at` | определение `:` | src/forthc.fth:574 | 2 |  |
| 642 | `fc-pop-pinned` | определение `:` | src/forthc.fth:577 | 3 |  |
| 643 | `fc-sk` | переменная | src/forthc.fth:578 | 12 |  |
| 644 | `fc-shift-copy` | определение `:` | src/forthc.fth:579 | 2 |  |
| 645 | `fc-inc` | определение `:` | src/forthc.fth:583 | 3 |  |
| 646 | `fc-read-key` | определение `:` | src/forthc.fth:586 | 1 |  |
| 647 | `fc-text-mem` | данные `create` | src/forthc.fth:591 | 1 |  |
| 648 | `fc-text` | переменная | src/forthc.fth:592 | 13 |  |
| 649 | `fc-tlen` | переменная | src/forthc.fth:592 | 14 |  |
| 650 | `fc-pos` | переменная | src/forthc.fth:592 | 24 |  |
| 651 | `fc-text-size` | переменная | src/forthc.fth:592 | 5 | вход бута (хост) |
| 652 | `fc-reset` | определение `:` | src/forthc.fth:593 | 3 |  |
| 653 | `fc-append` | определение `:` | src/forthc.fth:594 | 1 |  |
| 654 | `fc\|` | определение `:` | src/forthc.fth:598 | 1 | вход бута (хост) |
| 655 | `fc-ch` | определение `:` | src/forthc.fth:599 | 5 |  |
| 656 | `fc-more?` | определение `:` | src/forthc.fth:600 | 6 |  |
| 657 | `fc-next` | определение `:` | src/forthc.fth:601 | 8 |  |
| 658 | `fc-next!` | определение `:` | src/forthc.fth:609 | 10 |  |
| 659 | `fc-is?` | определение `:` | src/forthc.fth:610 | 5 |  |
| 660 | `fc-raw` | определение `:` | src/forthc.fth:613 | 1 |  |
| 661 | `fc-string-token` | определение `:` | src/forthc.fth:614 | 1 |  |
| 662 | `fc-names-size` | переменная | src/forthc.fth:619 | 4 | вход бута (хост) |
| 663 | `fc-max-words` | переменная | src/forthc.fth:619 | 4 | вход бута (хост) |
| 664 | `fc-names` | переменная | src/forthc.fth:620 | 3 |  |
| 665 | `fc-names-used` | переменная | src/forthc.fth:620 | 5 |  |
| 666 | `fc-wt` | переменная | src/forthc.fth:621 | 5 |  |
| 667 | `fc-nwords` | переменная | src/forthc.fth:621 | 12 |  |
| 668 | `fc-wbk` | переменная | src/forthc.fth:621 | 3 |  |
| 669 | `fc-wt@` | определение `:` | src/forthc.fth:624 | 6 |  |
| 670 | `fc-proved` | данные `create` | src/forthc.fth:626 | 2 |  |
| 671 | `fc-unproved` | данные `create` | src/forthc.fth:627 | 2 |  |
| 672 | `fc-mechanisms` | определение `:` | src/forthc.fth:628 | 1 |  |
| 673 | `fc-xt` | определение `:` | src/forthc.fth:633 | 5 |  |
| 674 | `fc-xtn` | определение `:` | src/forthc.fth:635 | 2 |  |
| 675 | `fc-hash` | определение `:` | src/forthc.fth:636 | 2 |  |
| 676 | `fc-define` | определение `:` | src/forthc.fth:638 | 6 |  |
| 677 | `fc-lookup` | определение `:` | src/forthc.fth:643 | 6 |  |
| 678 | `fc-find` | определение `:` | src/forthc.fth:647 | 6 |  |
| 679 | `fc-word-of` | определение `:` | src/forthc.fth:649 | 2 |  |
| 680 | `fc-cost` | определение `:` | src/forthc.fth:657 | 1 |  |
| 681 | `fc-proved?` | определение `:` | src/forthc.fth:660 | 1 |  |
| 682 | `fc-here` | переменная | src/forthc.fth:662 | 9 |  |
| 683 | `fc-word` | переменная | src/forthc.fth:662 | 13 |  |
| 684 | `fc-uses` | переменная | src/forthc.fth:662 | 17 |  |
| 685 | `fc-rt` | переменная | src/forthc.fth:663 | 7 |  |
| 686 | `fc-rta` | переменная | src/forthc.fth:663 | 7 |  |
| 687 | `fc-ctl` | данные `create` | src/forthc.fth:664 | 1 |  |
| 688 | `fc-nctl` | переменная | src/forthc.fth:664 | 12 |  |
| 689 | `fc-cleave` | переменная | src/forthc.fth:664 | 2 |  |
| 690 | `fc-ctl@` | определение `:` | src/forthc.fth:665 | 4 |  |
| 691 | `fc-ctl+` | определение `:` | src/forthc.fth:666 | 6 |  |
| 692 | `fc-ctl-` | определение `:` | src/forthc.fth:668 | 7 |  |
| 693 | `fc-do-entry` | определение `:` | src/forthc.fth:670 | 1 |  |
| 694 | `fc-ctl-leave` | определение `:` | src/forthc.fth:672 | 1 |  |
| 695 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:673 | 1 |  |
| 696 | `fc-loop-leave` | определение `:` | src/forthc.fth:674 | 1 |  |
| 697 | `fc-align` | определение `:` | src/forthc.fth:675 | 2 |  |
| 698 | `fc-check-here` | определение `:` | src/forthc.fth:676 | 3 |  |
| 699 | `fc-define-data` | определение `:` | src/forthc.fth:677 | 2 |  |
| 700 | `fc-sat` | переменная | src/forthc.fth:678 | 3 |  |
| 701 | `fc-store-string` | определение `:` | src/forthc.fth:679 | 1 |  |
| 702 | `fc-ct` | данные `create` | src/forthc.fth:684 | 3 |  |
| 703 | `fc-nct` | переменная | src/forthc.fth:684 | 11 |  |
| 704 | `fc-ct+` | определение `:` | src/forthc.fth:685 | 18 |  |
| 705 | `fc-ct-` | определение `:` | src/forthc.fth:686 | 9 |  |
| 706 | `fc-ct2` | определение `:` | src/forthc.fth:687 | 8 |  |
| 707 | `fc-inits` | данные `create` | src/forthc.fth:688 | 2 |  |
| 708 | `fc-ninit` | переменная | src/forthc.fth:688 | 5 |  |
| 709 | `fc-init-open` | переменная | src/forthc.fth:688 | 6 |  |
| 710 | `fc-ck-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 711 | `fc-stabs-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 712 | `fc-cbk-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 713 | `fc-link-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 714 | `fc-wt-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 715 | `fc-names-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 716 | `fc-wbk-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 717 | `fc-log-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 718 | `fc-decs-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 719 | `fc-calls-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 720 | `fc-pend-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 721 | `fc-init` | определение `:` | src/forthc.fth:695 | 1 |  |
| 722 | `fc-scan-uses` | определение `:` | src/forthc.fth:709 | 1 |  |
| 723 | `fc-const-shift` | определение `:` | src/forthc.fth:716 | 2 |  |
| 724 | `fc-lit?` | определение `:` | src/forthc.fth:725 | 3 |  |
| 725 | `fc-mul-lit?` | определение `:` | src/forthc.fth:727 | 1 |  |
| 726 | `fc-shift-lit?` | определение `:` | src/forthc.fth:732 | 2 |  |
| 727 | `fc-pick-roll` | определение `:` | src/forthc.fth:735 | 2 |  |
| 728 | `fc-stx` | переменная | src/forthc.fth:744 | 3 |  |
| 729 | `fc-stlo` | переменная | src/forthc.fth:744 | 11 |  |
| 730 | `fc-sthi` | переменная | src/forthc.fth:744 | 5 |  |
| 731 | `fc-stp` | переменная | src/forthc.fth:744 | 6 |  |
| 732 | `fc-strow` | переменная | src/forthc.fth:744 | 16 |  |
| 733 | `fc-stm` | переменная | src/forthc.fth:744 | 5 |  |
| 734 | `fc-ftr` | переменная | src/forthc.fth:745 | 5 |  |
| 735 | `fc-stg` | переменная | src/forthc.fth:745 | 2 |  |
| 736 | `fc-sw0` | определение `:` | src/forthc.fth:746 | 5 |  |
| 737 | `fc-sw1` | определение `:` | src/forthc.fth:747 | 3 |  |
| 738 | `fc-sbase` | определение `:` | src/forthc.fth:748 | 4 |  |
| 739 | `fc-space-end` | определение `:` | src/forthc.fth:749 | 3 |  |
| 740 | `fc-space-store` | определение `:` | src/forthc.fth:757 | 2 |  |
| 741 | `fc-space-fetch` | определение `:` | src/forthc.fth:764 | 2 |  |
| 742 | `fc-cp` | определение `:` | src/forthc.fth:775 | 4 |  |
| 743 | `fc-copy-row` | определение `:` | src/forthc.fth:777 | 1 |  |
| 744 | `fc-close-init` | определение `:` | src/forthc.fth:780 | 2 |  |
| 745 | `fc-open-init` | определение `:` | src/forthc.fth:783 | 1 |  |
| 746 | `fc-gens` | переменная | src/forthc.fth:794 | 3 |  |
| 747 | `fc-generator` | определение `:` | src/forthc.fth:795 | 88 |  |
| 748 | `fc-literal-name` | определение `:` | src/forthc.fth:797 | 10 |  |
| 749 | `fc-words` | определение `:` | src/forthc.fth:799 | 1 |  |
| 750 | `fc-known` | определение `:` | src/forthc.fth:808 | 1 |  |
| 751 | `fc-defining?` | определение `:` | src/forthc.fth:810 | 7 |  |
| 752 | `fc-code` | определение `:` | src/forthc.fth:811 | 52 | вариант 2 |
| 753 | `fc-fold?` | определение `:` | src/forthc.fth:813 | 13 |  |
| 754 | `fc-top-only` | определение `:` | src/forthc.fth:814 | 6 |  |
| 755 | `fc-not-found` | определение `:` | src/forthc.fth:816 | 1 |  |
| 756 | `fc-word-token` | определение `:` | src/forthc.fth:818 | 2 |  |
| 757 | `fc-token` | определение `:` | src/forthc.fth:823 | 2 |  |
| 758 | `fc-synonym-of` | определение `:` | src/forthc.fth:824 | 2 |  |
| 759 | `fc-synonym` | определение `:` | src/forthc.fth:825 | 10 |  |
| 760 | `fc-sy` | переменная | src/forthc.fth:828 | 2 |  |
| 761 | `fc-synonym?` | определение `:` | src/forthc.fth:829 | 1 |  |
| 762 | `fc-poke` | определение `:` | src/forthc.fth:832 | 2 |  |
| 763 | `fc-concept-record` | определение `:` | src/forthc.fth:835 | 1 |  |
| 764 | `fc-eval` | определение `:` | src/forthc.fth:840 | 64 |  |
| 765 | `fc-concepts` | определение `:` | src/forthc.fth:844 | 1 |  |
| 766 | `fc-nhost` | переменная | src/forthc.fth:851 | 5 |  |
| 767 | `fc-platform` | определение `:` | src/forthc.fth:852 | 1 |  |
| 768 | `fc-time-price` | определение `:` | src/forthc.fth:875 | 1 |  |
| 769 | `fc-replacement` | определение `:` | src/forthc.fth:885 | 1 |  |
| 770 | `fc-library` | определение `:` | src/forthc.fth:900 | 1 |  |
| 771 | `fc-forbidden` | определение `:` | src/forthc.fth:926 | 2 |  |
| 772 | `fc-long-host` | определение `:` | src/forthc.fth:927 | 1 |  |
| 773 | `fc-ltpl` | переменная | src/forthc.fth:939 | 2 |  |
| 774 | `fc-lpos` | переменная | src/forthc.fth:939 | 4 |  |
| 775 | `fc-llo` | переменная | src/forthc.fth:939 | 2 |  |
| 776 | `fc-lhi` | переменная | src/forthc.fth:939 | 2 |  |
| 777 | `fc-lcn` | переменная | src/forthc.fth:939 | 4 |  |
| 778 | `fc-ldir` | переменная | src/forthc.fth:939 | 3 |  |
| 779 | `fc-lp0` | переменная | src/forthc.fth:940 | 4 |  |
| 780 | `fc-lp1` | переменная | src/forthc.fth:940 | 4 |  |
| 781 | `fc-lpl` | переменная | src/forthc.fth:940 | 6 |  |
| 782 | `fc-ltemplate` | определение `:` | src/forthc.fth:941 | 1 |  |
| 783 | `fc-lhead` | определение `:` | src/forthc.fth:945 | 2 |  |
| 784 | `fc-lsend` | определение `:` | src/forthc.fth:950 | 2 |  |
| 785 | `fc-lput` | определение `:` | src/forthc.fth:951 | 1 |  |
| 786 | `fc-lget` | определение `:` | src/forthc.fth:960 | 1 |  |
| 787 | `fc-long-kernel` | определение `:` | src/forthc.fth:966 | 1 |  |
| 788 | `fc-long` | определение `:` | src/forthc.fth:973 | 1 |  |
| 789 | `fc-helpers-cost` | определение `:` | src/forthc.fth:977 | 1 |  |
| 790 | `fc-price-word` | определение `:` | src/forthc.fth:984 | 1 |  |
| 791 | `fc-compile` | определение `:` | src/forthc.fth:987 | 1 |  |
| 792 | `fc-go` | определение `:` | src/forthc.fth:1003 | 3 | вход бута (хост) |
| 793 | `gen+` | определение `:` | src/primitives.fth:4 | 5 |  |
| 794 | `gen-` | определение `:` | src/primitives.fth:5 | 2 |  |
| 795 | `gen-and` | определение `:` | src/primitives.fth:6 | 2 |  |
| 796 | `gen-or` | определение `:` | src/primitives.fth:7 | 2 |  |
| 797 | `gen-xor` | определение `:` | src/primitives.fth:8 | 2 |  |
| 798 | `gen=` | определение `:` | src/primitives.fth:9 | 2 |  |
| 799 | `gen<` | определение `:` | src/primitives.fth:10 | 2 |  |
| 800 | `gen-u<` | определение `:` | src/primitives.fth:11 | 2 |  |
| 801 | `gen-lshift` | определение `:` | src/primitives.fth:12 | 2 |  |
| 802 | `gen-rshift` | определение `:` | src/primitives.fth:14 | 2 |  |
| 803 | `gen-0=` | определение `:` | src/primitives.fth:16 | 2 |  |
| 804 | `gen-cells` | определение `:` | src/primitives.fth:17 | 2 |  |
| 805 | `gen-2*` | определение `:` | src/primitives.fth:18 | 2 |  |
| 806 | `gen-1+` | определение `:` | src/primitives.fth:19 | 2 |  |
| 807 | `gen-1-` | определение `:` | src/primitives.fth:20 | 2 |  |
| 808 | `gen-cell+` | определение `:` | src/primitives.fth:21 | 2 |  |
| 809 | `gen*` | определение `:` | src/primitives.fth:22 | 2 |  |
| 810 | `gen/` | определение `:` | src/primitives.fth:25 | 2 |  |
| 811 | `gen-mod` | определение `:` | src/primitives.fth:26 | 2 |  |
| 812 | `gen/mod` | определение `:` | src/primitives.fth:27 | 2 |  |
| 813 | `gen-dup` | определение `:` | src/primitives.fth:28 | 2 |  |
| 814 | `gen-drop` | определение `:` | src/primitives.fth:29 | 2 |  |
| 815 | `gen-swap` | определение `:` | src/primitives.fth:30 | 2 |  |
| 816 | `gen-over` | определение `:` | src/primitives.fth:31 | 2 |  |
| 817 | `gen-rot` | определение `:` | src/primitives.fth:32 | 2 |  |
| 818 | `gen-pick` | определение `:` | src/primitives.fth:33 | 2 |  |
| 819 | `gen-roll` | определение `:` | src/primitives.fth:34 | 2 |  |
| 820 | `gen->r` | определение `:` | src/primitives.fth:35 | 2 |  |
| 821 | `gen-r>` | определение `:` | src/primitives.fth:36 | 2 |  |
| 822 | `gen-r@` | определение `:` | src/primitives.fth:37 | 4 |  |
| 823 | `gen-j` | определение `:` | src/primitives.fth:38 | 2 |  |
| 824 | `gen-@` | определение `:` | src/primitives.fth:39 | 2 |  |
| 825 | `gen-!` | определение `:` | src/primitives.fth:41 | 2 |  |
| 826 | `gen-c@` | определение `:` | src/primitives.fth:42 | 2 |  |
| 827 | `gen-c!` | определение `:` | src/primitives.fth:44 | 2 |  |
| 828 | `gen-emit` | определение `:` | src/primitives.fth:45 | 2 |  |
| 829 | `gen-key` | определение `:` | src/primitives.fth:48 | 2 |  |
| 830 | `gen-if` | определение `:` | src/primitives.fth:50 | 2 |  |
| 831 | `gen-else` | определение `:` | src/primitives.fth:51 | 2 |  |
| 832 | `gen-then` | определение `:` | src/primitives.fth:53 | 2 |  |
| 833 | `gen-begin` | определение `:` | src/primitives.fth:57 | 2 |  |
| 834 | `gen-until` | определение `:` | src/primitives.fth:58 | 2 |  |
| 835 | `gen-while` | определение `:` | src/primitives.fth:60 | 2 |  |
| 836 | `gen-repeat` | определение `:` | src/primitives.fth:61 | 2 |  |
| 837 | `gen-again` | определение `:` | src/primitives.fth:62 | 2 |  |
| 838 | `gen-do` | определение `:` | src/primitives.fth:63 | 2 |  |
| 839 | `fc-di` | переменная | src/primitives.fth:66 | 3 |  |
| 840 | `fc-dl` | переменная | src/primitives.fth:66 | 3 |  |
| 841 | `gen-?do` | определение `:` | src/primitives.fth:67 | 2 |  |
| 842 | `fc-lv` | переменная | src/primitives.fth:73 | 2 |  |
| 843 | `gen-loop` | определение `:` | src/primitives.fth:74 | 2 |  |
| 844 | `gen-leave` | определение `:` | src/primitives.fth:83 | 2 |  |
| 845 | `gen-unloop` | определение `:` | src/primitives.fth:86 | 2 |  |
| 846 | `gen-exit` | определение `:` | src/primitives.fth:87 | 2 |  |
| 847 | `gen-bye` | определение `:` | src/primitives.fth:90 | 2 |  |
| 848 | `gen-recurse` | определение `:` | src/primitives.fth:92 | 2 |  |
| 849 | `gen-tick` | определение `:` | src/primitives.fth:93 | 2 |  |
| 850 | `gen-call` | определение `:` | src/primitives.fth:99 | 3 |  |
| 851 | `gen-space!` | определение `:` | src/primitives.fth:100 | 2 |  |
| 852 | `gen-spacec!` | определение `:` | src/primitives.fth:101 | 2 |  |
| 853 | `gen-space@` | определение `:` | src/primitives.fth:102 | 2 |  |
| 854 | `gen-spacec@` | определение `:` | src/primitives.fth:103 | 2 |  |
| 855 | `gen-execute` | определение `:` | src/primitives.fth:104 | 2 |  |
| 856 | `fc-entry-cell` | определение `:` | src/primitives.fth:110 | 1 |  |
| 857 | `fc-concept` | определение `:` | src/primitives.fth:112 | 1 |  |
| 858 | `gen-colon` | определение `:` | src/primitives.fth:119 | 2 |  |
| 859 | `gen-semicolon` | определение `:` | src/primitives.fth:125 | 2 |  |
| 860 | `gen-variable` | определение `:` | src/primitives.fth:128 | 2 |  |
| 861 | `gen-create` | определение `:` | src/primitives.fth:129 | 2 |  |
| 862 | `gen-allot` | определение `:` | src/primitives.fth:130 | 2 |  |
| 863 | `gen-constant` | определение `:` | src/primitives.fth:131 | 2 |  |
| 864 | `gen-decimal` | определение `:` | src/primitives.fth:132 | 2 |  |
| 865 | `gen-kernel-layout` | определение `:` | src/primitives.fth:133 | 2 |  |
| 866 | `gen-backslash` | определение `:` | src/primitives.fth:134 | 2 |  |
| 867 | `gen-paren` | определение `:` | src/primitives.fth:136 | 4 |  |
| 868 | `gen-char` | определение `:` | src/primitives.fth:137 | 2 |  |
| 869 | `gen-string` | определение `:` | src/primitives.fth:138 | 2 |  |
| 870 | `fc-digit@` | определение `:` | src/primitives.fth:141 | 1 |  |
| 871 | `gen-literal` | определение `:` | src/primitives.fth:143 | 2 |  |
| 872 | `fc-known-xt` | определение `:` | src/primitives.fth:150 | 2 |  |
| 873 | `gen-cost` | определение `:` | src/primitives.fth:151 | 2 |  |
| 874 | `gen-proved?` | определение `:` | src/primitives.fth:153 | 2 |  |
| 875 | `gen-library` | определение `:` | src/primitives.fth:154 | 16 |  |
| 876 | `gen-price` | определение `:` | src/primitives.fth:155 | 2 |  |
| 877 | `fc-cpos` | переменная | src/primitives.fth:160 | 4 |  |
| 878 | `fc-hn` | переменная | src/primitives.fth:160 | 2 |  |
| 879 | `fc-cdepth` | переменная | src/primitives.fth:160 | 4 |  |
| 880 | `fc-hname` | данные `create` | src/primitives.fth:160 | 2 |  |
| 881 | `fc-hb` | определение `:` | src/primitives.fth:161 | 3 |  |
| 882 | `fc-c,` | определение `:` | src/primitives.fth:162 | 17 |  |
| 883 | `fc-c1` | определение `:` | src/primitives.fth:163 | 8 |  |
| 884 | `fc-c-gen` | определение `:` | src/primitives.fth:164 | 1 |  |
| 885 | `fc-c-body` | определение `:` | src/primitives.fth:168 | 1 |  |
| 886 | `gen-host` | определение `:` | src/primitives.fth:177 | 2 |  |
| 887 | `fc-name2` | определение `:` | src/primitives.fth:194 | 1 |  |
| 888 | `fc-generators` | определение `:` | src/primitives.fth:197 | 1 |  |
| 889 | `+` | генератор | src/primitives.fth:198 | 570 | слово компилятора `gen+` |
| 890 | `-` | генератор | src/primitives.fth:198 | 64 | слово компилятора `gen-` |
| 891 | `*` | генератор | src/primitives.fth:199 | 80 | слово компилятора `gen*` |
| 892 | `/` | генератор | src/primitives.fth:199 | 4 | слово компилятора `gen/` |
| 893 | `mod` | генератор | src/primitives.fth:200 | 2 | слово компилятора `gen-mod` |
| 894 | `and` | генератор | src/primitives.fth:201 | 125 | слово компилятора `gen-and` |
| 895 | `or` | генератор | src/primitives.fth:201 | 44 | слово компилятора `gen-or` |
| 896 | `xor` | генератор | src/primitives.fth:202 | 5 | слово компилятора `gen-xor` |
| 897 | `lshift` | генератор | src/primitives.fth:202 | 98 | слово компилятора `gen-lshift` |
| 898 | `rshift` | генератор | src/primitives.fth:203 | 64 | слово компилятора `gen-rshift` |
| 899 | `=` | генератор | src/primitives.fth:203 | 89 | слово компилятора `gen=` |
| 900 | `<` | генератор | src/primitives.fth:204 | 24 | слово компилятора `gen<` |
| 901 | `u<` | генератор | src/primitives.fth:204 | 28 | слово компилятора `gen-u<` |
| 902 | `0=` | генератор | src/primitives.fth:205 | 106 | слово компилятора `gen-0=` |
| 903 | `2*` | генератор | src/primitives.fth:205 | 29 | слово компилятора `gen-2*` |
| 904 | `1+` | генератор | src/primitives.fth:206 | 44 | слово компилятора `gen-1+` |
| 905 | `1-` | генератор | src/primitives.fth:206 | 56 | слово компилятора `gen-1-` |
| 906 | `cells` | генератор | src/primitives.fth:207 | 274 | слово компилятора `gen-cells` |
| 907 | `cell+` | генератор | src/primitives.fth:207 | 57 | слово компилятора `gen-cell+` |
| 908 | `dup` | генератор | src/primitives.fth:208 | 305 | слово компилятора `gen-dup` |
| 909 | `drop` | генератор | src/primitives.fth:208 | 206 | слово компилятора `gen-drop` |
| 910 | `swap` | генератор | src/primitives.fth:209 | 140 | слово компилятора `gen-swap` |
| 911 | `over` | генератор | src/primitives.fth:209 | 86 | слово компилятора `gen-over` |
| 912 | `rot` | генератор | src/primitives.fth:210 | 39 | слово компилятора `gen-rot` |
| 913 | `pick` | генератор | src/primitives.fth:210 | 45 | слово компилятора `gen-pick` |
| 914 | `roll` | генератор | src/primitives.fth:211 | 7 | слово компилятора `gen-roll` |
| 915 | `>r` | генератор | src/primitives.fth:211 | 107 | слово компилятора `gen->r` |
| 916 | `r>` | генератор | src/primitives.fth:212 | 111 | слово компилятора `gen-r>` |
| 917 | `r@` | генератор | src/primitives.fth:212 | 108 | слово компилятора `gen-r@` |
| 918 | `i` | генератор | src/primitives.fth:213 | 172 | слово компилятора `gen-r@` |
| 919 | `j` | генератор | src/primitives.fth:213 | 12 | слово компилятора `gen-j` |
| 920 | `@` | генератор | src/primitives.fth:214 | 1296 | слово компилятора `gen-@` |
| 921 | `!` | генератор | src/primitives.fth:214 | 675 | слово компилятора `gen-!` |
| 922 | `c@` | генератор | src/primitives.fth:215 | 23 | слово компилятора `gen-c@` |
| 923 | `c!` | генератор | src/primitives.fth:215 | 18 | слово компилятора `gen-c!` |
| 924 | `space!` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-space!` |
| 925 | `spacec!` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-spacec!` |
| 926 | `space@` | генератор | src/primitives.fth:217 | 1 | слово компилятора `gen-space@` |
| 927 | `emit` | генератор | src/primitives.fth:218 | 4 | слово компилятора `gen-emit` |
| 928 | `key` | генератор | src/primitives.fth:218 | 1 | слово компилятора `gen-key` |
| 929 | `if` | генератор | src/primitives.fth:219 | 307 | слово компилятора `gen-if` |
| 930 | `else` | генератор | src/primitives.fth:219 | 83 | слово компилятора `gen-else` |
| 931 | `then` | генератор | src/primitives.fth:220 | 307 | слово компилятора `gen-then` |
| 932 | `begin` | генератор | src/primitives.fth:220 | 25 | слово компилятора `gen-begin` |
| 933 | `until` | генератор | src/primitives.fth:221 | 2 | слово компилятора `gen-until` |
| 934 | `while` | генератор | src/primitives.fth:221 | 22 | слово компилятора `gen-while` |
| 935 | `repeat` | генератор | src/primitives.fth:222 | 22 | слово компилятора `gen-repeat` |
| 936 | `again` | генератор | src/primitives.fth:222 | 1 | слово компилятора `gen-again` |
| 937 | `do` | генератор | src/primitives.fth:223 | 31 | слово компилятора `gen-do` |
| 938 | `?do` | генератор | src/primitives.fth:223 | 58 | слово компилятора `gen-?do` |
| 939 | `loop` | генератор | src/primitives.fth:224 | 89 | слово компилятора `gen-loop` |
| 940 | `leave` | генератор | src/primitives.fth:224 | 1 | слово компилятора `gen-leave` |
| 941 | `unloop` | генератор | src/primitives.fth:225 | 7 | слово компилятора `gen-unloop` |
| 942 | `exit` | генератор | src/primitives.fth:225 | 83 | слово компилятора `gen-exit` |
| 943 | `bye` | генератор | src/primitives.fth:226 | 1 | слово компилятора `gen-bye` |
| 944 | `recurse` | генератор | src/primitives.fth:227 | 2 | слово компилятора `gen-recurse` |
| 945 | `execute` | генератор | src/primitives.fth:227 | 10 | слово компилятора `gen-execute` |
| 946 | `[']` | генератор | src/primitives.fth:228 | 119 | слово компилятора `gen-tick` |
| 947 | `:` | генератор | src/primitives.fth:229 | 497 | слово компилятора `gen-colon` |
| 948 | `;` | генератор | src/primitives.fth:229 | 497 | слово компилятора `gen-semicolon` |
| 949 | `variable` | генератор | src/primitives.fth:230 | 331 | слово компилятора `gen-variable` |
| 950 | `create` | генератор | src/primitives.fth:230 | 62 | слово компилятора `gen-create` |
| 951 | `allot` | генератор | src/primitives.fth:231 | 62 | слово компилятора `gen-allot` |
| 952 | `constant` | генератор | src/primitives.fth:231 | 27 | слово компилятора `gen-constant` |
| 953 | `decimal` | генератор | src/primitives.fth:232 | 3 | слово компилятора `gen-decimal` |
| 954 | `kernel-layout` | генератор | src/primitives.fth:232 | 1 | слово компилятора `gen-kernel-layout` |
| 955 | `\` | генератор | src/primitives.fth:233 | 167 | слово компилятора `gen-backslash` |
| 956 | `(` | генератор | src/primitives.fth:233 | 477 | слово компилятора `gen-paren` |
| 957 | `[char]` | генератор | src/primitives.fth:233 | 8 | слово компилятора `gen-char` |
| 958 | `s"` | генератор | src/primitives.fth:234 | 211 | слово компилятора `gen-string` |
| 959 | `literal` | генератор | src/primitives.fth:235 | 505 | слово компилятора `gen-literal` |
| 960 | `0` | цифра (литерал) | src/primitives.fth:243 | 551 | значение 0 |
| 961 | `1` | цифра (литерал) | src/primitives.fth:243 | 474 | значение 1 |
| 962 | `2` | цифра (литерал) | src/primitives.fth:243 | 457 | значение 2 |
| 963 | `3` | цифра (литерал) | src/primitives.fth:243 | 304 | значение 3 |
| 964 | `4` | цифра (литерал) | src/primitives.fth:244 | 239 | значение 4 |
| 965 | `5` | цифра (литерал) | src/primitives.fth:244 | 111 | значение 5 |
| 966 | `6` | цифра (литерал) | src/primitives.fth:244 | 163 | значение 6 |
| 967 | `7` | цифра (литерал) | src/primitives.fth:244 | 66 | значение 7 |
| 968 | `8` | цифра (литерал) | src/primitives.fth:245 | 160 | значение 8 |
| 969 | `9` | цифра (литерал) | src/primitives.fth:245 | 43 | значение 9 |
| 970 | `fc-install-generators` | определение `:` | src/primitives.fth:246 | 1 |  |
| 971 | `fc-read` | определение `:` | src/main.fth:3 | 2 |  |
| 972 | `fc-sizes` | определение `:` | src/main.fth:8 | 2 |  |
| 973 | `kn-at` | переменная | src/kernel.fth:7 | 5 |  |
| 974 | `kn-put` | определение `:` | src/kernel.fth:8 | 1 |  |
| 975 | `kn-order` | определение `:` | src/kernel.fth:16 | 1 |  |
| 976 | `kn-get` | определение `:` | src/kernel.fth:18 | 1 |  |
| 977 | `kn-compile` | определение `:` | src/kernel.fth:19 | 1 |  |
| 978 | `main` | определение `:` | src/kernel.fth:25 | 1 | вариант 2 |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 96.

## Определены, но не использованы

Слов: 34. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

| Слово | Вид | Файл:строка |
|---|---|---|
| `lay-out` | определение `:` | src/backend.fth:115 |
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
