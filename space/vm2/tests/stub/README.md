# Space stub (placeholder loader)

The emulator does **not** synthesise a boot program: the run environment
supplies it. `tools/boundary.py boot` supplies the full-image installer;
this directory contains only the smallest seed fixture.

`nop.bin` is the simplest such stub: an all-NOP image for the default
configuration (`-s 65520 -p 64`). The seed copies it over the processor,
so on the next tick the processor holds only NOPs and the space stops.

```sh
./space -s 65520 -p 64 < tests/stub/nop.bin   # silent, exits 0
```

Regenerate it for other sizes (the image covers `proc_n` instructions):

```sh
python3 tools/driver_gen.py -s 65520 -p 64 --nop -o tests/stub/nop.bin
```

A valid seed stream supplies the whole processor packet, rounded to bytes.
A short stream changes only the bytes actually read; the remaining seed
bits may stay active or may form different instructions. There is no
host-level validation or promised termination for incomplete program input.
Use `-t` to limit executed ticks in experiments; it does not interrupt a
blocked read. See [the public contract](../../doc/emulator-contract.md#3-initial-state-and-stdin-seed).
For a full-image installer use `tools/boundary.py boot`, as described in
[the boundary guide](../../doc/boundary.md).
