"""Numeric allocation, alignment, rollback, capacity and uint32 wrap boundaries."""
from guest_support import run_guest

lines = ['create arena 3 cells allot', '13 100 arena cc-arena-init',
         '5 8 arena cc-arena-alloc . 3 16 arena cc-arena-alloc . cr',
         '0 1 arena cc-arena-alloc . arena cc-arena-used . cr',
         '13 arena cc-arena-restore arena cc-arena-mark . cr']
expected = [b'16 32 \n35 22 \n13 \n']
for i, (call, code) in enumerate((('100 1 arena cc-arena-alloc drop', -8),
                                ('1 3 arena cc-arena-alloc drop', -24),
                                ('1 0 arena cc-arena-alloc drop', -24),
                                ('999 arena cc-arena-restore', -9))):
    lines += [f': bad-arena-{i} {call} ;', f"' bad-arena-{i} catch . arena cc-arena-mark . cr"]
    expected.append(f'{code} 13 \n'.encode())
lines += ['4294901761 4294967295 arena cc-arena-init',
          ': wrap-arena 1 65536 arena cc-arena-alloc drop ;',
          "' wrap-arena catch . arena cc-arena-used . cr",
          '4294901760 4294967295 arena cc-arena-init',
          '255 256 arena cc-arena-alloc 4294901760 = . arena cc-arena-used . cr',
          'arena cc-arena-reset arena cc-arena-used . depth . cr', 'bye']
expected += [b'-8 0 \n-1 255 \n0 0 \n\n']
run_guest('arena', ['arena.fth'], lines, b''.join(expected))
