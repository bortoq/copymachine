# Ядро языка (14.8)

Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 940** (определение `:` — 471, переменная — 312, генератор — 72, данные `create` — 47, константа — 22, цифра (литерал) — 10, основание — 6).

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
| 36 | `lay-size` | переменная | src/backend.fth:8 | 13 |  |
| 37 | `lay-a` | переменная | src/backend.fth:8 | 19 |  |
| 38 | `lay-slots` | переменная | src/backend.fth:8 | 16 |  |
| 39 | `lay-cell-bits` | переменная | src/backend.fth:8 | 15 |  |
| 40 | `lay-chunk` | переменная | src/backend.fth:9 | 8 |  |
| 41 | `lay-chunk-buf` | переменная | src/backend.fth:9 | 6 |  |
| 42 | `lay-lbuf` | переменная | src/backend.fth:9 | 6 |  |
| 43 | `lay-pool` | переменная | src/backend.fth:9 | 5 |  |
| 44 | `lay-ebuf` | переменная | src/backend.fth:10 | 4 |  |
| 45 | `lay-dest` | переменная | src/backend.fth:10 | 6 |  |
| 46 | `lay-sink` | переменная | src/backend.fth:10 | 5 |  |
| 47 | `lay-start-cell` | переменная | src/backend.fth:10 | 3 |  |
| 48 | `lay-rev` | данные `create` | src/backend.fth:12 | 10 |  |
| 49 | `lay-rev-init` | определение `:` | src/backend.fth:13 | 1 |  |
| 50 | `lay-inst` | определение `:` | src/backend.fth:17 | 10 |  |
| 51 | `lay-layer-bits` | определение `:` | src/backend.fth:18 | 8 |  |
| 52 | `lay-lbytes` | определение `:` | src/backend.fth:19 | 6 |  |
| 53 | `lay-stdin` | определение `:` | src/backend.fth:20 | 4 |  |
| 54 | `lay-stdout` | определение `:` | src/backend.fth:21 | 3 |  |
| 55 | `lay-bits` | определение `:` | src/backend.fth:22 | 7 |  |
| 56 | `lay-numeric` | определение `:` | src/backend.fth:23 | 7 |  |
| 57 | `lay-numeric4` | определение `:` | src/backend.fth:28 | 1 |  |
| 58 | `lay-field-check` | определение `:` | src/backend.fth:31 | 1 |  |
| 59 | `lay-encode` | определение `:` | src/backend.fth:33 | 3 |  |
| 60 | `lay-start` | переменная | src/backend.fth:43 | 8 |  |
| 61 | `lay-len` | переменная | src/backend.fth:43 | 10 |  |
| 62 | `lay-rows` | данные `create` | src/backend.fth:44 | 6 |  |
| 63 | `lay-row!` | определение `:` | src/backend.fth:45 | 7 |  |
| 64 | `lay-clear-rows` | определение `:` | src/backend.fth:47 | 3 |  |
| 65 | `lay-loader` | определение `:` | src/backend.fth:48 | 1 |  |
| 66 | `lay-stream-flush` | определение `:` | src/backend.fth:55 | 3 |  |
| 67 | `lay-begin-chunk` | определение `:` | src/backend.fth:59 | 2 |  |
| 68 | `lay-put` | определение `:` | src/backend.fth:61 | 14 |  |
| 69 | `lay-scratch` | данные `create` | src/backend.fth:79 | 2 |  |
| 70 | `lay-put-numeric` | определение `:` | src/backend.fth:80 | 3 |  |
| 71 | `lay-max-layers` | константа | src/backend.fth:84 | 4 |  |
| 72 | `lay-record` | определение `:` | src/backend.fth:85 | 2 |  |
| 73 | `lay-pending` | переменная | src/backend.fth:86 | 10 |  |
| 74 | `lay-head` | переменная | src/backend.fth:86 | 6 |  |
| 75 | `lay-next-cell` | переменная | src/backend.fth:86 | 8 |  |
| 76 | `lay-seq#` | переменная | src/backend.fth:87 | 8 |  |
| 77 | `lay-seq-first` | переменная | src/backend.fth:87 | 3 |  |
| 78 | `lay-seq-entry` | переменная | src/backend.fth:87 | 2 |  |
| 79 | `lay-seq-last` | переменная | src/backend.fth:87 | 2 |  |
| 80 | `lay-foff` | данные `create` | src/backend.fth:88 | 2 |  |
| 81 | `lay-foff-init` | определение `:` | src/backend.fth:89 | 1 |  |
| 82 | `lay-machine` | определение `:` | src/backend.fth:90 | 1 |  |
| 83 | `lay-field` | определение `:` | src/backend.fth:107 | 44 |  |
| 84 | `lay-link-row` | основание | src/backend.fth:108 | 2 | основание: строка: копирование ссылки на следующий слой; определение инструкции — она сама |
| 85 | `lay-copy` | основание | src/backend.fth:109 | 80 | основание: строка: копирование n бит из источника в приёмник; определение инструкции — она сама |
| 86 | `lay-builder` | определение `:` | src/backend.fth:111 | 1 |  |
| 87 | `lay-new-cell` | определение `:` | src/backend.fth:112 | 13 |  |
| 88 | `lay-branch-bit` | определение `:` | src/backend.fth:114 | 16 |  |
| 89 | `lay-branch-step` | определение `:` | src/backend.fth:115 | 3 |  |
| 90 | `lay-group` | определение `:` | src/backend.fth:116 | 5 |  |
| 91 | `lay-layer-cell` | определение `:` | src/backend.fth:119 | 40 |  |
| 92 | `lay-next!` | определение `:` | src/backend.fth:120 | 18 |  |
| 93 | `lay-count` | определение `:` | src/backend.fth:121 | 7 |  |
| 94 | `lay-row-addr` | определение `:` | src/backend.fth:122 | 4 |  |
| 95 | `lay-pending@` | определение `:` | src/backend.fth:123 | 5 |  |
| 96 | `lay-encode-layer` | определение `:` | src/backend.fth:124 | 1 |  |
| 97 | `lay-on-write` | переменная | src/backend.fth:130 | 6 |  |
| 98 | `lay-write` | определение `:` | src/backend.fth:131 | 2 |  |
| 99 | `lay-write-oldest` | определение `:` | src/backend.fth:134 | 1 |  |
| 100 | `lay-new-record` | основание | src/backend.fth:135 | 9 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 101 | `lay-lone` | основание | src/backend.fth:139 | 5 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 102 | `lay-seq` | определение `:` | src/backend.fth:140 | 9 |  |
| 103 | `lay-last` | определение `:` | src/backend.fth:141 | 4 |  |
| 104 | `lay-layer` | основание | src/backend.fth:142 | 82 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
| 105 | `lay-entry` | определение `:` | src/backend.fth:147 | 4 |  |
| 106 | `lay-jump` | определение `:` | src/backend.fth:148 | 13 |  |
| 107 | `lay-l1` | переменная | src/backend.fth:149 | 4 |  |
| 108 | `lay-h1` | переменная | src/backend.fth:149 | 3 |  |
| 109 | `lay-l2` | переменная | src/backend.fth:149 | 4 |  |
| 110 | `lay-h2` | переменная | src/backend.fth:149 | 3 |  |
| 111 | `lay-ra` | переменная | src/backend.fth:150 | 2 |  |
| 112 | `lay-rb` | переменная | src/backend.fth:150 | 2 |  |
| 113 | `lay-cur` | переменная | src/backend.fth:150 | 7 |  |
| 114 | `lay-clash?` | определение `:` | src/backend.fth:152 | 1 |  |
| 115 | `lay-row-clash?` | определение `:` | src/backend.fth:157 | 1 |  |
| 116 | `lay-new-row` | данные `create` | src/backend.fth:162 | 6 |  |
| 117 | `lay-row-set` | определение `:` | src/backend.fth:163 | 2 |  |
| 118 | `lay-full?` | определение `:` | src/backend.fth:165 | 2 |  |
| 119 | `lay-clashes?` | определение `:` | src/backend.fth:166 | 2 |  |
| 120 | `lay-fits?` | определение `:` | src/backend.fth:170 | 2 |  |
| 121 | `lay-row` | основание | src/backend.fth:172 | 81 | основание: строка: добавляет строку в слой; определение инструкции — она сама |
| 122 | `lay-flush` | определение `:` | src/backend.fth:176 | 14 |  |
| 123 | `lay-finish` | определение `:` | src/backend.fth:179 | 1 |  |
| 124 | `dj-reader` | переменная | src/backend.fth:194 | 3 |  |
| 125 | `dj-bad-cell` | переменная | src/backend.fth:194 | 1 |  |
| 126 | `dj-bad-rule` | переменная | src/backend.fth:194 | 4 |  |
| 127 | `dj-bsh` | переменная | src/backend.fth:195 | 3 |  |
| 128 | `dj-csh` | переменная | src/backend.fth:195 | 6 |  |
| 129 | `dj-ssh` | переменная | src/backend.fth:195 | 2 |  |
| 130 | `dj-fsh` | переменная | src/backend.fth:195 | 2 |  |
| 131 | `dj-first` | переменная | src/backend.fth:196 | 2 |  |
| 132 | `dj-end` | переменная | src/backend.fth:196 | 2 |  |
| 133 | `dj-pa` | переменная | src/backend.fth:196 | 3 |  |
| 134 | `dj-cb` | переменная | src/backend.fth:196 | 8 |  |
| 135 | `dj-vdl` | переменная | src/backend.fth:197 | 16 |  |
| 136 | `dj-vdh` | переменная | src/backend.fth:197 | 12 |  |
| 137 | `dj-vsl` | переменная | src/backend.fth:197 | 14 |  |
| 138 | `dj-vsh` | переменная | src/backend.fth:197 | 12 |  |
| 139 | `dj-tc` | переменная | src/backend.fth:198 | 5 |  |
| 140 | `dj-ts` | переменная | src/backend.fth:198 | 6 |  |
| 141 | `dj-tf` | переменная | src/backend.fth:198 | 5 |  |
| 142 | `dj-tb` | переменная | src/backend.fth:198 | 2 |  |
| 143 | `dj-tn` | переменная | src/backend.fth:198 | 2 |  |
| 144 | `dj-tk` | переменная | src/backend.fth:198 | 7 |  |
| 145 | `dj-vt` | переменная | src/backend.fth:198 | 3 |  |
| 146 | `dj-blk` | переменная | src/backend.fth:199 | 5 |  |
| 147 | `dj-pr` | данные `create` | src/backend.fth:200 | 2 |  |
| 148 | `dj-tr` | данные `create` | src/backend.fth:200 | 3 |  |
| 149 | `dj-narrow` | константа | src/backend.fth:201 | 1 |  |
| 150 | `dj-seen` | данные `create` | src/backend.fth:202 | 2 |  |
| 151 | `dj-nseen` | переменная | src/backend.fth:202 | 6 |  |
| 152 | `dj-get` | определение `:` | src/backend.fth:203 | 9 |  |
| 153 | `dj-fail` | определение `:` | src/backend.fth:204 | 6 |  |
| 154 | `dj-blk?` | определение `:` | src/backend.fth:205 | 5 |  |
| 155 | `dj-in?` | определение `:` | src/backend.fth:206 | 4 |  |
| 156 | `dj-row!` | определение `:` | src/backend.fth:209 | 2 |  |
| 157 | `dj-row@` | определение `:` | src/backend.fth:211 | 3 |  |
| 158 | `dj-nop?` | определение `:` | src/backend.fth:213 | 4 |  |
| 159 | `dj-load` | определение `:` | src/backend.fth:214 | 1 |  |
| 160 | `dj-row-ok?` | определение `:` | src/backend.fth:222 | 1 |  |
| 161 | `dj-in-blk?` | определение `:` | src/backend.fth:227 | 2 |  |
| 162 | `dj-touches?` | определение `:` | src/backend.fth:231 | 1 |  |
| 163 | `dj-seen?` | определение `:` | src/backend.fth:232 | 1 |  |
| 164 | `dj-seen!` | определение `:` | src/backend.fth:237 | 1 |  |
| 165 | `dj-wide` | определение `:` | src/backend.fth:241 | 1 |  |
| 166 | `dj-patch` | определение `:` | src/backend.fth:257 | 1 |  |
| 167 | `dj-nn` | переменная | src/backend.fth:267 | 4 |  |
| 168 | `dj-lo` | переменная | src/backend.fth:267 | 2 |  |
| 169 | `dj-hi` | переменная | src/backend.fth:267 | 2 |  |
| 170 | `dj-scan` | определение `:` | src/backend.fth:268 | 1 |  |
| 171 | `dj-rows` | определение `:` | src/backend.fth:277 | 1 |  |
| 172 | `dj-prove` | определение `:` | src/backend.fth:284 | 2 |  |
| 173 | `lay-t1` | переменная | src/compute.fth:7 | 25 |  |
| 174 | `lay-t2` | переменная | src/compute.fth:7 | 13 |  |
| 175 | `lay-t3` | переменная | src/compute.fth:7 | 7 |  |
| 176 | `lay-t4` | переменная | src/compute.fth:7 | 4 |  |
| 177 | `lay-t5` | переменная | src/compute.fth:7 | 8 |  |
| 178 | `lay-lo` | переменная | src/compute.fth:8 | 5 |  |
| 179 | `lay-hi` | переменная | src/compute.fth:8 | 2 |  |
| 180 | `lay-l0` | переменная | src/compute.fth:9 | 21 |  |
| 181 | `lay-l1` | переменная | src/compute.fth:9 | 13 | вариант 2 |
| 182 | `lay-l2` | переменная | src/compute.fth:9 | 8 | вариант 2 |
| 183 | `lay-l3` | переменная | src/compute.fth:9 | 7 |  |
| 184 | `lay-l4` | переменная | src/compute.fth:9 | 7 |  |
| 185 | `lay-l5` | переменная | src/compute.fth:9 | 6 |  |
| 186 | `lay-work` | определение `:` | src/compute.fth:10 | 3 |  |
| 187 | `lay-cell-bit` | определение `:` | src/compute.fth:11 | 2 |  |
| 188 | `lay-link-slot` | определение `:` | src/compute.fth:12 | 6 |  |
| 189 | `lay-item-cells` | константа | src/compute.fth:13 | 1 |  |
| 190 | `lay-max-items` | константа | src/compute.fth:13 | 2 |  |
| 191 | `lay-items` | данные `create` | src/compute.fth:14 | 1 |  |
| 192 | `lay-nitems` | переменная | src/compute.fth:15 | 8 |  |
| 193 | `lay-item@` | определение `:` | src/compute.fth:16 | 6 |  |
| 194 | `lay-lookups-begin` | определение `:` | src/compute.fth:17 | 14 |  |
| 195 | `lay-item` | определение `:` | src/compute.fth:18 | 12 |  |
| 196 | `lay-seg` | определение `:` | src/compute.fth:23 | 18 |  |
| 197 | `lay-sl` | данные `create` | src/compute.fth:29 | 2 |  |
| 198 | `lay-sh` | данные `create` | src/compute.fth:29 | 2 |  |
| 199 | `lay-read-layer` | данные `create` | src/compute.fth:30 | 2 |  |
| 200 | `lay-read-slot` | данные `create` | src/compute.fth:30 | 2 |  |
| 201 | `lay-used` | данные `create` | src/compute.fth:31 | 2 |  |
| 202 | `lay-nused` | переменная | src/compute.fth:31 | 5 |  |
| 203 | `lay-rl` | переменная | src/compute.fth:31 | 6 |  |
| 204 | `lay-pk` | переменная | src/compute.fth:31 | 4 |  |
| 205 | `lay-pkl` | переменная | src/compute.fth:31 | 4 |  |
| 206 | `lay-npatches` | определение `:` | src/compute.fth:32 | 1 |  |
| 207 | `lay-used?` | определение `:` | src/compute.fth:33 | 1 |  |
| 208 | `lay-place-reads` | определение `:` | src/compute.fth:35 | 1 |  |
| 209 | `lay-patch` | определение `:` | src/compute.fth:47 | 1 |  |
| 210 | `lay-lookups` | определение `:` | src/compute.fth:56 | 14 |  |
| 211 | `lay-al` | данные `create` | src/compute.fth:62 | 2 |  |
| 212 | `lay-ar` | данные `create` | src/compute.fth:62 | 2 |  |
| 213 | `lay-ax` | переменная | src/compute.fth:63 | 4 |  |
| 214 | `lay-aa` | переменная | src/compute.fth:63 | 2 |  |
| 215 | `lay-ab` | переменная | src/compute.fth:63 | 2 |  |
| 216 | `lay-atab` | переменная | src/compute.fth:63 | 2 |  |
| 217 | `lay-acarry` | переменная | src/compute.fth:63 | 2 |  |
| 218 | `lay-al@` | определение `:` | src/compute.fth:64 | 8 |  |
| 219 | `lay-rd` | определение `:` | src/compute.fth:65 | 3 |  |
| 220 | `lay-adder-patch` | определение `:` | src/compute.fth:66 | 4 |  |
| 221 | `lay-adder` | определение `:` | src/compute.fth:71 | 6 |  |
| 222 | `lay-dsrc` | переменная | src/compute.fth:87 | 3 |  |
| 223 | `lay-dk` | переменная | src/compute.fth:87 | 5 |  |
| 224 | `lay-dg` | переменная | src/compute.fth:87 | 3 |  |
| 225 | `lay-dp` | переменная | src/compute.fth:87 | 3 |  |
| 226 | `lay-dx` | переменная | src/compute.fth:87 | 4 |  |
| 227 | `lay-decide` | определение `:` | src/compute.fth:88 | 2 |  |
| 228 | `lay-table-at` | переменная | src/compute.fth:95 | 4 |  |
| 229 | `lay-table-limit` | переменная | src/compute.fth:95 | 2 |  |
| 230 | `lay-tbuf` | переменная | src/compute.fth:95 | 7 |  |
| 231 | `lay-tx` | переменная | src/compute.fth:96 | 5 |  |
| 232 | `lay-tbits` | переменная | src/compute.fth:96 | 4 |  |
| 233 | `lay-ts` | переменная | src/compute.fth:96 | 6 |  |
| 234 | `lay-tsize` | переменная | src/compute.fth:96 | 7 |  |
| 235 | `lay-tbase` | переменная | src/compute.fth:96 | 4 |  |
| 236 | `lay-tper` | переменная | src/compute.fth:96 | 3 |  |
| 237 | `lay-tables` | определение `:` | src/compute.fth:97 | 2 |  |
| 238 | `lay-table-area` | определение `:` | src/compute.fth:98 | 2 |  |
| 239 | `lay-table-done` | определение `:` | src/compute.fth:106 | 2 |  |
| 240 | `lay-table` | определение `:` | src/compute.fth:108 | 23 |  |
| 241 | `lay-add-entry` | определение `:` | src/compute.fth:125 | 1 |  |
| 242 | `lay-sub-entry` | определение `:` | src/compute.fth:127 | 2 |  |
| 243 | `lay-xor-entry` | определение `:` | src/compute.fth:129 | 1 |  |
| 244 | `lay-or-entry` | определение `:` | src/compute.fth:130 | 1 |  |
| 245 | `lay-and-entry` | определение `:` | src/compute.fth:131 | 1 |  |
| 246 | `lay-or8-entry` | определение `:` | src/compute.fth:132 | 1 |  |
| 247 | `lay-fz` | переменная | src/compute.fth:133 | 3 |  |
| 248 | `lay-fu` | переменная | src/compute.fth:133 | 4 |  |
| 249 | `lay-fs` | переменная | src/compute.fth:133 | 3 |  |
| 250 | `lay-pair` | определение `:` | src/compute.fth:134 | 6 |  |
| 251 | `lay-flags-entry` | определение `:` | src/compute.fth:135 | 1 |  |
| 252 | `lay-not5-entry` | определение `:` | src/compute.fth:142 | 1 |  |
| 253 | `lay-sign-entry` | определение `:` | src/compute.fth:143 | 1 |  |
| 254 | `lay-fill24-entry` | определение `:` | src/compute.fth:144 | 1 |  |
| 255 | `lay-fill16-entry` | определение `:` | src/compute.fth:145 | 1 |  |
| 256 | `lay-inc1-entry` | определение `:` | src/compute.fth:146 | 1 |  |
| 257 | `lay-inc2-entry` | определение `:` | src/compute.fth:147 | 1 |  |
| 258 | `lay-t-add` | переменная | src/compute.fth:148 | 7 |  |
| 259 | `lay-t-sub` | переменная | src/compute.fth:148 | 5 |  |
| 260 | `lay-t-xor` | переменная | src/compute.fth:148 | 5 |  |
| 261 | `lay-t-or` | переменная | src/compute.fth:148 | 2 |  |
| 262 | `lay-t-and` | переменная | src/compute.fth:148 | 2 |  |
| 263 | `lay-t-or8` | переменная | src/compute.fth:149 | 2 |  |
| 264 | `lay-t-flags` | переменная | src/compute.fth:149 | 2 |  |
| 265 | `lay-t-not5` | переменная | src/compute.fth:149 | 2 |  |
| 266 | `lay-t-sign32` | переменная | src/compute.fth:149 | 2 |  |
| 267 | `lay-t-fill24` | переменная | src/compute.fth:150 | 1 |  |
| 268 | `lay-t-fill16` | переменная | src/compute.fth:150 | 1 |  |
| 269 | `lay-t-inc1` | переменная | src/compute.fth:150 | 1 |  |
| 270 | `lay-t-inc2` | переменная | src/compute.fth:150 | 1 |  |
| 271 | `lay-standard-tables` | определение `:` | src/compute.fth:151 | 1 |  |
| 272 | `lay-oo` | переменная | src/compute.fth:159 | 2 |  |
| 273 | `lay-os` | переменная | src/compute.fth:159 | 2 |  |
| 274 | `lay-ol` | переменная | src/compute.fth:159 | 4 |  |
| 275 | `lay-oh` | переменная | src/compute.fth:159 | 3 |  |
| 276 | `lay-or-chunks` | определение `:` | src/compute.fth:160 | 3 |  |
| 277 | `lay-cr` | переменная | src/compute.fth:166 | 5 |  |
| 278 | `lay-ca` | переменная | src/compute.fth:166 | 4 |  |
| 279 | `lay-cb` | переменная | src/compute.fth:166 | 4 |  |
| 280 | `lay-logic` | определение `:` | src/compute.fth:173 | 4 |  |
| 281 | `lay-sres` | переменная | src/compute.fth:179 | 3 |  |
| 282 | `lay-sa` | переменная | src/compute.fth:179 | 7 |  |
| 283 | `lay-samt` | переменная | src/compute.fth:179 | 8 |  |
| 284 | `lay-sw` | переменная | src/compute.fth:179 | 9 |  |
| 285 | `lay-szero` | переменная | src/compute.fth:179 | 4 |  |
| 286 | `lay-sarg` | переменная | src/compute.fth:180 | 6 |  |
| 287 | `lay-sign` | переменная | src/compute.fth:180 | 6 |  |
| 288 | `lay-shift-row` | определение `:` | src/compute.fth:181 | 3 |  |
| 289 | `lay-shift-patch` | определение `:` | src/compute.fth:182 | 6 |  |
| 290 | `lay-shift-right` | определение `:` | src/compute.fth:184 | 1 |  |
| 291 | `lay-shift-left` | определение `:` | src/compute.fth:201 | 1 |  |
| 292 | `fc-size` | константа | src/forthc.fth:6 | 2 |  |
| 293 | `fc-cellb` | константа | src/forthc.fth:6 | 7 |  |
| 294 | `fc-l` | константа | src/forthc.fth:6 | 1 |  |
| 295 | `fc-a` | константа | src/forthc.fth:6 | 2 |  |
| 296 | `fc-d` | переменная | src/forthc.fth:8 | 3 |  |
| 297 | `fc-first` | переменная | src/forthc.fth:8 | 3 |  |
| 298 | `fc-guard` | переменная | src/forthc.fth:10 | 18 |  |
| 299 | `fc-bbits` | константа | src/forthc.fth:14 | 11 |  |
| 300 | `fc-abits` | константа | src/forthc.fth:14 | 5 |  |
| 301 | `fc-ebits` | константа | src/forthc.fth:14 | 2 |  |
| 302 | `fc-etab` | константа | src/forthc.fth:14 | 3 |  |
| 303 | `fc-layout` | определение `:` | src/forthc.fth:15 | 1 |  |
| 304 | `fc-d+` | определение `:` | src/forthc.fth:17 | 27 |  |
| 305 | `fc-sp` | определение `:` | src/forthc.fth:18 | 6 |  |
| 306 | `fc-rp` | определение `:` | src/forthc.fth:18 | 18 |  |
| 307 | `fc-handler` | определение `:` | src/forthc.fth:18 | 6 |  |
| 308 | `fc-code` | определение `:` | src/forthc.fth:18 | 4 |  |
| 309 | `fc-regs` | определение `:` | src/forthc.fth:19 | 2 |  |
| 310 | `fc-nregs` | константа | src/forthc.fth:19 | 2 |  |
| 311 | `fc-tmp` | определение `:` | src/forthc.fth:20 | 12 |  |
| 312 | `fc-xr` | определение `:` | src/forthc.fth:20 | 10 |  |
| 313 | `fc-z` | определение `:` | src/forthc.fth:20 | 4 |  |
| 314 | `fc-idx` | определение `:` | src/forthc.fth:20 | 5 |  |
| 315 | `fc-ma` | определение `:` | src/forthc.fth:21 | 6 |  |
| 316 | `fc-mb` | определение `:` | src/forthc.fth:21 | 6 |  |
| 317 | `fc-mp` | определение `:` | src/forthc.fth:21 | 2 |  |
| 318 | `fc-mq` | определение `:` | src/forthc.fth:21 | 3 |  |
| 319 | `fc-mr` | определение `:` | src/forthc.fth:21 | 3 |  |
| 320 | `fc-zero` | определение `:` | src/forthc.fth:22 | 12 |  |
| 321 | `fc-consts` | определение `:` | src/forthc.fth:22 | 3 |  |
| 322 | `fc-sw` | определение `:` | src/forthc.fth:23 | 2 |  |
| 323 | `fc-su` | определение `:` | src/forthc.fth:23 | 1 |  |
| 324 | `fc-key` | определение `:` | src/forthc.fth:23 | 3 |  |
| 325 | `fc-bp` | определение `:` | src/forthc.fth:23 | 2 |  |
| 326 | `fc-tab` | определение `:` | src/forthc.fth:24 | 1 |  |
| 327 | `fc-stk` | определение `:` | src/forthc.fth:24 | 3 |  |
| 328 | `fc-rstk` | определение `:` | src/forthc.fth:25 | 16 |  |
| 329 | `fc-scr0` | определение `:` | src/forthc.fth:25 | 1 |  |
| 330 | `fc-links` | определение `:` | src/forthc.fth:26 | 2 |  |
| 331 | `fc-max-links` | константа | src/forthc.fth:26 | 1 |  |
| 332 | `fc-link-chunk` | константа | src/forthc.fth:26 | 2 |  |
| 333 | `fc-mem` | определение `:` | src/forthc.fth:27 | 7 |  |
| 334 | `fc-mw` | константа | src/forthc.fth:27 | 2 |  |
| 335 | `fc-htab` | определение `:` | src/forthc.fth:27 | 1 |  |
| 336 | `fc-data-start` | константа | src/forthc.fth:28 | 1 |  |
| 337 | `fc-off` | данные `create` | src/forthc.fth:30 | 2 |  |
| 338 | `fc-oc` | переменная | src/forthc.fth:30 | 2 |  |
| 339 | `fc-t-rev8` | переменная | src/forthc.fth:31 | 3 |  |
| 340 | `fc-t-zero32` | переменная | src/forthc.fth:31 | 2 |  |
| 341 | `fc-t-nz2` | переменная | src/forthc.fth:31 | 2 |  |
| 342 | `fc-t-lt32` | переменная | src/forthc.fth:31 | 2 |  |
| 343 | `fc-t-xr2` | переменная | src/forthc.fth:32 | 2 |  |
| 344 | `fc-t-ult32` | переменная | src/forthc.fth:32 | 2 |  |
| 345 | `fc-t-bytepos` | переменная | src/forthc.fth:32 | 2 |  |
| 346 | `fc-off@` | определение `:` | src/forthc.fth:33 | 3 |  |
| 347 | `fc-off-table` | определение `:` | src/forthc.fth:34 | 1 |  |
| 348 | `fc-rev-entry` | определение `:` | src/forthc.fth:37 | 1 |  |
| 349 | `fc-zero-entry` | определение `:` | src/forthc.fth:38 | 1 |  |
| 350 | `fc-nz-entry` | определение `:` | src/forthc.fth:39 | 1 |  |
| 351 | `fc-lt-entry` | определение `:` | src/forthc.fth:40 | 1 |  |
| 352 | `fc-xr2-entry` | определение `:` | src/forthc.fth:43 | 1 |  |
| 353 | `fc-ult-entry` | определение `:` | src/forthc.fth:44 | 1 |  |
| 354 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:45 | 1 |  |
| 355 | `fc-tables` | определение `:` | src/forthc.fth:46 | 1 |  |
| 356 | `fc-mul4-entry` | определение `:` | src/forthc.fth:57 | 1 |  |
| 357 | `fc-qsel-entry` | определение `:` | src/forthc.fth:60 | 1 |  |
| 358 | `fc-max-consts` | переменная | src/forthc.fth:63 | 5 | вход бута (хост) |
| 359 | `fc-ck` | переменная | src/forthc.fth:63 | 3 |  |
| 360 | `fc-nconsts` | переменная | src/forthc.fth:63 | 7 |  |
| 361 | `fc-nbuckets` | переменная | src/forthc.fth:64 | 9 | вход бута (хост) |
| 362 | `fc-cbk` | переменная | src/forthc.fth:64 | 3 |  |
| 363 | `fc-ck@` | определение `:` | src/forthc.fth:65 | 3 |  |
| 364 | `fc-chash` | определение `:` | src/forthc.fth:66 | 1 |  |
| 365 | `fc-cb` | переменная | src/forthc.fth:67 | 3 |  |
| 366 | `fc-const2` | определение `:` | src/forthc.fth:68 | 1 |  |
| 367 | `fc-const` | определение `:` | src/forthc.fth:78 | 5 |  |
| 368 | `fc-lit` | определение `:` | src/forthc.fth:81 | 3 |  |
| 369 | `fc-bit0` | определение `:` | src/forthc.fth:82 | 1 |  |
| 370 | `fc-bit1` | определение `:` | src/forthc.fth:83 | 1 |  |
| 371 | `fc-length` | определение `:` | src/forthc.fth:84 | 1 |  |
| 372 | `fc-lit-of` | определение `:` | src/forthc.fth:85 | 2 |  |
| 373 | `fc-load` | определение `:` | src/forthc.fth:87 | 2 |  |
| 374 | `fc-nlinks` | переменная | src/forthc.fth:89 | 5 |  |
| 375 | `fc-link-buf` | переменная | src/forthc.fth:89 | 4 |  |
| 376 | `fc-nbuf` | переменная | src/forthc.fth:89 | 8 |  |
| 377 | `fc-put-links` | определение `:` | src/forthc.fth:90 | 2 |  |
| 378 | `fc-link-const` | определение `:` | src/forthc.fth:94 | 4 |  |
| 379 | `fc-eight` | данные `create` | src/forthc.fth:99 | 7 |  |
| 380 | `fc-zeros` | данные `create` | src/forthc.fth:99 | 5 |  |
| 381 | `fc-put-consts` | определение `:` | src/forthc.fth:100 | 1 |  |
| 382 | `fc-cache` | данные `create` | src/forthc.fth:107 | 8 |  |
| 383 | `fc-n` | переменная | src/forthc.fth:107 | 31 |  |
| 384 | `fc-pin` | данные `create` | src/forthc.fth:108 | 10 |  |
| 385 | `fc-npin` | переменная | src/forthc.fth:108 | 21 |  |
| 386 | `fc-c@` | определение `:` | src/forthc.fth:109 | 8 |  |
| 387 | `fc-push` | определение `:` | src/forthc.fth:110 | 30 |  |
| 388 | `fc-pop1` | определение `:` | src/forthc.fth:111 | 30 |  |
| 389 | `fc-in?` | определение `:` | src/forthc.fth:112 | 3 |  |
| 390 | `fc-reg` | определение `:` | src/forthc.fth:113 | 18 |  |
| 391 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:118 | 1 |  |
| 392 | `fc-scr` | переменная | src/forthc.fth:119 | 3 |  |
| 393 | `fc-scratch` | определение `:` | src/forthc.fth:120 | 11 |  |
| 394 | `fc-offs` | данные `create` | src/forthc.fth:123 | 5 |  |
| 395 | `fc-noff` | переменная | src/forthc.fth:123 | 9 |  |
| 396 | `fc-ptr` | переменная | src/forthc.fth:123 | 4 |  |
| 397 | `fc-iw` | переменная | src/forthc.fth:124 | 4 |  |
| 398 | `fc-adjust` | определение `:` | src/forthc.fth:125 | 7 |  |
| 399 | `fc-prow` | данные `create` | src/forthc.fth:131 | 2 |  |
| 400 | `fc-nrow` | переменная | src/forthc.fth:131 | 8 |  |
| 401 | `fc-pl` | данные `create` | src/forthc.fth:132 | 2 |  |
| 402 | `fc-pslot` | данные `create` | src/forthc.fth:132 | 2 |  |
| 403 | `fc-rl` | переменная | src/forthc.fth:133 | 3 |  |
| 404 | `fc-f0` | переменная | src/forthc.fth:133 | 2 |  |
| 405 | `fc-f1` | переменная | src/forthc.fth:133 | 2 |  |
| 406 | `fc-psh` | переменная | src/forthc.fth:133 | 2 |  |
| 407 | `fc-row+` | определение `:` | src/forthc.fth:134 | 3 |  |
| 408 | `fc-4@` | определение `:` | src/forthc.fth:136 | 3 |  |
| 409 | `fc-patched` | определение `:` | src/forthc.fth:137 | 3 |  |
| 410 | `fc-popped` | данные `create` | src/forthc.fth:148 | 2 |  |
| 411 | `fc-srcs` | данные `create` | src/forthc.fth:148 | 16 |  |
| 412 | `fc-nsrc` | переменная | src/forthc.fth:148 | 21 |  |
| 413 | `fc-mbase` | переменная | src/forthc.fth:149 | 8 |  |
| 414 | `fc-mptr` | переменная | src/forthc.fth:149 | 4 |  |
| 415 | `fc-mn` | переменная | src/forthc.fth:149 | 7 |  |
| 416 | `fc-mw2` | переменная | src/forthc.fth:149 | 6 |  |
| 417 | `fc-popped@` | определение `:` | src/forthc.fth:150 | 10 |  |
| 418 | `fc-shift` | определение `:` | src/forthc.fth:151 | 4 |  |
| 419 | `fc-mem-pop` | определение `:` | src/forthc.fth:152 | 5 |  |
| 420 | `fc-push-group` | определение `:` | src/forthc.fth:160 | 2 |  |
| 421 | `fc-dup-at` | определение `:` | src/forthc.fth:166 | 1 |  |
| 422 | `fc-rest` | данные `create` | src/forthc.fth:168 | 2 |  |
| 423 | `fc-nrest` | переменная | src/forthc.fth:168 | 3 |  |
| 424 | `fc-mem-push` | определение `:` | src/forthc.fth:169 | 8 |  |
| 425 | `fc-src1` | определение `:` | src/forthc.fth:175 | 3 |  |
| 426 | `fc-need` | определение `:` | src/forthc.fth:176 | 15 |  |
| 427 | `fc-spill` | определение `:` | src/forthc.fth:182 | 19 |  |
| 428 | `fc-pop` | определение `:` | src/forthc.fth:188 | 13 |  |
| 429 | `fc-max-log` | константа | src/forthc.fth:193 | 2 |  |
| 430 | `fc-max-notes` | константа | src/forthc.fth:193 | 6 |  |
| 431 | `fc-log` | переменная | src/forthc.fth:194 | 3 |  |
| 432 | `fc-nlog` | переменная | src/forthc.fth:194 | 5 |  |
| 433 | `fc-decs` | переменная | src/forthc.fth:194 | 2 |  |
| 434 | `fc-ndec` | переменная | src/forthc.fth:194 | 6 |  |
| 435 | `fc-calls` | переменная | src/forthc.fth:194 | 2 |  |
| 436 | `fc-ncall` | переменная | src/forthc.fth:194 | 6 |  |
| 437 | `fc-pend` | переменная | src/forthc.fth:195 | 2 |  |
| 438 | `fc-npend` | переменная | src/forthc.fth:195 | 9 |  |
| 439 | `fc-unknown` | переменная | src/forthc.fth:195 | 7 |  |
| 440 | `fc-lc` | переменная | src/forthc.fth:196 | 3 |  |
| 441 | `fc-lb` | переменная | src/forthc.fth:196 | 3 |  |
| 442 | `fc-row-n` | определение `:` | src/forthc.fth:197 | 1 |  |
| 443 | `fc-mem-row?` | определение `:` | src/forthc.fth:198 | 1 |  |
| 444 | `fc-log-layer` | определение `:` | src/forthc.fth:199 | 2 |  |
| 445 | `fc-log-begin` | определение `:` | src/forthc.fth:210 | 3 |  |
| 446 | `fc-log-end` | определение `:` | src/forthc.fth:212 | 4 |  |
| 447 | `fc-by-execution` | определение `:` | src/forthc.fth:213 | 8 |  |
| 448 | `fc-dec@` | определение `:` | src/forthc.fth:214 | 2 |  |
| 449 | `fc-call@` | определение `:` | src/forthc.fth:215 | 2 |  |
| 450 | `fc-log-decision` | определение `:` | src/forthc.fth:216 | 2 |  |
| 451 | `fc-log-call` | определение `:` | src/forthc.fth:220 | 2 |  |
| 452 | `fc-callee` | переменная | src/forthc.fth:224 | 4 |  |
| 453 | `fc-live` | переменная | src/forthc.fth:226 | 7 |  |
| 454 | `fc-tramp` | переменная | src/forthc.fth:226 | 8 |  |
| 455 | `fc-ex` | переменная | src/forthc.fth:226 | 4 |  |
| 456 | `fc-thrower` | переменная | src/forthc.fth:226 | 4 |  |
| 457 | `fc-jump` | определение `:` | src/forthc.fth:227 | 7 |  |
| 458 | `fc-end` | определение `:` | src/forthc.fth:228 | 14 |  |
| 459 | `fc-begin-block` | определение `:` | src/forthc.fth:229 | 24 |  |
| 460 | `fc-rows1` | определение `:` | src/forthc.fth:233 | 15 |  |
| 461 | `fc-nonzero` | определение `:` | src/forthc.fth:234 | 2 |  |
| 462 | `fc-branch` | определение `:` | src/forthc.fth:237 | 6 |  |
| 463 | `fc-call` | определение `:` | src/forthc.fth:238 | 4 |  |
| 464 | `fc-v0` | переменная | src/forthc.fth:242 | 4 |  |
| 465 | `fc-v1` | переменная | src/forthc.fth:242 | 4 |  |
| 466 | `fc-jw` | определение `:` | src/forthc.fth:243 | 2 |  |
| 467 | `fc-xw` | определение `:` | src/forthc.fth:244 | 2 |  |
| 468 | `fc-xoff` | определение `:` | src/forthc.fth:245 | 2 |  |
| 469 | `fc-etab-at` | определение `:` | src/forthc.fth:246 | 1 |  |
| 470 | `fc-ex-base` | определение `:` | src/forthc.fth:247 | 1 |  |
| 471 | `fc-call-indirect` | определение `:` | src/forthc.fth:248 | 2 |  |
| 472 | `fc-push-frame` | определение `:` | src/forthc.fth:255 | 2 |  |
| 473 | `fc-link-copy` | определение `:` | src/forthc.fth:258 | 1 |  |
| 474 | `fc-restore` | определение `:` | src/forthc.fth:263 | 3 |  |
| 475 | `fc-build-thrower` | определение `:` | src/forthc.fth:265 | 1 |  |
| 476 | `fc-throw` | определение `:` | src/forthc.fth:271 | 1 |  |
| 477 | `fc-catch` | определение `:` | src/forthc.fth:274 | 1 |  |
| 478 | `fc-ret-p` | переменная | src/forthc.fth:283 | 4 |  |
| 479 | `fc-ret-l` | переменная | src/forthc.fth:283 | 7 |  |
| 480 | `fc-rs0` | переменная | src/forthc.fth:283 | 3 |  |
| 481 | `fc-rs1` | переменная | src/forthc.fth:283 | 3 |  |
| 482 | `fc-ret-patch` | определение `:` | src/forthc.fth:284 | 4 |  |
| 483 | `fc-ret-masked` | определение `:` | src/forthc.fth:286 | 1 |  |
| 484 | `fc-ret` | определение `:` | src/forthc.fth:290 | 3 |  |
| 485 | `fc-ca` | переменная | src/forthc.fth:302 | 3 |  |
| 486 | `fc-cl0` | переменная | src/forthc.fth:302 | 4 |  |
| 487 | `fc-cl1` | переменная | src/forthc.fth:302 | 4 |  |
| 488 | `fc-cr` | переменная | src/forthc.fth:302 | 4 |  |
| 489 | `fc-cslot` | переменная | src/forthc.fth:302 | 3 |  |
| 490 | `fc-csh` | переменная | src/forthc.fth:302 | 2 |  |
| 491 | `fc-cv` | переменная | src/forthc.fth:303 | 3 |  |
| 492 | `fc-cres` | переменная | src/forthc.fth:303 | 6 |  |
| 493 | `fc-cmode` | переменная | src/forthc.fth:303 | 6 |  |
| 494 | `fc-ar` | переменная | src/forthc.fth:303 | 5 |  |
| 495 | `fc-chk-read` | определение `:` | src/forthc.fth:304 | 1 |  |
| 496 | `fc-chk-seg` | определение `:` | src/forthc.fth:306 | 1 |  |
| 497 | `fc-as` | переменная | src/forthc.fth:309 | 2 |  |
| 498 | `fc-af` | переменная | src/forthc.fth:309 | 2 |  |
| 499 | `fc-al0` | переменная | src/forthc.fth:309 | 2 |  |
| 500 | `fc-al1` | переменная | src/forthc.fth:309 | 2 |  |
| 501 | `fc-apl` | переменная | src/forthc.fth:309 | 3 |  |
| 502 | `fc-afld` | переменная | src/forthc.fth:309 | 3 |  |
| 503 | `fc-access-patch` | определение `:` | src/forthc.fth:310 | 2 |  |
| 504 | `fc-access` | определение `:` | src/forthc.fth:315 | 1 |  |
| 505 | `fc-width` | определение `:` | src/forthc.fth:317 | 4 |  |
| 506 | `fc-check` | определение `:` | src/forthc.fth:318 | 4 |  |
| 507 | `fc-ring` | константа | src/forthc.fth:334 | 6 |  |
| 508 | `fc-window` | константа | src/forthc.fth:334 | 1 |  |
| 509 | `fc-sl` | данные `create` | src/forthc.fth:335 | 2 |  |
| 510 | `fc-stabs` | переменная | src/forthc.fth:335 | 2 |  |
| 511 | `fc-slen` | переменная | src/forthc.fth:336 | 7 |  |
| 512 | `fc-slow` | переменная | src/forthc.fth:336 | 4 |  |
| 513 | `fc-sinit` | определение `:` | src/forthc.fth:337 | 2 |  |
| 514 | `fc-sbegin` | определение `:` | src/forthc.fth:338 | 2 |  |
| 515 | `fc-tabs` | определение `:` | src/forthc.fth:339 | 3 |  |
| 516 | `fc-at` | определение `:` | src/forthc.fth:340 | 4 |  |
| 517 | `fc-has?` | определение `:` | src/forthc.fth:345 | 1 |  |
| 518 | `fc-tab+` | определение `:` | src/forthc.fth:346 | 1 |  |
| 519 | `fc-prw` | данные `create` | src/forthc.fth:347 | 6 |  |
| 520 | `fc-ptab` | переменная | src/forthc.fth:347 | 5 |  |
| 521 | `fc-place` | определение `:` | src/forthc.fth:348 | 3 |  |
| 522 | `fc-scopy` | определение `:` | src/forthc.fth:358 | 9 |  |
| 523 | `fc-segs` | данные `create` | src/forthc.fth:359 | 2 |  |
| 524 | `fc-nseg` | переменная | src/forthc.fth:359 | 5 |  |
| 525 | `fc-pp` | данные `create` | src/forthc.fth:360 | 2 |  |
| 526 | `fc-npp` | переменная | src/forthc.fth:360 | 4 |  |
| 527 | `fc-latest` | переменная | src/forthc.fth:360 | 4 |  |
| 528 | `fc-sga` | переменная | src/forthc.fth:360 | 14 |  |
| 529 | `fc-ltab` | переменная | src/forthc.fth:361 | 3 |  |
| 530 | `fc-ls` | переменная | src/forthc.fth:361 | 3 |  |
| 531 | `fc-lw` | переменная | src/forthc.fth:361 | 3 |  |
| 532 | `fc-ldst` | переменная | src/forthc.fth:361 | 2 |  |
| 533 | `fc-seg+` | определение `:` | src/forthc.fth:362 | 21 |  |
| 534 | `fc-pp+` | определение `:` | src/forthc.fth:365 | 1 |  |
| 535 | `fc-slookup` | определение `:` | src/forthc.fth:366 | 8 |  |
| 536 | `fc-nx` | переменная | src/forthc.fth:384 | 3 |  |
| 537 | `fc-nv` | переменная | src/forthc.fth:384 | 2 |  |
| 538 | `fc-nt` | переменная | src/forthc.fth:384 | 3 |  |
| 539 | `fc-negate-chain` | определение `:` | src/forthc.fth:385 | 1 |  |
| 540 | `fc-gw` | переменная | src/forthc.fth:391 | 4 |  |
| 541 | `fc-gs` | переменная | src/forthc.fth:391 | 2 |  |
| 542 | `fc-gs2` | переменная | src/forthc.fth:391 | 2 |  |
| 543 | `fc-gts` | переменная | src/forthc.fth:391 | 6 |  |
| 544 | `fc-gdst` | переменная | src/forthc.fth:391 | 2 |  |
| 545 | `fc-negate-select` | определение `:` | src/forthc.fth:392 | 4 |  |
| 546 | `fc-sfinish` | определение `:` | src/forthc.fth:397 | 2 |  |
| 547 | `fc-pr` | данные `create` | src/forthc.fth:400 | 2 |  |
| 548 | `fc-xs` | данные `create` | src/forthc.fth:400 | 2 |  |
| 549 | `fc-m4` | переменная | src/forthc.fth:401 | 2 |  |
| 550 | `fc-mj` | переменная | src/forthc.fth:401 | 11 |  |
| 551 | `fc-mk` | переменная | src/forthc.fth:401 | 6 |  |
| 552 | `fc-p@` | определение `:` | src/forthc.fth:402 | 3 |  |
| 553 | `fc-p!` | определение `:` | src/forthc.fth:403 | 1 |  |
| 554 | `fc-x@` | определение `:` | src/forthc.fth:404 | 3 |  |
| 555 | `fc-x!` | определение `:` | src/forthc.fth:405 | 2 |  |
| 556 | `fc-build-mul` | определение `:` | src/forthc.fth:406 | 1 |  |
| 557 | `fc-sub` | данные `create` | src/forthc.fth:424 | 2 |  |
| 558 | `fc-qsel` | переменная | src/forthc.fth:424 | 2 |  |
| 559 | `fc-absa` | переменная | src/forthc.fth:425 | 5 |  |
| 560 | `fc-absb` | переменная | src/forthc.fth:425 | 3 |  |
| 561 | `fc-ta` | переменная | src/forthc.fth:425 | 4 |  |
| 562 | `fc-tb` | переменная | src/forthc.fth:425 | 2 |  |
| 563 | `fc-rem` | переменная | src/forthc.fth:426 | 7 |  |
| 564 | `fc-tr` | переменная | src/forthc.fth:426 | 7 |  |
| 565 | `fc-q` | переменная | src/forthc.fth:426 | 3 |  |
| 566 | `fc-tq` | переменная | src/forthc.fth:426 | 4 |  |
| 567 | `fc-k` | переменная | src/forthc.fth:426 | 5 |  |
| 568 | `fc-w` | переменная | src/forthc.fth:427 | 14 |  |
| 569 | `fc-lo` | переменная | src/forthc.fth:427 | 7 |  |
| 570 | `fc-tlo` | переменная | src/forthc.fth:427 | 7 |  |
| 571 | `fc-t0` | переменная | src/forthc.fth:427 | 4 |  |
| 572 | `fc-t1` | переменная | src/forthc.fth:427 | 4 |  |
| 573 | `fc-qr` | переменная | src/forthc.fth:427 | 4 |  |
| 574 | `fc-tqk` | переменная | src/forthc.fth:427 | 3 |  |
| 575 | `fc-sub@` | определение `:` | src/forthc.fth:428 | 7 |  |
| 576 | `fc-step` | определение `:` | src/forthc.fth:429 | 3 |  |
| 577 | `fc-div-step` | определение `:` | src/forthc.fth:436 | 1 |  |
| 578 | `fc-build-div` | определение `:` | src/forthc.fth:453 | 1 |  |
| 579 | `fc-mul-entry` | переменная | src/forthc.fth:469 | 4 |  |
| 580 | `fc-mul-exit` | переменная | src/forthc.fth:469 | 2 |  |
| 581 | `fc-div-entry` | переменная | src/forthc.fth:469 | 5 |  |
| 582 | `fc-div-exit` | переменная | src/forthc.fth:469 | 4 |  |
| 583 | `fc-hl` | переменная | src/forthc.fth:470 | 6 |  |
| 584 | `fc-hcont` | переменная | src/forthc.fth:470 | 4 |  |
| 585 | `fc-mul-cost` | данные `create` | src/forthc.fth:471 | 2 |  |
| 586 | `fc-div-cost` | данные `create` | src/forthc.fth:471 | 2 |  |
| 587 | `fc-row-or-new` | определение `:` | src/forthc.fth:472 | 2 |  |
| 588 | `fc-call-helper` | определение `:` | src/forthc.fth:474 | 4 |  |
| 589 | `fc-result1` | определение `:` | src/forthc.fth:483 | 3 |  |
| 590 | `fc-s1` | переменная | src/forthc.fth:484 | 2 |  |
| 591 | `fc-s2` | переменная | src/forthc.fth:484 | 2 |  |
| 592 | `fc-r1` | переменная | src/forthc.fth:484 | 2 |  |
| 593 | `fc-result2` | определение `:` | src/forthc.fth:485 | 1 |  |
| 594 | `fc-pexit` | переменная | src/forthc.fth:492 | 2 |  |
| 595 | `fc-ptramp` | переменная | src/forthc.fth:492 | 2 |  |
| 596 | `fc-pd` | переменная | src/forthc.fth:492 | 5 |  |
| 597 | `fc-pc` | переменная | src/forthc.fth:492 | 5 |  |
| 598 | `fc-ends` | переменная | src/forthc.fth:492 | 3 |  |
| 599 | `fc-pb` | переменная | src/forthc.fth:493 | 5 |  |
| 600 | `fc-pcp` | переменная | src/forthc.fth:493 | 5 |  |
| 601 | `fc-pln` | переменная | src/forthc.fth:493 | 5 |  |
| 602 | `fc-pk` | переменная | src/forthc.fth:493 | 4 |  |
| 603 | `fc-pcall` | переменная | src/forthc.fth:493 | 3 |  |
| 604 | `fc-best` | данные `create` | src/forthc.fth:494 | 10 |  |
| 605 | `fc-pend@` | определение `:` | src/forthc.fth:495 | 7 |  |
| 606 | `fc-reach` | определение `:` | src/forthc.fth:496 | 2 |  |
| 607 | `fc-take` | определение `:` | src/forthc.fth:505 | 1 |  |
| 608 | `fc-end-path` | определение `:` | src/forthc.fth:512 | 1 |  |
| 609 | `fc-to` | определение `:` | src/forthc.fth:516 | 2 |  |
| 610 | `fc-node` | определение `:` | src/forthc.fth:520 | 1 |  |
| 611 | `fc-path` | определение `:` | src/forthc.fth:539 | 3 |  |
| 612 | `fc-cost!` | определение `:` | src/forthc.fth:548 | 3 |  |
| 613 | `fc-ll` | переменная | src/forthc.fth:550 | 6 |  |
| 614 | `fc-llr` | переменная | src/forthc.fth:550 | 3 |  |
| 615 | `fc-llv` | переменная | src/forthc.fth:550 | 3 |  |
| 616 | `fc-plit` | переменная | src/forthc.fth:550 | 6 |  |
| 617 | `fc-plr` | переменная | src/forthc.fth:550 | 4 |  |
| 618 | `fc-plv` | переменная | src/forthc.fth:550 | 6 |  |
| 619 | `fc-literal` | определение `:` | src/forthc.fth:551 | 14 |  |
| 620 | `fc-or-zero` | определение `:` | src/forthc.fth:553 | 2 |  |
| 621 | `fc-ba` | переменная | src/forthc.fth:556 | 13 |  |
| 622 | `fc-bb` | переменная | src/forthc.fth:556 | 13 |  |
| 623 | `fc-br` | переменная | src/forthc.fth:556 | 9 |  |
| 624 | `fc-binary` | определение `:` | src/forthc.fth:557 | 10 |  |
| 625 | `fc-r-at` | определение `:` | src/forthc.fth:581 | 2 |  |
| 626 | `fc-pop-pinned` | определение `:` | src/forthc.fth:584 | 3 |  |
| 627 | `fc-sk` | переменная | src/forthc.fth:585 | 12 |  |
| 628 | `fc-shift-copy` | определение `:` | src/forthc.fth:586 | 2 |  |
| 629 | `fc-inc` | определение `:` | src/forthc.fth:590 | 3 |  |
| 630 | `fc-read-key` | определение `:` | src/forthc.fth:593 | 1 |  |
| 631 | `fc-text` | переменная | src/forthc.fth:598 | 13 |  |
| 632 | `fc-tlen` | переменная | src/forthc.fth:598 | 14 |  |
| 633 | `fc-pos` | переменная | src/forthc.fth:598 | 24 |  |
| 634 | `fc-text-size` | переменная | src/forthc.fth:598 | 6 | вход бута (хост) |
| 635 | `fc-tok` | данные `create` | src/forthc.fth:599 | 19 |  |
| 636 | `fc-tl` | переменная | src/forthc.fth:599 | 24 |  |
| 637 | `fc-reset` | определение `:` | src/forthc.fth:600 | 3 |  |
| 638 | `fc-append` | определение `:` | src/forthc.fth:601 | 1 |  |
| 639 | `fc\|` | определение `:` | src/forthc.fth:605 | 1 | вход бута (хост) |
| 640 | `fc-ch` | определение `:` | src/forthc.fth:606 | 5 |  |
| 641 | `fc-more?` | определение `:` | src/forthc.fth:607 | 6 |  |
| 642 | `fc-next` | определение `:` | src/forthc.fth:608 | 8 |  |
| 643 | `fc-next!` | определение `:` | src/forthc.fth:616 | 10 |  |
| 644 | `fc-is?` | определение `:` | src/forthc.fth:617 | 5 |  |
| 645 | `fc-raw` | определение `:` | src/forthc.fth:620 | 1 |  |
| 646 | `fc-string-token` | определение `:` | src/forthc.fth:621 | 1 |  |
| 647 | `fc-names-size` | переменная | src/forthc.fth:626 | 5 | вход бута (хост) |
| 648 | `fc-max-words` | переменная | src/forthc.fth:626 | 5 | вход бута (хост) |
| 649 | `fc-names` | переменная | src/forthc.fth:627 | 3 |  |
| 650 | `fc-names-used` | переменная | src/forthc.fth:627 | 5 |  |
| 651 | `fc-wt` | переменная | src/forthc.fth:628 | 5 |  |
| 652 | `fc-nwords` | переменная | src/forthc.fth:628 | 12 |  |
| 653 | `fc-wbk` | переменная | src/forthc.fth:628 | 3 |  |
| 654 | `fc-wt@` | определение `:` | src/forthc.fth:631 | 6 |  |
| 655 | `fc-proved` | данные `create` | src/forthc.fth:633 | 2 |  |
| 656 | `fc-unproved` | данные `create` | src/forthc.fth:634 | 2 |  |
| 657 | `fc-mechanisms` | определение `:` | src/forthc.fth:635 | 1 |  |
| 658 | `fc-xt` | определение `:` | src/forthc.fth:640 | 5 |  |
| 659 | `fc-xtn` | определение `:` | src/forthc.fth:642 | 2 |  |
| 660 | `fc-hash` | определение `:` | src/forthc.fth:643 | 2 |  |
| 661 | `fc-define` | определение `:` | src/forthc.fth:645 | 6 |  |
| 662 | `fc-lookup` | определение `:` | src/forthc.fth:650 | 5 |  |
| 663 | `fc-find` | определение `:` | src/forthc.fth:654 | 6 |  |
| 664 | `fc-word-of` | определение `:` | src/forthc.fth:656 | 2 |  |
| 665 | `fc-cost` | определение `:` | src/forthc.fth:664 | 1 |  |
| 666 | `fc-proved?` | определение `:` | src/forthc.fth:667 | 1 |  |
| 667 | `fc-here` | переменная | src/forthc.fth:669 | 9 |  |
| 668 | `fc-word` | переменная | src/forthc.fth:669 | 13 |  |
| 669 | `fc-uses` | переменная | src/forthc.fth:669 | 16 |  |
| 670 | `fc-rt` | переменная | src/forthc.fth:670 | 7 |  |
| 671 | `fc-rta` | переменная | src/forthc.fth:670 | 7 |  |
| 672 | `fc-ctl` | данные `create` | src/forthc.fth:671 | 1 |  |
| 673 | `fc-nctl` | переменная | src/forthc.fth:671 | 12 |  |
| 674 | `fc-cleave` | переменная | src/forthc.fth:671 | 2 |  |
| 675 | `fc-ctl@` | определение `:` | src/forthc.fth:672 | 4 |  |
| 676 | `fc-ctl+` | определение `:` | src/forthc.fth:673 | 6 |  |
| 677 | `fc-ctl-` | определение `:` | src/forthc.fth:675 | 7 |  |
| 678 | `fc-do-entry` | определение `:` | src/forthc.fth:677 | 1 |  |
| 679 | `fc-ctl-leave` | определение `:` | src/forthc.fth:679 | 1 |  |
| 680 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:680 | 1 |  |
| 681 | `fc-loop-leave` | определение `:` | src/forthc.fth:681 | 1 |  |
| 682 | `fc-align` | определение `:` | src/forthc.fth:682 | 2 |  |
| 683 | `fc-check-here` | определение `:` | src/forthc.fth:683 | 3 |  |
| 684 | `fc-define-data` | определение `:` | src/forthc.fth:684 | 2 |  |
| 685 | `fc-sat` | переменная | src/forthc.fth:685 | 3 |  |
| 686 | `fc-store-string` | определение `:` | src/forthc.fth:686 | 1 |  |
| 687 | `fc-ct` | данные `create` | src/forthc.fth:691 | 3 |  |
| 688 | `fc-nct` | переменная | src/forthc.fth:691 | 11 |  |
| 689 | `fc-ct+` | определение `:` | src/forthc.fth:692 | 15 |  |
| 690 | `fc-ct-` | определение `:` | src/forthc.fth:693 | 9 |  |
| 691 | `fc-ct2` | определение `:` | src/forthc.fth:694 | 8 |  |
| 692 | `fc-inits` | данные `create` | src/forthc.fth:695 | 2 |  |
| 693 | `fc-ninit` | переменная | src/forthc.fth:695 | 5 |  |
| 694 | `fc-init-open` | переменная | src/forthc.fth:695 | 6 |  |
| 695 | `fc-init` | определение `:` | src/forthc.fth:696 | 1 |  |
| 696 | `fc-scan-uses` | определение `:` | src/forthc.fth:712 | 1 |  |
| 697 | `fc-const-shift` | определение `:` | src/forthc.fth:719 | 2 |  |
| 698 | `fc-lit?` | определение `:` | src/forthc.fth:728 | 3 |  |
| 699 | `fc-mul-lit?` | определение `:` | src/forthc.fth:730 | 1 |  |
| 700 | `fc-shift-lit?` | определение `:` | src/forthc.fth:735 | 2 |  |
| 701 | `fc-pick-roll` | определение `:` | src/forthc.fth:738 | 2 |  |
| 702 | `fc-stx` | переменная | src/forthc.fth:747 | 3 |  |
| 703 | `fc-stlo` | переменная | src/forthc.fth:747 | 8 |  |
| 704 | `fc-sthi` | переменная | src/forthc.fth:747 | 4 |  |
| 705 | `fc-stp` | переменная | src/forthc.fth:747 | 6 |  |
| 706 | `fc-strow` | переменная | src/forthc.fth:747 | 8 |  |
| 707 | `fc-stm` | переменная | src/forthc.fth:747 | 5 |  |
| 708 | `fc-ftr` | переменная | src/forthc.fth:748 | 5 |  |
| 709 | `fc-stg` | переменная | src/forthc.fth:748 | 2 |  |
| 710 | `fc-sw0` | определение `:` | src/forthc.fth:749 | 2 |  |
| 711 | `fc-sw1` | определение `:` | src/forthc.fth:750 | 2 |  |
| 712 | `fc-sbase` | определение `:` | src/forthc.fth:751 | 2 |  |
| 713 | `fc-space-end` | определение `:` | src/forthc.fth:752 | 2 |  |
| 714 | `fc-space-store` | определение `:` | src/forthc.fth:760 | 2 |  |
| 715 | `fc-space-fetch` | определение `:` | src/forthc.fth:767 | 2 |  |
| 716 | `fc-cp` | определение `:` | src/forthc.fth:778 | 4 |  |
| 717 | `fc-copy-row` | определение `:` | src/forthc.fth:780 | 1 |  |
| 718 | `fc-close-init` | определение `:` | src/forthc.fth:783 | 2 |  |
| 719 | `fc-open-init` | определение `:` | src/forthc.fth:786 | 1 |  |
| 720 | `fc-gens` | переменная | src/forthc.fth:797 | 3 |  |
| 721 | `fc-generator` | определение `:` | src/forthc.fth:798 | 87 |  |
| 722 | `fc-literal-name` | определение `:` | src/forthc.fth:800 | 10 |  |
| 723 | `fc-words` | определение `:` | src/forthc.fth:802 | 1 |  |
| 724 | `fc-known` | определение `:` | src/forthc.fth:813 | 1 |  |
| 725 | `fc-defining?` | определение `:` | src/forthc.fth:815 | 7 |  |
| 726 | `fc-code` | определение `:` | src/forthc.fth:816 | 51 | вариант 2 |
| 727 | `fc-fold?` | определение `:` | src/forthc.fth:818 | 13 |  |
| 728 | `fc-top-only` | определение `:` | src/forthc.fth:819 | 6 |  |
| 729 | `fc-not-found` | определение `:` | src/forthc.fth:821 | 1 |  |
| 730 | `fc-word-token` | определение `:` | src/forthc.fth:823 | 2 |  |
| 731 | `fc-token` | определение `:` | src/forthc.fth:828 | 2 |  |
| 732 | `fc-synonym-of` | определение `:` | src/forthc.fth:829 | 2 |  |
| 733 | `fc-synonym` | определение `:` | src/forthc.fth:830 | 10 |  |
| 734 | `fc-sy` | переменная | src/forthc.fth:833 | 2 |  |
| 735 | `fc-synonym?` | определение `:` | src/forthc.fth:834 | 1 |  |
| 736 | `fc-poke` | определение `:` | src/forthc.fth:837 | 2 |  |
| 737 | `fc-concept-record` | определение `:` | src/forthc.fth:840 | 1 |  |
| 738 | `fc-eval` | определение `:` | src/forthc.fth:845 | 54 |  |
| 739 | `fc-concepts` | определение `:` | src/forthc.fth:849 | 1 |  |
| 740 | `fc-nhost` | переменная | src/forthc.fth:856 | 5 |  |
| 741 | `fc-platform` | определение `:` | src/forthc.fth:857 | 1 |  |
| 742 | `fc-time-price` | определение `:` | src/forthc.fth:880 | 1 |  |
| 743 | `fc-replacement` | определение `:` | src/forthc.fth:890 | 1 |  |
| 744 | `fc-library` | определение `:` | src/forthc.fth:905 | 1 |  |
| 745 | `fc-long` | определение `:` | src/forthc.fth:924 | 1 |  |
| 746 | `fc-helpers-cost` | определение `:` | src/forthc.fth:932 | 1 |  |
| 747 | `fc-price-word` | определение `:` | src/forthc.fth:939 | 1 |  |
| 748 | `fc-compile` | определение `:` | src/forthc.fth:942 | 1 |  |
| 749 | `fc-go` | определение `:` | src/forthc.fth:959 | 3 | вход бута (хост) |
| 750 | `gen+` | определение `:` | src/primitives.fth:4 | 5 |  |
| 751 | `gen-` | определение `:` | src/primitives.fth:5 | 2 |  |
| 752 | `gen-and` | определение `:` | src/primitives.fth:6 | 2 |  |
| 753 | `gen-or` | определение `:` | src/primitives.fth:7 | 2 |  |
| 754 | `gen-xor` | определение `:` | src/primitives.fth:8 | 2 |  |
| 755 | `gen=` | определение `:` | src/primitives.fth:9 | 2 |  |
| 756 | `gen<` | определение `:` | src/primitives.fth:10 | 2 |  |
| 757 | `gen-u<` | определение `:` | src/primitives.fth:11 | 2 |  |
| 758 | `gen-lshift` | определение `:` | src/primitives.fth:12 | 2 |  |
| 759 | `gen-rshift` | определение `:` | src/primitives.fth:14 | 2 |  |
| 760 | `gen-0=` | определение `:` | src/primitives.fth:16 | 2 |  |
| 761 | `gen-cells` | определение `:` | src/primitives.fth:17 | 2 |  |
| 762 | `gen-2*` | определение `:` | src/primitives.fth:18 | 2 |  |
| 763 | `gen-1+` | определение `:` | src/primitives.fth:19 | 2 |  |
| 764 | `gen-1-` | определение `:` | src/primitives.fth:20 | 2 |  |
| 765 | `gen-cell+` | определение `:` | src/primitives.fth:21 | 2 |  |
| 766 | `gen*` | определение `:` | src/primitives.fth:22 | 2 |  |
| 767 | `gen/` | определение `:` | src/primitives.fth:25 | 2 |  |
| 768 | `gen-mod` | определение `:` | src/primitives.fth:26 | 2 |  |
| 769 | `gen/mod` | определение `:` | src/primitives.fth:27 | 2 |  |
| 770 | `gen-dup` | определение `:` | src/primitives.fth:28 | 2 |  |
| 771 | `gen-drop` | определение `:` | src/primitives.fth:29 | 2 |  |
| 772 | `gen-swap` | определение `:` | src/primitives.fth:30 | 2 |  |
| 773 | `gen-over` | определение `:` | src/primitives.fth:31 | 2 |  |
| 774 | `gen-rot` | определение `:` | src/primitives.fth:32 | 2 |  |
| 775 | `gen-pick` | определение `:` | src/primitives.fth:33 | 2 |  |
| 776 | `gen-roll` | определение `:` | src/primitives.fth:34 | 2 |  |
| 777 | `gen->r` | определение `:` | src/primitives.fth:35 | 2 |  |
| 778 | `gen-r>` | определение `:` | src/primitives.fth:36 | 2 |  |
| 779 | `gen-r@` | определение `:` | src/primitives.fth:37 | 4 |  |
| 780 | `gen-j` | определение `:` | src/primitives.fth:38 | 2 |  |
| 781 | `gen-@` | определение `:` | src/primitives.fth:39 | 2 |  |
| 782 | `gen-!` | определение `:` | src/primitives.fth:41 | 2 |  |
| 783 | `gen-c@` | определение `:` | src/primitives.fth:42 | 2 |  |
| 784 | `gen-c!` | определение `:` | src/primitives.fth:44 | 2 |  |
| 785 | `gen-emit` | определение `:` | src/primitives.fth:45 | 2 |  |
| 786 | `gen-key` | определение `:` | src/primitives.fth:48 | 2 |  |
| 787 | `gen-if` | определение `:` | src/primitives.fth:50 | 2 |  |
| 788 | `gen-else` | определение `:` | src/primitives.fth:51 | 2 |  |
| 789 | `gen-then` | определение `:` | src/primitives.fth:53 | 2 |  |
| 790 | `gen-begin` | определение `:` | src/primitives.fth:57 | 2 |  |
| 791 | `gen-until` | определение `:` | src/primitives.fth:58 | 2 |  |
| 792 | `gen-while` | определение `:` | src/primitives.fth:60 | 2 |  |
| 793 | `gen-repeat` | определение `:` | src/primitives.fth:61 | 2 |  |
| 794 | `gen-again` | определение `:` | src/primitives.fth:62 | 2 |  |
| 795 | `gen-do` | определение `:` | src/primitives.fth:63 | 2 |  |
| 796 | `fc-di` | переменная | src/primitives.fth:66 | 3 |  |
| 797 | `fc-dl` | переменная | src/primitives.fth:66 | 3 |  |
| 798 | `gen-?do` | определение `:` | src/primitives.fth:67 | 2 |  |
| 799 | `fc-lv` | переменная | src/primitives.fth:73 | 2 |  |
| 800 | `gen-loop` | определение `:` | src/primitives.fth:74 | 2 |  |
| 801 | `gen-leave` | определение `:` | src/primitives.fth:83 | 2 |  |
| 802 | `gen-unloop` | определение `:` | src/primitives.fth:86 | 2 |  |
| 803 | `gen-exit` | определение `:` | src/primitives.fth:87 | 2 |  |
| 804 | `gen-recurse` | определение `:` | src/primitives.fth:89 | 2 |  |
| 805 | `gen-tick` | определение `:` | src/primitives.fth:90 | 2 |  |
| 806 | `gen-throw` | определение `:` | src/primitives.fth:93 | 2 |  |
| 807 | `gen-call` | определение `:` | src/primitives.fth:97 | 3 |  |
| 808 | `gen-space!` | определение `:` | src/primitives.fth:98 | 2 |  |
| 809 | `gen-spacec!` | определение `:` | src/primitives.fth:99 | 2 |  |
| 810 | `gen-space@` | определение `:` | src/primitives.fth:100 | 2 |  |
| 811 | `gen-spacec@` | определение `:` | src/primitives.fth:101 | 2 |  |
| 812 | `gen-execute` | определение `:` | src/primitives.fth:102 | 2 |  |
| 813 | `gen-catch` | определение `:` | src/primitives.fth:103 | 2 |  |
| 814 | `fc-entry-cell` | определение `:` | src/primitives.fth:109 | 1 |  |
| 815 | `fc-concept` | определение `:` | src/primitives.fth:111 | 1 |  |
| 816 | `gen-colon` | определение `:` | src/primitives.fth:118 | 2 |  |
| 817 | `gen-semicolon` | определение `:` | src/primitives.fth:124 | 2 |  |
| 818 | `gen-variable` | определение `:` | src/primitives.fth:127 | 2 |  |
| 819 | `gen-create` | определение `:` | src/primitives.fth:128 | 2 |  |
| 820 | `gen-allot` | определение `:` | src/primitives.fth:129 | 2 |  |
| 821 | `gen-constant` | определение `:` | src/primitives.fth:130 | 2 |  |
| 822 | `gen-decimal` | определение `:` | src/primitives.fth:131 | 2 |  |
| 823 | `gen-kernel-layout` | определение `:` | src/primitives.fth:132 | 2 |  |
| 824 | `gen-backslash` | определение `:` | src/primitives.fth:133 | 2 |  |
| 825 | `gen-paren` | определение `:` | src/primitives.fth:135 | 4 |  |
| 826 | `gen-char` | определение `:` | src/primitives.fth:136 | 2 |  |
| 827 | `gen-string` | определение `:` | src/primitives.fth:137 | 2 |  |
| 828 | `fc-digit@` | определение `:` | src/primitives.fth:140 | 1 |  |
| 829 | `gen-literal` | определение `:` | src/primitives.fth:142 | 2 |  |
| 830 | `fc-known-xt` | определение `:` | src/primitives.fth:149 | 2 |  |
| 831 | `gen-cost` | определение `:` | src/primitives.fth:150 | 2 |  |
| 832 | `gen-proved?` | определение `:` | src/primitives.fth:152 | 2 |  |
| 833 | `gen-library` | определение `:` | src/primitives.fth:153 | 16 |  |
| 834 | `gen-price` | определение `:` | src/primitives.fth:154 | 2 |  |
| 835 | `fc-cpos` | переменная | src/primitives.fth:159 | 4 |  |
| 836 | `fc-hn` | переменная | src/primitives.fth:159 | 2 |  |
| 837 | `fc-cdepth` | переменная | src/primitives.fth:159 | 4 |  |
| 838 | `fc-hname` | данные `create` | src/primitives.fth:159 | 2 |  |
| 839 | `fc-hb` | определение `:` | src/primitives.fth:160 | 3 |  |
| 840 | `fc-c,` | определение `:` | src/primitives.fth:161 | 17 |  |
| 841 | `fc-c1` | определение `:` | src/primitives.fth:162 | 8 |  |
| 842 | `fc-c-gen` | определение `:` | src/primitives.fth:163 | 1 |  |
| 843 | `fc-c-body` | определение `:` | src/primitives.fth:167 | 1 |  |
| 844 | `gen-host` | определение `:` | src/primitives.fth:176 | 2 |  |
| 845 | `fc-name2` | определение `:` | src/primitives.fth:193 | 1 |  |
| 846 | `fc-generators` | определение `:` | src/primitives.fth:196 | 1 |  |
| 847 | `+` | генератор | src/primitives.fth:197 | 558 | слово компилятора `gen+` |
| 848 | `-` | генератор | src/primitives.fth:197 | 61 | слово компилятора `gen-` |
| 849 | `*` | генератор | src/primitives.fth:198 | 83 | слово компилятора `gen*` |
| 850 | `/` | генератор | src/primitives.fth:198 | 4 | слово компилятора `gen/` |
| 851 | `mod` | генератор | src/primitives.fth:199 | 2 | слово компилятора `gen-mod` |
| 852 | `and` | генератор | src/primitives.fth:200 | 121 | слово компилятора `gen-and` |
| 853 | `or` | генератор | src/primitives.fth:200 | 45 | слово компилятора `gen-or` |
| 854 | `xor` | генератор | src/primitives.fth:201 | 5 | слово компилятора `gen-xor` |
| 855 | `lshift` | генератор | src/primitives.fth:201 | 93 | слово компилятора `gen-lshift` |
| 856 | `rshift` | генератор | src/primitives.fth:202 | 63 | слово компилятора `gen-rshift` |
| 857 | `=` | генератор | src/primitives.fth:202 | 82 | слово компилятора `gen=` |
| 858 | `<` | генератор | src/primitives.fth:203 | 28 | слово компилятора `gen<` |
| 859 | `u<` | генератор | src/primitives.fth:203 | 24 | слово компилятора `gen-u<` |
| 860 | `0=` | генератор | src/primitives.fth:204 | 98 | слово компилятора `gen-0=` |
| 861 | `2*` | генератор | src/primitives.fth:204 | 29 | слово компилятора `gen-2*` |
| 862 | `1+` | генератор | src/primitives.fth:205 | 43 | слово компилятора `gen-1+` |
| 863 | `1-` | генератор | src/primitives.fth:205 | 56 | слово компилятора `gen-1-` |
| 864 | `cells` | генератор | src/primitives.fth:206 | 282 | слово компилятора `gen-cells` |
| 865 | `cell+` | генератор | src/primitives.fth:206 | 57 | слово компилятора `gen-cell+` |
| 866 | `dup` | генератор | src/primitives.fth:207 | 304 | слово компилятора `gen-dup` |
| 867 | `drop` | генератор | src/primitives.fth:207 | 205 | слово компилятора `gen-drop` |
| 868 | `swap` | генератор | src/primitives.fth:208 | 141 | слово компилятора `gen-swap` |
| 869 | `over` | генератор | src/primitives.fth:208 | 87 | слово компилятора `gen-over` |
| 870 | `rot` | генератор | src/primitives.fth:209 | 37 | слово компилятора `gen-rot` |
| 871 | `pick` | генератор | src/primitives.fth:209 | 47 | слово компилятора `gen-pick` |
| 872 | `roll` | генератор | src/primitives.fth:210 | 7 | слово компилятора `gen-roll` |
| 873 | `>r` | генератор | src/primitives.fth:210 | 112 | слово компилятора `gen->r` |
| 874 | `r>` | генератор | src/primitives.fth:211 | 116 | слово компилятора `gen-r>` |
| 875 | `r@` | генератор | src/primitives.fth:211 | 108 | слово компилятора `gen-r@` |
| 876 | `i` | генератор | src/primitives.fth:212 | 172 | слово компилятора `gen-r@` |
| 877 | `j` | генератор | src/primitives.fth:212 | 12 | слово компилятора `gen-j` |
| 878 | `@` | генератор | src/primitives.fth:213 | 1262 | слово компилятора `gen-@` |
| 879 | `!` | генератор | src/primitives.fth:213 | 662 | слово компилятора `gen-!` |
| 880 | `c@` | генератор | src/primitives.fth:214 | 23 | слово компилятора `gen-c@` |
| 881 | `c!` | генератор | src/primitives.fth:214 | 18 | слово компилятора `gen-c!` |
| 882 | `space!` | генератор | src/primitives.fth:215 | 1 | слово компилятора `gen-space!` |
| 883 | `spacec!` | генератор | src/primitives.fth:215 | 1 | слово компилятора `gen-spacec!` |
| 884 | `space@` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-space@` |
| 885 | `emit` | генератор | src/primitives.fth:217 | 4 | слово компилятора `gen-emit` |
| 886 | `key` | генератор | src/primitives.fth:217 | 1 | слово компилятора `gen-key` |
| 887 | `if` | генератор | src/primitives.fth:218 | 307 | слово компилятора `gen-if` |
| 888 | `else` | генератор | src/primitives.fth:218 | 84 | слово компилятора `gen-else` |
| 889 | `then` | генератор | src/primitives.fth:219 | 307 | слово компилятора `gen-then` |
| 890 | `begin` | генератор | src/primitives.fth:219 | 25 | слово компилятора `gen-begin` |
| 891 | `until` | генератор | src/primitives.fth:220 | 2 | слово компилятора `gen-until` |
| 892 | `while` | генератор | src/primitives.fth:220 | 22 | слово компилятора `gen-while` |
| 893 | `repeat` | генератор | src/primitives.fth:221 | 22 | слово компилятора `gen-repeat` |
| 894 | `again` | генератор | src/primitives.fth:221 | 1 | слово компилятора `gen-again` |
| 895 | `do` | генератор | src/primitives.fth:222 | 31 | слово компилятора `gen-do` |
| 896 | `?do` | генератор | src/primitives.fth:222 | 58 | слово компилятора `gen-?do` |
| 897 | `loop` | генератор | src/primitives.fth:223 | 89 | слово компилятора `gen-loop` |
| 898 | `leave` | генератор | src/primitives.fth:223 | 1 | слово компилятора `gen-leave` |
| 899 | `unloop` | генератор | src/primitives.fth:224 | 7 | слово компилятора `gen-unloop` |
| 900 | `exit` | генератор | src/primitives.fth:224 | 81 | слово компилятора `gen-exit` |
| 901 | `recurse` | генератор | src/primitives.fth:225 | 2 | слово компилятора `gen-recurse` |
| 902 | `execute` | генератор | src/primitives.fth:225 | 10 | слово компилятора `gen-execute` |
| 903 | `[']` | генератор | src/primitives.fth:226 | 119 | слово компилятора `gen-tick` |
| 904 | `catch` | генератор | src/primitives.fth:226 | 1 | слово компилятора `gen-catch` |
| 905 | `throw` | генератор | src/primitives.fth:227 | 83 | слово компилятора `gen-throw` |
| 906 | `:` | генератор | src/primitives.fth:228 | 490 | слово компилятора `gen-colon` |
| 907 | `;` | генератор | src/primitives.fth:228 | 490 | слово компилятора `gen-semicolon` |
| 908 | `variable` | генератор | src/primitives.fth:229 | 319 | слово компилятора `gen-variable` |
| 909 | `create` | генератор | src/primitives.fth:229 | 47 | слово компилятора `gen-create` |
| 910 | `allot` | генератор | src/primitives.fth:230 | 45 | слово компилятора `gen-allot` |
| 911 | `constant` | генератор | src/primitives.fth:230 | 22 | слово компилятора `gen-constant` |
| 912 | `decimal` | генератор | src/primitives.fth:231 | 3 | слово компилятора `gen-decimal` |
| 913 | `kernel-layout` | генератор | src/primitives.fth:231 | 1 | слово компилятора `gen-kernel-layout` |
| 914 | `\` | генератор | src/primitives.fth:232 | 137 | слово компилятора `gen-backslash` |
| 915 | `(` | генератор | src/primitives.fth:232 | 469 | слово компилятора `gen-paren` |
| 916 | `[char]` | генератор | src/primitives.fth:232 | 8 | слово компилятора `gen-char` |
| 917 | `s"` | генератор | src/primitives.fth:233 | 198 | слово компилятора `gen-string` |
| 918 | `literal` | генератор | src/primitives.fth:234 | 496 | слово компилятора `gen-literal` |
| 919 | `0` | цифра (литерал) | src/primitives.fth:242 | 534 | значение 0 |
| 920 | `1` | цифра (литерал) | src/primitives.fth:242 | 445 | значение 1 |
| 921 | `2` | цифра (литерал) | src/primitives.fth:242 | 458 | значение 2 |
| 922 | `3` | цифра (литерал) | src/primitives.fth:242 | 304 | значение 3 |
| 923 | `4` | цифра (литерал) | src/primitives.fth:243 | 242 | значение 4 |
| 924 | `5` | цифра (литерал) | src/primitives.fth:243 | 105 | значение 5 |
| 925 | `6` | цифра (литерал) | src/primitives.fth:243 | 156 | значение 6 |
| 926 | `7` | цифра (литерал) | src/primitives.fth:243 | 60 | значение 7 |
| 927 | `8` | цифра (литерал) | src/primitives.fth:244 | 157 | значение 8 |
| 928 | `9` | цифра (литерал) | src/primitives.fth:244 | 37 | значение 9 |
| 929 | `fc-install-generators` | определение `:` | src/primitives.fth:245 | 1 |  |
| 930 | `heap-start` | данные `create` | src/main.fth:3 | 1 |  |
| 931 | `fc-read` | определение `:` | src/main.fth:6 | 2 |  |
| 932 | `fc-sizes` | определение `:` | src/main.fth:11 | 2 |  |
| 933 | `kn-at` | переменная | src/kernel.fth:7 | 5 |  |
| 934 | `kn-put` | определение `:` | src/kernel.fth:8 | 1 |  |
| 935 | `kn-order` | определение `:` | src/kernel.fth:16 | 1 |  |
| 936 | `kn-get` | определение `:` | src/kernel.fth:18 | 1 |  |
| 937 | `kn-compile` | определение `:` | src/kernel.fth:19 | 1 |  |
| 938 | `kn-.n` | определение `:` | src/kernel.fth:23 | 1 |  |
| 939 | `main` | определение `:` | src/kernel.fth:27 | 1 | вариант 2 |
| 940 | `kn-heap-start` | данные `create` | src/kernel.fth:31 | 1 |  |

## Числа определения

Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят сами цифры и `literal`. Различных чисел в определении: 90.

## Определены, но не использованы

Слов: 34. Они есть в тексте определения (замкнутость от этого не нарушается), но по графу до них не доходит ни одна ссылка.

| Слово | Вид | Файл:строка |
|---|---|---|
| `lay-out` | определение `:` | src/backend.fth:110 |
| `lay-cz` | переменная | src/compute.fth:166 |
| `lay-cf` | переменная | src/compute.fth:166 |
| `lay-compare` | определение `:` | src/compute.fth:167 |
| `lay-fc` | переменная | src/compute.fth:213 |
| `lay-ff` | переменная | src/compute.fth:213 |
| `lay-flag-exit` | определение `:` | src/compute.fth:214 |
| `lay-exit-layers` | определение `:` | src/compute.fth:222 |
| `lay-ce` | переменная | src/compute.fth:226 |
| `lay-cl` | переменная | src/compute.fth:226 |
| `lay-ch` | переменная | src/compute.fth:226 |
| `lay-call-rows` | определение `:` | src/compute.fth:227 |
| `lay-halt-begin` | определение `:` | src/compute.fth:231 |
| `lay-halt-region` | определение `:` | src/compute.fth:232 |
| `lay-halt-end` | определение `:` | src/compute.fth:233 |
| `lay-stub-on` | определение `:` | src/compute.fth:234 |
| `lay-stub` | определение `:` | src/compute.fth:235 |
| `fc-depth` | определение `:` | src/forthc.fth:811 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:812 |
| `/mod` | генератор | src/primitives.fth:199 |
| `spacec@` | генератор | src/primitives.fth:216 |
| `cost` | генератор | src/primitives.fth:235 |
| `price` | генератор | src/primitives.fth:235 |
| `proved?` | генератор | src/primitives.fth:236 |
| `check-table` | генератор | src/primitives.fth:237 |
| `accuracy` | генератор | src/primitives.fth:237 |
| `replace` | генератор | src/primitives.fth:238 |
| `long!` | генератор | src/primitives.fth:239 |
| `long@` | генератор | src/primitives.fth:239 |
| `host` | генератор | src/primitives.fth:240 |
| `time` | генератор | src/primitives.fth:240 |
| `platform` | генератор | src/primitives.fth:241 |
| `platform-of` | генератор | src/primitives.fth:241 |
| `main` (вариант 1) | определение `:` | src/main.fth:14 |

## Слова, которые при буте исполняет хост

Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки `backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках 83; все они определены в определении языка (генератором в `primitives.fth` или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: `!` `*` `+` `+!` `-` `-rot` `/` `/string` `0<` `0<>` `0=` `0>` `1+` `1-` `2!` `2*` `2@` `2drop` `2dup` `2over` `2swap` `<` `<>` `=` `>` `>in` `>r` `?do` `?dup` `@` `again` `allocate` `and` `begin` `c!` `c@` `cell+` `cells` `cmove` `cmove>` `compare` `decimal` `do` `drop` `dup` `else` `execute` `exit` `fill` `free` `i` `if` `invert` `j` `leave` `loop` `lshift` `max` `min` `mod` `negate` `nip` `or` `over` `pick` `r>` `r@` `repeat` `roll` `rot` `rshift` `source` `swap` `then` `throw` `tuck` `type` `u<` `u>` `unloop` `until` `while` `xor`.

Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро читает каналом `key`), `source` и `>in` — слова только этого пути.
