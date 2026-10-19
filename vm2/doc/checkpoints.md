# Local snapshot and resume fixtures

These are independent emulator integration fixtures, not a kernel snapshot
API or an application runner supported by this project. The
[public contract](emulator-contract.md) defines the kernel. The standalone
[boot/copycode guide](boundary.md) documents full-image installation.

`TerminalFragment` in `tools/terminal.py` emits a full logical-space image,
an explicit processor continuation and a terminal/status record. It copies
memory through ordinary output channels. `tools/checkpoint.py` is retained
as test support for archive validation, immutable resume and fork. Consumer
generators and product runners belong to their own repositories; their
migration requirements are in [the handoff](consumer-interval-handoff.md).

## Boundary and streams

A cooperative snapshot follows a program-defined boundary, after previous
copies have committed. The program chooses its continuation and report
sources; the host does not infer guest execution or manufacture a continuation.
Use `TerminalFragment.report_ticks` for physical reporting cost rather than
the count of stored layers. Sources and destinations remain pairwise disjoint;
SYS requests and dependent new-response reads require separate ticks.

The in-space report supplies logical input/output byte cursors and counters.
A new process rebinds a seekable, content-hashed input at the logical input
cursor, then concatenates boot and the remaining input. Host read-ahead or
pipe buffering does not count as logical input consumption. Stdout is written
to a new delta file and checked against the cursor increment. Arbitrary live
socket replay is outside this file-based test fixture.

The test helper `execute_segments` can resume with `image=None` once a full
snapshot and its validated manifest/ancestry exist. Forking never modifies
the parent archive. Existing output directories cannot be overwritten.
A host tick limit, timeout, signal or incomplete report publishes no checkpoint.

## Archive and status

Each local segment archive contains:

| File | Content |
|---|---|
| `space.bin` | Full logical space, including continuation |
| `stdout.bin` | Segment output delta |
| `status.bin` | Copycode-emitted terminal record |
| `debug.bin` | Separate trace/debug stream |
| `checkpoint.json` | Schema, identities, parent, report and file hashes |

Validation checks full lengths, file hashes, boundary/layout identity,
input identity, saved processor, cursors/counters and parent ancestry.
Ancestry references currently use absolute paths. A zero-processor terminal
snapshot does not become a running checkpoint by changing metadata.

SPT2 retains the first 80 bytes/field orders of SPT1, changes the magic to
`SPT2`, and appends numeric 64-bit counters at byte offsets 80 (committed),
88 (read operations), and 96 (write operations). Its length is 104 bytes.
Input/output cursors remain at 60/68 and status at 76. These are fixture
protocols, not additional emulator services or compatibility promises.

`make check` runs `tests/test_checkpoint.py`, `test_transport.py` and
`test_dynamic_trace.py`: independent local continuation, immutable forks,
corruption/incomplete-run rejection, separate streams and traced resume.
No external guest generator or compiler is needed. [PCS2 tracing](tracing.md)
records optional trace hashes/audits and cumulative segment totals.
