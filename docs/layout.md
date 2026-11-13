# Раскладка

| Каталог | Содержимое |
|---|---|
| `emulator/` | один эмулятор (bitcopy, длинное копирование LONG, SYS, режим `checked`), его тесты, [контракт](../emulator/doc/emulator-contract.md) |
| `tower/` | цепочка вложенных языков 1–5: [`README.md`](../tower/README.md) (определение), эталоны `*.py` и `tests/`, тексты инструментов и программ `programs/` (в том числе `programs/assoc/` — ассоциативное пространство, 25.2; `programs/far/` — дальнее копирование, этапы 26 и 25.8: `far_copy_ck.tw`, `far_copy_file_w.tw`, `far_copy_file_r.tw`; `programs/prove/` — доказательство выхода прохода через канал, `provepass.tw`, 25.7.2), `golden/` — эталонные выходы проходов (`tests/test_golden.py`, долгая `long_golden.py`; `tests/test_prove.py`, `tests/test_provepass.py` — доказательства через канал; `programs/assoc/assoc_prove.tw`); замеры — `docs/measurements/tower.md`; проверка — `make check-tower` |
| `tools/` | `limited_run.py`, `check_layout.py`, `gcov_summary.py`, `ci/*.sh` |
| `docs/` | [`README.md`](README.md) — указатель двух частей документации; изучение: `guide/` (руководство по шагам), `dictionary.md`, `layout.md`; сопровождение разработки: `journal/` (журнал плана), `design/` (журнал дизайна), `measurements/` (замеры), `research/` |
| `build/` | результаты сборки; в Git не входят |

Корневой `Makefile` собирает эмулятор и запускает проверки (`check-fast`, `check`, `check-full`, `check-tower`); `tools/check_layout.py` проверяет раскладку.

Всё удалённое при уборке (Forth на RV32I, vm2, copycode, прямой компилятор, pForth на языке) — в теге `archive-2026-10-30`; прежний язык `language/` (бут через pForth, ядро, L0) — в теге `archive-2026-11-10`; ранние порты — в ветке `archive/legacy`. Восстановление: `git restore --source=archive-2026-10-30 -- <путь>`.
