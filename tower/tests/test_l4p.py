"""Tests of language 4 on the chain: the copy with the address of the host (a number 0x1... in `copy`, the long copy to and from the host). Language 4 has no
words of its own: its compiler is the pass `programs/l4c.tw` over the text of language 3, which makes of such a copy the words of language 3 and the copy with the address
of the channel SYS (1048570; l3c writes the row of a channel by the address, as for emit and key); the chain is: text of language 4 -> l4c -> l3c -> [l3p] -> l2l -> seed ->
the image (chain.py makes all the passes). Here: the table and the words of l4c.tw, the images of the chain against the images of the Python compiler (the output and the host
files are the same), the example of tower/README.md (section 3.5). What the pass makes of the texts of language 4 (the long copy, the far copy of the links 0, 1 and 2, the computed
address, the forms of the channels, the edges, the refusals, the spoiled texts) is frozen in tower/golden/l4c.jsonl (test_golden.py, long_golden.py); the lists of texts below (EDGES,
FAR_EDGES, FAR_LINKS, CHAN_EDGES, COMP_*) are the inputs of that freeze (golden_programs.py).
Run: make check-tower  or  python3 -B tower/tests/test_l4p.py"""
import os
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, HERE)
import chain
import tables
import test_l3c as t
import text
from common import run

LIMIT = 30 * 10 ** 6
_PASS = {}
FILE = bytes(range(1, 65))                  # a host file: 64 bytes


def setUpModule():
    t.setUpModule()


def host(area, bit):
    """The address of the host: 2^128 + the position (the area in the top 32 bits, the bit in the area), 0x1 and 32 hex digits."""
    return '0x%x' % (1 << 128 | area << 96 | bit)


def pass_tool():
    """The image of the pass l4c made by the chain itself (chain.py: the seed on l4c.l1)."""
    if not _PASS:
        img, A, P = chain.tool('l4c')
        _PASS.update(image=img, A=A, P=P)
    return _PASS


def says(r):
    """What the tool wrote to stderr (without the audit line of the checking emulator)."""
    return r.err.split('VM1_AUDIT')[0]


def l4c(src, limit=LIMIT):
    """What the tool l4c gives for a text of language 4 (bytes; the zero byte is added)."""
    st = pass_tool()
    return run(st['image'], st['A'], st['P'], checked=True, limit=limit, stdin=src + b'\0')


def readme_example():
    """The program of tower/README.md, section 3.5."""
    with open(os.path.join(HERE, '..', 'README.md'), encoding='utf-8') as h:
        doc = h.read()
    return re.search(r'### 3\.5\..*?```tw\n(.*?)```', doc, re.S).group(1)


PROGRAMS = {
    # put 40 bits at the bit 8 of the area 1 (the file), get them back (less than 117 bits: through the buffer of the answer)
    'rw': ':out data 40 "hello"\n:got data 40 "\\0\\0\\0\\0\\0"\n:main block\ncopy %s &out\ncopy &got %s\nemit &got\nhalt\n' % (host(1, 8), host(1, 8)),
    # three reads of 8 bytes, the position moved by 64: a constant in the text
    'cat': ':buf data 64 0\n:main block\n' + ''.join('copy &buf %s\nemit &buf\n' % host(1, 64 * k) for k in range(3)) + 'halt\n',
    # 200 bits (a whole answer is read into the data): put, get; 117 and 116 bits (the edge of the buffer), 1 bit, 5 bits at the bit 2
    'sizes': (':x data 200 "abcdefghijklmnopqrstuvwxy"\n:w data 200 0\n:v data 120 0\n:u data 8 0\n:main block\n'
              'copy %(a)s &x\ncopy &w %(a)s\nemit &w\ncopy &v[0:117] %(a)s\nemit &v[0:112]\n'
              'copy &v[0:116] %(a)s\nemit &v[0:112]\ncopy %(a)s &x[0:1]\ncopy &u[0:5] %(a)s\nemit &u\n'
              'copy %(b)s &x[8:13]\ncopy &u %(b)s\nemit &u\nhalt\n') % {'a': host(1, 2), 'b': host(1, 7)},
    # outside the file (past its end, far above it, an area which is not there): reads give zeros, writes are lost
    'outside': (':x data 16 "ab"\n:z data 16 "\\0\\0"\n:main block\ncopy %(a)s &x\ncopy &z %(a)s\nemit &z\ncopy &z %(b)s\nemit &z\nhalt\n')
               % {'a': host(1, 1 << 20), 'b': host(17, 1 << 20)},
    # the clock (the area 0): two reads, the second is not less than the first
    'clock': (':t1 data 64 0\n:t2 data 64 0\n:c data 17 0\n:y data 8 "Y"\n:n data 8 "N"\n:main block\ncopy &t1 %(a)s\n'
              'copy &t2 %(a)s\nlt &t2 &t1 &c\nif &c[16] &no &yes\n:yes block\nemit &y\nhalt\n:no block\nemit &n\nhalt\n') % {'a': host(0, 0)},
}
HOSTA = host(1, 8)


def farad(bit, link=0):
    """The far address (26.4): 0x2 and 32 hex digits: the link in the top 32 bits, the position in bits in the low 96."""
    return '0x2%032x' % (link << 96 | bit)


FAR = farad(8 * 3)
# the texts with the far copy: the forms which are translated and those which are not (the same bytes as the reference, also in the pack mode, in a string, in a comment)
FAR_EDGES = [
    (':x data 64 0\n:y data 8 0\n:z data 16 0\n:main block\ncopy &x {a}\ncopy {a} &x\ncopy &y {a}\ncopy {a} &z\nhalt\n'.format(a=FAR)).encode(),
    ':x data 64 0\n:main block\ncopy &x[8:24] {a}\ncopy {a} &x[32:64]\ncopy &x[0:8] {b}\nhalt\n'.format(a=FAR, b=farad(8 * 255)).encode(),
    ':x data 64 0\n:main block\ncopy &x {a}\ncopy {a} &x\nhalt\n'.format(a=farad(8 * (1 << 28) - 8 * 3)).encode(),         # the carry through the nibbles
    ':x data 64 0\n:main block\ncopy &x {a}\ncopy {a} &x\ncopy &x {b}\nhalt\n'.format(a=farad(8 * 0xfff0), b=farad(8 * 0x7fffff8 - 8 * 100)).encode(),
    # not translated: the link is not 0, the position is not a multiple of 8, 2^32 bits or more, the width is not whole bytes of 8..64 or is not known, two far or a far and a host
    ':x data 64 0\n:b data 4 0\n:w data 72 0\n:t table 1 8 1 2\n:main block\ncopy &x {l}\ncopy {l} &x\ncopy &x {m}\ncopy {m} &x\ncopy &x {g}\ncopy {g} &x\ncopy &b {a}\n'
    'copy {a} &w\ncopy &t {a}\ncopy &q {a}\ncopy &x[3] {a}\ncopy &x[0:12] {a}\ncopy &x[5:5] {a}\ncopy {a} {a}\ncopy {a} {h}\ncopy {h} {a}\nhalt\n'.format(
        l=farad(0, 3), m=farad(12), g=farad(1 << 32), a=FAR, h=HOSTA).encode(),
    # 0x2 with another number of digits is not a far address (a host one, as before: the digits are the position)
    ':x data 8 0\n:main block\ncopy &x 0x2{d31}\ncopy &x 0x2{d33}\ncopy &x 0x2000\ncopy &x 0x2\ncopy &x 0X2{d32}\ncopy &x 0x3{d32}\ncopy &x 0x2{d32}g\nhalt\n'.format(
        d31='0' * 31, d32='0' * 32, d33='0' * 33).encode(),
    b':x data 16 0\n:main block\ncopy &x ' + FAR.encode() + b'  # copy &x ' + FAR.encode() + b'\n:s data 8 "copy &x ' + FAR.encode() + b'"\ncopy ' + FAR.encode() + b'\n',
    b'copy &x ' + FAR.encode(), b':x data 16 0\ncopy &x ' + FAR.encode(), b':x data 16 0\ncopy ' + FAR.encode() + b' &x', b':x data 8 0\n:main block\ncopy +2 ' + FAR.encode() + b'\n',
    b'pack\n:x data 24 0\n:main block\ncopy &x ' + FAR.encode() + b'\ncopy ' + FAR.encode() + b' &x\nhalt\n',
    b':x data 9000 0\n:y data 16 0\n:main block\ncopy &x[9890:9906] ' + FAR.encode() + b'\ncopy &x[9899:9915] ' + FAR.encode() + b'\ncopy &x[9900:9916] ' + FAR.encode() + b'\ncopy &y ' + FAR.encode() + b'\n',
]
FAR0, FAR1, FAR2 = FAR, farad(8 * 3, 1), farad(8 * 3, 2)
# the links 1 (the check and the repeat) and 2 (the common file) are translated (the words l4ask, l4flag, l4fget stand once at the end of the text); 3 and over are not
FAR_LINKS = [
    ':x data 64 0\n:y data 8 0\n:z data 16 0\n:main block\ncopy &x {a}\ncopy {a} &x\ncopy &y {a}\ncopy {a} &z\nhalt\n'.format(a=FAR1).encode(),
    ':x data 64 0\n:y data 8 0\n:z data 16 0\n:main block\ncopy &x {a}\ncopy {a} &x\ncopy &y {a}\ncopy {a} &z\nhalt\n'.format(a=FAR2).encode(),
    ':x data 64 0\n:main block\ncopy &x[8:24] {a}\ncopy {a} &x[32:64]\ncopy &x[0:8] {b}\nhalt\n'.format(a=FAR1, b=farad(8 * 255, 1)).encode(),
    ':x data 64 0\n:main block\ncopy &x[8:24] {a}\ncopy {a} &x[32:64]\ncopy &x[0:8] {b}\nhalt\n'.format(a=FAR2, b=farad(8 * 255, 2)).encode(),
    ':x data 64 0\n:main block\ncopy &x {a}\ncopy {a} &x\nhalt\n'.format(a=farad(8 * (1 << 28) - 8 * 3, 1)).encode(),         # the carry through the nibbles
    ':x data 64 0\n:main block\ncopy &x {a}\ncopy {a} &x\ncopy &x {b}\nhalt\n'.format(a=farad(8 * 0xfff0, 2), b=farad(8 * 0x7fffff8 - 8 * 100, 2)).encode(),
    # the three links and the host in one text: the words in the order l4ask, l4flag, l4fget, once each; the labels go on from copy to copy
    ':x data 32 0\n:main block\ncopy &x {a}\ncopy {b} &x\ncopy &x {c}\ncopy {d} &x\ncopy &x {e}\ncopy {a} &x\ncopy &x {c}\nhalt\n'.format(
        a=farad(0), b=farad(8, 1), c=farad(16, 2), d=farad(24, 2), e=HOSTA).encode(),
    # only a put of the link 2 (l4flag alone), only a get of it (l4fget alone), only a get of the link 1 (l4ask alone)
    ':x data 8 0\n:main block\ncopy {a} &x\nhalt\n'.format(a=FAR2).encode(), ':x data 8 0\n:main block\ncopy &x {a}\nhalt\n'.format(a=FAR2).encode(),
    ':x data 8 0\n:main block\ncopy &x {a}\nhalt\n'.format(a=FAR1).encode(),
    b'pack\n:x data 24 0\n:main block\ncopy &x ' + FAR1.encode() + b'\ncopy ' + FAR1.encode() + b' &x\ncopy &x ' + FAR2.encode() + b'\ncopy ' + FAR2.encode() + b' &x\nhalt\n',
    # the text ends in the middle of a copy, or with no newline: the words follow
    b':x data 8 0\n:main block\ncopy &x ' + FAR1.encode() + b'\nhalt', b':x data 8 0\n:main block\ncopy &x ' + FAR2.encode() + b'\ncopy &x',
    # not translated: the link 3 and over, the position as for the link 0
    ':x data 8 0\n:main block\ncopy &x {a}\ncopy {b} &x\ncopy &x {c}\ncopy &x {d}\ncopy &x {e}\nhalt\n'.format(
        a=farad(0, 3), b=farad(0, 255), c=farad(12, 1), d=farad(1 << 32, 2), e=farad(4, 2)).encode(),
]
FAR_EDGES += FAR_LINKS
# a channel from the end of the space: `+k` is S + k (the same text for every A); the program with the forms and the same with the words emit warn key
CHAN_FORMS = ':a data 8 "A"\n:e data 8 "E"\n:b data 8 0\n:main block\ncopy +2 &a\ncopy +3 &e\ncopy &b +1\ncopy +2 &b\ncopy +3 &b\nhalt\n'
CHAN_WORDS = ':a data 8 "A"\n:e data 8 "E"\n:b data 8 0\n:main block\nemit &a\nwarn &e\nkey &b\nemit &b\nwarn &b\nhalt\n'
CHAN_EDGES = [
    b':a data 8 0\n:main block\ncopy +2 &a\ncopy &a +1\ncopy +0 &a\ncopy +3 &a  # c\n:t data 8 "copy +2 &a"\n', b'copy +2', b'copy +2 +3', b'copy +5 +4 copy +1 +2',
    b':a data 8 0\n:main block\ncopy +6 &a\ncopy +12 &a\ncopy + &a\ncopy +a &a\ncopy -2 &a\ncopy ++ &a\ncopy &a[0:4] +4\n',
    b':a data 8 0\n:main block\ncopy +2 ' + HOSTA.encode() + b'\ncopy ' + HOSTA.encode() + b' +1\ncopy &a ' + HOSTA.encode() + b'\n',
    b'pack\n:a data 8 0\n:main block\ncopy +2 &a\nhalt\n', b':a data 8 "+2"\n:main block\ncopy  +2   &a   copy &a\t+1\n',
]
# the computed address (25.4): `copy &x &t@&i` is `lut &t &i &x`, `copy &t@&i &x` is `store &t &i &x`; the widths are those of lut and store (the index K bits, &x w bits)
COMP_PRE = ':i data 3 0\n:j data 10 0\n:x data 8 0\n:y data 9 0\n:t table 3 8 1 2 3 4 5 6 7 8\n:a array 3 8\n:b array 10 8\n:c array 1 8\n:main block\n'
COMP_GOOD = ['&x &t@&i', '&x &a@&i', '&a@&i &x', '&x &b@&j', '&b@&j &x', '&x &a@&j[0:3]', '&a@&j[3:6] &x', '&x[0:8] &b@&j[0:10]', '&x &c@&j[5]', '&c@&j[9] &x[0:8]',
             '&y[1:9] &a@&i', '&a@&i &y[0:8]', '&x   &a@&i', '&a@&i\t&x']
# not translated: the table or array is not known (not a table, a data, an unknown name, a table for the write), the width of &x or of the index is not w or K, the other operand is
# not a part of space (a channel, a number, an address of the host or of the far space, a computed address too)
COMP_BAD = {'at name': ['&t@&i &x', '&x &q@&i', '&x &x@&i', '&y &i@&i', '&x &add4@&i', '&x &hex4@&i', '&x &zero@&i'],
            'at width': ['&a@&i &q', '&y &a@&i', '&a@&i &y', '&x &a@&j', '&x &a@&j[0:2]', '&x &a@&j[0:4]', '&x[0:7] &a@&i', '&x &a@&q', '&x &a@', '&x &a@&', '&x &a@0', '&x &a@&i[1:1]',
                         '&a@&i &a@&i', '+2 &a@&i', '&a@&i +1', '1048572 &a@&i', '&x &a@&b@&j', '%s &a@&i' % HOSTA, '&a@&i %s' % FAR, '&x &a@&i&j']}
COMP_EDGES = [
    (COMP_PRE + ''.join('copy %s\n' % c for c in COMP_GOOD) + 'halt\n').encode(),
    (COMP_PRE + ''.join('copy %s\n' % c for r in COMP_BAD.values() for c in r) + 'halt\n').encode(),
    # the declarations: the first of a name stays, table array and data share the names, K and w are the numbers after the word (else nothing is kept)
    b':t table 3 8 1 2 3 4 5 6 7 8\n:t table 2 8 1 2 3 4\n:t data 8 0\n:x data 8 0\n:i data 3 0\n:i data 2 0\n:main block\ncopy &x &t@&i\ncopy &t@&i &x\n',
    b':t array 3 8\n:t table 3 8 1 2 3 4 5 6 7 8\n:x data 8 0\n:i data 3 0\n:main block\ncopy &x &t@&i\ncopy &t@&i &x\n',
    b':x data 8 0\n:i data 3 0\n:t table 3\n:u table x 8\n:v array 3 "8"\n:w table 0x3 8\n:z array 3 8x\n:main block\ncopy &x &t@&i\ncopy &x &u@&i\ncopy &x &v@&i\ncopy &x &w@&i\ncopy &x &z@&i\n',
    b':x data 8 0\n:i data 3 0\n:t table 19 8\n:u array 3 136\n:v array 3 1\n:w table 1048579 8\n:main block\ncopy &x &t@&i\ncopy &x &u@&i\ncopy &v@&i[0:3] &x[0:1]\ncopy &x &w@&i[0]\n',
    b':x data 8 0\n:i data 3 0\n:t\ntable 3 8 :u\n array\n3\n8\n:main block\ncopy &x &t@&i\ncopy &x &u@&i\ncopy &u@&i &x\n',
    b':x data 8 0\n:i data 3 0\n:a array 3 8\n:main block\ncopy &a@&i &x\n# copy &x &a@&i\n:s data 64 "copy &x &a@&i"\ncopy &x &a@&i   # x\n',
    b':x data 8 0\n:i data 3 0\n:a array 3 8\n:main block\ncopy &x &abcdefghijklmn@&i\ncopy &x &abcdefghijklmno@&i\ncopy &x &1a@&i\ncopy &x &@&i\ncopy &x &a@@&i\ncopy &x & a@&i\n',
    b':x data 8 0\n:i data 3 0\n:abcdefghijklmn array 3 8\n:main block\ncopy &x &abcdefghijklmn@&i\ncopy &abcdefghijklmn@&i[0:3] &x\n',
    b'pack\n:x data 8 0\n:i data 3 0\n:a array 3 8\n:main block\ncopy &x &a@&i\ncopy &a@&i &x\nhalt\n',
    b':x data 8 0\n:i data 3 0\n:a array 3 8\n:main block\ncopy &x &a@&i', b':x data 8 0\n:i data 3 0\n:a array 3 8\n:main block\ncopy &x', b'copy &x &a@&i',
    b':a array 3 8\ncopy &x &a@&i', b':x data 8 0\ncopy &x &a@&i',
    # with the host, the far space and the channels in one text: each form by itself
    (':x data 8 0\n:i data 3 0\n:a array 3 8\n:main block\ncopy &x {h}\ncopy &x &a@&i\ncopy {f} &x\ncopy &a@&i &x\ncopy +2 &x\ncopy &x {f}\nhalt\n'.format(h=HOSTA, f=FAR)).encode(),
]
# texts for the pass: what it must give as it is, and what it must leave unchanged
EDGES = [
    b'', b'# only a comment', b'   ', b'copy', b'copy &a', b'copy &a &b', b'x copy &a 0x1000', b':a data 8 0\n:main block\ncopy &a 0x1000\nhalt\n',
    ':a data 8 0 :main block copy &a {h} halt'.format(h=HOSTA).encode(),
    (':a data 8 0\n:b data 300 0\n:main block\ncopy &a {h}\ncopy {h} &b[0:117]\ncopy &b[3:4]  {h}\ncopy &b[3] {h}\nhalt\n'.format(h=HOSTA)).encode(),
    (':a data 8 0\n:main block\ncopy &zz {h}\ncopy &a[2:2] {h}\ncopy &a[3:9] {h}\ncopy &a[:] {h}\ncopy &a[1:2:3] {h}\ncopy &a[1:2]x {h}\n'.format(h=HOSTA)).encode(),
    (':a data 3000 0\n:b data 2048 0\n:c data 2049 0\n:main block\ncopy &a {h}\ncopy &b {h}\ncopy &c {h}\ncopy &c[0:100] {h}\n'.format(h=HOSTA)).encode(),
    (':a data 8 "copy &b 0x1"\n# copy &a 0x1\n:main block\ncopy &a {h}  # trailing\nhalt\n'.format(h=HOSTA)).encode(),
    (':a data 8 "q\\"copy"\n:main block\ncopy {h} &a\n copy 0x1 0x1\ncopy 0x1 &a\ncopy {h} {h}\ncopy 0x0x &a\n'.format(h=HOSTA)).encode(),
    (':abcdefghijklmnop data 8 0\n:abcdefghijklmn data 9 0\n:main block\ncopy &abcdefghijklmn {h}\ncopy &abcdefghijklmnop {h}\ncopy &1a {h}\n'.format(h=HOSTA)).encode(),
    (':a data 8 0\n:a data 16 0\n:t table 2 8 1 2 3 4\n:q data 5 0\n:r array 2 8\n:main block\ncopy &a {h}\ncopy &t {h}\ncopy &r {h}\ncopy &q {h}\n'.format(h=HOSTA)).encode(),
    b':w data 0x10 5\n:v data 12 7\n:main block\ncopy 0X1000000010000000000000000000000ff &v\ncopy &v 0x1000000010000000000000000000000FF\n'
    b'copy &v 0x1000000010000000000000000000000fg\ncopy &v 0x\ncopy &v 0xf\n',
    b'copy &a ' + HOSTA.encode(), b':a data 8 0\ncopy ' + HOSTA.encode(), b':a data 8 0\ncopy ' + HOSTA.encode() + b' &a', b':a data 8 "unfinished',
    b':a data 8 1099511627776 :b data 12 4095 :main block copy &b ' + HOSTA.encode() + b' copy &a ' + HOSTA.encode(),
]


class Texts(unittest.TestCase):
    """The text of l4c.tw (no emulator); the texts which the pass makes are frozen in tower/golden/l4c.jsonl (test_golden.py, long_golden.py)."""

    def test_tables_are_current(self):
        """The numbers of the tables in l4c.tw are what tables.py makes."""
        self.assertEqual(tables.generated_block(t.read('l4c.tw')), tables.x_tables_text())

    def test_strings_have_their_width(self):
        """The data of l4c.tw which are strings have exactly the bits of their bytes (emit sends all of them)."""
        n = 0
        for m in re.finditer(r'^:\w+ data (\d+) "((?:[^"\\]|\\.)*)"', t.read('l4c.tw'), re.M):
            self.assertEqual(int(m.group(1)), 8 * len(m.group(2).replace('\\n', '\n').replace('\\0', '\0').replace('\\"', '"')), m.group(0))
            n += 1
        self.assertGreater(n, 20)

    def test_the_words_of_the_links_in_the_tool(self):
        """The strings fa.., ff.., fg.. of l4c.tw (32 bytes each, emitted one after the other) are the words l4ask, l4flag, l4fget of tables.py, each after a line break."""
        src = t.read('l4c.tw')
        for pfx, word in zip(('fa', 'ff', 'fg'), tables.FARWORDS, strict=True):
            got = ''.join(m.group(1).replace('\\n', '\n') for m in re.finditer(r'^:%s\d\d data \d+ "((?:[^"\\]|\\.)*)"' % pfx, src, re.M))
            self.assertEqual(got, '\n' + word, pfx)

    def test_tool_image(self):
        """The image of the pass (made by the chain, serial: A = 20, P = 2) is in the places of l3c (the tables of the library stand at LIMIT bits)."""
        st = pass_tool()
        self.assertEqual((st['A'], st['P']), (20, 2))
        self.assertLess(len(st['image']) * 8, tables.LIMIT)


class Programs(unittest.TestCase):
    """The images of the chain (l4c, l3c, l2l, seed) do the long copies as the images of the Python compiler: the same output and the same host file."""

    def both(self, src, data=FILE, pack=False):
        img, P = chain.build(('pack\n' if pack else '') + src, True)
        py, errs = text.compile_text(src)
        self.assertEqual(errs, [])
        res = []
        for image, A, p in ((img, 20, P), (py.stats['image'], py.stats['A'], py.stats['P'])):
            d = tempfile.mkdtemp(prefix='tower-l4p-')
            self.addCleanup(shutil.rmtree, d, True)
            f = os.path.join(d, 'f.bin')
            with open(f, 'wb') as h:
                h.write(data)
            r = run(image, A, p, checked=True, limit=LIMIT, files=[f])
            with open(f, 'rb') as h:
                res.append((r.rc, r.out, h.read(), r.ticks))
        self.assertEqual(res[0][:3], res[1][:3], src)
        self.assertEqual(res[0][0], 0)
        return res[0]

    def test_programs(self):
        for name, src in PROGRAMS.items():
            with self.subTest(name):
                rc, out, host_file, ticks = self.both(src)
                self.assertTrue(out)
                if name == 'rw':
                    self.assertEqual((out, host_file[:6]), (b'hello', bytes([FILE[0]]) + b'hello'))
                elif name == 'cat':
                    self.assertEqual(out, FILE[:24])
                elif name == 'clock':
                    self.assertEqual(out, b'Y')

    def test_channel_from_the_end(self):
        """A program with `copy +2 &a` (stdout), `copy +3 &e` (stderr), `copy &b +1` (stdin) does what the same program with emit warn key does: the same
        output, error, code, and the same image (the pass l4c gives the numbers of l3c, and the rows of a channel are the same); in the pack mode too. Only A = 20 is built by the chain (l3c has
        A = 20), so the text is checked as one for every A by the reference: it has no number of A."""
        for pack in ('', 'pack\n'):
            forms, P = chain.build(pack + CHAN_FORMS, True)
            words, P2 = chain.build(pack + CHAN_WORDS, True)
            self.assertEqual((forms, P), (words, P2))
            a, b = (run(img, 20, P, checked=True, limit=LIMIT, stdin=b'Z') for img in (forms, words))
            self.assertEqual((a.rc, a.out, a.err), (b.rc, b.out, b.err))
            self.assertEqual((a.rc, a.out), (0, b'AZ'))
            self.assertIn('E', a.err)
        self.assertNotRegex(CHAN_FORMS, r'10485')

    def test_packed_programs(self):
        """The same in pack mode (l4c, l3c, l3p): the output and the host file as the Python images, in fewer ticks than the serial."""
        for name in ('rw', 'sizes', 'outside', 'cat'):
            with self.subTest(name):
                a = self.both(PROGRAMS[name])
                b = self.both(PROGRAMS[name], pack=True)
                self.assertEqual(a[:3], b[:3])
                self.assertLess(b[3], a[3])

    def test_readme_example(self):
        """The example of the README: `hello` is written at the bit 8 of the file and read back; the pack mode gives the same, in fewer ticks."""
        src = readme_example()
        rc, out, host_file, ticks = self.both(src)
        self.assertEqual((out, host_file[:6]), (b'hello', bytes([FILE[0]]) + b'hello'))
        self.assertEqual(host_file[6:], FILE[6:])
        _, out2, host2, ticks2 = self.both(src, pack=True)
        self.assertEqual((out2, host2), (out, host_file))
        self.assertLess(ticks2, ticks)


if __name__ == '__main__':
    unittest.main()
