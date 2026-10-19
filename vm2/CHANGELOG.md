# Этап 6: постоянная трансляция

- `vm2c compile/check/run/resume`, символический вход, сохранённые готовые
  псевдоинструкции vm1 и ABI `vm2-direct-v1`; обычный make строит прямой пример.
- Типизированные поля/релокации, обновление границ в пространстве, шаблоны,
  динамическое описание, нативные каналы/SYS и согласованные checkpoints.
- Независимый эталон, аудит каждого физического такта, настоящий фрагмент
  генераторов RV32I и сравнение с обоими совместимыми исполнителями.
- Бенчмарки ограничены памятью, одним CPU и общим таймаутом; исправлены
  остановка legacy-контроля и конфликт патча с fetch следующего слоя.
- Прежние упакованные образы запускаются явно через совместимый vm2.

# Этап 5: планирование и ускорение копикода vm2

- Общие интервальные планировщик и оптимизатор copycode.vm1.schedule:
  RAW/WAR/WAW, запрет src/src, ограничения слотов, fetch, барьеры,
  удаление/разбиение ненужных записей и слияние соседних копирований.
- Параллельная подготовка обычных дескрипторов vm2 и исполнение партиями;
  блочная префиксная арифметика. Сохранены full fetch и виртуальные IO/SYS.
- Проверки общего планировщика, реальной арифметики и варианты генератора
  на независимом эталоне; сравнительные замеры в doc/vm2-scheduling.md.

# vm2 0.2.0 — 2026-10-19

Основной путь заменён гостевым интерпретатором троек на копикоде vm1.
Полный fetch, арифметика границ, отображение каналов/SYS, old/new ответы и
виртуальные границы выполняются в пространстве. Добавлены независимый
эталон, проверки фактических расписаний, snapshot на границе, CLI/кэш,
автономный выпуск и измерения. ABI троек сохранён; расходы интерпретации
существенно выше C, см. doc/vm1-guest.md. Прежний C — legacy-контроль.

---

# Release notes

## 0.1.0 — 2026-10-18

First source release of the standalone positional address-space emulator.
The public machine contract is revision 3. This version identifies the
source distribution; it does not add a wire field or CLI option.

- One `space` executable, with `-s`, `-p` and `-t`. The initial ordinary
  seed reads the processor from stdin. There is no diagnostic emulator build.
- All active source and destination memory intervals of a tick must be
  pairwise disjoint, including source/source. Read-only fan-out is invalid.
- Channel operations complete by tick end. A SYS read returns the response
  committed before its tick; a new request's response is readable later.
  A dependent transfer, FSTAT request and response read need separate ticks.
  CLOSE SYS preserves old-response reads in its closing tick.
- Pre-bound stdin, stdout, debug, optional status fd 3 and snapshot fd 4.
  Snapshot/trace/report formats remain copycode protocols, not kernel APIs.
- Independent bitcopy, decode/tick, SYS, process and executed-schedule checks;
  GCC/Clang release and ASan/UBSan CI configurations.
- Deterministic source archives, staged installation and standalone core
  benchmarks. Build/runtime assumptions and the trust contract are explicit.

Earlier shared-source and same-tick SYS pipeline behavior is unsupported.
Old generated images may violate the machine contract; old source-side
protocol/layout identities and snapshots must be rebuilt, not relabeled.
Earlier copy-space compatibility/performance claims remain withdrawn until
its owners repair and independently revalidate their generator. The release
has no runtime handshake or automatic validation of input programs.

Supported baseline: Linux x86-64, 8-bit bytes, little-endian, 64-bit
`size_t`/`long`, C11/POSIX and `unsigned __int128`. Locally verified compiler
versions are GCC 12.3 and Clang 15.0.7. See doc/build.md for full dependencies,
commands, CI scope and the local LeakSanitizer limitation. MIT licensing and
existing copyright notices are retained.
