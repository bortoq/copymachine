# Current verification summary

The normative behavior is [contract revision 3](emulator-contract.md), with
[the positional model](addressing.md). Superseded audit narratives, design
proposals and external benchmark claims are available in Git history.

## Corrected machine invariants

- Every active memory source/destination interval in a tick is pairwise
  disjoint, including source/source. Read-only fan-out is invalid.
- Instructions are fetched before execution. Channel copies complete by tick
  end; SYS reads observe the response committed before that tick. Dependent
  transfer, FSTAT and new-response retrieval require separate ticks.
- Production execution trusts program bounds/independence. Test-only operand
  checks do not add a validating machine or diagnostic emulator build.

## Independent and integration checks

`make check-core` runs 43840 bitcopy oracle cases, 38400 decoder cases,
864 whole-space tick comparisons, 42 channel cases and 935 process/config
cases, plus SYS checks, a 6000-case schedule oracle and cleanup regressions.
`make check` also exercises stdin boot, live IO, independent executed-operand
validation, trace, full snapshots, immutable resume/fork, and 8/64/256 MiB
fixtures. These require no neighboring repository. Full details are in
[core verification](core-verification.md) and [build/CI](build.md).

GCC/Clang release and ASan/UBSan configurations are tested. Local LSan is
disabled under ptrace; CI enables it. Native huge-allocation probes use
RLIMIT_AS; ASan uses its return-NULL mode, without omitting process cases.

`make check-dist` tests a clean source archive without Git, compares the
shipped generated header, checks staged install/run and deterministic repack.
Source release identity and dependencies are in [releases](releases.md).
The retained [core baseline](core-benchmarks.md) includes raw measurements,
compiler flags and binary/source hashes; raw wait4 RSS is not emulator-only
memory evidence. External compatibility remains a consumer task described
in [the handoff](consumer-interval-handoff.md).

## Cleanup

Obsolete DATA scatter code, external benchmark runners, their unused
profiling module, old plans and superseded measurements were removed.
Only the current baseline and concrete consumer-compatibility evidence remain.
Local agent dependencies/session state and old multi-gigabyte scratch outputs
were removed from the working tree. `make clean` removes generated scratch,
archives, binaries, objects and bytecode without deleting sources, seed
fixtures or SCM/environment state. A regression check covers custom output
paths, repeated cleanup, source protection and directory symlinks.
