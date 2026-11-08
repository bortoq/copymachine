# Документация

Документы делятся на две части. **Изучение** отвечает на вопросы «что это» и «как устроено», **сопровождение разработки** — «как шла и идёт работа». Новому разработчику — сначала часть 1, начиная с [README](../README.md).

## Часть 1. Изучение проекта

Читать в таком порядке. Определения понятий — только в [словаре](dictionary.md#понятия) (и низкоуровневые — в словаре); остальные документы ссылаются на них.

| Документ | О чём, кому |
|---|---|
| [README](../README.md) | полное руководство: понятия, как всё устроено, быстрый старт, карта, что сделано и что будет; всем |
| [guide/README.md](guide/README.md) | оглавление пошагового руководства из шести глав |
| [guide/01-space.md](guide/01-space.md) | пространство и копирование, разбор готового образа; всем |
| [guide/02-emulator.md](guide/02-emulator.md) | запуск эмулятора, такт, SYS, режим `checked`, тесты, исходники; пишущим на C и тестах |
| [guide/03-language.md](guide/03-language.md) | язык: слова, стек, от слова до копирований, цена; пишущим на языке |
| [guide/04-kernel.md](guide/04-kernel.md) | бут, L0/L1, раскладка ядра, изоляция, доказательство, замена |
| [guide/05-long-copy.md](guide/05-long-copy.md) | длинные копирования, адресное пространство хоста, определения на хосте |
| [guide/06-plans.md](guide/06-plans.md) | что осталось сделать |
| [dictionary.md](dictionary.md) | словарь низкоуровневых терминов (описания, процессор, образы) и указатель понятий README |
| [layout.md](layout.md) | раскладка каталогов репозитория |
| [../tower/README.md](../tower/README.md) | единственное определение языка цепочки 1–5 (этап 23): понятия, все слова, что в пространстве и что на хосте, минимум понятий, сборка |
| [../emulator/README.md](../emulator/README.md) | краткая справка по эмулятору (English) |
| [../emulator/doc/emulator-contract.md](../emulator/doc/emulator-contract.md) | точный контракт эмулятора: кодировка, такт, каналы, SYS, обязанности программы |
| [../language/README.md](../language/README.md) | что такое каталог `language/` и как его проверить |
| [../language/doc/language.md](../language/doc/language.md) | определение языка на русском: запись на каждое слово ядра (сверяется с кодом); справочник |
| [../language/doc/core.md](../language/doc/core.md) | список слов ядра (порождается автоматически, руками не правится) |
| [../language/doc/boot.md](../language/doc/boot.md) | бут через хостовый pForth, цели `make`, самосборка |
| [../language/doc/closure.md](../language/doc/closure.md) | замкнутость определения: как проверяется, что внешних имён нет |
| [../language/doc/generators.md](../language/doc/generators.md) | слова-генераторы: запись словаря, виды, регистрация |
| [../language/doc/literals.md](../language/doc/literals.md) | цифры, числа и литералы (компилятор не разбирает числа) |
| [../language/doc/word.md](../language/doc/word.md) | запись слова: механизмы, цена, счётчики |
| [../language/doc/isolation.md](../language/doc/isolation.md) | динамическая изоляция, слово непересечения, длинное копирование в программе ядра |
| [../language/doc/proof.md](../language/doc/proof.md) | проверка таблицей и доказательство слова |
| [../language/doc/replace.md](../language/doc/replace.md) | замена определения и синонимы |
| [../language/doc/user_programs.md](../language/doc/user_programs.md) | программы пользователя не дорожают при перекомпиляции языка |
| [../language/doc/platform.md](../language/doc/platform.md) | платформы, время, определения на хосте |

Справочные документы `language/doc/*` содержат в основном замеры и подробности отдельных этапов; пути к ним зафиксированы в тестах и журналах, поэтому они не переносились.

## Часть 2. Сопровождение разработки

Нужны тем, кто ведёт проект: планы, решения, замеры, исследования. Для изучения не обязательны.

| Документ | О чём |
|---|---|
| [../ROADMAP.md](../ROADMAP.md) | план: этапы и пункты со статусами ✅/❌ |
| [journal/roadmap.md](journal/roadmap.md) | журнал плана: полный текст каждого этапа, принятые решения, «Сделано» с цифрами |
| [design/exclude_this_file_from_git.txt](design/exclude_this_file_from_git.txt) | журнал дизайна: обсуждение и решения автора (раздел 7.2 — действующие); подлежит переработке в дизайн проекта |
| [measurements/](measurements/) | действующие замеры: [минимум понятий](measurements/min-concepts.md) (18.1, ждёт автора); замеры завершённых пунктов (18.2–18.22, 21.1) и скрипты `*-tools/` — в теге `archive-2026-11-05` |
| [measurements/tower.md](measurements/tower.md) | замеры цепочки языков по пунктам 23.x |
| [measurements/tower-forth37.md](measurements/tower-forth37.md) | 37 программ нынешнего языка на цепочке (23.11) |
| [measurements/level-proof.md](measurements/level-proof.md) | доказательство уровня: слово `copy n d s` (23.21, к 7.2.35) |
| [research/](research/) | [граф определений ядра](research/definition-graph.md) (порождается `defgraph.py`) и данные `definition-graph.json`, `isolation-ticks.json` |

Пути `docs/journal/`, `docs/design/`, `docs/measurements/` и `language/doc/` не меняются: на них ссылаются тесты и журналы.

## Цели make и CI

| Цель | Что делает |
|---|---|
| `make` | эмулятор и L0 |
| `make check-fast` | тесты эмулятора (с режимом `checked`), 37 программ на хосте, замкнутость, сверка `language.md`, `make check-tower` (цепочка языков 1–5) |
| `make check` | + бут и `make -C language check` (около 10 минут) |
| `make check-full` | + долгие цели: ядро, самосборка `check-self`, изоляция, доказательство, замена, программы пользователя, `make check-tower-long` (часы) |
| `make lint`, `make coverage` | ruff; покрытие эмулятора gcov |
| `sh tools/ci/fast.sh` | то же, что быстрое задание CI: lint, `check-fast`, лицензии, документация, покрытие |
| `sh tools/ci/docs.sh` | ссылки в Markdown и объём документации (меньше, чем в теге `archive-2026-10-30`) |

CI (`.github/workflows/`): `check.yml` — быстрый набор, эмулятор gcc/clang в release и с санитайзерами, язык; `nightly.yml` — долгие цели, `check-self` выкладывает sha256 L0 и L1 (сверяйте хеши).
