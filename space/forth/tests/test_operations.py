"""Row summaries and pairwise conflicts against the Python Format.validate oracle."""
import random
from guest_support import run_guest
from copycode.vm1.machine import Format

fmt = Format(1000, 8)
pool = (0, 5, 10, 100, 200, 500, 850, 870, 999, 1000, 1001, 1002, 1003, 1005, 1023, 1024)


def valid(rows):
    try:
        fmt.validate(rows)
        return True
    except ValueError:
        return False


def random_row(rng):
    if rng.random() < 0.5:
        n = rng.choice((0, 1, 8, 16, 64, 130, 400))
        if rng.random() < 0.15:
            n += 3
        dl = rng.choice(pool) if rng.random() < 0.3 else rng.randrange(0, 1000)
        sl = rng.choice(pool) if rng.random() < 0.3 else rng.randrange(0, 1000)
        return dl, dl if dl >= 1000 else dl + n, sl, sl if sl >= 1000 else sl + n
    return tuple(rng.choice(pool) for _ in range(4))


lines = ['create fmt 3 cells allot', '1000 0 8 fmt cc-format-init',
         'create r1 8 cells allot', 'create r2 8 cells allot',
         'create op1 16 cells allot', 'create op2 16 cells allot',
         'r1 8 cells 0 fill r2 8 cells 0 fill',
         ': set4 ( a b c d row -- ) >r r@ 6 cells + ! r@ 4 cells + ! r@ 2 cells + ! r> ! ;',
         ': summary. ( op -- ) dup @ . dup cell+ @ . dup @ 0 ?do',
         '  i over cc-op-span dup @ . 2 cells + @ . loop drop cr ;']
expected = []
for row, text in (((10, 20, 30, 40), b'2 0 10 20 30 40 \n'), ((1000, 1000, 10, 12), b'1 2 10 140 \n'),
                  ((10, 12, 1000, 1000), b'1 3 10 117 \n'), ((1001, 1001, 16, 24), b'1 1 16 24 \n'),
                  ((0, 0, 0, 0), b'0 0 \n')):
    lines.append('%d %d %d %d r1 set4 r1 fmt op1 cc-op-check summary.' % row)
    expected.append(text)
lines += [': pair ( a b c d e f g h -- flag )',
          '  r2 set4 r1 set4 r1 fmt op1 cc-op-check drop r2 fmt op2 cc-op-check drop',
          '  op1 op2 cc-ops-conflict? ;',
          ": run8 ['] pair catch if 8 0 do drop loop 9 then . cr ;"]
cases = (((10, 20, 30, 40), (50, 60, 70, 80)),      # disjoint copies
         ((10, 20, 30, 40), (35, 45, 90, 100)),    # source overlaps source
         ((10, 20, 30, 40), (15, 25, 90, 100)),    # destination overlaps destination
         ((10, 20, 30, 40), (0, 0, 0, 0)),         # NOP partner
         ((1000, 1000, 10, 12), (1000, 1000, 500, 502)),  # two SYS requests
         ((1000, 1000, 10, 12), (500, 510, 600, 610)),    # SYS and copy
         ((1000, 1000, 10, 12), (20, 30, 1000, 1000)),    # SYS request and response
         ((10, 20, 1000, 1000), (500, 510, 600, 610)),    # SYS response and copy
         ((1001, 1001, 16, 24), (1001, 1001, 40, 48)),    # same data channel
         ((1001, 1001, 16, 24), (1002, 1002, 40, 48)),    # different data channels
         ((1001, 1001, 16, 24), (20, 28, 500, 508)),      # channel source overlap
         ((1000, 1000, 1001, 1001), (5, 6, 7, 8)),        # channel to channel
         ((10, 20, 15, 25), (50, 60, 70, 80)),            # self overlap
         ((10, 20, 30, 41), (50, 60, 70, 80)),            # unequal lengths
         ((1001, 1001, 16, 20), (50, 60, 70, 80)),        # partial-byte channel
         ((990, 1000, 10, 20), (1000, 1000, 5, 5)))       # empty channel copy
lines += [': pair ( a b c d e f g h -- flag )',
          '  r2 set4 r1 set4 r1 fmt op1 cc-op-check drop r2 fmt op2 cc-op-check drop',
          '  op1 op2 cc-ops-conflict? ;',
          ": run8 ['] pair catch if 8 0 do drop loop 9 then . cr ;"]
for rows in cases:
    if valid(rows[:1]) and valid(rows[1:]):
        answer = b'0 \n' if valid(rows) else b'-1 \n'
    else:
        answer = b'9 \n'
    lines.append('%d %d %d %d %d %d %d %d run8' % (rows[0] + rows[1]))
    expected.append(answer)
lines += ['depth . cr', 'bye']
expected.append(b'0 \n\n')
run_guest('operations', ['integers.fth', 'bitfields.fth', 'instructions.fth', 'format.fth',
                         'operations.fth'], lines, b''.join(expected))
