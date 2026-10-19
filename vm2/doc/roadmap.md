# Emulator roadmap and release preparation

The project develops the emulator. Copycode, generators, application
runners and product migration belong to their respective projects.
The current normative public interface is [the emulator contract](emulator-contract.md),
revision 3. Superseded design notes are available in Git history, not in
the supported source distribution.
The positional address-space definition remains in `doc/addressing.md`.

**Critical interval error corrected (2026-10-18):** revision 1 incorrectly
permitted shared sources. Contract revision 2, corrected local schedules
and independent executed-operand checks now enforce the model. See 0.0
for evidence and the external consumer handoff. This correction does not
restore the withdrawn compatibility claims for external generators.

**P0 channel timing corrected (2026-10-18):** channel copies are guaranteed
complete only at tick end. Contract revision 3 removes the former
same-tick data → SYS request → new answer pipeline. Section 0.0a records
the correction and new verification; 0.1–0.3 are revalidated. External
consumer compatibility still requires its owners to repair and rebuild
schedules under both corrections.

## 0. Preparation for publication and use

This is the current release plan. Publication does not depend on completing
pForth/copy-c/GCC/Linux migration or optimising external generators. A
compatibility copycode implementation of the old copy-space machine is a
separate consumer deliverable, not a kernel feature. Archived integration
experiments are evidence, not additional emulator release gates.

### 0.0 P0 — Critical interval error — CORRECTED 2026-10-18

Discovered 2026-10-18. Two ordinary copies must not share even read-only
source positions in the same tick. For every active instruction i, let
S_i=[src_i,src_i+n_i), D_i=[dst_i,dst_i+n_i). All members of the family
{S_i,D_i} must be pairwise disjoint, including S_i versus S_j for i != j.
Touching half-open boundaries are allowed; sharing any contained position
is not. NOPs contribute no intervals. Slot-order independence alone is a
weaker condition and is insufficient.

The erroneous revision 1 explicitly permitted shared read-only sources;
its random tick tests could generate intersecting sources. Those earlier
tests and affected copycode/measurements described a machine VM1 cannot
implement. They are superseded or withdrawn by this correction. This is a correctness/compatibility error, not a
performance optimisation or an optional tightening of the model.

- [x] **Emulator coder + writer, before other release work:** correct the
  public contract, README, test methodology and relevant code comments to
  require the complete interval invariant. Record that previous shared-source
  claims were erroneous. Check against `~/work/vm1` without changing VM1's
  model to accommodate the erroneous emulator contract.
- [x] **Core test owner:** independently validate all active source and
  destination intervals of each generated ordinary-copy tick, before using
  that tick as conformance evidence. Check source/source, source/destination
  and destination/destination intersections, including within one copy.
  Include fully/partly shared sources as rejected test-schedule cases and
  adjacent disjoint intervals as accepted cases. The test validator must
  not depend on a generator's own placement checks.
- [x] Repair the random tick oracle inputs and audit all local fixtures,
  installers, monitor/report fragments and examples for this assumption.
  Review processor accesses and channel/SYS phases explicitly against the
  model; do not silently exempt shared memory sources as "read-only".
  Repeated uses of a value need a conforming schedule, not same-tick fan-out
  from one interval.
- [x] Identify affected external generators/integrations as consumer work,
  with concrete offending schedules and the corrected contract. External
  product migration is still outside this repository's scope.
- [x] Re-run independent core and local integration checks using validated
  schedules. Revalidate affected compatibility and benchmark claims; retain
  old results as historical evidence only where their schedules violate
  the corrected model. Close 0.1–0.3 again only with corrected evidence.
- **Acceptance:** no current contract/example/conformance claim permits
  shared source positions in an ordinary-copy tick; the independent schedule
  validator detects both complete and partial source overlap; all claimed
  valid local schedules satisfy the full invariant. The emulator may retain
  its trusted-program design: mandatory production overlap checks or a new
  diagnostic build are not implied. Execution of an invalid schedule is
  outside the contract, never an advertised machine capability.

- **Corrected evidence:** the independent C operand validator runs before
  every tick of core engine tests. A separate temporary fixture harness
  validates boot, finite/dynamic trace, snapshot, resume/fork and shell
  programs at execution, including 8/64/256 MiB. Python validation has a
  separate 6000-case all-pairs oracle. Invalid shared-source schedules are
  rejected by tests/generator interfaces, not blessed by accidental C results.
  Snapshot/link and tracer fan-out are serialized; installer tail bits no
  longer use an out-of-range rounded transfer. `make check` and ASan/UBSan
  C checks pass. Old manifests are incompatible; old base/IO speed and
  compatibility claims are withdrawn. Corrected standalone microbenchmarks
  are saved separately. [Consumer handoff](consumer-interval-handoff.md)
  records concrete shared-source sites in copy-space; that external generator
  was not modified. The production core retains its trusted-program model.

### 0.0a P0 — Channel completion at tick end — CORRECTED 2026-10-18

Discovered 2026-10-18. Like ordinary copies, a requested copy to/from a
channel is guaranteed to complete only by the end of its tick. Programs
must not depend on a channel operation completing before another operation
of that same tick. Disjoint memory buffers do not remove dependencies
through channel state.

The former `sys_tick()` completed device transfers, then serviced SYS,
then published the new SYS answer. This permitted transfer → FSTAT → new
answer in one tick, request → new answer in one tick, and immediate
same-tick effects of SYS CLOSE. Those guarantees were explicitly documented
and tested but did not follow from the required completion model. VM1's
software loop reads input before its copy cycle and writes output after
it; that implementation is not evidence of intermediate channel readiness
or of support for the emulator's SYS pipeline.

- [x] **Emulator coder + writer, before other release work:** define the
  channel tick contract without intermediate completion guarantees.
  Specify which simultaneous accesses to a channel are valid, what state
  an answer read observes, and when control effects become visible. A
  request's new response must not be promised to a read in the same tick.
  Fetch all instructions before execution as before, and retain the full
  source/destination memory interval invariant from 0.0.
- [x] **Emulator coder:** replace the externally observable ordered SYS
  subphases with behavior conforming to that contract. Separate operations
  that depend on completed channel work across ticks: transfer, subsequent
  FSTAT request, and subsequent retrieval of that request's new answer.
  Audit CLOSE (including SYS itself), SEEK, EXEC, persistent responses,
  short transfers, EOF and errors for the same timing issue. Internal C
  execution order must not become an extra machine guarantee.
- [x] **Core test owner:** replace tests blessing the same-tick pipeline
  with an independent tick-boundary state oracle. Check slot permutations,
  old versus new responses, control visibility, short/error transfers and
  next-tick use of input/answers, including processor self-writes. Verify
  that disjoint buffers alone cannot legitimize channel-state dependencies.
- [x] **Writer, with coder review:** revise the normative contract and its
  revision/compatibility identity, headers, README and channel/trace/snapshot
  guides. Explicitly withdraw the earlier data/SYS/answer phase guarantees.
- [x] Repair affected local test fixtures, boot/report/trace/snapshot
  examples and supporting generators so release checks exercise the new
  timing. Record concrete migration instructions for external owners;
  external application implementation remains outside this repository.
- [x] Re-run independent core and local integration checks; reassess
  compatibility, tick counts and measurements affected by added ticks.
  Close 0.1–0.3 again only after this timing correction is verified.
- **Acceptance:** no supported schedule, example, contract or conformance
  test relies on completion of a channel operation before the end of its
  tick. New response/status dependencies span tick boundaries. Valid
  independent operations retain slot-order independence, the full interval
  invariant and existing fetch-before-execute semantics. No diagnostic
  emulator build or new host inspection service is required.

- **Corrected evidence:** `sys_tick()` reads the previously committed
  response before processing any request. Concurrent request/answer reads
  receive the old response; CLOSE SYS preserves closing-tick reads and
  disables later ones. Target FSTAT/SEEK/CLOSE versus transfer conflicts
  are invalid schedules, independently detected from pre-tick records by
  the temporary executed-schedule validator. Production retains its trusted
  program contract. Whole-memory oracles cover 42 channel cases, old/new
  responses, NONE, multiple reads, processor erasure, persistent responses,
  EOF/error/partial progress and closure. `make check` passes, including
  local trace/snapshot/resume and 8/64/256 MiB fixtures under independent
  executed-schedule validation. C engine/SYS checks pass ASan/UBSan with
  leak detection disabled because of the local ptrace restriction.
  Local FSTAT reporters use separate request/read ticks; PCS2 costs 20
  ticks per original layer (body offset 11 unchanged). Revision 3 changes
  protocol/layout identities; old manifests are rejected by tooling.
  Standalone five-repeat core results are preserved in
  [the current baseline](measurements/core-0.1.0.json). External migration
  instructions are in the [consumer handoff](consumer-interval-handoff.md);
  no sibling project was changed.

### 0.1 Public emulator contract — completed, corrected by 0.0 and 0.0a

- [x] Correct and revalidate channel timing under 0.0a (revision 3).

- [x] **Emulator coder + writer:** publish one normative description of the
  implemented machine and process interface: instruction/byte encoding,
  dimensions, initial state and stdin seed, tick phases, dependency rules,
  stopping, inherited descriptors, data/SYS records and operations, errors
  and exit codes. State program obligations and behavior outside them.
- [x] Distinguish kernel guarantees from loader/trace/snapshot/guest protocols;
  define compatibility expectations without inventing a runtime handshake.
- **Result:** `doc/emulator-contract.md`, revision 3, checked against
  `config.c`, `engine.c`, `sys_ctrl.c`, `space.c` and `proto.def`. README
  links to it. It records current details such as exit 0 on tick limit,
  full-record SYS access, byte-rounded transfers, CLOSE ownership and
  continued data access after SYS CLOSE. Revision 3 changes SYS timing while
  preserving instruction/record fields; consumers must rebuild schedules.

### 0.2 Consistent public documentation — completed, corrected by 0.0 and 0.0a

- [x] Remove superseded channel phase guarantees and recheck examples
  under 0.0a; update compatibility, tracing clocks and snapshot guidance.

- [x] **Writer, with coder review:** reconcile README and design material
  with the normative contract. Remove active claims of unimplemented
  `--proto`, XPROTO/PING/version negotiation and other historical features.
  Clearly separate implemented behavior, proposals and historical notes.
- [x] Put a short standalone build/run example and supported-host statement
  in the entry documentation; remove dependence on a sibling checkout.
- **Acceptance:** every advertised emulator option/service exists, examples
  run against the published sources, and consumers can find the complete
  contract without reconstructing it from the roadmap.
- **Result:** README now states the verified host/dependencies,
  documents the actual CLI/status behavior and contains standalone examples.
  Historical channel/boot drafts and superseded integration guides are kept
  in Git history; current local fixture guides state their scope.
  The runnable README and finite diagnostic examples were checked against
  this repository's executable. Release toolchain expansion stays in 0.4.

### 0.3 Independent core verification — completed, revalidated under 0.0 and 0.0a

- [x] Replace the affected SYS phase expectations and revalidate under
  0.0a; passing legacy pipeline tests are superseded.

- [x] **Emulator coder:** compare bit copying against a simple independent
  reference across source/destination alignments, lengths and byte edges,
  using valid nonoverlapping intervals and checking unaffected bits.
- [x] Check instruction decoding and fetch-before-execute semantics,
  processor self-writes, configuration boundaries, channel errors and
  channel tick-boundary visibility and slot-order independence.
  Retain meaningful existing tests.
- **Acceptance:** core conformance checks run from this repository alone;
  external copy-space tests remain optional integration evidence.
  Invalid programs outside the trust contract are not required to fail
  safely; do not silently turn this into a new validating machine.
- **Result:** `make check-core` runs independent bitcopy, decoder/tick,
  full-tick SYS/stream and process/configuration oracles without consumer
  imports. Cases cover 43840 bit copies, 38400 decoder inputs, 864 whole-space
  tick comparisons, 42 channel cases and 935 process/configuration cases,
  plus existing SYS tests. Full-width channel capacity now uses safe
  unsigned subtraction; admissible a=64 configurations reach allocation
  failure instead of being rejected as lacking device positions. New C
  harnesses pass ASan/UBSan; leak checking is unavailable under ptrace here.
  Scope and reproduction: [core verification](core-verification.md).

### 0.4 Build and CI — completed 2026-10-18

- [x] **Emulator coder:** make tests exercise the selected build flags and
  binary instead of unconditionally replacing them with a hard-coded build.
- [x] Declare the supported host/compiler baseline and dependencies. Check
  GCC and Clang and run ASan/UBSan on valid-program tests. Keep one emulator
  implementation/build interface; sanitizer flags are verification tooling,
  not a restored diagnostic emulator with extra host services.
- **Acceptance:** a clean checkout builds and passes the selected checks
  with each declared toolchain; CI actually exercises those configurations.
  Additional platform ports are optional after the first release.

- **Result:** Make and all test harnesses honor CC/CPPFLAGS/CFLAGS/LDFLAGS/
  LDLIBS. The runner checks an explicitly selected executable without
  rebuilding it; integration children inherit the chosen absolute path.
  Make tracks compiler/flag changes and supports separate BIN paths;
  `check-built` verifies an existing binary without building the product.
  Default flags support both compilers without an LTO linker dependency.
  CI now runs four clean-checkout jobs on Ubuntu 24.04/Python 3.11:
  GCC/Clang × release/ASan+UBSan. Every job runs the full suite against
  `tmp/ci/space`, requires no root `space`, and checks source cleanliness.
  The same four configurations passed locally from clean source copies
  with GCC 12.3 and Clang 15.0.7. Additional checks prove flag-change rebuilds,
  no rebuild with identical flags, and unchanged prebuilt execution with
  spaces in its path. All 935 process probes still run: ASan uses return-NULL
  allocation mode instead of incompatible RLIMIT_AS. Local LeakSanitizer
  remains disabled under ptrace; CI enables it. The workflow is configured
  here; its first remote run requires pushing this revision. Reproduction
  and supported dependencies: [build guide](build.md).

### 0.5 Release contents and installation — completed 2026-10-18

- [x] **Coder + writer:** define the source distribution and installation
  of the binary and public specification; include every required generated
  or generator input file and state build-time dependencies.
- [x] Assign a release version, write release notes and verify build/tests
  from a clean source archive. Check that the public tree contains all
  required files and excludes local artifacts. Retain the existing MIT
  license and relevant notices.
- **Acceptance:** users can build, test and install the release without
  development-session files or neighboring repositories; version and
  compatibility are identifiable from the delivered release materials.

- **Result:** source release 0.1.0, public contract revision 3, VERSION and
  CHANGELOG identify the delivered behavior and compatibility. `make dist`
  uses an explicit sorted manifest, deterministic tar/gzip metadata, internal
  SHA256SUMS and an archive checksum receipt. The archive includes required
  generated protocol/header inputs and all standalone test fixtures; no Git
  metadata, build products, session state or neighboring project is needed.
  `make install` supports prefix/bindir/docdir and DESTDIR, installs one
  executable plus release/specification/license documentation, and leaves
  fixture Python modules uninstalled. `make check-dist` passed clean-archive
  build/full tests, regenerated-header comparison, staged installation,
  installed-binary execution and byte-identical repacking after checks.
  CI has a separate source-release job. [Release guide](releases.md).

### 0.6 Repository responsibility and release measurements — completed 2026-10-18

- [x] **Maintainer + consumer owners:** keep the emulator, specification,
  build, core tests and minimal examples here. Agree ownership/locations
  for application generators, segmented runners and product integrations;
  preserve useful independent fixtures when moving implementation tools.
  Document the handoff rather than deleting consumer dependencies blindly.
- [x] Retain reproducible core benchmark recipes and a baseline. The existing
  base/IO integration measurements are supplementary; ongoing performance
  optimisation and completion of consumer migrations do not block release.
- **Acceptance:** the supported emulator interface and its release checks
  stand alone; roadmap tasks for external products are assigned externally.

- **Result:** [repository scope](ownership.md) assigns the emulator kernel,
  specification, independent tests and core benchmarks here; application
  generators, segmented product runners and guest migration belong to
  consumer repositories. Local boot/trace/snapshot/resume modules remain
  private test infrastructure rather than an installed Python API, preserving
  independent fixtures and avoiding a blind dependency deletion. The former
  copy-space-specific benchmark/verifier and its unused profiling module
  have been removed; the main benchmark imports no consumer generator.
  Existing consumer handoff instructions remain actionable without claiming
  external owner approval or completed migration. No external tree changed.
  `make benchmark` now provides 13 standalone core cases with raw repeats,
  boot subtraction, compiler/flags and source/binary hashes. The five-repeat
  100000-tick release baseline is saved in
  [core-0.1.0.json](measurements/core-0.1.0.json), with recipe and limits in
  [core benchmarks](core-benchmarks.md). Raw wait4 RSS is explicitly not an
  emulator-only memory claim; superseded external results remain in Git history.

Critical 0.0 and 0.0a and preparation steps 0.1–0.6 are closed locally.
The 0.1.0 source package is ready for publication; no remote tag/release or
upload has been performed. Updated CI must run when this revision is pushed. Earlier integration evidence using shared sources is withdrawn; current
interval conformance evidence is the revalidation recorded under 0.0;
channel timing conformance is the revalidation recorded under 0.0a. No new emulator
features are required merely to reproduce the old host runner's options:
compatibility behavior belongs in its copycode and launcher.


## Working-tree cleanup

- [x] Remove obsolete external benchmark runners, DATA scatter specification,
  unused profiler/encoder and superseded plans/measurements; preserve them
  in Git history rather than shipping them.
- [x] Retain independent kernel and local boot/IO/trace/snapshot fixtures.
- [x] Clean project scratch, archives, objects and caches with `make clean`,
  protect sources and NOP fixtures, and test cleanup/rebuild/archive checks.
