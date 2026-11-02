# Ядро языка (14.8)

Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 940** (определение `:` — 471, переменная — 312, генератор — 72, данные `create` — 47, константа — 22, цифра (литерал) — 10, основание — 6).

## Основание

Основание — слова-копирования: генераторы строки (копия — приёмник и источник) и слоя (ячейка строк) из `src/backend.fth`. Определение инструкции — она сама: тело этих слов не сводится к другим словам языка, а строка и слой — сами инструкции индексного пространства.

| Слово | Что порождает | Файл:строка |
|---|---|---|
| `lay-copy` | строка: копирование n бит из источника в приёмник | src/backend.fth:119 |
| `lay-link-row` | строка: копирование ссылки на следующий слой | src/backend.fth:118 |
| `lay-row` | строка: добавляет строку в слой | src/backend.fth:186 |
| `lay-new-record` | слой: новый слой в ячейке | src/backend.fth:148 |
| `lay-lone` | слой: отдельный слой в новой ячейке | src/backend.fth:152 |
| `lay-layer` | слой: следующий слой последовательности | src/backend.fth:155 |

## Слова ядра

Вид: генератор (слово словаря, исполняемое при компиляции, `doc/generators.md`; в пояснении слово компилятора), определение `:`, переменная, константа, данные `create`, цифра (литерал, `doc/literals.md`), основание. «Исп.» — число ссылок из других слов (цифры — и из чисел определения). Повторное определение имени — «вариант N» (старое имя остаётся у прежних ссылок).

| № | Слово | Вид | Файл:строка | Исп. | Пояснение |
|---|---|---|---|---|---|
| 1 | `nip` | определение `:` | src/prelude.fth:6 | 25 |  |
| 2 | `tuck` | определение `:` | src/prelude.fth:7 | 9 |  |
| 3 | `-rot` | определение `:` | src/prelude.fth:8 | 10 |  |
| 4 | `2dup` | определение `:` | src/prelude.fth:9 | 14 |  |
| 5 | `2drop` | определение `:` | src/prelude.fth:10 | 26 |  |
| 6 | `2swap` | определение `:` | src/prelude.fth:11 | 6 |  |
| 7 | `2over` | определение `:` | src/prelude.fth:12 | 2 |  |
| 8 | `?dup` | определение `:` | src/prelude.fth:13 | 20 |  |
| 9 | `negate` | определение `:` | src/prelude.fth:14 | 5 |  |
| 10 | `invert` | определение `:` | src/prelude.fth:15 | 2 |  |
| 11 | `>` | определение `:` | src/prelude.fth:16 | 10 |  |
| 12 | `u>` | определение `:` | src/prelude.fth:17 | 8 |  |
| 13 | `<>` | определение `:` | src/prelude.fth:18 | 11 |  |
| 14 | `0<` | определение `:` | src/prelude.fth:19 | 5 |  |
| 15 | `0>` | определение `:` | src/prelude.fth:20 | 3 |  |
| 16 | `0<>` | определение `:` | src/prelude.fth:21 | 4 |  |
| 17 | `max` | определение `:` | src/prelude.fth:22 | 21 |  |
| 18 | `min` | определение `:` | src/prelude.fth:23 | 5 |  |
| 19 | `+!` | определение `:` | src/prelude.fth:24 | 68 |  |
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
| 36 | `lay-size` | переменная | src/backend.fth:14 | 13 |  |
| 37 | `lay-a` | переменная | src/backend.fth:14 | 19 |  |
| 38 | `lay-slots` | переменная | src/backend.fth:14 | 16 |  |
| 39 | `lay-cell-bits` | переменная | src/backend.fth:14 | 15 |  |
| 40 | `lay-chunk` | переменная | src/backend.fth:15 | 8 |  |
| 41 | `lay-chunk-buf` | переменная | src/backend.fth:15 | 6 |  |
| 42 | `lay-lbuf` | переменная | src/backend.fth:15 | 6 |  |
| 43 | `lay-pool` | переменная | src/backend.fth:15 | 5 |  |
| 44 | `lay-ebuf` | переменная | src/backend.fth:16 | 4 |  |
| 45 | `lay-dest` | переменная | src/backend.fth:16 | 6 |  |
| 46 | `lay-sink` | переменная | src/backend.fth:16 | 5 |  |
| 47 | `lay-start-cell` | переменная | src/backend.fth:16 | 3 |  |
| 48 | `lay-rev` | данные `create` | src/backend.fth:18 | 10 |  |
| 49 | `lay-rev-init` | определение `:` | src/backend.fth:19 | 1 |  |
| 50 | `lay-inst` | определение `:` | src/backend.fth:23 | 10 |  |
| 51 | `lay-layer-bits` | определение `:` | src/backend.fth:24 | 8 |  |
| 52 | `lay-lbytes` | определение `:` | src/backend.fth:25 | 6 |  |
| 53 | `lay-stdin` | определение `:` | src/backend.fth:26 | 4 |  |
| 54 | `lay-stdout` | определение `:` | src/backend.fth:27 | 3 |  |
| 55 | `lay-bits` | определение `:` | src/backend.fth:28 | 7 |  |
| 56 | `lay-numeric` | определение `:` | src/backend.fth:29 | 7 |  |
| 57 | `lay-numeric4` | определение `:` | src/backend.fth:35 | 1 |  |
| 58 | `lay-field-check` | определение `:` | src/backend.fth:38 | 1 |  |
| 59 | `lay-encode` | определение `:` | src/backend.fth:41 | 3 |  |
| 60 | `lay-start` | переменная | src/backend.fth:51 | 8 |  |
| 61 | `lay-len` | переменная | src/backend.fth:51 | 10 |  |
| 62 | `lay-rows` | данные `create` | src/backend.fth:52 | 6 |  |
| 63 | `lay-row!` | определение `:` | src/backend.fth:53 | 7 |  |
| 64 | `lay-clear-rows` | определение `:` | src/backend.fth:55 | 3 |  |
| 65 | `lay-loader` | определение `:` | src/backend.fth:56 | 1 |  |
| 66 | `lay-stream-flush` | определение `:` | src/backend.fth:63 | 3 |  |
| 67 | `lay-begin-chunk` | определение `:` | src/backend.fth:67 | 2 |  |
| 68 | `lay-put` | определение `:` | src/backend.fth:69 | 14 |  |
| 69 | `lay-scratch` | данные `create` | src/backend.fth:87 | 2 |  |
| 70 | `lay-put-numeric` | определение `:` | src/backend.fth:88 | 3 |  |
| 71 | `lay-max-layers` | константа | src/backend.fth:93 | 4 |  |
| 72 | `lay-record` | определение `:` | src/backend.fth:94 | 2 |  |
| 73 | `lay-pending` | переменная | src/backend.fth:95 | 10 |  |
| 74 | `lay-head` | переменная | src/backend.fth:95 | 6 |  |
| 75 | `lay-next-cell` | переменная | src/backend.fth:95 | 8 |  |
| 76 | `lay-seq#` | переменная | src/backend.fth:96 | 8 |  |
| 77 | `lay-seq-first` | переменная | src/backend.fth:96 | 3 |  |
| 78 | `lay-seq-entry` | переменная | src/backend.fth:96 | 2 |  |
| 79 | `lay-seq-last` | переменная | src/backend.fth:96 | 2 |  |
| 80 | `lay-foff` | данные `create` | src/backend.fth:98 | 2 |  |
| 81 | `lay-foff-init` | определение `:` | src/backend.fth:99 | 1 |  |
| 82 | `lay-machine` | определение `:` | src/backend.fth:100 | 1 |  |
| 83 | `lay-field` | определение `:` | src/backend.fth:117 | 44 |  |
| 84 | `lay-link-row` | основание | src/backend.fth:118 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 85 | `lay-copy` | основание | src/backend.fth:119 | 80 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 86 | `lay-builder` | определение `:` | src/backend.fth:121 | 1 |  |
| 87 | `lay-new-cell` | определение `:` | src/backend.fth:122 | 13 |  |
| 88 | `lay-branch-bit` | определение `:` | src/backend.fth:125 | 16 |  |
| 89 | `lay-branch-step` | определение `:` | src/backend.fth:126 | 3 |  |
| 90 | `lay-group` | определение `:` | src/backend.fth:128 | 5 |  |
| 91 | `lay-layer-cell` | определение `:` | src/backend.fth:131 | 40 |  |
| 92 | `lay-next!` | определение `:` | src/backend.fth:132 | 18 |  |
| 93 | `lay-count` | определение `:` | src/backend.fth:133 | 7 |  |
| 94 | `lay-row-addr` | определение `:` | src/backend.fth:134 | 4 |  |
| 95 | `lay-pending@` | определение `:` | src/backend.fth:135 | 5 |  |
| 96 | `lay-encode-layer` | определение `:` | src/backend.fth:136 | 1 |  |
| 97 | `lay-on-write` | переменная | src/backend.fth:143 | 6 |  |
| 98 | `lay-write` | определение `:` | src/backend.fth:144 | 2 |  |
| 99 | `lay-write-oldest` | определение `:` | src/backend.fth:147 | 1 |  |
| 100 | `lay-new-record` | основание | src/backend.fth:148 | 9 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 101 | `lay-lone` | основание | src/backend.fth:152 | 5 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 102 | `lay-seq` | определение `:` | src/backend.fth:153 | 9 |  |
| 103 | `lay-last` | определение `:` | src/backend.fth:154 | 4 |  |
| 104 | `lay-layer` | основание | src/backend.fth:155 | 82 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 105 | `lay-entry` | определение `:` | src/backend.fth:160 | 4 |  |
| 106 | `lay-jump` | определение `:` | src/backend.fth:161 | 13 |  |
| 107 | `lay-l1` | переменная | src/backend.fth:162 | 4 |  |
| 108 | `lay-h1` | переменная | src/backend.fth:162 | 3 |  |
| 109 | `lay-l2` | переменная | src/backend.fth:162 | 4 |  |
| 110 | `lay-h2` | переменная | src/backend.fth:162 | 3 |  |
| 111 | `lay-ra` | переменная | src/backend.fth:163 | 2 |  |
| 112 | `lay-rb` | переменная | src/backend.fth:163 | 2 |  |
| 113 | `lay-cur` | переменная | src/backend.fth:163 | 7 |  |
| 114 | `lay-clash?` | определение `:` | src/backend.fth:165 | 1 |  |
| 115 | `lay-row-clash?` | определение `:` | src/backend.fth:170 | 1 |  |
| 116 | `lay-new-row` | данные `create` | src/backend.fth:175 | 6 |  |
| 117 | `lay-row-set` | определение `:` | src/backend.fth:176 | 2 |  |
| 118 | `lay-full?` | определение `:` | src/backend.fth:178 | 2 |  |
| 119 | `lay-clashes?` | определение `:` | src/backend.fth:179 | 2 |  |
| 120 | `lay-fits?` | определение `:` | src/backend.fth:184 | 2 |  |
| 121 | `lay-row` | основание | src/backend.fth:186 | 81 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 122 | `lay-flush` | определение `:` | src/backend.fth:190 | 14 |  |
| 123 | `lay-finish` | определение `:` | src/backend.fth:193 | 1 |  |
| 124 | `dj-reader` | переменная | src/backend.fth:212 | 3 |  |
| 125 | `dj-bad-cell` | переменная | src/backend.fth:212 | 1 |  |
| 126 | `dj-bad-rule` | переменная | src/backend.fth:212 | 4 |  |
| 127 | `dj-bsh` | переменная | src/backend.fth:213 | 3 |  |
| 128 | `dj-csh` | переменная | src/backend.fth:213 | 6 |  |
| 129 | `dj-ssh` | переменная | src/backend.fth:213 | 2 |  |
| 130 | `dj-fsh` | переменная | src/backend.fth:213 | 2 |  |
| 131 | `dj-first` | переменная | src/backend.fth:214 | 2 |  |
| 132 | `dj-end` | переменная | src/backend.fth:214 | 2 |  |
| 133 | `dj-pa` | переменная | src/backend.fth:214 | 3 |  |
| 134 | `dj-cb` | переменная | src/backend.fth:214 | 8 |  |
| 135 | `dj-vdl` | переменная | src/backend.fth:215 | 16 |  |
| 136 | `dj-vdh` | переменная | src/backend.fth:215 | 12 |  |
| 137 | `dj-vsl` | переменная | src/backend.fth:215 | 14 |  |
| 138 | `dj-vsh` | переменная | src/backend.fth:215 | 12 |  |
| 139 | `dj-tc` | переменная | src/backend.fth:216 | 5 |  |
| 140 | `dj-ts` | переменная | src/backend.fth:216 | 6 |  |
| 141 | `dj-tf` | переменная | src/backend.fth:216 | 5 |  |
| 142 | `dj-tb` | переменная | src/backend.fth:216 | 2 |  |
| 143 | `dj-tn` | переменная | src/backend.fth:216 | 2 |  |
| 144 | `dj-tk` | переменная | src/backend.fth:216 | 7 |  |
| 145 | `dj-vt` | переменная | src/backend.fth:216 | 3 |  |
| 146 | `dj-blk` | переменная | src/backend.fth:217 | 5 |  |
| 147 | `dj-pr` | данные `create` | src/backend.fth:218 | 2 |  |
| 148 | `dj-tr` | данные `create` | src/backend.fth:218 | 3 |  |
| 149 | `dj-narrow` | константа | src/backend.fth:219 | 1 |  |
| 150 | `dj-seen` | данные `create` | src/backend.fth:221 | 2 |  |
| 151 | `dj-nseen` | переменная | src/backend.fth:221 | 6 |  |
| 152 | `dj-get` | определение `:` | src/backend.fth:222 | 9 |  |
| 153 | `dj-fail` | определение `:` | src/backend.fth:223 | 6 |  |
| 154 | `dj-blk?` | определение `:` | src/backend.fth:224 | 5 |  |
| 155 | `dj-in?` | определение `:` | src/backend.fth:226 | 4 |  |
| 156 | `dj-row!` | определение `:` | src/backend.fth:229 | 2 |  |
| 157 | `dj-row@` | определение `:` | src/backend.fth:231 | 3 |  |
| 158 | `dj-nop?` | определение `:` | src/backend.fth:234 | 4 |  |
| 159 | `dj-load` | определение `:` | src/backend.fth:236 | 1 |  |
| 160 | `dj-row-ok?` | определение `:` | src/backend.fth:245 | 1 |  |
| 161 | `dj-in-blk?` | определение `:` | src/backend.fth:251 | 2 |  |
| 162 | `dj-touches?` | определение `:` | src/backend.fth:256 | 1 |  |
| 163 | `dj-seen?` | определение `:` | src/backend.fth:257 | 1 |  |
| 164 | `dj-seen!` | определение `:` | src/backend.fth:262 | 1 |  |
| 165 | `dj-wide` | определение `:` | src/backend.fth:268 | 1 |  |
| 166 | `dj-patch` | определение `:` | src/backend.fth:285 | 1 |  |
| 167 | `dj-nn` | переменная | src/backend.fth:296 | 4 |  |
| 168 | `dj-lo` | переменная | src/backend.fth:296 | 2 |  |
| 169 | `dj-hi` | переменная | src/backend.fth:296 | 2 |  |
| 170 | `dj-scan` | определение `:` | src/backend.fth:297 | 1 |  |
| 171 | `dj-rows` | определение `:` | src/backend.fth:307 | 1 |  |
| 172 | `dj-prove` | определение `:` | src/backend.fth:314 | 2 |  |
| 173 | `lay-t1` | переменная | src/compute.fth:10 | 25 |  |
| 174 | `lay-t2` | переменная | src/compute.fth:10 | 13 |  |
| 175 | `lay-t3` | переменная | src/compute.fth:10 | 7 |  |
| 176 | `lay-t4` | переменная | src/compute.fth:10 | 4 |  |
| 177 | `lay-t5` | переменная | src/compute.fth:10 | 8 |  |
| 178 | `lay-lo` | переменная | src/compute.fth:11 | 5 |  |
| 179 | `lay-hi` | переменная | src/compute.fth:11 | 2 |  |
| 180 | `lay-l0` | переменная | src/compute.fth:12 | 21 |  |
| 181 | `lay-l1` | переменная | src/compute.fth:12 | 13 | вариант 2 |
| 182 | `lay-l2` | переменная | src/compute.fth:12 | 8 | вариант 2 |
| 183 | `lay-l3` | переменная | src/compute.fth:12 | 7 |  |
| 184 | `lay-l4` | переменная | src/compute.fth:12 | 7 |  |
| 185 | `lay-l5` | переменная | src/compute.fth:12 | 6 |  |
| 186 | `lay-work` | определение `:` | src/compute.fth:13 | 3 |  |
| 187 | `lay-cell-bit` | определение `:` | src/compute.fth:14 | 2 |  |
| 188 | `lay-link-slot` | определение `:` | src/compute.fth:15 | 6 |  |
| 189 | `lay-item-cells` | константа | src/compute.fth:17 | 1 |  |
| 190 | `lay-max-items` | константа | src/compute.fth:17 | 2 |  |
| 191 | `lay-items` | данные `create` | src/compute.fth:18 | 1 |  |
| 192 | `lay-nitems` | переменная | src/compute.fth:19 | 8 |  |
| 193 | `lay-item@` | определение `:` | src/compute.fth:20 | 6 |  |
| 194 | `lay-lookups-begin` | определение `:` | src/compute.fth:21 | 14 |  |
| 195 | `lay-item` | определение `:` | src/compute.fth:22 | 12 |  |
| 196 | `lay-seg` | определение `:` | src/compute.fth:27 | 18 |  |
| 197 | `lay-sl` | данные `create` | src/compute.fth:33 | 2 |  |
| 198 | `lay-sh` | данные `create` | src/compute.fth:33 | 2 |  |
| 199 | `lay-read-layer` | данные `create` | src/compute.fth:34 | 2 |  |
| 200 | `lay-read-slot` | данные `create` | src/compute.fth:34 | 2 |  |
| 201 | `lay-used` | данные `create` | src/compute.fth:35 | 2 |  |
| 202 | `lay-nused` | переменная | src/compute.fth:35 | 5 |  |
| 203 | `lay-rl` | переменная | src/compute.fth:35 | 6 |  |
| 204 | `lay-pk` | переменная | src/compute.fth:35 | 4 |  |
| 205 | `lay-pkl` | переменная | src/compute.fth:35 | 4 |  |
| 206 | `lay-npatches` | определение `:` | src/compute.fth:36 | 1 |  |
| 207 | `lay-used?` | определение `:` | src/compute.fth:37 | 1 |  |
| 208 | `lay-place-reads` | определение `:` | src/compute.fth:39 | 1 |  |
| 209 | `lay-patch` | определение `:` | src/compute.fth:51 | 1 |  |
| 210 | `lay-lookups` | определение `:` | src/compute.fth:60 | 14 |  |
| 211 | `lay-al` | данные `create` | src/compute.fth:67 | 2 |  |
| 212 | `lay-ar` | данные `create` | src/compute.fth:67 | 2 |  |
| 213 | `lay-ax` | переменная | src/compute.fth:68 | 4 |  |
| 214 | `lay-aa` | переменная | src/compute.fth:68 | 2 |  |
| 215 | `lay-ab` | переменная | src/compute.fth:68 | 2 |  |
| 216 | `lay-atab` | переменная | src/compute.fth:68 | 2 |  |
| 217 | `lay-acarry` | переменная | src/compute.fth:68 | 2 |  |
| 218 | `lay-al@` | определение `:` | src/compute.fth:69 | 8 |  |
| 219 | `lay-rd` | определение `:` | src/compute.fth:70 | 3 |  |
| 220 | `lay-adder-patch` | определение `:` | src/compute.fth:71 | 4 |  |
| 221 | `lay-adder` | определение `:` | src/compute.fth:76 | 6 |  |
| 222 | `lay-dsrc` | переменная | src/compute.fth:93 | 3 |  |
| 223 | `lay-dk` | переменная | src/compute.fth:93 | 5 |  |
| 224 | `lay-dg` | переменная | src/compute.fth:93 | 3 |  |
| 225 | `lay-dp` | переменная | src/compute.fth:93 | 3 |  |
| 226 | `lay-dx` | переменная | src/compute.fth:93 | 4 |  |
| 227 | `lay-decide` | определение `:` | src/compute.fth:94 | 2 |  |
| 228 | `lay-table-at` | переменная | src/compute.fth:102 | 4 |  |
| 229 | `lay-table-limit` | переменная | src/compute.fth:102 | 2 |  |
| 230 | `lay-tbuf` | переменная | src/compute.fth:102 | 7 |  |
| 231 | `lay-tx` | переменная | src/compute.fth:103 | 5 |  |
| 232 | `lay-tbits` | переменная | src/compute.fth:103 | 4 |  |
| 233 | `lay-ts` | переменная | src/compute.fth:103 | 6 |  |
| 234 | `lay-tsize` | переменная | src/compute.fth:103 | 7 |  |
| 235 | `lay-tbase` | переменная | src/compute.fth:103 | 4 |  |
| 236 | `lay-tper` | переменная | src/compute.fth:103 | 3 |  |
| 237 | `lay-tables` | определение `:` | src/compute.fth:104 | 2 |  |
| 238 | `lay-table-area` | определение `:` | src/compute.fth:105 | 2 |  |
| 239 | `lay-table-done` | определение `:` | src/compute.fth:113 | 2 |  |
| 240 | `lay-table` | определение `:` | src/compute.fth:116 | 23 |  |
| 241 | `lay-add-entry` | определение `:` | src/compute.fth:133 | 1 |  |
| 242 | `lay-sub-entry` | определение `:` | src/compute.fth:135 | 2 |  |
| 243 | `lay-xor-entry` | определение `:` | src/compute.fth:137 | 1 |  |
| 244 | `lay-or-entry` | определение `:` | src/compute.fth:138 | 1 |  |
| 245 | `lay-and-entry` | определение `:` | src/compute.fth:139 | 1 |  |
| 246 | `lay-or8-entry` | определение `:` | src/compute.fth:140 | 1 |  |
| 247 | `lay-fz` | переменная | src/compute.fth:141 | 3 |  |
| 248 | `lay-fu` | переменная | src/compute.fth:141 | 4 |  |
| 249 | `lay-fs` | переменная | src/compute.fth:141 | 3 |  |
| 250 | `lay-pair` | определение `:` | src/compute.fth:142 | 6 |  |
| 251 | `lay-flags-entry` | определение `:` | src/compute.fth:143 | 1 |  |
| 252 | `lay-not5-entry` | определение `:` | src/compute.fth:150 | 1 |  |
| 253 | `lay-sign-entry` | определение `:` | src/compute.fth:151 | 1 |  |
| 254 | `lay-fill24-entry` | определение `:` | src/compute.fth:152 | 1 |  |
| 255 | `lay-fill16-entry` | определение `:` | src/compute.fth:153 | 1 |  |
| 256 | `lay-inc1-entry` | определение `:` | src/compute.fth:154 | 1 |  |
| 257 | `lay-inc2-entry` | определение `:` | src/compute.fth:155 | 1 |  |
| 258 | `lay-t-add` | переменная | src/compute.fth:156 | 7 |  |
| 259 | `lay-t-sub` | переменная | src/compute.fth:156 | 5 |  |
| 260 | `lay-t-xor` | переменная | src/compute.fth:156 | 5 |  |
| 261 | `lay-t-or` | переменная | src/compute.fth:156 | 2 |  |
| 262 | `lay-t-and` | переменная | src/compute.fth:156 | 2 |  |
| 263 | `lay-t-or8` | переменная | src/compute.fth:157 | 2 |  |
| 264 | `lay-t-flags` | переменная | src/compute.fth:157 | 2 |  |
| 265 | `lay-t-not5` | переменная | src/compute.fth:157 | 2 |  |
| 266 | `lay-t-sign32` | переменная | src/compute.fth:157 | 2 |  |
| 267 | `lay-t-fill24` | переменная | src/compute.fth:158 | 1 |  |
| 268 | `lay-t-fill16` | переменная | src/compute.fth:158 | 1 |  |
| 269 | `lay-t-inc1` | переменная | src/compute.fth:158 | 1 |  |
| 270 | `lay-t-inc2` | переменная | src/compute.fth:158 | 1 |  |
| 271 | `lay-standard-tables` | определение `:` | src/compute.fth:159 | 1 |  |
| 272 | `lay-oo` | переменная | src/compute.fth:168 | 2 |  |
| 273 | `lay-os` | переменная | src/compute.fth:168 | 2 |  |
| 274 | `lay-ol` | переменная | src/compute.fth:168 | 4 |  |
| 275 | `lay-oh` | переменная | src/compute.fth:168 | 3 |  |
| 276 | `lay-or-chunks` | определение `:` | src/compute.fth:169 | 3 |  |
| 277 | `lay-cr` | переменная | src/compute.fth:175 | 5 |  |
| 278 | `lay-ca` | переменная | src/compute.fth:175 | 4 |  |
| 279 | `lay-cb` | переменная | src/compute.fth:175 | 4 |  |
| 280 | `lay-logic` | определение `:` | src/compute.fth:182 | 4 |  |
| 281 | `lay-sres` | переменная | src/compute.fth:188 | 3 |  |
| 282 | `lay-sa` | переменная | src/compute.fth:188 | 7 |  |
| 283 | `lay-samt` | переменная | src/compute.fth:188 | 8 |  |
| 284 | `lay-sw` | переменная | src/compute.fth:188 | 9 |  |
| 285 | `lay-szero` | переменная | src/compute.fth:188 | 4 |  |
| 286 | `lay-sarg` | переменная | src/compute.fth:189 | 6 |  |
| 287 | `lay-sign` | переменная | src/compute.fth:189 | 6 |  |
| 288 | `lay-shift-row` | определение `:` | src/compute.fth:190 | 3 |  |
| 289 | `lay-shift-patch` | определение `:` | src/compute.fth:191 | 6 |  |
| 290 | `lay-shift-right` | определение `:` | src/compute.fth:193 | 1 |  |
| 291 | `lay-shift-left` | определение `:` | src/compute.fth:210 | 1 |  |
| 292 | `fc-size` | константа | src/forthc.fth:11 | 2 |  |
| 293 | `fc-cellb` | константа | src/forthc.fth:11 | 7 |  |
| 294 | `fc-l` | константа | src/forthc.fth:11 | 1 |  |
| 295 | `fc-a` | константа | src/forthc.fth:11 | 2 |  |
| 296 | `fc-d` | переменная | src/forthc.fth:16 | 3 |  |
| 297 | `fc-first` | переменная | src/forthc.fth:16 | 3 |  |
| 298 | `fc-guard` | переменная | src/forthc.fth:21 | 18 |  |
| 299 | `fc-bbits` | константа | src/forthc.fth:28 | 11 |  |
| 300 | `fc-abits` | константа | src/forthc.fth:28 | 5 |  |
| 301 | `fc-ebits` | константа | src/forthc.fth:28 | 2 |  |
| 302 | `fc-etab` | константа | src/forthc.fth:28 | 3 |  |
| 303 | `fc-layout` | определение `:` | src/forthc.fth:29 | 1 |  |
| 304 | `fc-d+` | определение `:` | src/forthc.fth:31 | 27 |  |
| 305 | `fc-sp` | определение `:` | src/forthc.fth:32 | 6 |  |
| 306 | `fc-rp` | определение `:` | src/forthc.fth:32 | 18 |  |
| 307 | `fc-handler` | определение `:` | src/forthc.fth:32 | 6 |  |
| 308 | `fc-code` | определение `:` | src/forthc.fth:32 | 4 |  |
| 309 | `fc-regs` | определение `:` | src/forthc.fth:33 | 2 |  |
| 310 | `fc-nregs` | константа | src/forthc.fth:33 | 2 |  |
| 311 | `fc-tmp` | определение `:` | src/forthc.fth:34 | 12 |  |
| 312 | `fc-xr` | определение `:` | src/forthc.fth:34 | 10 |  |
| 313 | `fc-z` | определение `:` | src/forthc.fth:34 | 4 |  |
| 314 | `fc-idx` | определение `:` | src/forthc.fth:34 | 5 |  |
| 315 | `fc-ma` | определение `:` | src/forthc.fth:35 | 6 |  |
| 316 | `fc-mb` | определение `:` | src/forthc.fth:35 | 6 |  |
| 317 | `fc-mp` | определение `:` | src/forthc.fth:35 | 2 |  |
| 318 | `fc-mq` | определение `:` | src/forthc.fth:35 | 3 |  |
| 319 | `fc-mr` | определение `:` | src/forthc.fth:35 | 3 |  |
| 320 | `fc-zero` | определение `:` | src/forthc.fth:36 | 12 |  |
| 321 | `fc-consts` | определение `:` | src/forthc.fth:36 | 3 |  |
| 322 | `fc-sw` | определение `:` | src/forthc.fth:37 | 2 |  |
| 323 | `fc-su` | определение `:` | src/forthc.fth:37 | 1 |  |
| 324 | `fc-key` | определение `:` | src/forthc.fth:37 | 3 |  |
| 325 | `fc-bp` | определение `:` | src/forthc.fth:37 | 2 |  |
| 326 | `fc-tab` | определение `:` | src/forthc.fth:38 | 1 |  |
| 327 | `fc-stk` | определение `:` | src/forthc.fth:38 | 3 |  |
| 328 | `fc-rstk` | определение `:` | src/forthc.fth:39 | 16 |  |
| 329 | `fc-scr0` | определение `:` | src/forthc.fth:39 | 1 |  |
| 330 | `fc-links` | определение `:` | src/forthc.fth:40 | 2 |  |
| 331 | `fc-max-links` | константа | src/forthc.fth:40 | 1 |  |
| 332 | `fc-link-chunk` | константа | src/forthc.fth:40 | 2 |  |
| 333 | `fc-mem` | определение `:` | src/forthc.fth:41 | 7 |  |
| 334 | `fc-mw` | константа | src/forthc.fth:41 | 2 |  |
| 335 | `fc-htab` | определение `:` | src/forthc.fth:41 | 1 |  |
| 336 | `fc-data-start` | константа | src/forthc.fth:42 | 1 |  |
| 337 | `fc-off` | данные `create` | src/forthc.fth:45 | 2 |  |
| 338 | `fc-oc` | переменная | src/forthc.fth:45 | 2 |  |
| 339 | `fc-t-rev8` | переменная | src/forthc.fth:46 | 3 |  |
| 340 | `fc-t-zero32` | переменная | src/forthc.fth:46 | 2 |  |
| 341 | `fc-t-nz2` | переменная | src/forthc.fth:46 | 2 |  |
| 342 | `fc-t-lt32` | переменная | src/forthc.fth:46 | 2 |  |
| 343 | `fc-t-xr2` | переменная | src/forthc.fth:47 | 2 |  |
| 344 | `fc-t-ult32` | переменная | src/forthc.fth:47 | 2 |  |
| 345 | `fc-t-bytepos` | переменная | src/forthc.fth:47 | 2 |  |
| 346 | `fc-off@` | определение `:` | src/forthc.fth:48 | 3 |  |
| 347 | `fc-off-table` | определение `:` | src/forthc.fth:50 | 1 |  |
| 348 | `fc-rev-entry` | определение `:` | src/forthc.fth:53 | 1 |  |
| 349 | `fc-zero-entry` | определение `:` | src/forthc.fth:54 | 1 |  |
| 350 | `fc-nz-entry` | определение `:` | src/forthc.fth:55 | 1 |  |
| 351 | `fc-lt-entry` | определение `:` | src/forthc.fth:56 | 1 |  |
| 352 | `fc-xr2-entry` | определение `:` | src/forthc.fth:59 | 1 |  |
| 353 | `fc-ult-entry` | определение `:` | src/forthc.fth:60 | 1 |  |
| 354 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:62 | 1 |  |
| 355 | `fc-tables` | определение `:` | src/forthc.fth:63 | 1 |  |
| 356 | `fc-mul4-entry` | определение `:` | src/forthc.fth:74 | 1 |  |
| 357 | `fc-qsel-entry` | определение `:` | src/forthc.fth:77 | 1 |  |
| 358 | `fc-max-consts` | переменная | src/forthc.fth:82 | 5 | вход бута (хост) |
| 359 | `fc-ck` | переменная | src/forthc.fth:82 | 3 |  |
| 360 | `fc-nconsts` | переменная | src/forthc.fth:82 | 7 |  |
| 361 | `fc-nbuckets` | переменная | src/forthc.fth:83 | 9 | вход бута (хост) |
| 362 | `fc-cbk` | переменная | src/forthc.fth:83 | 3 |  |
| 363 | `fc-ck@` | определение `:` | src/forthc.fth:84 | 3 |  |
| 364 | `fc-chash` | определение `:` | src/forthc.fth:85 | 1 |  |
| 365 | `fc-cb` | переменная | src/forthc.fth:86 | 3 |  |
| 366 | `fc-const2` | определение `:` | src/forthc.fth:87 | 1 |  |
| 367 | `fc-const` | определение `:` | src/forthc.fth:97 | 5 |  |
| 368 | `fc-lit` | определение `:` | src/forthc.fth:105 | 3 |  |
| 369 | `fc-bit0` | определение `:` | src/forthc.fth:106 | 1 |  |
| 370 | `fc-bit1` | определение `:` | src/forthc.fth:107 | 1 |  |
| 371 | `fc-length` | определение `:` | src/forthc.fth:108 | 1 |  |
| 372 | `fc-lit-of` | определение `:` | src/forthc.fth:109 | 2 |  |
| 373 | `fc-load` | определение `:` | src/forthc.fth:113 | 2 |  |
| 374 | `fc-nlinks` | переменная | src/forthc.fth:117 | 5 |  |
| 375 | `fc-link-buf` | переменная | src/forthc.fth:117 | 4 |  |
| 376 | `fc-nbuf` | переменная | src/forthc.fth:117 | 8 |  |
| 377 | `fc-put-links` | определение `:` | src/forthc.fth:118 | 2 |  |
| 378 | `fc-link-const` | определение `:` | src/forthc.fth:122 | 4 |  |
| 379 | `fc-eight` | данные `create` | src/forthc.fth:127 | 7 |  |
| 380 | `fc-zeros` | данные `create` | src/forthc.fth:127 | 5 |  |
| 381 | `fc-put-consts` | определение `:` | src/forthc.fth:128 | 1 |  |
| 382 | `fc-cache` | данные `create` | src/forthc.fth:136 | 8 |  |
| 383 | `fc-n` | переменная | src/forthc.fth:136 | 31 |  |
| 384 | `fc-pin` | данные `create` | src/forthc.fth:137 | 10 |  |
| 385 | `fc-npin` | переменная | src/forthc.fth:137 | 21 |  |
| 386 | `fc-c@` | определение `:` | src/forthc.fth:138 | 8 |  |
| 387 | `fc-push` | определение `:` | src/forthc.fth:139 | 30 |  |
| 388 | `fc-pop1` | определение `:` | src/forthc.fth:140 | 30 |  |
| 389 | `fc-in?` | определение `:` | src/forthc.fth:141 | 3 |  |
| 390 | `fc-reg` | определение `:` | src/forthc.fth:142 | 18 |  |
| 391 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:147 | 1 |  |
| 392 | `fc-scr` | переменная | src/forthc.fth:148 | 3 |  |
| 393 | `fc-scratch` | определение `:` | src/forthc.fth:149 | 11 |  |
| 394 | `fc-offs` | данные `create` | src/forthc.fth:153 | 5 |  |
| 395 | `fc-noff` | переменная | src/forthc.fth:153 | 9 |  |
| 396 | `fc-ptr` | переменная | src/forthc.fth:153 | 4 |  |
| 397 | `fc-iw` | переменная | src/forthc.fth:155 | 4 |  |
| 398 | `fc-adjust` | определение `:` | src/forthc.fth:156 | 7 |  |
| 399 | `fc-prow` | данные `create` | src/forthc.fth:162 | 2 |  |
| 400 | `fc-nrow` | переменная | src/forthc.fth:162 | 8 |  |
| 401 | `fc-pl` | данные `create` | src/forthc.fth:163 | 2 |  |
| 402 | `fc-pslot` | данные `create` | src/forthc.fth:163 | 2 |  |
| 403 | `fc-rl` | переменная | src/forthc.fth:164 | 3 |  |
| 404 | `fc-f0` | переменная | src/forthc.fth:164 | 2 |  |
| 405 | `fc-f1` | переменная | src/forthc.fth:164 | 2 |  |
| 406 | `fc-psh` | переменная | src/forthc.fth:164 | 2 |  |
| 407 | `fc-row+` | определение `:` | src/forthc.fth:165 | 3 |  |
| 408 | `fc-4@` | определение `:` | src/forthc.fth:167 | 3 |  |
| 409 | `fc-patched` | определение `:` | src/forthc.fth:169 | 3 |  |
| 410 | `fc-popped` | данные `create` | src/forthc.fth:181 | 2 |  |
| 411 | `fc-srcs` | данные `create` | src/forthc.fth:181 | 16 |  |
| 412 | `fc-nsrc` | переменная | src/forthc.fth:181 | 21 |  |
| 413 | `fc-mbase` | переменная | src/forthc.fth:182 | 8 |  |
| 414 | `fc-mptr` | переменная | src/forthc.fth:182 | 4 |  |
| 415 | `fc-mn` | переменная | src/forthc.fth:182 | 7 |  |
| 416 | `fc-mw2` | переменная | src/forthc.fth:182 | 6 |  |
| 417 | `fc-popped@` | определение `:` | src/forthc.fth:183 | 10 |  |
| 418 | `fc-shift` | определение `:` | src/forthc.fth:184 | 4 |  |
| 419 | `fc-mem-pop` | определение `:` | src/forthc.fth:185 | 5 |  |
| 420 | `fc-push-group` | определение `:` | src/forthc.fth:193 | 2 |  |
| 421 | `fc-dup-at` | определение `:` | src/forthc.fth:201 | 1 |  |
| 422 | `fc-rest` | данные `create` | src/forthc.fth:203 | 2 |  |
| 423 | `fc-nrest` | переменная | src/forthc.fth:203 | 3 |  |
| 424 | `fc-mem-push` | определение `:` | src/forthc.fth:204 | 8 |  |
| 425 | `fc-src1` | определение `:` | src/forthc.fth:210 | 3 |  |
| 426 | `fc-need` | определение `:` | src/forthc.fth:212 | 15 |  |
| 427 | `fc-spill` | определение `:` | src/forthc.fth:219 | 19 |  |
| 428 | `fc-pop` | определение `:` | src/forthc.fth:225 | 13 |  |
| 429 | `fc-max-log` | константа | src/forthc.fth:233 | 2 |  |
| 430 | `fc-max-notes` | константа | src/forthc.fth:233 | 6 |  |
| 431 | `fc-log` | переменная | src/forthc.fth:234 | 3 |  |
| 432 | `fc-nlog` | переменная | src/forthc.fth:234 | 5 |  |
| 433 | `fc-decs` | переменная | src/forthc.fth:234 | 2 |  |
| 434 | `fc-ndec` | переменная | src/forthc.fth:234 | 6 |  |
| 435 | `fc-calls` | переменная | src/forthc.fth:234 | 2 |  |
| 436 | `fc-ncall` | переменная | src/forthc.fth:234 | 6 |  |
| 437 | `fc-pend` | переменная | src/forthc.fth:235 | 2 |  |
| 438 | `fc-npend` | переменная | src/forthc.fth:235 | 9 |  |
| 439 | `fc-unknown` | переменная | src/forthc.fth:235 | 7 |  |
| 440 | `fc-lc` | переменная | src/forthc.fth:236 | 3 |  |
| 441 | `fc-lb` | переменная | src/forthc.fth:236 | 3 |  |
| 442 | `fc-row-n` | определение `:` | src/forthc.fth:239 | 1 |  |
| 443 | `fc-mem-row?` | определение `:` | src/forthc.fth:240 | 1 |  |
| 444 | `fc-log-layer` | определение `:` | src/forthc.fth:241 | 2 |  |
| 445 | `fc-log-begin` | определение `:` | src/forthc.fth:252 | 3 |  |
| 446 | `fc-log-end` | определение `:` | src/forthc.fth:254 | 4 |  |
| 447 | `fc-by-execution` | определение `:` | src/forthc.fth:256 | 8 |  |
| 448 | `fc-dec@` | определение `:` | src/forthc.fth:257 | 2 |  |
| 449 | `fc-call@` | определение `:` | src/forthc.fth:258 | 2 |  |
| 450 | `fc-log-decision` | определение `:` | src/forthc.fth:260 | 2 |  |
| 451 | `fc-log-call` | определение `:` | src/forthc.fth:266 | 2 |  |
| 452 | `fc-callee` | переменная | src/forthc.fth:270 | 4 |  |
| 453 | `fc-live` | переменная | src/forthc.fth:273 | 7 |  |
| 454 | `fc-tramp` | переменная | src/forthc.fth:273 | 8 |  |
| 455 | `fc-ex` | переменная | src/forthc.fth:273 | 4 |  |
| 456 | `fc-thrower` | переменная | src/forthc.fth:273 | 4 |  |
| 457 | `fc-jump` | определение `:` | src/forthc.fth:274 | 7 |  |
| 458 | `fc-end` | определение `:` | src/forthc.fth:275 | 14 |  |
| 459 | `fc-begin-block` | определение `:` | src/forthc.fth:277 | 24 |  |
| 460 | `fc-rows1` | определение `:` | src/forthc.fth:281 | 15 |  |
| 461 | `fc-nonzero` | определение `:` | src/forthc.fth:282 | 2 |  |
| 462 | `fc-branch` | определение `:` | src/forthc.fth:285 | 6 |  |
| 463 | `fc-call` | определение `:` | src/forthc.fth:287 | 4 |  |
| 464 | `fc-v0` | переменная | src/forthc.fth:291 | 4 |  |
| 465 | `fc-v1` | переменная | src/forthc.fth:291 | 4 |  |
| 466 | `fc-jw` | определение `:` | src/forthc.fth:295 | 2 |  |
| 467 | `fc-xw` | определение `:` | src/forthc.fth:299 | 2 |  |
| 468 | `fc-xoff` | определение `:` | src/forthc.fth:300 | 2 |  |
| 469 | `fc-etab-at` | определение `:` | src/forthc.fth:301 | 1 |  |
| 470 | `fc-ex-base` | определение `:` | src/forthc.fth:302 | 1 |  |
| 471 | `fc-call-indirect` | определение `:` | src/forthc.fth:303 | 2 |  |
| 472 | `fc-push-frame` | определение `:` | src/forthc.fth:310 | 2 |  |
| 473 | `fc-link-copy` | определение `:` | src/forthc.fth:316 | 1 |  |
| 474 | `fc-restore` | определение `:` | src/forthc.fth:321 | 3 |  |
| 475 | `fc-build-thrower` | определение `:` | src/forthc.fth:323 | 1 |  |
| 476 | `fc-throw` | определение `:` | src/forthc.fth:329 | 1 |  |
| 477 | `fc-catch` | определение `:` | src/forthc.fth:332 | 1 |  |
| 478 | `fc-ret-p` | переменная | src/forthc.fth:341 | 4 |  |
| 479 | `fc-ret-l` | переменная | src/forthc.fth:341 | 7 |  |
| 480 | `fc-rs0` | переменная | src/forthc.fth:341 | 3 |  |
| 481 | `fc-rs1` | переменная | src/forthc.fth:341 | 3 |  |
| 482 | `fc-ret-patch` | определение `:` | src/forthc.fth:345 | 4 |  |
| 483 | `fc-ret-masked` | определение `:` | src/forthc.fth:347 | 1 |  |
| 484 | `fc-ret` | определение `:` | src/forthc.fth:351 | 3 |  |
| 485 | `fc-ca` | переменная | src/forthc.fth:367 | 3 |  |
| 486 | `fc-cl0` | переменная | src/forthc.fth:367 | 4 |  |
| 487 | `fc-cl1` | переменная | src/forthc.fth:367 | 4 |  |
| 488 | `fc-cr` | переменная | src/forthc.fth:367 | 4 |  |
| 489 | `fc-cslot` | переменная | src/forthc.fth:367 | 3 |  |
| 490 | `fc-csh` | переменная | src/forthc.fth:367 | 2 |  |
| 491 | `fc-cv` | переменная | src/forthc.fth:368 | 3 |  |
| 492 | `fc-cres` | переменная | src/forthc.fth:368 | 6 |  |
| 493 | `fc-cmode` | переменная | src/forthc.fth:368 | 6 |  |
| 494 | `fc-ar` | переменная | src/forthc.fth:368 | 5 |  |
| 495 | `fc-chk-read` | определение `:` | src/forthc.fth:370 | 1 |  |
| 496 | `fc-chk-seg` | определение `:` | src/forthc.fth:373 | 1 |  |
| 497 | `fc-as` | переменная | src/forthc.fth:378 | 2 |  |
| 498 | `fc-af` | переменная | src/forthc.fth:378 | 2 |  |
| 499 | `fc-al0` | переменная | src/forthc.fth:378 | 2 |  |
| 500 | `fc-al1` | переменная | src/forthc.fth:378 | 2 |  |
| 501 | `fc-apl` | переменная | src/forthc.fth:378 | 3 |  |
| 502 | `fc-afld` | переменная | src/forthc.fth:378 | 3 |  |
| 503 | `fc-access-patch` | определение `:` | src/forthc.fth:379 | 2 |  |
| 504 | `fc-access` | определение `:` | src/forthc.fth:384 | 1 |  |
| 505 | `fc-width` | определение `:` | src/forthc.fth:386 | 4 |  |
| 506 | `fc-check` | определение `:` | src/forthc.fth:387 | 4 |  |
| 507 | `fc-ring` | константа | src/forthc.fth:403 | 6 |  |
| 508 | `fc-window` | константа | src/forthc.fth:403 | 1 |  |
| 509 | `fc-sl` | данные `create` | src/forthc.fth:404 | 2 |  |
| 510 | `fc-stabs` | переменная | src/forthc.fth:404 | 2 |  |
| 511 | `fc-slen` | переменная | src/forthc.fth:405 | 7 |  |
| 512 | `fc-slow` | переменная | src/forthc.fth:405 | 4 |  |
| 513 | `fc-sinit` | определение `:` | src/forthc.fth:406 | 2 |  |
| 514 | `fc-sbegin` | определение `:` | src/forthc.fth:407 | 2 |  |
| 515 | `fc-tabs` | определение `:` | src/forthc.fth:408 | 3 |  |
| 516 | `fc-at` | определение `:` | src/forthc.fth:409 | 4 |  |
| 517 | `fc-has?` | определение `:` | src/forthc.fth:414 | 1 |  |
| 518 | `fc-tab+` | определение `:` | src/forthc.fth:415 | 1 |  |
| 519 | `fc-prw` | данные `create` | src/forthc.fth:416 | 6 |  |
| 520 | `fc-ptab` | переменная | src/forthc.fth:416 | 5 |  |
| 521 | `fc-place` | определение `:` | src/forthc.fth:417 | 3 |  |
| 522 | `fc-scopy` | определение `:` | src/forthc.fth:427 | 9 |  |
| 523 | `fc-segs` | данные `create` | src/forthc.fth:429 | 2 |  |
| 524 | `fc-nseg` | переменная | src/forthc.fth:429 | 5 |  |
| 525 | `fc-pp` | данные `create` | src/forthc.fth:430 | 2 |  |
| 526 | `fc-npp` | переменная | src/forthc.fth:430 | 4 |  |
| 527 | `fc-latest` | переменная | src/forthc.fth:430 | 4 |  |
| 528 | `fc-sga` | переменная | src/forthc.fth:430 | 14 |  |
| 529 | `fc-ltab` | переменная | src/forthc.fth:431 | 3 |  |
| 530 | `fc-ls` | переменная | src/forthc.fth:431 | 3 |  |
| 531 | `fc-lw` | переменная | src/forthc.fth:431 | 3 |  |
| 532 | `fc-ldst` | переменная | src/forthc.fth:431 | 2 |  |
| 533 | `fc-seg+` | определение `:` | src/forthc.fth:432 | 21 |  |
| 534 | `fc-pp+` | определение `:` | src/forthc.fth:435 | 1 |  |
| 535 | `fc-slookup` | определение `:` | src/forthc.fth:436 | 8 |  |
| 536 | `fc-nx` | переменная | src/forthc.fth:455 | 3 |  |
| 537 | `fc-nv` | переменная | src/forthc.fth:455 | 2 |  |
| 538 | `fc-nt` | переменная | src/forthc.fth:455 | 3 |  |
| 539 | `fc-negate-chain` | определение `:` | src/forthc.fth:456 | 1 |  |
| 540 | `fc-gw` | переменная | src/forthc.fth:463 | 4 |  |
| 541 | `fc-gs` | переменная | src/forthc.fth:463 | 2 |  |
| 542 | `fc-gs2` | переменная | src/forthc.fth:463 | 2 |  |
| 543 | `fc-gts` | переменная | src/forthc.fth:463 | 6 |  |
| 544 | `fc-gdst` | переменная | src/forthc.fth:463 | 2 |  |
| 545 | `fc-negate-select` | определение `:` | src/forthc.fth:464 | 4 |  |
| 546 | `fc-sfinish` | определение `:` | src/forthc.fth:469 | 2 |  |
| 547 | `fc-pr` | данные `create` | src/forthc.fth:472 | 2 |  |
| 548 | `fc-xs` | данные `create` | src/forthc.fth:472 | 2 |  |
| 549 | `fc-m4` | переменная | src/forthc.fth:473 | 2 |  |
| 550 | `fc-mj` | переменная | src/forthc.fth:473 | 11 |  |
| 551 | `fc-mk` | переменная | src/forthc.fth:473 | 6 |  |
| 552 | `fc-p@` | определение `:` | src/forthc.fth:474 | 3 |  |
| 553 | `fc-p!` | определение `:` | src/forthc.fth:475 | 1 |  |
| 554 | `fc-x@` | определение `:` | src/forthc.fth:476 | 3 |  |
| 555 | `fc-x!` | определение `:` | src/forthc.fth:477 | 2 |  |
| 556 | `fc-build-mul` | определение `:` | src/forthc.fth:478 | 1 |  |
| 557 | `fc-sub` | данные `create` | src/forthc.fth:496 | 2 |  |
| 558 | `fc-qsel` | переменная | src/forthc.fth:496 | 2 |  |
| 559 | `fc-absa` | переменная | src/forthc.fth:497 | 5 |  |
| 560 | `fc-absb` | переменная | src/forthc.fth:497 | 3 |  |
| 561 | `fc-ta` | переменная | src/forthc.fth:497 | 4 |  |
| 562 | `fc-tb` | переменная | src/forthc.fth:497 | 2 |  |
| 563 | `fc-rem` | переменная | src/forthc.fth:498 | 7 |  |
| 564 | `fc-tr` | переменная | src/forthc.fth:498 | 7 |  |
| 565 | `fc-q` | переменная | src/forthc.fth:498 | 3 |  |
| 566 | `fc-tq` | переменная | src/forthc.fth:498 | 4 |  |
| 567 | `fc-k` | переменная | src/forthc.fth:498 | 5 |  |
| 568 | `fc-w` | переменная | src/forthc.fth:499 | 14 |  |
| 569 | `fc-lo` | переменная | src/forthc.fth:499 | 7 |  |
| 570 | `fc-tlo` | переменная | src/forthc.fth:499 | 7 |  |
| 571 | `fc-t0` | переменная | src/forthc.fth:499 | 4 |  |
| 572 | `fc-t1` | переменная | src/forthc.fth:499 | 4 |  |
| 573 | `fc-qr` | переменная | src/forthc.fth:499 | 4 |  |
| 574 | `fc-tqk` | переменная | src/forthc.fth:499 | 3 |  |
| 575 | `fc-sub@` | определение `:` | src/forthc.fth:500 | 7 |  |
| 576 | `fc-step` | определение `:` | src/forthc.fth:502 | 3 |  |
| 577 | `fc-div-step` | определение `:` | src/forthc.fth:509 | 1 |  |
| 578 | `fc-build-div` | определение `:` | src/forthc.fth:526 | 1 |  |
| 579 | `fc-mul-entry` | переменная | src/forthc.fth:542 | 4 |  |
| 580 | `fc-mul-exit` | переменная | src/forthc.fth:542 | 2 |  |
| 581 | `fc-div-entry` | переменная | src/forthc.fth:542 | 5 |  |
| 582 | `fc-div-exit` | переменная | src/forthc.fth:542 | 4 |  |
| 583 | `fc-hl` | переменная | src/forthc.fth:543 | 6 |  |
| 584 | `fc-hcont` | переменная | src/forthc.fth:543 | 4 |  |
| 585 | `fc-mul-cost` | данные `create` | src/forthc.fth:545 | 2 |  |
| 586 | `fc-div-cost` | данные `create` | src/forthc.fth:545 | 2 |  |
| 587 | `fc-row-or-new` | определение `:` | src/forthc.fth:546 | 2 |  |
| 588 | `fc-call-helper` | определение `:` | src/forthc.fth:549 | 4 |  |
| 589 | `fc-result1` | определение `:` | src/forthc.fth:558 | 3 |  |
| 590 | `fc-s1` | переменная | src/forthc.fth:559 | 2 |  |
| 591 | `fc-s2` | переменная | src/forthc.fth:559 | 2 |  |
| 592 | `fc-r1` | переменная | src/forthc.fth:559 | 2 |  |
| 593 | `fc-result2` | определение `:` | src/forthc.fth:560 | 1 |  |
| 594 | `fc-pexit` | переменная | src/forthc.fth:570 | 2 |  |
| 595 | `fc-ptramp` | переменная | src/forthc.fth:570 | 2 |  |
| 596 | `fc-pd` | переменная | src/forthc.fth:570 | 5 |  |
| 597 | `fc-pc` | переменная | src/forthc.fth:570 | 5 |  |
| 598 | `fc-ends` | переменная | src/forthc.fth:570 | 3 |  |
| 599 | `fc-pb` | переменная | src/forthc.fth:571 | 5 |  |
| 600 | `fc-pcp` | переменная | src/forthc.fth:571 | 5 |  |
| 601 | `fc-pln` | переменная | src/forthc.fth:571 | 5 |  |
| 602 | `fc-pk` | переменная | src/forthc.fth:571 | 4 |  |
| 603 | `fc-pcall` | переменная | src/forthc.fth:571 | 3 |  |
| 604 | `fc-best` | данные `create` | src/forthc.fth:572 | 10 |  |
| 605 | `fc-pend@` | определение `:` | src/forthc.fth:573 | 7 |  |
| 606 | `fc-reach` | определение `:` | src/forthc.fth:575 | 2 |  |
| 607 | `fc-take` | определение `:` | src/forthc.fth:585 | 1 |  |
| 608 | `fc-end-path` | определение `:` | src/forthc.fth:593 | 1 |  |
| 609 | `fc-to` | определение `:` | src/forthc.fth:598 | 2 |  |
| 610 | `fc-node` | определение `:` | src/forthc.fth:603 | 1 |  |
| 611 | `fc-path` | определение `:` | src/forthc.fth:623 | 3 |  |
| 612 | `fc-cost!` | определение `:` | src/forthc.fth:632 | 3 |  |
| 613 | `fc-ll` | переменная | src/forthc.fth:636 | 6 |  |
| 614 | `fc-llr` | переменная | src/forthc.fth:636 | 3 |  |
| 615 | `fc-llv` | переменная | src/forthc.fth:636 | 3 |  |
| 616 | `fc-plit` | переменная | src/forthc.fth:636 | 6 |  |
| 617 | `fc-plr` | переменная | src/forthc.fth:636 | 4 |  |
| 618 | `fc-plv` | переменная | src/forthc.fth:636 | 6 |  |
| 619 | `fc-literal` | определение `:` | src/forthc.fth:637 | 14 |  |
| 620 | `fc-or-zero` | определение `:` | src/forthc.fth:639 | 2 |  |
| 621 | `fc-ba` | переменная | src/forthc.fth:642 | 13 |  |
| 622 | `fc-bb` | переменная | src/forthc.fth:642 | 13 |  |
| 623 | `fc-br` | переменная | src/forthc.fth:642 | 9 |  |
| 624 | `fc-binary` | определение `:` | src/forthc.fth:644 | 10 |  |
| 625 | `fc-r-at` | определение `:` | src/forthc.fth:668 | 2 |  |
| 626 | `fc-pop-pinned` | определение `:` | src/forthc.fth:671 | 3 |  |
| 627 | `fc-sk` | переменная | src/forthc.fth:673 | 12 |  |
| 628 | `fc-shift-copy` | определение `:` | src/forthc.fth:674 | 2 |  |
| 629 | `fc-inc` | определение `:` | src/forthc.fth:679 | 3 |  |
| 630 | `fc-read-key` | определение `:` | src/forthc.fth:682 | 1 |  |
| 631 | `fc-text` | переменная | src/forthc.fth:688 | 13 |  |
| 632 | `fc-tlen` | переменная | src/forthc.fth:688 | 14 |  |
| 633 | `fc-pos` | переменная | src/forthc.fth:688 | 24 |  |
| 634 | `fc-text-size` | переменная | src/forthc.fth:688 | 6 | вход бута (хост) |
| 635 | `fc-tok` | данные `create` | src/forthc.fth:689 | 19 |  |
| 636 | `fc-tl` | переменная | src/forthc.fth:689 | 24 |  |
| 637 | `fc-reset` | определение `:` | src/forthc.fth:690 | 3 |  |
| 638 | `fc-append` | определение `:` | src/forthc.fth:691 | 1 |  |
| 639 | `fc\|` | определение `:` | src/forthc.fth:695 | 1 | вход бута (хост) |
| 640 | `fc-ch` | определение `:` | src/forthc.fth:696 | 5 |  |
| 641 | `fc-more?` | определение `:` | src/forthc.fth:697 | 6 |  |
| 642 | `fc-next` | определение `:` | src/forthc.fth:701 | 8 |  |
| 643 | `fc-next!` | определение `:` | src/forthc.fth:709 | 10 |  |
| 644 | `fc-is?` | определение `:` | src/forthc.fth:711 | 5 |  |
| 645 | `fc-raw` | определение `:` | src/forthc.fth:715 | 1 |  |
| 646 | `fc-string-token` | определение `:` | src/forthc.fth:717 | 1 |  |
| 647 | `fc-names-size` | переменная | src/forthc.fth:722 | 5 | вход бута (хост) |
| 648 | `fc-max-words` | переменная | src/forthc.fth:722 | 5 | вход бута (хост) |
| 649 | `fc-names` | переменная | src/forthc.fth:723 | 3 |  |
| 650 | `fc-names-used` | переменная | src/forthc.fth:723 | 5 |  |
| 651 | `fc-wt` | переменная | src/forthc.fth:724 | 5 |  |
| 652 | `fc-nwords` | переменная | src/forthc.fth:724 | 12 |  |
| 653 | `fc-wbk` | переменная | src/forthc.fth:724 | 3 |  |
| 654 | `fc-wt@` | определение `:` | src/forthc.fth:732 | 6 |  |
| 655 | `fc-proved` | данные `create` | src/forthc.fth:736 | 2 |  |
| 656 | `fc-unproved` | данные `create` | src/forthc.fth:737 | 2 |  |
| 657 | `fc-mechanisms` | определение `:` | src/forthc.fth:740 | 1 |  |
| 658 | `fc-xt` | определение `:` | src/forthc.fth:745 | 5 |  |
| 659 | `fc-xtn` | определение `:` | src/forthc.fth:748 | 2 |  |
| 660 | `fc-hash` | определение `:` | src/forthc.fth:749 | 2 |  |
| 661 | `fc-define` | определение `:` | src/forthc.fth:751 | 6 |  |
| 662 | `fc-lookup` | определение `:` | src/forthc.fth:756 | 5 |  |
| 663 | `fc-find` | определение `:` | src/forthc.fth:760 | 6 |  |
| 664 | `fc-word-of` | определение `:` | src/forthc.fth:763 | 2 |  |
| 665 | `fc-cost` | определение `:` | src/forthc.fth:771 | 1 |  |
| 666 | `fc-proved?` | определение `:` | src/forthc.fth:774 | 1 |  |
| 667 | `fc-here` | переменная | src/forthc.fth:777 | 9 |  |
| 668 | `fc-word` | переменная | src/forthc.fth:777 | 13 |  |
| 669 | `fc-uses` | переменная | src/forthc.fth:777 | 16 |  |
| 670 | `fc-rt` | переменная | src/forthc.fth:780 | 7 |  |
| 671 | `fc-rta` | переменная | src/forthc.fth:780 | 7 |  |
| 672 | `fc-ctl` | данные `create` | src/forthc.fth:783 | 1 |  |
| 673 | `fc-nctl` | переменная | src/forthc.fth:783 | 12 |  |
| 674 | `fc-cleave` | переменная | src/forthc.fth:783 | 2 |  |
| 675 | `fc-ctl@` | определение `:` | src/forthc.fth:784 | 4 |  |
| 676 | `fc-ctl+` | определение `:` | src/forthc.fth:785 | 6 |  |
| 677 | `fc-ctl-` | определение `:` | src/forthc.fth:787 | 7 |  |
| 678 | `fc-do-entry` | определение `:` | src/forthc.fth:789 | 1 |  |
| 679 | `fc-ctl-leave` | определение `:` | src/forthc.fth:793 | 1 |  |
| 680 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:794 | 1 |  |
| 681 | `fc-loop-leave` | определение `:` | src/forthc.fth:795 | 1 |  |
| 682 | `fc-align` | определение `:` | src/forthc.fth:797 | 2 |  |
| 683 | `fc-check-here` | определение `:` | src/forthc.fth:798 | 3 |  |
| 684 | `fc-define-data` | определение `:` | src/forthc.fth:799 | 2 |  |
| 685 | `fc-sat` | переменная | src/forthc.fth:800 | 3 |  |
| 686 | `fc-store-string` | определение `:` | src/forthc.fth:801 | 1 |  |
| 687 | `fc-ct` | данные `create` | src/forthc.fth:807 | 3 |  |
| 688 | `fc-nct` | переменная | src/forthc.fth:807 | 11 |  |
| 689 | `fc-ct+` | определение `:` | src/forthc.fth:808 | 15 |  |
| 690 | `fc-ct-` | определение `:` | src/forthc.fth:809 | 9 |  |
| 691 | `fc-ct2` | определение `:` | src/forthc.fth:810 | 8 |  |
| 692 | `fc-inits` | данные `create` | src/forthc.fth:812 | 2 |  |
| 693 | `fc-ninit` | переменная | src/forthc.fth:812 | 5 |  |
| 694 | `fc-init-open` | переменная | src/forthc.fth:812 | 6 |  |
| 695 | `fc-init` | определение `:` | src/forthc.fth:813 | 1 |  |
| 696 | `fc-scan-uses` | определение `:` | src/forthc.fth:832 | 1 |  |
| 697 | `fc-const-shift` | определение `:` | src/forthc.fth:840 | 2 |  |
| 698 | `fc-lit?` | определение `:` | src/forthc.fth:851 | 3 |  |
| 699 | `fc-mul-lit?` | определение `:` | src/forthc.fth:853 | 1 |  |
| 700 | `fc-shift-lit?` | определение `:` | src/forthc.fth:858 | 2 |  |
| 701 | `fc-pick-roll` | определение `:` | src/forthc.fth:861 | 2 |  |
| 702 | `fc-stx` | переменная | src/forthc.fth:876 | 3 |  |
| 703 | `fc-stlo` | переменная | src/forthc.fth:876 | 8 |  |
| 704 | `fc-sthi` | переменная | src/forthc.fth:876 | 4 |  |
| 705 | `fc-stp` | переменная | src/forthc.fth:876 | 6 |  |
| 706 | `fc-strow` | переменная | src/forthc.fth:876 | 8 |  |
| 707 | `fc-stm` | переменная | src/forthc.fth:876 | 5 |  |
| 708 | `fc-ftr` | переменная | src/forthc.fth:877 | 5 |  |
| 709 | `fc-stg` | переменная | src/forthc.fth:877 | 2 |  |
| 710 | `fc-sw0` | определение `:` | src/forthc.fth:878 | 2 |  |
| 711 | `fc-sw1` | определение `:` | src/forthc.fth:879 | 2 |  |
| 712 | `fc-sbase` | определение `:` | src/forthc.fth:881 | 2 |  |
| 713 | `fc-space-end` | определение `:` | src/forthc.fth:884 | 2 |  |
| 714 | `fc-space-store` | определение `:` | src/forthc.fth:892 | 2 |  |
| 715 | `fc-space-fetch` | определение `:` | src/forthc.fth:899 | 2 |  |
| 716 | `fc-cp` | определение `:` | src/forthc.fth:912 | 4 |  |
| 717 | `fc-copy-row` | определение `:` | src/forthc.fth:914 | 1 |  |
| 718 | `fc-close-init` | определение `:` | src/forthc.fth:917 | 2 |  |
| 719 | `fc-open-init` | определение `:` | src/forthc.fth:920 | 1 |  |
| 720 | `fc-gens` | переменная | src/forthc.fth:936 | 3 |  |
| 721 | `fc-generator` | определение `:` | src/forthc.fth:937 | 87 |  |
| 722 | `fc-literal-name` | определение `:` | src/forthc.fth:939 | 10 |  |
| 723 | `fc-words` | определение `:` | src/forthc.fth:941 | 1 |  |
| 724 | `fc-known` | определение `:` | src/forthc.fth:952 | 1 |  |
| 725 | `fc-defining?` | определение `:` | src/forthc.fth:955 | 7 |  |
| 726 | `fc-code` | определение `:` | src/forthc.fth:958 | 51 | вариант 2 |
| 727 | `fc-fold?` | определение `:` | src/forthc.fth:961 | 13 |  |
| 728 | `fc-top-only` | определение `:` | src/forthc.fth:963 | 6 |  |
| 729 | `fc-not-found` | определение `:` | src/forthc.fth:968 | 1 |  |
| 730 | `fc-word-token` | определение `:` | src/forthc.fth:975 | 2 |  |
| 731 | `fc-token` | определение `:` | src/forthc.fth:982 | 2 |  |
| 732 | `fc-synonym-of` | определение `:` | src/forthc.fth:985 | 2 |  |
| 733 | `fc-synonym` | определение `:` | src/forthc.fth:987 | 10 |  |
| 734 | `fc-sy` | переменная | src/forthc.fth:990 | 2 |  |
| 735 | `fc-synonym?` | определение `:` | src/forthc.fth:991 | 1 |  |
| 736 | `fc-poke` | определение `:` | src/forthc.fth:996 | 2 |  |
| 737 | `fc-concept-record` | определение `:` | src/forthc.fth:1001 | 1 |  |
| 738 | `fc-eval` | определение `:` | src/forthc.fth:1007 | 54 |  |
| 739 | `fc-concepts` | определение `:` | src/forthc.fth:1013 | 1 |  |
| 740 | `fc-nhost` | переменная | src/forthc.fth:1028 | 5 |  |
| 741 | `fc-platform` | определение `:` | src/forthc.fth:1029 | 1 |  |
| 742 | `fc-time-price` | определение `:` | src/forthc.fth:1055 | 1 |  |
| 743 | `fc-replacement` | определение `:` | src/forthc.fth:1068 | 1 |  |
| 744 | `fc-library` | определение `:` | src/forthc.fth:1083 | 1 |  |
| 745 | `fc-long` | определение `:` | src/forthc.fth:1107 | 1 |  |
| 746 | `fc-helpers-cost` | определение `:` | src/forthc.fth:1117 | 1 |  |
| 747 | `fc-price-word` | определение `:` | src/forthc.fth:1125 | 1 |  |
| 748 | `fc-compile` | определение `:` | src/forthc.fth:1128 | 1 |  |
| 749 | `fc-go` | определение `:` | src/forthc.fth:1145 | 3 | вход бута (хост) |
| 750 | `gen+` | определение `:` | src/primitives.fth:9 | 5 |  |
| 751 | `gen-` | определение `:` | src/primitives.fth:10 | 2 |  |
| 752 | `gen-and` | определение `:` | src/primitives.fth:11 | 2 |  |
| 753 | `gen-or` | определение `:` | src/primitives.fth:12 | 2 |  |
| 754 | `gen-xor` | определение `:` | src/primitives.fth:13 | 2 |  |
| 755 | `gen=` | определение `:` | src/primitives.fth:14 | 2 |  |
| 756 | `gen<` | определение `:` | src/primitives.fth:15 | 2 |  |
| 757 | `gen-u<` | определение `:` | src/primitives.fth:16 | 2 |  |
| 758 | `gen-lshift` | определение `:` | src/primitives.fth:17 | 2 |  |
| 759 | `gen-rshift` | определение `:` | src/primitives.fth:19 | 2 |  |
| 760 | `gen-0=` | определение `:` | src/primitives.fth:21 | 2 |  |
| 761 | `gen-cells` | определение `:` | src/primitives.fth:22 | 2 |  |
| 762 | `gen-2*` | определение `:` | src/primitives.fth:23 | 2 |  |
| 763 | `gen-1+` | определение `:` | src/primitives.fth:24 | 2 |  |
| 764 | `gen-1-` | определение `:` | src/primitives.fth:25 | 2 |  |
| 765 | `gen-cell+` | определение `:` | src/primitives.fth:26 | 2 |  |
| 766 | `gen*` | определение `:` | src/primitives.fth:28 | 2 |  |
| 767 | `gen/` | определение `:` | src/primitives.fth:31 | 2 |  |
| 768 | `gen-mod` | определение `:` | src/primitives.fth:32 | 2 |  |
| 769 | `gen/mod` | определение `:` | src/primitives.fth:33 | 2 |  |
| 770 | `gen-dup` | определение `:` | src/primitives.fth:37 | 2 |  |
| 771 | `gen-drop` | определение `:` | src/primitives.fth:38 | 2 |  |
| 772 | `gen-swap` | определение `:` | src/primitives.fth:39 | 2 |  |
| 773 | `gen-over` | определение `:` | src/primitives.fth:40 | 2 |  |
| 774 | `gen-rot` | определение `:` | src/primitives.fth:41 | 2 |  |
| 775 | `gen-pick` | определение `:` | src/primitives.fth:42 | 2 |  |
| 776 | `gen-roll` | определение `:` | src/primitives.fth:43 | 2 |  |
| 777 | `gen->r` | определение `:` | src/primitives.fth:44 | 2 |  |
| 778 | `gen-r>` | определение `:` | src/primitives.fth:45 | 2 |  |
| 779 | `gen-r@` | определение `:` | src/primitives.fth:46 | 4 |  |
| 780 | `gen-j` | определение `:` | src/primitives.fth:47 | 2 |  |
| 781 | `gen-@` | определение `:` | src/primitives.fth:48 | 2 |  |
| 782 | `gen-!` | определение `:` | src/primitives.fth:50 | 2 |  |
| 783 | `gen-c@` | определение `:` | src/primitives.fth:51 | 2 |  |
| 784 | `gen-c!` | определение `:` | src/primitives.fth:53 | 2 |  |
| 785 | `gen-emit` | определение `:` | src/primitives.fth:54 | 2 |  |
| 786 | `gen-key` | определение `:` | src/primitives.fth:57 | 2 |  |
| 787 | `gen-if` | определение `:` | src/primitives.fth:61 | 2 |  |
| 788 | `gen-else` | определение `:` | src/primitives.fth:62 | 2 |  |
| 789 | `gen-then` | определение `:` | src/primitives.fth:64 | 2 |  |
| 790 | `gen-begin` | определение `:` | src/primitives.fth:68 | 2 |  |
| 791 | `gen-until` | определение `:` | src/primitives.fth:69 | 2 |  |
| 792 | `gen-while` | определение `:` | src/primitives.fth:71 | 2 |  |
| 793 | `gen-repeat` | определение `:` | src/primitives.fth:72 | 2 |  |
| 794 | `gen-again` | определение `:` | src/primitives.fth:73 | 2 |  |
| 795 | `gen-do` | определение `:` | src/primitives.fth:75 | 2 |  |
| 796 | `fc-di` | переменная | src/primitives.fth:79 | 3 |  |
| 797 | `fc-dl` | переменная | src/primitives.fth:79 | 3 |  |
| 798 | `gen-?do` | определение `:` | src/primitives.fth:80 | 2 |  |
| 799 | `fc-lv` | переменная | src/primitives.fth:87 | 2 |  |
| 800 | `gen-loop` | определение `:` | src/primitives.fth:88 | 2 |  |
| 801 | `gen-leave` | определение `:` | src/primitives.fth:97 | 2 |  |
| 802 | `gen-unloop` | определение `:` | src/primitives.fth:100 | 2 |  |
| 803 | `gen-exit` | определение `:` | src/primitives.fth:103 | 2 |  |
| 804 | `gen-recurse` | определение `:` | src/primitives.fth:106 | 2 |  |
| 805 | `gen-tick` | определение `:` | src/primitives.fth:107 | 2 |  |
| 806 | `gen-throw` | определение `:` | src/primitives.fth:110 | 2 |  |
| 807 | `gen-call` | определение `:` | src/primitives.fth:116 | 3 |  |
| 808 | `gen-space!` | определение `:` | src/primitives.fth:117 | 2 |  |
| 809 | `gen-spacec!` | определение `:` | src/primitives.fth:118 | 2 |  |
| 810 | `gen-space@` | определение `:` | src/primitives.fth:119 | 2 |  |
| 811 | `gen-spacec@` | определение `:` | src/primitives.fth:120 | 2 |  |
| 812 | `gen-execute` | определение `:` | src/primitives.fth:121 | 2 |  |
| 813 | `gen-catch` | определение `:` | src/primitives.fth:122 | 2 |  |
| 814 | `fc-entry-cell` | определение `:` | src/primitives.fth:134 | 1 |  |
| 815 | `fc-concept` | определение `:` | src/primitives.fth:136 | 1 |  |
| 816 | `gen-colon` | определение `:` | src/primitives.fth:145 | 2 |  |
| 817 | `gen-semicolon` | определение `:` | src/primitives.fth:151 | 2 |  |
| 818 | `gen-variable` | определение `:` | src/primitives.fth:154 | 2 |  |
| 819 | `gen-create` | определение `:` | src/primitives.fth:155 | 2 |  |
| 820 | `gen-allot` | определение `:` | src/primitives.fth:156 | 2 |  |
| 821 | `gen-constant` | определение `:` | src/primitives.fth:157 | 2 |  |
| 822 | `gen-decimal` | определение `:` | src/primitives.fth:158 | 2 |  |
| 823 | `gen-kernel-layout` | определение `:` | src/primitives.fth:160 | 2 |  |
| 824 | `gen-backslash` | определение `:` | src/primitives.fth:163 | 2 |  |
| 825 | `gen-paren` | определение `:` | src/primitives.fth:165 | 4 |  |
| 826 | `gen-char` | определение `:` | src/primitives.fth:166 | 2 |  |
| 827 | `gen-string` | определение `:` | src/primitives.fth:167 | 2 |  |
| 828 | `fc-digit@` | определение `:` | src/primitives.fth:176 | 1 |  |
| 829 | `gen-literal` | определение `:` | src/primitives.fth:178 | 2 |  |
| 830 | `fc-known-xt` | определение `:` | src/primitives.fth:187 | 2 |  |
| 831 | `gen-cost` | определение `:` | src/primitives.fth:188 | 2 |  |
| 832 | `gen-proved?` | определение `:` | src/primitives.fth:190 | 2 |  |
| 833 | `gen-library` | определение `:` | src/primitives.fth:191 | 16 |  |
| 834 | `gen-price` | определение `:` | src/primitives.fth:192 | 2 |  |
| 835 | `fc-cpos` | переменная | src/primitives.fth:200 | 4 |  |
| 836 | `fc-hn` | переменная | src/primitives.fth:200 | 2 |  |
| 837 | `fc-cdepth` | переменная | src/primitives.fth:200 | 4 |  |
| 838 | `fc-hname` | данные `create` | src/primitives.fth:200 | 2 |  |
| 839 | `fc-hb` | определение `:` | src/primitives.fth:201 | 3 |  |
| 840 | `fc-c,` | определение `:` | src/primitives.fth:202 | 17 |  |
| 841 | `fc-c1` | определение `:` | src/primitives.fth:203 | 8 |  |
| 842 | `fc-c-gen` | определение `:` | src/primitives.fth:204 | 1 |  |
| 843 | `fc-c-body` | определение `:` | src/primitives.fth:208 | 1 |  |
| 844 | `gen-host` | определение `:` | src/primitives.fth:217 | 2 |  |
| 845 | `fc-name2` | определение `:` | src/primitives.fth:235 | 1 |  |
| 846 | `fc-generators` | определение `:` | src/primitives.fth:240 | 1 |  |
| 847 | `+` | генератор | src/primitives.fth:241 | 558 | слово компилятора `gen+` |
| 848 | `-` | генератор | src/primitives.fth:241 | 61 | слово компилятора `gen-` |
| 849 | `*` | генератор | src/primitives.fth:242 | 83 | слово компилятора `gen*` |
| 850 | `/` | генератор | src/primitives.fth:242 | 4 | слово компилятора `gen/` |
| 851 | `mod` | генератор | src/primitives.fth:243 | 2 | слово компилятора `gen-mod` |
| 852 | `and` | генератор | src/primitives.fth:244 | 121 | слово компилятора `gen-and` |
| 853 | `or` | генератор | src/primitives.fth:244 | 45 | слово компилятора `gen-or` |
| 854 | `xor` | генератор | src/primitives.fth:245 | 5 | слово компилятора `gen-xor` |
| 855 | `lshift` | генератор | src/primitives.fth:245 | 93 | слово компилятора `gen-lshift` |
| 856 | `rshift` | генератор | src/primitives.fth:246 | 63 | слово компилятора `gen-rshift` |
| 857 | `=` | генератор | src/primitives.fth:246 | 82 | слово компилятора `gen=` |
| 858 | `<` | генератор | src/primitives.fth:247 | 28 | слово компилятора `gen<` |
| 859 | `u<` | генератор | src/primitives.fth:247 | 24 | слово компилятора `gen-u<` |
| 860 | `0=` | генератор | src/primitives.fth:248 | 98 | слово компилятора `gen-0=` |
| 861 | `2*` | генератор | src/primitives.fth:248 | 29 | слово компилятора `gen-2*` |
| 862 | `1+` | генератор | src/primitives.fth:249 | 43 | слово компилятора `gen-1+` |
| 863 | `1-` | генератор | src/primitives.fth:249 | 56 | слово компилятора `gen-1-` |
| 864 | `cells` | генератор | src/primitives.fth:250 | 282 | слово компилятора `gen-cells` |
| 865 | `cell+` | генератор | src/primitives.fth:250 | 57 | слово компилятора `gen-cell+` |
| 866 | `dup` | генератор | src/primitives.fth:251 | 304 | слово компилятора `gen-dup` |
| 867 | `drop` | генератор | src/primitives.fth:251 | 205 | слово компилятора `gen-drop` |
| 868 | `swap` | генератор | src/primitives.fth:252 | 141 | слово компилятора `gen-swap` |
| 869 | `over` | генератор | src/primitives.fth:252 | 87 | слово компилятора `gen-over` |
| 870 | `rot` | генератор | src/primitives.fth:253 | 37 | слово компилятора `gen-rot` |
| 871 | `pick` | генератор | src/primitives.fth:253 | 47 | слово компилятора `gen-pick` |
| 872 | `roll` | генератор | src/primitives.fth:254 | 7 | слово компилятора `gen-roll` |
| 873 | `>r` | генератор | src/primitives.fth:254 | 112 | слово компилятора `gen->r` |
| 874 | `r>` | генератор | src/primitives.fth:255 | 116 | слово компилятора `gen-r>` |
| 875 | `r@` | генератор | src/primitives.fth:255 | 108 | слово компилятора `gen-r@` |
| 876 | `i` | генератор | src/primitives.fth:256 | 172 | слово компилятора `gen-r@` |
| 877 | `j` | генератор | src/primitives.fth:256 | 12 | слово компилятора `gen-j` |
| 878 | `@` | генератор | src/primitives.fth:257 | 1262 | слово компилятора `gen-@` |
| 879 | `!` | генератор | src/primitives.fth:257 | 662 | слово компилятора `gen-!` |
| 880 | `c@` | генератор | src/primitives.fth:258 | 23 | слово компилятора `gen-c@` |
| 881 | `c!` | генератор | src/primitives.fth:258 | 18 | слово компилятора `gen-c!` |
| 882 | `space!` | генератор | src/primitives.fth:259 | 1 | слово компилятора `gen-space!` |
| 883 | `spacec!` | генератор | src/primitives.fth:259 | 1 | слово компилятора `gen-spacec!` |
| 884 | `space@` | генератор | src/primitives.fth:260 | 1 | слово компилятора `gen-space@` |
| 885 | `emit` | генератор | src/primitives.fth:261 | 4 | слово компилятора `gen-emit` |
| 886 | `key` | генератор | src/primitives.fth:261 | 1 | слово компилятора `gen-key` |
| 887 | `if` | генератор | src/primitives.fth:262 | 307 | слово компилятора `gen-if` |
| 888 | `else` | генератор | src/primitives.fth:262 | 84 | слово компилятора `gen-else` |
| 889 | `then` | генератор | src/primitives.fth:263 | 307 | слово компилятора `gen-then` |
| 890 | `begin` | генератор | src/primitives.fth:263 | 25 | слово компилятора `gen-begin` |
| 891 | `until` | генератор | src/primitives.fth:264 | 2 | слово компилятора `gen-until` |
| 892 | `while` | генератор | src/primitives.fth:264 | 22 | слово компилятора `gen-while` |
| 893 | `repeat` | генератор | src/primitives.fth:265 | 22 | слово компилятора `gen-repeat` |
| 894 | `again` | генератор | src/primitives.fth:265 | 1 | слово компилятора `gen-again` |
| 895 | `do` | генератор | src/primitives.fth:266 | 31 | слово компилятора `gen-do` |
| 896 | `?do` | генератор | src/primitives.fth:266 | 58 | слово компилятора `gen-?do` |
| 897 | `loop` | генератор | src/primitives.fth:267 | 89 | слово компилятора `gen-loop` |
| 898 | `leave` | генератор | src/primitives.fth:267 | 1 | слово компилятора `gen-leave` |
| 899 | `unloop` | генератор | src/primitives.fth:268 | 7 | слово компилятора `gen-unloop` |
| 900 | `exit` | генератор | src/primitives.fth:268 | 81 | слово компилятора `gen-exit` |
| 901 | `recurse` | генератор | src/primitives.fth:269 | 2 | слово компилятора `gen-recurse` |
| 902 | `execute` | генератор | src/primitives.fth:269 | 10 | слово компилятора `gen-execute` |
| 903 | `[']` | генератор | src/primitives.fth:270 | 119 | слово компилятора `gen-tick` |
| 904 | `catch` | генератор | src/primitives.fth:270 | 1 | слово компилятора `gen-catch` |
| 905 | `throw` | генератор | src/primitives.fth:271 | 83 | слово компилятора `gen-throw` |
| 906 | `:` | генератор | src/primitives.fth:272 | 490 | слово компилятора `gen-colon` |
| 907 | `;` | генератор | src/primitives.fth:272 | 490 | слово компилятора `gen-semicolon` |
| 908 | `variable` | генератор | src/primitives.fth:273 | 319 | слово компилятора `gen-variable` |
| 909 | `create` | генератор | src/primitives.fth:273 | 47 | слово компилятора `gen-create` |
| 910 | `allot` | генератор | src/primitives.fth:274 | 45 | слово компилятора `gen-allot` |
| 911 | `constant` | генератор | src/primitives.fth:274 | 22 | слово компилятора `gen-constant` |
| 912 | `decimal` | генератор | src/primitives.fth:275 | 3 | слово компилятора `gen-decimal` |
| 913 | `kernel-layout` | генератор | src/primitives.fth:275 | 1 | слово компилятора `gen-kernel-layout` |
| 914 | `\` | генератор | src/primitives.fth:276 | 461 | слово компилятора `gen-backslash` |
| 915 | `(` | генератор | src/primitives.fth:276 | 469 | слово компилятора `gen-paren` |
| 916 | `[char]` | генератор | src/primitives.fth:276 | 8 | слово компилятора `gen-char` |
| 917 | `s"` | генератор | src/primitives.fth:277 | 198 | слово компилятора `gen-string` |
| 918 | `literal` | генератор | src/primitives.fth:278 | 496 | слово компилятора `gen-literal` |
| 919 | `0` | цифра (литерал) | src/primitives.fth:286 | 534 | значение 0 |
| 920 | `1` | цифра (литерал) | src/primitives.fth:286 | 445 | значение 1 |
| 921 | `2` | цифра (литерал) | src/primitives.fth:286 | 458 | значение 2 |
| 922 | `3` | цифра (литерал) | src/primitives.fth:286 | 304 | значение 3 |
| 923 | `4` | цифра (литерал) | src/primitives.fth:287 | 242 | значение 4 |
| 924 | `5` | цифра (литерал) | src/primitives.fth:287 | 105 | значение 5 |
| 925 | `6` | цифра (литерал) | src/primitives.fth:287 | 156 | значение 6 |
| 926 | `7` | цифра (литерал) | src/primitives.fth:287 | 60 | значение 7 |
| 927 | `8` | цифра (литерал) | src/primitives.fth:288 | 157 | значение 8 |
| 928 | `9` | цифра (литерал) | src/primitives.fth:288 | 37 | значение 9 |
| 929 | `fc-install-generators` | определение `:` | src/primitives.fth:289 | 1 |  |
| 930 | `heap-start` | данные `create` | src/main.fth:4 | 1 |  |
| 931 | `fc-read` | определение `:` | src/main.fth:7 | 2 |  |
| 932 | `fc-sizes` | определение `:` | src/main.fth:12 | 2 |  |
| 933 | `kn-at` | переменная | src/kernel.fth:12 | 5 |  |
| 934 | `kn-put` | определение `:` | src/kernel.fth:13 | 1 |  |
| 935 | `kn-order` | определение `:` | src/kernel.fth:21 | 1 |  |
| 936 | `kn-get` | определение `:` | src/kernel.fth:24 | 1 |  |
| 937 | `kn-compile` | определение `:` | src/kernel.fth:25 | 1 |  |
| 938 | `kn-.n` | определение `:` | src/kernel.fth:29 | 1 |  |
| 939 | `main` | определение `:` | src/kernel.fth:33 | 1 | вариант 2 |
| 940 | `kn-heap-start` | данные `create` | src/kernel.fth:38 | 1 |  |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 90.

## Определены, но не использованы

Слов: 34. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

| Слово | Вид | Файл:строка |
|---|---|---|
| `lay-out` | определение `:` | src/backend.fth:120 |
| `lay-cz` | переменная | src/compute.fth:175 |
| `lay-cf` | переменная | src/compute.fth:175 |
| `lay-compare` | определение `:` | src/compute.fth:176 |
| `lay-fc` | переменная | src/compute.fth:223 |
| `lay-ff` | переменная | src/compute.fth:223 |
| `lay-flag-exit` | определение `:` | src/compute.fth:224 |
| `lay-exit-layers` | определение `:` | src/compute.fth:233 |
| `lay-ce` | переменная | src/compute.fth:238 |
| `lay-cl` | переменная | src/compute.fth:238 |
| `lay-ch` | переменная | src/compute.fth:238 |
| `lay-call-rows` | определение `:` | src/compute.fth:239 |
| `lay-halt-begin` | определение `:` | src/compute.fth:244 |
| `lay-halt-region` | определение `:` | src/compute.fth:245 |
| `lay-halt-end` | определение `:` | src/compute.fth:246 |
| `lay-stub-on` | определение `:` | src/compute.fth:247 |
| `lay-stub` | определение `:` | src/compute.fth:248 |
| `fc-depth` | определение `:` | src/forthc.fth:950 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:951 |
| `/mod` | генератор | src/primitives.fth:243 |
| `spacec@` | генератор | src/primitives.fth:260 |
| `cost` | генератор | src/primitives.fth:279 |
| `price` | генератор | src/primitives.fth:279 |
| `proved?` | генератор | src/primitives.fth:280 |
| `check-table` | генератор | src/primitives.fth:281 |
| `accuracy` | генератор | src/primitives.fth:281 |
| `replace` | генератор | src/primitives.fth:282 |
| `long!` | генератор | src/primitives.fth:283 |
| `long@` | генератор | src/primitives.fth:283 |
| `host` | генератор | src/primitives.fth:284 |
| `time` | генератор | src/primitives.fth:284 |
| `platform` | генератор | src/primitives.fth:285 |
| `platform-of` | генератор | src/primitives.fth:285 |
| `main` (вариант 1) | определение `:` | src/main.fth:15 |

## Слова, которые при буте исполняет хост

Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки `backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках 83; все они определены в определении языка (генератором в `primitives.fth` или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: `!` `*` `+` `+!` `-` `-rot` `/` `/string` `0<` `0<>` `0=` `0>` `1+` `1-` `2!` `2*` `2@` `2drop` `2dup` `2over` `2swap` `<` `<>` `=` `>` `>in` `>r` `?do` `?dup` `@` `again` `allocate` `and` `begin` `c!` `c@` `cell+` `cells` `cmove` `cmove>` `compare` `decimal` `do` `drop` `dup` `else` `execute` `exit` `fill` `free` `i` `if` `invert` `j` `leave` `loop` `lshift` `max` `min` `mod` `negate` `nip` `or` `over` `pick` `r>` `r@` `repeat` `roll` `rot` `rshift` `source` `swap` `then` `throw` `tuck` `type` `u<` `u>` `unloop` `until` `while` `xor`.

Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро читает каналом `key`), `source` и `>in` — слова только этого пути.
