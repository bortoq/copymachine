# Independent core verification

Run from this checkout:

```sh
make check-core
```

This target builds the emulator and test harnesses, then runs the independent
kernel checks and existing SYS unit tests. It needs the documented Linux
host, a compiler, make and Python's standard library. It does not import
`tools/machine.py`, copycode generators, manifests, RV32I interpreters or
anything from a neighboring project. Every actual tick in the core engine
tests is first checked by `tests/interval_reference.h`: all memory source
and destination intervals must be pairwise disjoint, including read/read. `make check` includes these checks
alongside the local copycode/transport integration fixtures.

## Bit copying

`tests/test_bitcopy.c` compares production bitcpy against a bit-at-a-time
reference. Its 43840 deterministic cases cover all 64 source/destination
alignment pairs, lengths 0–192 and longer edge lengths through 65536 bits,
plus seeded random lengths/offsets. Cases use separate arrays and disjoint
intervals in the same array, including adjacent intervals sharing a byte.
Whole-array comparisons verify unchanged source data and destination bits
outside the copied interval. Exact-size allocations additionally expose
lookahead/overwrite bugs to sanitizers.

## Decoding and ticks

`tests/test_engine.c` uses its own bit encoder/decoder and reference copier.
It does not use production field or copying helpers to construct expected
results. It includes engine.c solely to reach the private decoder functions
without adding a testing interface to the emulator.

- 38400 decoder cases exercise address widths 5–64, every bit alignment,
  zero/max/random fields and tight/padded windows. These include both fast
  decoders and the wide per-bit fallback. Small isolated decoder windows
  test field widths that would require impractical full machine allocations;
  they are decoder unit tests, not claims of enormous-machine execution.
- 864 complete-memory comparisons exercise independent scheduled copies
  and processor replacement across narrow/wide formats and 7/8/9/64 slots.
  Sources are allocated in disjoint per-slot regions. The reference fetches operands before applying writes and compares every
  byte after each tick, including unchanged data and padding.
- Seed tests compare the entire initial memory, input consumption and
  byte-rounded installation. Operand patches before/after the affected slot
  take effect on the following tick. A processor-clearing copy cannot
  suppress another already-fetched instruction; all-NOP stops next fetch.

## Channels and host resources

The same harness executes the actual full tick for 42 channel/stream cases,
using independently encoded SYS requests and decoded responses:

- Transfer, subsequent FSTAT request and subsequent answer retrieval,
  permuting their slots 0/3/7 for short input,
  EOF, EISDIR, ordinary output, ENOSPC and EPIPE; independent ordinary memory
  work runs alongside and the whole memory result is checked.
- Initial zero response, stored response reads across later transfers,
  explicit NONE response reset, IOCTL/unknown-op errors. Concurrent
  request/answer reads return the previous response, including NONE reset.
  Independent pre-tick record decoding rejects FSTAT/SEEK/CLOSE combined
  with a transfer on their target even when memory buffers are disjoint.
- Present/absent optional descriptors, no accidental binding of missing
  fd 4, logical CLOSE versus original-descriptor ownership, and data access
  after SYS CLOSE. The closing tick still delivers the previous response;
  later SYS reads leave their memory buffers unchanged.
- A 40000-byte request with short input crosses the 32768-byte internal
  buffer boundary at an unaligned memory address; its unwritten suffix is
  preserved and the received bytes are written back exactly.
- A nonblocking pipe accepts a prefix then returns EAGAIN. FSTAT must
  report both the progress and the error; the sink's actual bytes are checked.

The existing `tests/test_sys.c` adds SEEK, EXEC and other control behavior and
other error/seed checks. Tests use Linux `/dev/full`, directory reads and
ordinary files/pipes; required fixture setup fails explicitly in the new
harness rather than silently skipping its cases.

## Process and configuration

`tests/test_core_cli.py` runs 935 process cases with a formula-based oracle:
small configurations, powers-of-two and channel-capacity edges, processor/
seed limits, malformed values and 64-bit numeric limits. It independently
encodes a raw output/stop program to verify that seed counts toward `-t`,
the entire last active tick completes, all-NOP stops, and both normal stop
and tick limit return exit 0.

Huge admissible dimensions are tested with a 128 MiB RLIMIT_AS to force a
bounded allocation failure. These tests distinguish exit 1 for allocation
from exit 2 for invalid configuration; they do not allocate huge spaces.
They found and now guard the full-width channel-capacity bug: when a=64,
`2^a-S` must be computed without representing `2^a` or shifting by 64.

## Verification recorded on 2026-10-18

The full suite is checked with GCC and Clang, in release and ASan/UBSan
configurations. The runner honors the selected executable and compiler,
preprocessor, compile and linker flags. See [build and CI](build.md) for
commands, the toolchain matrix and local versus CI leak-check settings.
Native configuration probes use RLIMIT_AS; ASan runs the same probes with
its return-NULL allocation mode because shadow memory needs a larger virtual
address space. No configuration/allocation probes are silently skipped.

These tests exercise valid programs and specified error responses. They do
not require memory-safety diagnostics for programs violating the trusted
machine's bounds, overlap or simultaneous-operation rules. See the
[public contract](emulator-contract.md) and [release roadmap](roadmap.md).


## Critical interval correction, revision 2

Earlier verification accepted shared read sources and therefore did not
establish conformance to the positional machine. That claim is withdrawn.
The corrected random inputs are independently checked before each tick.
`tests/test_schedule.py` compares the tooling validator against a separate
all-pairs set oracle on 6000 schedules; complete/partial source overlaps,
self overlaps, cross-role intersections and adjacency have explicit cases.
The C validator has its own negative/positive regressions. Invalid schedules
are rejected as test input, not executed as evidence of machine capability.

`tests/check_local_schedules.py` builds a temporary fixture harness that
checks actual fetched operands before executing each tick. It runs local
boot, stream, snapshot, full/channel trace, shell-driver and CLI fixtures,
including resumed images and the 8/64/256 MiB cases. This test harness is
not a second public emulator build or a host diagnostic mode. `make check`
runs it; the production binary and CLI keep the trusted-program model.

The machine description includes the strict interval rule; old manifests
are incompatible. Older external-generator benchmark and integration
claims require revalidation by their owners; see [the consumer handoff](consumer-interval-handoff.md).

## Channel timing correction, revision 3

The former data/control/new-answer pipeline tests were incorrect and are
superseded. Whole-memory tick oracles check old-response visibility at request
submission and new-response visibility on a following tick. Local executed
schedule checks also decode SYS targets before execution to reject control
versus target-transfer conflicts. This remains test tooling, not a production
validation mode. The interval correction and its checks remain in effect.
