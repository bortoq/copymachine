"""ABI geometry, full-width addresses, channel headroom and atomic rejection."""
from guest_support import run_guest

lines = ['create fmt 3 cells allot', '65520 0 8 fmt cc-format-init',
         'fmt cc-format-check cc-format-a . fmt cc-layer-bits . cr',
         '134217712 0 8 fmt cc-format-init',
         'fmt cc-format-a . fmt cc-layer-bits . cr',
         '0 2147483648 8 fmt cc-format-init',
         'fmt cc-format-a . fmt cc-layer-bits . cr']
expected = [b'16 512 \n27 864 \n64 2048 \n']
for i, (low, high, slots) in enumerate(((0, 0, 8), (65535, 0, 8), (65520, 0, 0),
                                        (255, 0, 8), (4294967295, 4294967295, 8),
                                        (0, 2147483648, 2147483647))):
    lines += [f': bad-format-{i} {low} {high} {slots} fmt cc-format-init ;',
              f"' bad-format-{i} catch . fmt cc-format-a . cr"]
    expected.append(b'-24 64 \n')
lines += ['depth . cr', 'bye']
expected.append(b'0 \n\n')
run_guest('format', ['integers.fth', 'bitfields.fth', 'format.fth'], lines, b''.join(expected))
