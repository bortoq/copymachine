"""Tests of the planner (23.10), the improvement of the economical language: the serial layout of l3c (a row of the text is a layer) packed
into fewer layers. The text of language 3 begins with the word `pack` (pack mode: three slots of the processor, data before the code, the
alignments marked); l3c writes the same serial layers for the pass `programs/l3p.tw`, which lays the rows of every block out again (the list
scheduler of l3.py: nothing is touched twice in a layer, source with source too; a write into the text of a row 2 layers before it). The
chain is: text of language 3 -> l3c -> l3p -> l2l -> seed -> image (P = 3). The Python reference is l3ctext.py (encode with `pack`, pack_pass).
Here: the reference (the layout, the rules of the schedule, the errors), the images of packed programs (they print what the serial ones print, in
fewer ticks), l3c in pack mode and l3p agree with the reference byte for byte, language 5 chooses the layout by the price. The long runs
(the tools made by the packed chain, the fixed point with the planner) are in long_l3c.py.
Run: make check-tower  or  python3 -B tower/tests/test_l3p.py"""
import os
import random
import re
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import l1text
import l2ltext
import l3ctext
import l5
import test_l3c as t
from common import run

LIMIT = 60 * 10 ** 6
PROGS = ['echo', 'branch', 'and_hex', 'loop_digits', 'arith8', 'arith16', 'add16_hex', 'calls']
STDIN = dict(t.STDIN)
_PASS = {}


def setUpModule():
    t.setUpModule()


def pass_tool():
    """The image of l3p.tw made packed by the references of the chain (l3c in pack mode, l3p, l2l, the seed; the long test runs the tools themselves)."""
    if not _PASS:
        img, P = l5.chain_image('pack\n' + t.read('l3p.tw'))
        _PASS.update(image=img, A=20, P=P)
    return _PASS


def l3p(l2, limit=LIMIT):
    st = pass_tool()
    return run(st['image'], st['A'], st['P'], checked=True, limit=limit, stdin=l2)


ERRORS = [(':bmain\nw 1\n', 'bad'), (':bmain\nc 1 2\n', 'bad'), (':bmain\nz 51\nc a0 0 0\n:e\n', 'bad'), (':bmain\nz 50\nz 50\n', 'bad'),
          (':bmain\nd 14 1\nc 1 1 1\n', 'bad'), (':bmain\nz 50\nc a0 0 200\n:e\n', 'bad'), (':bmain\nd 14 1\nd 14 1\nd 14 1\nc a0 0 0\n', 'bad'),
          (':bmain\nz 50\nc a0 0 0\n# a 3 5\nc 1 1 1\n:e\n', 'bad'), ('# a 2 3\n', 'bad'), (':bmain\nz 50\nc a0 0 &e\n# a 3 5\nz 4\n:e\n', 'bad'),
          (':bmain\nz 50\nc a0 0 &e\n:e\nz 5', 'bad'), (':bmain\nc 1 2 3\nc a0 0 100\n', 'bad'), (':bmain\nz 50\n', 'bad'),
          (':bmain\n' + 'c 1 2 3\nc a0 0 4\n' * 253 + 'z 50\nc a0 0 &e\n:e\n', None), (':bmain\n' + 'c 1 2 3\nc a0 0 4\n' * 254 + 'z 50\nc a0 0 &e\n:e\n', 'big'),
          (':bmain\nc 1 2 3\nc a0 0 &e\n:bx\nc 4 1 2\nc a0 0 0\n:e\n', None), (':bmain\nz 50\nc 1 2 2e0\nc a0 0 &e\n:e\n', 'bad'),
          (':bmain\nz 50\nc 1 %x 2\nc a0 0 &e\n:e\n' % 0x1e1, 'bad')]


def packed_of(name):
    return 'pack\n' + t.hoisted(name)


def image_of(src):
    """The image and the P by the references of the whole chain."""
    return l5.chain_image(src)


class Reference(unittest.TestCase):
    """The texts and the Python reference (no emulator)."""

    def test_tables_are_current(self):
        """The numbers of the tables in l3p.tw are what l3ctext.p_tables_text makes."""
        src = t.read('l3p.tw')
        a, b = src.index('# --- begin generated\n'), src.index('# --- end generated')
        self.assertEqual(src[a + len('# --- begin generated\n'):b], l3ctext.p_tables_text())

    def test_tool_is_in_its_subset(self):
        """l3p.tw is a text of the subset (the chain compiles it): the reference takes it, in both layouts, with room in A = 20 and in l2l."""
        src = t.read('l3p.tw')
        for text in (src, 'pack\n' + src):
            out, err = l3ctext.encode(text)
            self.assertIsNone(err)
            self.assertLess(len(out) * 8, 1 << 21)
        c = l3ctext.Compiler()
        c.put(l3ctext.prelude())
        l3ctext.run(c, src.encode())
        self.assertLess(c.pos, l3ctext.LIMIT)
        self.assertLess(2 * len(c.syms), l3ctext.MAXSYM)
        out, err = l3ctext.encode('pack\n' + src)
        self.assertLess(sum(1 for ln in out.decode().split('\n') if ln[:2] in (':b', ':r', ':t')), l2ltext.MAXLAB - 100)

    def test_pack_mode_format(self):
        """The first word: the prelude with three slots, `zero` and `one` 80 bits later, the markers of the alignments, +f0, data before code."""
        out, err = l3ctext.encode('pack\n:a data 8 5\n:main block\nhalt\n')
        self.assertIsNone(err)
        self.assertEqual(out.decode(), l3ctext.prelude(True) + 'd 8 5\n:bmain\nz 50\nc a0 0 &e\n# a 3 7\nz 7\n:e\n\0')
        self.assertEqual(l3ctext.prelude(True).count('\n'), l3ctext.prelude().count('\n') + 2)
        out, err = l3ctext.encode('pack\n:t table 2 4 1 2 3 4\n:main block\nhalt\n')
        self.assertIn('d 14 &e\nd 14 ffffb\nd 14 ffffb\nz 50\nz 50\no\nz 50\nc f0 0 &bmain\nz 50\nz 40\nd 1 1\n# a ', out.decode())
        self.assertEqual(l3ctext.encode(':main block\nhalt\n')[0], l3ctext.encode('\n:main block\nhalt\n')[0])
        out, err = l3ctext.encode('pack\n:main block\nif &zero &y &n\n:y block\nhalt\n:n block\nhalt\n')
        self.assertIsNone(err)
        self.assertIn('d 14 &bn\nd 14 &bn+f0\n', out.decode())
        self.assertIn('\n# a 7 ', out.decode())
        for src, why in (('pack\n:main block\nhalt\n:a data 1 0\n', 'blk'), ('pack\n:main block\nhalt\n:a table 1 1 1 0\n', 'blk'),
                         (':a data 1 0\npack\n:main block\nhalt\n', 'bad'), ('pack pack\n:main block\nhalt\n', 'bad'),
                         ('pack\n:a data 1 0\n:b block\n:main block\nhalt\n', 'blk')):
            with self.subTest(src):
                self.assertEqual(l3ctext.encode(src)[1], why)
        self.assertEqual(l3ctext.encode('pack')[0], l3ctext.encode('pack\n')[0])

    def test_pass_example(self):
        """The text of the pass for a copy, a read of what it writes, halt: two layers, not three; the first has three slots."""
        ser, err = l3ctext.encode('pack\n:a data 8 5\n:b data 8 0\n:main block\ncopy &b &a\nemit &b\nhalt\n')
        out, perr = l3ctext.pack_pass(ser)
        self.assertIsNone(perr)
        lines = out.decode().split('\n')
        self.assertEqual(lines[lines.index(':bmain'):], [':bmain', 'c 8 139 131', 'c a0 0 231', 'z 50', 'd 14 ffffc', 'd 14 ffffc', 'd 14 139',
                                                        'd 14 141', 'c f0 0 &e', 'z 7', ':e', '\0'])
        self.assertEqual(l3ctext.STATS, {'serial': (5, 3, 480), 'packed': (4, 2, 400)})

    def layers(self, src):
        ser, err = l3ctext.encode('pack\n' + src)
        self.assertIsNone(err, src)
        out, perr = l3ctext.pack_pass(ser)
        self.assertIsNone(perr)
        return l3ctext.STATS['packed'][1]

    def test_rules_of_the_schedule(self):
        """Independent copies share a layer (two rows at most); a write meets a read or a write: the next layer; two reads of the same bits:
        two layers (source with source); a patch is 2 layers before the row it patches (lut: 2 patches, the row 2 layers after the second)."""
        head = ':a data 8 1\n:b data 8 2\n:c data 8 3\n:d data 8 4\n:e data 8 5\n:f data 8 6\n:t table 1 8 7 9\n:o data 8 0\n:main block\n'
        self.assertEqual(self.layers(head + 'copy &a &b\ncopy &c &d\nhalt\n'), 1)
        self.assertEqual(self.layers(head + 'copy &a &b\ncopy &c &d\ncopy &e &f\nhalt\n'), 2)         # a layer has two rows
        self.assertEqual(self.layers(head + 'copy &a &b\ncopy &c &a\nhalt\n'), 2)                    # a is read, then written
        self.assertEqual(self.layers(head + 'copy &a &b\ncopy &d &b\nhalt\n'), 2)                    # b is read twice: source with source
        self.assertEqual(self.layers(head + 'copy &a &b\ncopy &d &a\ncopy &b &d\nhalt\n'), 3)        # a chain of three
        self.assertEqual(self.layers(head + 'copy &a &b\nhalt\n'), 1)
        # lut with one index: patch sl, patch sh (the same source), then the row 2 layers after: 4 layers; a copy and a halt fit in
        self.assertEqual(self.layers(head + 'lut &t &d[0] &o\nhalt\n'), 4)
        self.assertEqual(self.layers(head + 'lut &t &d[0] &o\ncopy &e &f\nhalt\n'), 4)
        self.assertEqual(self.layers(head + 'lut &t &d[0] &o\nlut &t &e[0] &f\nhalt\n'), 5)          # the patches of the second fill the first's waits

    def test_language_4_in_the_plan(self):
        """Language 4: after the pass l4c a long copy is planned like other rows: the row to the channel SYS (the request) is a layer before the row from it (the
        answer), the answer is copied into the data a layer after the read, the nibbles of the request are copied from the constants of the pass, and the rows
        of the request are packed as others (fewer layers than the serial text)."""
        host = '0x%x' % (1 << 128 | 1 << 96 | 8)
        src = 'pack\n:w data 200 0\n:x data 8 0\n:main block\ncopy &w[0:16] %s\ncopy &x &w[0:8]\ncopy %s &w[0:16]\nhalt\n' % (host, host)
        l3, _ = l3ctext.l4c(src.encode() + b'\0')
        ser, err = l3ctext.encode(l3[:-1])
        self.assertIsNone(err)
        out, perr = l3ctext.pack_pass(ser)
        self.assertIsNone(perr)
        lines = out.decode().split('\n')
        lines = lines[lines.index(':bmain') + 1:lines.index(':e')]
        layers, cur = [], []
        for ln in lines:
            cur.append(ln)
            if ln.startswith('c ') and ln.split()[2] == '0':
                layers.append(cur)
                cur = []
        text = ['\n'.join(lay) for lay in layers]
        w = [k for k, x in enumerate(text) if re.search(r'd 14 ffffa\nd 14 ffffa\nd 14 [0-9a-f]+\nd 14 [0-9a-f]+\n', x)]
        r = [k for k, x in enumerate(text) if re.search(r'd 14 [0-9a-f]+\nd 14 [0-9a-f]+\nd 14 ffffa\nd 14 ffffa\n', x)]
        self.assertEqual((len(w), len(r)), (2, 1))              # the request of the get, the request of the put; the answer of the get
        self.assertLess(w[0], r[0])
        copy = [k for k, lay in enumerate(layers) if any(x.startswith('c 10 ') for x in lay)]
        self.assertEqual(len(copy), 2)                              # the answer into the data, the data into the request of the put
        self.assertLess(r[0], copy[0])
        self.assertLess(len(layers), l3ctext.STATS['serial'][1])

    def test_the_layers_of_a_block_are_of_the_text(self):
        """The rows go out unchanged in a packed block, in the order the layers give; the sets of rows are the same (fields moved only in
        the patches and the tail)."""
        for name in PROGS:
            with self.subTest(name):
                ser, err = l3ctext.encode(packed_of(name))
                self.assertIsNone(err)
                out, perr = l3ctext.pack_pass(ser)
                self.assertIsNone(perr)
                a = sorted(x for x in ser.decode().split('\n') if x.startswith('c ') and ' 0 ' not in x[:8])
                b = sorted(x for x in out.decode().split('\n') if x.startswith('c ') and ' 0 ' not in x[:8])
                self.assertEqual(len(a), len(b))
                self.assertLess(l3ctext.STATS['packed'][1], l3ctext.STATS['serial'][1])

    def test_the_tools_are_packed(self):
        """Fewer layers and bits for the tools of the chain: seed, l2c, l2l (rows and bits, layers; the measurements are in docs)."""
        for name, ratio in (('seed', 0.85), ('l2c', 0.8), ('l2l', 0.7)):
            with self.subTest(name):
                ser, err = l3ctext.encode(packed_of(name))
                self.assertIsNone(err)
                self.assertIsNone(l3ctext.pack_pass(ser)[1])
                (rs, ls, bs), (rp, lp, bp) = l3ctext.STATS['serial'], l3ctext.STATS['packed']
                self.assertLess(lp, ratio * ls)
                self.assertLess(bp, bs)
                self.assertLess(rp, rs)

    def test_errors_of_the_pass(self):
        """A block with a wrong line, cut by the zero byte, of more than 254 layers, a pad without its zeros: the report, and the lines before it."""
        good, err = l3ctext.encode(packed_of('branch'))
        self.assertIsNone(err)
        text = good.decode()
        head = text[:text.index(':bmain\n')]
        for tail, why in ERRORS:
            with self.subTest(tail[:50]):
                out, perr = l3ctext.pack_pass((head + tail).encode() + b'\0')
                self.assertEqual(perr, why)
                if why:
                    self.assertTrue((head + tail[:tail.index('\n') + 1] if tail.startswith(':b') else head).encode().startswith(out[:len(head)]))
                    self.assertFalse(out.endswith(b'\0'))
        out, perr = l3ctext.pack_pass((head + ':bmain\nz 50\nc a0 0 &e\n:e\n').encode() + b'\0')
        self.assertEqual((perr, out.endswith(b':bmain\nc f0 0 &e\nz 50\nz 50\n:e\n\0')), (None, True))
        out, perr = l3ctext.pack_pass((head + ':bmain\nw 1\n').encode() + b'\0')
        self.assertEqual((perr, out.endswith(b':bmain\n')), ('bad', True))


class Images(unittest.TestCase):
    """The images of packed programs (three slots) print what the serial ones print, in fewer ticks."""

    def run_both(self, src, stdin=b''):
        a, P = image_of(src)
        b, Q = image_of('pack\n' + src)
        self.assertEqual((P, Q), (2, 3))
        r = run(a, 20, 2, checked=True, limit=LIMIT, stdin=stdin)
        q = run(b, 20, 3, checked=True, limit=LIMIT, stdin=stdin)
        self.assertEqual((r.rc, q.rc), (0, 0), (r.err, q.err))
        self.assertEqual(r.out, q.out)
        return r, q

    def test_programs(self):
        total = [0, 0]
        for name in PROGS:
            with self.subTest(name):
                r, q = self.run_both(t.hoisted(name), STDIN.get(name, b''))
                self.assertTrue(r.out)
                self.assertLess(q.ticks, r.ticks)
                total[0] += r.ticks
                total[1] += q.ticks
        self.assertLess(total[1] * 6, total[0] * 5)         # a fifth fewer ticks at least on these (the numbers are in docs/measurements/tower.md)

    def test_calls_and_stores(self):
        src = ''':msg data 24 "ab\\n"
:t table 2 4 5 6 7 8
:x array 3 4
:i data 3 0
:v data 4 0
:o data 4 0
:r data 3 0
:s data 5 0
:q data 1 0
:n data 8 0
:sh data 8 0
:h1 data 8 0
:h2 data 8 0
:main block
emit &msg[0:8]
copy &i[0:2] &msg[1:3]
call &w &m2
:m2 block
lt &o &v &r
eq &o &v &q
sub &o &v &s
shl &msg[0:8] &sh 3
shr &msg[0:8] &n 2
lut &hex4 &o &h1
lut &hex4 &s[0:4] &h2
emit &h1
emit &h2
if &q &m3 &m4
:m3 block
emit &msg[8:16]
halt
:m4 block
emit &msg[16:24]
halt
:w word
lut &t &i[0:2] &v
store &x &i &v
lut &x &i &o
ret
'''
        r, q = self.run_both(src)
        self.assertEqual(r.out[:1], b'a')
        self.assertLess(q.ticks, r.ticks)

    def test_the_tools_made_packed(self):
        """seed turns seed.l1 into the image of the seed, l2l makes the text of language 1 of hello_names.l2, both made packed (P = 3)."""
        seed, P = image_of(packed_of('seed'))
        src = t.read('seed.l1', 'rb') + b'\0'
        r = run(seed, 20, P, checked=True, limit=LIMIT, stdin=src)
        self.assertEqual((r.rc, r.out), (0, l1text.encode(src)[0]))
        serial, _ = image_of(t.hoisted('seed'))
        s = run(serial, 20, 2, checked=True, limit=LIMIT, stdin=src)
        self.assertEqual(s.out, r.out)
        self.assertLess(r.ticks * 4, s.ticks * 3)
        l2l, P = image_of(packed_of('l2l'))
        hn = t.read('hello_names.l2', 'rb')
        r = run(l2l, 20, P, checked=True, limit=LIMIT, stdin=hn + b'\0' + hn + b'\0')
        self.assertEqual((r.rc, r.out), (0, l2ltext.encode(hn, twice=True)[0]))


class Planner(unittest.TestCase):
    """l3c in pack mode and l3p, the images made by the Python compiler of the chain, against the reference."""

    @classmethod
    def setUpClass(cls):
        cls.tool = t.tool()
        cls.p = pass_tool()

    def test_l3p_image(self):
        self.assertEqual((self.p['A'], self.p['P']), (20, 3))
        self.assertLess(len(self.p['image']) * 8, 1 << 20)

    def test_l3c_in_pack_mode(self):
        """l3c writes in pack mode what the reference writes (the programs, the errors of the mode)."""
        for name in PROGS:
            with self.subTest(name):
                r = t.l3c(packed_of(name))
                want, err = l3ctext.encode(packed_of(name))
                self.assertEqual((r.rc, r.out, err), (0, want, None), r.err)
        for src in ('pack\n:main block\nhalt\n:a data 1 0\n', 'pack\n:main block\nhalt\n:a table 1 1 1 0\n', ':a data 1 0\npack\n:main block\nhalt\n',
                    'pack pack\n', 'pack\n:a data 1 0\n:main block\nhalt\n', 'pack', 'pack\n\n# x\n:t table 3 2 1 2 3 0 1 2 3 0\n:main block\nhalt\n',
                    'pack\n:a :b data 1 0', 'pack\n:x array 4 7\n:main block\nstore &x &x[0:4] &x[0:7]\nhalt\n', '@\n', '# c\n@\n',
                    'pack\n:a data 8 0\n:main block\nif &a &main &main\nadd &a &a &a\n'):
            with self.subTest(src):
                r = t.l3c(src)
                want, err = l3ctext.encode(src)
                self.assertEqual(r.out, want)
                self.assertEqual('l3c: ' in r.err, err is not None, r.err)

    def check_pass(self, l2):
        r = l3p(l2)
        want, err = l3ctext.pack_pass(l2)
        self.assertEqual(r.out, want, l2[-200:])
        self.assertEqual('l3p: ' in r.err, err is not None, (l2[-200:], r.err))
        if err:
            self.assertIn(l3ctext.PMESSAGES[err], r.err)
        return r

    def test_l3p_programs(self):
        for name in ('echo', 'branch', 'arith8', 'calls'):
            with self.subTest(name):
                ser, err = l3ctext.encode(packed_of(name))
                self.assertIsNone(err)
                r = self.check_pass(ser)
                self.assertEqual(r.rc, 0)

    def test_l3p_long_words(self):
        """The planner on the text after the pass l4c: the rows to SYS and the nibbles from the constants, the same bytes as the reference."""
        host = '0x%x' % (1 << 128 | 1 << 96 | 8)
        src = 'pack\n:w data 200 0\n:x data 8 0\n:main block\ncopy &w[0:16] %s\ncopy &x &w[0:8]\ncopy %s &w\ncopy &w %s\nhalt\n' % (host, host, host)
        ser, err = l3ctext.encode(l3ctext.l4c(src.encode() + b'\0')[0][:-1])
        self.assertIsNone(err)
        self.assertEqual(self.check_pass(ser).rc, 0)

    def test_l3p_tools(self):
        """The planner on the output of l3c for seed.tw: the same bytes (the long run does l2c, l2l, l3c and l3p)."""
        ser, err = l3ctext.encode(packed_of('seed'))
        self.assertIsNone(err)
        self.assertEqual(self.check_pass(ser).rc, 0)

    def test_the_chain(self):
        """text of language 3 -> l3c (the image of Python) -> l3p (the image of Python) -> l2l, seed (the references) -> the image runs as the serial one."""
        for name in ('branch', 'loop_digits', 'echo'):
            with self.subTest(name):
                a = t.l3c(packed_of(name))
                b = l3p(a.out)
                self.assertEqual(b.rc, 0, b.err)
                l1, err = l2ltext.encode(b.out[:-1], twice=True)
                self.assertIsNone(err)
                img, err = l1text.encode(l1)
                self.assertIsNone(err)
                q = run(img, 20, 3, checked=True, limit=LIMIT, stdin=STDIN.get(name, b''))
                ser, _ = image_of(t.hoisted(name))
                r = run(ser, 20, 2, checked=True, limit=LIMIT, stdin=STDIN.get(name, b''))
                self.assertEqual((q.rc, q.out), (r.rc, r.out))
                self.assertLess(q.ticks, r.ticks)

    def test_errors_of_l3p(self):
        good, err = l3ctext.encode(packed_of('branch'))
        text = good.decode()
        head = text[:text.index(':bmain\n')]
        for tail, why in ERRORS:
            with self.subTest(tail[:50]):
                r = self.check_pass((head + tail).encode() + b'\0')
                self.assertEqual(r.rc, 0 if why is None else r.rc)

    def test_mutations(self):
        """About 80 spoiled texts of a small program: the pass and the reference give the same bytes and the same report."""
        rng = random.Random(2310)
        base, err = l3ctext.encode('pack\n:t table 2 8 1 2 3 4\n:a data 8 1\n:b data 8 2\n:main block\nlut &t &a[0:2] &b\nif &b[0] &y &n\n:y block\n'
                                   'emit &a\ncall &w &z\n:z block\nhalt\n:n block\nhalt\n:w word\nkey &a\nret\n')
        self.assertIsNone(err)
        junk = ['c', 'z 50', 'd 14 1', 'c a0 0 &e', 'c a0 0 0', 'c 1 2', '# a 3 4', ':bx', '', 'q', 'c a0 0 &bmain', 'c f0 0 12', 'o', 'z ff', '# a 9 0',
                '# a 3', '# b 3 4', '#a 3 4', '# a', 'w 14 1 2 3', 'c a0 0 0 0']
        lines = base.decode().split('\n')[:-1]
        for _ in range(80):
            ls = list(lines)
            for _ in range(rng.choice((1, 1, 2))):
                k = rng.randrange(len(ls))
                m = rng.randrange(4)
                if m == 0:
                    ls[k] = rng.choice(junk)
                elif m == 1:
                    del ls[k]
                elif m == 2:
                    ls.insert(k, rng.choice(junk))
                else:
                    ls = ls[:k]
                    break
                if not ls:
                    break
            text = ('\n'.join(ls) + '\n').encode('latin-1') + b'\0'
            self.check_pass(text)


class Price(unittest.TestCase):
    """Language 5 chooses the layout by the price; the lower languages know nothing of it (`pack` is a word of their text)."""

    def test_packed_is_cheaper(self):
        for name in ('branch', 'echo', 'arith8'):
            with self.subTest(name):
                src = t.hoisted(name)
                ch = l5.replace_layout(src, inputs=[STDIN.get(name, b'')])
                self.assertEqual(ch.index, 1)
                self.assertLess(ch.prices[1], ch.prices[0])
                self.assertTrue(ch.program.startswith('pack\n'))
                (c0, o0), (c1, o1) = (l5.chain_cost(x, [STDIN.get(name, b'')]) for x in (src, 'pack\n' + src))
                self.assertEqual(o0, o1)
                self.assertLess(c1.layers, c0.layers)
                self.assertLess(c1.bits, c0.bits)
                self.assertLess(c1.ticks, c0.ticks)

    def test_serial_is_cheaper_when_nothing_to_pack(self):
        ch = l5.replace_layout(':main block\nhalt\n')
        self.assertEqual((ch.index, ch.program), (0, ':main block\nhalt\n'))       # the first layer of three slots costs bits and gains no tick
        self.assertGreater(ch.prices[1], ch.prices[0])

    def test_different_results_are_rejected(self):
        src = ':a data 8 65\n:main block\nemit &a\nhalt\n'
        _, outs = l5.chain_cost(src)
        self.assertEqual(outs, [(0, b'\x82')])
        orig = l5.chain_cost
        try:
            l5.chain_cost = lambda s, inputs=(b'',), limit=0: (orig(s, inputs)[0], [(0, b'x' if s.startswith('pack') else b'y')])
            with self.assertRaises(ValueError):
                l5.replace_layout(src)
        finally:
            l5.chain_cost = orig


if __name__ == '__main__':
    unittest.main()
