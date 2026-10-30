# emulator — four-index positional space emulator

emulator executes simultaneous copies between bit half-intervals. Its processor is
part of the same bit space and can replace its own instructions. The
[public contract](doc/emulator-contract.md) defines encoding, tick boundaries,
channels and valid-program obligations.

Each four-index record is a **pseudo-instruction** describing a channel for
bit-signal transfer between memory intervals. Stream/SYS device channels have
their own protocol.

Input: a boot image on stdin (the first processor). Output: stdout/stderr and the
requested channels.

```
[dst_low, dst_high, src_low, src_high]
```

Build and run on Linux with a C11 compiler, GNU make and Python 3 for protocol
header regeneration:

```sh
make
./emulator -s 65520 -p 128 -t 0 < boot.bin
```

`-s` sets the number of bit positions, `-p` the processor instruction slots,
`-t` the maximum complete ticks (zero means unlimited). Defaults are 65520,
128 and zero. The instruction has four A-bit fields, A=bit_length(S). All
instructions are fetched before any copy; writes affect the following tick.
Every source/destination memory interval of a tick must be disjoint, including
source/source. Production trusts valid programs.

stdin/stdout/stderr and optional inherited fd 3/4 are pre-bound channels. SYS
provides operation results, EOF and control requests. All operations complete
by tick end; a concurrent SYS request/read returns the old response. A channel
operand is `[C,C]` outside memory; the other pair specifies its memory buffer.
The first processor is loaded by an ordinary stdin seed. There is no host
image parser, diagnostic build, trace or dump/restore interface.

A self-contained finite example prints `A` and stops:

```sh
python3 examples/write-byte.py --write A > /tmp/emulator-a.boot
./emulator < /tmp/emulator-a.boot
```

Runtime sizes and slot counts are limited only by representation and available
memory; 64/256 MiB image budgets are tested. Besides SYS there is the long copy LONG
(remote spaces: `-r path` gives host files as spaces 2, 3, ...; see `src/proto.def`).

**Security.** The SYS request EXEC runs a host command through `system()`. Run
images from others only in a container or VM.

Verification (Python 3.11+ standard library and POSIX shell for full checks):

```sh
make -C emulator check         # whole-memory oracle (709 cases), SYS, CLI
make -C emulator checked       # the mode of checking disjointness (audit after each tick)
```
