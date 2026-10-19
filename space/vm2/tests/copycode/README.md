# Copycode tests

Tests for the **in-space driver** (the code that runs inside the space)
are kept separate from the emulator tests in `tests/`.

- Emulator tests (`tests/*.sh`, `tests/test_sys.c`) exercise the host side:
  the space engine, bit copy, configuration, the `SYS` protocol and the
  channel data path.
- Copycode tests (here) exercise programs built for the space: the boot
  loader, the `SYS` request/answer builder, finite tracing and checkpoint
  fixtures. External compatibility generators are not part of the kernel
  contract.

## Run

`sys_driver.sh` is run by `make check`: `tools/sys_gen.py` builds an
in-space program that issues an `FSTAT` request through `SYS`, reads the
answer back through `SYS`, and writes it to the `stdout` channel
([the SYS contract](../../doc/emulator-contract.md#6-sys-records)).
`tests/test_boundary.py` also runs under `make check`: full stdin image
installation, input framing, full/channel-only copycode trace, terminal
dump and checkpoint restore.

`tools/boundary.py` generates the stream loader and cooperative diagnostic
modules. `tools/sys_gen.py` and `tools/driver_gen.py` generate the other
copy programs. The all-NOP fixture in `tests/stub/` tests only the seed; it
is not the full-image loader. See [the boundary guide](../../doc/boundary.md).
