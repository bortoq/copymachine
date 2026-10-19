# emulator — four-index positional space emulator

В монорепозитории бинарники и результаты проверок находятся в
`../build/emulator/`; Makefile выбирает пути автоматически. Каталога legacy/
для сборки, установки, обычных проверок и выпуска не требуется. Локальные
build/dist в примерах относятся к самостоятельному исходному выпуску.


emulator executes simultaneous copies between bit half-intervals. Its processor is
part of the same bit space and can replace its own instructions. The
[public contract](doc/emulator-contract.md) defines encoding, tick boundaries,
channels and valid-program obligations.

Each four-index record is a **pseudo-instruction** describing a channel for
bit-signal transfer between memory intervals. Logical **copycode** uses triples
`[n,dst,src]`; [vm2c](../space/vm2/doc/direct.md) compiles these to stored emulator
pseudo-instructions. Stream/SYS device channels have their own protocol.

```
[dst_low, dst_high, src_low, src_high]
```

Build and run on Linux with a C11 compiler, GNU make and Python 3 for protocol
header regeneration:

```sh
make                          # fast bitcopy, the default
make BACKEND=network           # verified two-phase addressing mechanism
make                          # selects bitcopy again, without clean
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

Bitcopy supports runtime sizes/slot counts up to representation and available
memory; 64/256 MiB image budgets are tested. Network supports S divisible by 16,
up to 65520, and P<=128, subject to processor fit. It constructs the network
internally: no sorter file is needed. Both executables use the same new ABI on
common configurations. BACKEND is chosen at compilation; there is no runtime
backend switch or automatic fallback. Old LDR1/native-word and vm2 three-field
images require rebuilding, not merely renaming their executable.

Verification (Python 3.11+ standard library and POSIX shell for full checks):

```sh
make check CFLAGS='-Wall -Wextra -Werror -pedantic -std=c11 -O2'
make check-runtime             # both production variants, whole-memory and CLI
make check-mechanism           # separate historical mechanism controls
make benchmark                 # optional CPU/process/RSS comparison; GNU time
make clean                     # removes both builds and generated test/network files
```

See [runtime verification and measurements](doc/runtime.md),
[mechanism proof](doc/README.md), [hardware limits](doc/hardware.md),
[project roadmap](doc/roadmap.md) and the workspace roadmap at `../ROADMAP.md`.
Исторические проверки механизма выполняются отдельно: они строят текстовые
сети сортировки и не входят в ограниченную обычную проверку.

The former mechanism's native-word process interface and loader survive only
as historical test controls; ordinary `make` builds the new common runtime.
Application software and the vm2 guest implementation belong to other projects.

License: [MIT](LICENSE).

Исходный выпуск собирается `make dist`; `make distcheck` распаковывает его
в новый каталог с пробелами в имени, сверяет SHA256, выполняет полный набор
проверок, установку обоих вариантов и запуск установленного бинарника.
`make install prefix=/usr/local` устанавливает `bin/emulator` и документацию;
`DESTDIR=/путь` задаёт корень промежуточной установки. Выбранный `BACKEND`
сохраняется при установке. `make clean` удаляет также `dist/`.
Архив воспроизводим при одинаковом `SOURCE_DATE_EPOCH` (по умолчанию 0).
