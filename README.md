# copymachine

**RU.** Пространство копирований (эмулятор: одновременные копирования между полуинтервалами битов) и язык, определение которого написано его собственными словами и компилирует себя: L1 = L0 (L0 = 17 559 635 байт, совпадает с K0 независимой модели). Первые 30 секунд: `make && make check-fast` (сборка около 13 с на 12 ядрах, быстрый набор около 45 с).

**EN.** A copy space (an emulator of simultaneous copies between bit half-intervals) and a language whose definition is written in its own words and compiles itself: L1 = L0 (L0 = 17,559,635 bytes, equal to K0 of an independent model). First 30 seconds: `make && make check-fast` (build about 13 s on 12 cores, fast suite about 45 s).

## Раскладка

- `emulator/` — один эмулятор: bitcopy и длинное копирование (LONG), режим проверки непересечения `checked`; [README](emulator/README.md).
- `language/` — определение языка (`src/`), `tools/`, `tests/` (с независимыми эталонами в `tests/reference/`), `doc/`, `boot/` (хостовый pForth32 для первой компиляции); [README](language/README.md).
- `tools/` — `limited_run.py`, `check_layout.py`, `gcov_summary.py`, `ci/*.sh`.
- `docs/` — [словарь](docs/dictionary.md), [раскладка](docs/layout.md), `design/` (журнал дизайна), `research/`.

Дальнейший план — [ROADMAP.md](ROADMAP.md).

## Проверки

| Цель | Что делает | Время |
|---|---|---|
| `make` | эмулятор и L0 | около 13 с (12 ядер) |
| `make check-fast` | быстрый набор без L0 | около 45 с |
| `make check` | + бут и `language check` | |
| `make check-full` | + длинные цели; `check-self`: L0 компилирует определение языка, L1 = L0 | `check-self` около 1,5–2 ч |
| `make lint`, `make coverage` | ruff; покрытие (эмулятор около 91 % строк) | |

CI: `.github/workflows/check.yml` (быстрый набор, эмулятор gcc/clang в release и с санитайзерами, язык) и `nightly.yml` (длинные цели; `check-self` выкладывает sha256 L0 и L1 артефактом — сверяйте хеши).

Требования: POSIX, `cc` с `-m32` (gcc-multilib), Python 3.11 или новее, make.

## Статус

Ядро языка не доказано: механизм доказательства есть и применён к тестовым словам.

## Безопасность

Запрос SYS EXEC исполняет команду хоста через `system()`; язык через него вызывает `cc` (слово `host`, замена пространства). Чужие образы запускайте только в контейнере или виртуальной машине.

## Лицензия и архивы

MIT ([LICENSE](LICENSE)); сторонний код — [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

- Тег `archive-2026-10-30` — всё до уборки (Forth на RV32I, vm2, copycode, прямой компилятор, pForth на языке).
- Ветка `archive/legacy` и тег `archive-legacy-2026-10-30` — исходники ранних портов (C, GCC, Linux); истории в git-bundles.
- Восстановление: `git restore --source=archive-2026-10-30 -- <путь>`.

## Для этой среды

Корневой `.git` защищён от записи; используйте `./project-git status`, `./project-git diff` и т. д. вместо `git`. В обычном клоне работает стандартный Git.
