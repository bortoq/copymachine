# Standalone core benchmark baseline

Release 0.1.0 baseline, 2026-10-18: Linux x86-64, GCC 12.3,
`-std=c11 -Wall -Wextra -O3`, 5 repeats and 100000 compute ticks.
[The raw report](measurements/core-0.1.0.json) preserves every run,
boot-only run, medians, binary/source hashes, compiler version and build
flags. This is a baseline for this machine/build, not a performance promise
on other hosts or a measurement of any guest application.

```sh
make benchmark
# A new output directory is required on subsequent runs:
make benchmark BENCH_OUTPUT=tmp/benchmark-next BENCH_REPEATS=5 BENCH_TICKS=100000
```

Or invoke `python3 -B tools/benchmark.py --emulator /path/to/space --output
/path/to/new-directory --repeats 5 --micro-ticks 100000` as one command.
The tool imports no external generator or guest interpreter. The default
suite validates the executed workload templates with the independent
interval/channel-conflict harness at reduced tick counts; timings use the
ordinary selected emulator without that instrumentation.

Workloads separate sparse/dense processor fetch/dispatch (a=16/26,
P=64/256), 1024/65536-bit aligned and unaligned copies, and alternating
4096-byte stdin/stdout transfers with distinct read/write ticks. For the
IO workload, rounds are ticks/20 (5000 pairs here). Ordinary data sources,
destinations and control links are pairwise disjoint. No SYS request/answer
pipeline or application monitor is involved.

| Workload | Estimated compute CPU, ms |
|---|---:|
| fetch/copy a=16, P=64, active=0 | 31.204 |
| fetch/copy a=16, P=64, active=63 | 59.007 |
| fetch/copy a=16, P=256, active=0 | 110.795 |
| fetch/copy a=16, P=256, active=255 | 224.964 |
| fetch/copy a=26, P=64, active=0 | 66.229 |
| fetch/copy a=26, P=64, active=63 | 91.769 |
| fetch/copy a=26, P=256, active=0 | 253.649 |
| fetch/copy a=26, P=256, active=255 | 356.572 |
| bitcopy 1024 bits, offset 0 | 9.322 |
| bitcopy 1024 bits, offset 3 | 9.727 |
| bitcopy 65536 bits, offset 0 | 16.131 |
| bitcopy 65536 bits, offset 3 | 16.533 |
| IO 5000 pairs × 4096 bytes | 10.792 |

Each CPU estimate subtracts the median user+system CPU of boot-only runs
from the corresponding workload median. Both raw components are retained;
small or negative differences are measurement noise, not negative work.
Wall times include launch/boot/pipe handling and are also retained. Runs
are sequential, CPU is not pinned, and host load/frequency and compiler
choices matter. Compare repeated raw results with the same environment;
there is no flaky wall-time threshold in CI.

Raw wait4 peak RSS may include the pre-exec Python parent's high-water mark;
it is not evidence of the emulator's own memory footprint. The report labels
that limit. This baseline makes no external copy-space speedup or memory
claim. Superseded application measurements and integration scripts were
removed from the working tree; Git history preserves them. Consumer
performance and migration remain outside core release acceptance.
