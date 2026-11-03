# Ядро языка (14.8)

Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется `tests/test_core.py`; руками не правится.

Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения (`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего `main`. Определение замкнуто: имён, использованных и не определённых в нём, нет (`external 0`). Слова — в порядке определения.

**Слов в ядре: 949** (определение `:` — 475, переменная — 315, генератор — 72, данные `create` — 47, константа — 24, цифра (литерал) — 10, основание — 6).

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
| 19 | `+!` | определение `:` | src/prelude.fth:24 | 69 |  |
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
| 88 | `lay-branch-bit` | определение `:` | src/backend.fth:114 | 21 |  |
| 89 | `lay-branch-step` | определение `:` | src/backend.fth:115 | 3 |  |
| 90 | `lay-group` | определение `:` | src/backend.fth:116 | 5 |  |
| 91 | `lay-layer-cell` | определение `:` | src/backend.fth:119 | 41 |  |
| 92 | `lay-next!` | определение `:` | src/backend.fth:120 | 19 |  |
| 93 | `lay-count` | определение `:` | src/backend.fth:121 | 7 |  |
| 94 | `lay-row-addr` | определение `:` | src/backend.fth:122 | 4 |  |
| 95 | `lay-pending@` | определение `:` | src/backend.fth:123 | 5 |  |
| 96 | `lay-encode-layer` | определение `:` | src/backend.fth:124 | 1 |  |
| 97 | `lay-on-write` | переменная | src/backend.fth:130 | 6 |  |
| 98 | `lay-write` | определение `:` | src/backend.fth:131 | 2 |  |
| 99 | `lay-write-oldest` | определение `:` | src/backend.fth:134 | 1 |  |
| 100 | `lay-new-record` | основание | src/backend.fth:135 | 10 | основание: слой: новый слой в ячейке; определение инструкции — она сама |
| 101 | `lay-lone` | основание | src/backend.fth:139 | 5 | основание: слой: отдельный слой в новой ячейке; определение инструкции — она сама |
| 102 | `lay-seq` | определение `:` | src/backend.fth:140 | 9 |  |
| 103 | `lay-last` | определение `:` | src/backend.fth:141 | 4 |  |
| 104 | `lay-layer` | основание | src/backend.fth:142 | 85 | основание: слой: следующий слой последовательности; определение инструкции — она сама |
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
| 172 | `dj-prove` | определение `:` | src/backend.fth:284 | 3 |  |
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
| 187 | `lay-cell-bit` | определение `:` | src/compute.fth:11 | 3 |  |
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
| 293 | `fc-cellb` | константа | src/forthc.fth:6 | 4 |  |
| 294 | `fc-l` | константа | src/forthc.fth:6 | 1 |  |
| 295 | `fc-a` | константа | src/forthc.fth:6 | 2 |  |
| 296 | `fc-d` | переменная | src/forthc.fth:8 | 3 |  |
| 297 | `fc-first` | переменная | src/forthc.fth:8 | 3 |  |
| 298 | `fc-guard` | переменная | src/forthc.fth:10 | 21 |  |
| 299 | `fc-bbits` | константа | src/forthc.fth:16 | 7 |  |
| 300 | `fc-abits` | константа | src/forthc.fth:16 | 5 |  |
| 301 | `fc-ebits` | константа | src/forthc.fth:16 | 2 |  |
| 302 | `fc-etab` | константа | src/forthc.fth:16 | 5 |  |
| 303 | `fc-rbits` | константа | src/forthc.fth:17 | 7 |  |
| 304 | `fc-rtab` | константа | src/forthc.fth:17 | 4 |  |
| 305 | `fc-layout` | определение `:` | src/forthc.fth:18 | 1 |  |
| 306 | `fc-d+` | определение `:` | src/forthc.fth:20 | 27 |  |
| 307 | `fc-sp` | определение `:` | src/forthc.fth:21 | 6 |  |
| 308 | `fc-rp` | определение `:` | src/forthc.fth:21 | 18 |  |
| 309 | `fc-handler` | определение `:` | src/forthc.fth:21 | 6 |  |
| 310 | `fc-code` | определение `:` | src/forthc.fth:21 | 4 |  |
| 311 | `fc-regs` | определение `:` | src/forthc.fth:22 | 2 |  |
| 312 | `fc-nregs` | константа | src/forthc.fth:22 | 2 |  |
| 313 | `fc-tmp` | определение `:` | src/forthc.fth:23 | 12 |  |
| 314 | `fc-xr` | определение `:` | src/forthc.fth:23 | 10 |  |
| 315 | `fc-z` | определение `:` | src/forthc.fth:23 | 4 |  |
| 316 | `fc-idx` | определение `:` | src/forthc.fth:23 | 5 |  |
| 317 | `fc-ma` | определение `:` | src/forthc.fth:24 | 6 |  |
| 318 | `fc-mb` | определение `:` | src/forthc.fth:24 | 6 |  |
| 319 | `fc-mp` | определение `:` | src/forthc.fth:24 | 2 |  |
| 320 | `fc-mq` | определение `:` | src/forthc.fth:24 | 3 |  |
| 321 | `fc-mr` | определение `:` | src/forthc.fth:24 | 3 |  |
| 322 | `fc-zero` | определение `:` | src/forthc.fth:25 | 12 |  |
| 323 | `fc-consts` | определение `:` | src/forthc.fth:25 | 3 |  |
| 324 | `fc-sw` | определение `:` | src/forthc.fth:26 | 2 |  |
| 325 | `fc-su` | определение `:` | src/forthc.fth:26 | 1 |  |
| 326 | `fc-key` | определение `:` | src/forthc.fth:26 | 3 |  |
| 327 | `fc-bp` | определение `:` | src/forthc.fth:26 | 2 |  |
| 328 | `fc-tab` | определение `:` | src/forthc.fth:27 | 1 |  |
| 329 | `fc-stk` | определение `:` | src/forthc.fth:27 | 3 |  |
| 330 | `fc-rstk` | определение `:` | src/forthc.fth:28 | 16 |  |
| 331 | `fc-scr0` | определение `:` | src/forthc.fth:28 | 1 |  |
| 332 | `fc-links` | определение `:` | src/forthc.fth:29 | 2 |  |
| 333 | `fc-max-links` | константа | src/forthc.fth:29 | 1 |  |
| 334 | `fc-link-chunk` | константа | src/forthc.fth:29 | 2 |  |
| 335 | `fc-mem` | определение `:` | src/forthc.fth:30 | 7 |  |
| 336 | `fc-mw` | константа | src/forthc.fth:30 | 2 |  |
| 337 | `fc-htab` | определение `:` | src/forthc.fth:30 | 1 |  |
| 338 | `fc-data-start` | константа | src/forthc.fth:31 | 1 |  |
| 339 | `fc-off` | данные `create` | src/forthc.fth:33 | 2 |  |
| 340 | `fc-oc` | переменная | src/forthc.fth:33 | 2 |  |
| 341 | `fc-t-rev8` | переменная | src/forthc.fth:34 | 3 |  |
| 342 | `fc-t-zero32` | переменная | src/forthc.fth:34 | 2 |  |
| 343 | `fc-t-nz2` | переменная | src/forthc.fth:34 | 2 |  |
| 344 | `fc-t-lt32` | переменная | src/forthc.fth:34 | 2 |  |
| 345 | `fc-t-xr2` | переменная | src/forthc.fth:35 | 2 |  |
| 346 | `fc-t-ult32` | переменная | src/forthc.fth:35 | 2 |  |
| 347 | `fc-t-bytepos` | переменная | src/forthc.fth:35 | 2 |  |
| 348 | `fc-off@` | определение `:` | src/forthc.fth:36 | 3 |  |
| 349 | `fc-off-table` | определение `:` | src/forthc.fth:37 | 1 |  |
| 350 | `fc-rev-entry` | определение `:` | src/forthc.fth:40 | 1 |  |
| 351 | `fc-zero-entry` | определение `:` | src/forthc.fth:41 | 1 |  |
| 352 | `fc-nz-entry` | определение `:` | src/forthc.fth:42 | 1 |  |
| 353 | `fc-lt-entry` | определение `:` | src/forthc.fth:43 | 1 |  |
| 354 | `fc-xr2-entry` | определение `:` | src/forthc.fth:46 | 1 |  |
| 355 | `fc-ult-entry` | определение `:` | src/forthc.fth:47 | 1 |  |
| 356 | `fc-bytepos-entry` | определение `:` | src/forthc.fth:48 | 1 |  |
| 357 | `fc-tables` | определение `:` | src/forthc.fth:49 | 1 |  |
| 358 | `fc-mul4-entry` | определение `:` | src/forthc.fth:60 | 1 |  |
| 359 | `fc-qsel-entry` | определение `:` | src/forthc.fth:63 | 1 |  |
| 360 | `fc-max-consts` | переменная | src/forthc.fth:66 | 5 | вход бута (хост) |
| 361 | `fc-ck` | переменная | src/forthc.fth:66 | 3 |  |
| 362 | `fc-nconsts` | переменная | src/forthc.fth:66 | 7 |  |
| 363 | `fc-nbuckets` | переменная | src/forthc.fth:67 | 9 | вход бута (хост) |
| 364 | `fc-cbk` | переменная | src/forthc.fth:67 | 3 |  |
| 365 | `fc-ck@` | определение `:` | src/forthc.fth:68 | 3 |  |
| 366 | `fc-chash` | определение `:` | src/forthc.fth:69 | 1 |  |
| 367 | `fc-cb` | переменная | src/forthc.fth:70 | 3 |  |
| 368 | `fc-const2` | определение `:` | src/forthc.fth:71 | 1 |  |
| 369 | `fc-const` | определение `:` | src/forthc.fth:81 | 5 |  |
| 370 | `fc-lit` | определение `:` | src/forthc.fth:84 | 3 |  |
| 371 | `fc-bit0` | определение `:` | src/forthc.fth:85 | 1 |  |
| 372 | `fc-bit1` | определение `:` | src/forthc.fth:86 | 1 |  |
| 373 | `fc-length` | определение `:` | src/forthc.fth:87 | 1 |  |
| 374 | `fc-lit-of` | определение `:` | src/forthc.fth:88 | 2 |  |
| 375 | `fc-load` | определение `:` | src/forthc.fth:90 | 2 |  |
| 376 | `fc-nlinks` | переменная | src/forthc.fth:92 | 5 |  |
| 377 | `fc-link-buf` | переменная | src/forthc.fth:92 | 4 |  |
| 378 | `fc-nbuf` | переменная | src/forthc.fth:92 | 8 |  |
| 379 | `fc-put-links` | определение `:` | src/forthc.fth:93 | 2 |  |
| 380 | `fc-link-pair` | определение `:` | src/forthc.fth:97 | 2 |  |
| 381 | `fc-link-const` | определение `:` | src/forthc.fth:102 | 1 |  |
| 382 | `fc-eight` | данные `create` | src/forthc.fth:103 | 7 |  |
| 383 | `fc-zeros` | данные `create` | src/forthc.fth:103 | 5 |  |
| 384 | `fc-put-consts` | определение `:` | src/forthc.fth:104 | 1 |  |
| 385 | `fc-cache` | данные `create` | src/forthc.fth:111 | 8 |  |
| 386 | `fc-n` | переменная | src/forthc.fth:111 | 31 |  |
| 387 | `fc-pin` | данные `create` | src/forthc.fth:112 | 10 |  |
| 388 | `fc-npin` | переменная | src/forthc.fth:112 | 21 |  |
| 389 | `fc-c@` | определение `:` | src/forthc.fth:113 | 8 |  |
| 390 | `fc-push` | определение `:` | src/forthc.fth:114 | 30 |  |
| 391 | `fc-pop1` | определение `:` | src/forthc.fth:115 | 30 |  |
| 392 | `fc-in?` | определение `:` | src/forthc.fth:116 | 3 |  |
| 393 | `fc-reg` | определение `:` | src/forthc.fth:117 | 18 |  |
| 394 | `fc-reg-for-pop` | определение `:` | src/forthc.fth:122 | 1 |  |
| 395 | `fc-scr` | переменная | src/forthc.fth:123 | 3 |  |
| 396 | `fc-scratch` | определение `:` | src/forthc.fth:124 | 11 |  |
| 397 | `fc-offs` | данные `create` | src/forthc.fth:127 | 5 |  |
| 398 | `fc-noff` | переменная | src/forthc.fth:127 | 9 |  |
| 399 | `fc-ptr` | переменная | src/forthc.fth:127 | 4 |  |
| 400 | `fc-iw` | переменная | src/forthc.fth:128 | 4 |  |
| 401 | `fc-adjust` | определение `:` | src/forthc.fth:129 | 7 |  |
| 402 | `fc-prow` | данные `create` | src/forthc.fth:135 | 2 |  |
| 403 | `fc-nrow` | переменная | src/forthc.fth:135 | 8 |  |
| 404 | `fc-pl` | данные `create` | src/forthc.fth:136 | 2 |  |
| 405 | `fc-pslot` | данные `create` | src/forthc.fth:136 | 2 |  |
| 406 | `fc-rl` | переменная | src/forthc.fth:137 | 3 |  |
| 407 | `fc-f0` | переменная | src/forthc.fth:137 | 2 |  |
| 408 | `fc-f1` | переменная | src/forthc.fth:137 | 2 |  |
| 409 | `fc-psh` | переменная | src/forthc.fth:137 | 2 |  |
| 410 | `fc-row+` | определение `:` | src/forthc.fth:138 | 3 |  |
| 411 | `fc-4@` | определение `:` | src/forthc.fth:140 | 3 |  |
| 412 | `fc-patched` | определение `:` | src/forthc.fth:141 | 3 |  |
| 413 | `fc-popped` | данные `create` | src/forthc.fth:152 | 2 |  |
| 414 | `fc-srcs` | данные `create` | src/forthc.fth:152 | 16 |  |
| 415 | `fc-nsrc` | переменная | src/forthc.fth:152 | 21 |  |
| 416 | `fc-mbase` | переменная | src/forthc.fth:153 | 8 |  |
| 417 | `fc-mptr` | переменная | src/forthc.fth:153 | 4 |  |
| 418 | `fc-mn` | переменная | src/forthc.fth:153 | 7 |  |
| 419 | `fc-mw2` | переменная | src/forthc.fth:153 | 6 |  |
| 420 | `fc-popped@` | определение `:` | src/forthc.fth:154 | 10 |  |
| 421 | `fc-shift` | определение `:` | src/forthc.fth:155 | 4 |  |
| 422 | `fc-mem-pop` | определение `:` | src/forthc.fth:156 | 5 |  |
| 423 | `fc-push-group` | определение `:` | src/forthc.fth:164 | 2 |  |
| 424 | `fc-dup-at` | определение `:` | src/forthc.fth:170 | 1 |  |
| 425 | `fc-rest` | данные `create` | src/forthc.fth:172 | 2 |  |
| 426 | `fc-nrest` | переменная | src/forthc.fth:172 | 3 |  |
| 427 | `fc-mem-push` | определение `:` | src/forthc.fth:173 | 8 |  |
| 428 | `fc-src1` | определение `:` | src/forthc.fth:179 | 3 |  |
| 429 | `fc-need` | определение `:` | src/forthc.fth:180 | 15 |  |
| 430 | `fc-spill` | определение `:` | src/forthc.fth:186 | 19 |  |
| 431 | `fc-pop` | определение `:` | src/forthc.fth:192 | 13 |  |
| 432 | `fc-max-log` | константа | src/forthc.fth:197 | 2 |  |
| 433 | `fc-max-notes` | константа | src/forthc.fth:197 | 6 |  |
| 434 | `fc-log` | переменная | src/forthc.fth:198 | 3 |  |
| 435 | `fc-nlog` | переменная | src/forthc.fth:198 | 5 |  |
| 436 | `fc-decs` | переменная | src/forthc.fth:198 | 2 |  |
| 437 | `fc-ndec` | переменная | src/forthc.fth:198 | 6 |  |
| 438 | `fc-calls` | переменная | src/forthc.fth:198 | 2 |  |
| 439 | `fc-ncall` | переменная | src/forthc.fth:198 | 6 |  |
| 440 | `fc-pend` | переменная | src/forthc.fth:199 | 2 |  |
| 441 | `fc-npend` | переменная | src/forthc.fth:199 | 9 |  |
| 442 | `fc-unknown` | переменная | src/forthc.fth:199 | 7 |  |
| 443 | `fc-lc` | переменная | src/forthc.fth:200 | 3 |  |
| 444 | `fc-lb` | переменная | src/forthc.fth:200 | 3 |  |
| 445 | `fc-row-n` | определение `:` | src/forthc.fth:201 | 1 |  |
| 446 | `fc-mem-row?` | определение `:` | src/forthc.fth:202 | 1 |  |
| 447 | `fc-log-layer` | определение `:` | src/forthc.fth:203 | 2 |  |
| 448 | `fc-log-begin` | определение `:` | src/forthc.fth:215 | 3 |  |
| 449 | `fc-log-end` | определение `:` | src/forthc.fth:217 | 4 |  |
| 450 | `fc-by-execution` | определение `:` | src/forthc.fth:218 | 8 |  |
| 451 | `fc-dec@` | определение `:` | src/forthc.fth:219 | 2 |  |
| 452 | `fc-call@` | определение `:` | src/forthc.fth:220 | 2 |  |
| 453 | `fc-log-decision` | определение `:` | src/forthc.fth:221 | 2 |  |
| 454 | `fc-log-call` | определение `:` | src/forthc.fth:225 | 2 |  |
| 455 | `fc-callee` | переменная | src/forthc.fth:229 | 4 |  |
| 456 | `fc-live` | переменная | src/forthc.fth:231 | 7 |  |
| 457 | `fc-tramp` | переменная | src/forthc.fth:231 | 8 |  |
| 458 | `fc-ex` | переменная | src/forthc.fth:231 | 4 |  |
| 459 | `fc-thrower` | переменная | src/forthc.fth:231 | 4 |  |
| 460 | `fc-jump` | определение `:` | src/forthc.fth:232 | 7 |  |
| 461 | `fc-end` | определение `:` | src/forthc.fth:233 | 14 |  |
| 462 | `fc-begin-block` | определение `:` | src/forthc.fth:234 | 24 |  |
| 463 | `fc-rows1` | определение `:` | src/forthc.fth:238 | 15 |  |
| 464 | `fc-nonzero` | определение `:` | src/forthc.fth:239 | 2 |  |
| 465 | `fc-branch` | определение `:` | src/forthc.fth:242 | 6 |  |
| 466 | `fc-rtab-at` | определение `:` | src/forthc.fth:243 | 1 |  |
| 467 | `fc-nret` | переменная | src/forthc.fth:244 | 6 |  |
| 468 | `fc-ret-link` | определение `:` | src/forthc.fth:248 | 4 |  |
| 469 | `fc-ret-base` | определение `:` | src/forthc.fth:253 | 4 |  |
| 470 | `fc-call` | определение `:` | src/forthc.fth:254 | 4 |  |
| 471 | `fc-v0` | переменная | src/forthc.fth:258 | 4 |  |
| 472 | `fc-v1` | переменная | src/forthc.fth:258 | 4 |  |
| 473 | `fc-jw` | определение `:` | src/forthc.fth:259 | 2 |  |
| 474 | `fc-xw` | определение `:` | src/forthc.fth:260 | 2 |  |
| 475 | `fc-xoff` | определение `:` | src/forthc.fth:261 | 2 |  |
| 476 | `fc-etab-at` | определение `:` | src/forthc.fth:262 | 1 |  |
| 477 | `fc-ex-base` | определение `:` | src/forthc.fth:263 | 1 |  |
| 478 | `fc-call-indirect` | определение `:` | src/forthc.fth:264 | 2 |  |
| 479 | `fc-push-frame` | определение `:` | src/forthc.fth:271 | 2 |  |
| 480 | `fc-link-copy` | определение `:` | src/forthc.fth:274 | 1 |  |
| 481 | `fc-restore` | определение `:` | src/forthc.fth:280 | 3 |  |
| 482 | `fc-build-thrower` | определение `:` | src/forthc.fth:282 | 1 |  |
| 483 | `fc-throw` | определение `:` | src/forthc.fth:288 | 1 |  |
| 484 | `fc-catch` | определение `:` | src/forthc.fth:291 | 1 |  |
| 485 | `fc-ret-p` | переменная | src/forthc.fth:300 | 4 |  |
| 486 | `fc-ret-l` | переменная | src/forthc.fth:300 | 6 |  |
| 487 | `fc-rs0` | переменная | src/forthc.fth:300 | 3 |  |
| 488 | `fc-rs1` | переменная | src/forthc.fth:300 | 3 |  |
| 489 | `fc-ret-m` | переменная | src/forthc.fth:300 | 3 |  |
| 490 | `fc-ret-t` | переменная | src/forthc.fth:300 | 3 |  |
| 491 | `fc-ret-patch` | определение `:` | src/forthc.fth:301 | 4 |  |
| 492 | `fc-ret-masked` | определение `:` | src/forthc.fth:303 | 1 |  |
| 493 | `fc-ret` | определение `:` | src/forthc.fth:309 | 3 |  |
| 494 | `fc-ca` | переменная | src/forthc.fth:321 | 3 |  |
| 495 | `fc-cl0` | переменная | src/forthc.fth:321 | 4 |  |
| 496 | `fc-cl1` | переменная | src/forthc.fth:321 | 4 |  |
| 497 | `fc-cr` | переменная | src/forthc.fth:321 | 4 |  |
| 498 | `fc-cslot` | переменная | src/forthc.fth:321 | 3 |  |
| 499 | `fc-csh` | переменная | src/forthc.fth:321 | 2 |  |
| 500 | `fc-cv` | переменная | src/forthc.fth:322 | 3 |  |
| 501 | `fc-cres` | переменная | src/forthc.fth:322 | 6 |  |
| 502 | `fc-cmode` | переменная | src/forthc.fth:322 | 6 |  |
| 503 | `fc-ar` | переменная | src/forthc.fth:322 | 5 |  |
| 504 | `fc-chk-read` | определение `:` | src/forthc.fth:323 | 1 |  |
| 505 | `fc-chk-seg` | определение `:` | src/forthc.fth:325 | 1 |  |
| 506 | `fc-as` | переменная | src/forthc.fth:328 | 2 |  |
| 507 | `fc-af` | переменная | src/forthc.fth:328 | 2 |  |
| 508 | `fc-al0` | переменная | src/forthc.fth:328 | 2 |  |
| 509 | `fc-al1` | переменная | src/forthc.fth:328 | 2 |  |
| 510 | `fc-apl` | переменная | src/forthc.fth:328 | 3 |  |
| 511 | `fc-afld` | переменная | src/forthc.fth:328 | 3 |  |
| 512 | `fc-access-patch` | определение `:` | src/forthc.fth:329 | 2 |  |
| 513 | `fc-access` | определение `:` | src/forthc.fth:334 | 1 |  |
| 514 | `fc-width` | определение `:` | src/forthc.fth:336 | 4 |  |
| 515 | `fc-check` | определение `:` | src/forthc.fth:337 | 4 |  |
| 516 | `fc-ring` | константа | src/forthc.fth:353 | 6 |  |
| 517 | `fc-window` | константа | src/forthc.fth:353 | 1 |  |
| 518 | `fc-sl` | данные `create` | src/forthc.fth:354 | 2 |  |
| 519 | `fc-stabs` | переменная | src/forthc.fth:354 | 2 |  |
| 520 | `fc-slen` | переменная | src/forthc.fth:355 | 7 |  |
| 521 | `fc-slow` | переменная | src/forthc.fth:355 | 4 |  |
| 522 | `fc-sinit` | определение `:` | src/forthc.fth:356 | 2 |  |
| 523 | `fc-sbegin` | определение `:` | src/forthc.fth:357 | 2 |  |
| 524 | `fc-tabs` | определение `:` | src/forthc.fth:358 | 3 |  |
| 525 | `fc-at` | определение `:` | src/forthc.fth:359 | 4 |  |
| 526 | `fc-has?` | определение `:` | src/forthc.fth:364 | 1 |  |
| 527 | `fc-tab+` | определение `:` | src/forthc.fth:365 | 1 |  |
| 528 | `fc-prw` | данные `create` | src/forthc.fth:366 | 6 |  |
| 529 | `fc-ptab` | переменная | src/forthc.fth:366 | 5 |  |
| 530 | `fc-place` | определение `:` | src/forthc.fth:367 | 3 |  |
| 531 | `fc-scopy` | определение `:` | src/forthc.fth:377 | 9 |  |
| 532 | `fc-segs` | данные `create` | src/forthc.fth:378 | 2 |  |
| 533 | `fc-nseg` | переменная | src/forthc.fth:378 | 5 |  |
| 534 | `fc-pp` | данные `create` | src/forthc.fth:379 | 2 |  |
| 535 | `fc-npp` | переменная | src/forthc.fth:379 | 4 |  |
| 536 | `fc-latest` | переменная | src/forthc.fth:379 | 4 |  |
| 537 | `fc-sga` | переменная | src/forthc.fth:379 | 14 |  |
| 538 | `fc-ltab` | переменная | src/forthc.fth:380 | 3 |  |
| 539 | `fc-ls` | переменная | src/forthc.fth:380 | 3 |  |
| 540 | `fc-lw` | переменная | src/forthc.fth:380 | 3 |  |
| 541 | `fc-ldst` | переменная | src/forthc.fth:380 | 2 |  |
| 542 | `fc-seg+` | определение `:` | src/forthc.fth:381 | 21 |  |
| 543 | `fc-pp+` | определение `:` | src/forthc.fth:384 | 1 |  |
| 544 | `fc-slookup` | определение `:` | src/forthc.fth:385 | 8 |  |
| 545 | `fc-nx` | переменная | src/forthc.fth:403 | 3 |  |
| 546 | `fc-nv` | переменная | src/forthc.fth:403 | 2 |  |
| 547 | `fc-nt` | переменная | src/forthc.fth:403 | 3 |  |
| 548 | `fc-negate-chain` | определение `:` | src/forthc.fth:404 | 1 |  |
| 549 | `fc-gw` | переменная | src/forthc.fth:410 | 4 |  |
| 550 | `fc-gs` | переменная | src/forthc.fth:410 | 2 |  |
| 551 | `fc-gs2` | переменная | src/forthc.fth:410 | 2 |  |
| 552 | `fc-gts` | переменная | src/forthc.fth:410 | 6 |  |
| 553 | `fc-gdst` | переменная | src/forthc.fth:410 | 2 |  |
| 554 | `fc-negate-select` | определение `:` | src/forthc.fth:411 | 4 |  |
| 555 | `fc-sfinish` | определение `:` | src/forthc.fth:416 | 2 |  |
| 556 | `fc-pr` | данные `create` | src/forthc.fth:419 | 2 |  |
| 557 | `fc-xs` | данные `create` | src/forthc.fth:419 | 2 |  |
| 558 | `fc-m4` | переменная | src/forthc.fth:420 | 2 |  |
| 559 | `fc-mj` | переменная | src/forthc.fth:420 | 11 |  |
| 560 | `fc-mk` | переменная | src/forthc.fth:420 | 6 |  |
| 561 | `fc-p@` | определение `:` | src/forthc.fth:421 | 3 |  |
| 562 | `fc-p!` | определение `:` | src/forthc.fth:422 | 1 |  |
| 563 | `fc-x@` | определение `:` | src/forthc.fth:423 | 3 |  |
| 564 | `fc-x!` | определение `:` | src/forthc.fth:424 | 2 |  |
| 565 | `fc-build-mul` | определение `:` | src/forthc.fth:425 | 1 |  |
| 566 | `fc-sub` | данные `create` | src/forthc.fth:443 | 2 |  |
| 567 | `fc-qsel` | переменная | src/forthc.fth:443 | 2 |  |
| 568 | `fc-absa` | переменная | src/forthc.fth:444 | 5 |  |
| 569 | `fc-absb` | переменная | src/forthc.fth:444 | 3 |  |
| 570 | `fc-ta` | переменная | src/forthc.fth:444 | 4 |  |
| 571 | `fc-tb` | переменная | src/forthc.fth:444 | 2 |  |
| 572 | `fc-rem` | переменная | src/forthc.fth:445 | 7 |  |
| 573 | `fc-tr` | переменная | src/forthc.fth:445 | 7 |  |
| 574 | `fc-q` | переменная | src/forthc.fth:445 | 3 |  |
| 575 | `fc-tq` | переменная | src/forthc.fth:445 | 4 |  |
| 576 | `fc-k` | переменная | src/forthc.fth:445 | 5 |  |
| 577 | `fc-w` | переменная | src/forthc.fth:446 | 14 |  |
| 578 | `fc-lo` | переменная | src/forthc.fth:446 | 7 |  |
| 579 | `fc-tlo` | переменная | src/forthc.fth:446 | 7 |  |
| 580 | `fc-t0` | переменная | src/forthc.fth:446 | 4 |  |
| 581 | `fc-t1` | переменная | src/forthc.fth:446 | 4 |  |
| 582 | `fc-qr` | переменная | src/forthc.fth:446 | 4 |  |
| 583 | `fc-tqk` | переменная | src/forthc.fth:446 | 3 |  |
| 584 | `fc-sub@` | определение `:` | src/forthc.fth:447 | 7 |  |
| 585 | `fc-step` | определение `:` | src/forthc.fth:448 | 3 |  |
| 586 | `fc-div-step` | определение `:` | src/forthc.fth:455 | 1 |  |
| 587 | `fc-build-div` | определение `:` | src/forthc.fth:472 | 1 |  |
| 588 | `fc-mul-entry` | переменная | src/forthc.fth:488 | 4 |  |
| 589 | `fc-mul-exit` | переменная | src/forthc.fth:488 | 2 |  |
| 590 | `fc-div-entry` | переменная | src/forthc.fth:488 | 5 |  |
| 591 | `fc-div-exit` | переменная | src/forthc.fth:488 | 4 |  |
| 592 | `fc-hl` | переменная | src/forthc.fth:489 | 5 |  |
| 593 | `fc-hcont` | переменная | src/forthc.fth:489 | 4 |  |
| 594 | `fc-mul-cost` | данные `create` | src/forthc.fth:490 | 2 |  |
| 595 | `fc-div-cost` | данные `create` | src/forthc.fth:490 | 2 |  |
| 596 | `fc-row-or-new` | определение `:` | src/forthc.fth:491 | 2 |  |
| 597 | `fc-call-helper` | определение `:` | src/forthc.fth:493 | 4 |  |
| 598 | `fc-result1` | определение `:` | src/forthc.fth:503 | 3 |  |
| 599 | `fc-s1` | переменная | src/forthc.fth:504 | 2 |  |
| 600 | `fc-s2` | переменная | src/forthc.fth:504 | 2 |  |
| 601 | `fc-r1` | переменная | src/forthc.fth:504 | 2 |  |
| 602 | `fc-result2` | определение `:` | src/forthc.fth:505 | 1 |  |
| 603 | `fc-pexit` | переменная | src/forthc.fth:512 | 2 |  |
| 604 | `fc-ptramp` | переменная | src/forthc.fth:512 | 2 |  |
| 605 | `fc-pd` | переменная | src/forthc.fth:512 | 5 |  |
| 606 | `fc-pc` | переменная | src/forthc.fth:512 | 5 |  |
| 607 | `fc-ends` | переменная | src/forthc.fth:512 | 3 |  |
| 608 | `fc-pb` | переменная | src/forthc.fth:513 | 5 |  |
| 609 | `fc-pcp` | переменная | src/forthc.fth:513 | 5 |  |
| 610 | `fc-pln` | переменная | src/forthc.fth:513 | 5 |  |
| 611 | `fc-pk` | переменная | src/forthc.fth:513 | 4 |  |
| 612 | `fc-pcall` | переменная | src/forthc.fth:513 | 3 |  |
| 613 | `fc-best` | данные `create` | src/forthc.fth:514 | 10 |  |
| 614 | `fc-pend@` | определение `:` | src/forthc.fth:515 | 7 |  |
| 615 | `fc-reach` | определение `:` | src/forthc.fth:516 | 2 |  |
| 616 | `fc-take` | определение `:` | src/forthc.fth:525 | 1 |  |
| 617 | `fc-end-path` | определение `:` | src/forthc.fth:532 | 1 |  |
| 618 | `fc-to` | определение `:` | src/forthc.fth:536 | 2 |  |
| 619 | `fc-node` | определение `:` | src/forthc.fth:540 | 1 |  |
| 620 | `fc-path` | определение `:` | src/forthc.fth:559 | 3 |  |
| 621 | `fc-cost!` | определение `:` | src/forthc.fth:568 | 3 |  |
| 622 | `fc-ll` | переменная | src/forthc.fth:570 | 6 |  |
| 623 | `fc-llr` | переменная | src/forthc.fth:570 | 3 |  |
| 624 | `fc-llv` | переменная | src/forthc.fth:570 | 3 |  |
| 625 | `fc-plit` | переменная | src/forthc.fth:570 | 6 |  |
| 626 | `fc-plr` | переменная | src/forthc.fth:570 | 4 |  |
| 627 | `fc-plv` | переменная | src/forthc.fth:570 | 6 |  |
| 628 | `fc-literal` | определение `:` | src/forthc.fth:571 | 14 |  |
| 629 | `fc-or-zero` | определение `:` | src/forthc.fth:573 | 2 |  |
| 630 | `fc-ba` | переменная | src/forthc.fth:576 | 13 |  |
| 631 | `fc-bb` | переменная | src/forthc.fth:576 | 13 |  |
| 632 | `fc-br` | переменная | src/forthc.fth:576 | 9 |  |
| 633 | `fc-binary` | определение `:` | src/forthc.fth:577 | 10 |  |
| 634 | `fc-r-at` | определение `:` | src/forthc.fth:601 | 2 |  |
| 635 | `fc-pop-pinned` | определение `:` | src/forthc.fth:604 | 3 |  |
| 636 | `fc-sk` | переменная | src/forthc.fth:605 | 12 |  |
| 637 | `fc-shift-copy` | определение `:` | src/forthc.fth:606 | 2 |  |
| 638 | `fc-inc` | определение `:` | src/forthc.fth:610 | 3 |  |
| 639 | `fc-read-key` | определение `:` | src/forthc.fth:613 | 1 |  |
| 640 | `fc-text` | переменная | src/forthc.fth:618 | 13 |  |
| 641 | `fc-tlen` | переменная | src/forthc.fth:618 | 14 |  |
| 642 | `fc-pos` | переменная | src/forthc.fth:618 | 24 |  |
| 643 | `fc-text-size` | переменная | src/forthc.fth:618 | 6 | вход бута (хост) |
| 644 | `fc-tok` | данные `create` | src/forthc.fth:619 | 19 |  |
| 645 | `fc-tl` | переменная | src/forthc.fth:619 | 24 |  |
| 646 | `fc-reset` | определение `:` | src/forthc.fth:620 | 3 |  |
| 647 | `fc-append` | определение `:` | src/forthc.fth:621 | 1 |  |
| 648 | `fc\|` | определение `:` | src/forthc.fth:625 | 1 | вход бута (хост) |
| 649 | `fc-ch` | определение `:` | src/forthc.fth:626 | 5 |  |
| 650 | `fc-more?` | определение `:` | src/forthc.fth:627 | 6 |  |
| 651 | `fc-next` | определение `:` | src/forthc.fth:628 | 8 |  |
| 652 | `fc-next!` | определение `:` | src/forthc.fth:636 | 10 |  |
| 653 | `fc-is?` | определение `:` | src/forthc.fth:637 | 5 |  |
| 654 | `fc-raw` | определение `:` | src/forthc.fth:640 | 1 |  |
| 655 | `fc-string-token` | определение `:` | src/forthc.fth:641 | 1 |  |
| 656 | `fc-names-size` | переменная | src/forthc.fth:646 | 5 | вход бута (хост) |
| 657 | `fc-max-words` | переменная | src/forthc.fth:646 | 5 | вход бута (хост) |
| 658 | `fc-names` | переменная | src/forthc.fth:647 | 3 |  |
| 659 | `fc-names-used` | переменная | src/forthc.fth:647 | 5 |  |
| 660 | `fc-wt` | переменная | src/forthc.fth:648 | 5 |  |
| 661 | `fc-nwords` | переменная | src/forthc.fth:648 | 12 |  |
| 662 | `fc-wbk` | переменная | src/forthc.fth:648 | 3 |  |
| 663 | `fc-wt@` | определение `:` | src/forthc.fth:651 | 6 |  |
| 664 | `fc-proved` | данные `create` | src/forthc.fth:653 | 2 |  |
| 665 | `fc-unproved` | данные `create` | src/forthc.fth:654 | 2 |  |
| 666 | `fc-mechanisms` | определение `:` | src/forthc.fth:655 | 1 |  |
| 667 | `fc-xt` | определение `:` | src/forthc.fth:660 | 5 |  |
| 668 | `fc-xtn` | определение `:` | src/forthc.fth:662 | 2 |  |
| 669 | `fc-hash` | определение `:` | src/forthc.fth:663 | 2 |  |
| 670 | `fc-define` | определение `:` | src/forthc.fth:665 | 6 |  |
| 671 | `fc-lookup` | определение `:` | src/forthc.fth:670 | 5 |  |
| 672 | `fc-find` | определение `:` | src/forthc.fth:674 | 6 |  |
| 673 | `fc-word-of` | определение `:` | src/forthc.fth:676 | 2 |  |
| 674 | `fc-cost` | определение `:` | src/forthc.fth:684 | 1 |  |
| 675 | `fc-proved?` | определение `:` | src/forthc.fth:687 | 1 |  |
| 676 | `fc-here` | переменная | src/forthc.fth:689 | 9 |  |
| 677 | `fc-word` | переменная | src/forthc.fth:689 | 13 |  |
| 678 | `fc-uses` | переменная | src/forthc.fth:689 | 16 |  |
| 679 | `fc-rt` | переменная | src/forthc.fth:690 | 7 |  |
| 680 | `fc-rta` | переменная | src/forthc.fth:690 | 7 |  |
| 681 | `fc-ctl` | данные `create` | src/forthc.fth:691 | 1 |  |
| 682 | `fc-nctl` | переменная | src/forthc.fth:691 | 12 |  |
| 683 | `fc-cleave` | переменная | src/forthc.fth:691 | 2 |  |
| 684 | `fc-ctl@` | определение `:` | src/forthc.fth:692 | 4 |  |
| 685 | `fc-ctl+` | определение `:` | src/forthc.fth:693 | 6 |  |
| 686 | `fc-ctl-` | определение `:` | src/forthc.fth:695 | 7 |  |
| 687 | `fc-do-entry` | определение `:` | src/forthc.fth:697 | 1 |  |
| 688 | `fc-ctl-leave` | определение `:` | src/forthc.fth:699 | 1 |  |
| 689 | `fc-ctl-leave!` | определение `:` | src/forthc.fth:700 | 1 |  |
| 690 | `fc-loop-leave` | определение `:` | src/forthc.fth:701 | 1 |  |
| 691 | `fc-align` | определение `:` | src/forthc.fth:702 | 2 |  |
| 692 | `fc-check-here` | определение `:` | src/forthc.fth:703 | 3 |  |
| 693 | `fc-define-data` | определение `:` | src/forthc.fth:704 | 2 |  |
| 694 | `fc-sat` | переменная | src/forthc.fth:705 | 3 |  |
| 695 | `fc-store-string` | определение `:` | src/forthc.fth:706 | 1 |  |
| 696 | `fc-ct` | данные `create` | src/forthc.fth:711 | 3 |  |
| 697 | `fc-nct` | переменная | src/forthc.fth:711 | 11 |  |
| 698 | `fc-ct+` | определение `:` | src/forthc.fth:712 | 15 |  |
| 699 | `fc-ct-` | определение `:` | src/forthc.fth:713 | 9 |  |
| 700 | `fc-ct2` | определение `:` | src/forthc.fth:714 | 8 |  |
| 701 | `fc-inits` | данные `create` | src/forthc.fth:715 | 2 |  |
| 702 | `fc-ninit` | переменная | src/forthc.fth:715 | 5 |  |
| 703 | `fc-init-open` | переменная | src/forthc.fth:715 | 6 |  |
| 704 | `fc-init` | определение `:` | src/forthc.fth:716 | 1 |  |
| 705 | `fc-scan-uses` | определение `:` | src/forthc.fth:732 | 1 |  |
| 706 | `fc-const-shift` | определение `:` | src/forthc.fth:739 | 2 |  |
| 707 | `fc-lit?` | определение `:` | src/forthc.fth:748 | 3 |  |
| 708 | `fc-mul-lit?` | определение `:` | src/forthc.fth:750 | 1 |  |
| 709 | `fc-shift-lit?` | определение `:` | src/forthc.fth:755 | 2 |  |
| 710 | `fc-pick-roll` | определение `:` | src/forthc.fth:758 | 2 |  |
| 711 | `fc-stx` | переменная | src/forthc.fth:767 | 3 |  |
| 712 | `fc-stlo` | переменная | src/forthc.fth:767 | 8 |  |
| 713 | `fc-sthi` | переменная | src/forthc.fth:767 | 4 |  |
| 714 | `fc-stp` | переменная | src/forthc.fth:767 | 6 |  |
| 715 | `fc-strow` | переменная | src/forthc.fth:767 | 8 |  |
| 716 | `fc-stm` | переменная | src/forthc.fth:767 | 5 |  |
| 717 | `fc-ftr` | переменная | src/forthc.fth:768 | 5 |  |
| 718 | `fc-stg` | переменная | src/forthc.fth:768 | 2 |  |
| 719 | `fc-sw0` | определение `:` | src/forthc.fth:769 | 2 |  |
| 720 | `fc-sw1` | определение `:` | src/forthc.fth:770 | 2 |  |
| 721 | `fc-sbase` | определение `:` | src/forthc.fth:771 | 2 |  |
| 722 | `fc-space-end` | определение `:` | src/forthc.fth:772 | 2 |  |
| 723 | `fc-space-store` | определение `:` | src/forthc.fth:780 | 2 |  |
| 724 | `fc-space-fetch` | определение `:` | src/forthc.fth:787 | 2 |  |
| 725 | `fc-cp` | определение `:` | src/forthc.fth:798 | 4 |  |
| 726 | `fc-copy-row` | определение `:` | src/forthc.fth:800 | 1 |  |
| 727 | `fc-close-init` | определение `:` | src/forthc.fth:803 | 2 |  |
| 728 | `fc-open-init` | определение `:` | src/forthc.fth:806 | 1 |  |
| 729 | `fc-gens` | переменная | src/forthc.fth:817 | 3 |  |
| 730 | `fc-generator` | определение `:` | src/forthc.fth:818 | 87 |  |
| 731 | `fc-literal-name` | определение `:` | src/forthc.fth:820 | 10 |  |
| 732 | `fc-words` | определение `:` | src/forthc.fth:822 | 1 |  |
| 733 | `fc-known` | определение `:` | src/forthc.fth:833 | 1 |  |
| 734 | `fc-defining?` | определение `:` | src/forthc.fth:835 | 7 |  |
| 735 | `fc-code` | определение `:` | src/forthc.fth:836 | 51 | вариант 2 |
| 736 | `fc-fold?` | определение `:` | src/forthc.fth:838 | 13 |  |
| 737 | `fc-top-only` | определение `:` | src/forthc.fth:839 | 6 |  |
| 738 | `fc-not-found` | определение `:` | src/forthc.fth:841 | 1 |  |
| 739 | `fc-word-token` | определение `:` | src/forthc.fth:843 | 2 |  |
| 740 | `fc-token` | определение `:` | src/forthc.fth:848 | 2 |  |
| 741 | `fc-synonym-of` | определение `:` | src/forthc.fth:849 | 2 |  |
| 742 | `fc-synonym` | определение `:` | src/forthc.fth:850 | 10 |  |
| 743 | `fc-sy` | переменная | src/forthc.fth:853 | 2 |  |
| 744 | `fc-synonym?` | определение `:` | src/forthc.fth:854 | 1 |  |
| 745 | `fc-poke` | определение `:` | src/forthc.fth:857 | 2 |  |
| 746 | `fc-concept-record` | определение `:` | src/forthc.fth:860 | 1 |  |
| 747 | `fc-eval` | определение `:` | src/forthc.fth:865 | 54 |  |
| 748 | `fc-concepts` | определение `:` | src/forthc.fth:869 | 1 |  |
| 749 | `fc-nhost` | переменная | src/forthc.fth:876 | 5 |  |
| 750 | `fc-platform` | определение `:` | src/forthc.fth:877 | 1 |  |
| 751 | `fc-time-price` | определение `:` | src/forthc.fth:900 | 1 |  |
| 752 | `fc-replacement` | определение `:` | src/forthc.fth:910 | 1 |  |
| 753 | `fc-library` | определение `:` | src/forthc.fth:925 | 1 |  |
| 754 | `fc-long` | определение `:` | src/forthc.fth:944 | 1 |  |
| 755 | `fc-helpers-cost` | определение `:` | src/forthc.fth:952 | 1 |  |
| 756 | `fc-price-word` | определение `:` | src/forthc.fth:959 | 1 |  |
| 757 | `fc-compile` | определение `:` | src/forthc.fth:962 | 1 |  |
| 758 | `fc-go` | определение `:` | src/forthc.fth:979 | 3 | вход бута (хост) |
| 759 | `gen+` | определение `:` | src/primitives.fth:4 | 5 |  |
| 760 | `gen-` | определение `:` | src/primitives.fth:5 | 2 |  |
| 761 | `gen-and` | определение `:` | src/primitives.fth:6 | 2 |  |
| 762 | `gen-or` | определение `:` | src/primitives.fth:7 | 2 |  |
| 763 | `gen-xor` | определение `:` | src/primitives.fth:8 | 2 |  |
| 764 | `gen=` | определение `:` | src/primitives.fth:9 | 2 |  |
| 765 | `gen<` | определение `:` | src/primitives.fth:10 | 2 |  |
| 766 | `gen-u<` | определение `:` | src/primitives.fth:11 | 2 |  |
| 767 | `gen-lshift` | определение `:` | src/primitives.fth:12 | 2 |  |
| 768 | `gen-rshift` | определение `:` | src/primitives.fth:14 | 2 |  |
| 769 | `gen-0=` | определение `:` | src/primitives.fth:16 | 2 |  |
| 770 | `gen-cells` | определение `:` | src/primitives.fth:17 | 2 |  |
| 771 | `gen-2*` | определение `:` | src/primitives.fth:18 | 2 |  |
| 772 | `gen-1+` | определение `:` | src/primitives.fth:19 | 2 |  |
| 773 | `gen-1-` | определение `:` | src/primitives.fth:20 | 2 |  |
| 774 | `gen-cell+` | определение `:` | src/primitives.fth:21 | 2 |  |
| 775 | `gen*` | определение `:` | src/primitives.fth:22 | 2 |  |
| 776 | `gen/` | определение `:` | src/primitives.fth:25 | 2 |  |
| 777 | `gen-mod` | определение `:` | src/primitives.fth:26 | 2 |  |
| 778 | `gen/mod` | определение `:` | src/primitives.fth:27 | 2 |  |
| 779 | `gen-dup` | определение `:` | src/primitives.fth:28 | 2 |  |
| 780 | `gen-drop` | определение `:` | src/primitives.fth:29 | 2 |  |
| 781 | `gen-swap` | определение `:` | src/primitives.fth:30 | 2 |  |
| 782 | `gen-over` | определение `:` | src/primitives.fth:31 | 2 |  |
| 783 | `gen-rot` | определение `:` | src/primitives.fth:32 | 2 |  |
| 784 | `gen-pick` | определение `:` | src/primitives.fth:33 | 2 |  |
| 785 | `gen-roll` | определение `:` | src/primitives.fth:34 | 2 |  |
| 786 | `gen->r` | определение `:` | src/primitives.fth:35 | 2 |  |
| 787 | `gen-r>` | определение `:` | src/primitives.fth:36 | 2 |  |
| 788 | `gen-r@` | определение `:` | src/primitives.fth:37 | 4 |  |
| 789 | `gen-j` | определение `:` | src/primitives.fth:38 | 2 |  |
| 790 | `gen-@` | определение `:` | src/primitives.fth:39 | 2 |  |
| 791 | `gen-!` | определение `:` | src/primitives.fth:41 | 2 |  |
| 792 | `gen-c@` | определение `:` | src/primitives.fth:42 | 2 |  |
| 793 | `gen-c!` | определение `:` | src/primitives.fth:44 | 2 |  |
| 794 | `gen-emit` | определение `:` | src/primitives.fth:45 | 2 |  |
| 795 | `gen-key` | определение `:` | src/primitives.fth:48 | 2 |  |
| 796 | `gen-if` | определение `:` | src/primitives.fth:50 | 2 |  |
| 797 | `gen-else` | определение `:` | src/primitives.fth:51 | 2 |  |
| 798 | `gen-then` | определение `:` | src/primitives.fth:53 | 2 |  |
| 799 | `gen-begin` | определение `:` | src/primitives.fth:57 | 2 |  |
| 800 | `gen-until` | определение `:` | src/primitives.fth:58 | 2 |  |
| 801 | `gen-while` | определение `:` | src/primitives.fth:60 | 2 |  |
| 802 | `gen-repeat` | определение `:` | src/primitives.fth:61 | 2 |  |
| 803 | `gen-again` | определение `:` | src/primitives.fth:62 | 2 |  |
| 804 | `gen-do` | определение `:` | src/primitives.fth:63 | 2 |  |
| 805 | `fc-di` | переменная | src/primitives.fth:66 | 3 |  |
| 806 | `fc-dl` | переменная | src/primitives.fth:66 | 3 |  |
| 807 | `gen-?do` | определение `:` | src/primitives.fth:67 | 2 |  |
| 808 | `fc-lv` | переменная | src/primitives.fth:73 | 2 |  |
| 809 | `gen-loop` | определение `:` | src/primitives.fth:74 | 2 |  |
| 810 | `gen-leave` | определение `:` | src/primitives.fth:83 | 2 |  |
| 811 | `gen-unloop` | определение `:` | src/primitives.fth:86 | 2 |  |
| 812 | `gen-exit` | определение `:` | src/primitives.fth:87 | 2 |  |
| 813 | `gen-recurse` | определение `:` | src/primitives.fth:89 | 2 |  |
| 814 | `gen-tick` | определение `:` | src/primitives.fth:90 | 2 |  |
| 815 | `gen-throw` | определение `:` | src/primitives.fth:93 | 2 |  |
| 816 | `gen-call` | определение `:` | src/primitives.fth:97 | 3 |  |
| 817 | `gen-space!` | определение `:` | src/primitives.fth:98 | 2 |  |
| 818 | `gen-spacec!` | определение `:` | src/primitives.fth:99 | 2 |  |
| 819 | `gen-space@` | определение `:` | src/primitives.fth:100 | 2 |  |
| 820 | `gen-spacec@` | определение `:` | src/primitives.fth:101 | 2 |  |
| 821 | `gen-execute` | определение `:` | src/primitives.fth:102 | 2 |  |
| 822 | `gen-catch` | определение `:` | src/primitives.fth:103 | 2 |  |
| 823 | `fc-entry-cell` | определение `:` | src/primitives.fth:109 | 1 |  |
| 824 | `fc-concept` | определение `:` | src/primitives.fth:111 | 1 |  |
| 825 | `gen-colon` | определение `:` | src/primitives.fth:118 | 2 |  |
| 826 | `gen-semicolon` | определение `:` | src/primitives.fth:124 | 2 |  |
| 827 | `gen-variable` | определение `:` | src/primitives.fth:127 | 2 |  |
| 828 | `gen-create` | определение `:` | src/primitives.fth:128 | 2 |  |
| 829 | `gen-allot` | определение `:` | src/primitives.fth:129 | 2 |  |
| 830 | `gen-constant` | определение `:` | src/primitives.fth:130 | 2 |  |
| 831 | `gen-decimal` | определение `:` | src/primitives.fth:131 | 2 |  |
| 832 | `gen-kernel-layout` | определение `:` | src/primitives.fth:132 | 2 |  |
| 833 | `gen-backslash` | определение `:` | src/primitives.fth:133 | 2 |  |
| 834 | `gen-paren` | определение `:` | src/primitives.fth:135 | 4 |  |
| 835 | `gen-char` | определение `:` | src/primitives.fth:136 | 2 |  |
| 836 | `gen-string` | определение `:` | src/primitives.fth:137 | 2 |  |
| 837 | `fc-digit@` | определение `:` | src/primitives.fth:140 | 1 |  |
| 838 | `gen-literal` | определение `:` | src/primitives.fth:142 | 2 |  |
| 839 | `fc-known-xt` | определение `:` | src/primitives.fth:149 | 2 |  |
| 840 | `gen-cost` | определение `:` | src/primitives.fth:150 | 2 |  |
| 841 | `gen-proved?` | определение `:` | src/primitives.fth:152 | 2 |  |
| 842 | `gen-library` | определение `:` | src/primitives.fth:153 | 16 |  |
| 843 | `gen-price` | определение `:` | src/primitives.fth:154 | 2 |  |
| 844 | `fc-cpos` | переменная | src/primitives.fth:159 | 4 |  |
| 845 | `fc-hn` | переменная | src/primitives.fth:159 | 2 |  |
| 846 | `fc-cdepth` | переменная | src/primitives.fth:159 | 4 |  |
| 847 | `fc-hname` | данные `create` | src/primitives.fth:159 | 2 |  |
| 848 | `fc-hb` | определение `:` | src/primitives.fth:160 | 3 |  |
| 849 | `fc-c,` | определение `:` | src/primitives.fth:161 | 17 |  |
| 850 | `fc-c1` | определение `:` | src/primitives.fth:162 | 8 |  |
| 851 | `fc-c-gen` | определение `:` | src/primitives.fth:163 | 1 |  |
| 852 | `fc-c-body` | определение `:` | src/primitives.fth:167 | 1 |  |
| 853 | `gen-host` | определение `:` | src/primitives.fth:176 | 2 |  |
| 854 | `fc-name2` | определение `:` | src/primitives.fth:193 | 1 |  |
| 855 | `fc-generators` | определение `:` | src/primitives.fth:196 | 1 |  |
| 856 | `+` | генератор | src/primitives.fth:197 | 562 | слово компилятора `gen+` |
| 857 | `-` | генератор | src/primitives.fth:197 | 63 | слово компилятора `gen-` |
| 858 | `*` | генератор | src/primitives.fth:198 | 83 | слово компилятора `gen*` |
| 859 | `/` | генератор | src/primitives.fth:198 | 4 | слово компилятора `gen/` |
| 860 | `mod` | генератор | src/primitives.fth:199 | 2 | слово компилятора `gen-mod` |
| 861 | `and` | генератор | src/primitives.fth:200 | 121 | слово компилятора `gen-and` |
| 862 | `or` | генератор | src/primitives.fth:200 | 45 | слово компилятора `gen-or` |
| 863 | `xor` | генератор | src/primitives.fth:201 | 5 | слово компилятора `gen-xor` |
| 864 | `lshift` | генератор | src/primitives.fth:201 | 97 | слово компилятора `gen-lshift` |
| 865 | `rshift` | генератор | src/primitives.fth:202 | 64 | слово компилятора `gen-rshift` |
| 866 | `=` | генератор | src/primitives.fth:202 | 82 | слово компилятора `gen=` |
| 867 | `<` | генератор | src/primitives.fth:203 | 28 | слово компилятора `gen<` |
| 868 | `u<` | генератор | src/primitives.fth:203 | 26 | слово компилятора `gen-u<` |
| 869 | `0=` | генератор | src/primitives.fth:204 | 102 | слово компилятора `gen-0=` |
| 870 | `2*` | генератор | src/primitives.fth:204 | 30 | слово компилятора `gen-2*` |
| 871 | `1+` | генератор | src/primitives.fth:205 | 43 | слово компилятора `gen-1+` |
| 872 | `1-` | генератор | src/primitives.fth:205 | 56 | слово компилятора `gen-1-` |
| 873 | `cells` | генератор | src/primitives.fth:206 | 282 | слово компилятора `gen-cells` |
| 874 | `cell+` | генератор | src/primitives.fth:206 | 57 | слово компилятора `gen-cell+` |
| 875 | `dup` | генератор | src/primitives.fth:207 | 305 | слово компилятора `gen-dup` |
| 876 | `drop` | генератор | src/primitives.fth:207 | 206 | слово компилятора `gen-drop` |
| 877 | `swap` | генератор | src/primitives.fth:208 | 146 | слово компилятора `gen-swap` |
| 878 | `over` | генератор | src/primitives.fth:208 | 87 | слово компилятора `gen-over` |
| 879 | `rot` | генератор | src/primitives.fth:209 | 37 | слово компилятора `gen-rot` |
| 880 | `pick` | генератор | src/primitives.fth:209 | 47 | слово компилятора `gen-pick` |
| 881 | `roll` | генератор | src/primitives.fth:210 | 7 | слово компилятора `gen-roll` |
| 882 | `>r` | генератор | src/primitives.fth:210 | 111 | слово компилятора `gen->r` |
| 883 | `r>` | генератор | src/primitives.fth:211 | 115 | слово компилятора `gen-r>` |
| 884 | `r@` | генератор | src/primitives.fth:211 | 108 | слово компилятора `gen-r@` |
| 885 | `i` | генератор | src/primitives.fth:212 | 172 | слово компилятора `gen-r@` |
| 886 | `j` | генератор | src/primitives.fth:212 | 12 | слово компилятора `gen-j` |
| 887 | `@` | генератор | src/primitives.fth:213 | 1270 | слово компилятора `gen-@` |
| 888 | `!` | генератор | src/primitives.fth:213 | 666 | слово компилятора `gen-!` |
| 889 | `c@` | генератор | src/primitives.fth:214 | 23 | слово компилятора `gen-c@` |
| 890 | `c!` | генератор | src/primitives.fth:214 | 18 | слово компилятора `gen-c!` |
| 891 | `space!` | генератор | src/primitives.fth:215 | 1 | слово компилятора `gen-space!` |
| 892 | `spacec!` | генератор | src/primitives.fth:215 | 1 | слово компилятора `gen-spacec!` |
| 893 | `space@` | генератор | src/primitives.fth:216 | 1 | слово компилятора `gen-space@` |
| 894 | `emit` | генератор | src/primitives.fth:217 | 4 | слово компилятора `gen-emit` |
| 895 | `key` | генератор | src/primitives.fth:217 | 1 | слово компилятора `gen-key` |
| 896 | `if` | генератор | src/primitives.fth:218 | 313 | слово компилятора `gen-if` |
| 897 | `else` | генератор | src/primitives.fth:218 | 85 | слово компилятора `gen-else` |
| 898 | `then` | генератор | src/primitives.fth:219 | 313 | слово компилятора `gen-then` |
| 899 | `begin` | генератор | src/primitives.fth:219 | 25 | слово компилятора `gen-begin` |
| 900 | `until` | генератор | src/primitives.fth:220 | 2 | слово компилятора `gen-until` |
| 901 | `while` | генератор | src/primitives.fth:220 | 22 | слово компилятора `gen-while` |
| 902 | `repeat` | генератор | src/primitives.fth:221 | 22 | слово компилятора `gen-repeat` |
| 903 | `again` | генератор | src/primitives.fth:221 | 1 | слово компилятора `gen-again` |
| 904 | `do` | генератор | src/primitives.fth:222 | 31 | слово компилятора `gen-do` |
| 905 | `?do` | генератор | src/primitives.fth:222 | 58 | слово компилятора `gen-?do` |
| 906 | `loop` | генератор | src/primitives.fth:223 | 89 | слово компилятора `gen-loop` |
| 907 | `leave` | генератор | src/primitives.fth:223 | 1 | слово компилятора `gen-leave` |
| 908 | `unloop` | генератор | src/primitives.fth:224 | 7 | слово компилятора `gen-unloop` |
| 909 | `exit` | генератор | src/primitives.fth:224 | 83 | слово компилятора `gen-exit` |
| 910 | `recurse` | генератор | src/primitives.fth:225 | 2 | слово компилятора `gen-recurse` |
| 911 | `execute` | генератор | src/primitives.fth:225 | 10 | слово компилятора `gen-execute` |
| 912 | `[']` | генератор | src/primitives.fth:226 | 119 | слово компилятора `gen-tick` |
| 913 | `catch` | генератор | src/primitives.fth:226 | 1 | слово компилятора `gen-catch` |
| 914 | `throw` | генератор | src/primitives.fth:227 | 85 | слово компилятора `gen-throw` |
| 915 | `:` | генератор | src/primitives.fth:228 | 494 | слово компилятора `gen-colon` |
| 916 | `;` | генератор | src/primitives.fth:228 | 494 | слово компилятора `gen-semicolon` |
| 917 | `variable` | генератор | src/primitives.fth:229 | 322 | слово компилятора `gen-variable` |
| 918 | `create` | генератор | src/primitives.fth:229 | 47 | слово компилятора `gen-create` |
| 919 | `allot` | генератор | src/primitives.fth:230 | 45 | слово компилятора `gen-allot` |
| 920 | `constant` | генератор | src/primitives.fth:230 | 24 | слово компилятора `gen-constant` |
| 921 | `decimal` | генератор | src/primitives.fth:231 | 3 | слово компилятора `gen-decimal` |
| 922 | `kernel-layout` | генератор | src/primitives.fth:231 | 1 | слово компилятора `gen-kernel-layout` |
| 923 | `\` | генератор | src/primitives.fth:232 | 142 | слово компилятора `gen-backslash` |
| 924 | `(` | генератор | src/primitives.fth:232 | 473 | слово компилятора `gen-paren` |
| 925 | `[char]` | генератор | src/primitives.fth:232 | 8 | слово компилятора `gen-char` |
| 926 | `s"` | генератор | src/primitives.fth:233 | 198 | слово компилятора `gen-string` |
| 927 | `literal` | генератор | src/primitives.fth:234 | 495 | слово компилятора `gen-literal` |
| 928 | `0` | цифра (литерал) | src/primitives.fth:242 | 536 | значение 0 |
| 929 | `1` | цифра (литерал) | src/primitives.fth:242 | 449 | значение 1 |
| 930 | `2` | цифра (литерал) | src/primitives.fth:242 | 453 | значение 2 |
| 931 | `3` | цифра (литерал) | src/primitives.fth:242 | 302 | значение 3 |
| 932 | `4` | цифра (литерал) | src/primitives.fth:243 | 242 | значение 4 |
| 933 | `5` | цифра (литерал) | src/primitives.fth:243 | 106 | значение 5 |
| 934 | `6` | цифра (литерал) | src/primitives.fth:243 | 156 | значение 6 |
| 935 | `7` | цифра (литерал) | src/primitives.fth:243 | 60 | значение 7 |
| 936 | `8` | цифра (литерал) | src/primitives.fth:244 | 158 | значение 8 |
| 937 | `9` | цифра (литерал) | src/primitives.fth:244 | 38 | значение 9 |
| 938 | `fc-install-generators` | определение `:` | src/primitives.fth:245 | 1 |  |
| 939 | `heap-start` | данные `create` | src/main.fth:3 | 1 |  |
| 940 | `fc-read` | определение `:` | src/main.fth:6 | 2 |  |
| 941 | `fc-sizes` | определение `:` | src/main.fth:11 | 2 |  |
| 942 | `kn-at` | переменная | src/kernel.fth:7 | 5 |  |
| 943 | `kn-put` | определение `:` | src/kernel.fth:8 | 1 |  |
| 944 | `kn-order` | определение `:` | src/kernel.fth:16 | 1 |  |
| 945 | `kn-get` | определение `:` | src/kernel.fth:18 | 1 |  |
| 946 | `kn-compile` | определение `:` | src/kernel.fth:19 | 1 |  |
| 947 | `kn-.n` | определение `:` | src/kernel.fth:24 | 1 |  |
| 948 | `main` | определение `:` | src/kernel.fth:28 | 1 | вариант 2 |
| 949 | `kn-heap-start` | данные `create` | src/kernel.fth:32 | 1 |  |

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
| `fc-depth` | определение `:` | src/forthc.fth:831 |
| `fc-ctl-depth` | определение `:` | src/forthc.fth:832 |
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
