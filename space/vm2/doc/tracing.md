# Local dynamic trace fixture

`tools/dynamic_trace.py` generates PCS2 copycode for the independent
self-patching fixture in `tests/test_dynamic_trace.py`. It does not add a
trace mode to the emulator or trace arbitrary uninstrumented images.
The [public contract](emulator-contract.md) remains the kernel boundary.
External generator migration belongs to consumers; see [the handoff](consumer-interval-handoff.md).

The wrapper serializes its own captures to preserve strict interval
independence. Data transfer, following FSTAT request and answer retrieval
use distinct ticks. It preserves a pending application response on
non-data layers. Each original layer costs 20 physical ticks; its body has
offset 11 (zero-based). Reporter cost uses `TerminalFragment.report_ticks`.
Protocol/layout identities reject pre-correction manifests.

For a fixture-generated manifest and recorded segment:

```sh
python3 tools/dynamic_trace.py SEGMENT/debug.bin \
  --manifest SESSION/image.json --status SEGMENT/status.bin
```

`--events` emits JSON-line events before the summary. The CLI reads raw/gzip;
`audit(stream, manifest, terminal=..., on_event=...)` processes bounded frames
without retaining all events. See [local checkpoint fixtures](checkpoints.md)
for immutable segment/resume behavior.

## Что наблюдается

Исходные адреса инструкций сохраняются: патчи продолжают попадать в свои
поля. Перед выполнением слоя обёртка захватывает его текущие инструкции,
сохраняет управляющую копию и исполняет захваченный слой один раз. Метки
переходов переназначаются на обёртки. Поэтому видны реально выбранные
ветви, повторения и изменённые операнды.

В `full` сохраняется весь процессор; последний управляющий слот заменён
служебным переходом, исходная управляющая инструкция передаётся отдельно.
В `channels` передаются только два буфера для выбранных канальных/SYS
инструкций и точное число обычных копий. Генератор отвергает динамический
`n` обычной копии, для которого такой счётчик не доказан; динамический
размер передачи данных поддерживается. Это контракт данного генератора,
не универсальный трассировщик произвольного raw-образа.

После слоя с передачей данных копикод получает FSTAT и записывает
`moved/status/eof`. На остальных слоях он не опрашивает SYS: иначе можно
затереть ответ приложения между отдельными слоями запроса и чтения.
У событий SYS поле `status` отсутствует (`null`), поскольку приписывать
им результат предыдущей передачи нельзя.

Слои приложения, монитора и чистого управления помечаются отдельно.
Сводка считает обычные копии приложения отдельно от копий монитора;
служебные переходы, boot и обёртки не входят в число копий приложения.
Каждый исходный слой обходится в 20 физических тактов. Внутри сегмента
`step` нумерует исходные слои, `application_step` исключает монитор,
`committed` — накопленный счётчик гостевых инструкций. Для канальных/SYS
событий `physical_tick = (step−1)*20+12`, считая первый такт после boot
тактом 1. Полная стоимость включает начальный такт, три такта конечного
шлюза и терминальный фрагмент; bootstrap учитывается отдельно.

## Формат PCS2

Все целые заголовка/метаданных — little endian; захваченные числовые поля
пространства остаются в его битовом порядке. Точные ширины берутся из
boundary manifest. `row_bytes = ceil(instruction_bits/8)`.

| Часть | Содержание |
|---|---|
| Заголовок `<4sBBI` | `PCS2`, тип 1 (слой) / 2 (конец), режим 0 full / 1 channels, длина payload |
| Метаданные слоя `<QIBBHH` | исходный home, число обычных копий, фаза 0/1/2, число выбранных слотов, два индекса слотов |
| Идентичность и счётчик | 32 байта layout_id, 64 бита committed в порядке пространства |
| Тело | весь процессор или два буфера по row_bytes |
| Контроль и результат | исходный управляющий слот, дополненный до row_bytes; SYS response, дополненный до байта |
| Конец | kind 1 terminal / 2 checkpoint, reason 0 idle / 1 limit, layout_id, committed64, guest_status32 |

Между записями идут пятибайтовые маркеры `PHT1B` (boot окончен),
`PHT1C` (вычисление окончено), необязательный `PHT1S` (снэпшот начинается),
`PHT1F` (снэпшот и SPT полностью отправлены). End сам по себе недостаточен:
он предшествует снэпшоту. При объявленном в manifest completion marker
аудитор требует F; прерывание после End также отклоняется. Для старого
PCS2 без такого объявления необходим отдельный полный терминальный receipt.

Сырые reason согласованы с SPT. Производный `outcome` различает `limit`,
нормальный `idle` (RV32I status 10) и `error`. Аудитор проверяет длины,
layout, порядок фаз, непрерывность управления, границы/пересечения записей,
счётчики и соответствие SPT. В full дополнительно сверяется фактическое
число обычных копий; channels полагается на проверенное расписание.

Архив сегмента хранит SHA-256 `debug.bin`, `trace_audit`, `trace_totals`
и ресурсы запуска. Resume повторно проверяет хеши и аудиты всей цепочки.
Трассы сегментов аудируются по отдельности; простая конкатенация не является
одним PCS2-сеансом. Контрольные суммы обнаруживают повреждение, но не
являются криптографическим подтверждением доверенности генератора.

## Verification

`make check` runs standalone self-patched operands, pending SYS response,
channel errors, full/channels parity, resume/fork, malformed framing and
exact final-tick checks. A separate C harness independently validates every
executed operand, including service layers. Full traces include ordinary
operands; channels traces alone cannot establish interval independence.
No external RV32I/GCC result is claimed. Performance evidence is limited to
[standalone core benchmarks](core-benchmarks.md).
