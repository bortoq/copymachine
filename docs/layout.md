# Раскладка

| Каталог | Содержимое |
|---|---|
| `emulator/` | один эмулятор (bitcopy, длинное копирование LONG, SYS, режим `checked`), его тесты, текст определения слова «пространство», [контракт](../emulator/doc/emulator-contract.md) |
| `language/src/` | определение языка |
| `language/tools/`, `language/tests/` | инструменты и тесты; `tests/reference/` — независимые эталоны (модель K0 и др.) |
| `language/doc/` | документация языка |
| `language/boot/` | хостовый pForth32 для первой компиляции (нужен `cc -m32`) |
| `tools/` | `limited_run.py`, `check_layout.py`, `gcov_summary.py`, `ci/*.sh` |
| `docs/` | `dictionary.md`, `design/` (журнал дизайна), `research/` |
| `build/` | результаты сборки; в Git не входят |

Корневой `Makefile` собирает эмулятор и L0 и запускает проверки (`check-fast`, `check`, `check-full`); `tools/check_layout.py` проверяет раскладку.

Всё удалённое при уборке (Forth на RV32I, vm2, copycode, прямой компилятор, pForth на языке) — в теге `archive-2026-10-30`; ранние порты — в ветке `archive/legacy`. Восстановление: `git restore --source=archive-2026-10-30 -- <путь>`.
