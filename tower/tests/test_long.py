"""Tests of language 4 (the long copy `long!`, `long@`) on the emulator in checked mode and the audit of
intervals: files `-r` (also sparse, positions over 2**32 bits), the clock, positions outside, cat in a loop.
Run: make check-tower  or  python3 -B tower/tests/test_long.py"""
import os
import re
import shutil
import sys
import tempfile
import time

sys.dont_write_bytecode = True
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import l3
import l4
import progs
from common import rev, run
from l4 import host_pos
from test_tower import intervals


def setUpModule():
    common.ensure_built()


def slurp(path):
    with open(path, 'rb') as h:
        return h.read()


def bits(buf, pos, n):
    """n bits of the host file buf from the bit pos as bytes in the order of space (zeros past the end)."""
    out = bytearray((n + 7) // 8)
    for k in range(n):
        i = pos + k
        if i >> 3 < len(buf) and buf[i >> 3] & 128 >> (i & 7):
            out[k >> 3] |= 128 >> (k & 7)
    return bytes(out)


def put_bits(buf, pos, data, n):
    buf = bytearray(buf)
    need = (pos + n + 7) // 8
    buf.extend(bytes(max(0, need - len(buf))))
    for k in range(n):
        i = pos + k
        if data[k >> 3] & 128 >> (k & 7):
            buf[i >> 3] |= 128 >> (i & 7)
        else:
            buf[i >> 3] &= ~(128 >> (i & 7)) & 255
    return bytes(buf)


class Long(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='tower-long-')
        self.addCleanup(shutil.rmtree, self.dir, True)

    def file(self, content=b'', name='f'):
        path = os.path.join(self.dir, name)
        with open(path, 'wb') as f:
            f.write(content)
        return path

    def go(self, build, files=(), stdin=b'', plain=False):
        p = l3.compile_program(build)
        st = p.stats
        r = run(st['image'], st['A'], st['P'], checked=True, stdin=stdin, files=files)
        self.assertEqual(r.rc, 0, r.err)
        self.assertNotIn('AUDIT', r.err.replace('VM1_AUDIT_TICKS', ''))
        intervals(p)
        if plain:                     # the production emulator on a copy of the files: the same output and files
            copies = []
            for k, f in enumerate(files):
                c = os.path.join(self.dir, 'plain%d' % k)
                shutil.copyfile(f, c)
                copies.append(c)
            q = run(st['image'], st['A'], st['P'], checked=False, stdin=stdin, files=copies)
            self.assertEqual(q.out, r.out)
        return p, r

    def test_constants_match_proto_def(self):
        src = slurp(os.path.join(common.ROOT, 'emulator', 'src', 'proto.def')).decode()
        self.assertEqual(int(re.search(r'XOP\(LONG,\s*(\d+)\)', src).group(1)), l4.OP_LONG)
        self.assertEqual(int(re.search(r'XCONST\(HOST_POS_BITS,\s*(\d+)\)', src).group(1)), l4.POS_BITS)
        self.assertEqual(int(re.search(r'XCONST\(HOST_AREA_BITS,\s*(\d+)\)', src).group(1)), l4.AREA_BITS)
        self.assertEqual(int(re.search(r'XFIELD\(req, arg,\s*(\d+)\)', src).group(1)), l4.ARG_BITS)

    def test_write_then_read(self):
        """long! then long@ of the same place; the file gets the bits (the rest of it stays), at byte and bit positions."""
        old = bytes(range(0x80, 0x80 + 40))
        for k, (bit, data) in enumerate(((64, b'Hello!'), (0, b'\x00\xff\x12'), (3, b'bit offset'), (37, b'x'), (8 * 100, b'tail'))):
            f = self.file(old)
            p, r = self.go(progs.long_rw(host_pos(1, bit), data, host_pos(1, bit)), [f], plain=(k == 0))
            self.assertEqual(r.out, data, (bit, data))
            self.assertEqual(slurp(f), put_bits(old, bit, data, 8 * len(data)), (bit, data))
        self.assertEqual((p.stores, p.lookups), (0, 0))

    def test_read_existing(self):
        """long@ of a file made on the host: the text, a chunk across a byte boundary, the bytes with high bits."""
        text = bytes(range(256)) + b'copymachine\n'
        f = self.file(text)
        for bit, n in ((0, 16), (8 * 256, 12), (5, 20), (8 * 250 + 7, 10), (8 * len(text) - 16, 2)):
            p, r = self.go(progs.long_rw(0, b'', host_pos(1, bit), n), [f])
            self.assertEqual(r.out, bits(text, bit, 8 * n), (bit, n))
            self.assertEqual(slurp(f), text)

    def test_two_files(self):
        """Areas 1 and 2 are the files in the order of -r; a write to one does not touch the other."""
        a, b = self.file(b'AAAAAAAA', 'a'), self.file(b'BBBBBBBB', 'b')
        p, r = self.go(progs.long_rw(host_pos(2, 16), b'xy', host_pos(1, 8), 3), [a, b])
        self.assertEqual(r.out, b'AAA')
        self.assertEqual((slurp(a), slurp(b)), (b'AAAAAAAA', b'BBxyBBBB'))

    def test_sparse_file_far_position(self):
        """A sparse file over 32 MiB, and positions over 2**32 bits (a byte over 512 MiB): written, read, the rest stays a hole."""
        f = self.file()
        with open(f, 'r+b') as h:
            h.truncate(40 * 1024 * 1024)
            h.seek(40 * 1024 * 1024 - 4)
            h.write(b'END!')
        for bit in (2 ** 33 + 5, 2 ** 32, 2 ** 32 - 3, 40 * 1024 * 1024 * 8 - 128):
            data = b'far:' + bytes([bit & 255])
            p, r = self.go(progs.long_rw(host_pos(1, bit), data, host_pos(1, bit)), [f])
            self.assertEqual(r.out, data, bit)
            self.assertEqual(bits(self.window(f, bit), bit % 8, 8 * len(data)), data)
        st = os.stat(f)
        self.assertGreaterEqual(st.st_size, (2 ** 33 + 5 + 40) // 8)
        self.assertLess(st.st_blocks * 512, 1 << 20)                     # still a hole, not 1 GiB of data
        p, r = self.go(progs.long_rw(0, b'', host_pos(1, 40 * 1024 * 1024 * 8 - 32), 4), [f])
        self.assertEqual(r.out, b'END!')
        self.assertEqual(self.window(f, 0)[:8], bytes(8))

    @staticmethod
    def window(path, bit):
        with open(path, 'rb') as h:
            h.seek(bit // 8)
            return h.read(16)

    def test_clock(self):
        """Area 0: 64 bits, the time of the host in ns (low bit first); two reads do not decrease."""
        before = time.monotonic_ns()
        p, r = self.go(progs.long_clock())
        after = time.monotonic_ns()
        self.assertEqual(len(r.out), 16)
        t1, t2 = (sum(rev(b, 8) << 8 * i for i, b in enumerate(r.out[k:k + 8])) for k in (0, 8))
        self.assertTrue(before <= t1 <= t2 <= after, (before, t1, t2, after))
        self.assertGreater(t1, 0)

    def test_outside_is_zero(self):
        """Outside a file, outside an area, an unknown area, the clock past 64 bits: zeros, nothing else happens."""
        text = b'0123456789'
        f = self.file(text)
        for area, bit, n in ((1, 80, 4), (1, 8 * 9 + 4, 4), (1, 2 ** 40, 4), (1, 2 ** 64 + 8, 4), (1, 2 ** 70, 4),
                             (1, 2 ** 96 - 8, 3), (2, 0, 4), (7, 0, 4), (2 ** 32 - 1, 5, 2), (0, 64, 4), (0, 2 ** 80, 4)):
            p, r = self.go(progs.long_rw(0, b'', host_pos(area, bit), n), [f])
            self.assertEqual(r.out, bytes(n) if (area, bit) != (1, 8 * 9 + 4) else bits(text, bit, 8 * n), (area, bit))
            self.assertEqual(slurp(f), text)
        # a write there is lost: the file is the same, a read back gives zeros
        for area, bit in ((1, 2 ** 64 + 8), (1, 2 ** 96 - 8), (2, 0), (0, 0), (0, 8)):
            p, r = self.go(progs.long_rw(host_pos(area, bit), b'lost', host_pos(1, 8 * 3)), [f])
            self.assertEqual(r.out, b'3456', (area, bit))
            self.assertEqual(slurp(f), text)
            if area != 0:                                       # the same place read back: zeros
                p, r = self.go(progs.long_rw(host_pos(area, bit), b'lost', host_pos(area, bit)), [f])
                self.assertEqual(r.out, bytes(4), (area, bit))
        self.assertEqual(os.stat(f).st_size, len(text))

    def test_cat(self):
        """A loop reads the file by chunks, the position grows by a chain of `add` of 128 bits, the chunks go to stdout."""
        text = bytes(range(1, 41))
        f = self.file(text)
        p, r = self.go(progs.long_cat(1, 5, 8), [f], plain=True)
        self.assertEqual(r.out, text)
        self.assertEqual(p.stores, 0)
        p, r = self.go(progs.long_cat(1, 4, 8), [self.file(b'hello, copymachine', 'g')])    # 18 bytes in 4 chunks of 8
        self.assertEqual(r.out, b'hello, copymachine' + bytes(14))                         # past the end: zeros
        p, r = self.go(progs.long_cat(1, 3, 5, start=12), [f])                            # not at a byte
        self.assertEqual(r.out, bits(text, 12, 120))
        p, r = self.go(progs.long_cat(1, 3, 16), [f])                                     # a chunk longer than an answer record
        self.assertEqual(r.out, text + bytes(8))
        for n in (1, 15):
            p, r = self.go(progs.long_cat(1, n, 3), [f])
            self.assertEqual(r.out, (text + bytes(9))[:3 * n])

    def test_cat_over_2_32_bits(self):
        """The position crosses 2**32 bits: the carry of the chain of `add` runs through the nibbles."""
        f = self.file()
        base = 2 ** 32 // 8 - 16
        payload = bytes(range(100, 100 + 40))
        with open(f, 'r+b') as h:
            h.seek(base)
            h.write(payload)
        p, r = self.go(progs.long_cat(1, 5, 8, start=2 ** 32 - 128), [f])
        self.assertEqual(r.out, payload)
        self.assertLess(os.stat(f).st_blocks * 512, 1 << 20)
        p, r = self.go(progs.long_cat(1, 3, 8, start=2 ** 64 - 64), [f])                   # across 2**64 bits: outside
        self.assertEqual(r.out, bytes(24))

    def test_grammar(self):
        """A request cannot be written in another way: the position has 128 bits, the length is 1..2**32-1."""
        def short_pos(p):
            p.block('main'); p.long_put(p.var('pos', 64), p.var('d', 8))
        def empty(p):
            p.block('main'); p.long_get(p.var('pos', 128), p.var('d', 0))
        def too_long(p):
            p.block('main'); p.long_get(p.var('pos', 128), p.var('d', 2 ** 32))
        for build in (short_pos, empty, too_long):
            with self.assertRaises(AssertionError):
                l3.compile_program(build)
        with self.assertRaises(AssertionError):
            host_pos(2 ** 32, 0)
        with self.assertRaises(AssertionError):
            host_pos(1, 2 ** 96)
        src = ''.join(slurp(os.path.join(common.HERE, 'tests', m + '.py')).decode() for m in ('l1', 'l2', 'l3', 'lib'))
        self.assertNotIn('SYS', src.replace('SYS pseudo', ''))     # no word of languages 1-3 touches the channel SYS


if __name__ == '__main__':
    common.ensure_built()
    unittest.main()
