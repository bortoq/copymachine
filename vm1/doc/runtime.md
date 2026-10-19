# Common four-index runtime: verification and measurements

2026-10-19. The usable base emulator is now `src/runtime.c` plus one compile-time
backend. The [public contract](emulator-contract.md) is normative. The former
native-word/LDR1 machine remains an isolated test control under build/legacy;
it is not the public vm1 executable.

## Implemented boundary

- `make` selects bitcopy; BACKEND=network compiles the verified two-phase kernel.
  Both variant directories have configuration stamps. Switching back without
  clean refreshes vm1, and changing/restoring compiler flags rebuilds it.
- Runtime `-s`, `-p`, `-t`, four A-bit fields, full fetch, current-tick commit,
  all-NOP stop and stdin seed; no external sorter or host image parser.
- MSB-first stream/space positions, LSB-first numeric fields, degenerate external
  channel operand; SYS moved width A. This is a new ABI, not old-image compatibility.
- SYS and pre-bound stdin/stdout/stderr/fd3/fd4, complete-at-tick-end semantics,
  previous committed answers, short reads/errors/EOF and logical CLOSE.
- Bitcopy uses packed memory plus O(P) decoded records; no per-bit network state
  or fabric is linked/allocated. Network keeps the same 16-bit position state
  and reuses the old classification/splitting/stable-data-ordering algorithm.
  The common runtime reads the processor snapshot; the network kernel consumes
  each slot independently. There is no per-instruction network replay.

Internal `[length,destination,source]` arrays are normalized host IO/bitcopy
records, not a second supported instruction format. Network receives the original
four-endpoint snapshot, without synthesizing memory endpoints from length.
Host snapshot/control allocations are not an RTL resource/synthesis claim.

## Checks

`make check` runs both production variants and the retained mechanism controls.
Local GCC 12.3.0 strict C11 `-O2` passed:

- 43,840 independent bitcopy cases: every alignment, exact allocations, edges
  and untouched bits, including byte-sharing adjacent half-intervals.
- 709 bitcopy and 708 network whole-memory snapshot cases with an independent
  codec/range validator. Small N=240/256/1040, default N=65520, all 128 slots,
  randomized valid layers, repeated cycles and processor erasure/next-tick stop.
  Bitcopy also checks a 64 MiB image budget with wide, unaligned addresses.
- Exact-size numeric codec windows: widths 1..64 at offsets 0..7.
- Ported SYS checks on both implementations: direct data/control, input/output
  errors, SEEK, FSTAT, IOCTL, EXEC including shifted commands, CLOSE SYS with an
  old response read, persistent answers and stdin seed.
- 51 real-process checks of both CLIs: finite input/output boot, final tick,
  later-tick consumption, old/new SYS responses, short reads/EOF, CLOSE SYS,
  stderr plus inherited status/snapshot fd3/fd4, small dimensions, invalid flags
  and unsupported network profiles. Bitcopy startup also covers 64/256 MiB image
  budgets, P=256 and a non-byte-sized S. These do not certify large applications.
- Build selection network/default/network/bitcopy and compiler-flag changes.
- Existing machine/network/loader/compiler controls, full-memory addressing
  oracle and structural network checks for several N and K. The old 454-step
  schedule proof remains a mechanism result, not a timing claim for host IO.

ASan/UBSan runs the full same suite. Local LeakSanitizer cannot start under the
execution environment's ptrace restriction; the completed local run disables
only leak detection, retaining address/undefined-behavior checks. CI is configured
for GCC/Clang release and sanitizers with leak detection enabled; it has not been
run on GitHub as part of this local change. Clang is not installed locally.

Reproduce:

```sh
make check CFLAGS='-Wall -Wextra -Werror -pedantic -std=c11 -O2'
make clean
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
  make check CFLAGS='-Wall -Wextra -Werror -pedantic -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie'
```

## Measurements of the new runtime

AMD Ryzen 5 PRO 5650U, GCC 12.3.0, strict C11 `-O2`. `make benchmark` saves
process and actual production-cycle measurements under build/measurements.
Process order is shuffled, seven samples per fixture/variant. Pipes carry boot
and output. CPU uses child user+system time; wall time includes process launch
through exit. Peak RSS is measured by a separate equally checked launch under
GNU time, avoiding the inherited Python-parent RSS floor.

| Whole process, S=65520 / P=8 | Bitcopy | Network |
|---|---:|---:|
| NOP seed, wall median | 0.952 ms | 125.273 ms |
| Finite installer + one-byte output, wall median | 1.011 ms | 194.704 ms |
| Peak RSS, finite output median | 1408 KiB | 65200 KiB |
| Executable size | 27136 bytes | 46024 bytes |

The NOP fixture includes one active stdin seed tick. Network startup includes
internal fabric generation; bitcopy pays neither its time nor memory.

The core benchmark measures `computation()` with actual production fetch and
memory backend, excluding initialization/IO. P=128, two warmup cycles, five rounds
of 16 measured cycles. Expected entire memory is independently constructed before
timing and compared after each round. Repeated layers have unchanged sources.

| Cycle fixture | Bitcopy, ms | Network, ms |
|---|---:|---:|
| one short copy | 0.006016 | 21.843635 |
| 128 short copies | 0.006723 | 21.949790 |
| 128 long copies | 0.008387 | 22.930719 |
| one long unaligned copy | 0.006403 | 22.223759 |

These are workload/build-specific host C measurements. The large difference is
expected: bitcopy handles selected buffers, whereas network visits positions
and the fabric. It does not predict end-to-end vm2/RV32I/GCC speed, FPGA latency,
area or energy. The previous 6–7% CLI improvement compared two historical network
versions, not network versus bitcopy.

Saved [metadata](measurements/runtime-stage1/metadata.json),
[summary](measurements/runtime-stage1/summary.json),
[raw process samples](measurements/runtime-stage1/process.csv),
[bitcopy cycles](measurements/runtime-stage1/bitcopy-core.csv),
[network cycles](measurements/runtime-stage1/network-core.csv).

## Remaining ownership

vm1 is ready to be the base machine under this contract. vm2 is now implemented
as guest copycode in the sibling project; copy-space must repair/rebuild its schedules and
images. Common guest libraries now belong to the separate copycode project;
application extraction remains a later workspace milestone. Source-release
packaging is verified below. Actual hardware synthesis remains separate work.

## Source release verification (stage 2)

`make distcheck` passed on 2026-10-19: checksum verification, full suite from
a clean archive in a directory containing spaces, installation and real stdin
execution of both bitcopy/network, staged documentation/protocol checks and
byte-identical repack. `make install` supports prefix/bindir/docdir/DESTDIR;
`make clean` removes dist as well as build. GCC/Clang CI includes a release
distcheck job; GitHub execution is not claimed. Shared guest software now
belongs to the separate copycode project; vm1 keeps only independent core
fixtures and a minimal example. vm2 interpretation now belongs to the sibling
vm2guest project; application extraction remains later workspace work.

Чтение числового поля `space_get` выполняется по пересекающим его байтам:
обращается порядок битов каждого байта, затем извлекается нужная часть.
Это сохраняет MSB-first поток и LSB-first поля, включая ширины 0 и 64
и поля у самой границы пространства. Регрессия сравнивает его с независимым
побитным эталоном по всем допустимым смещениям/ширинам в случайных буферах.
