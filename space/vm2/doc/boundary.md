# Stdin boot and diagnostic copycode

This guide describes supporting copycode and launcher tools currently kept
in this checkout. The [public emulator contract](emulator-contract.md) defines
the kernel interface. Loader framing, PCS and SPT are tool protocols, not
services interpreted by the emulator. Standalone examples below run from
this repository; paragraphs mentioning copy-space describe optional external
integration.

The emulator is the single `space` binary. Its options are `-s`, `-p`,
`-t`. The launching process supplies streams by redirection. There is no
host image insertion, dump, restore or trace option, and no separate
emulator build for diagnostics.

## Boot and image installation

```sh
make
# A complete standalone raw processor image that stops on entry:
python3 tools/driver_gen.py -s 65520 -p 64 --nop -o /tmp/space-nop.bin
python3 tools/boundary.py boot -s 65520 -p 64 /tmp/space-nop.bin -o /tmp/boot
./space < /tmp/boot
# Or prepend boot to application input:
cat /tmp/boot /dev/stdin | ./space
```

`image.bin` is a raw space image: MSB-first stream bytes, with numeric
instruction fields LSB-first. Its processor at position zero is the entry
layer. Short images are zero padded to the configured space; oversized
images and nonzero padding outside the space are rejected. The image and
launcher must use the same `-s` and `-p`.

The existing seed reads `p * (3a-1)` bits, rounded up to whole stream
bytes, from stdin into the processor. The stream builder supplies a
complete first layer. Each installer record has two execution ticks:

1. Slot 0 reads a payload into its final position outside the processor.
   Ordinary copies erase slots 0..2 and enable the next-layer read in
   slot 3. These writes and their sources are disjoint.
2. Slot 3 reads the next processor layer from stdin. No ordinary copy
   modifies that newly loaded layer in this tick.

Records occupy exactly `ceil(p * (3a-1) / 8)` bytes. A record's payload
occupies `ceil(n / 8)` bytes, independently padded. Numeric fields remain
LSB-first; padding is at the low end of the last stream byte. The payload
size and target are in the copy instruction itself; no host stream parser
or additional header is needed. The last layer in the stream is the
image's entry processor. It also restores any real data bits sharing the
processor's last byte. The next byte belongs to application input.

The loader needs `p >= 8`, plus the ordinary emulator fit relations. It
uses only processor slots; it reserves no persistent memory. Payloads
are split at the instruction count-field limit. All-zero chunks are
omitted on a fresh, zero-initialised emulator; `--dense` also emits them.
Images and snapshots can overwrite the loader's entire footprint.
A malformed or truncated boot stream is outside this loader's contract;
use `-t` to bound executed ticks in experiments; it cannot interrupt a
blocked input call. A future checked loader can use
SYS state without changing the emulator.

## Diagnostics and a runnable example

`tools/boundary.py` supplies `Program`, a cooperative copycode library.
It reserves code and record memory and the last processor slot for links.
Application steps run between monitor layers. Only ordinary copies run
inside the emulator: there are no callbacks, privileged memory reads or
host diagnostic paths.

```sh
python3 tools/boundary_demo.py --trace full -o /tmp/echo.boot
printf DEMO | cat /tmp/echo.boot /dev/stdin | ./space -p 8 \
    > /tmp/echo-and-snapshot.bin 2> /tmp/echo.trace
python3 tools/boundary.py decode /tmp/echo.trace
head -c 4 /tmp/echo-and-snapshot.bin       # DEMO
# The demo emits four application bytes, then an 8190-byte raw snapshot:
tail -c 8190 /tmp/echo-and-snapshot.bin > /tmp/snapshot.bin
python3 tools/boundary.py boot -s 65520 -p 8 /tmp/snapshot.bin -o /tmp/resume.boot
./space -p 8 < /tmp/resume.boot           # DEMO, then stop
```

Use `--trace channels` in the demo for channel-only textual events and
final copy/channel counts. `make check` exercises both modes, full-space
installation, short input, dump and restore, and non-byte-aligned seed
layers.

The channel table is `SYS = s`, `stdin = s+1` (fd 0), `stdout = s+2`
(fd 1), `debug = s+3` (fd 2, stderr). Bind the trace with `2> file`.
Debug is a normal pre-bound data channel, present in every build. It does
not share the SYS control record. `status = s+4` (fd 3) and
`snapshot = s+5` (fd 4) bind pre-opened descriptors when present; missing
optional streams are unavailable, with positions still reserved. `NDEV = 5`;
leave six address positions. The C kernel never opens paths. Use
`machine.space_bits_for_bytes(byte_budget)` instead of subtracting a fixed
number. Shared-description checks reject old four-position manifests; the
core only checks channel capacity, not the identity of an input image.

## Copycode API and tracing contract

```python
from boundary import Program, boot_stream
p = Program(space_bits=65520, slots=8, code_base=8192, trace='full')
p.step([(32, 1024, 65521)])       # read four application bytes
p.step([(32, 65522, 1024)])       # write them
p.halt()
boot = boot_stream(p.finish(), 65520, 8)
```

All source and destination memory intervals in a step must be pairwise
disjoint, including source/source. `Program.step` and final link assembly
reject overlapping schedules. A step may contain up to `p-1` ordinary copies. It must not write the
processor or the library's code/records. Use one operation per data
channel per step, whole-byte data transfers and independent copies.
`Program` generates a finite schedule with fixed instruction fields;
self-modifying control flow and arbitrary existing images require their
generator to insert equivalent monitor calls. Diagnostics need a
byte-aligned processor (`p=8`, `64` or `256` works); the installer itself
also handles unaligned processor layers. Reserved memory and extra ticks
can be substantial; allocation overflow is reported by the generator.

The full mode emits a live instruction-layer snapshot before each
application step. After channel service it queries each used channel with
SYS FSTAT, reads its answer in a later tick, then emits the memory answer. The channel-only mode emits only the fixed channel instructions and a
count of ordinary copies, without capturing individual copy rows; its
decoder emits `counts`.
Monitor slots and links are excluded from application counts. Tick
numbers count application steps, not physical diagnostic ticks. Events
are emitted by copycode on the debug channel as the binary `PCS1` stream;
the host decoder only formats that supplied stream:

- `copy tick slot n dst src`
- `channel tick channel_position n buffer moved_bits error`
- `counts copies channels` (channel-only mode)
- `stop idle` or `stop limit`

The channel identifier is a positional channel, not an old IN/OUT slot.
Consumers must use these coordinates and application-step ticks. This is
an explicit format migration from `copy-space`'s host event observer;
the legacy host-trace path in `space_segments.py` cannot parse PCS1. The
included decoder and tests validate the new format. `halt()` and
`checkpoint()` produce cooperative stop records; hitting host `-t` or
interrupting a run produces an incomplete trace, which the decoder
rejects. The library cannot observe an external host stop reason.

## Checkpoints, continuation and external streams

`Program.checkpoint(continuation, reason='limit')` is a terminal report.
It writes a processor layer containing the requested continuation, then
all memory outside the processor, including its own code and records.
Only the processor changes while the report runs, so the rest of the
snapshot is stable. The running reporter stops after output. This is a
checkpoint at an application-chosen boundary, not an asynchronous dump
of any arbitrary image at a host tick limit.

Restore wraps that raw snapshot with `boot_stream`, starts a fresh
ordinary emulator, installs all memory and runs the saved continuation.
An empty continuation restores a stopped processor. The launcher must
preserve/rebind external descriptors and provide remaining application
input at the recorded position. Non-seekable connections cannot be
reconstructed from the space snapshot. Boot input bytes are distinct
from application input bytes and are not included in application trace
counts. A terminal snapshot follows application stdout; its fixed size is
`ceil(space_bits/8)`, so launchers can split it from the end of the stream.

For an existing generated layered image with a known halt label,
`report_image(image, s, p, halt_address, code_base=...)` installs a terminal
report layer in unused memory and redirects the halt link to it.
`run_image(...)` performs stdin boot and returns application stdout plus
the raw snapshot separately. It validates the halt link and unused
reporter region. It never adds emulator options. Choose free reporter memory that the running
application will not overwrite.

## Shared machine description and SYS timing

`tools/machine.py` is the importable source contract (`space-boundary-v1`,
provisional). It resolves `proto.def` for the selected space and processor:
request/answer fields with bit offsets and widths, operation codes, device
descriptors/positions/directions, raw image size, instruction and processor
sizes, and stdin installation framing. Device positions follow **table
order**, not descriptor number. `boundary` and the SYS driver generator
consume this description.

Configure the module location separately from the executable. For example,
from this repository root:

```sh
export SPACE_BOUNDARY_TOOLS="$PWD/tools"
PYTHONPATH="$SPACE_BOUNDARY_TOOLS" python3 -m machine -s 65520 -p 8 > machine.json
PYTHONPATH="$SPACE_BOUNDARY_TOOLS" python3 -m machine -s 65520 -p 8 --check machine.json
```

```python
from machine import describe, require_compatible
machine = describe(65520, 8)
require_compatible(saved_description, 65520, 8)
stdin_position = next(d['position'] for d in machine['channels']['devices']
                      if d['name'] == 'stdin')
```

`protocol_id` identifies the symbolic protocol and tick contract;
`layout_id` also includes resolved parameters and boot framing. Preserve
this description with a generated image/checkpoint. `require_compatible`
and CLI `--check` reject mismatched fields, device tables, schemas and
machine sizes, including edited content with a copied identifier. A
`--protocol PATH` CLI option / `protocol_path` API argument supports explicit
source selection for tooling. It does not change a compiled emulator.
There is no executable handshake: build the emulator and tooling from
the same revision. A JSON description is not binary introspection.

Channel operations are guaranteed complete only at tick end. A SYS read
returns the response committed before that tick, even alongside a new
request. Transfer, dependent FSTAT request and retrieval of its new answer
use separate ticks. The answer's memory buffer is usable the following tick.
One exchange per device, exactly one device endpoint per data copy, and
one SYS request per tick are supported. Answer buffers and every other
memory operand must be pairwise disjoint. FSTAT/SEEK/CLOSE and a transfer
on their target require separate ticks; EXEC side effects must be independent
of concurrent operations. CLOSE SYS disables later ticks' SYS accesses;
reads in its submission tick still receive the old response. Revision 2's
ordered data/control/new-answer pipeline is withdrawn; rebuild old manifests.

## Streaming launch and separate terminal streams

The bounded-memory supporting-tool path uses `boundary.iter_boot(reader, s, p)` and
`transport.run_stream`. The installer retains one processor packet and at
most a 64 KiB payload, handles short reads, skips zero chunks and leaves
application input immediately after the final entry packet. Missing image
bytes remain zero in the freshly allocated space. The `boundary.py boot`
CLI also uses this path. `boot_stream(bytes)` and the older `run_image`
remain buffered convenience APIs; they are not the large-image launcher.

`run_stream` uses POSIX spawn descriptor actions and readiness-based pipe
relay. It drains stdout, stderr, status and snapshot independently. File/
pipe application input must be supplied as an unbuffered binary stream;
it may remain open when the guest exits. It stops reading input on child
exit, propagates source/sink failures, detects incomplete reports and
kills/reaps the child on errors or timeout. No relay threads survive a run.
Readers without `fileno()` must implement bounded, nonblocking `read(n)`;
output sinks accept synchronous writes. Sink backpressure is intentional;
a blocking user callback must return before the timeout can be processed.
The caller owns the source and sinks; use files/stream consumers for bounded
memory. Optional sinks set to `None` discard that stream.

```python
from transport import run_stream
with open('instrumented.bin', 'rb') as image, \
     open('input.bin', 'rb', buffering=0) as inp, \
     open('output.bin', 'wb', buffering=0) as out, \
     open('snapshot.bin', 'wb', buffering=0) as snapshot:
    result = run_stream('/path/to/space', image, s, p,
                        input_stream=inp, stdout=out, snapshot=snapshot,
                        description=saved_boundary_description)
print(result.terminal['exit_code'])
```

The launcher sends only `-s/-p/-t` to the emulator. Descriptor meanings:

| Host descriptor | Device position | Stream |
|---|---|---|
| 0 | s+1 | boot, then application input |
| 1 | s+2 | application stdout |
| 2 | s+3 | debug/trace |
| 3 | s+4 | copycode terminal status |
| 4 | s+5 | optional raw snapshot |

Descriptors >=3 are pre-opened by the launcher and bound according to
`proto.def` mode and table order. The kernel duplicates them above the
entire table, so one binding cannot accidentally create another absent
descriptor; duplicates are closed at shutdown or channel CLOSE. Missing
optional descriptors are unbound. All table positions remain reserved.
`space_bits_for_bytes` reserves six positions today, preserving the bulk
generator's address width. Rebuild images made with the old four-position
layout. Manifest validation rejects incompatible descriptions; the emulator
rejects configurations without channel capacity, but cannot recognize an
incompatible image whose configuration still fits.

`terminal.TerminalFragment(s, p, base, ...)` generates ordinary copycode
with a small code/record buffer, without allocating a full raw image. The
generator links to `fragment.entry` at its terminal boundary and places
`fragment.data` at `base`. `exit_address` and optional
`guest_status_address` identify live 32-bit numeric fields in space;
optional input/output cursor addresses identify 64-bit logical counters.
These fields are copied into the report in explicit preceding ticks.
Without `snapshot=True` only the short terminal record is emitted.

For existing layered images with a known halt label:

```python
from terminal import attach_terminal
with open('image.bin', 'rb') as source, open('instrumented.bin', 'w+b') as target:
    attach_terminal(source, target, s, p, manifest['labels']['halt'],
                    exit_address=manifest['exit_code_bit'],
                    guest_status_address=manifest['status_bit'], snapshot=False)
```

Attachment copies the source with a bounded file buffer, validates its
halt-to-zero link, appends the fragment in unused tail space and redirects
the halt link. The generator guarantees no application write reaches that
tail. A full padded source must be prepared with room for the fragment;
attachment does not guess unused memory. The source stays unchanged.

```sh
PYTHONPATH="$SPACE_BOUNDARY_TOOLS" python3 -m transport instrumented.bin \
  --emulator /path/to/space -s 65520 -p 8 \
  --debug debug.bin --status terminal.bin --snapshot snapshot.bin
```

CLI input defaults to live stdin; stdout stays live application output.
It returns the guest exit code's low byte for an idle terminal report;
limit/error, malformed/truncated records or launcher failure return 125.
Snapshot output is optional: status and guest exit require no dump.
`copy-space/scripts/rv32i/run.py --new-emulator` attaches this report from
its manifest, checks guest status 10 and supports optional `--dump-space`
as a **launcher output**, without passing host dump flags to the emulator.

### SPT1 framing

A completed cooperative run emits exactly one 80-byte record on fd 3,
after its optional snapshot. Its first 56 bytes use struct
`<4sBBHQQ32s` (little-endian):

| Offset (bytes) | Field |
|---|---|
| 0 | magic `SPT1` (4 bytes) |
| 4 | kind: 1 terminal, 2 checkpoint |
| 5 | reason: 0 idle, 1 limit, 2 error |
| 6 | flags (uint16): bit 0 input cursor, bit 1 output cursor, bit 2 guest status |
| 8 | logical space bits (uint64) |
| 16 | snapshot length in bytes (uint64), zero or ceil(s/8) |
| 24 | 32-byte binary layout_id |
| 56 | exit code, 32 bits in **space numeric field order** |
| 60 | logical input cursor, 64 bits in space numeric field order |
| 68 | logical output cursor, 64 bits in space numeric field order |
| 76 | guest status, 32 bits in space numeric field order |

Absent optional fields are zero and decode to `None`. Copying numeric
fields directly preserves arbitrary live guest values; unlike the header,
their bit representation is LSB-first within MSB-first physical bytes.
Use `decode_terminal` rather than native integer unpacking for those fields.
The shared machine description includes this framing and its layout ID.
A different version/length/identity is rejected, not guessed.

Fd 4 carries only raw snapshot bytes, no prefix. With `snapshot=True`,
the first processor packet is the supplied continuation, followed by all
remaining memory, including terminal copycode. Default continuation is
zero (a terminal dump). A nonempty explicit continuation marks kind 2.
The record supplies length, identity, reason and any caller-maintained
logical cursors. The relay verifies total snapshot length. A killed run
with no complete terminal record is incomplete even if it emitted data.

SPT1 framing alone does not add dynamic checkpoints. The optional RV32I
commit monitor now maintains logical cursors and counters, emits SPT2 and
supports segmented resume/forks; see [the checkpoint guide](checkpoints.md).
A host tick limit cannot create a valid checkpoint. Existing finite
`Program` demos and buffered reports keep their earlier stdout snapshot
convention; new supporting launchers use the separate SPT1/SPT2 and fd-4 path.

Tests stream complete sparse images and full snapshots at 8/64/256 MiB
through one ordinary executable. Measured peak Python relay allocations
are about 345 KiB, checked below 2 MiB independently of image/snapshot size.
The emulator's own space allocation and caller-owned input/output storage
are separate from relay memory.


## Dynamic tracing beyond the finite fixture

`Program` and PCS1 describe finite fixture schedules. Dynamic RV32I now uses
PCS2 generator-inserted copycode from `tools/dynamic_trace.py`, including
live patched operands, repeated branches, full/channel capture and streaming
audit. See [the dynamic tracing contract](tracing.md). Completion requires
the final PHT1F marker after SPT and the optional snapshot, not merely the
earlier trace end record. The kernel still has no host trace observer.

`run_stream` exposes whole-child CPU/wall metrics and boot byte/tick counts.
PHT1 phase markers give arrival intervals only; they do not measure phase
CPU. Raw direct-spawn wait4 RSS can include the pre-exec Python address
space. [Core benchmarks](core-benchmarks.md) retain this raw metric and
do not present it as emulator-only memory.


## Strict interval correction (contract revision 2)

The source-side machine identity now includes pairwise-disjoint memory
operands, so old manifests are incompatible. Installer framing is
`space-stdin-install-v2`: a final partial byte is embedded in a NOP field
and copied as ordinary bits, avoiding a rounded device transfer beyond
logical space. Such a two-tick record yields an empty payload fragment;
joining fragments is unchanged and fragment counting still gives boot ticks.

Whole-space outputs must not read the next-layer link source in the same
tick. The report/finite-trace helpers use a two-tick processor transition
when needed: first output and self-erase/enable, then load the next layer.
TerminalFragment.report_ticks records actual execution cost. Partial final
bytes are prepared in a zero-padded scratch byte before snapshot output.
Only processor state changes during the resulting snapshot transfer.

The temporary test harness in tests/check_local_schedules.py validates every
actual memory operand, including all service layers, with a separate C codec
and interval oracle. It adds no option to the production emulator.
