# Раскладка

| Каталог | Содержимое |
|---|---|
| `emulator/` | один эмулятор (bitcopy, длинное копирование LONG, SYS, режим `checked`), его тесты, [контракт](../emulator/doc/emulator-contract.md) |
| `tower/` | цепочка вложенных языков 1–5: [`README.md`](../tower/README.md) (определение), эталоны `*.py` и `tests/`, тексты инструментов и программ `programs/`; замеры — `docs/measurements/tower.md`; проверка — `make check-tower` |
| `tools/` | `limited_run.py`, `check_layout.py`, `gcov_summary.py`, `ci/*.sh` |
| `docs/` | [`README.md`](README.md) — указатель двух частей документации; изучение: `guide/` (руководство по шагам), `dictionary.md`, `layout.md`; сопровождение разработки: `journal/` (журнал плана), `design/` (журнал дизайна), `measurements/` (замеры), `research/` |
| `build/` | результаты сборки; в Git не входят |

Корневой `Makefile` собирает эмулятор и запускает проверки (`check-fast`, `check`, `check-full`, `check-tower`); `tools/check_layout.py` проверяет раскладку.

Всё удалённое при уборке (Forth на RV32I, vm2, copycode, прямой компилятор, pForth на языке) — в теге `archive-2026-10-30`; прежний язык `language/` (бут через pForth, ядро, L0) — в теге `archive-2026-11-10`; ранние порты — в ветке `archive/legacy`. Восстановление: `git restore --source=archive-2026-10-30 -- <путь>`.
