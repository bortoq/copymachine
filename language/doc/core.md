# Ядро языка (14.8)

Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 954** (определение `:` — 468, переменная — 313, генератор — 71, данные `create` — 62, константа — 24, цифра (литерал) — 10, основание — 6).

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
| 67 | `lay-put` | определение `:` | src/backend.fth:68 | 13 |  |
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
| 87 | `lay-field` | определение `:` | src/backend.fth:107 | 43 |  |
| 88 | `lay-link-row` | основание | src/backend.fth:108 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 89 | `lay-copy` | основание | src/backend.fth:109 | 72 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 90 | `lay-builder` | определение `:` | src/backend.fth:111 | 1 |  |
| 91 | `lay-new-cell` | определение `:` | src/backend.fth:112 | 10 |  |
| 92 | `lay-branch-bit` | определение `:` | src/backend.fth:114 | 20 |  |
| 93 | `lay-branch-step` | определение `:` | src/backend.fth:115 | 3 |  |
| 94 | `lay-group` | определение `:` | src/backend.fth:116 | 5 |  |
| 95 | `lay-layer-cell` | определение `:` | src/backend.fth:119 | 42 |  |
| 96 | `lay-next!` | определение `:` | src/backend.fth:120 | 18 |  |
| 97 | `lay-count` | определение `:` | src/backend.fth:121 | 7 |  |
| 98 | `lay-row-addr` | определение `:` | src/backend.fth:122 | 4 |  |
| 99 | `lay-pending@` | определение `:` | src/backend.fth:123 | 5 |  |
| 100 | `lay-encode-layer` | определение `:` | src/backend.fth:124 | 1 |  |
| 101 | `lay-on-write` | переменная | src/backend.fth:130 | 6 |  |
| 102 | `lay-write` | определение `:` | src/backend.fth:131 | 2 |  |
| 103 | `lay-write-oldest` | определение `:` | src/backend.fth:134 | 1 |  |
| 104 | `lay-new-record` | основание | src/backend.fth:135 | 8 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 105 | `lay-lone` | основание | src/backend.fth:139 | 6 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 106 | `lay-seq` | определение `:` | src/backend.fth:140 | 8 |  |
| 107 | `lay-last` | определение `:` | src/backend.fth:141 | 4 |  |
| 108 | `lay-layer` | основание | src/backend.fth:142 | 82 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 109 | `lay-entry` | определение `:` | src/backend.fth:147 | 3 |  |
| 110 | `lay-jump` | определение `:` | src/backend.fth:148 | 10 |  |
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
| 125 | `lay-row` | основание | src/backend.fth:172 | 78 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 126 | `lay-flush` | определение `:` | src/backend.fth:176 | 13 |  |
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
| 198 | `lay-lookups-begin` | определение `:` | src/compute.fth:17 | 12 |  |
| 199 | `lay-item` | определение `:` | src/compute.fth:18 | 11 |  |
| 200 | `lay-seg` | определение `:` | src/compute.fth:23 | 17 |  |
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
| 214 | `lay-lookups` | определение `:` | src/compute.fth:56 | 12 |  |
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
| 303 | `fc-guard` | переменная | src/forthc.fth:10 | 20 |  |
| 304 | `fc-bbits` | константа | src/forthc.fth:16 | 7 |  |
| 305 | `fc-abits` | константа | src/forthc.fth:16 | 5 |  |
| 306 | `fc-ebits` | константа | src/forthc.fth:16 | 6 |  |
| 307 | `fc-etab` | константа | src/forthc.fth:16 | 5 |  |
| 308 | `fc-rbits` | константа | src/forthc.fth:17 | 5 |  |
| 309 | `fc-rtab` | константа | src/forthc.fth:17 | 4 |  |
| 310 | `fc-layout` | определение `:` | src/forthc.fth:18 | 1 |  |
| 311 | `fc-d+` | определение `:` | src/forthc.fth:20 | 26 |  |
| 312 | `fc-sp` | определение `:` | src/forthc.fth:21 | 4 |  |
| 313 | `fc-rp` | определение `:` | src/forthc.fth:21 | 13 |  |
| 314 | `fc-code` | определение `:` | src/forthc.fth:21 | 1 |  |
| 315 | `fc-regs` | определение `:` | src/forthc.fth:22 | 2 |  |
| 316 | `fc-nregs` | константа | src/forthc.fth:22 | 2 |  |
| 317 | `fc-tmp` | определение `:` | src/forthc.fth:23 | 12 |  |
| 318 | `fc-xr` | определение `:` | src/forthc.fth:23 | 10 |  |
| 319 | `fc-z` | определение `:` | src/forthc.fth:23 | 4 |  |
| 320 | `fc-idx` | определение `:` | src/forthc.fth:23 | 5 |  |
| 321 | `fc-ma` | определение `:` | src/forthc.fth:24 | 6 |  |
| 322 | `fc-mb` | определение `:` | src/forthc.fth:24 | 6 |  |
| 323 | `fc-mp` | определение `:` | src/forthc.fth:24 | 2 |  |
| 324 | `fc-mq` | определение `:` | src/forthc.fth:24 | 3 |  |
| 325 | `fc-mr` | определение `:` | src/forthc.fth:24 | 3 |  |
| 326 | `fc-zero` | определение `:` | src/forthc.fth:25 | 12 |  |
| 327 | `fc-consts` | определение `:` | src/forthc.fth:25 | 3 |  |
| 328 | `fc-sw` | определение `:` | src/forthc.fth:26 | 2 |  |
| 329 | `fc-su` | определение `:` | src/forthc.fth:26 | 1 |  |
| 330 | `fc-key` | определение `:` | src/forthc.fth:26 | 3 |  |
| 331 | `fc-bp` | определение `:` | src/forthc.fth:26 | 2 |  |
| 332 | `fc-tab` | определение `:` | src/forthc.fth:27 | 1 |  |
| 333 | `fc-stk` | определение `:` | src/forthc.fth:27 | 3 |  |
| 334 | `fc-rstk` | определение `:` | src/forthc.fth:28 | 13 |  |
| 335 | `fc-scr0` | определение `:` | src/forthc.fth:28 | 1 |  |
| 336 | `fc-links` | определение `:` | src/forthc.fth:29 | 2 |  |
| 337 | `fc-max-links` | константа | src/forthc.fth:29 | 1 |  |
| 338 | `fc-link-chunk` | константа | src/forthc.fth:29 | 1 |  |
| 339 | `fc-mem` | определение `:` | src/forthc.fth:30 | 7 |  |
| 340 | `fc-mw` | константа | src/forthc.fth:30 | 2 |  |
| 341 | `fc-htab` | определение `:` | src/forthc.fth:30 | 1 |  |
| 342 | `fc-data-start` | константа | src/forthc.fth:31 | 1 |  |
| 343 | `fc-off` | данные `create` | src/forthc.fth:33 | 2 |  |
| 344 | `fc-oc` | переменная | src/forthc.fth:33 | 2 |  |
| 345 | `fc-t-rev8` | переменная | src/forthc.fth:34 | 3 |  |
| 346 | `fc-t-zero32` | переменная | src/forthc.fth:34 | 2 |  |
| 347 | `fc-t-nz2` | переменная | src/forthc.fth:34 | 2 |  |
| 348 | `fc-t-lt32` | переменная | src/forthc.fth:34 | 2 |  |
| 349 | `fc-t-xr2` | переменная | src/forthc.fth:35 | 2 |  |
| 350 | `fc-t-ult32` | переменная | src/forthc.fth:35 | 2 |  |
| 351 | `fc-t-bytepos` | переменная | src/forthc.fth:35 | 2 |  |
| 352 | `fc-off@` | определение `:` | src/forthc.fth:36 | 2 |  |
| 353 | `fc-off-table` | определение `:` | src/forthc.fth:37 | 1 |  |
| 354 | `fc-rev-entry` | определение `:` | src/forthc.fth:40 | 1 |  |
| 355 | `fc-zero-entry` | определение `:` | src/forthc.fth:41 | 1 |  |
| 356 | `fc-nz-entry` | определение `:` | src/forthc.fth:42 | 1 |  |
| 357 | `fc-lt-entry` | определение `:` | src/forthc.fth:43 | 1 |  |
| 358 | `fc-xr2-entry` | определение `:` | src/forthc.fth:46 | 1 |  |
| 359 | `fc-ult-entry` | определение `:` | src/forthc.fth:47 | 1 |  |
| 360 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 361 | `fc-tables` | определение `:` | src/forthc.fth:49 | 1 |  |
| 362 | `fc-mul4-entry` | определение `:` | src/forthc.fth:60 | 1 |  |
| 363 | `fc-qsel-entry` | определение `:` | src/forthc.fth:63 | 1 |  |
| 364 | `fc-max-consts` | переменная | src/forthc.fth:66 | 4 | вход бута (хост) |
| 365 | `fc-ck` | переменная | src/forthc.fth:66 | 3 |  |
| 366 | `fc-nconsts` | переменная | src/forthc.fth:66 | 7 |  |
| 367 | `fc-nbuckets` | переменная | src/forthc.fth:67 | 7 | вход бута (хост) |
| 368 | `fc-cbk` | переменная | src/forthc.fth:67 | 3 |  |
| 369 | `fc-ck@` | определение `:` | src/forthc.fth:68 | 3 |  |
| 370 | `fc-chash` | определение `:` | src/forthc.fth:69 | 1 |  |
| 371 | `fc-cb` | переменная | src/forthc.fth:70 | 3 |  |
| 372 | `fc-const2` | определение `:` | src/forthc.fth:71 | 1 |  |
| 373 | `fc-const` | определение `:` | src/forthc.fth:81 | 4 |  |
| 374 | `fc-lit` | определение `:` | src/forthc.fth:84 | 3 |  |
| 375 | `fc-bit0` | определение `:` | src/forthc.fth:85 | 1 |  |
| 376 | `fc-bit1` | определение `:` | src/forthc.fth:86 | 1 |  |
| 377 | `fc-length` | определение `:` | src/forthc.fth:87 | 1 |  |
| 378 | `fc-lit-of` | определение `:` | src/forthc.fth:88 | 1 |  |
| 379 | `fc-load` | определение `:` | src/forthc.fth:90 | 1 |  |
| 380 | `fc-nlinks` | переменная | src/forthc.fth:92 | 5 |  |
| 381 | `fc-link-buf` | переменная | src/forthc.fth:92 | 4 |  |
| 382 | `fc-nbuf` | переменная | src/forthc.fth:92 | 8 |  |
| 383 | `fc-put-links` | определение `:` | src/forthc.fth:93 | 2 |  |
| 384 | `fc-link-pair` | определение `:` | src/forthc.fth:97 | 2 |  |
| 385 | `fc-link-const` | определение `:` | src/forthc.fth:102 | 1 |  |
| 386 | `fc-eight` | данные `create` | src/forthc.fth:103 | 7 |  |
| 387 | `fc-zeros` | данные `create` | src/forthc.fth:103 | 4 |  |
| 388 | `fc-put-consts` | определение `:` | src/forthc.fth:104 | 1 |  |
| 389 | `fc-cache` | данные `create` | src/forthc.fth:111 | 8 |  |
| 390 | `fc-n` | переменная | src/forthc.fth:111 | 28 |  |
| 391 | `fc-pin` | данные `create` | src/forthc.fth:112 | 10 |  |
| 392 | `fc-npin` | переменная | src/forthc.fth:112 | 19 |  |
| 393 | `fc-c@` | определение `:` | src/forthc.fth:113 | 8 |  |
| 394 | `fc-push` | определение `:` | src/forthc.fth:114 | 28 |  |
| 395 | `fc-pop1` | определение `:` | src/forthc.fth:115 | 30 |  |
| 396 | `fc-in?` | определение `:` | src/forthc.fth:116 | 3 |  |
| 397 | `fc-reg` | определение `:` | src/forthc.fth:117 | 16 |  |
| 398 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:122 | 1 |  |
| 399 | `fc-scr` | переменная | src/forthc.fth:123 | 3 |  |
| 400 | `fc-scratch` | определение `:` | src/forthc.fth:124 | 11 |  |
| 401 | `fc-offs` | данные `create` | src/forthc.fth:127 | 5 |  |
| 402 | `fc-noff` | переменная | src/forthc.fth:127 | 9 |  |
| 403 | `fc-ptr` | переменная | src/forthc.fth:127 | 4 |  |
| 404 | `fc-iw` | переменная | src/forthc.fth:128 | 4 |  |
| 405 | `fc-adjust` | определение `:` | src/forthc.fth:129 | 7 |  |
| 406 | `fc-prow` | данные `create` | src/forthc.fth:135 | 2 |  |
| 407 | `fc-nrow` | переменная | src/forthc.fth:135 | 8 |  |
| 408 | `fc-pl` | данные `create` | src/forthc.fth:136 | 2 |  |
| 409 | `fc-pslot` | данные `create` | src/forthc.fth:136 | 2 |  |
| 410 | `fc-rl` | переменная | src/forthc.fth:137 | 3 |  |
| 411 | `fc-f0` | переменная | src/forthc.fth:137 | 2 |  |
| 412 | `fc-f1` | переменная | src/forthc.fth:137 | 2 |  |
| 413 | `fc-psh` | переменная | src/forthc.fth:137 | 2 |  |
| 414 | `fc-row+` | определение `:` | src/forthc.fth:138 | 3 |  |
| 415 | `fc-4@` | определение `:` | src/forthc.fth:140 | 3 |  |
| 416 | `fc-patched` | определение `:` | src/forthc.fth:141 | 3 |  |
| 417 | `fc-popped` | данные `create` | src/forthc.fth:152 | 2 |  |
| 418 | `fc-srcs` | данные `create` | src/forthc.fth:152 | 13 |  |
| 419 | `fc-nsrc` | переменная | src/forthc.fth:152 | 20 |  |
| 420 | `fc-mbase` | переменная | src/forthc.fth:153 | 8 |  |
| 421 | `fc-mptr` | переменная | src/forthc.fth:153 | 4 |  |
| 422 | `fc-mn` | переменная | src/forthc.fth:153 | 7 |  |
| 423 | `fc-mw2` | переменная | src/forthc.fth:153 | 6 |  |
| 424 | `fc-popped@` | определение `:` | src/forthc.fth:154 | 6 |  |
| 425 | `fc-shift` | определение `:` | src/forthc.fth:155 | 4 |  |
| 426 | `fc-mem-pop` | определение `:` | src/forthc.fth:156 | 3 |  |
| 427 | `fc-push-group` | определение `:` | src/forthc.fth:164 | 2 |  |
| 428 | `fc-dup-at` | определение `:` | src/forthc.fth:170 | 1 |  |
| 429 | `fc-rest` | данные `create` | src/forthc.fth:172 | 2 |  |
| 430 | `fc-nrest` | переменная | src/forthc.fth:172 | 3 |  |
| 431 | `fc-mem-push` | определение `:` | src/forthc.fth:173 | 7 |  |
| 432 | `fc-src1` | определение `:` | src/forthc.fth:179 | 3 |  |
| 433 | `fc-need` | определение `:` | src/forthc.fth:180 | 15 |  |
| 434 | `fc-spill` | определение `:` | src/forthc.fth:186 | 16 |  |
| 435 | `fc-pop` | определение `:` | src/forthc.fth:192 | 11 |  |
| 436 | `fc-max-log` | константа | src/forthc.fth:197 | 1 |  |
| 437 | `fc-max-notes` | константа | src/forthc.fth:197 | 3 |  |
| 438 | `fc-log` | переменная | src/forthc.fth:198 | 3 |  |
| 439 | `fc-nlog` | переменная | src/forthc.fth:198 | 5 |  |
| 440 | `fc-decs` | переменная | src/forthc.fth:198 | 2 |  |
| 441 | `fc-ndec` | переменная | src/forthc.fth:198 | 6 |  |
| 442 | `fc-calls` | переменная | src/forthc.fth:198 | 2 |  |
| 443 | `fc-ncall` | переменная | src/forthc.fth:198 | 6 |  |
| 444 | `fc-pend` | переменная | src/forthc.fth:199 | 2 |  |
| 445 | `fc-npend` | переменная | src/forthc.fth:199 | 9 |  |
| 446 | `fc-unknown` | переменная | src/forthc.fth:199 | 7 |  |
| 447 | `fc-lc` | переменная | src/forthc.fth:200 | 3 |  |
| 448 | `fc-lb` | переменная | src/forthc.fth:200 | 3 |  |
| 449 | `fc-row-n` | определение `:` | src/forthc.fth:201 | 1 |  |
| 450 | `fc-mem-row?` | определение `:` | src/forthc.fth:202 | 1 |  |
| 451 | `fc-log-layer` | определение `:` | src/forthc.fth:203 | 2 |  |
| 452 | `fc-log-begin` | определение `:` | src/forthc.fth:215 | 3 |  |
| 453 | `fc-log-end` | определение `:` | src/forthc.fth:217 | 4 |  |
| 454 | `fc-by-execution` | определение `:` | src/forthc.fth:218 | 7 |  |
| 455 | `fc-dec@` | определение `:` | src/forthc.fth:219 | 2 |  |
| 456 | `fc-call@` | определение `:` | src/forthc.fth:220 | 2 |  |
| 457 | `fc-log-decision` | определение `:` | src/forthc.fth:221 | 2 |  |
| 458 | `fc-log-call` | определение `:` | src/forthc.fth:225 | 2 |  |
| 459 | `fc-callee` | переменная | src/forthc.fth:229 | 4 |  |
| 460 | `fc-live` | переменная | src/forthc.fth:231 | 7 |  |
| 461 | `fc-tramp` | переменная | src/forthc.fth:231 | 6 |  |
| 462 | `fc-ex` | переменная | src/forthc.fth:231 | 4 |  |
| 463 | `fc-halt` | переменная | src/forthc.fth:231 | 3 |  |
| 464 | `fc-jump` | определение `:` | src/forthc.fth:232 | 8 |  |
| 465 | `fc-end` | определение `:` | src/forthc.fth:233 | 12 |  |
| 466 | `fc-begin-block` | определение `:` | src/forthc.fth:234 | 21 |  |
| 467 | `fc-rows1` | определение `:` | src/forthc.fth:238 | 10 |  |
| 468 | `fc-nonzero` | определение `:` | src/forthc.fth:239 | 2 |  |
| 469 | `fc-branch` | определение `:` | src/forthc.fth:242 | 5 |  |
| 470 | `fc-rtab-at` | определение `:` | src/forthc.fth:243 | 1 |  |
| 471 | `fc-nret` | переменная | src/forthc.fth:244 | 6 |  |
| 472 | `fc-ret-link` | определение `:` | src/forthc.fth:248 | 3 |  |
| 473 | `fc-ret-base` | определение `:` | src/forthc.fth:253 | 4 |  |
| 474 | `fc-call` | определение `:` | src/forthc.fth:254 | 4 |  |
| 475 | `fc-v0` | переменная | src/forthc.fth:258 | 4 |  |
| 476 | `fc-v1` | переменная | src/forthc.fth:258 | 4 |  |
| 477 | `fc-jw` | определение `:` | src/forthc.fth:259 | 2 |  |
| 478 | `fc-xw` | определение `:` | src/forthc.fth:260 | 2 |  |
| 479 | `fc-xoff` | определение `:` | src/forthc.fth:261 | 2 |  |
| 480 | `fc-etab-at` | определение `:` | src/forthc.fth:262 | 1 |  |
| 481 | `fc-ex-base` | определение `:` | src/forthc.fth:263 | 1 |  |
| 482 | `fc-call-indirect` | определение `:` | src/forthc.fth:264 | 1 |  |
| 483 | `fc-ret-p` | переменная | src/forthc.fth:271 | 4 |  |
| 484 | `fc-ret-l` | переменная | src/forthc.fth:271 | 6 |  |
| 485 | `fc-rs0` | переменная | src/forthc.fth:271 | 3 |  |
| 486 | `fc-rs1` | переменная | src/forthc.fth:271 | 3 |  |
| 487 | `fc-ret-m` | переменная | src/forthc.fth:271 | 3 |  |
| 488 | `fc-ret-t` | переменная | src/forthc.fth:271 | 3 |  |
| 489 | `fc-ret-patch` | определение `:` | src/forthc.fth:272 | 4 |  |
| 490 | `fc-ret-masked` | определение `:` | src/forthc.fth:274 | 1 |  |
| 491 | `fc-ret` | определение `:` | src/forthc.fth:280 | 3 |  |
| 492 | `fc-ca` | переменная | src/forthc.fth:292 | 3 |  |
| 493 | `fc-cl0` | переменная | src/forthc.fth:292 | 4 |  |
| 494 | `fc-cl1` | переменная | src/forthc.fth:292 | 4 |  |
| 495 | `fc-cr` | переменная | src/forthc.fth:292 | 4 |  |
| 496 | `fc-cslot` | переменная | src/forthc.fth:292 | 3 |  |
| 497 | `fc-csh` | переменная | src/forthc.fth:292 | 2 |  |
| 498 | `fc-cv` | переменная | src/forthc.fth:293 | 3 |  |
| 499 | `fc-cres` | переменная | src/forthc.fth:293 | 6 |  |
| 500 | `fc-cmode` | переменная | src/forthc.fth:293 | 6 |  |
| 501 | `fc-ar` | переменная | src/forthc.fth:293 | 5 |  |
| 502 | `fc-chk-read` | определение `:` | src/forthc.fth:294 | 1 |  |
| 503 | `fc-chk-seg` | определение `:` | src/forthc.fth:296 | 1 |  |
| 504 | `fc-as` | переменная | src/forthc.fth:299 | 2 |  |
| 505 | `fc-af` | переменная | src/forthc.fth:299 | 2 |  |
| 506 | `fc-al0` | переменная | src/forthc.fth:299 | 2 |  |
| 507 | `fc-al1` | переменная | src/forthc.fth:299 | 2 |  |
| 508 | `fc-apl` | переменная | src/forthc.fth:299 | 3 |  |
| 509 | `fc-afld` | переменная | src/forthc.fth:299 | 3 |  |
| 510 | `fc-access-patch` | определение `:` | src/forthc.fth:300 | 2 |  |
| 511 | `fc-access` | определение `:` | src/forthc.fth:305 | 1 |  |
| 512 | `fc-width` | определение `:` | src/forthc.fth:307 | 4 |  |
| 513 | `fc-check` | определение `:` | src/forthc.fth:308 | 4 |  |
| 514 | `fc-ring` | константа | src/forthc.fth:324 | 5 |  |
| 515 | `fc-window` | константа | src/forthc.fth:324 | 1 |  |
| 516 | `fc-sl` | данные `create` | src/forthc.fth:325 | 2 |  |
| 517 | `fc-stabs` | переменная | src/forthc.fth:325 | 2 |  |
| 518 | `fc-slen` | переменная | src/forthc.fth:326 | 7 |  |
| 519 | `fc-slow` | переменная | src/forthc.fth:326 | 4 |  |
| 520 | `fc-sinit` | определение `:` | src/forthc.fth:327 | 2 |  |
| 521 | `fc-sbegin` | определение `:` | src/forthc.fth:328 | 2 |  |
| 522 | `fc-tabs` | определение `:` | src/forthc.fth:329 | 3 |  |
| 523 | `fc-at` | определение `:` | src/forthc.fth:330 | 4 |  |
| 524 | `fc-has?` | определение `:` | src/forthc.fth:335 | 1 |  |
| 525 | `fc-tab+` | определение `:` | src/forthc.fth:336 | 1 |  |
| 526 | `fc-prw` | данные `create` | src/forthc.fth:337 | 6 |  |
| 527 | `fc-ptab` | переменная | src/forthc.fth:337 | 5 |  |
| 528 | `fc-place` | определение `:` | src/forthc.fth:338 | 3 |  |
| 529 | `fc-scopy` | определение `:` | src/forthc.fth:348 | 9 |  |
| 530 | `fc-segs` | данные `create` | src/forthc.fth:349 | 2 |  |
| 531 | `fc-nseg` | переменная | src/forthc.fth:349 | 5 |  |
| 532 | `fc-pp` | данные `create` | src/forthc.fth:350 | 2 |  |
| 533 | `fc-npp` | переменная | src/forthc.fth:350 | 4 |  |
| 534 | `fc-latest` | переменная | src/forthc.fth:350 | 4 |  |
| 535 | `fc-sga` | переменная | src/forthc.fth:350 | 14 |  |
| 536 | `fc-ltab` | переменная | src/forthc.fth:351 | 3 |  |
| 537 | `fc-ls` | переменная | src/forthc.fth:351 | 3 |  |
| 538 | `fc-lw` | переменная | src/forthc.fth:351 | 3 |  |
| 539 | `fc-ldst` | переменная | src/forthc.fth:351 | 2 |  |
| 540 | `fc-seg+` | определение `:` | src/forthc.fth:352 | 21 |  |
| 541 | `fc-pp+` | определение `:` | src/forthc.fth:355 | 1 |  |
| 542 | `fc-slookup` | определение `:` | src/forthc.fth:356 | 8 |  |
| 543 | `fc-nx` | переменная | src/forthc.fth:374 | 3 |  |
| 544 | `fc-nv` | переменная | src/forthc.fth:374 | 2 |  |
| 545 | `fc-nt` | переменная | src/forthc.fth:374 | 3 |  |
| 546 | `fc-negate-chain` | определение `:` | src/forthc.fth:375 | 1 |  |
| 547 | `fc-gw` | переменная | src/forthc.fth:381 | 4 |  |
| 548 | `fc-gs` | переменная | src/forthc.fth:381 | 2 |  |
| 549 | `fc-gs2` | переменная | src/forthc.fth:381 | 2 |  |
| 550 | `fc-gts` | переменная | src/forthc.fth:381 | 6 |  |
| 551 | `fc-gdst` | переменная | src/forthc.fth:381 | 2 |  |
| 552 | `fc-negate-select` | определение `:` | src/forthc.fth:382 | 4 |  |
| 553 | `fc-sfinish` | определение `:` | src/forthc.fth:387 | 2 |  |
| 554 | `fc-pr` | данные `create` | src/forthc.fth:390 | 2 |  |
| 555 | `fc-xs` | данные `create` | src/forthc.fth:390 | 2 |  |
| 556 | `fc-m4` | переменная | src/forthc.fth:391 | 2 |  |
| 557 | `fc-mj` | переменная | src/forthc.fth:391 | 11 |  |
| 558 | `fc-mk` | переменная | src/forthc.fth:391 | 6 |  |
| 559 | `fc-p@` | определение `:` | src/forthc.fth:392 | 3 |  |
| 560 | `fc-p!` | определение `:` | src/forthc.fth:393 | 1 |  |
| 561 | `fc-x@` | определение `:` | src/forthc.fth:394 | 3 |  |
| 562 | `fc-x!` | определение `:` | src/forthc.fth:395 | 2 |  |
| 563 | `fc-build-mul` | определение `:` | src/forthc.fth:396 | 1 |  |
| 564 | `fc-sub` | данные `create` | src/forthc.fth:414 | 2 |  |
| 565 | `fc-qsel` | переменная | src/forthc.fth:414 | 2 |  |
| 566 | `fc-absa` | переменная | src/forthc.fth:415 | 5 |  |
| 567 | `fc-absb` | переменная | src/forthc.fth:415 | 3 |  |
| 568 | `fc-ta` | переменная | src/forthc.fth:415 | 4 |  |
| 569 | `fc-tb` | переменная | src/forthc.fth:415 | 2 |  |
| 570 | `fc-rem` | переменная | src/forthc.fth:416 | 7 |  |
| 571 | `fc-tr` | переменная | src/forthc.fth:416 | 7 |  |
| 572 | `fc-q` | переменная | src/forthc.fth:416 | 3 |  |
| 573 | `fc-tq` | переменная | src/forthc.fth:416 | 4 |  |
| 574 | `fc-k` | переменная | src/forthc.fth:416 | 5 |  |
| 575 | `fc-w` | переменная | src/forthc.fth:417 | 14 |  |
| 576 | `fc-lo` | переменная | src/forthc.fth:417 | 7 |  |
| 577 | `fc-tlo` | переменная | src/forthc.fth:417 | 7 |  |
| 578 | `fc-t0` | переменная | src/forthc.fth:417 | 4 |  |
| 579 | `fc-t1` | переменная | src/forthc.fth:417 | 4 |  |
| 580 | `fc-qr` | переменная | src/forthc.fth:417 | 4 |  |
| 581 | `fc-tqk` | переменная | src/forthc.fth:417 | 3 |  |
| 582 | `fc-sub@` | определение `:` | src/forthc.fth:418 | 7 |  |
| 583 | `fc-step` | определение `:` | src/forthc.fth:419 | 3 |  |
| 584 | `fc-div-step` | определение `:` | src/forthc.fth:426 | 1 |  |
| 585 | `fc-build-div` | определение `:` | src/forthc.fth:443 | 1 |  |
| 586 | `fc-mul-entry` | переменная | src/forthc.fth:459 | 4 |  |
| 587 | `fc-mul-exit` | переменная | src/forthc.fth:459 | 2 |  |
| 588 | `fc-div-entry` | переменная | src/forthc.fth:459 | 5 |  |
| 589 | `fc-div-exit` | переменная | src/forthc.fth:459 | 4 |  |
| 590 | `fc-hl` | переменная | src/forthc.fth:460 | 5 |  |
| 591 | `fc-hcont` | переменная | src/forthc.fth:460 | 4 |  |
| 592 | `fc-mul-cost` | данные `create` | src/forthc.fth:461 | 2 |  |
| 593 | `fc-div-cost` | данные `create` | src/forthc.fth:461 | 2 |  |
| 594 | `fc-row-or-new` | определение `:` | src/forthc.fth:462 | 2 |  |
| 595 | `fc-call-helper` | определение `:` | src/forthc.fth:464 | 4 |  |
| 596 | `fc-result1` | определение `:` | src/forthc.fth:474 | 3 |  |
| 597 | `fc-s1` | переменная | src/forthc.fth:475 | 2 |  |
| 598 | `fc-s2` | переменная | src/forthc.fth:475 | 2 |  |
| 599 | `fc-r1` | переменная | src/forthc.fth:475 | 2 |  |
| 600 | `fc-result2` | определение `:` | src/forthc.fth:476 | 1 |  |
| 601 | `fc-forbid` | константа | src/forthc.fth:484 | 2 |  |
| 602 | `fc-pexit` | переменная | src/forthc.fth:485 | 2 |  |
| 603 | `fc-ptramp` | переменная | src/forthc.fth:485 | 2 |  |
| 604 | `fc-pd` | переменная | src/forthc.fth:485 | 5 |  |
| 605 | `fc-pc` | переменная | src/forthc.fth:485 | 5 |  |
| 606 | `fc-ends` | переменная | src/forthc.fth:485 | 3 |  |
| 607 | `fc-pb` | переменная | src/forthc.fth:486 | 5 |  |
| 608 | `fc-pcp` | переменная | src/forthc.fth:486 | 5 |  |
| 609 | `fc-pln` | переменная | src/forthc.fth:486 | 5 |  |
| 610 | `fc-pk` | переменная | src/forthc.fth:486 | 4 |  |
| 611 | `fc-pcall` | переменная | src/forthc.fth:486 | 3 |  |
| 612 | `fc-best` | данные `create` | src/forthc.fth:487 | 10 |  |
| 613 | `fc-pend@` | определение `:` | src/forthc.fth:488 | 7 |  |
| 614 | `fc-reach` | определение `:` | src/forthc.fth:489 | 2 |  |
| 615 | `fc-take` | определение `:` | src/forthc.fth:498 | 1 |  |
| 616 | `fc-end-path` | определение `:` | src/forthc.fth:505 | 2 |  |
| 617 | `fc-to` | определение `:` | src/forthc.fth:509 | 2 |  |
| 618 | `fc-node` | определение `:` | src/forthc.fth:513 | 1 |  |
| 619 | `fc-path` | определение `:` | src/forthc.fth:532 | 3 |  |
| 620 | `fc-cost!` | определение `:` | src/forthc.fth:541 | 4 |  |
| 621 | `fc-ll` | переменная | src/forthc.fth:543 | 6 |  |
| 622 | `fc-llr` | переменная | src/forthc.fth:543 | 3 |  |
| 623 | `fc-llv` | переменная | src/forthc.fth:543 | 3 |  |
| 624 | `fc-plit` | переменная | src/forthc.fth:543 | 6 |  |
| 625 | `fc-plr` | переменная | src/forthc.fth:543 | 4 |  |
| 626 | `fc-plv` | переменная | src/forthc.fth:543 | 6 |  |
| 627 | `fc-literal` | определение `:` | src/forthc.fth:544 | 14 |  |
| 628 | `fc-or-zero` | определение `:` | src/forthc.fth:546 | 2 |  |
| 629 | `fc-ba` | переменная | src/forthc.fth:549 | 13 |  |
| 630 | `fc-bb` | переменная | src/forthc.fth:549 | 13 |  |
| 631 | `fc-br` | переменная | src/forthc.fth:549 | 9 |  |
| 632 | `fc-binary` | определение `:` | src/forthc.fth:550 | 10 |  |
| 633 | `fc-r-at` | определение `:` | src/forthc.fth:574 | 2 |  |
| 634 | `fc-pop-pinned` | определение `:` | src/forthc.fth:577 | 3 |  |
| 635 | `fc-sk` | переменная | src/forthc.fth:578 | 12 |  |
| 636 | `fc-shift-copy` | определение `:` | src/forthc.fth:579 | 2 |  |
| 637 | `fc-inc` | определение `:` | src/forthc.fth:583 | 3 |  |
| 638 | `fc-read-key` | определение `:` | src/forthc.fth:586 | 1 |  |
| 639 | `fc-text-mem` | данные `create` | src/forthc.fth:591 | 1 |  |
| 640 | `fc-text` | переменная | src/forthc.fth:592 | 13 |  |
| 641 | `fc-tlen` | переменная | src/forthc.fth:592 | 14 |  |
| 642 | `fc-pos` | переменная | src/forthc.fth:592 | 24 |  |
| 643 | `fc-text-size` | переменная | src/forthc.fth:592 | 5 | вход бута (хост) |
| 644 | `fc-reset` | определение `:` | src/forthc.fth:593 | 3 |  |
| 645 | `fc-append` | определение `:` | src/forthc.fth:594 | 1 |  |
| 646 | `fc\|` | определение `:` | src/forthc.fth:598 | 1 | вход бута (хост) |
| 647 | `fc-ch` | определение `:` | src/forthc.fth:599 | 5 |  |
| 648 | `fc-more?` | определение `:` | src/forthc.fth:600 | 6 |  |
| 649 | `fc-next` | определение `:` | src/forthc.fth:601 | 8 |  |
| 650 | `fc-next!` | определение `:` | src/forthc.fth:609 | 10 |  |
| 651 | `fc-is?` | определение `:` | src/forthc.fth:610 | 5 |  |
| 652 | `fc-raw` | определение `:` | src/forthc.fth:613 | 1 |  |
| 653 | `fc-string-token` | определение `:` | src/forthc.fth:614 | 1 |  |
| 654 | `fc-names-size` | переменная | src/forthc.fth:619 | 4 | вход бута (хост) |
| 655 | `fc-max-words` | переменная | src/forthc.fth:619 | 4 | вход бута (хост) |
| 656 | `fc-names` | переменная | src/forthc.fth:620 | 3 |  |
| 657 | `fc-names-used` | переменная | src/forthc.fth:620 | 5 |  |
| 658 | `fc-wt` | переменная | src/forthc.fth:621 | 5 |  |
| 659 | `fc-nwords` | переменная | src/forthc.fth:621 | 12 |  |
| 660 | `fc-wbk` | переменная | src/forthc.fth:621 | 3 |  |
| 661 | `fc-wt@` | определение `:` | src/forthc.fth:624 | 6 |  |
| 662 | `fc-proved` | данные `create` | src/forthc.fth:626 | 2 |  |
| 663 | `fc-unproved` | данные `create` | src/forthc.fth:627 | 2 |  |
| 664 | `fc-mechanisms` | определение `:` | src/forthc.fth:628 | 1 |  |
| 665 | `fc-xt` | определение `:` | src/forthc.fth:633 | 5 |  |
| 666 | `fc-xtn` | определение `:` | src/forthc.fth:635 | 2 |  |
| 667 | `fc-hash` | определение `:` | src/forthc.fth:636 | 2 |  |
| 668 | `fc-define` | определение `:` | src/forthc.fth:638 | 6 |  |
| 669 | `fc-lookup` | определение `:` | src/forthc.fth:643 | 6 |  |
| 670 | `fc-find` | определение `:` | src/forthc.fth:647 | 6 |  |
| 671 | `fc-word-of` | определение `:` | src/forthc.fth:649 | 2 |  |
| 672 | `fc-cost` | определение `:` | src/forthc.fth:657 | 1 |  |
| 673 | `fc-proved?` | определение `:` | src/forthc.fth:660 | 1 |  |
| 674 | `fc-here` | переменная | src/forthc.fth:662 | 9 |  |
| 675 | `fc-word` | переменная | src/forthc.fth:662 | 13 |  |
| 676 | `fc-uses` | переменная | src/forthc.fth:662 | 16 |  |
| 677 | `fc-rt` | переменная | src/forthc.fth:663 | 7 |  |
| 678 | `fc-rta` | переменная | src/forthc.fth:663 | 7 |  |
| 679 | `fc-ctl` | данные `create` | src/forthc.fth:664 | 1 |  |
| 680 | `fc-nctl` | переменная | src/forthc.fth:664 | 12 |  |
| 681 | `fc-cleave` | переменная | src/forthc.fth:664 | 2 |  |
| 682 | `fc-ctl@` | определение `:` | src/forthc.fth:665 | 4 |  |
| 683 | `fc-ctl+` | определение `:` | src/forthc.fth:666 | 6 |  |
| 684 | `fc-ctl-` | определение `:` | src/forthc.fth:668 | 7 |  |
| 685 | `fc-do-entry` | определение `:` | src/forthc.fth:670 | 1 |  |
| 686 | `fc-ctl-leave` | определение `:` | src/forthc.fth:672 | 1 |  |
| 687 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:673 | 1 |  |
| 688 | `fc-loop-leave` | определение `:` | src/forthc.fth:674 | 1 |  |
| 689 | `fc-align` | определение `:` | src/forthc.fth:675 | 2 |  |
| 690 | `fc-check-here` | определение `:` | src/forthc.fth:676 | 3 |  |
| 691 | `fc-define-data` | определение `:` | src/forthc.fth:677 | 2 |  |
| 692 | `fc-sat` | переменная | src/forthc.fth:678 | 3 |  |
| 693 | `fc-store-string` | определение `:` | src/forthc.fth:679 | 1 |  |
| 694 | `fc-ct` | данные `create` | src/forthc.fth:684 | 3 |  |
| 695 | `fc-nct` | переменная | src/forthc.fth:684 | 11 |  |
| 696 | `fc-ct+` | определение `:` | src/forthc.fth:685 | 18 |  |
| 697 | `fc-ct-` | определение `:` | src/forthc.fth:686 | 9 |  |
| 698 | `fc-ct2` | определение `:` | src/forthc.fth:687 | 8 |  |
| 699 | `fc-inits` | данные `create` | src/forthc.fth:688 | 2 |  |
| 700 | `fc-ninit` | переменная | src/forthc.fth:688 | 5 |  |
| 701 | `fc-init-open` | переменная | src/forthc.fth:688 | 6 |  |
| 702 | `fc-ck-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 703 | `fc-stabs-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 704 | `fc-cbk-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 705 | `fc-link-mem` | данные `create` | src/forthc.fth:692 | 1 |  |
| 706 | `fc-wt-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 707 | `fc-names-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 708 | `fc-wbk-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 709 | `fc-log-mem` | данные `create` | src/forthc.fth:693 | 1 |  |
| 710 | `fc-decs-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 711 | `fc-calls-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 712 | `fc-pend-mem` | данные `create` | src/forthc.fth:694 | 1 |  |
| 713 | `fc-init` | определение `:` | src/forthc.fth:695 | 1 |  |
| 714 | `fc-scan-uses` | определение `:` | src/forthc.fth:709 | 1 |  |
| 715 | `fc-const-shift` | определение `:` | src/forthc.fth:716 | 2 |  |
| 716 | `fc-lit?` | определение `:` | src/forthc.fth:725 | 3 |  |
| 717 | `fc-mul-lit?` | определение `:` | src/forthc.fth:727 | 1 |  |
| 718 | `fc-shift-lit?` | определение `:` | src/forthc.fth:732 | 2 |  |
| 719 | `fc-pick-roll` | определение `:` | src/forthc.fth:735 | 2 |  |
| 720 | `fc-stx` | переменная | src/forthc.fth:744 | 3 |  |
| 721 | `fc-stlo` | переменная | src/forthc.fth:744 | 8 |  |
| 722 | `fc-sthi` | переменная | src/forthc.fth:744 | 4 |  |
| 723 | `fc-stp` | переменная | src/forthc.fth:744 | 6 |  |
| 724 | `fc-strow` | переменная | src/forthc.fth:744 | 8 |  |
| 725 | `fc-stm` | переменная | src/forthc.fth:744 | 5 |  |
| 726 | `fc-ftr` | переменная | src/forthc.fth:745 | 5 |  |
| 727 | `fc-stg` | переменная | src/forthc.fth:745 | 2 |  |
| 728 | `fc-sw0` | определение `:` | src/forthc.fth:746 | 2 |  |
| 729 | `fc-sw1` | определение `:` | src/forthc.fth:747 | 2 |  |
| 730 | `fc-sbase` | определение `:` | src/forthc.fth:748 | 2 |  |
| 731 | `fc-space-end` | определение `:` | src/forthc.fth:749 | 2 |  |
| 732 | `fc-space-store` | определение `:` | src/forthc.fth:757 | 2 |  |
| 733 | `fc-space-fetch` | определение `:` | src/forthc.fth:764 | 2 |  |
| 734 | `fc-cp` | определение `:` | src/forthc.fth:775 | 4 |  |
| 735 | `fc-copy-row` | определение `:` | src/forthc.fth:777 | 1 |  |
| 736 | `fc-close-init` | определение `:` | src/forthc.fth:780 | 2 |  |
| 737 | `fc-open-init` | определение `:` | src/forthc.fth:783 | 1 |  |
| 738 | `fc-gens` | переменная | src/forthc.fth:794 | 3 |  |
| 739 | `fc-generator` | определение `:` | src/forthc.fth:795 | 86 |  |
| 740 | `fc-literal-name` | определение `:` | src/forthc.fth:797 | 10 |  |
| 741 | `fc-words` | определение `:` | src/forthc.fth:799 | 1 |  |
| 742 | `fc-known` | определение `:` | src/forthc.fth:808 | 1 |  |
| 743 | `fc-defining?` | определение `:` | src/forthc.fth:810 | 7 |  |
| 744 | `fc-code` | определение `:` | src/forthc.fth:811 | 50 | вариант 2 |
| 745 | `fc-fold?` | определение `:` | src/forthc.fth:813 | 13 |  |
| 746 | `fc-top-only` | определение `:` | src/forthc.fth:814 | 6 |  |
| 747 | `fc-not-found` | определение `:` | src/forthc.fth:816 | 1 |  |
| 748 | `fc-word-token` | определение `:` | src/forthc.fth:818 | 2 |  |
| 749 | `fc-token` | определение `:` | src/forthc.fth:823 | 2 |  |
| 750 | `fc-synonym-of` | определение `:` | src/forthc.fth:824 | 2 |  |
| 751 | `fc-synonym` | определение `:` | src/forthc.fth:825 | 10 |  |
| 752 | `fc-sy` | переменная | src/forthc.fth:828 | 2 |  |
| 753 | `fc-synonym?` | определение `:` | src/forthc.fth:829 | 1 |  |
| 754 | `fc-poke` | определение `:` | src/forthc.fth:832 | 2 |  |
| 755 | `fc-concept-record` | определение `:` | src/forthc.fth:835 | 1 |  |
| 756 | `fc-eval` | определение `:` | src/forthc.fth:840 | 59 |  |
| 757 | `fc-concepts` | определение `:` | src/forthc.fth:844 | 1 |  |
| 758 | `fc-nhost` | переменная | src/forthc.fth:851 | 5 |  |
| 759 | `fc-platform` | определение `:` | src/forthc.fth:852 | 1 |  |
| 760 | `fc-time-price` | определение `:` | src/forthc.fth:875 | 1 |  |
| 761 | `fc-replacement` | определение `:` | src/forthc.fth:885 | 1 |  |
| 762 | `fc-library` | определение `:` | src/forthc.fth:900 | 1 |  |
| 763 | `fc-forbidden` | определение `:` | src/forthc.fth:925 | 2 |  |
| 764 | `fc-long` | определение `:` | src/forthc.fth:926 | 1 |  |
| 765 | `fc-helpers-cost` | определение `:` | src/forthc.fth:935 | 1 |  |
| 766 | `fc-price-word` | определение `:` | src/forthc.fth:942 | 1 |  |
| 767 | `fc-compile` | определение `:` | src/forthc.fth:945 | 1 |  |
| 768 | `fc-go` | определение `:` | src/forthc.fth:961 | 3 | вход бута (хост) |
| 769 | `gen+` | определение `:` | src/primitives.fth:4 | 5 |  |
| 770 | `gen-` | определение `:` | src/primitives.fth:5 | 2 |  |
| 771 | `gen-and` | определение `:` | src/primitives.fth:6 | 2 |  |
| 772 | `gen-or` | определение `:` | src/primitives.fth:7 | 2 |  |
| 773 | `gen-xor` | определение `:` | src/primitives.fth:8 | 2 |  |
| 774 | `gen=` | определение `:` | src/primitives.fth:9 | 2 |  |
| 775 | `gen<` | определение `:` | src/primitives.fth:10 | 2 |  |
| 776 | `gen-u<` | определение `:` | src/primitives.fth:11 | 2 |  |
| 777 | `gen-lshift` | определение `:` | src/primitives.fth:12 | 2 |  |
| 778 | `gen-rshift` | определение `:` | src/primitives.fth:14 | 2 |  |
| 779 | `gen-0=` | определение `:` | src/primitives.fth:16 | 2 |  |
| 780 | `gen-cells` | определение `:` | src/primitives.fth:17 | 2 |  |
| 781 | `gen-2*` | определение `:` | src/primitives.fth:18 | 2 |  |
| 782 | `gen-1+` | определение `:` | src/primitives.fth:19 | 2 |  |
| 783 | `gen-1-` | определение `:` | src/primitives.fth:20 | 2 |  |
| 784 | `gen-cell+` | определение `:` | src/primitives.fth:21 | 2 |  |
| 785 | `gen*` | определение `:` | src/primitives.fth:22 | 2 |  |
| 786 | `gen/` | определение `:` | src/primitives.fth:25 | 2 |  |
| 787 | `gen-mod` | определение `:` | src/primitives.fth:26 | 2 |  |
| 788 | `gen/mod` | определение `:` | src/primitives.fth:27 | 2 |  |
| 789 | `gen-dup` | определение `:` | src/primitives.fth:28 | 2 |  |
| 790 | `gen-drop` | определение `:` | src/primitives.fth:29 | 2 |  |
| 791 | `gen-swap` | определение `:` | src/primitives.fth:30 | 2 |  |
| 792 | `gen-over` | определение `:` | src/primitives.fth:31 | 2 |  |
| 793 | `gen-rot` | определение `:` | src/primitives.fth:32 | 2 |  |
| 794 | `gen-pick` | определение `:` | src/primitives.fth:33 | 2 |  |
| 795 | `gen-roll` | определение `:` | src/primitives.fth:34 | 2 |  |
| 796 | `gen->r` | определение `:` | src/primitives.fth:35 | 2 |  |
| 797 | `gen-r>` | определение `:` | src/primitives.fth:36 | 2 |  |
| 798 | `gen-r@` | определение `:` | src/primitives.fth:37 | 4 |  |
| 799 | `gen-j` | определение `:` | src/primitives.fth:38 | 2 |  |
| 800 | `gen-@` | определение `:` | src/primitives.fth:39 | 2 |  |
| 801 | `gen-!` | определение `:` | src/primitives.fth:41 | 2 |  |
| 802 | `gen-c@` | определение `:` | src/primitives.fth:42 | 2 |  |
| 803 | `gen-c!` | определение `:` | src/primitives.fth:44 | 2 |  |
| 804 | `gen-emit` | определение `:` | src/primitives.fth:45 | 2 |  |
| 805 | `gen-key` | определение `:` | src/primitives.fth:48 | 2 |  |
| 806 | `gen-if` | определение `:` | src/primitives.fth:50 | 2 |  |
| 807 | `gen-else` | определение `:` | src/primitives.fth:51 | 2 |  |
| 808 | `gen-then` | определение `:` | src/primitives.fth:53 | 2 |  |
| 809 | `gen-begin` | определение `:` | src/primitives.fth:57 | 2 |  |
| 810 | `gen-until` | определение `:` | src/primitives.fth:58 | 2 |  |
| 811 | `gen-while` | определение `:` | src/primitives.fth:60 | 2 |  |
| 812 | `gen-repeat` | определение `:` | src/primitives.fth:61 | 2 |  |
| 813 | `gen-again` | определение `:` | src/primitives.fth:62 | 2 |  |
| 814 | `gen-do` | определение `:` | src/primitives.fth:63 | 2 |  |
| 815 | `fc-di` | переменная | src/primitives.fth:66 | 3 |  |
| 816 | `fc-dl` | переменная | src/primitives.fth:66 | 3 |  |
| 817 | `gen-?do` | определение `:` | src/primitives.fth:67 | 2 |  |
| 818 | `fc-lv` | переменная | src/primitives.fth:73 | 2 |  |
| 819 | `gen-loop` | определение `:` | src/primitives.fth:74 | 2 |  |
| 820 | `gen-leave` | определение `:` | src/primitives.fth:83 | 2 |  |
| 821 | `gen-unloop` | определение `:` | src/primitives.fth:86 | 2 |  |
| 822 | `gen-exit` | определение `:` | src/primitives.fth:87 | 2 |  |
| 823 | `gen-bye` | определение `:` | src/primitives.fth:90 | 2 |  |
| 824 | `gen-recurse` | определение `:` | src/primitives.fth:92 | 2 |  |
| 825 | `gen-tick` | определение `:` | src/primitives.fth:93 | 2 |  |
| 826 | `gen-call` | определение `:` | src/primitives.fth:99 | 3 |  |
| 827 | `gen-space!` | определение `:` | src/primitives.fth:100 | 2 |  |
| 828 | `gen-spacec!` | определение `:` | src/primitives.fth:101 | 2 |  |
| 829 | `gen-space@` | определение `:` | src/primitives.fth:102 | 2 |  |
| 830 | `gen-spacec@` | определение `:` | src/primitives.fth:103 | 2 |  |
| 831 | `gen-execute` | определение `:` | src/primitives.fth:104 | 2 |  |
| 832 | `fc-entry-cell` | определение `:` | src/primitives.fth:110 | 1 |  |
| 833 | `fc-concept` | определение `:` | src/primitives.fth:112 | 1 |  |
| 834 | `gen-colon` | определение `:` | src/primitives.fth:119 | 2 |  |
| 835 | `gen-semicolon` | определение `:` | src/primitives.fth:125 | 2 |  |
| 836 | `gen-variable` | определение `:` | src/primitives.fth:128 | 2 |  |
| 837 | `gen-create` | определение `:` | src/primitives.fth:129 | 2 |  |
| 838 | `gen-allot` | определение `:` | src/primitives.fth:130 | 2 |  |
| 839 | `gen-constant` | определение `:` | src/primitives.fth:131 | 2 |  |
| 840 | `gen-decimal` | определение `:` | src/primitives.fth:132 | 2 |  |
| 841 | `gen-kernel-layout` | определение `:` | src/primitives.fth:133 | 2 |  |
| 842 | `gen-backslash` | определение `:` | src/primitives.fth:134 | 2 |  |
| 843 | `gen-paren` | определение `:` | src/primitives.fth:136 | 4 |  |
| 844 | `gen-char` | определение `:` | src/primitives.fth:137 | 2 |  |
| 845 | `gen-string` | определение `:` | src/primitives.fth:138 | 2 |  |
| 846 | `fc-digit@` | определение `:` | src/primitives.fth:141 | 1 |  |
| 847 | `gen-literal` | определение `:` | src/primitives.fth:143 | 2 |  |
| 848 | `fc-known-xt` | определение `:` | src/primitives.fth:150 | 2 |  |
| 849 | `gen-cost` | определение `:` | src/primitives.fth:151 | 2 |  |
| 850 | `gen-proved?` | определение `:` | src/primitives.fth:153 | 2 |  |
| 851 | `gen-library` | определение `:` | src/primitives.fth:154 | 16 |  |
| 852 | `gen-price` | определение `:` | src/primitives.fth:155 | 2 |  |
| 853 | `fc-cpos` | переменная | src/primitives.fth:160 | 4 |  |
| 854 | `fc-hn` | переменная | src/primitives.fth:160 | 2 |  |
| 855 | `fc-cdepth` | переменная | src/primitives.fth:160 | 4 |  |
| 856 | `fc-hname` | данные `create` | src/primitives.fth:160 | 2 |  |
| 857 | `fc-hb` | определение `:` | src/primitives.fth:161 | 3 |  |
| 858 | `fc-c,` | определение `:` | src/primitives.fth:162 | 17 |  |
| 859 | `fc-c1` | определение `:` | src/primitives.fth:163 | 8 |  |
| 860 | `fc-c-gen` | определение `:` | src/primitives.fth:164 | 1 |  |
| 861 | `fc-c-body` | определение `:` | src/primitives.fth:168 | 1 |  |
| 862 | `gen-host` | определение `:` | src/primitives.fth:177 | 2 |  |
| 863 | `fc-name2` | определение `:` | src/primitives.fth:194 | 1 |  |
| 864 | `fc-generators` | определение `:` | src/primitives.fth:197 | 1 |  |
| 865 | `+` | генератор | src/primitives.fth:198 | 558 | слово компилятора `gen+` |
| 866 | `-` | генератор | src/primitives.fth:198 | 63 | слово компилятора `gen-` |
| 867 | `*` | генератор | src/primitives.fth:199 | 80 | слово компилятора `gen*` |
| 868 | `/` | генератор | src/primitives.fth:199 | 4 | слово компилятора `gen/` |
| 869 | `mod` | генератор | src/primitives.fth:200 | 2 | слово компилятора `gen-mod` |
| 870 | `and` | генератор | src/primitives.fth:201 | 117 | слово компилятора `gen-and` |
| 871 | `or` | генератор | src/primitives.fth:201 | 43 | слово компилятора `gen-or` |
| 872 | `xor` | генератор | src/primitives.fth:202 | 5 | слово компилятора `gen-xor` |
| 873 | `lshift` | генератор | src/primitives.fth:202 | 98 | слово компилятора `gen-lshift` |
| 874 | `rshift` | генератор | src/primitives.fth:203 | 62 | слово компилятора `gen-rshift` |
| 875 | `=` | генератор | src/primitives.fth:203 | 81 | слово компилятора `gen=` |
| 876 | `<` | генератор | src/primitives.fth:204 | 24 | слово компилятора `gen<` |
| 877 | `u<` | генератор | src/primitives.fth:204 | 26 | слово компилятора `gen-u<` |
| 878 | `0=` | генератор | src/primitives.fth:205 | 102 | слово компилятора `gen-0=` |
| 879 | `2*` | генератор | src/primitives.fth:205 | 29 | слово компилятора `gen-2*` |
| 880 | `1+` | генератор | src/primitives.fth:206 | 44 | слово компилятора `gen-1+` |
| 881 | `1-` | генератор | src/primitives.fth:206 | 55 | слово компилятора `gen-1-` |
| 882 | `cells` | генератор | src/primitives.fth:207 | 273 | слово компилятора `gen-cells` |
| 883 | `cell+` | генератор | src/primitives.fth:207 | 56 | слово компилятора `gen-cell+` |
| 884 | `dup` | генератор | src/primitives.fth:208 | 299 | слово компилятора `gen-dup` |
| 885 | `drop` | генератор | src/primitives.fth:208 | 197 | слово компилятора `gen-drop` |
| 886 | `swap` | генератор | src/primitives.fth:209 | 139 | слово компилятора `gen-swap` |
| 887 | `over` | генератор | src/primitives.fth:209 | 86 | слово компилятора `gen-over` |
| 888 | `rot` | генератор | src/primitives.fth:210 | 37 | слово компилятора `gen-rot` |
| 889 | `pick` | генератор | src/primitives.fth:210 | 43 | слово компилятора `gen-pick` |
| 890 | `roll` | генератор | src/primitives.fth:211 | 7 | слово компилятора `gen-roll` |
| 891 | `>r` | генератор | src/primitives.fth:211 | 106 | слово компилятора `gen->r` |
| 892 | `r>` | генератор | src/primitives.fth:212 | 110 | слово компилятора `gen-r>` |
| 893 | `r@` | генератор | src/primitives.fth:212 | 107 | слово компилятора `gen-r@` |
| 894 | `i` | генератор | src/primitives.fth:213 | 172 | слово компилятора `gen-r@` |
| 895 | `j` | генератор | src/primitives.fth:213 | 12 | слово компилятора `gen-j` |
| 896 | `@` | генератор | src/primitives.fth:214 | 1245 | слово компилятора `gen-@` |
| 897 | `!` | генератор | src/primitives.fth:214 | 652 | слово компилятора `gen-!` |
| 898 | `c@` | генератор | src/primitives.fth:215 | 23 | слово компилятора `gen-c@` |
| 899 | `c!` | генератор | src/primitives.fth:215 | 18 | слово компилятора `gen-c!` |
| 900 | `space!` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-space!` |
| 901 | `spacec!` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-spacec!` |
| 902 | `space@` | генератор | src/primitives.fth:217 | 1 | слово компилятора `gen-space@` |
| 903 | `emit` | генератор | src/primitives.fth:218 | 4 | слово компилятора `gen-emit` |
| 904 | `key` | генератор | src/primitives.fth:218 | 1 | слово компилятора `gen-key` |
| 905 | `if` | генератор | src/primitives.fth:219 | 301 | слово компилятора `gen-if` |
| 906 | `else` | генератор | src/primitives.fth:219 | 82 | слово компилятора `gen-else` |
| 907 | `then` | генератор | src/primitives.fth:220 | 301 | слово компилятора `gen-then` |
| 908 | `begin` | генератор | src/primitives.fth:220 | 25 | слово компилятора `gen-begin` |
| 909 | `until` | генератор | src/primitives.fth:221 | 2 | слово компилятора `gen-until` |
| 910 | `while` | генератор | src/primitives.fth:221 | 22 | слово компилятора `gen-while` |
| 911 | `repeat` | генератор | src/primitives.fth:222 | 22 | слово компилятора `gen-repeat` |
| 912 | `again` | генератор | src/primitives.fth:222 | 1 | слово компилятора `gen-again` |
| 913 | `do` | генератор | src/primitives.fth:223 | 31 | слово компилятора `gen-do` |
| 914 | `?do` | генератор | src/primitives.fth:223 | 58 | слово компилятора `gen-?do` |
| 915 | `loop` | генератор | src/primitives.fth:224 | 89 | слово компилятора `gen-loop` |
| 916 | `leave` | генератор | src/primitives.fth:224 | 1 | слово компилятора `gen-leave` |
| 917 | `unloop` | генератор | src/primitives.fth:225 | 7 | слово компилятора `gen-unloop` |
| 918 | `exit` | генератор | src/primitives.fth:225 | 81 | слово компилятора `gen-exit` |
| 919 | `bye` | генератор | src/primitives.fth:226 | 1 | слово компилятора `gen-bye` |
| 920 | `recurse` | генератор | src/primitives.fth:227 | 2 | слово компилятора `gen-recurse` |
| 921 | `execute` | генератор | src/primitives.fth:227 | 10 | слово компилятора `gen-execute` |
| 922 | `[']` | генератор | src/primitives.fth:228 | 117 | слово компилятора `gen-tick` |
| 923 | `:` | генератор | src/primitives.fth:229 | 487 | слово компилятора `gen-colon` |
| 924 | `;` | генератор | src/primitives.fth:229 | 487 | слово компилятора `gen-semicolon` |
| 925 | `variable` | генератор | src/primitives.fth:230 | 320 | слово компилятора `gen-variable` |
| 926 | `create` | генератор | src/primitives.fth:230 | 62 | слово компилятора `gen-create` |
| 927 | `allot` | генератор | src/primitives.fth:231 | 62 | слово компилятора `gen-allot` |
| 928 | `constant` | генератор | src/primitives.fth:231 | 24 | слово компилятора `gen-constant` |
| 929 | `decimal` | генератор | src/primitives.fth:232 | 3 | слово компилятора `gen-decimal` |
| 930 | `kernel-layout` | генератор | src/primitives.fth:232 | 1 | слово компилятора `gen-kernel-layout` |
| 931 | `\` | генератор | src/primitives.fth:233 | 152 | слово компилятора `gen-backslash` |
| 932 | `(` | генератор | src/primitives.fth:233 | 467 | слово компилятора `gen-paren` |
| 933 | `[char]` | генератор | src/primitives.fth:233 | 8 | слово компилятора `gen-char` |
| 934 | `s"` | генератор | src/primitives.fth:234 | 204 | слово компилятора `gen-string` |
| 935 | `literal` | генератор | src/primitives.fth:235 | 492 | слово компилятора `gen-literal` |
| 936 | `0` | цифра (литерал) | src/primitives.fth:243 | 540 | значение 0 |
| 937 | `1` | цифра (литерал) | src/primitives.fth:243 | 465 | значение 1 |
| 938 | `2` | цифра (литерал) | src/primitives.fth:243 | 446 | значение 2 |
| 939 | `3` | цифра (литерал) | src/primitives.fth:243 | 295 | значение 3 |
| 940 | `4` | цифра (литерал) | src/primitives.fth:244 | 237 | значение 4 |
| 941 | `5` | цифра (литерал) | src/primitives.fth:244 | 103 | значение 5 |
| 942 | `6` | цифра (литерал) | src/primitives.fth:244 | 155 | значение 6 |
| 943 | `7` | цифра (литерал) | src/primitives.fth:244 | 66 | значение 7 |
| 944 | `8` | цифра (литерал) | src/primitives.fth:245 | 157 | значение 8 |
| 945 | `9` | цифра (литерал) | src/primitives.fth:245 | 43 | значение 9 |
| 946 | `fc-install-generators` | определение `:` | src/primitives.fth:246 | 1 |  |
| 947 | `fc-read` | определение `:` | src/main.fth:3 | 2 |  |
| 948 | `fc-sizes` | определение `:` | src/main.fth:8 | 2 |  |
| 949 | `kn-at` | переменная | src/kernel.fth:7 | 5 |  |
| 950 | `kn-put` | определение `:` | src/kernel.fth:8 | 1 |  |
| 951 | `kn-order` | определение `:` | src/kernel.fth:16 | 1 |  |
| 952 | `kn-get` | определение `:` | src/kernel.fth:18 | 1 |  |
| 953 | `kn-compile` | определение `:` | src/kernel.fth:19 | 1 |  |
| 954 | `main` | определение `:` | src/kernel.fth:25 | 1 | вариант 2 |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 93.

## Определены, но не использованы

Слов: 34. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

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
