"""Independent configuration oracle and raw-stream process checks.

No imports from emulator generators, machine manifests or consumer projects.
"""
from pathlib import Path
import os
import resource
import subprocess
import sys

EMULATOR = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SPACE_EMULATOR', './space')).resolve()
ASAN = os.environ.get('SPACE_TEST_ASAN') == '1'
if ASAN:
    assert 'allocator_may_return_null=1' in os.environ.get('ASAN_OPTIONS', ''), (
        'ASan allocation probes require ASAN_OPTIONS=allocator_may_return_null=1')
    print('ASan: RLIMIT_AS disabled for shadow memory; enormous requests must return NULL')
cases = 0


def run(args, data=b'', limited=False):
    global cases
    def limit_memory():
        resource.setrlimit(resource.RLIMIT_AS, (128*1024*1024, 128*1024*1024))
    result = subprocess.run([str(EMULATOR), *map(str, args)], input=data,
                            capture_output=True, timeout=5,
                            preexec_fn=limit_memory if limited and not ASAN else None)
    cases += 1
    return result


def check_config(bits, slots):
    width = bits.bit_length()
    valid = (bits > 0 and slots > 0 and
             slots*(3*width-1) <= min(bits, (1 << max(0, width-1))-1) and
             bits+6 <= 1 << width)
    result = run(['-s', bits, '-p', slots, '-t', 1])
    assert result.returncode == (0 if valid else 2), (bits, slots, result)
    assert not result.stdout


for bits in range(1, 65):
    for slots in range(1, 6):
        check_config(bits, slots)
for width in range(5, 25):
    for bits in sorted({(1 << width)+offset for offset in (-7, -6, -5, -1, 0, 1)}):
        a = bits.bit_length()
        top = min(bits, (1 << (a-1))-1)//(3*a-1)
        for slots in sorted({0, 1, max(1, top-1), top, top+1}):
            check_config(bits, slots)

for args in [
    ['-s', 0], ['-p', 0], ['-s'], ['-p'], ['-t'], ['--help'], ['--core', 'x'],
    ['x'], ['-s', '-1'], ['-p', '+1'], ['-s', '0x100'], ['-t', '1x'],
    ['-s', ''], ['-t', '-1'], ['-s', 1 << 64], ['-p', 1 << 64], ['-t', 1 << 64],
]:
    assert run(args).returncode == 2, args
assert run(['-s16', '-p1', '-t1']).returncode == 0
assert run(['-s', 0, '-s16', '-p1', '-t1']).returncode == 0
assert run(['-s16', '-p1', '-t', (1 << 64)-1], b'\0\0').returncode == 0

# Huge, otherwise admissible sizes must reach allocation failure, not an
# arbitrary width/channel rejection. Native builds use RLIMIT_AS. ASan
# reserves shadow memory, so it instead uses allocator_may_return_null=1:
# these >= 2**59-byte requests exceed the supported host address space.
for bits in (1 << 62, 1 << 63, (1 << 64)-6):
    result = run(['-s', bits, '-p', 1, '-t', 1], limited=True)
    assert result.returncode == 1 and b'out of memory' in result.stderr, (bits, result)
for bits in range((1 << 64)-5, 1 << 64):
    assert run(['-s', bits, '-p', 1, '-t', 1], limited=True).returncode == 2


def put(image, at, width, value):
    for j in range(width):
        bit = 128 >> ((at+j) % 8)
        if value >> j & 1:
            image[(at+j)//8] |= bit
        else:
            image[(at+j)//8] &= ~bit


def instruction(image, slot, n, dst, src):
    for offset, width, value in ((0, 15, n), (15, 16, dst), (31, 16, src)):
        put(image, slot*47+offset, width, value)


image = bytearray(47)  # Eight 47-bit slots at -s65520; one output per tick.
instruction(image, 0, 8, 65522, 62)
for k in range(8):
    put(image, 62+k, 1, (ord('A') >> (7-k)) & 1)  # Payload in a NOP field.
for ticks in (1, 2, 3, 9):
    result = run(['-p8', '-t', ticks], bytes(image))
    assert result.returncode == 0 and result.stdout == b'A'*(ticks-1), result

# Erase output n and the two erasing instructions; the source of A remains
# untouched. The whole active tick completes before the next all-NOP fetch.
instruction(image, 2, 15, 0, 512)
instruction(image, 3, 62, 94, 576)
for args in (['-p8'], ['-p8', '-t2'], ['-p8', '-t9']):
    result = run(args, bytes(image))
    assert result.returncode == 0 and result.stdout == b'A', result

print(f'core CLI: {cases} configuration/process cases, bounded allocation failures and exact tick stops passed')
