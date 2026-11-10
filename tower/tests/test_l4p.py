"""Tests of language 4 on the chain: the copy with the address of the host (a number 0x1... in `copy`, the long copy to and from the host). Language 4 has no
words of its own: its compiler is the pass `programs/l4c.tw` over the text of language 3, which makes of such a copy the words of language 3 and the copy with the address
of the channel SYS (1048570; l3c writes the row of a channel by the address, as for emit and key); the chain is: text of language 4 -> l4c -> l3c -> [l3p] -> l2l -> seed ->
the image. Here: the reference (the text which the pass makes, the unchanged rest, the edges), the tool l4c against it byte for byte (also on spoiled texts), the images of
the chain against the images of the Python compiler (the output and the host files are the same), the example of tower/README.md (section 3.5). The long runs (the tools
made by the chain itself) are in long_l3c.py.
Run: make check-tower  or  python3 -B tower/tests/test_l4p.py"""
import os
import random
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import l3ctext
import l5
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
    """The image of l4c.tw made by the references of the chain (l3c, l2l, the seed; the long test runs the tools themselves)."""
    if not _PASS:
        img, P = l5.chain_image(t.read('l4c.tw'))
        _PASS.update(image=img, A=20, P=P)
    return _PASS


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
        l=farad(0, 1), m=farad(12), g=farad(1 << 32), a=FAR, h=HOSTA).encode(),
    # 0x2 with another number of digits is not a far address (a host one, as before: the digits are the position)
    ':x data 8 0\n:main block\ncopy &x 0x2{d31}\ncopy &x 0x2{d33}\ncopy &x 0x2000\ncopy &x 0x2\ncopy &x 0X2{d32}\ncopy &x 0x3{d32}\ncopy &x 0x2{d32}g\nhalt\n'.format(
        d31='0' * 31, d32='0' * 32, d33='0' * 33).encode(),
    b':x data 16 0\n:main block\ncopy &x ' + FAR.encode() + b'  # copy &x ' + FAR.encode() + b'\n:s data 8 "copy &x ' + FAR.encode() + b'"\ncopy ' + FAR.encode() + b'\n',
    b'copy &x ' + FAR.encode(), b':x data 16 0\ncopy &x ' + FAR.encode(), b':x data 16 0\ncopy ' + FAR.encode() + b' &x', b':x data 8 0\n:main block\ncopy +2 ' + FAR.encode() + b'\n',
    b'pack\n:x data 24 0\n:main block\ncopy &x ' + FAR.encode() + b'\ncopy ' + FAR.encode() + b' &x\nhalt\n',
    b':x data 9000 0\n:y data 16 0\n:main block\ncopy &x[9890:9906] ' + FAR.encode() + b'\ncopy &x[9899:9915] ' + FAR.encode() + b'\ncopy &x[9900:9916] ' + FAR.encode() + b'\ncopy &y ' + FAR.encode() + b'\n',
]
# a channel from the end of the space: `+k` is S + k (the same text for every A); the program with the forms and the same with the words emit warn key
CHAN_FORMS = ':a data 8 "A"\n:e data 8 "E"\n:b data 8 0\n:main block\ncopy +2 &a\ncopy +3 &e\ncopy &b +1\ncopy +2 &b\ncopy +3 &b\nhalt\n'
CHAN_WORDS = ':a data 8 "A"\n:e data 8 "E"\n:b data 8 0\n:main block\nemit &a\nwarn &e\nkey &b\nemit &b\nwarn &b\nhalt\n'
CHAN_EDGES = [
    b':a data 8 0\n:main block\ncopy +2 &a\ncopy &a +1\ncopy +0 &a\ncopy +3 &a  # c\n:t data 8 "copy +2 &a"\n', b'copy +2', b'copy +2 +3', b'copy +5 +4 copy +1 +2',
    b':a data 8 0\n:main block\ncopy +6 &a\ncopy +12 &a\ncopy + &a\ncopy +a &a\ncopy -2 &a\ncopy ++ &a\ncopy &a[0:4] +4\n',
    b':a data 8 0\n:main block\ncopy +2 ' + HOSTA.encode() + b'\ncopy ' + HOSTA.encode() + b' +1\ncopy &a ' + HOSTA.encode() + b'\n',
    b'pack\n:a data 8 0\n:main block\ncopy +2 &a\nhalt\n', b':a data 8 "+2"\n:main block\ncopy  +2   &a   copy &a\t+1\n',
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


class Reference(unittest.TestCase):
    """The reference (no emulator)."""

    def test_tables_are_current(self):
        """The numbers of the tables in l4c.tw are what l3ctext.x_tables_text makes."""
        src = t.read('l4c.tw')
        a, b = src.index('# --- begin generated\n'), src.index('# --- end generated')
        self.assertEqual(src[a + len('# --- begin generated\n'):b], l3ctext.x_tables_text())

    def test_strings_have_their_width(self):
        """The data of l4c.tw which are strings have exactly the bits of their bytes (emit sends all of them)."""
        n = 0
        for m in re.finditer(r'^:\w+ data (\d+) "((?:[^"\\]|\\.)*)"', t.read('l4c.tw'), re.M):
            self.assertEqual(int(m.group(1)), 8 * len(m.group(2).replace('\\n', '\n').replace('\\0', '\0').replace('\\"', '"')), m.group(0))
            n += 1
        self.assertGreater(n, 20)

    def test_tool_is_in_its_subset(self):
        src = t.read('l4c.tw')
        out, err = l3ctext.encode(src)
        self.assertIsNone(err)
        c = l3ctext.Compiler()
        c.put(l3ctext.prelude())
        l3ctext.run(c, src.encode())
        self.assertLess(c.pos, l3ctext.LIMIT)

    def test_the_text_of_a_long_copy(self):
        """The words of language 3 for a put and a get: the buffer is zeroed, the nonzero nibbles of op, flags, n and the position are copied from the constants
        l4n0..l4n3, the data after the record, the row to SYS; a get reads max(n, 117) bits of the answer."""
        put, get = (l3ctext.host_copy(p, b'&x', 40, [1, 0, 0, 0, 0, 0, 0, 0, 0, 8]) for p in (True, False))
        self.assertEqual(put, 'copy &l4q[0:204] &l4z[0:204]\ncopy &l4q[0:4] &l4n1[4:8]\ncopy &l4q[44:48] &l4n1[12:16]\ncopy &l4q[48:52] &l4n0[8:12]\n'
                              'copy &l4q[76:80] &l4n1[12:16]\ncopy &l4q[112:116] &l4n0[4:8]\ncopy &l4q[204:244] &x\ncopy 1048570 &l4q[0:244]\n')
        self.assertEqual(get, 'copy &l4q[0:204] &l4z[0:204]\ncopy &l4q[0:4] &l4n1[4:8]\ncopy &l4q[28:32] &l4n0[4:8]\ncopy &l4q[44:48] &l4n1[12:16]\n'
                              'copy &l4q[48:52] &l4n0[8:12]\ncopy &l4q[76:80] &l4n1[12:16]\ncopy &l4q[112:116] &l4n0[4:8]\ncopy 1048570 &l4q[0:204]\n'
                              'copy &l4q[204:321] 1048570\ncopy &x &l4q[204:244]\n')
        self.assertEqual(l3ctext.host_copy(False, b"&x", 300, [0]).split("\n")[-3], 'copy &l4q[204:504] 1048570')      # a whole answer: n bits
        for n, v in enumerate(l3ctext.L4N):                  # the constants: the nibble k is the bits 4k.. of the number
            self.assertEqual([v >> 4 * k & 15 for k in range(5)], [5 * n + k if 5 * n + k < 16 else 0 for k in range(5)])

    def test_a_text_without_the_host_is_as_it_is(self):
        """Nothing is changed but the prelude (after the word `pack` if it stands first); the prelude is what l4c_prelude says."""
        for name in ('echo', 'branch', 'arith8', 'loop_digits'):
            src = t.hoisted(name).encode()
            out = l3ctext.l4c(src + b'\0')[0]
            self.assertEqual(out, l3ctext.l4c_prelude().encode() + src + b'\0')
        self.assertEqual(l3ctext.l4c(b'pack\n:a data 1 0\n\0')[0], b'pack' + l3ctext.l4c_prelude().encode() + b'\n:a data 1 0\n\0')
        self.assertEqual(l3ctext.l4c(b'\0')[0], l3ctext.l4c_prelude().encode() + b'\0')
        self.assertTrue(l3ctext.l4c_prelude().encode() in l3ctext.l4c(b'  # a comment\n:a data 1 0\n\0')[0])

    def test_the_pass(self):
        """A put and a get: the words of language 3, the rest as it is (blanks, comments, strings with the word copy in them)."""
        src = (':a data 8 "copy &a 0x1"\n:out data 40 "hello"  # x\n:main block\ncopy &a %s\n  copy %s &out[0:8]\nhalt\n' % (HOSTA, HOSTA))
        out = l3ctext.l4c(src.encode() + b'\0')[0].decode()
        self.assertEqual(out.count('copy &l4q[0:204] &l4z[0:204]\n'), 2)           # the blanks which come before the end of the copy go out as they come
        self.assertIn(':a data 8 "copy &a 0x1"\n:out data 40 "hello"  # x\n:main block\n', out)
        self.assertIn('copy &a &l4q[204:212]\n', out)                      # n is the width of &a; the data of the put is &out[0:8]
        self.assertIn('copy &l4q[204:212] &out[0:8]\n', out)
        self.assertTrue(out.endswith('\nhalt\n\0'), out[-40:])

    def test_the_rest_goes_out_unchanged(self):
        """Two hosts, none, a width which is not known (a table, an array, a name not defined, 2049 bits) or a spoiled operand: `copy a b` as it was."""
        for src, tail in ((':main block\ncopy 0x1 0x1\n', 'copy 0x1 0x1\n'), (':a data 8 0\n:main block\ncopy &a &a\n', 'copy &a &a\n'),
                          (':t table 1 8 1 2\n:main block\ncopy &t %s\n' % HOSTA, 'copy &t %s\n' % HOSTA),
                          (':main block\ncopy &q %s\n' % HOSTA, 'copy &q %s\n' % HOSTA), (':c data 2049 0\n:main block\ncopy &c %s\n' % HOSTA, 'copy &c %s\n' % HOSTA),
                          (':c data 8 0\n:main block\ncopy &c[3:3] %s\n' % HOSTA, 'copy &c[3:3] %s\n' % HOSTA)):
            out = l3ctext.l4c(src.encode() + b'\0')[0].decode()
            self.assertTrue(out.endswith(tail + '\0'), (src, out[-50:]))
            if '0x1' in src.split('\n')[-2]:
                self.assertIsNotNone(l3ctext.encode(out[:-1])[1], src)           # and l3c does not take it (a number which is not a channel)

    def test_channel_from_the_end(self):
        """`+k` (k 0..5) in `copy` is the channel S + k: l4c gives the number l3c reads (+1 stdin, +2 stdout, +3 stderr, +0 SYS), the rest of the operands as they are;
        the text with the forms is, after l3c, the text with emit warn key (the same rows)."""
        for k in range(6):
            out = l3ctext.l4c(b':a data 8 0\n:main block\ncopy +%d &a\ncopy &a +%d\n\0' % (k, k))[0]
            self.assertTrue(out.endswith(b'copy %d &a\ncopy &a %d\n\0' % (l3ctext.SYSC + k, l3ctext.SYSC + k)), out)
        for tok in (b'+6', b'+9', b'+', b'+12', b'+a', b'-2', b'++', b'2', b'+0x', b'&a'):
            out = l3ctext.l4c(b':a data 8 0\n:main block\ncopy ' + tok + b' &a\n\0')[0]
            self.assertTrue(out.endswith(b'copy ' + tok + b' &a\n\0'), (tok, out))
            if tok[:1] in b'+-':
                self.assertIsNotNone(l3ctext.encode(out[:-1])[1], tok)                  # l3c does not take such a number
        out = l3ctext.l4c(b':t data 8 "copy +2 &a" # copy +2 &a\n\0')[0]
        self.assertTrue(out.endswith(b':t data 8 "copy +2 &a" # copy +2 &a\n\0'), out)                 # a string and a comment are not changed
        forms = l3ctext.encode(l3ctext.l4c(CHAN_FORMS.encode() + b'\0')[0][:-1])
        words = l3ctext.encode(CHAN_WORDS)
        self.assertEqual((forms[1], words[1]), (None, None))
        self.assertTrue(forms[0] and forms[0].count(b'\n') > 10)

    def test_the_text_of_a_far_copy(self):
        """A far get and put (26.4): the record of 6 bytes in l4q (op, the number of the byte = the position / 8, dat), a request per byte, the get reads each answer after a
        goto (a label l4f<k> of its own), the number of the byte goes up by the nibbles which change; the labels go on from copy to copy."""
        out = l3ctext.l4c((':x data 16 0\n:main block\ncopy &x %s\ncopy %s &x[8:16]\ncopy &x[8:16] %s\nhalt\n' % (farad(8 * 255), farad(8 * 3), farad(8 * 3))).encode() + b'\0')[0].decode()
        whole, out = out, out[out.index(':main block\n') + 12:]
        self.assertEqual(out, 'copy &l4q[0:204] &l4z[0:204]\ncopy &l4q[0:4] &l4n0[4:8]\ncopy &l4q[8:12] &l4n3[0:4]\ncopy &l4q[12:16] &l4n3[0:4]\n'
                              'emit &l4q[0:48]\ngoto &l4f0\n:l4f0 block\nkey &x[0:8]\ncopy &l4q[8:12] &l4n0[0:4]\ncopy &l4q[12:16] &l4n0[0:4]\n'
                              'copy &l4q[16:20] &l4n0[4:8]\nemit &l4q[0:48]\n'
                              'goto &l4f1\n:l4f1 block\nkey &x[8:16]\n\n'
                              'copy &l4q[0:204] &l4z[0:204]\ncopy &l4q[0:4] &l4n0[8:12]\ncopy &l4q[8:12] &l4n0[12:16]\ncopy &l4q[40:48] &x[8:16]\nemit &l4q[0:48]\n\n'
                              'copy &l4q[0:204] &l4z[0:204]\ncopy &l4q[0:4] &l4n0[4:8]\ncopy &l4q[8:12] &l4n0[12:16]\nemit &l4q[0:48]\ngoto &l4f2\n:l4f2 block\n'
                              'key &x[8:16]\n\nhalt\n\0')
        self.assertIsNone(l3ctext.encode(whole[:-1])[1])
        for pack in ('', 'pack\n'):
            for src in FAR_EDGES[:4]:
                self.assertIsNone(l3ctext.encode(pack + l3ctext.l4c(src + b'\0')[0][:-1].decode('latin-1'))[1], src)

    def test_a_far_copy_which_is_not_as_told_is_as_it_was(self):
        """The link which is not 0, a position which is not a multiple of 8 or is 2^32 bits and over, a width which is not 8..64 whole bytes or is not known, two far
        addresses, far and host, lo of 9900 and more, no more labels: `copy a b` as it was (l3c does not take it); 0x2 with other digits is a host address, as before."""
        pre = ':x data 64 0\n:b data 4 0\n:w data 72 0\n:t table 1 8 1 2\n:main block\n'
        for pair in ('&x %s' % farad(0, 1), '%s &x' % farad(12), '&x %s' % farad(1 << 32), '&b %s' % FAR, '%s &w' % FAR, '&t %s' % FAR, '&q %s' % FAR, '&x[3] %s' % FAR,
                     '&x[0:12] %s' % FAR, '%s %s' % (FAR, FAR), '%s %s' % (FAR, HOSTA), '%s &x[0:0]' % FAR):
            out = l3ctext.l4c((pre + 'copy %s\n' % pair).encode() + b'\0')[0]
            self.assertTrue(out.endswith(('copy %s\n' % pair).encode() + b'\0'), (pair, out[-50:]))
            self.assertIsNotNone(l3ctext.encode(out[:-1])[1], pair)
        out = l3ctext.l4c((':y data 9000 0\n:main block\ncopy &y[9899:9907] %s\ncopy &y[9900:9908] %s\n' % (FAR, FAR)).encode() + b'\0')[0]
        self.assertIn(b'key &y[9899:9907]', out)
        self.assertTrue(out.endswith(b'copy &y[9900:9908] %s\n\0' % FAR.encode()), out[-60:])
        for d in ('0' * 31, '0' * 33):                         # 0x2 and another number of digits: a host address (the low 32 digits are the position)
            out = l3ctext.l4c((':x data 8 0\n:main block\ncopy &x 0x2%s\n' % d).encode() + b'\0')[0]
            self.assertIn(b'copy 1048570 &l4q[0:204]', out)
        out = l3ctext.l4c((':x data 64 0\n:main block\n' + 'copy &x %s\n' % FAR * 257).encode() + b'\0')[0]       # 257 gets of 8 bytes: 256 take 2048 labels, the last stays
        self.assertEqual((out.count(b'goto &l4f'), out.count(b'\ncopy &x 0x2')), (2048, 1))

    def test_chain_of_references(self):
        """The text of language 3 which the pass makes is a text l3c takes."""
        for name, src in PROGRAMS.items():
            with self.subTest(name):
                out = l3ctext.l4c(src.encode() + b'\0')[0]
                self.assertNotIn(b'0x1', out[out.index(b':main'):])
                self.assertIsNone(l3ctext.encode(out[:-1])[1])
                self.assertIsNone(l3ctext.encode(b'pack\n' + out[:-1])[1])

    def test_cli(self):
        import subprocess
        root = os.path.dirname(os.path.dirname(HERE))
        src = ':a data 8 0\n:main block\ncopy &a %s\nhalt\n' % HOSTA
        e = subprocess.run([sys.executable, '-B', 'tower/l3ctext.py', '-x'], input=src.encode() + b'\0', cwd=root, check=False, capture_output=True, timeout=120)
        self.assertEqual((e.returncode, e.stdout), (0, l3ctext.l4c(src.encode() + b'\0')[0]))


class Tool(unittest.TestCase):
    """The pass on the chain against the reference."""

    def check(self, src, limit=LIMIT):
        r = l4c(src, limit)
        self.assertEqual((r.rc, r.out), (0, l3ctext.l4c(src + b'\0')[0]), src[:100])
        return r

    def test_tool_image(self):
        st = pass_tool()
        self.assertEqual((st['A'], st['P']), (20, 2))
        self.assertLess(len(st['image']) * 8, 1 << 20)

    def test_programs(self):
        for name, src in PROGRAMS.items():
            with self.subTest(name):
                self.assertIn(b'0x1', src.encode())
                self.check(src.encode())
        self.check(t.hoisted('echo').encode())                         # no address of the host: the text as it is
        self.check(b'pack\n' + readme_example().encode())

    def test_channel_from_the_end(self):
        """The forms `+k` of the channels: the same bytes as the reference (also in the pack mode, in a string, in a comment, with the host, a form spoiled)."""
        for src in CHAN_EDGES:
            with self.subTest(src):
                self.check(src)
        self.check(CHAN_FORMS.encode())
        r = self.check(b':a data 8 0\n:main block\ncopy +2 &a\ncopy &a +1\ncopy +3 &a\ncopy +4 &a\ncopy +5 &a\ncopy +0 &a\n')
        self.assertTrue(r.out.endswith(b'copy 1048572 &a\ncopy &a 1048571\ncopy 1048573 &a\ncopy 1048574 &a\ncopy 1048575 &a\ncopy 1048570 &a\n\0'), r.out)

    def test_far_copy(self):
        """The far copies (26.4): the same bytes as the reference for the texts which are translated and for those which are not."""
        for src in FAR_EDGES:
            with self.subTest(src):
                self.check(src)
        self.check(PROGRAMS['rw'].encode() + b'\n' + FAR_EDGES[0])                  # the host and the far one in a text; the labels go on after the gets of the text before it
        out = self.check(b':x data 64 0\n:main block\n' + (b'copy &x ' + FAR.encode() + b'\n') * 257, limit=10 ** 9).out      # the labels end at 2048: the 257th is not made
        self.assertEqual((out.count(b'goto &l4f'), out.count(b'\ncopy &x 0x2')), (2048, 1))

    def test_far_mutations(self):
        """Texts with far addresses spoiled at random (a character replaced, dropped, doubled): the same bytes."""
        rng = random.Random(2644)
        for _ in range(30):
            b = bytearray(rng.choice(FAR_EDGES[:6]))
            for _ in range(rng.choice((1, 2, 3))):
                i = rng.randrange(len(b))
                m = rng.randrange(3)
                if m == 0:
                    b[i] = rng.choice(b'0123456789abcdefx&[]:# "\n\\')
                elif m == 1:
                    del b[i]
                else:
                    b.insert(i, rng.choice(b'02x&[]: "\n\\#'))
            self.check(bytes(b).replace(b'\0', b' '))

    def test_edges(self):
        for src in EDGES:
            with self.subTest(src):
                self.check(src)

    @staticmethod
    def name_hash(name):
        """The hash of a name in l4c.tw (mkname): h = 8h + c modulo 2^12 over the bytes; the tree of the names is keyed by it."""
        h = 0
        for c in name.encode():
            h = (h * 8 + c) & 4095
        return h

    @staticmethod
    def names_program(names, widths):
        """The data `names` of the widths and two copies with the host for each (the whole name, a part of it)."""
        a = host(1, 8)
        return (''.join(':%s data %d 0\n' % (n, w) for n, w in zip(names, widths, strict=True)) + ':main block\n'
                + ''.join('copy &%s %s\ncopy %s &%s[1:3]\n' % (n, a, a, n) for n in names) + 'halt\n').encode()

    def test_names_with_the_same_hash(self):
        """The names of data are a tree of tables by the hash of the name (12 bits); names with the same hash are the versions of one key (the name is compared
        with each); a repeated name keeps its first width: the same bytes as the reference."""
        by = {}
        for a in 'abcdefghijklmnopqrstuvwxyz':
            for b in 'abcdefghijklmnopqrstuvwxyz':
                for c in 'abcdefghijkl':
                    by.setdefault(self.name_hash(a + b + c), []).append(a + b + c)
        groups = [v for v in by.values() if len(v) >= 4][:6]
        self.assertEqual(len(groups), 6)
        names = [n for g in groups for n in g[:4]]
        self.check(self.names_program(names, list(range(5, 5 + len(names)))))
        self.check(self.names_program(names + names[::-1], list(range(5, 5 + 2 * len(names)))))
        rng = random.Random(2531)
        for _ in range(4):
            pool = [n for g in groups for n in g] + [''.join(rng.choice('abxyz_09') for _ in range(rng.randrange(1, 15))) for _ in range(10)]
            names = [n for n in rng.sample(pool, 30) if n[0] not in '0123456789']
            self.check(self.names_program(names, [rng.randrange(1, 300) for _ in names]))

    def test_table_of_names_is_full(self):
        """63 names are kept (cells 1..63); a name past them is not kept, its copy goes out unchanged (as for a name which is not known)."""
        names = ['n%d' % i for i in range(70)]
        out = l4c(self.names_program(names, [8] * 70)).out
        self.assertEqual(out.count(b'copy 1048570 &l4q[0:204]\n'), 63)
        self.assertEqual(out.count(b'copy &n63 0x'), 1)
        self.assertEqual(out.count(b'copy &n69 0x'), 1)
        self.assertEqual(out.count(b'copy &n62 0x'), 0)

    def test_mutations(self):
        """Texts spoiled at random (a character replaced, dropped, doubled): the same bytes."""
        rng = random.Random(2317)
        bases = [EDGES[9], EDGES[10], EDGES[12], PROGRAMS['rw'].encode()]
        for _ in range(30):
            b = bytearray(rng.choice(bases))
            for _ in range(rng.choice((1, 2, 3))):
                i = rng.randrange(len(b))
                m = rng.randrange(3)
                if m == 0:
                    b[i] = rng.choice(b'0123456789abcdefx&[]:# "\n\\')
                elif m == 1:
                    del b[i]
                else:
                    b.insert(i, rng.choice(b'0x&[]: "\n\\#'))
            self.check(bytes(b).replace(b'\0', b' '))


class Programs(unittest.TestCase):
    """The images of the chain (l4c, l3c, l2l, seed) do the long copies as the images of the Python compiler: the same output and the same host file."""

    def both(self, src, data=FILE, pack=False):
        img, P = l5.chain_image(('pack\n' if pack else '') + src, True)
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
            forms, P = l5.chain_image(pack + CHAN_FORMS, True)
            words, P2 = l5.chain_image(pack + CHAN_WORDS, True)
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

    def test_the_tools_of_the_chain(self):
        """The tools themselves: l4c (the image of the references) and l3c (the image of Python) make the text, l2l and the seed the image."""
        src = PROGRAMS['rw']
        a = l4c(src.encode())
        want = l3ctext.l4c(src.encode() + b'\0')[0]
        self.assertEqual(a.out, want)
        b = t.l3c(a.out[:-1])
        self.assertEqual(b.out, l3ctext.encode(want[:-1])[0])
        img = t.image_of(b.out)
        self.assertEqual(img, l5.chain_image(src, True)[0])


if __name__ == '__main__':
    unittest.main()
