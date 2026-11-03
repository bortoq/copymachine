"""The long copy and the clock (15.2, 18.24): the action LONG of the definition of the word "space" (emulator/src,
proto.def) and the words long! long@ ( pos lo hi -- ) of the language.

The address space of the host has no numbers of spaces: pos = area * 2^28 + the bit position in the area
(HOST_AREA_BITS of proto.def). Area 0 is the clock, areas 1.. the -r paths in order (files, devices).
The programs are compiled by the definition on the host pForth and run on the emulator built from the
definition (language/build/space/emulator; `make space`). A buffer of a program is a half-interval
of positions of the space (here at 2^30 + 2^27); spacec! and spacec@ write and read its bytes (a byte of
the space is numeric there: bit k of the value at position lo + k).

1. A file of the host (-r path, the area 1): long! writes 23 bytes at the bit position 13, long@
   reads the whole file back; the file on the disk is the old one with these bits replaced, the bytes read
   are the bytes of the file. Bits past the end of the file are read as zeros.
2. The clock (the area 0): two reads of 64 bits, the second after work; the values do not decrease
   and lie between the monotonic time of the host before and after the run (nanoseconds).
3. Devices: a read of /dev/zero gives zeros (over a buffer of ones); a write to /dev/null and a read of it
   (zeros) end with the exit code 0.
4. No errors: a write to the clock, to an area that no path gives, past the end of an area, or to a path
   that cannot be opened is lost (the files stay), and a read there gives zeros; the exit code is 0 and
   nothing is written to stderr.
5. The same checks 1-4 run twice: for the program compiled on the host (the whole space) and for the program that L0
   compiles and runs in its own space (the program of the kernel, 18.24 step 2: the request is a block of the data with
   the header copied from a template of the code, language/doc/isolation.md).
6. The words of the long copy are in a program only when its source names them: the stream of another
   program equals the stream of the model; the definition of the language has none of them. Their price
   is FC-FORBID (the price of the division by 0).
"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_programs
import host
import paths
import word_cost

SPACE_EMULATOR = paths.OUT / 'space/emulator'
S = paths.SIZE
A = S.bit_length()
REQ = 8 + A + 16 + 32 + 64                 # the request record of SYS (proto.def)
RSP_FIELDS = (('op', 8), ('status', 8), ('flags', 16), ('size', 64), ('moved', A), ('eof', 1))
RSP = sum(w for _, w in RSP_FIELDS)
BUF, BUF2 = (1 << 30) + (1 << 27), (1 << 30) + (1 << 27) + (1 << 20)

PRINT = ': d. ( u -- ) dup 10 < if 48 + emit exit then dup 10 / recurse 10 mod 48 + emit ;\n'


def rev(b):
    return int(f'{b:08b}'[::-1], 2)


def get_bit(data, p, numeric):
    """Bit p of bytes: numeric (bit k of byte i at 8i + k, as the output of emit of spacec@) or stream
    (position 0 is the high bit of byte 0, as a file and a raw image)."""
    return data[p // 8] >> (p % 8 if numeric else 7 - p % 8) & 1


def field(data, at, n, numeric):
    return sum(get_bit(data, at + k, numeric) << k for k in range(n))


def answer(data, numeric):
    out, at = {}, 0
    for name, w in RSP_FIELDS:
        out[name] = field(data, at, w, numeric)
        at += w
    return out


KERNEL = False                                   # the program is given to L0 (the program of the kernel)


def compile_language(source):
    if KERNEL:
        return paths.L0.read_bytes() + source.encode('latin-1') + b'\0'
    return check_programs.compile_on_host(host.build(), paths.source_bytes(paths.LIBRARY_FILES), source)


def run(stream, *options, stdin=b''):
    result = subprocess.run([str(SPACE_EMULATOR), '-s', str(S), '-p', '8', *options], input=stream + stdin,
                            capture_output=True, timeout=600, check=False)
    assert result.returncode == 0 and not result.stderr, (result.returncode, result.stderr[-300:])
    return result.stdout


def store_bytes(at, values):
    return '\n'.join(f'{v} {at + 8 * i} spacec!' for i, v in enumerate(values)) + '\n'


def emit_bytes(at, n):
    return f'{n} 0 do {at} i 8 * + spacec@ emit loop'


def check_file(folder):
    old = bytes((i * 91 + 7) % 256 for i in range(40))
    path = folder / 'remote.bin'
    path.write_bytes(old)
    data = [(i * 37 + 5) % 256 for i in range(23)]
    pos, back = 13, len(old) + 2                  # read 2 bytes past the end: zeros
    source = (f': main {store_bytes(BUF, data)} {AREA + pos} {BUF} {BUF + 8 * len(data)} long!\n'
              f'  {AREA} {BUF2} {BUF2 + 8 * back} long@ {emit_bytes(BUF2, back)} ;\n')
    got = run(compile_language(source), '-r', str(path))
    bits = [get_bit(old, p, False) for p in range(8 * len(old))]
    for i, v in enumerate(data):
        for k in range(8):
            bits[pos + 8 * i + k] = v >> k & 1
    want = bytes(sum(bits[8 * j + m] << (7 - m) for m in range(8)) for j in range(len(old)))
    assert path.read_bytes() == want, (path.read_bytes().hex(), want.hex())
    assert got == bytes(rev(b) for b in want) + b'\0\0', (got.hex(), want.hex())
    print(f'PASS file (area 1): long! of {len(data)} bytes at bit {pos} changed exactly these bits of '
          f'the file; long@ read back the {len(want)} bytes of the file (and zeros past its end)')


def check_big(folder):
    """More than the 65536 bits a request of a program of the kernel carries: long! sends them in pieces."""
    path = folder / 'big.bin'
    path.write_bytes(bytes(30000))
    n = 25003
    source = (f': main {n} 0 do i 251 * 7 + 255 and {BUF} i 8 * + spacec! loop\n'
              f'  {AREA + 5} {BUF} {BUF + 8 * n} long! {AREA} {BUF2} {BUF2 + 8 * (n + 1)} long@ {emit_bytes(BUF2, n + 1)} ;\n')
    got = run(compile_language(source), '-r', str(path))
    want = bytearray(30000)
    bits = ''.join(f'{(i * 251 + 7) % 256:08b}'[::-1] for i in range(n))
    stream = ''.join(f'{b:08b}' for b in want)
    stream = stream[:5] + bits + stream[5 + len(bits):]
    want = bytes(int(stream[8 * j:8 * j + 8], 2) for j in range(len(stream) // 8))
    assert path.read_bytes() == want, 'the file differs'
    assert got == bytes(rev(b) for b in want[:n + 1]), got[:32].hex()
    print(f'PASS big: long! of {8 * n} bits (in pieces of at most 65536 in the kernel) and long@ of {8 * (n + 1)} bits')


def check_clock():
    source = PRINT + (f': main 0 {BUF} {BUF + 64} long@ 0 200 0 do i + loop drop 0 {BUF2} {BUF2 + 64} long@\n'
                      f'  {emit_bytes(BUF, 8)} {emit_bytes(BUF2, 8)} ;\n')
    stream = compile_language(source)
    before = time.monotonic_ns()
    got = run(stream)
    after = time.monotonic_ns()
    first, second = int.from_bytes(got[:8], 'little'), int.from_bytes(got[8:16], 'little')
    assert len(got) == 16 and before <= first <= second <= after, (before, first, second, after)
    print(f'PASS clock (area 0): {first} <= {second} ns (monotonic time of the host, '
          f'{second - first} ns apart; the run took {after - before} ns)')


FORBID = 16777216                                # fc-forbid, the price of the division by 0
AREA = 1 << 28                                   # HOST_AREA_BITS = 28 (proto.def)


def check_devices(folder):
    ones = [255] * 16
    source = (f': main {store_bytes(BUF, ones)} {AREA} {BUF} {BUF + 128} long@ {emit_bytes(BUF, 16)}\n'
              f'  {store_bytes(BUF2, ones)} {AREA * 2} {BUF2} {BUF2 + 128} long! {AREA * 2} {BUF2} {BUF2 + 128} long@\n'
              f'  {emit_bytes(BUF2, 16)} ;\n')
    got = run(compile_language(source), '-r', '/dev/zero', '-r', '/dev/null')
    assert got == bytes(32), got.hex()
    print('PASS devices: /dev/zero (area 1) read as zeros over a buffer of ones; /dev/null (area 2) written and read: zeros, exit 0')


def check_no_errors(folder):
    path = folder / 'keep.bin'
    old = bytes((i * 53 + 1) % 256 for i in range(24))
    path.write_bytes(old)
    data = [(i * 29 + 3) % 256 for i in range(8)]
    write = lambda pos: f'{pos} {BUF} {BUF + 64} long!'
    read = lambda pos, n: f'{pos} {BUF2} {BUF2 + 8 * n} long@ {emit_bytes(BUF2, n)}'
    ones = store_bytes(BUF2, [255] * 8)
    source = (f': main {store_bytes(BUF, data)}\n'
              f'  {write(0)} {write(AREA * 5)} {write(AREA * 2)} {write(AREA * 3)} {write(AREA * 3 - 24)}\n'
              f'  {ones} {read(AREA * 5, 8)}\n'                    # an area no path gives
              f'  {ones} {read(AREA * 2, 8)}\n'                    # an area of an unopenable path
              f'  {ones} {read(AREA * 3 - 24, 8)}\n'               # across the end of an area without a path
              f'  {ones} {read(AREA + 8 * 20, 8)} ;\n')           # across the end of the file: 4 bytes of it, 4 zeros
    got = run(compile_language(source), '-r', str(path), '-r', str(folder / 'missing/none'))
    assert path.read_bytes() == old, path.read_bytes().hex()
    assert got == bytes(8) * 3 + bytes(rev(b) for b in old[20:24]) + bytes(4), got.hex()
    print('PASS no errors: writes to the clock, to an area without a path, to an unopenable path and across the end of '
          'such an area are lost (the file stays), reads there are zeros; exit 0, stderr empty')


def check_only_when_named():
    sys.path[:0] = [str(paths.REFERENCE)]
    import model
    source = PRINT + ': main 65 emit 10 emit ;'
    assert compile_language(source) == model.compile_forth(source)
    _, records, _ = word_cost.compile_with_records(f': main 0 {BUF} {BUF + 64} long@ ;')
    assert {'%lr', '%lst', '%lld', 'long!', 'long@'} <= set(records), list(records)[:12]
    for name in ('long!', 'long@'):
        record = records[name]
        assert (record['bits'], record['copies'], record['layers'], record['known']) == (FORBID, FORBID, FORBID, -1), record
    _, records, _ = word_cost.definition()
    assert not [name for name in records if name.startswith('%l') or name.startswith('long')], 'in the definition'
    print('PASS the words of the long copy are compiled only into a program that names them (the stream of '
          'another equals the model; the definition of the language has none)')


def main():
    global KERNEL
    subprocess.run(['make', '-s', '-C', str(paths.ROOT), 'space'], check=True)
    for KERNEL in (False, True):
        print('--', 'the program of the kernel (L0 compiles it)' if KERNEL else 'the program compiled on the host')
        with tempfile.TemporaryDirectory(dir=paths.BUILD) as name:
            folder = Path(name)
            check_file(folder)
            check_big(folder)
            check_clock()
            check_devices(folder)
            check_no_errors(folder)
    KERNEL = False
    check_only_when_named()
    print('ALL long copy: file, clock, devices and no errors in the address space of the host on', SPACE_EMULATOR,
          'for the program of the host and the program of the kernel')


if __name__ == '__main__':
    main()
