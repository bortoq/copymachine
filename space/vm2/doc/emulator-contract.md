# Public emulator contract

Revision 4, 2026-10-19. This document specifies the `vm2`
machine and its process interface. It is the normative reference for
consumers; roadmap sketches and application protocols do not override it.
The bit/record tables are defined by the formulas below and `proto.def`.
This document revision is not an emulator release number or an on-wire
version field. Revision 3 changes SYS timing: old same-tick completion
pipelines are withdrawn. Instruction and record encodings are unchanged.

vm2 now executes as copycode on emulator ABI rev1, launched by Python 3.11+.
Revision 4 preserves the triple/SYS encoding and logical tick semantics.
The verified host is Linux x86-64/POSIX. The former native C implementation
is retained only as a migration/control executable. See [implementation](emulator-guest.md).

## 1. Process interface and configuration

```sh
vm2 [-s bits] [-p instructions] [-t ticks] < input > output
```

| Option | Unit | Default | Meaning |
|---|---|---:|---|
| `-s` | bits | 65520 | Number of memory positions S |
| `-p` | instructions | 64 | Number of processor slots P |
| `-t` | ticks | 0 | Maximum tick executions; 0 means unlimited |

Values are unsigned decimal integers. Both `-s65520` and `-s 65520` are
accepted; likewise for `-p` and `-t`. Repeated options use the last value.
Sizes must fit `size_t`; the tick limit must fit `uint64_t`. Unknown
options, positional arguments, missing values and invalid numbers fail
with exit code 2. There are no host image, trace or snapshot options.

For S > 0, define:

```
a = bit_length(S) = ceil(log2(S + 1))
z = a - 1
I = 3*a - 1                       instruction width, bits
L = P*I                           processor width, bits
D = number of XDEV entries        currently 5
```

Accepted guest configurations satisfy P >= 1, a <= 62, L <= S, L <= 2^z−1 and
S+1+D <= 2^a. The reserved positions must fit even when optional
descriptors are absent. The rounded seed buffer and the generated emulator interpreter must also fit.
Allocation must succeed; emulator needs separate code/data/guest arenas. Some small configurations cannot encode
a full SYS request/response; accepting a configuration does not guarantee
that every service or external loader fits it.

## 2. Memory, instructions and byte encoding

This document specifies the packed triple compatibility ABI, executed by the
explicit `vm2` interpreter. The primary `vm2c` path uses the separate
[direct target ABI](direct.md), with symbolic fields and stored native emulator
pseudo-instructions. It does not promise byte compatibility of executable
code or raw checkpoints. Logical copycode instructions are `[n,dst,src]`;
four emulator bounds describe a signal-transfer channel between memory intervals,
distinct from the stream/SYS device protocol.

Memory consists of S bit positions `[0,S)`. The processor occupies `[0,L)`
inside the same memory. Slot i starts at i*I and contains:

| Field | Offset within instruction, bits | Width, bits |
|---|---:|---:|
| `n` | 0 | z |
| `dst` | z | a |
| `src` | z+a | a |

`copy n,dst,src` copies `[src,src+n)` to `[dst,dst+n)` when both endpoints
are in memory. Addresses and lengths are in bits. `n=0` is NOP; its other
fields are ignored. A copy with an endpoint >=S is a channel operation,
not a memory interval extending beyond S.

In a byte stream, position k is byte `k//8`, mask `0x80 >> (k%8)`.
Within a numeric field, value bit j occupies position `field_start+j`:
numeric fields are least-significant-bit first in this position order.
For example, an eight-bit numeric field holding 1 at position 0 is the
stream byte `80` hex; an ordinary payload byte `01` hex remains byte `01`.
Instructions and records have no implicit byte alignment or padding.

## 3. Initial state and stdin seed

Memory is initially zero, except slot 0, which the emulator sets to:

```
copy L, 0, S+1
```

The other slots remain NOP. Channels are bound before the first tick;
the initial SYS response and channel state fields are zero. The first
tick executes this ordinary stdin transfer into the processor. The next
tick fetches instructions from the resulting memory.

The seed consumes ceil(L/8) input bytes. If L is not byte-aligned, the
transfer also writes the remaining bits of its last byte after `[0,L)`;
that whole rounded buffer must fit in memory. For accepted configurations
this is part of the seed's supplied storage. The seed does not install a
whole raw memory image. A loader in the stream may do so with further
ordinary copies. Application input follows whatever framing that loader
defines; the emulator does not parse a boot envelope or raw-image header.

An input shorter than requested is an ordinary short read/EOF. Only bytes
actually read overwrite memory. There is no host-level boot validation or
special exit code for an incomplete program stream.

## 4. Ticks, dependencies and stopping

Each tick first fetches all P instructions from processor memory. Only
then are their copies executed. A write into processor memory, including
a write by stdin or a SYS response, affects the next tick's instructions.
It cannot change an instruction already fetched for the current tick.

For every active ordinary copy i, let S_i=[src_i,src_i+n_i) and
D_i=[dst_i,dst_i+n_i). All source and destination intervals of the same
tick must be pairwise disjoint, including S_i versus S_j. Two instructions
cannot read even one shared source position in that tick. Half-open
intervals may touch at their boundaries. NOPs contribute no intervals.

Slot-order independence alone is insufficient. Read-only fan-out from a
common interval is not part of this machine: repeat copies on different
ticks or first prepare disjoint source storage with conforming copies.
There is no source-data snapshot or memmove guarantee.

Revision 1 erroneously permitted shared read-only sources; that statement
is withdrawn. The invariant above agrees with the underlying EMULATOR positional
mechanism. The C implementation trusts the program and need not reject
an invalid schedule; accidental results outside the contract are not
supported machine behavior.

All requested copies, including copies to/from channels, are guaranteed
complete only at the end of their tick. No program may rely on intermediate
completion or an ordering between independent copies within that tick.
A channel result written into memory can be used from the next tick.

A SYS answer read observes the response committed **before** this tick.
A request replaces the stored response at the tick boundary; its new answer
can be read on a later tick. A simultaneous request and answer read is
allowed with disjoint memory buffers, but the read receives the old answer.
All answer reads of a tick observe that same old response. Initially it is
zero. Closing SYS still permits old-response reads in the closing tick;
subsequent SYS accesses are skipped.

FSTAT, SEEK or CLOSE and a data transfer on their target channel must use
separate ticks. EXEC side effects must be independent of every concurrent
operation. An unrelated device transfer and a SYS request may share a tick.
These rules apply even when memory buffers are disjoint. The implementation's
host call order is not an additional channel readiness guarantee.

To observe a transfer's result: execute the transfer in tick T, submit FSTAT
in tick T+1 or later, read its answer in tick T+2 or later, and use the
memory answer in tick T+3 or later. A new request can share the answer-read
tick if it obeys all independence rules; that read still returns the earlier
response. Revision 2's data → SYS request → new answer pipeline was erroneous
and is withdrawn.

If a fetch finds all `n=0`, the machine stops without performing transfers
or copies. Otherwise it executes the entire tick. A positive `-t T` permits
at most T tick executions, including the seed tick, and stops between
ticks. It does not interrupt a blocked transfer or EXEC. Neither tick-limit
termination nor a host signal creates a cooperative checkpoint or report.

## 5. Device positions and inherited descriptors

| Position | Channel | Host binding | Supported direction |
|---|---|---|---|
| S | SYS | Emulator control state | Request/answer |
| S+1 | stdin | fd 0 | Read into memory |
| S+2 | stdout | fd 1 | Write from memory |
| S+3 | debug | fd 2, stderr | Write from memory |
| S+4 | status | Inherited fd 3, if available | Write from memory |
| S+5 | snapshot | Inherited fd 4, if available | Write from memory |

Device positions follow `XDEV` table order; descriptor numbers are the
table's ids, not a second addressing scheme in copycode. Names such as
status/snapshot describe their intended use: the emulator treats their
contents as arbitrary bytes. It does not know SPT, PCS or snapshot formats.

For fd >=3 the emulator duplicates an already-open descriptor above all
table descriptors, uses the duplicate and closes that duplicate at shutdown
or channel CLOSE. Missing/unbindable optional descriptors leave an unbound
reserved position. Original inherited descriptors are not owned or closed
by the channel. fd 0/1/2 use the process's standard streams directly.
The emulator does not open device paths or dynamically add channels.

A data instruction has exactly one device endpoint and one memory buffer.
Copy to a device writes; copy from a device reads. There is at most one
transfer per device per tick. Buffer positions need not be byte-aligned;
payloads are byte sequences. Programs use `n` divisible by 8. The current
implementation rounds a non-byte count up to ceil(n/8) bytes, including the
seed; it does not mask the final byte. The rounded buffer must be in memory.

Transfers are synchronous and may block. Reads try to obtain the requested
number of bytes until completion, EOF or error; pipe read-ahead by stdio
is not a logical application cursor. `moved` counts delivered bytes.
Stdout and duplicated output streams are unbuffered so a completed write
is available before a following blocking read. SIGPIPE is ignored by the
emulator; a failed pipe write is observable through SYS state.

A transfer sets `status` and `moved`; a read also resets/sets `eof`. A write
does not reset an earlier EOF flag. Successful transfers have status 0;
errors use host errno, or fallback 1 if stdio reports an error without errno.
Partial progress and an error may coexist. EOF means a read observed EOF:
a read returning exactly its requested length need not report EOF yet.

Copies involving only an unbound or closed channel position are skipped;
they do not access memory beyond S. Querying such a target with FSTAT
returns EBADF. Device-to-device, SYS-to-device and unsupported-direction
transfers are outside the valid-program contract.

## 6. SYS records

`copy REQ_BITS,S,B` submits the request at memory position B.
`copy RSP_BITS,A,S` reads the stored response into A. Use these complete
record lengths: the implementation decodes/encodes the entire record and
does not enforce a shorter instruction's advertised count. Buffers must
fit the full record. Multiple answer reads may use disjoint buffers.

Fields are adjacent numeric fields in the bit order of section 2:

| Request field | Offset, bits | Width, bits |
|---|---:|---:|
| op | 0 | 8 |
| chan | 8 | a |
| flags | 8+a | 16 |
| arg | 24+a | 32 |
| off | 56+a | 64 |

`REQ_BITS = 120+a`.

| Response field | Offset, bits | Width, bits |
|---|---:|---:|
| op | 0 | 8 |
| status | 8 | 8 |
| flags | 16 | 16 |
| size | 32 | 64 |
| moved | 96 | z |
| eof | 96+z | 1 |

`RSP_BITS = 97+z`. `chan` is the channel's position. `moved` and `size`
are byte quantities; instruction `n` is a bit quantity. Values are encoded
in the stated field width, so status is the low eight bits of host status.
Unused request fields must be zero. Response flags are currently zero.

There is at most one SYS request per tick. Each request replaces the stored
response at tick end; without a request the previous response remains readable. Data
transfers alone update their device state, not the stored SYS response.

| op | Name | Request and result |
|---:|---|---|
| 0 | NONE | Replace response with zeros (`op=0`). |
| 1 | CLOSE | Close the channel named by chan; EBADF if unbound/closed. |
| 2 | SEEK | `fseek(stream,(long)off,(int)arg)`; arg is host SEEK_SET/CUR/END. Success status 0, failure errno. |
| 3 | FSTAT | Query chan; return its size and last data-operation status/moved/eof. |
| 4 | IOCTL | Currently always ENOTTY; no ioctl is forwarded to the device. |
| 5 | EXEC | Synchronous host shell command; details below. |

Unknown opcodes return EINVAL. Except NONE, response op echoes the requested
opcode. Fields not supplied by the operation are reset to zero.

SEEK offsets are byte offsets using the host `long` representation; on the
verified host negative offsets use a 64-bit two's-complement field. Values
and origin must be valid for the host call. SEEK does not report a resulting
position or reset the device's stored moved/eof/status metadata. Pipes may
reject SEEK. FSTAT/SEEK/CLOSE and a transfer on their target require separate ticks.

Successful FSTAT refreshes size from host `st_size` and preserves the last
transfer's status/moved/eof. Failure sets errno (or EBADF for a missing
stream) and size 0. Pipe/device size is the host's value, not a byte cursor.
FSTAT observes a transfer completed in an earlier tick. Read the FSTAT
response in a tick after submitting the request.

CLOSE disables the logical channel. For fd 0/1/2 it does not `fclose` the
standard stream; for optional devices it closes the owned duplicate only.
The original inherited descriptor remains open. Errors from closing an
owned stream are not returned. Closing SYS disables further control and
answer reads from the next tick. Reads in the closing tick still receive
the previously committed response; the CLOSE SYS response itself cannot
be retrieved after closure. Already-bound data channels continue to work.
SYS cannot be reopened.

### EXEC

One request copy must cover a record and the following command bytes:

```
[B, B+REQ_BITS)             request: op=5, arg=L bytes
[B+REQ_BITS, B+REQ_BITS+8*L) command bytes in ordinary stream order
n >= REQ_BITS + 8*L
```

The implementation copies L bytes, appends NUL and calls `system()`.
The command should contain no embedded NUL. The response status is the
shell exit code, errno if `system` returns −1, or `128+signal` on abnormal
termination; size carries the raw `system` result. Too short an advertised
request returns EINVAL; command allocation failure returns ENOMEM.

EXEC uses the process's environment, working directory, permissions and
descriptor inheritance. It has no separate stream redirection or timeout.
Its side effects must be independent of other operations in the tick.
The emulator is a trusted-program mechanism, not a host isolation boundary.

## 7. Program obligations and process results

A valid program guarantees all memory buffers fit, arithmetic ranges do
not wrap, every source/destination memory interval of a tick is disjoint
from every other such interval (including source/source), and channel use obeys
sections 5–6. Bounds and overlap are not checked by the emulator. Violating
these conditions has no defined result or promised diagnostic and can
access memory outside the allocation. Such a program must not be treated
as safely rejected input.

| Process result | Meaning |
|---|---|
| Exit 0 | All-NOP stop or tick limit reached. |
| Exit 1 | Allocation failure reported by the emulator. |
| Exit 2 | Invalid command line/configuration. |
| Host signal | Host process termination under normal OS rules; no machine-level stop record. |

Device errors and EXEC exit codes are returned through SYS, not as the
emulator's process exit code. Guest exit/status protocols belong to copycode
and its launcher. Shutdown flushes stdout and closes owned channel duplicates;
flush/close failures do not change the process exit code. Host diagnostics
use stderr, which also backs the debug channel; valid application stdout is
not mixed with emulator status records.

## 8. Compatibility and ownership

Consumers agree on S, P, the packed triples and the same vm2 proto.def.
Changes to instruction/record fields, device positions or logical timing
are compatibility changes. The separate emulator ABI is translated by guest
copycode; emulator field widths do not change guest memory layout.

Channel endpoints are typed positions, not memory intervals. Concurrent
request and old-answer reads do not relax buffer disjointness. Fetch is
an earlier guest phase, not an extra copy operand in the guest layer.

The maintained product is vm2guest/compiler.py, assembler.py and cli.py.
The independent oracle is tests/vm2_reference.py. C kernel files and their
checks are retained only as explicit migration/regression controls.
Shared boot/SYS/trace/checkpoint/transport belong to copycode.vm2; tools
contain compatibility entry points. Their provisional boundary/layout
identities remain source-side checks, not runtime handshakes. Snapshot,
trace and application framing are guest software, not host services.

## 9. Nested process transport

The launcher prepends the emulator interpreter bootstrap and then forwards the
original guest stdin bytes. Pipes remain live pipes. Regular-file stdin is
spooled with the prefix into a temporary seekable file; copycode adjusts
SEEK_SET/CUR/END and FSTAT size to guest coordinates. Translated physical
positions must fit host off_t; stdin changes through external/shared
descriptors (including shell commands) are outside this transport profile. Concurrent external
mutation of that input file and shared parent file-offset observations are
not supported by this transport. VM2's -t counts virtual ticks, not emulator ticks.
No guest decoding/execution takes place in the host launcher.

Optional raw-memory snapshots are generated by guest copies on virtual
boundaries; they do not serialize external channels or private SYS state.
Normal process invocation emits no hidden reports. See [implementation](emulator-guest.md).
