# Ядро языка (14.8)

Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 961** (определение `:` — 476, переменная — 313, генератор — 71, данные `create` — 62, константа — 23, цифра (литерал) — 10, основание — 6).

## Основание

Основание — слова-копирования: генераторы строки (копия — приёмник и источник) и слоя (ячейка строк) из `src/backend.fth`. Определение инструкции — она сама: тело этих слов не сводится к другим словам языка, а строка и слой — сами инструкции индексного пространства.

| Слово | Что порождает | Файл:строка |
|---|---|---|
| `lay-copy` | строка: копирование n бит из источника в приёмник | src/backend.fth:109 |
| `lay-link-row` | строка: копирование ссылки на следующий слой | src/backend.fth:108 |
| `lay-row` | строка: добавляет строку в слой | src/backend.fth:172 |
| `lay-new-record` | слой: новый слой в ячейке | src/backend.fth:135 |
| `lay-lone` | слой: отдельный слой в новой ячейке | src/backend.fth:139 |
| `lay-layer` | слой: следующий слой последовательности | src/backend.fth:142 |

## Слова ядра

Вид: генератор (слово словаря, исполняемое при компиляции, `doc/generators.md`; в пояснении слово компилятора), определение `:`, переменная, константа, данные `create`, цифра (литерал, `doc/literals.md`), основание. «Исп.» — число ссылок из других слов (цифры — и из чисел определения). Повторное определение имени — «вариант N» (старое имя остаётся у прежних ссылок).

| № | Слово | Вид | Файл:строка | Исп. | Пояснение |
|---|---|---|---|---|---|
| 1 | `nip` | определение `:` | src/prelude.fth:4 | 25 |  |
| 2 | `tuck` | определение `:` | src/prelude.fth:5 | 8 |  |
| 3 | `-rot` | определение `:` | src/prelude.fth:6 | 10 |  |
| 4 | `2dup` | определение `:` | src/prelude.fth:7 | 14 |  |
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
| 35 | `lay-size` | переменная | src/backend.fth:15 | 12 |  |
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
| 54 | `lay-bits` | определение `:` | src/backend.fth:29 | 7 |  |
| 55 | `lay-numeric` | определение `:` | src/backend.fth:30 | 7 |  |
| 56 | `lay-numeric4` | определение `:` | src/backend.fth:35 | 1 |  |
| 57 | `lay-field-check` | определение `:` | src/backend.fth:38 | 1 |  |
| 58 | `lay-encode` | определение `:` | src/backend.fth:40 | 3 |  |
| 59 | `lay-start` | переменная | src/backend.fth:50 | 8 |  |
| 60 | `lay-len` | переменная | src/backend.fth:50 | 10 |  |
| 61 | `lay-rows` | данные `create` | src/backend.fth:51 | 6 |  |
| 62 | `lay-row!` | определение `:` | src/backend.fth:52 | 7 |  |
| 63 | `lay-clear-rows` | определение `:` | src/backend.fth:54 | 3 |  |
| 64 | `lay-loader` | определение `:` | src/backend.fth:55 | 1 |  |
| 65 | `lay-stream-flush` | определение `:` | src/backend.fth:62 | 3 |  |
| 66 | `lay-begin-chunk` | определение `:` | src/backend.fth:66 | 2 |  |
| 67 | `lay-put` | определение `:` | src/backend.fth:68 | 14 |  |
| 68 | `lay-scratch` | данные `create` | src/backend.fth:86 | 2 |  |
| 69 | `lay-put-numeric` | определение `:` | src/backend.fth:87 | 3 |  |
| 70 | `lay-max-layers` | константа | src/backend.fth:91 | 3 |  |
| 71 | `lay-record` | определение `:` | src/backend.fth:92 | 1 |  |
| 72 | `lay-pending` | переменная | src/backend.fth:93 | 10 |  |
| 73 | `lay-head` | переменная | src/backend.fth:93 | 6 |  |
| 74 | `lay-next-cell` | переменная | src/backend.fth:93 | 8 |  |
| 75 | `lay-seq#` | переменная | src/backend.fth:94 | 8 |  |
| 76 | `lay-seq-first` | переменная | src/backend.fth:94 | 3 |  |
| 77 | `lay-seq-entry` | переменная | src/backend.fth:94 | 2 |  |
| 78 | `lay-seq-last` | переменная | src/backend.fth:94 | 2 |  |
| 79 | `lay-foff` | данные `create` | src/backend.fth:95 | 2 |  |
| 80 | `lay-foff-init` | определение `:` | src/backend.fth:96 | 1 |  |
| 81 | `lay-chunk-mem` | данные `create` | src/backend.fth:98 | 1 |  |
| 82 | `lay-lbuf-mem` | данные `create` | src/backend.fth:98 | 1 |  |
| 83 | `lay-ebuf-mem` | данные `create` | src/backend.fth:98 | 1 |  |
| 84 | `lay-pool-mem` | данные `create` | src/backend.fth:99 | 1 |  |
| 85 | `lay-bufs` | определение `:` | src/backend.fth:100 | 1 |  |
| 86 | `lay-machine` | определение `:` | src/backend.fth:101 | 1 |  |
| 87 | `lay-field` | определение `:` | src/backend.fth:107 | 44 |  |
| 88 | `lay-link-row` | основание | src/backend.fth:108 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 89 | `lay-copy` | основание | src/backend.fth:109 | 80 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 90 | `lay-builder` | определение `:` | src/backend.fth:111 | 1 |  |
| 91 | `lay-new-cell` | определение `:` | src/backend.fth:112 | 13 |  |
| 92 | `lay-branch-bit` | определение `:` | src/backend.fth:114 | 21 |  |
| 93 | `lay-branch-step` | определение `:` | src/backend.fth:115 | 3 |  |
| 94 | `lay-group` | определение `:` | src/backend.fth:116 | 5 |  |
| 95 | `lay-layer-cell` | определение `:` | src/backend.fth:119 | 41 |  |
| 96 | `lay-next!` | определение `:` | src/backend.fth:120 | 19 |  |
| 97 | `lay-count` | определение `:` | src/backend.fth:121 | 7 |  |
| 98 | `lay-row-addr` | определение `:` | src/backend.fth:122 | 4 |  |
| 99 | `lay-pending@` | определение `:` | src/backend.fth:123 | 5 |  |
| 100 | `lay-encode-layer` | определение `:` | src/backend.fth:124 | 1 |  |
| 101 | `lay-on-write` | переменная | src/backend.fth:130 | 6 |  |
| 102 | `lay-write` | определение `:` | src/backend.fth:131 | 2 |  |
| 103 | `lay-write-oldest` | определение `:` | src/backend.fth:134 | 1 |  |
| 104 | `lay-new-record` | основание | src/backend.fth:135 | 10 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 105 | `lay-lone` | основание | src/backend.fth:139 | 5 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 106 | `lay-seq` | определение `:` | src/backend.fth:140 | 9 |  |
| 107 | `lay-last` | определение `:` | src/backend.fth:141 | 4 |  |
| 108 | `lay-layer` | основание | src/backend.fth:142 | 85 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 109 | `lay-entry` | определение `:` | src/backend.fth:147 | 4 |  |
| 110 | `lay-jump` | определение `:` | src/backend.fth:148 | 13 |  |
| 111 | `lay-l1` | переменная | src/backend.fth:149 | 4 |  |
| 112 | `lay-h1` | переменная | src/backend.fth:149 | 3 |  |
| 113 | `lay-l2` | переменная | src/backend.fth:149 | 4 |  |
| 114 | `lay-h2` | переменная | src/backend.fth:149 | 3 |  |
| 115 | `lay-ra` | переменная | src/backend.fth:150 | 2 |  |
| 116 | `lay-rb` | переменная | src/backend.fth:150 | 2 |  |
| 117 | `lay-cur` | переменная | src/backend.fth:150 | 7 |  |
| 118 | `lay-clash?` | определение `:` | src/backend.fth:152 | 1 |  |
| 119 | `lay-row-clash?` | определение `:` | src/backend.fth:157 | 1 |  |
| 120 | `lay-new-row` | данные `create` | src/backend.fth:162 | 6 |  |
| 121 | `lay-row-set` | определение `:` | src/backend.fth:163 | 2 |  |
| 122 | `lay-full?` | определение `:` | src/backend.fth:165 | 2 |  |
| 123 | `lay-clashes?` | определение `:` | src/backend.fth:166 | 2 |  |
| 124 | `lay-fits?` | определение `:` | src/backend.fth:170 | 2 |  |
| 125 | `lay-row` | основание | src/backend.fth:172 | 81 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 126 | `lay-flush` | определение `:` | src/backend.fth:176 | 14 |  |
| 127 | `lay-finish` | определение `:` | src/backend.fth:179 | 1 |  |
| 128 | `dj-reader` | переменная | src/backend.fth:194 | 3 |  |
| 129 | `dj-bad-cell` | переменная | src/backend.fth:194 | 1 |  |
| 130 | `dj-bad-rule` | переменная | src/backend.fth:194 | 4 |  |
| 131 | `dj-bsh` | переменная | src/backend.fth:195 | 3 |  |
| 132 | `dj-csh` | переменная | src/backend.fth:195 | 6 |  |
| 133 | `dj-ssh` | переменная | src/backend.fth:195 | 2 |  |
| 134 | `dj-fsh` | переменная | src/backend.fth:195 | 2 |  |
| 135 | `dj-first` | переменная | src/backend.fth:196 | 2 |  |
| 136 | `dj-end` | переменная | src/backend.fth:196 | 2 |  |
| 137 | `dj-pa` | переменная | src/backend.fth:196 | 3 |  |
| 138 | `dj-cb` | переменная | src/backend.fth:196 | 8 |  |
| 139 | `dj-vdl` | переменная | src/backend.fth:197 | 16 |  |
| 140 | `dj-vdh` | переменная | src/backend.fth:197 | 12 |  |
| 141 | `dj-vsl` | переменная | src/backend.fth:197 | 14 |  |
| 142 | `dj-vsh` | переменная | src/backend.fth:197 | 12 |  |
| 143 | `dj-tc` | переменная | src/backend.fth:198 | 5 |  |
| 144 | `dj-ts` | переменная | src/backend.fth:198 | 6 |  |
| 145 | `dj-tf` | переменная | src/backend.fth:198 | 5 |  |
| 146 | `dj-tb` | переменная | src/backend.fth:198 | 2 |  |
| 147 | `dj-tn` | переменная | src/backend.fth:198 | 2 |  |
| 148 | `dj-tk` | переменная | src/backend.fth:198 | 7 |  |
| 149 | `dj-vt` | переменная | src/backend.fth:198 | 3 |  |
| 150 | `dj-blk` | переменная | src/backend.fth:199 | 5 |  |
| 151 | `dj-pr` | данные `create` | src/backend.fth:200 | 2 |  |
| 152 | `dj-tr` | данные `create` | src/backend.fth:200 | 3 |  |
| 153 | `dj-narrow` | константа | src/backend.fth:201 | 1 |  |
| 154 | `dj-seen` | данные `create` | src/backend.fth:202 | 2 |  |
| 155 | `dj-nseen` | переменная | src/backend.fth:202 | 6 |  |
| 156 | `dj-get` | определение `:` | src/backend.fth:203 | 9 |  |
| 157 | `dj-fail` | определение `:` | src/backend.fth:204 | 6 |  |
| 158 | `dj-blk?` | определение `:` | src/backend.fth:205 | 5 |  |
| 159 | `dj-in?` | определение `:` | src/backend.fth:206 | 4 |  |
| 160 | `dj-row!` | определение `:` | src/backend.fth:209 | 2 |  |
| 161 | `dj-row@` | определение `:` | src/backend.fth:211 | 3 |  |
| 162 | `dj-nop?` | определение `:` | src/backend.fth:213 | 4 |  |
| 163 | `dj-load` | определение `:` | src/backend.fth:214 | 1 |  |
| 164 | `dj-row-ok?` | определение `:` | src/backend.fth:222 | 1 |  |
| 165 | `dj-in-blk?` | определение `:` | src/backend.fth:227 | 2 |  |
| 166 | `dj-touches?` | определение `:` | src/backend.fth:231 | 1 |  |
| 167 | `dj-seen?` | определение `:` | src/backend.fth:232 | 1 |  |
| 168 | `dj-seen!` | определение `:` | src/backend.fth:237 | 1 |  |
| 169 | `dj-wide` | определение `:` | src/backend.fth:241 | 1 |  |
| 170 | `dj-patch` | определение `:` | src/backend.fth:257 | 1 |  |
| 171 | `dj-nn` | переменная | src/backend.fth:267 | 4 |  |
| 172 | `dj-lo` | переменная | src/backend.fth:267 | 2 |  |
| 173 | `dj-hi` | переменная | src/backend.fth:267 | 2 |  |
| 174 | `dj-scan` | определение `:` | src/backend.fth:268 | 1 |  |
| 175 | `dj-rows` | определение `:` | src/backend.fth:277 | 1 |  |
| 176 | `dj-prove` | определение `:` | src/backend.fth:284 | 3 |  |
| 177 | `lay-t1` | переменная | src/compute.fth:7 | 25 |  |
| 178 | `lay-t2` | переменная | src/compute.fth:7 | 13 |  |
| 179 | `lay-t3` | переменная | src/compute.fth:7 | 7 |  |
| 180 | `lay-t4` | переменная | src/compute.fth:7 | 4 |  |
| 181 | `lay-t5` | переменная | src/compute.fth:7 | 8 |  |
| 182 | `lay-lo` | переменная | src/compute.fth:8 | 5 |  |
| 183 | `lay-hi` | переменная | src/compute.fth:8 | 2 |  |
| 184 | `lay-l0` | переменная | src/compute.fth:9 | 21 |  |
| 185 | `lay-l1` | переменная | src/compute.fth:9 | 13 | вариант 2 |
| 186 | `lay-l2` | переменная | src/compute.fth:9 | 8 | вариант 2 |
| 187 | `lay-l3` | переменная | src/compute.fth:9 | 7 |  |
| 188 | `lay-l4` | переменная | src/compute.fth:9 | 7 |  |
| 189 | `lay-l5` | переменная | src/compute.fth:9 | 6 |  |
| 190 | `lay-work` | определение `:` | src/compute.fth:10 | 3 |  |
| 191 | `lay-cell-bit` | определение `:` | src/compute.fth:11 | 3 |  |
| 192 | `lay-link-slot` | определение `:` | src/compute.fth:12 | 6 |  |
| 193 | `lay-item-cells` | константа | src/compute.fth:13 | 1 |  |
| 194 | `lay-max-items` | константа | src/compute.fth:13 | 2 |  |
| 195 | `lay-items` | данные `create` | src/compute.fth:14 | 1 |  |
| 196 | `lay-nitems` | переменная | src/compute.fth:15 | 8 |  |
| 197 | `lay-item@` | определение `:` | src/compute.fth:16 | 6 |  |
| 198 | `lay-lookups-begin` | определение `:` | src/compute.fth:17 | 14 |  |
| 199 | `lay-item` | определение `:` | src/compute.fth:18 | 12 |  |
| 200 | `lay-seg` | определение `:` | src/compute.fth:23 | 18 |  |
| 201 | `lay-sl` | данные `create` | src/compute.fth:29 | 2 |  |
| 202 | `lay-sh` | данные `create` | src/compute.fth:29 | 2 |  |
| 203 | `lay-read-layer` | данные `create` | src/compute.fth:30 | 2 |  |
| 204 | `lay-read-slot` | данные `create` | src/compute.fth:30 | 2 |  |
| 205 | `lay-used` | данные `create` | src/compute.fth:31 | 2 |  |
| 206 | `lay-nused` | переменная | src/compute.fth:31 | 5 |  |
| 207 | `lay-rl` | переменная | src/compute.fth:31 | 6 |  |
| 208 | `lay-pk` | переменная | src/compute.fth:31 | 4 |  |
| 209 | `lay-pkl` | переменная | src/compute.fth:31 | 4 |  |
| 210 | `lay-npatches` | определение `:` | src/compute.fth:32 | 1 |  |
| 211 | `lay-used?` | определение `:` | src/compute.fth:33 | 1 |  |
| 212 | `lay-place-reads` | определение `:` | src/compute.fth:35 | 1 |  |
| 213 | `lay-patch` | определение `:` | src/compute.fth:47 | 1 |  |
| 214 | `lay-lookups` | определение `:` | src/compute.fth:56 | 14 |  |
| 215 | `lay-al` | данные `create` | src/compute.fth:62 | 2 |  |
| 216 | `lay-ar` | данные `create` | src/compute.fth:62 | 2 |  |
| 217 | `lay-ax` | переменная | src/compute.fth:63 | 4 |  |
| 218 | `lay-aa` | переменная | src/compute.fth:63 | 2 |  |
| 219 | `lay-ab` | переменная | src/compute.fth:63 | 2 |  |
| 220 | `lay-atab` | переменная | src/compute.fth:63 | 2 |  |
| 221 | `lay-acarry` | переменная | src/compute.fth:63 | 2 |  |
| 222 | `lay-al@` | определение `:` | src/compute.fth:64 | 8 |  |
| 223 | `lay-rd` | определение `:` | src/compute.fth:65 | 3 |  |
| 224 | `lay-adder-patch` | определение `:` | src/compute.fth:66 | 4 |  |
| 225 | `lay-adder` | определение `:` | src/compute.fth:71 | 6 |  |
| 226 | `lay-dsrc` | переменная | src/compute.fth:87 | 3 |  |
| 227 | `lay-dk` | переменная | src/compute.fth:87 | 5 |  |
| 228 | `lay-dg` | переменная | src/compute.fth:87 | 3 |  |
| 229 | `lay-dp` | переменная | src/compute.fth:87 | 3 |  |
| 230 | `lay-dx` | переменная | src/compute.fth:87 | 4 |  |
| 231 | `lay-decide` | определение `:` | src/compute.fth:88 | 2 |  |
| 232 | `lay-table-at` | переменная | src/compute.fth:95 | 4 |  |
| 233 | `lay-table-limit` | переменная | src/compute.fth:95 | 2 |  |
| 234 | `lay-tbuf` | переменная | src/compute.fth:95 | 6 |  |
| 235 | `lay-tx` | переменная | src/compute.fth:96 | 5 |  |
| 236 | `lay-tbits` | переменная | src/compute.fth:96 | 4 |  |
| 237 | `lay-ts` | переменная | src/compute.fth:96 | 6 |  |
| 238 | `lay-tsize` | переменная | src/compute.fth:96 | 6 |  |
| 239 | `lay-tbase` | переменная | src/compute.fth:96 | 4 |  |
| 240 | `lay-tper` | переменная | src/compute.fth:96 | 3 |  |
| 241 | `lay-tables` | определение `:` | src/compute.fth:97 | 2 |  |
| 242 | `lay-table-mem` | данные `create` | src/compute.fth:99 | 1 |  |
| 243 | `lay-table-area` | определение `:` | src/compute.fth:100 | 2 |  |
| 244 | `lay-table-done` | определение `:` | src/compute.fth:108 | 2 |  |
| 245 | `lay-table` | определение `:` | src/compute.fth:110 | 23 |  |
| 246 | `lay-add-entry` | определение `:` | src/compute.fth:127 | 1 |  |
| 247 | `lay-sub-entry` | определение `:` | src/compute.fth:129 | 2 |  |
| 248 | `lay-xor-entry` | определение `:` | src/compute.fth:131 | 1 |  |
| 249 | `lay-or-entry` | определение `:` | src/compute.fth:132 | 1 |  |
| 250 | `lay-and-entry` | определение `:` | src/compute.fth:133 | 1 |  |
| 251 | `lay-or8-entry` | определение `:` | src/compute.fth:134 | 1 |  |
| 252 | `lay-fz` | переменная | src/compute.fth:135 | 3 |  |
| 253 | `lay-fu` | переменная | src/compute.fth:135 | 4 |  |
| 254 | `lay-fs` | переменная | src/compute.fth:135 | 3 |  |
| 255 | `lay-pair` | определение `:` | src/compute.fth:136 | 6 |  |
| 256 | `lay-flags-entry` | определение `:` | src/compute.fth:137 | 1 |  |
| 257 | `lay-not5-entry` | определение `:` | src/compute.fth:144 | 1 |  |
| 258 | `lay-sign-entry` | определение `:` | src/compute.fth:145 | 1 |  |
| 259 | `lay-fill24-entry` | определение `:` | src/compute.fth:146 | 1 |  |
| 260 | `lay-fill16-entry` | определение `:` | src/compute.fth:147 | 1 |  |
| 261 | `lay-inc1-entry` | определение `:` | src/compute.fth:148 | 1 |  |
| 262 | `lay-inc2-entry` | определение `:` | src/compute.fth:149 | 1 |  |
| 263 | `lay-t-add` | переменная | src/compute.fth:150 | 7 |  |
| 264 | `lay-t-sub` | переменная | src/compute.fth:150 | 5 |  |
| 265 | `lay-t-xor` | переменная | src/compute.fth:150 | 5 |  |
| 266 | `lay-t-or` | переменная | src/compute.fth:150 | 2 |  |
| 267 | `lay-t-and` | переменная | src/compute.fth:150 | 2 |  |
| 268 | `lay-t-or8` | переменная | src/compute.fth:151 | 2 |  |
| 269 | `lay-t-flags` | переменная | src/compute.fth:151 | 2 |  |
| 270 | `lay-t-not5` | переменная | src/compute.fth:151 | 2 |  |
| 271 | `lay-t-sign32` | переменная | src/compute.fth:151 | 2 |  |
| 272 | `lay-t-fill24` | переменная | src/compute.fth:152 | 1 |  |
| 273 | `lay-t-fill16` | переменная | src/compute.fth:152 | 1 |  |
| 274 | `lay-t-inc1` | переменная | src/compute.fth:152 | 1 |  |
| 275 | `lay-t-inc2` | переменная | src/compute.fth:152 | 1 |  |
| 276 | `lay-standard-tables` | определение `:` | src/compute.fth:153 | 1 |  |
| 277 | `lay-oo` | переменная | src/compute.fth:161 | 2 |  |
| 278 | `lay-os` | переменная | src/compute.fth:161 | 2 |  |
| 279 | `lay-ol` | переменная | src/compute.fth:161 | 4 |  |
| 280 | `lay-oh` | переменная | src/compute.fth:161 | 3 |  |
| 281 | `lay-or-chunks` | определение `:` | src/compute.fth:162 | 3 |  |
| 282 | `lay-cr` | переменная | src/compute.fth:168 | 5 |  |
| 283 | `lay-ca` | переменная | src/compute.fth:168 | 4 |  |
| 284 | `lay-cb` | переменная | src/compute.fth:168 | 4 |  |
| 285 | `lay-logic` | определение `:` | src/compute.fth:175 | 4 |  |
| 286 | `lay-sres` | переменная | src/compute.fth:181 | 3 |  |
| 287 | `lay-sa` | переменная | src/compute.fth:181 | 7 |  |
| 288 | `lay-samt` | переменная | src/compute.fth:181 | 8 |  |
| 289 | `lay-sw` | переменная | src/compute.fth:181 | 9 |  |
| 290 | `lay-szero` | переменная | src/compute.fth:181 | 4 |  |
| 291 | `lay-sarg` | переменная | src/compute.fth:182 | 6 |  |
| 292 | `lay-sign` | переменная | src/compute.fth:182 | 6 |  |
| 293 | `lay-shift-row` | определение `:` | src/compute.fth:183 | 3 |  |
| 294 | `lay-shift-patch` | определение `:` | src/compute.fth:184 | 6 |  |
| 295 | `lay-shift-right` | определение `:` | src/compute.fth:186 | 1 |  |
| 296 | `lay-shift-left` | определение `:` | src/compute.fth:203 | 1 |  |
| 297 | `fc-size` | константа | src/forthc.fth:6 | 2 |  |
| 298 | `fc-cellb` | константа | src/forthc.fth:6 | 5 |  |
| 299 | `fc-l` | константа | src/forthc.fth:6 | 1 |  |
| 300 | `fc-a` | константа | src/forthc.fth:6 | 2 |  |
| 301 | `fc-d` | переменная | src/forthc.fth:8 | 3 |  |
| 302 | `fc-first` | переменная | src/forthc.fth:8 | 3 |  |
| 303 | `fc-guard` | переменная | src/forthc.fth:10 | 21 |  |
| 304 | `fc-bbits` | константа | src/forthc.fth:16 | 7 |  |
| 305 | `fc-abits` | константа | src/forthc.fth:16 | 5 |  |
| 306 | `fc-ebits` | константа | src/forthc.fth:16 | 2 |  |
| 307 | `fc-etab` | константа | src/forthc.fth:16 | 5 |  |
| 308 | `fc-rbits` | константа | src/forthc.fth:17 | 7 |  |
| 309 | `fc-rtab` | константа | src/forthc.fth:17 | 4 |  |
| 310 | `fc-layout` | определение `:` | src/forthc.fth:18 | 1 |  |
| 311 | `fc-d+` | определение `:` | src/forthc.fth:20 | 27 |  |
| 312 | `fc-sp` | определение `:` | src/forthc.fth:21 | 6 |  |
| 313 | `fc-rp` | определение `:` | src/forthc.fth:21 | 18 |  |
| 314 | `fc-handler` | определение `:` | src/forthc.fth:21 | 6 |  |
| 315 | `fc-code` | определение `:` | src/forthc.fth:21 | 4 |  |
| 316 | `fc-regs` | определение `:` | src/forthc.fth:22 | 2 |  |
| 317 | `fc-nregs` | константа | src/forthc.fth:22 | 2 |  |
| 318 | `fc-tmp` | определение `:` | src/forthc.fth:23 | 12 |  |
| 319 | `fc-xr` | определение `:` | src/forthc.fth:23 | 10 |  |
| 320 | `fc-z` | определение `:` | src/forthc.fth:23 | 4 |  |
| 321 | `fc-idx` | определение `:` | src/forthc.fth:23 | 5 |  |
| 322 | `fc-ma` | определение `:` | src/forthc.fth:24 | 6 |  |
| 323 | `fc-mb` | определение `:` | src/forthc.fth:24 | 6 |  |
| 324 | `fc-mp` | определение `:` | src/forthc.fth:24 | 2 |  |
| 325 | `fc-mq` | определение `:` | src/forthc.fth:24 | 3 |  |
| 326 | `fc-mr` | определение `:` | src/forthc.fth:24 | 3 |  |
| 327 | `fc-zero` | определение `:` | src/forthc.fth:25 | 12 |  |
| 328 | `fc-consts` | определение `:` | src/forthc.fth:25 | 3 |  |
| 329 | `fc-sw` | определение `:` | src/forthc.fth:26 | 2 |  |
| 330 | `fc-su` | определение `:` | src/forthc.fth:26 | 1 |  |
| 331 | `fc-key` | определение `:` | src/forthc.fth:26 | 3 |  |
| 332 | `fc-bp` | определение `:` | src/forthc.fth:26 | 2 |  |
| 333 | `fc-tab` | определение `:` | src/forthc.fth:27 | 1 |  |
| 334 | `fc-stk` | определение `:` | src/forthc.fth:27 | 3 |  |
| 335 | `fc-rstk` | определение `:` | src/forthc.fth:28 | 16 |  |
| 336 | `fc-scr0` | определение `:` | src/forthc.fth:28 | 1 |  |
| 337 | `fc-links` | определение `:` | src/forthc.fth:29 | 2 |  |
| 338 | `fc-max-links` | константа | src/forthc.fth:29 | 1 |  |
| 339 | `fc-link-chunk` | константа | src/forthc.fth:29 | 1 |  |
| 340 | `fc-mem` | определение `:` | src/forthc.fth:30 | 7 |  |
| 341 | `fc-mw` | константа | src/forthc.fth:30 | 2 |  |
| 342 | `fc-htab` | определение `:` | src/forthc.fth:30 | 1 |  |
| 343 | `fc-data-start` | константа | src/forthc.fth:31 | 1 |  |
| 344 | `fc-off` | данные `create` | src/forthc.fth:33 | 2 |  |
| 345 | `fc-oc` | переменная | src/forthc.fth:33 | 2 |  |
| 346 | `fc-t-rev8` | переменная | src/forthc.fth:34 | 3 |  |
| 347 | `fc-t-zero32` | переменная | src/forthc.fth:34 | 2 |  |
| 348 | `fc-t-nz2` | переменная | src/forthc.fth:34 | 2 |  |
| 349 | `fc-t-lt32` | переменная | src/forthc.fth:34 | 2 |  |
| 350 | `fc-t-xr2` | переменная | src/forthc.fth:35 | 2 |  |
| 351 | `fc-t-ult32` | переменная | src/forthc.fth:35 | 2 |  |
| 352 | `fc-t-bytepos` | переменная | src/forthc.fth:35 | 2 |  |
| 353 | `fc-off@` | определение `:` | src/forthc.fth:36 | 3 |  |
| 354 | `fc-off-table` | определение `:` | src/forthc.fth:37 | 1 |  |
| 355 | `fc-rev-entry` | определение `:` | src/forthc.fth:40 | 1 |  |
| 356 | `fc-zero-entry` | определение `:` | src/forthc.fth:41 | 1 |  |
| 357 | `fc-nz-entry` | определение `:` | src/forthc.fth:42 | 1 |  |
| 358 | `fc-lt-entry` | определение `:` | src/forthc.fth:43 | 1 |  |
| 359 | `fc-xr2-entry` | определение `:` | src/forthc.fth:46 | 1 |  |
| 360 | `fc-ult-entry` | определение `:` | src/forthc.fth:47 | 1 |  |
| 361 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 362 | `fc-tables` | определение `:` | src/forthc.fth:49 | 1 |  |
| 363 | `fc-mul4-entry` | определение `:` | src/forthc.fth:60 | 1 |  |
| 364 | `fc-qsel-entry` | определение `:` | src/forthc.fth:63 | 1 |  |
| 365 | `fc-max-consts` | переменная | src/forthc.fth:66 | 4 | вход бута (хост) |
| 366 | `fc-ck` | переменная | src/forthc.fth:66 | 3 |  |
| 367 | `fc-nconsts` | переменная | src/forthc.fth:66 | 7 |  |
| 368 | `fc-nbuckets` | переменная | src/forthc.fth:67 | 7 | вход бута (хост) |
| 369 | `fc-cbk` | переменная | src/forthc.fth:67 | 3 |  |
| 370 | `fc-ck@` | определение `:` | src/forthc.fth:68 | 3 |  |
| 371 | `fc-chash` | определение `:` | src/forthc.fth:69 | 1 |  |
| 372 | `fc-cb` | переменная | src/forthc.fth:70 | 3 |  |
| 373 | `fc-const2` | определение `:` | src/forthc.fth:71 | 1 |  |
| 374 | `fc-const` | определение `:` | src/forthc.fth:81 | 5 |  |
| 375 | `fc-lit` | определение `:` | src/forthc.fth:84 | 3 |  |
| 376 | `fc-bit0` | определение `:` | src/forthc.fth:85 | 1 |  |
| 377 | `fc-bit1` | определение `:` | src/forthc.fth:86 | 1 |  |
| 378 | `fc-length` | определение `:` | src/forthc.fth:87 | 1 |  |
| 379 | `fc-lit-of` | определение `:` | src/forthc.fth:88 | 2 |  |
| 380 | `fc-load` | определение `:` | src/forthc.fth:90 | 2 |  |
| 381 | `fc-nlinks` | переменная | src/forthc.fth:92 | 5 |  |
| 382 | `fc-link-buf` | переменная | src/forthc.fth:92 | 4 |  |
| 383 | `fc-nbuf` | переменная | src/forthc.fth:92 | 8 |  |
| 384 | `fc-put-links` | определение `:` | src/forthc.fth:93 | 2 |  |
| 385 | `fc-link-pair` | определение `:` | src/forthc.fth:97 | 2 |  |
| 386 | `fc-link-const` | определение `:` | src/forthc.fth:102 | 1 |  |
| 387 | `fc-eight` | данные `create` | src/forthc.fth:103 | 7 |  |
| 388 | `fc-zeros` | данные `create` | src/forthc.fth:103 | 5 |  |
| 389 | `fc-put-consts` | определение `:` | src/forthc.fth:104 | 1 |  |
| 390 | `fc-cache` | данные `create` | src/forthc.fth:111 | 8 |  |
| 391 | `fc-n` | переменная | src/forthc.fth:111 | 31 |  |
| 392 | `fc-pin` | данные `create` | src/forthc.fth:112 | 10 |  |
| 393 | `fc-npin` | переменная | src/forthc.fth:112 | 21 |  |
| 394 | `fc-c@` | определение `:` | src/forthc.fth:113 | 8 |  |
| 395 | `fc-push` | определение `:` | src/forthc.fth:114 | 30 |  |
| 396 | `fc-pop1` | определение `:` | src/forthc.fth:115 | 30 |  |
| 397 | `fc-in?` | определение `:` | src/forthc.fth:116 | 3 |  |
| 398 | `fc-reg` | определение `:` | src/forthc.fth:117 | 18 |  |
| 399 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:122 | 1 |  |
| 400 | `fc-scr` | переменная | src/forthc.fth:123 | 3 |  |
| 401 | `fc-scratch` | определение `:` | src/forthc.fth:124 | 11 |  |
| 402 | `fc-offs` | данные `create` | src/forthc.fth:127 | 5 |  |
| 403 | `fc-noff` | переменная | src/forthc.fth:127 | 9 |  |
| 404 | `fc-ptr` | переменная | src/forthc.fth:127 | 4 |  |
| 405 | `fc-iw` | переменная | src/forthc.fth:128 | 4 |  |
| 406 | `fc-adjust` | определение `:` | src/forthc.fth:129 | 7 |  |
| 407 | `fc-prow` | данные `create` | src/forthc.fth:135 | 2 |  |
| 408 | `fc-nrow` | переменная | src/forthc.fth:135 | 8 |  |
| 409 | `fc-pl` | данные `create` | src/forthc.fth:136 | 2 |  |
| 410 | `fc-pslot` | данные `create` | src/forthc.fth:136 | 2 |  |
| 411 | `fc-rl` | переменная | src/forthc.fth:137 | 3 |  |
| 412 | `fc-f0` | переменная | src/forthc.fth:137 | 2 |  |
| 413 | `fc-f1` | переменная | src/forthc.fth:137 | 2 |  |
| 414 | `fc-psh` | переменная | src/forthc.fth:137 | 2 |  |
| 415 | `fc-row+` | определение `:` | src/forthc.fth:138 | 3 |  |
| 416 | `fc-4@` | определение `:` | src/forthc.fth:140 | 3 |  |
| 417 | `fc-patched` | определение `:` | src/forthc.fth:141 | 3 |  |
| 418 | `fc-popped` | данные `create` | src/forthc.fth:152 | 2 |  |
| 419 | `fc-srcs` | данные `create` | src/forthc.fth:152 | 16 |  |
| 420 | `fc-nsrc` | переменная | src/forthc.fth:152 | 21 |  |
| 421 | `fc-mbase` | переменная | src/forthc.fth:153 | 8 |  |
| 422 | `fc-mptr` | переменная | src/forthc.fth:153 | 4 |  |
| 423 | `fc-mn` | переменная | src/forthc.fth:153 | 7 |  |
| 424 | `fc-mw2` | переменная | src/forthc.fth:153 | 6 |  |
| 425 | `fc-popped@` | определение `:` | src/forthc.fth:154 | 10 |  |
| 426 | `fc-shift` | определение `:` | src/forthc.fth:155 | 4 |  |
| 427 | `fc-mem-pop` | определение `:` | src/forthc.fth:156 | 5 |  |
| 428 | `fc-push-group` | определение `:` | src/forthc.fth:164 | 2 |  |
| 429 | `fc-dup-at` | определение `:` | src/forthc.fth:170 | 1 |  |
| 430 | `fc-rest` | данные `create` | src/forthc.fth:172 | 2 |  |
| 431 | `fc-nrest` | переменная | src/forthc.fth:172 | 3 |  |
| 432 | `fc-mem-push` | определение `:` | src/forthc.fth:173 | 8 |  |
| 433 | `fc-src1` | определение `:` | src/forthc.fth:179 | 3 |  |
| 434 | `fc-need` | определение `:` | src/forthc.fth:180 | 15 |  |
| 435 | `fc-spill` | определение `:` | src/forthc.fth:186 | 20 |  |
| 436 | `fc-pop` | определение `:` | src/forthc.fth:192 | 13 |  |
| 437 | `fc-max-log` | константа | src/forthc.fth:197 | 1 |  |
| 438 | `fc-max-notes` | константа | src/forthc.fth:197 | 3 |  |
| 439 | `fc-log` | переменная | src/forthc.fth:198 | 3 |  |
| 440 | `fc-nlog` | переменная | src/forthc.fth:198 | 5 |  |
| 441 | `fc-decs` | переменная | src/forthc.fth:198 | 2 |  |
| 442 | `fc-ndec` | переменная | src/forthc.fth:198 | 6 |  |
| 443 | `fc-calls` | переменная | src/forthc.fth:198 | 2 |  |
| 444 | `fc-ncall` | переменная | src/forthc.fth:198 | 6 |  |
| 445 | `fc-pend` | переменная | src/forthc.fth:199 | 2 |  |
| 446 | `fc-npend` | переменная | src/forthc.fth:199 | 9 |  |
| 447 | `fc-unknown` | переменная | src/forthc.fth:199 | 7 |  |
| 448 | `fc-lc` | переменная | src/forthc.fth:200 | 3 |  |
| 449 | `fc-lb` | переменная | src/forthc.fth:200 | 3 |  |
| 450 | `fc-row-n` | определение `:` | src/forthc.fth:201 | 1 |  |
| 451 | `fc-mem-row?` | определение `:` | src/forthc.fth:202 | 1 |  |
| 452 | `fc-log-layer` | определение `:` | src/forthc.fth:203 | 2 |  |
| 453 | `fc-log-begin` | определение `:` | src/forthc.fth:215 | 3 |  |
| 454 | `fc-log-end` | определение `:` | src/forthc.fth:217 | 4 |  |
| 455 | `fc-by-execution` | определение `:` | src/forthc.fth:218 | 8 |  |
| 456 | `fc-dec@` | определение `:` | src/forthc.fth:219 | 2 |  |
| 457 | `fc-call@` | определение `:` | src/forthc.fth:220 | 2 |  |
| 458 | `fc-log-decision` | определение `:` | src/forthc.fth:221 | 2 |  |
| 459 | `fc-log-call` | определение `:` | src/forthc.fth:225 | 2 |  |
| 460 | `fc-callee` | переменная | src/forthc.fth:229 | 4 |  |
| 461 | `fc-live` | переменная | src/forthc.fth:231 | 7 |  |
| 462 | `fc-tramp` | переменная | src/forthc.fth:231 | 8 |  |
| 463 | `fc-ex` | переменная | src/forthc.fth:231 | 4 |  |
| 464 | `fc-thrower` | переменная | src/forthc.fth:231 | 4 |  |
| 465 | `fc-jump` | определение `:` | src/forthc.fth:232 | 8 |  |
| 466 | `fc-end` | определение `:` | src/forthc.fth:233 | 15 |  |
| 467 | `fc-begin-block` | определение `:` | src/forthc.fth:234 | 25 |  |
| 468 | `fc-rows1` | определение `:` | src/forthc.fth:238 | 15 |  |
| 469 | `fc-nonzero` | определение `:` | src/forthc.fth:239 | 2 |  |
| 470 | `fc-branch` | определение `:` | src/forthc.fth:242 | 6 |  |
| 471 | `fc-rtab-at` | определение `:` | src/forthc.fth:243 | 1 |  |
| 472 | `fc-nret` | переменная | src/forthc.fth:244 | 6 |  |
| 473 | `fc-ret-link` | определение `:` | src/forthc.fth:248 | 4 |  |
| 474 | `fc-ret-base` | определение `:` | src/forthc.fth:253 | 4 |  |
| 475 | `fc-call` | определение `:` | src/forthc.fth:254 | 4 |  |
| 476 | `fc-v0` | переменная | src/forthc.fth:258 | 4 |  |
| 477 | `fc-v1` | переменная | src/forthc.fth:258 | 4 |  |
| 478 | `fc-jw` | определение `:` | src/forthc.fth:259 | 2 |  |
| 479 | `fc-xw` | определение `:` | src/forthc.fth:260 | 2 |  |
| 480 | `fc-xoff` | определение `:` | src/forthc.fth:261 | 2 |  |
| 481 | `fc-etab-at` | определение `:` | src/forthc.fth:262 | 1 |  |
| 482 | `fc-ex-base` | определение `:` | src/forthc.fth:263 | 1 |  |
| 483 | `fc-call-indirect` | определение `:` | src/forthc.fth:264 | 2 |  |
| 484 | `fc-push-frame` | определение `:` | src/forthc.fth:271 | 2 |  |
| 485 | `fc-link-copy` | определение `:` | src/forthc.fth:274 | 1 |  |
| 486 | `fc-restore` | определение `:` | src/forthc.fth:280 | 3 |  |
| 487 | `fc-build-thrower` | определение `:` | src/forthc.fth:282 | 1 |  |
| 488 | `fc-throw` | определение `:` | src/forthc.fth:288 | 1 |  |
| 489 | `fc-catch` | определение `:` | src/forthc.fth:291 | 1 |  |
| 490 | `fc-ret-p` | переменная | src/forthc.fth:300 | 4 |  |
| 491 | `fc-ret-l` | переменная | src/forthc.fth:300 | 6 |  |
| 492 | `fc-rs0` | переменная | src/forthc.fth:300 | 3 |  |
| 493 | `fc-rs1` | переменная | src/forthc.fth:300 | 3 |  |
| 494 | `fc-ret-m` | переменная | src/forthc.fth:300 | 3 |  |
| 495 | `fc-ret-t` | переменная | src/forthc.fth:300 | 3 |  |
| 496 | `fc-ret-patch` | определение `:` | src/forthc.fth:301 | 4 |  |
| 497 | `fc-ret-masked` | определение `:` | src/forthc.fth:303 | 1 |  |
| 498 | `fc-ret` | определение `:` | src/forthc.fth:309 | 3 |  |
| 499 | `fc-ca` | переменная | src/forthc.fth:321 | 3 |  |
| 500 | `fc-cl0` | переменная | src/forthc.fth:321 | 4 |  |
| 501 | `fc-cl1` | переменная | src/forthc.fth:321 | 4 |  |
| 502 | `fc-cr` | переменная | src/forthc.fth:321 | 4 |  |
| 503 | `fc-cslot` | переменная | src/forthc.fth:321 | 3 |  |
| 504 | `fc-csh` | переменная | src/forthc.fth:321 | 2 |  |
| 505 | `fc-cv` | переменная | src/forthc.fth:322 | 3 |  |
| 506 | `fc-cres` | переменная | src/forthc.fth:322 | 6 |  |
| 507 | `fc-cmode` | переменная | src/forthc.fth:322 | 6 |  |
| 508 | `fc-ar` | переменная | src/forthc.fth:322 | 5 |  |
| 509 | `fc-chk-read` | определение `:` | src/forthc.fth:323 | 1 |  |
| 510 | `fc-chk-seg` | определение `:` | src/forthc.fth:325 | 1 |  |
| 511 | `fc-as` | переменная | src/forthc.fth:328 | 2 |  |
| 512 | `fc-af` | переменная | src/forthc.fth:328 | 2 |  |
| 513 | `fc-al0` | переменная | src/forthc.fth:328 | 2 |  |
| 514 | `fc-al1` | переменная | src/forthc.fth:328 | 2 |  |
| 515 | `fc-apl` | переменная | src/forthc.fth:328 | 3 |  |
| 516 | `fc-afld` | переменная | src/forthc.fth:328 | 3 |  |
| 517 | `fc-access-patch` | определение `:` | src/forthc.fth:329 | 2 |  |
| 518 | `fc-access` | определение `:` | src/forthc.fth:334 | 1 |  |
| 519 | `fc-width` | определение `:` | src/forthc.fth:336 | 4 |  |
| 520 | `fc-check` | определение `:` | src/forthc.fth:337 | 4 |  |
| 521 | `fc-ring` | константа | src/forthc.fth:353 | 5 |  |
| 522 | `fc-window` | константа | src/forthc.fth:353 | 1 |  |
| 523 | `fc-sl` | данные `create` | src/forthc.fth:354 | 2 |  |
| 524 | `fc-stabs` | переменная | src/forthc.fth:354 | 2 |  |
| 525 | `fc-slen` | переменная | src/forthc.fth:355 | 7 |  |
| 526 | `fc-slow` | переменная | src/forthc.fth:355 | 4 |  |
| 527 | `fc-sinit` | определение `:` | src/forthc.fth:356 | 2 |  |
| 528 | `fc-sbegin` | определение `:` | src/forthc.fth:357 | 2 |  |
| 529 | `fc-tabs` | определение `:` | src/forthc.fth:358 | 3 |  |
| 530 | `fc-at` | определение `:` | src/forthc.fth:359 | 4 |  |
| 531 | `fc-has?` | определение `:` | src/forthc.fth:364 | 1 |  |
| 532 | `fc-tab+` | определение `:` | src/forthc.fth:365 | 1 |  |
| 533 | `fc-prw` | данные `create` | src/forthc.fth:366 | 6 |  |
| 534 | `fc-ptab` | переменная | src/forthc.fth:366 | 5 |  |
| 535 | `fc-place` | определение `:` | src/forthc.fth:367 | 3 |  |
| 536 | `fc-scopy` | определение `:` | src/forthc.fth:377 | 9 |  |
| 537 | `fc-segs` | данные `create` | src/forthc.fth:378 | 2 |  |
| 538 | `fc-nseg` | переменная | src/forthc.fth:378 | 5 |  |
| 539 | `fc-pp` | данные `create` | src/forthc.fth:379 | 2 |  |
| 540 | `fc-npp` | переменная | src/forthc.fth:379 | 4 |  |
| 541 | `fc-latest` | переменная | src/forthc.fth:379 | 4 |  |
| 542 | `fc-sga` | переменная | src/forthc.fth:379 | 14 |  |
| 543 | `fc-ltab` | переменная | src/forthc.fth:380 | 3 |  |
| 544 | `fc-ls` | переменная | src/forthc.fth:380 | 3 |  |
| 545 | `fc-lw` | переменная | src/forthc.fth:380 | 3 |  |
| 546 | `fc-ldst` | переменная | src/forthc.fth:380 | 2 |  |
| 547 | `fc-seg+` | определение `:` | src/forthc.fth:381 | 21 |  |
| 548 | `fc-pp+` | определение `:` | src/forthc.fth:384 | 1 |  |
| 549 | `fc-slookup` | определение `:` | src/forthc.fth:385 | 8 |  |
| 550 | `fc-nx` | переменная | src/forthc.fth:403 | 3 |  |
| 551 | `fc-nv` | переменная | src/forthc.fth:403 | 2 |  |
| 552 | `fc-nt` | переменная | src/forthc.fth:403 | 3 |  |
| 553 | `fc-negate-chain` | определение `:` | src/forthc.fth:404 | 1 |  |
| 554 | `fc-gw` | переменная | src/forthc.fth:410 | 4 |  |
| 555 | `fc-gs` | переменная | src/forthc.fth:410 | 2 |  |
| 556 | `fc-gs2` | переменная | src/forthc.fth:410 | 2 |  |
| 557 | `fc-gts` | переменная | src/forthc.fth:410 | 6 |  |
| 558 | `fc-gdst` | переменная | src/forthc.fth:410 | 2 |  |
| 559 | `fc-negate-select` | определение `:` | src/forthc.fth:411 | 4 |  |
| 560 | `fc-sfinish` | определение `:` | src/forthc.fth:416 | 2 |  |
| 561 | `fc-pr` | данные `create` | src/forthc.fth:419 | 2 |  |
| 562 | `fc-xs` | данные `create` | src/forthc.fth:419 | 2 |  |
| 563 | `fc-m4` | переменная | src/forthc.fth:420 | 2 |  |
| 564 | `fc-mj` | переменная | src/forthc.fth:420 | 11 |  |
| 565 | `fc-mk` | переменная | src/forthc.fth:420 | 6 |  |
| 566 | `fc-p@` | определение `:` | src/forthc.fth:421 | 3 |  |
| 567 | `fc-p!` | определение `:` | src/forthc.fth:422 | 1 |  |
| 568 | `fc-x@` | определение `:` | src/forthc.fth:423 | 3 |  |
| 569 | `fc-x!` | определение `:` | src/forthc.fth:424 | 2 |  |
| 570 | `fc-build-mul` | определение `:` | src/forthc.fth:425 | 1 |  |
| 571 | `fc-sub` | данные `create` | src/forthc.fth:443 | 2 |  |
| 572 | `fc-qsel` | переменная | src/forthc.fth:443 | 2 |  |
| 573 | `fc-absa` | переменная | src/forthc.fth:444 | 5 |  |
| 574 | `fc-absb` | переменная | src/forthc.fth:444 | 3 |  |
| 575 | `fc-ta` | переменная | src/forthc.fth:444 | 4 |  |
| 576 | `fc-tb` | переменная | src/forthc.fth:444 | 2 |  |
| 577 | `fc-rem` | переменная | src/forthc.fth:445 | 7 |  |
| 578 | `fc-tr` | переменная | src/forthc.fth:445 | 7 |  |
| 579 | `fc-q` | переменная | src/forthc.fth:445 | 3 |  |
| 580 | `fc-tq` | переменная | src/forthc.fth:445 | 4 |  |
| 581 | `fc-k` | переменная | src/forthc.fth:445 | 5 |  |
| 582 | `fc-w` | переменная | src/forthc.fth:446 | 14 |  |
| 583 | `fc-lo` | переменная | src/forthc.fth:446 | 7 |  |
| 584 | `fc-tlo` | переменная | src/forthc.fth:446 | 7 |  |
| 585 | `fc-t0` | переменная | src/forthc.fth:446 | 4 |  |
| 586 | `fc-t1` | переменная | src/forthc.fth:446 | 4 |  |
| 587 | `fc-qr` | переменная | src/forthc.fth:446 | 4 |  |
| 588 | `fc-tqk` | переменная | src/forthc.fth:446 | 3 |  |
| 589 | `fc-sub@` | определение `:` | src/forthc.fth:447 | 7 |  |
| 590 | `fc-step` | определение `:` | src/forthc.fth:448 | 3 |  |
| 591 | `fc-div-step` | определение `:` | src/forthc.fth:455 | 1 |  |
| 592 | `fc-build-div` | определение `:` | src/forthc.fth:472 | 1 |  |
| 593 | `fc-mul-entry` | переменная | src/forthc.fth:488 | 4 |  |
| 594 | `fc-mul-exit` | переменная | src/forthc.fth:488 | 2 |  |
| 595 | `fc-div-entry` | переменная | src/forthc.fth:488 | 5 |  |
| 596 | `fc-div-exit` | переменная | src/forthc.fth:488 | 4 |  |
| 597 | `fc-hl` | переменная | src/forthc.fth:489 | 5 |  |
| 598 | `fc-hcont` | переменная | src/forthc.fth:489 | 4 |  |
| 599 | `fc-mul-cost` | данные `create` | src/forthc.fth:490 | 2 |  |
| 600 | `fc-div-cost` | данные `create` | src/forthc.fth:490 | 2 |  |
| 601 | `fc-row-or-new` | определение `:` | src/forthc.fth:491 | 2 |  |
| 602 | `fc-call-helper` | определение `:` | src/forthc.fth:493 | 4 |  |
| 603 | `fc-result1` | определение `:` | src/forthc.fth:503 | 3 |  |
| 604 | `fc-s1` | переменная | src/forthc.fth:504 | 2 |  |
| 605 | `fc-s2` | переменная | src/forthc.fth:504 | 2 |  |
| 606 | `fc-r1` | переменная | src/forthc.fth:504 | 2 |  |
| 607 | `fc-result2` | определение `:` | src/forthc.fth:505 | 1 |  |
| 608 | `fc-pexit` | переменная | src/forthc.fth:512 | 2 |  |
| 609 | `fc-ptramp` | переменная | src/forthc.fth:512 | 2 |  |
| 610 | `fc-pd` | переменная | src/forthc.fth:512 | 5 |  |
| 611 | `fc-pc` | переменная | src/forthc.fth:512 | 5 |  |
| 612 | `fc-ends` | переменная | src/forthc.fth:512 | 3 |  |
| 613 | `fc-pb` | переменная | src/forthc.fth:513 | 5 |  |
| 614 | `fc-pcp` | переменная | src/forthc.fth:513 | 5 |  |
| 615 | `fc-pln` | переменная | src/forthc.fth:513 | 5 |  |
| 616 | `fc-pk` | переменная | src/forthc.fth:513 | 4 |  |
| 617 | `fc-pcall` | переменная | src/forthc.fth:513 | 3 |  |
| 618 | `fc-best` | данные `create` | src/forthc.fth:514 | 10 |  |
| 619 | `fc-pend@` | определение `:` | src/forthc.fth:515 | 7 |  |
| 620 | `fc-reach` | определение `:` | src/forthc.fth:516 | 2 |  |
| 621 | `fc-take` | определение `:` | src/forthc.fth:525 | 1 |  |
| 622 | `fc-end-path` | определение `:` | src/forthc.fth:532 | 1 |  |
| 623 | `fc-to` | определение `:` | src/forthc.fth:536 | 2 |  |
| 624 | `fc-node` | определение `:` | src/forthc.fth:540 | 1 |  |
| 625 | `fc-path` | определение `:` | src/forthc.fth:559 | 3 |  |
| 626 | `fc-cost!` | определение `:` | src/forthc.fth:568 | 3 |  |
| 627 | `fc-ll` | переменная | src/forthc.fth:570 | 6 |  |
| 628 | `fc-llr` | переменная | src/forthc.fth:570 | 3 |  |
| 629 | `fc-llv` | переменная | src/forthc.fth:570 | 3 |  |
| 630 | `fc-plit` | переменная | src/forthc.fth:570 | 6 |  |
| 631 | `fc-plr` | переменная | src/forthc.fth:570 | 4 |  |
| 632 | `fc-plv` | переменная | src/forthc.fth:570 | 6 |  |
| 633 | `fc-literal` | определение `:` | src/forthc.fth:571 | 14 |  |
| 634 | `fc-or-zero` | определение `:` | src/forthc.fth:573 | 2 |  |
| 635 | `fc-ba` | переменная | src/forthc.fth:576 | 13 |  |
| 636 | `fc-bb` | переменная | src/forthc.fth:576 | 13 |  |
| 637 | `fc-br` | переменная | src/forthc.fth:576 | 9 |  |
| 638 | `fc-binary` | определение `:` | src/forthc.fth:577 | 10 |  |
| 639 | `fc-r-at` | определение `:` | src/forthc.fth:601 | 2 |  |
| 640 | `fc-pop-pinned` | определение `:` | src/forthc.fth:604 | 3 |  |
| 641 | `fc-sk` | переменная | src/forthc.fth:605 | 12 |  |
| 642 | `fc-shift-copy` | определение `:` | src/forthc.fth:606 | 2 |  |
| 643 | `fc-inc` | определение `:` | src/forthc.fth:610 | 3 |  |
| 644 | `fc-read-key` | определение `:` | src/forthc.fth:613 | 1 |  |
| 645 | `fc-text-mem` | данные `create` | src/forthc.fth:618 | 1 |  |
| 646 | `fc-text` | переменная | src/forthc.fth:619 | 13 |  |
| 647 | `fc-tlen` | переменная | src/forthc.fth:619 | 14 |  |
| 648 | `fc-pos` | переменная | src/forthc.fth:619 | 24 |  |
| 649 | `fc-text-size` | переменная | src/forthc.fth:619 | 5 | вход бута (хост) |
| 650 | `fc-reset` | определение `:` | src/forthc.fth:620 | 3 |  |
| 651 | `fc-append` | определение `:` | src/forthc.fth:621 | 1 |  |
| 652 | `fc\|` | определение `:` | src/forthc.fth:625 | 1 | вход бута (хост) |
| 653 | `fc-ch` | определение `:` | src/forthc.fth:626 | 5 |  |
| 654 | `fc-more?` | определение `:` | src/forthc.fth:627 | 6 |  |
| 655 | `fc-next` | определение `:` | src/forthc.fth:628 | 8 |  |
| 656 | `fc-next!` | определение `:` | src/forthc.fth:636 | 10 |  |
| 657 | `fc-is?` | определение `:` | src/forthc.fth:637 | 5 |  |
| 658 | `fc-raw` | определение `:` | src/forthc.fth:640 | 1 |  |
| 659 | `fc-string-token` | определение `:` | src/forthc.fth:641 | 1 |  |
| 660 | `fc-names-size` | переменная | src/forthc.fth:646 | 4 | вход бута (хост) |
| 661 | `fc-max-words` | переменная | src/forthc.fth:646 | 4 | вход бута (хост) |
| 662 | `fc-names` | переменная | src/forthc.fth:647 | 3 |  |
| 663 | `fc-names-used` | переменная | src/forthc.fth:647 | 5 |  |
| 664 | `fc-wt` | переменная | src/forthc.fth:648 | 5 |  |
| 665 | `fc-nwords` | переменная | src/forthc.fth:648 | 12 |  |
| 666 | `fc-wbk` | переменная | src/forthc.fth:648 | 3 |  |
| 667 | `fc-wt@` | определение `:` | src/forthc.fth:651 | 6 |  |
| 668 | `fc-proved` | данные `create` | src/forthc.fth:653 | 2 |  |
| 669 | `fc-unproved` | данные `create` | src/forthc.fth:654 | 2 |  |
| 670 | `fc-mechanisms` | определение `:` | src/forthc.fth:655 | 1 |  |
| 671 | `fc-xt` | определение `:` | src/forthc.fth:660 | 5 |  |
| 672 | `fc-xtn` | определение `:` | src/forthc.fth:662 | 2 |  |
| 673 | `fc-hash` | определение `:` | src/forthc.fth:663 | 2 |  |
| 674 | `fc-define` | определение `:` | src/forthc.fth:665 | 6 |  |
| 675 | `fc-lookup` | определение `:` | src/forthc.fth:670 | 5 |  |
| 676 | `fc-find` | определение `:` | src/forthc.fth:674 | 6 |  |
| 677 | `fc-word-of` | определение `:` | src/forthc.fth:676 | 2 |  |
| 678 | `fc-cost` | определение `:` | src/forthc.fth:684 | 1 |  |
| 679 | `fc-proved?` | определение `:` | src/forthc.fth:687 | 1 |  |
| 680 | `fc-here` | переменная | src/forthc.fth:689 | 9 |  |
| 681 | `fc-word` | переменная | src/forthc.fth:689 | 13 |  |
| 682 | `fc-uses` | переменная | src/forthc.fth:689 | 16 |  |
| 683 | `fc-rt` | переменная | src/forthc.fth:690 | 7 |  |
| 684 | `fc-rta` | переменная | src/forthc.fth:690 | 7 |  |
| 685 | `fc-ctl` | данные `create` | src/forthc.fth:691 | 1 |  |
| 686 | `fc-nctl` | переменная | src/forthc.fth:691 | 12 |  |
| 687 | `fc-cleave` | переменная | src/forthc.fth:691 | 2 |  |
| 688 | `fc-ctl@` | определение `:` | src/forthc.fth:692 | 4 |  |
| 689 | `fc-ctl+` | определение `:` | src/forthc.fth:693 | 6 |  |
| 690 | `fc-ctl-` | определение `:` | src/forthc.fth:695 | 7 |  |
| 691 | `fc-do-entry` | определение `:` | src/forthc.fth:697 | 1 |  |
| 692 | `fc-ctl-leave` | определение `:` | src/forthc.fth:699 | 1 |  |
| 693 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:700 | 1 |  |
| 694 | `fc-loop-leave` | определение `:` | src/forthc.fth:701 | 1 |  |
| 695 | `fc-align` | определение `:` | src/forthc.fth:702 | 2 |  |
| 696 | `fc-check-here` | определение `:` | src/forthc.fth:703 | 3 |  |
| 697 | `fc-define-data` | определение `:` | src/forthc.fth:704 | 2 |  |
| 698 | `fc-sat` | переменная | src/forthc.fth:705 | 3 |  |
| 699 | `fc-store-string` | определение `:` | src/forthc.fth:706 | 1 |  |
| 700 | `fc-ct` | данные `create` | src/forthc.fth:711 | 3 |  |
| 701 | `fc-nct` | переменная | src/forthc.fth:711 | 11 |  |
| 702 | `fc-ct+` | определение `:` | src/forthc.fth:712 | 15 |  |
| 703 | `fc-ct-` | определение `:` | src/forthc.fth:713 | 9 |  |
| 704 | `fc-ct2` | определение `:` | src/forthc.fth:714 | 8 |  |
| 705 | `fc-inits` | данные `create` | src/forthc.fth:715 | 2 |  |
| 706 | `fc-ninit` | переменная | src/forthc.fth:715 | 5 |  |
| 707 | `fc-init-open` | переменная | src/forthc.fth:715 | 6 |  |
| 708 | `fc-ck-mem` | данные `create` | src/forthc.fth:718 | 1 |  |
| 709 | `fc-stabs-mem` | данные `create` | src/forthc.fth:718 | 1 |  |
| 710 | `fc-cbk-mem` | данные `create` | src/forthc.fth:718 | 1 |  |
| 711 | `fc-link-mem` | данные `create` | src/forthc.fth:718 | 1 |  |
| 712 | `fc-wt-mem` | данные `create` | src/forthc.fth:719 | 1 |  |
| 713 | `fc-names-mem` | данные `create` | src/forthc.fth:719 | 1 |  |
| 714 | `fc-wbk-mem` | данные `create` | src/forthc.fth:719 | 1 |  |
| 715 | `fc-log-mem` | данные `create` | src/forthc.fth:719 | 1 |  |
| 716 | `fc-decs-mem` | данные `create` | src/forthc.fth:720 | 1 |  |
| 717 | `fc-calls-mem` | данные `create` | src/forthc.fth:720 | 1 |  |
| 718 | `fc-pend-mem` | данные `create` | src/forthc.fth:720 | 1 |  |
| 719 | `fc-init` | определение `:` | src/forthc.fth:721 | 1 |  |
| 720 | `fc-scan-uses` | определение `:` | src/forthc.fth:734 | 1 |  |
| 721 | `fc-const-shift` | определение `:` | src/forthc.fth:741 | 2 |  |
| 722 | `fc-lit?` | определение `:` | src/forthc.fth:750 | 3 |  |
| 723 | `fc-mul-lit?` | определение `:` | src/forthc.fth:752 | 1 |  |
| 724 | `fc-shift-lit?` | определение `:` | src/forthc.fth:757 | 2 |  |
| 725 | `fc-pick-roll` | определение `:` | src/forthc.fth:760 | 2 |  |
| 726 | `fc-stx` | переменная | src/forthc.fth:769 | 3 |  |
| 727 | `fc-stlo` | переменная | src/forthc.fth:769 | 8 |  |
| 728 | `fc-sthi` | переменная | src/forthc.fth:769 | 4 |  |
| 729 | `fc-stp` | переменная | src/forthc.fth:769 | 6 |  |
| 730 | `fc-strow` | переменная | src/forthc.fth:769 | 8 |  |
| 731 | `fc-stm` | переменная | src/forthc.fth:769 | 5 |  |
| 732 | `fc-ftr` | переменная | src/forthc.fth:770 | 5 |  |
| 733 | `fc-stg` | переменная | src/forthc.fth:770 | 2 |  |
| 734 | `fc-sw0` | определение `:` | src/forthc.fth:771 | 2 |  |
| 735 | `fc-sw1` | определение `:` | src/forthc.fth:772 | 2 |  |
| 736 | `fc-sbase` | определение `:` | src/forthc.fth:773 | 2 |  |
| 737 | `fc-space-end` | определение `:` | src/forthc.fth:774 | 2 |  |
| 738 | `fc-space-store` | определение `:` | src/forthc.fth:782 | 2 |  |
| 739 | `fc-space-fetch` | определение `:` | src/forthc.fth:789 | 2 |  |
| 740 | `fc-cp` | определение `:` | src/forthc.fth:800 | 4 |  |
| 741 | `fc-copy-row` | определение `:` | src/forthc.fth:802 | 1 |  |
| 742 | `fc-close-init` | определение `:` | src/forthc.fth:805 | 2 |  |
| 743 | `fc-open-init` | определение `:` | src/forthc.fth:808 | 1 |  |
| 744 | `fc-gens` | переменная | src/forthc.fth:819 | 3 |  |
| 745 | `fc-generator` | определение `:` | src/forthc.fth:820 | 88 |  |
| 746 | `fc-literal-name` | определение `:` | src/forthc.fth:822 | 10 |  |
| 747 | `fc-words` | определение `:` | src/forthc.fth:824 | 1 |  |
| 748 | `fc-known` | определение `:` | src/forthc.fth:833 | 1 |  |
| 749 | `fc-defining?` | определение `:` | src/forthc.fth:835 | 7 |  |
| 750 | `fc-code` | определение `:` | src/forthc.fth:836 | 52 | вариант 2 |
| 751 | `fc-fold?` | определение `:` | src/forthc.fth:838 | 13 |  |
| 752 | `fc-top-only` | определение `:` | src/forthc.fth:839 | 6 |  |
| 753 | `fc-not-found` | определение `:` | src/forthc.fth:841 | 1 |  |
| 754 | `fc-word-token` | определение `:` | src/forthc.fth:843 | 2 |  |
| 755 | `fc-token` | определение `:` | src/forthc.fth:848 | 2 |  |
| 756 | `fc-synonym-of` | определение `:` | src/forthc.fth:849 | 2 |  |
| 757 | `fc-synonym` | определение `:` | src/forthc.fth:850 | 10 |  |
| 758 | `fc-sy` | переменная | src/forthc.fth:853 | 2 |  |
| 759 | `fc-synonym?` | определение `:` | src/forthc.fth:854 | 1 |  |
| 760 | `fc-poke` | определение `:` | src/forthc.fth:857 | 2 |  |
| 761 | `fc-concept-record` | определение `:` | src/forthc.fth:860 | 1 |  |
| 762 | `fc-eval` | определение `:` | src/forthc.fth:865 | 54 |  |
| 763 | `fc-concepts` | определение `:` | src/forthc.fth:869 | 1 |  |
| 764 | `fc-nhost` | переменная | src/forthc.fth:876 | 5 |  |
| 765 | `fc-platform` | определение `:` | src/forthc.fth:877 | 1 |  |
| 766 | `fc-time-price` | определение `:` | src/forthc.fth:900 | 1 |  |
| 767 | `fc-replacement` | определение `:` | src/forthc.fth:910 | 1 |  |
| 768 | `fc-library` | определение `:` | src/forthc.fth:925 | 1 |  |
| 769 | `fc-long` | определение `:` | src/forthc.fth:944 | 1 |  |
| 770 | `fc-helpers-cost` | определение `:` | src/forthc.fth:952 | 1 |  |
| 771 | `fc-price-word` | определение `:` | src/forthc.fth:959 | 1 |  |
| 772 | `fc-compile` | определение `:` | src/forthc.fth:962 | 1 |  |
| 773 | `fc-go` | определение `:` | src/forthc.fth:979 | 3 | вход бута (хост) |
| 774 | `gen+` | определение `:` | src/primitives.fth:4 | 5 |  |
| 775 | `gen-` | определение `:` | src/primitives.fth:5 | 2 |  |
| 776 | `gen-and` | определение `:` | src/primitives.fth:6 | 2 |  |
| 777 | `gen-or` | определение `:` | src/primitives.fth:7 | 2 |  |
| 778 | `gen-xor` | определение `:` | src/primitives.fth:8 | 2 |  |
| 779 | `gen=` | определение `:` | src/primitives.fth:9 | 2 |  |
| 780 | `gen<` | определение `:` | src/primitives.fth:10 | 2 |  |
| 781 | `gen-u<` | определение `:` | src/primitives.fth:11 | 2 |  |
| 782 | `gen-lshift` | определение `:` | src/primitives.fth:12 | 2 |  |
| 783 | `gen-rshift` | определение `:` | src/primitives.fth:14 | 2 |  |
| 784 | `gen-0=` | определение `:` | src/primitives.fth:16 | 2 |  |
| 785 | `gen-cells` | определение `:` | src/primitives.fth:17 | 2 |  |
| 786 | `gen-2*` | определение `:` | src/primitives.fth:18 | 2 |  |
| 787 | `gen-1+` | определение `:` | src/primitives.fth:19 | 2 |  |
| 788 | `gen-1-` | определение `:` | src/primitives.fth:20 | 2 |  |
| 789 | `gen-cell+` | определение `:` | src/primitives.fth:21 | 2 |  |
| 790 | `gen*` | определение `:` | src/primitives.fth:22 | 2 |  |
| 791 | `gen/` | определение `:` | src/primitives.fth:25 | 2 |  |
| 792 | `gen-mod` | определение `:` | src/primitives.fth:26 | 2 |  |
| 793 | `gen/mod` | определение `:` | src/primitives.fth:27 | 2 |  |
| 794 | `gen-dup` | определение `:` | src/primitives.fth:28 | 2 |  |
| 795 | `gen-drop` | определение `:` | src/primitives.fth:29 | 2 |  |
| 796 | `gen-swap` | определение `:` | src/primitives.fth:30 | 2 |  |
| 797 | `gen-over` | определение `:` | src/primitives.fth:31 | 2 |  |
| 798 | `gen-rot` | определение `:` | src/primitives.fth:32 | 2 |  |
| 799 | `gen-pick` | определение `:` | src/primitives.fth:33 | 2 |  |
| 800 | `gen-roll` | определение `:` | src/primitives.fth:34 | 2 |  |
| 801 | `gen->r` | определение `:` | src/primitives.fth:35 | 2 |  |
| 802 | `gen-r>` | определение `:` | src/primitives.fth:36 | 2 |  |
| 803 | `gen-r@` | определение `:` | src/primitives.fth:37 | 4 |  |
| 804 | `gen-j` | определение `:` | src/primitives.fth:38 | 2 |  |
| 805 | `gen-@` | определение `:` | src/primitives.fth:39 | 2 |  |
| 806 | `gen-!` | определение `:` | src/primitives.fth:41 | 2 |  |
| 807 | `gen-c@` | определение `:` | src/primitives.fth:42 | 2 |  |
| 808 | `gen-c!` | определение `:` | src/primitives.fth:44 | 2 |  |
| 809 | `gen-emit` | определение `:` | src/primitives.fth:45 | 2 |  |
| 810 | `gen-key` | определение `:` | src/primitives.fth:48 | 2 |  |
| 811 | `gen-if` | определение `:` | src/primitives.fth:50 | 2 |  |
| 812 | `gen-else` | определение `:` | src/primitives.fth:51 | 2 |  |
| 813 | `gen-then` | определение `:` | src/primitives.fth:53 | 2 |  |
| 814 | `gen-begin` | определение `:` | src/primitives.fth:57 | 2 |  |
| 815 | `gen-until` | определение `:` | src/primitives.fth:58 | 2 |  |
| 816 | `gen-while` | определение `:` | src/primitives.fth:60 | 2 |  |
| 817 | `gen-repeat` | определение `:` | src/primitives.fth:61 | 2 |  |
| 818 | `gen-again` | определение `:` | src/primitives.fth:62 | 2 |  |
| 819 | `gen-do` | определение `:` | src/primitives.fth:63 | 2 |  |
| 820 | `fc-di` | переменная | src/primitives.fth:66 | 3 |  |
| 821 | `fc-dl` | переменная | src/primitives.fth:66 | 3 |  |
| 822 | `gen-?do` | определение `:` | src/primitives.fth:67 | 2 |  |
| 823 | `fc-lv` | переменная | src/primitives.fth:73 | 2 |  |
| 824 | `gen-loop` | определение `:` | src/primitives.fth:74 | 2 |  |
| 825 | `gen-leave` | определение `:` | src/primitives.fth:83 | 2 |  |
| 826 | `gen-unloop` | определение `:` | src/primitives.fth:86 | 2 |  |
| 827 | `gen-exit` | определение `:` | src/primitives.fth:87 | 2 |  |
| 828 | `gen-bye` | определение `:` | src/primitives.fth:90 | 2 |  |
| 829 | `gen-recurse` | определение `:` | src/primitives.fth:92 | 2 |  |
| 830 | `gen-tick` | определение `:` | src/primitives.fth:93 | 2 |  |
| 831 | `gen-throw` | определение `:` | src/primitives.fth:96 | 2 |  |
| 832 | `gen-call` | определение `:` | src/primitives.fth:100 | 3 |  |
| 833 | `gen-space!` | определение `:` | src/primitives.fth:101 | 2 |  |
| 834 | `gen-spacec!` | определение `:` | src/primitives.fth:102 | 2 |  |
| 835 | `gen-space@` | определение `:` | src/primitives.fth:103 | 2 |  |
| 836 | `gen-spacec@` | определение `:` | src/primitives.fth:104 | 2 |  |
| 837 | `gen-execute` | определение `:` | src/primitives.fth:105 | 2 |  |
| 838 | `gen-catch` | определение `:` | src/primitives.fth:106 | 2 |  |
| 839 | `fc-entry-cell` | определение `:` | src/primitives.fth:112 | 1 |  |
| 840 | `fc-concept` | определение `:` | src/primitives.fth:114 | 1 |  |
| 841 | `gen-colon` | определение `:` | src/primitives.fth:121 | 2 |  |
| 842 | `gen-semicolon` | определение `:` | src/primitives.fth:127 | 2 |  |
| 843 | `gen-variable` | определение `:` | src/primitives.fth:130 | 2 |  |
| 844 | `gen-create` | определение `:` | src/primitives.fth:131 | 2 |  |
| 845 | `gen-allot` | определение `:` | src/primitives.fth:132 | 2 |  |
| 846 | `gen-constant` | определение `:` | src/primitives.fth:133 | 2 |  |
| 847 | `gen-decimal` | определение `:` | src/primitives.fth:134 | 2 |  |
| 848 | `gen-kernel-layout` | определение `:` | src/primitives.fth:135 | 2 |  |
| 849 | `gen-backslash` | определение `:` | src/primitives.fth:136 | 2 |  |
| 850 | `gen-paren` | определение `:` | src/primitives.fth:138 | 4 |  |
| 851 | `gen-char` | определение `:` | src/primitives.fth:139 | 2 |  |
| 852 | `gen-string` | определение `:` | src/primitives.fth:140 | 2 |  |
| 853 | `fc-digit@` | определение `:` | src/primitives.fth:143 | 1 |  |
| 854 | `gen-literal` | определение `:` | src/primitives.fth:145 | 2 |  |
| 855 | `fc-known-xt` | определение `:` | src/primitives.fth:152 | 2 |  |
| 856 | `gen-cost` | определение `:` | src/primitives.fth:153 | 2 |  |
| 857 | `gen-proved?` | определение `:` | src/primitives.fth:155 | 2 |  |
| 858 | `gen-library` | определение `:` | src/primitives.fth:156 | 16 |  |
| 859 | `gen-price` | определение `:` | src/primitives.fth:157 | 2 |  |
| 860 | `fc-cpos` | переменная | src/primitives.fth:162 | 4 |  |
| 861 | `fc-hn` | переменная | src/primitives.fth:162 | 2 |  |
| 862 | `fc-cdepth` | переменная | src/primitives.fth:162 | 4 |  |
| 863 | `fc-hname` | данные `create` | src/primitives.fth:162 | 2 |  |
| 864 | `fc-hb` | определение `:` | src/primitives.fth:163 | 3 |  |
| 865 | `fc-c,` | определение `:` | src/primitives.fth:164 | 17 |  |
| 866 | `fc-c1` | определение `:` | src/primitives.fth:165 | 8 |  |
| 867 | `fc-c-gen` | определение `:` | src/primitives.fth:166 | 1 |  |
| 868 | `fc-c-body` | определение `:` | src/primitives.fth:170 | 1 |  |
| 869 | `gen-host` | определение `:` | src/primitives.fth:179 | 2 |  |
| 870 | `fc-name2` | определение `:` | src/primitives.fth:196 | 1 |  |
| 871 | `fc-generators` | определение `:` | src/primitives.fth:199 | 1 |  |
| 872 | `+` | генератор | src/primitives.fth:200 | 559 | слово компилятора `gen+` |
| 873 | `-` | генератор | src/primitives.fth:200 | 63 | слово компилятора `gen-` |
| 874 | `*` | генератор | src/primitives.fth:201 | 78 | слово компилятора `gen*` |
| 875 | `/` | генератор | src/primitives.fth:201 | 4 | слово компилятора `gen/` |
| 876 | `mod` | генератор | src/primitives.fth:202 | 2 | слово компилятора `gen-mod` |
| 877 | `and` | генератор | src/primitives.fth:203 | 117 | слово компилятора `gen-and` |
| 878 | `or` | генератор | src/primitives.fth:203 | 43 | слово компилятора `gen-or` |
| 879 | `xor` | генератор | src/primitives.fth:204 | 5 | слово компилятора `gen-xor` |
| 880 | `lshift` | генератор | src/primitives.fth:204 | 94 | слово компилятора `gen-lshift` |
| 881 | `rshift` | генератор | src/primitives.fth:205 | 62 | слово компилятора `gen-rshift` |
| 882 | `=` | генератор | src/primitives.fth:205 | 81 | слово компилятора `gen=` |
| 883 | `<` | генератор | src/primitives.fth:206 | 24 | слово компилятора `gen<` |
| 884 | `u<` | генератор | src/primitives.fth:206 | 26 | слово компилятора `gen-u<` |
| 885 | `0=` | генератор | src/primitives.fth:207 | 102 | слово компилятора `gen-0=` |
| 886 | `2*` | генератор | src/primitives.fth:207 | 29 | слово компилятора `gen-2*` |
| 887 | `1+` | генератор | src/primitives.fth:208 | 43 | слово компилятора `gen-1+` |
| 888 | `1-` | генератор | src/primitives.fth:208 | 55 | слово компилятора `gen-1-` |
| 889 | `cells` | генератор | src/primitives.fth:209 | 273 | слово компилятора `gen-cells` |
| 890 | `cell+` | генератор | src/primitives.fth:209 | 57 | слово компилятора `gen-cell+` |
| 891 | `dup` | генератор | src/primitives.fth:210 | 300 | слово компилятора `gen-dup` |
| 892 | `drop` | генератор | src/primitives.fth:210 | 205 | слово компилятора `gen-drop` |
| 893 | `swap` | генератор | src/primitives.fth:211 | 146 | слово компилятора `gen-swap` |
| 894 | `over` | генератор | src/primitives.fth:211 | 86 | слово компилятора `gen-over` |
| 895 | `rot` | генератор | src/primitives.fth:212 | 37 | слово компилятора `gen-rot` |
| 896 | `pick` | генератор | src/primitives.fth:212 | 44 | слово компилятора `gen-pick` |
| 897 | `roll` | генератор | src/primitives.fth:213 | 7 | слово компилятора `gen-roll` |
| 898 | `>r` | генератор | src/primitives.fth:213 | 111 | слово компилятора `gen->r` |
| 899 | `r>` | генератор | src/primitives.fth:214 | 115 | слово компилятора `gen-r>` |
| 900 | `r@` | генератор | src/primitives.fth:214 | 108 | слово компилятора `gen-r@` |
| 901 | `i` | генератор | src/primitives.fth:215 | 172 | слово компилятора `gen-r@` |
| 902 | `j` | генератор | src/primitives.fth:215 | 12 | слово компилятора `gen-j` |
| 903 | `@` | генератор | src/primitives.fth:216 | 1249 | слово компилятора `gen-@` |
| 904 | `!` | генератор | src/primitives.fth:216 | 661 | слово компилятора `gen-!` |
| 905 | `c@` | генератор | src/primitives.fth:217 | 23 | слово компилятора `gen-c@` |
| 906 | `c!` | генератор | src/primitives.fth:217 | 18 | слово компилятора `gen-c!` |
| 907 | `space!` | генератор | src/primitives.fth:218 | 1 | слово компилятора `gen-space!` |
| 908 | `spacec!` | генератор | src/primitives.fth:218 | 1 | слово компилятора `gen-spacec!` |
| 909 | `space@` | генератор | src/primitives.fth:219 | 1 | слово компилятора `gen-space@` |
| 910 | `emit` | генератор | src/primitives.fth:220 | 4 | слово компилятора `gen-emit` |
| 911 | `key` | генератор | src/primitives.fth:220 | 1 | слово компилятора `gen-key` |
| 912 | `if` | генератор | src/primitives.fth:221 | 302 | слово компилятора `gen-if` |
| 913 | `else` | генератор | src/primitives.fth:221 | 83 | слово компилятора `gen-else` |
| 914 | `then` | генератор | src/primitives.fth:222 | 302 | слово компилятора `gen-then` |
| 915 | `begin` | генератор | src/primitives.fth:222 | 25 | слово компилятора `gen-begin` |
| 916 | `until` | генератор | src/primitives.fth:223 | 2 | слово компилятора `gen-until` |
| 917 | `while` | генератор | src/primitives.fth:223 | 22 | слово компилятора `gen-while` |
| 918 | `repeat` | генератор | src/primitives.fth:224 | 22 | слово компилятора `gen-repeat` |
| 919 | `again` | генератор | src/primitives.fth:224 | 1 | слово компилятора `gen-again` |
| 920 | `do` | генератор | src/primitives.fth:225 | 31 | слово компилятора `gen-do` |
| 921 | `?do` | генератор | src/primitives.fth:225 | 58 | слово компилятора `gen-?do` |
| 922 | `loop` | генератор | src/primitives.fth:226 | 89 | слово компилятора `gen-loop` |
| 923 | `leave` | генератор | src/primitives.fth:226 | 1 | слово компилятора `gen-leave` |
| 924 | `unloop` | генератор | src/primitives.fth:227 | 7 | слово компилятора `gen-unloop` |
| 925 | `exit` | генератор | src/primitives.fth:227 | 81 | слово компилятора `gen-exit` |
| 926 | `bye` | генератор | src/primitives.fth:228 | 1 | слово компилятора `gen-bye` |
| 927 | `recurse` | генератор | src/primitives.fth:229 | 2 | слово компилятора `gen-recurse` |
| 928 | `execute` | генератор | src/primitives.fth:229 | 10 | слово компилятора `gen-execute` |
| 929 | `[']` | генератор | src/primitives.fth:230 | 119 | слово компилятора `gen-tick` |
| 930 | `:` | генератор | src/primitives.fth:232 | 495 | слово компилятора `gen-colon` |
| 931 | `;` | генератор | src/primitives.fth:232 | 495 | слово компилятора `gen-semicolon` |
| 932 | `variable` | генератор | src/primitives.fth:233 | 320 | слово компилятора `gen-variable` |
| 933 | `create` | генератор | src/primitives.fth:233 | 62 | слово компилятора `gen-create` |
| 934 | `allot` | генератор | src/primitives.fth:234 | 62 | слово компилятора `gen-allot` |
| 935 | `constant` | генератор | src/primitives.fth:234 | 23 | слово компилятора `gen-constant` |
| 936 | `decimal` | генератор | src/primitives.fth:235 | 3 | слово компилятора `gen-decimal` |
| 937 | `kernel-layout` | генератор | src/primitives.fth:235 | 1 | слово компилятора `gen-kernel-layout` |
| 938 | `\` | генератор | src/primitives.fth:236 | 147 | слово компилятора `gen-backslash` |
| 939 | `(` | генератор | src/primitives.fth:236 | 474 | слово компилятора `gen-paren` |
| 940 | `[char]` | генератор | src/primitives.fth:236 | 8 | слово компилятора `gen-char` |
| 941 | `s"` | генератор | src/primitives.fth:237 | 199 | слово компилятора `gen-string` |
| 942 | `literal` | генератор | src/primitives.fth:238 | 503 | слово компилятора `gen-literal` |
| 943 | `0` | цифра (литерал) | src/primitives.fth:246 | 542 | значение 0 |
| 944 | `1` | цифра (литерал) | src/primitives.fth:246 | 459 | значение 1 |
| 945 | `2` | цифра (литерал) | src/primitives.fth:246 | 452 | значение 2 |
| 946 | `3` | цифра (литерал) | src/primitives.fth:246 | 303 | значение 3 |
| 947 | `4` | цифра (литерал) | src/primitives.fth:247 | 237 | значение 4 |
| 948 | `5` | цифра (литерал) | src/primitives.fth:247 | 106 | значение 5 |
| 949 | `6` | цифра (литерал) | src/primitives.fth:247 | 165 | значение 6 |
| 950 | `7` | цифра (литерал) | src/primitives.fth:247 | 64 | значение 7 |
| 951 | `8` | цифра (литерал) | src/primitives.fth:248 | 160 | значение 8 |
| 952 | `9` | цифра (литерал) | src/primitives.fth:248 | 42 | значение 9 |
| 953 | `fc-install-generators` | определение `:` | src/primitives.fth:249 | 1 |  |
| 954 | `fc-read` | определение `:` | src/main.fth:3 | 2 |  |
| 955 | `fc-sizes` | определение `:` | src/main.fth:8 | 2 |  |
| 956 | `kn-at` | переменная | src/kernel.fth:7 | 5 |  |
| 957 | `kn-put` | определение `:` | src/kernel.fth:8 | 1 |  |
| 958 | `kn-order` | определение `:` | src/kernel.fth:16 | 1 |  |
| 959 | `kn-get` | определение `:` | src/kernel.fth:18 | 1 |  |
| 960 | `kn-compile` | определение `:` | src/kernel.fth:19 | 1 |  |
| 961 | `main` | определение `:` | src/kernel.fth:25 | 1 | вариант 2 |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 91.

## Определены, но не использованы

Слов: 36. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

| Слово | Вид | Файл:строка |
|---|---|---|
| `lay-out` | определение `:` | src/backend.fth:110 |
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
| `fc-depth` | определение `:` | src/forthc.fth:831 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:832 |
| `/mod` | генератор | src/primitives.fth:202 |
| `spacec@` | генератор | src/primitives.fth:219 |
| `catch` | генератор | src/primitives.fth:230 |
| `throw` | генератор | src/primitives.fth:231 |
| `cost` | генератор | src/primitives.fth:239 |
| `price` | генератор | src/primitives.fth:239 |
| `proved?` | генератор | src/primitives.fth:240 |
| `check-table` | генератор | src/primitives.fth:241 |
| `accuracy` | генератор | src/primitives.fth:241 |
| `replace` | генератор | src/primitives.fth:242 |
| `long!` | генератор | src/primitives.fth:243 |
| `long@` | генератор | src/primitives.fth:243 |
| `host` | генератор | src/primitives.fth:244 |
| `time` | генератор | src/primitives.fth:244 |
| `platform` | генератор | src/primitives.fth:245 |
| `platform-of` | генератор | src/primitives.fth:245 |
| `main` (вариант 1) | определение `:` | src/main.fth:11 |

## Слова, которые при буте исполняет хост

Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки `backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках 82; все они определены в определении языка (генератором в `primitives.fth` или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: `!` `*` `+` `+!` `-` `-rot` `/` `/string` `0<` `0<>` `0=` `0>` `1+` `1-` `2!` `2*` `2@` `2drop` `2dup` `2over` `2swap` `<` `<>` `=` `>` `>in` `>r` `?do` `?dup` `@` `again` `and` `begin` `bye` `c!` `c@` `cell+` `cells` `cmove` `cmove>` `compare` `decimal` `do` `drop` `dup` `else` `emit` `execute` `exit` `fill` `i` `if` `invert` `j` `leave` `loop` `lshift` `max` `min` `mod` `negate` `nip` `or` `over` `pick` `r>` `r@` `repeat` `roll` `rot` `rshift` `source` `swap` `then` `tuck` `type` `u<` `u>` `unloop` `until` `while` `xor`.

Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро читает каналом `key`), `source` и `>in` — слова только этого пути.
