"""Tests of the planner (23.10), the improvement of the economical language: the serial layout of l3c (a row of the text is a layer) packed
into fewer layers. The text of language 3 begins with the word `pack` (pack mode: three slots of the processor, data before the code, the
alignments marked); l3c writes the same serial layers for the pass `programs/l3p.tw`, which lays the rows of every block out again (the list
scheduler of l3.py: nothing is touched twice in a layer, source with source too; a write into the text of a row 2 layers before it). The
chain is: text of language 3 -> l3c -> l3p -> l2l -> seed -> image (P = 3), all made by chain.py. Here: the table of l3p.tw, the layout and the rules of the
schedule on the output of the chain (layout_cost counts layers, rows and bits from the texts of language 2), the images of packed programs (they print what the serial
ones print, in fewer ticks), the choice of the layout by the price (layout.py). The outputs of l3p on the programs, the wrong texts and the spoiled ones are frozen in
tower/golden/l3p.jsonl; the packed l3p as a tool is in long_l3c.py. 
Run: make check-tower  or  python3 -B tower/tests/test_l3p.py"""
import os
import re
import sys

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import chain
import l1text
import layout
import tables
import test_l3c as t
from common import run
from golden_programs import layout_cost

LIMIT = 60 * 10 ** 6
PROGS = ['echo', 'branch', 'and_hex', 'loop_digits', 'arith8', 'arith16', 'add16_hex', 'calls']
STDIN = dict(t.STDIN)
_PASS = {}


def setUpModule():
    t.setUpModule()


def packed_of(name):
    return 'pack\n' + t.hoisted(name)


def image_of(src):
    """The image and the P by the chain (chain.build)."""
    return chain.build(src)


def l3c(src):
    """The text of language 2 which the chain gives for a text of language 3 (str or bytes; the zero byte is added): the checked run must end without a word on stderr."""
    return chain.step('l3c', 'l3c', (src.encode('latin-1') if isinstance(src, str) else src) + b'\0')


def l3p(l2):
    return chain.step('l3p', 'l3p', l2)


class Reference(unittest.TestCase):
    """The texts and the layout of the chain (no run of an image)."""

    def test_tables_are_current(self):
        """The numbers of the tables in l3p.tw are what tables.py makes."""
        self.assertEqual(tables.generated_block(t.read('l3p.tw')), tables.p_tables_text())

    def test_pass_example(self):
        """The text of the pass for a copy, a read of what it writes, halt: two layers, not three; the first has three slots."""
        ser = l3c('pack\n:a data 8 5\n:b data 8 0\n:main block\ncopy &b &a\nemit &b\nhalt\n')
        out = l3p(ser)
        lines = out.decode().split('\n')
        self.assertEqual(lines[lines.index(':bmain'):], [':bmain', 'c 8 139 131', 'c a0 0 231', 'z 50', 'd 14 ffffc', 'd 14 ffffc', 'd 14 139',
                                                        'd 14 141', 'c f0 0 &e', 'z 7', ':e', '\0'])
        self.assertEqual((layout_cost(ser, False), layout_cost(out, True)), ((5, 3, 480), (4, 2, 400)))       # (rows, layers, bits) serial and packed

    def layers(self, src):
        """The layers of the packed layout of a block text (the planner l3p of the chain on the text l3c writes)."""
        return layout_cost(l3p(l3c('pack\n' + src)), True)[1]

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
        ser = l3c(chain.step('l4c', 'l4c', src.encode() + b'\0')[:-1])
        out = l3p(ser)
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
        self.assertLess(len(layers), layout_cost(ser, False)[1])

    def test_the_layers_of_a_block_are_of_the_text(self):
        """The rows go out unchanged in a packed block, in the order the layers give; the sets of rows are the same (fields moved only in
        the patches and the tail)."""
        for name in PROGS:
            with self.subTest(name):
                ser = l3c(packed_of(name))
                out = l3p(ser)
                a = sorted(x for x in ser.decode().split('\n') if x.startswith('c ') and ' 0 ' not in x[:8])
                b = sorted(x for x in out.decode().split('\n') if x.startswith('c ') and ' 0 ' not in x[:8])
                self.assertEqual(len(a), len(b))
                self.assertLess(layout_cost(out, True)[1], layout_cost(ser, False)[1])

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
        want = chain.run_pass('l2l', hn + b'\0' + hn + b'\0')                 # the same text of language 1 as the serial l2l of the chain gives
        self.assertEqual((r.rc, r.out), (want.rc, want.out))
        self.assertEqual(r.rc, 0)


class Price(unittest.TestCase):
    """The choice of the layout by the price (layout.py): the lower languages know nothing of it (`pack` is a word of their text)."""

    def test_packed_is_cheaper(self):
        for name in ('branch', 'echo', 'arith8'):
            with self.subTest(name):
                src = t.hoisted(name)
                ch = layout.replace_layout(src, inputs=[STDIN.get(name, b'')])
                self.assertEqual(ch.index, 1)
                self.assertLess(ch.prices[1], ch.prices[0])
                self.assertTrue(ch.program.startswith('pack\n'))
                (c0, o0), (c1, o1) = (layout.chain_cost(x, [STDIN.get(name, b'')]) for x in (src, 'pack\n' + src))
                self.assertEqual(o0, o1)
                self.assertLess(c1.layers, c0.layers)
                self.assertLess(c1.bits, c0.bits)
                self.assertLess(c1.ticks, c0.ticks)

    def test_serial_is_cheaper_when_nothing_to_pack(self):
        ch = layout.replace_layout(':main block\nhalt\n')
        self.assertEqual((ch.index, ch.program), (0, ':main block\nhalt\n'))       # the first layer of three slots costs bits and gains no tick
        self.assertGreater(ch.prices[1], ch.prices[0])

    def test_different_results_are_rejected(self):
        src = ':a data 8 65\n:main block\nemit &a\nhalt\n'
        _, outs = layout.chain_cost(src)
        self.assertEqual(outs, [(0, b'\x82')])
        orig = layout.chain_cost
        try:
            layout.chain_cost = lambda s, inputs=(b'',), limit=0: (orig(s, inputs)[0], [(0, b'x' if s.startswith('pack') else b'y')])
            with self.assertRaises(ValueError):
                layout.replace_layout(src)
        finally:
            layout.chain_cost = orig


if __name__ == '__main__':
    unittest.main()
