"""Common seed module (host, Python, temporary): bit memory, allocator, emulator runner."""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
EMU = os.path.join(ROOT, 'emulator', 'build', 'bitcopy', 'emulator')
CHK = os.path.join(ROOT, 'emulator', 'build', 'checked-emulator')


def ensure_built():
    subprocess.run(['make', '-C', os.path.join(ROOT, 'emulator'), 'all', 'checked'],
                   check=True, capture_output=True)


class Mem:
    """Bit memory: position 0 is the 0x80 bit of byte 0; numeric values LSB first."""

    def __init__(self):
        self.b = bytearray()

    def put(self, pos, value, width):
        need = (pos + width + 7) // 8
        if len(self.b) < need:
            self.b.extend(bytes(need - len(self.b)))
        for k in range(width):
            i = pos + k
            if value >> k & 1:
                self.b[i >> 3] |= 128 >> (i & 7)
            else:
                self.b[i >> 3] &= ~(128 >> (i & 7)) & 255

    def get(self, pos, width):
        v = 0
        for k in range(width):
            i = pos + k
            if i >> 3 < len(self.b) and self.b[i >> 3] & (128 >> (i & 7)):
                v |= 1 << k
        return v

    def trimmed(self, min_bits=0):
        n = len(self.b)
        while n > 0 and self.b[n - 1] == 0:
            n -= 1
        n = max(n, (min_bits + 7) // 8)
        out = bytes(self.b[:n])
        return out + bytes(n - len(out))


def bytes_value(bs):
    """Integer which put() turns into the given bytes in memory order (MSB first)."""
    v = 0
    for i, c in enumerate(bs):
        for k in range(8):
            if c >> (7 - k) & 1:
                v |= 1 << (8 * i + k)
    return v


def rev(v, n):
    return int(format(v, '0%db' % n)[::-1], 2)


class Alloc:
    """First-fit allocator of bit intervals with alignment."""

    def __init__(self, size):
        self.size, self.taken = size, []

    def take(self, lo, bits):
        self.taken.append((lo, lo + bits))

    def alloc(self, bits, align=1):
        starts = {0} | {h for _, h in self.taken}
        for c in sorted(starts):
            c = -(-c // align) * align
            if c + bits <= self.size and all(c + bits <= l or h <= c for l, h in self.taken):
                self.taken.append((c, c + bits))
                return c
        raise MemoryError('no room for %d bits' % bits)

    def end(self):
        return max([h for _, h in self.taken] + [0])


class Result:
    pass


def run(image, A, P, checked=True, limit=200000, stdin=b''):
    S = 2 ** A - 6
    r = subprocess.run([CHK if checked else EMU, '-s', str(S), '-p', str(P), '-t', str(limit)], check=False,
                       input=image + stdin, capture_output=True, timeout=120)
    res = Result()
    res.out, res.rc, res.err = r.stdout, r.returncode, r.stderr.decode(errors='replace')
    m = re.search(r'VM1_AUDIT_TICKS=(\d+)', res.err)
    res.ticks = int(m.group(1)) if m else None
    return res


def stream(v, nbits):
    """Bytes of stdin which a `key` chain stores as the nbits-bit number v (LSB first in space)."""
    return bytes(rev(v >> 8 * i & 255, 8) for i in range(nbits // 8))
