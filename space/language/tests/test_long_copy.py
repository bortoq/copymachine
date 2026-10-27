"""The long copy and the clock (15.2): the action LONG of the definition of the word "space" (space/,
proto.def) and the words long! long@ ( space pos lo hi -- ) of the language.

The programs are compiled by the definition on the host pForth and run on the emulator built from the
definition (build/space/language/space/emulator; `make space`). A buffer of a program is a half-interval
of positions of the space (here at 2^30 + 2^27); spacec! and spacec@ write and read its bytes (a byte of
the space is numeric there: bit k of the value at position lo + k).

1. A file of the host (-r path, the remote space 2): long! writes 23 bytes at the bit position 13, long@
   reads the whole file back; the file on the disk is the old one with these bits replaced, the bytes read
   are the bytes of the file. Bits past the end of the file are read as zeros.
2. The clock (the remote space 1): two reads of 64 bits, the second after work; the values do not decrease
   and lie between the monotonic time of the host before and after the run (nanoseconds).
3. EXEC through the remote space 0: long! writes the old request record EXEC with its command to the
   position 0 of space 0, long@ reads the answer record from it; a stream that writes the same record to
   SYS directly (the old way) and reads the answer gives the same answer (op, status, size, moved, eof).
4. The words of the long copy are in a program only when its source names them: the stream of another
   program equals the stream of the model; the definition of the language has none of them.
"""
import os, subprocess, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_programs, host, paths, word_cost

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


def compile_language(source):
    return check_programs.compile_on_host(host.build(), paths.source_bytes(paths.LIBRARY_FILES), source)


def run(stream, *options, stdin=b''):
    result = subprocess.run([str(SPACE_EMULATOR), '-s', str(S), '-p', '8', *options], input=stream + stdin,
                            capture_output=True, timeout=600)
    assert result.returncode == 0 and not result.stderr, (result.returncode, result.stderr[-300:])
    return result.stdout


def store_bytes(at, values):
    return '\n'.join(f'{v} {at + 8 * i} {at + 8 * i + 8} spacec!' for i, v in enumerate(values)) + '\n'


def emit_bytes(at, n):
    return f'{n} 0 do {at} i 8 * + dup 8 + spacec@ emit loop'


def check_file(folder):
    old = bytes((i * 91 + 7) % 256 for i in range(40))
    path = folder / 'remote.bin'
    path.write_bytes(old)
    data = [(i * 37 + 5) % 256 for i in range(23)]
    pos, back = 13, len(old) + 2                  # read 2 bytes past the end: zeros
    source = (f': main {store_bytes(BUF, data)} 2 {pos} {BUF} {BUF + 8 * len(data)} long!\n'
              f'  2 0 {BUF2} {BUF2 + 8 * back} long@ {emit_bytes(BUF2, back)} ;\n')
    got = run(compile_language(source), '-r', str(path))
    bits = [get_bit(old, p, False) for p in range(8 * len(old))]
    for i, v in enumerate(data):
        for k in range(8):
            bits[pos + 8 * i + k] = v >> k & 1
    want = bytes(sum(bits[8 * j + m] << (7 - m) for m in range(8)) for j in range(len(old)))
    assert path.read_bytes() == want, (path.read_bytes().hex(), want.hex())
    assert got == bytes(rev(b) for b in want) + b'\0\0', (got.hex(), want.hex())
    print(f'PASS file (remote space 2): long! of {len(data)} bytes at bit {pos} changed exactly these bits of '
          f'the file; long@ read back the {len(want)} bytes of the file (and zeros past its end)')


def check_clock():
    source = PRINT + (f': main 1 0 {BUF} {BUF + 64} long@ 0 200 0 do i + loop drop 1 0 {BUF2} {BUF2 + 64} long@\n'
                      f'  {emit_bytes(BUF, 8)} {emit_bytes(BUF2, 8)} ;\n')
    stream = compile_language(source)
    before = time.monotonic_ns()
    got = run(stream)
    after = time.monotonic_ns()
    first, second = int.from_bytes(got[:8], 'little'), int.from_bytes(got[8:16], 'little')
    assert len(got) == 16 and before <= first <= second <= after, (before, first, second, after)
    print(f'PASS clock (remote space 1): {first} <= {second} ns (monotonic time of the host, '
          f'{second - first} ns apart; the run took {after - before} ns)')


def exec_record(command):
    """The old request record EXEC with its command, as stream bytes (proto.def: op chan flags arg off)."""
    bits = [0] * REQ
    for at, n, value in ((0, 8, 5), (8, A, 0), (8 + A, 16, 0), (24 + A, 32, len(command)), (56 + A, 64, 0)):
        for k in range(n):
            bits[at + k] = value >> k & 1
    record = bytes(sum(bits[8 * j + m] << (7 - m) for m in range(8)) for j in range(REQ // 8))
    return record + command


def put(image, at, n, value):
    for k in range(n):
        if value >> k & 1:
            image[(at + k) // 8] |= 128 >> ((at + k) % 8)


def layer(*rows):
    """A processor of 8 slots of four A-bit fields (dst_low, dst_high, src_low, src_high)."""
    image = bytearray(8 * 4 * A // 8)
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            put(image, (4 * i + j) * A, A, value)
    return bytes(image)


def old_way(record):
    """The stream of the old way: the request written to SYS directly. The seed reads layer 1; each layer
    reads the next one from stdin into the processor [0, 1024); layer 1 also reads the record to 1024,
    layer 2 writes it to SYS, layer 3 reads the answer to 8192, layer 4 writes it to stdout and clears
    the processor (the next tick has no copies: the emulator stops)."""
    proc, data, at = 8 * 4 * A, 8 * len(record), 8192
    stdin, sysc, stdout = S + 1, S, S + 2
    return (layer((0, proc + data, stdin, stdin)) + layer((0, proc, stdin, stdin)) + record +
            layer((0, proc, stdin, stdin), (sysc, sysc, proc, proc + data)) +
            layer((0, proc, stdin, stdin), (at, at + 136, sysc, sysc)) +
            layer((stdout, stdout, at, at + 136), (0, proc, 16384, 16384 + proc)))


def check_exec(folder):
    mark = folder / 'exec-mark'
    command = f'echo ran >> {mark}; exit 3'.encode()
    record = exec_record(command)
    old = run(old_way(record))
    assert mark.read_text() == 'ran\n', mark.read_text()
    source = (f': main {store_bytes(BUF, [rev(b) for b in record])} 0 0 {BUF} {BUF + 8 * len(record)} long!\n'
              f'  0 0 {BUF2} {BUF2 + 136} long@ {emit_bytes(BUF2, 17)} ;\n')
    new = run(compile_language(source))
    assert mark.read_text() == 'ran\nran\n', mark.read_text()
    want, got = answer(old, False), answer(new, True)
    assert want == got and want['op'] == 5 and want['status'] == 3 and want['size'] == 3 << 8, (want, got)
    print(f'PASS EXEC through the remote space 0: the command ran, the answer {got} equals the answer of '
          'the old record written to SYS')


def check_only_when_named():
    sys.path[:0] = [str(paths.FORTH / 'scripts')]
    from forthc import model
    source = PRINT + ': main 65 emit 10 emit ;'
    assert compile_language(source) == model.compile_forth(source)
    _, records, _ = word_cost.compile_with_records(f': main 1 0 {BUF} {BUF + 64} long@ ;')
    assert {'%lr', '%lst', '%lld', 'long!', 'long@'} <= set(records), list(records)[:12]
    _, records, _ = word_cost.definition()
    assert not [name for name in records if name.startswith('%l') or name.startswith('long')], 'in the definition'
    print('PASS the words of the long copy are compiled only into a program that names them (the stream of '
          'another equals the model; the definition of the language has none)')


def main():
    subprocess.run(['make', '-s', '-C', str(paths.ROOT), 'space'], check=True)
    with tempfile.TemporaryDirectory(dir=paths.BUILD) as name:
        folder = Path(name)
        check_file(folder)
        check_clock()
        check_exec(folder)
    check_only_when_named()
    print('ALL long copy: file, clock and the old SYS through the remote space 0 on', SPACE_EMULATOR)


if __name__ == '__main__':
    main()
