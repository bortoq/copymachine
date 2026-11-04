# Документация

Документы делятся на две части. **Изучение** отвечает на вопросы «что это» и «как устроено», **сопровождение разработки** — «как шла и идёт работа». Новому разработчику — сначала часть 1, начиная с [README](../README.md).

## Часть 1. Изучение проекта

Читать в таком порядке. Определения понятий — только в [README](../README.md#понятия) (и низкоуровневые — в словаре); остальные документы ссылаются на них.

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
| [measurements/](measurements/) | замеры и разборы отдельных пунктов: [бут на L0](measurements/boot-on-l0.md) (18.2), [динамическая изоляция](measurements/dynamic-isolation.md) (18.18), [вызов на хосте](measurements/host-call.md) (18.13), [задержки](measurements/host-delay.md) (18.15), [раскладка](measurements/host-layout.md) (18.19), [следующие слова](measurements/host-next.md) (18.16), [слова на хосте](measurements/host-words.md) (18.11), [минимум понятий](measurements/min-concepts.md) (18.1), [без исключений](measurements/no-exceptions.md) (18.21), [таблица возвратов](measurements/return-table.md) (18.22); `check-full.json` — результаты долгих целей; `*-tools/` — скрипты замеров |
| [research/](research/) | [граф определений ядра](research/definition-graph.md) (порождается `defgraph.py`) и данные `definition-graph.json`, `isolation-ticks.json` |

Пути `docs/journal/`, `docs/design/`, `docs/measurements/` и `language/doc/` не меняются: на них ссылаются тесты и журналы.
