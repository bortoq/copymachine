#!/usr/bin/env python3
"""Real subprocess tests of the emulator contract."""
import subprocess
import tempfile
from pathlib import Path

from runtime_codec import copy, layer, program, put_field, validate

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from output_paths import output_dir

BINS = [output_dir(ROOT, 'build')/'bitcopy'/'emulator']
S, P = 65520, 8
A = S.bit_length()
RSP_BITS = 97+A
REQ_BITS = 120+A
checks = 0

def run(binary, packet, *, size=S, slots=P, ticks=0, expected=b''):
    global checks
    result = subprocess.run([str(binary), '-s', str(size), '-p', str(slots), '-t', str(ticks)],
                            input=packet, capture_output=True, timeout=60, check=True)
    assert result.stdout == expected, (binary, result.stdout.hex(), expected.hex())
    assert not result.stderr, result.stderr
    checks += 1
    return result

def record(values, widths):
    data = bytearray((sum(widths)+7)//8)
    at = 0
    for v, width in zip(values, widths, strict=False):
        put_field(data, at, width, v)
        at += width
    return bytes(data)

for binary in BINS:
    run(binary, layer([], S, P))
    # Output is committed on the final tick; no old pending-result pipeline.
    packet, clocks = program([[copy(8, S+2, 24000, S)]], data=[(24000, b'A')])
    run(binary, packet, ticks=clocks+1, expected=b'A')
    run(binary, packet, expected=b'A')
    run(binary, packet, ticks=clocks, expected=b'')
    # Input is used only by the following layer; then the machine becomes idle.
    packet, clocks = program([[copy(32, 24000, S+1, S)],
                               [copy(32, S+2, 24000, S)]])
    run(binary, packet+b'abcd', expected=b'abcd')
    run(binary, packet+b'abcd', ticks=clocks+1, expected=b'')
    # Same-tick request/read returns the OLD SYS response.
    req = record([3, S+2, 0, 0, 0], [8, A, 16, 32, 64])
    old = bytes((RSP_BITS+7)//8)
    new = record([3, 0, 0, 0, 0, 0], [8, 8, 16, 64, A, 1])
    rows = [[copy(REQ_BITS, S, 24000, S), copy(RSP_BITS, 25000, S, S)],
            [copy(RSP_BITS, 26000, S, S)],
            [copy(len(old)*8, S+2, 25000, S)],
            [copy(len(new)*8, S+2, 26000, S)]]
    packet, _ = program(rows, data=[(24000, req)])
    run(binary, packet, expected=old+new)
    # Short read + EOF -> later FSTAT -> later response -> output.
    req = record([3, S+1, 0, 0, 0], [8, A, 16, 32, 64])
    rows = [[copy(32, 27000, S+1, S)], [copy(REQ_BITS, S, 24000, S)],
            [copy(RSP_BITS, 25000, S, S)], [copy(len(old)*8, S+2, 25000, S)],
            [copy(32, S+2, 27000, S)]]
    packet, _ = program(rows, data=[(24000, req)])
    response = record([3, 0, 0, 0, 2, 1], [8, 8, 16, 64, A, 1])
    run(binary, packet+b'xy', expected=response+b'xy\0\0')
    # CLOSE SYS preserves the closing tick's old read, then disables reads.
    req = record([1, S, 0, 0, 0], [8, A, 16, 32, 64])
    rows = [[copy(REQ_BITS, S, 24000, S), copy(RSP_BITS, 25000, S, S)],
            [copy(RSP_BITS, 26000, S, S)],
            [copy(len(old)*8, S+2, 25000, S)],
            [copy(len(old)*8, S+2, 26000, S)]]
    canary = b'Z'*len(old)
    packet, _ = program(rows, data=[(24000, req), (26000, canary)])
    run(binary, packet, expected=old+canary)
    # Real inherited status/snapshot descriptors and stderr stay independent.
    rows = [[copy(8, S+3, 24000, S), copy(8, S+4, 25000, S), copy(8, S+5, 26000, S)]]
    packet, _ = program(rows, data=[(24000, b'D'), (25000, b'S'), (26000, b'P')])
    with tempfile.TemporaryDirectory(prefix='emulator-fds-') as directory:
        status, snapshot = Path(directory)/'status', Path(directory)/'snapshot'
        result = subprocess.run(['/bin/sh', '-c', 'exec "$1" -s 65520 -p 8 3>"$2" 4>"$3"',
                                 'emulator-test', str(binary), str(status), str(snapshot)],
                                input=packet, capture_output=True, check=True, timeout=60)
        assert result.stdout == b'' and result.stderr == b'D'
        assert status.read_bytes() == b'S' and snapshot.read_bytes() == b'P'
        checks += 1
    # Smaller runtime dimensions use a narrower instruction codec.
    small = 1040
    rows = [copy(8, small+2, 800, small)]
    packet, clocks = program([rows], size=small, slots=8, data=[(800, b'Z')])
    run(binary, packet, size=small, slots=8, expected=b'Z')
    # Smallest byte-rounded seed works with a partial-byte processor width.
    run(binary, layer([], 32, 1), size=32, slots=1)
    for args in [('-s','0'), ('-p','0'), ('-t','-1'), ('-s','65535'),
                 ('--backend','bitcopy'), ('--core','x'), ('sorter.txt',),
                 ('-s','18446744073709551616'), ('-s','2'), ('-p','999999')]:
        result = subprocess.run([str(binary), *args], capture_output=True, check=False)
        assert result.returncode == 2, (binary, args, result.returncode)
        checks += 1
# bitcopy-only sizes: wider addresses and more than 128 slots.
for size, slots in [((1<<29)-16, 256), ((1<<31)-16, 256), (65520, 256), (65519, 8)]:
    run(BINS[0], layer([], size, slots), size=size, slots=slots)
# The independent fixture checker rejects shared sources and accepts adjacency.
try:
    validate([copy(1, 8, 0, 32), copy(1, 16, 0, 32)], 32)
except ValueError:
    pass
else:
    raise AssertionError('shared source accepted')
validate([copy(1, 1, 0, 32), copy(1, 3, 2, 32)], 32)
print(f'emulator real CLI: {checks} checks passed (boot, IO, SYS, dimensions, errors)')
