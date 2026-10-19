# vm1 public emulator contract, revision 1

2026-10-19. This contract describes the new common four-index runtime. It
supersedes the old native-word/LDR1 process interface. Old images and vm2's
three-field images are not binary compatible. There is no runtime negotiation
or automatic old-format detection. The target contract/size belongs in the
producer's build manifest.

## Process interface and compilation

```
make                         # BACKEND=bitcopy
make BACKEND=network          # two-phase addressing, same instruction contract
./vm1 [-s bits] [-p instructions] [-t ticks] < boot-and-input > output
```

Defaults: S=65520 bit positions, P=128 instructions, no tick limit (`-t 0`).
Flags take unsigned decimal integers; attached values such as `-s65520` work.
A nonzero limit counts complete logical ticks, including seed and installer
work. The final tick commits fully before exit. An all-NOP processor stops.
Both conditions return 0. Invalid arguments/configurations return 2; allocation
failure returns 1. IO/device failures are returned through SYS, not process
exit. A tick limit cannot interrupt blocking IO or EXEC.

The supported baseline is Linux with 8-bit bytes, 64-bit size_t/long, C11 and
POSIX streams/descriptors. Build dependencies: C compiler, GNU make and Python 3 for protocol regeneration. Tests
also need Python 3.11+ (standard library) and a POSIX shell; optional measurements
need GNU time. No sibling repository, external sorter file, diagnostic build,
host image parser, trace or dump/restore option is required.

BACKEND is a build-time choice. Object/executable/configuration paths are separate
under `build/bitcopy` and `build/network`. Every `make` refreshes the public vm1
from the selected variant, even when switching back to a previously built one.
CC/CPPFLAGS/CFLAGS/LDFLAGS/LDLIBS changes invalidate the corresponding build.
Bitcopy does not compile or allocate the network mechanism. Network never falls
back to bitcopy. It constructs its sorting fabric internally during startup.

## Encoding, dimensions and initial state

Terminology: copycode is the logical triple `[n,dst,src]`. A vm1 four-index
record is a **pseudo-instruction**, describing a signal-transfer channel
between half-open memory intervals. This information-flow meaning is separate
from the stdin/stdout/SYS device channels. Existing instruction names in the
CLI and C API refer to pseudo-instructions. Direct vm2 compilation uses a new
target ABI; vm1 does not decode logical triples or monitor their updates.

A = bit_length(S). One pseudo-instruction is **4A bits**, in order:

```
[dst_low, dst_high, src_low, src_high]
```

Each field has A bits, least significant numeric bit first. Space position zero
is the most significant bit (0x80) of byte zero; position seven is its least
significant bit. Stream bytes keep that bit order. Encoding never depends on
native integer byte order. The processor occupies `[0,P*4A)` in ordinary memory.
It is fetched in full at tick start; replacing its bits changes the next tick.

P>=1; the processor must fit inside S and its byte-rounded seed transfer must
fit. S and reserved channel codes S..S+5 must fit in A bits. Widths up to 64 are
supported by the software representation, subject to size_t and available RAM.
There is no separate 128-slot/16-bit limit in bitcopy. Tests cover 64/256 MiB image
budgets and >128 slots. Network supports S divisible by 16, 16<=S<=65520 and
P<=128, also subject to processor/seed fit. Invalid network dimensions exit 2.
Small supported networks use the same four-A-bit wire format, even though the
verified mechanism's internal keys remain 16-bit. Larger hardware is a separate
implementation/proof task.

Initially all memory is zero except slot zero, seeded as:

```
[0, ceil(P*4A/8)*8, S+1, S+1]
```

This is an ordinary stdin-channel copy. Supply that many bytes containing the
first processor layer, with zero padding if it ends inside a byte. No LDR1 or
host header is consumed. A larger image is installed by supplied copycode;
installation consumes ordinary ticks and input bytes. The emulator does not
interpret image, trace, status or checkpoint formats. A short initial seed read
can leave parts of the seed; a conforming bootstrap supplies its full packet
and manages later EOF/errors through the channel protocol.

## Memory operations, channels and NOP

An ordinary operation copies `[src_low,src_high)` to `[dst_low,dst_high)`.
Both lengths are positive and equal; all endpoints are within `[0,S]`.
An ordinary empty source denotes NOP and its destination fields are ignored.
Canonical NOP is `[0,0,0,0]`.

A channel operand is a degenerate pair `[C,C]`, C>=S. It is classified before
ordinary empty-source NOP. Its other operand is one positive memory buffer:

```
input:  [buf_low,buf_high,C,C]
output: [C,C,buf_low,buf_high]
```

The buffer defines the transfer length. An empty buffer requests nothing.
Channel-to-channel copies and malformed unequal/descending memory intervals
are outside the valid-program contract. Reserved channels are:

| Code | Binding |
|---|---|
| S | SYS control/answer |
| S+1 | stdin fd 0, read |
| S+2 | stdout fd 1, write |
| S+3 | stderr fd 2, write |
| S+4 | optional inherited fd 3, write (status convention) |
| S+5 | optional inherited fd 4, write (snapshot convention) |

Optional codes remain reserved when descriptors are absent. Optional inherited
streams are duplicated above the reserved descriptors; owned duplicates are
closed during shutdown. CLOSE disables a logical binding; original inherited
and standard descriptors are not closed. Access to an absent/closed data binding
is ignored; SYS requests referring to it return EBADF.

Data lengths are whole bytes. Memory buffers can begin at any bit position.
SYS reads require room for the full response; requests require the full request
record and any EXEC command. Partial data reads overwrite only transferred bytes;
remaining bits are preserved. Input/output state is available through later
FSTAT. SIGPIPE is ignored so broken-pipe errors reach the IO status.

## Tick and valid-program obligations

Every active memory source and destination interval of a tick is pairwise
disjoint, **including source/source**, within one instruction and across all
ordinary/channel instructions. Adjacent half-open boundaries are allowed.
Source fan-out is forbidden. SYS answer reads may share the external SYS code
but require disjoint destination memory buffers. All actual SYS record/EXEC
buffer extents count toward the memory invariant.

At most one transfer per data device and one SYS request per tick are supported.
FSTAT/SEEK/CLOSE and a transfer on their target require separate ticks. EXEC side
effects must be independent of other operations in the same tick. No slot order
is promised. The production emulator trusts these obligations; violating them
is not a supported machine capability or an isolation boundary.

All instructions are fetched before any execution. Ordinary copies and channel
operations finish by tick end. There is no intermediate-readiness guarantee.
A SYS answer read observes the response committed **before** this tick, even
with a concurrent request or CLOSE SYS. New responses are available to reads in
following ticks, and data loaded into memory can be used by instructions fetched
on a later tick. A typical dependent sequence is transfer T, FSTAT T+1, response
read T+2, use response T+3. CLOSE SYS preserves closing-tick old-response reads,
then disables later SYS reads/requests while leaving other devices usable.

A sequential bitcopy loop implements the same simultaneous result for valid
disjoint intervals after full fetch; a full data-memory snapshot is unnecessary.
The network mechanism commits in the current tick, including its last tick.
Its independent slot inputs and collective classification remain the target
hardware architecture; a sequential C loop is not a hardware timing claim.

## SYS records

`src/proto.def` is the schema. Numeric field bit order matches instructions.
The host request/response record contents are unchanged apart from the explicit
vm1 count width (moved uses **A**, not vm2's A-1). Request:

```
op:8 chan:A flags:16 arg:32 off:64       (120+A bits)
```

Response:

```
op:8 status:8 flags:16 size:64 moved:A eof:1   (97+A bits)
```

NONE=0, CLOSE=1, SEEK=2, FSTAT=3, IOCTL=4, EXEC=5. FSTAT returns target size
and the last data-operation status, **moved byte count**, EOF. SEEK uses arg as
whence and off as the host offset. IOCTL returns ENOTTY. EXEC synchronously runs
the shell command appended immediately after the request record, with arg its
byte length, returning exit status and raw system result. EXEC is an explicitly
requested host operation; the emulator is intended for trusted programs.
No SPAWN, dynamic open or runtime version handshake is implemented.

## Consumer boundary

vm2 must implement its own three-field memory/processor, guest tick boundary,
address mapping and SYS record/channel conversion on copycode. Static endpoint
expansion alone cannot preserve arbitrary self-modifying vm2 programs. Existing
copy-space generators also need repairs for shared sources and channel timing.
Their old images/checkpoints are not silently compatible with this runtime.
Common guest boot/monitor/checkpoint libraries will be extracted later. Minimal
independent local fixtures remain with vm1 so its tests are standalone.
