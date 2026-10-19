# Consumer handoff: strict source/destination intervals

Contract revision 2 corrects a critical mistake: every active ordinary-copy
source and destination interval in a tick must be pairwise disjoint.
Read-only fan-out is forbidden. Programs must schedule repeated uses on
separate ticks or prepare distinct copies beforehand. See the
[public contract](emulator-contract.md#4-ticks-dependencies-and-stopping).

No external project was modified by this correction. Its generator and
product migration remain its owner's work. Existing compatibility claims
and base/IO benchmark speed ratios are withdrawn until revalidated.

## Concrete static findings in copy-space

A read-only audit generated base/IO schedules for a minimal ebreak image
with 8 MiB layout, 256 slots and 64 KiB guest memory. It checked the initial
790/1078 static layers with the independent validator. Examples in both:

| Block / layer home, bits | Conflicting sources |
|---|---|
| guard_1 / 557824 | Slots 0 and 1 both read `[196736,196737)` |
| guard_2 / 833792 | Slots 1 and 3 both read `[132096,132097)` |
| guard_2 / 873216 | Slots 1 and 3 both read `[196928,196929)` |

[Audit receipt](measurements/consumer-interval-audit.json) records the
external generator hash and examples. This is a static audit, not a completed
execution proof. Its `src=0` control-transfer findings can be unresolved
patch placeholders and must be resolved/checked at execution, not treated
as proof that that unpatched control actually runs. Likewise later dynamic
operands need validation after patching. The shared-source examples above
are concrete generator sites to inspect and rewrite.

## Consumer tasks

1. Replace write-only/order-independence schedule checks with validation of
   **all** memory source/destination pairs, including partial source overlap.
   Include control copies and effective device/SYS memory buffer widths.
2. Repair LUT/gate/monitor fan-out by scheduling or distinct storage; ensure
   dynamic operand patching and branches preserve the same invariant.
3. Rebuild manifests against the corrected machine identity and boot-v2
   tooling. Old snapshots/layout identities must not be silently relabeled.
4. Use `TerminalFragment.report_ticks` for reporter cost; serialized output
   can execute a static layer twice. The corrected PCS2 wrapper costs 20
   ticks per logical layer, with body offset 11 (zero-based).
5. Independently validate **executed** operands, including boot, monitoring,
   report, resume and fork. Channels traces omit ordinary operands and alone
   cannot establish this proof. Then repeat state/IO oracle comparisons and
   benchmarks; only those corrected runs can restore compatibility claims.

The emulator continues to trust valid programs. The C loop's ability to
produce some result for an invalid shared-source schedule is not a capability
of the positional machine and must not be used to justify a generator.

## Channel tick boundary (contract revision 3)

Rebuild all boundary identities and schedules. Channel completion is only
guaranteed at tick end. To observe a data operation, use tick T for the
transfer, T+1 for its FSTAT request, T+2 for the SYS answer read, and T+3
for using the answer in memory. A concurrent SYS request and read returns
the old committed response. FSTAT/SEEK/CLOSE cannot share a tick with a
transfer on their target. CLOSE SYS still permits the closing tick's old
answer read; it disables subsequent accesses. EXEC side effects must remain
independent. PCS2 now costs 20 ticks per wrapped original layer, with body
offset 11 unchanged. Old channel-phase and timing measurements are withdrawn;
consumer repairs and live validation belong to their owning projects.
