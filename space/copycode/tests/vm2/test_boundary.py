#!/usr/bin/env python3
"""End-to-end boot, cooperative trace and checkpoint tests on ordinary space."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EMULATOR = Path(os.environ.get('SPACE_EMULATOR', ROOT.parent/'vm2/space')).resolve()
sys.path.insert(0, str(ROOT/'compat/vm2'))
from boundary import Format, Program, boot_stream, decode_trace


def run(packet, bits=65520, slots=8, ticks=0):
    result = subprocess.run([str(EMULATOR), '-s', str(bits), '-p', str(slots),
                             '-t', str(ticks)], input=packet, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return result


# Full installation overwrites every location touched by the loader, including
# its own processor. Use high, low and non-byte-aligned processor formats.
for bits, slots in [(65520, 8), (30000, 9), (1048576, 8)]:
    f = Format(bits, slots)
    image = bytearray(f.space_bytes)
    data, zero = f.layer_bytes*8+64, f.layer_bytes*8+256
    # Entry emits data installed well outside the processor, then stops.
    entry = f.layer([(40, bits+2, data), (f.layer_bits, 0, zero)])
    image[:len(entry)] = entry
    image[data//8:data//8+5] = b'hello'
    result = run(boot_stream(image, bits, slots), bits, slots)
    assert result.stdout == b'hello' and result.stderr == b'', result
    print(f'ok: full image through stdin, a={f.a}, p={slots}')

# Boot consumes precisely its framing/payload, leaving application input alone.
f = Format(65520, 8)
buf, zero = 4000, 5000
write = 5504
entry = f.layer([(40, buf, 65521), (f.layer_bits, 0, write)])
image = bytearray(f.space_bytes)
image[:len(entry)] = entry
# Force several payload records rather than just the final processor layer.
image[1000:7000] = bytes((i*37+11) % 256 for i in range(6000))
image[zero//8:zero//8+f.layer_bytes] = bytes(f.layer_bytes)
image[write//8:write//8+f.layer_bytes] = f.layer([(40,65522,buf),(f.layer_bits,0,zero)])
packet = boot_stream(image, 65520, 8)
assert run(packet+b'ABCDEunconsumed').stdout == b'ABCDE'
# Exercise the documented cat boot /dev/stdin launch, with actual shell redirection.
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp)/'boot'
    path.write_bytes(packet)
    result = subprocess.run(['bash', '-c', 'cat "$1" /dev/stdin | "$2" -p 8',
                             'boot-test', str(path), str(EMULATOR)],
                            input=b'ABCDEtail', capture_output=True, timeout=10)
    assert result.returncode == 0 and result.stdout == b'ABCDE', result
print('ok: concatenated boot/application input and cat boot /dev/stdin')

# A deterministic checkpoint preserves all non-processor memory and resumes
# at the requested continuation. It emits a raw image solely via copycode.
for mode in ('full', 'channels'):
    program = Program(trace=mode, code_base=8192)
    bits = program.fmt.space_bits
    source, target, input_buf, zero = 1024, 1088, 1200, 2048
    program.image[source//8:source//8+3] = b'ABC'
    program.step([(24, target, source)])
    program.step([(24, bits+2, target)])
    program.step([(32, input_buf, bits+1)])
    # Save a continuation that prints the consumed input once, then stops.
    continuation = [(32, bits+2, input_buf),
                    (program.fmt.layer_bits, 0, zero)]
    program.checkpoint(continuation, reason='limit')
    image = program.finish()
    boot = boot_stream(image, bits, 8)
    result = run(boot+b'WXYZtail')
    assert result.stdout[:3] == b'ABC'
    snapshot = result.stdout[3:]
    assert len(snapshot) == len(image)
    assert snapshot[:program.fmt.layer_bytes] == program.fmt.layer(continuation)
    expected = bytearray(image)
    expected[target//8:target//8+3] = b'ABC'
    expected[input_buf//8:input_buf//8+4] = b'WXYZ'
    # SYS answer buffers are diagnostic state; compare every byte outside
    # library-owned code and records, including untouched upper memory.
    assert snapshot[program.fmt.layer_bytes:program.base//8] == expected[program.fmt.layer_bytes:program.base//8]
    assert snapshot[program.at//8:] == expected[program.at//8:]
    text = decode_trace(result.stderr)
    assert f'channel 2 {bits+2} 24 {target} 24 0\n' in text, text
    assert f'channel 3 {bits+1} 32 {input_buf} 32 0\n' in text, text
    assert text.endswith('stop limit\n'), text
    if mode == 'full':
        assert f'copy 1 0 24 {target} {source}\n' in text, text
    else:
        assert 'copy ' not in text and 'counts 1 2\n' in text, text
    restored = run(boot_stream(snapshot, bits, 8)+b'tail')
    assert restored.stdout == b'WXYZ' and restored.stderr == b'', restored
    # Boot then dump then boot preserves the raw checkpoint, including its
    # embedded diagnostic modules; the saved continuation controls resume.
    print(f'ok: {mode} copycode trace, terminal dump, snapshot stdin restore')

# EOF state is captured by FSTAT after data service, not inferred by the decoder.
program = Program(trace='full', code_base=8192)
program.step([(40, 1024, 65521)])
program.halt()
result = run(boot_stream(program.finish(), 65520, 8)+b'XY')
assert 'channel 1 65521 40 1024 16 0\n' in decode_trace(result.stderr)
try:
    decode_trace(result.stderr[:-1])
    raise AssertionError('accepted truncated trace')
except ValueError:
    pass
print('ok: short data read and truncated trace rejection')

for option in ('--core', '--dump-space', '--restore', '--trace', '--trace-channels'):
    result = subprocess.run([str(EMULATOR), option, 'unused'], capture_output=True)
    assert result.returncode == 2, (option, result)
result = subprocess.run(['make', '-n', 'space-dev'], cwd=ROOT, capture_output=True)
assert result.returncode != 0
print('ok: removed host options and diagnostic build are unavailable')

# Migrate a generated image's ordinary halt link to a terminal report layer.
from boundary import run_image
f = Format(65520, 8)
raw = bytearray(2048)
halt, zeros = 2048, 3072
raw[halt//8:halt//8+f.layer_bytes] = f.layer([(f.layer_bits, 0, zeros)])
raw[:f.layer_bytes] = f.layer([(f.layer_bits, 0, halt)])
raw[1200:1205] = b'state'
result, snapshot = run_image(EMULATOR, raw, 65520, 8, halt)
assert result.stdout == b'' and result.stderr == b''
assert snapshot[:f.layer_bytes] == bytes(f.layer_bytes)
assert snapshot[1200:1205] == b'state'
print('ok: generated halt layer replaced by in-space terminal reporter')

# Real data bits sharing a non-byte-aligned processor byte are restored by
# the final entry read, rather than discarded as installer padding.
f = Format(30000, 9)
image = bytearray(f.space_bytes)
image[:f.layer_bytes] = f.layer([(8, 30002, f.layer_bits), (f.layer_bits, 0, 2048)])
assert f.layer_bits % 8 == 4
image[f.layer_bytes-1] |= 0x0a
image[f.layer_bytes] = 0x70
assert run(boot_stream(image, 30000, 9), 30000, 9).stdout == b'\xa7'
print('ok: image data sharing the processor padding byte survives boot')
