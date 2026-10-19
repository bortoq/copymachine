"""Decode pre-existing external bytes, rather than trusting encoder round trips."""
from guest_support import run_guest
from copycode.vm1.machine import put

data = bytearray([165] * 16)
values = (800, 808, 1024, 1032)
for i, value in enumerate(values):
    put(data, 3 + i * 27, 27, value)
lines = ['create decoded 8 cells allot', 'decoded 32 90 fill', 'create encoded 16 allot']
lines += [f'{value} encoded {i} + c!' for i, value in enumerate(data)]
lines += ['decoded encoded 16 3 27 cc-instruction@', 'decoded 32 type cr', 'depth . cr']
expected = [b''.join(v.to_bytes(8, 'little') for v in values) + b'\n', b'0 \n']
for i, call in enumerate(('decoded encoded 16 21 27', 'decoded encoded 16 0 0',
                          'decoded decoded 32 0 1')):
    code = -24 if i == 1 else -9
    lines += [f': bad-decode-{i} {call} cc-instruction@ ;',
              f"' bad-decode-{i} catch . cr", 'decoded 32 type cr']
    expected += [f'{code} \n'.encode(), expected[0]]
lines += ['encoded 16 type cr', 'depth . cr', 'bye']
expected += [bytes(data) + b'\n', b'0 \n', b'\n']
run_guest('instruction-decode', ['bitfields.fth', 'instructions.fth'], lines, b''.join(expected))
