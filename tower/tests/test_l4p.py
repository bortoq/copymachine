"""Tests of language 4 on the chain (23.17): `long!` and `long@`, the long copy to and from the host. l3c has no room for the whole word (98 % of
A = 20): it checks the two arguments and writes a placeholder (the line `long` and a layer with four numbers, ten layers of room); the pass
`programs/l4p.tw` puts the 11 layers there: the request of the SYS channel, built of copies (the numbers op, direction and length are 4 bits
copied from the table add4), the row to SYS, for `long@` the row which reads the answer. The chain is: text of language 3 -> l3c -> l4p ->
[l3p] -> l2l -> seed -> the image. Here: the reference (the layers, the errors), the tool l4p against it byte for byte (also on spoiled texts), the
images of the chain against the images of the Python compiler (the output and the host files are the same), the example of tower/README.md
(section 3.5). The long runs (the tools made by the chain itself) are in long_l3c.py.
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


def pass_tool():
    """The image of l4p.tw made by the references of the chain (l3c, l2l, the seed; the long test runs the tools themselves)."""
    if not _PASS:
        img, P = l5.chain_image(t.read('l4p.tw'))
        _PASS.update(image=img, A=20, P=P)
    return _PASS


def l4p(l2, limit=LIMIT):
    st = pass_tool()
    return run(st['image'], st['A'], st['P'], checked=True, limit=limit, stdin=l2)


def readme_example():
    """The program of tower/README.md, section 3.5."""
    with open(os.path.join(HERE, '..', 'README.md'), encoding='utf-8') as h:
        doc = h.read()
    return re.search(r'### 3\.5\..*?```tw\n(.*?)```', doc, re.S).group(1)


# the position of the bit 8 of the area 1 (the file): 2^96 + 8, made of two bits
HEAD = ':pos data 128 0\n:one data 1 1\n:main block\ncopy &pos[96:97] &one\n'

PROGRAMS = {
    # put 40 bits at the bit 8, get them back (less than 117 bits: through the buffer of the answer)
    'rw': ':pos data 128 0\n:one data 1 1\n:out data 40 "hello"\n:got data 40 "\\0\\0\\0\\0\\0"\n:main block\ncopy &pos[96:97] &one\ncopy &pos[3:4] &one\n'
          'long! &pos &out\nlong@ &pos &got\nemit &got\nhalt\n',
    # three reads of 8 bytes, the position moved by 64 with add (128 bits)
    'cat': ':pos data 128 0\n:one data 1 1\n:step data 128 0\n:pos2 data 129 0\n:buf data 64 0\n:main block\ncopy &pos[96:97] &one\ncopy &step[6:7] &one\n'
           'long@ &pos &buf\nemit &buf\nadd &pos &step &pos2\ncopy &pos &pos2[0:128]\nlong@ &pos &buf\nemit &buf\nadd &pos &step &pos2\n'
           'copy &pos &pos2[0:128]\nlong@ &pos &buf\nemit &buf\nhalt\n',
    # 200 bits (a whole answer is read into the data): put, get; 117 and 116 bits (the edge of the buffer), 1 bit, 5 bits at the bit 3
    'sizes': ':pos data 128 0\n:one data 1 1\n:x data 200 "abcdefghijklmnopqrstuvwxy"\n:w data 200 0\n:v data 120 0\n:u data 8 0\n:main block\n'
             'copy &pos[96:97] &one\ncopy &pos[1:2] &one\nlong! &pos &x\nlong@ &pos &w\nemit &w\nlong@ &pos &v[0:117]\nemit &v[0:112]\n'
             'long@ &pos &v[0:116]\nemit &v[0:112]\nlong! &pos &x[0:1]\nlong@ &pos &u[0:5]\nemit &u\ncopy &pos[0:1] &one\ncopy &pos[2:3] &one\n'
             'long! &pos &x[8:13]\nlong@ &pos &u\nemit &u\nhalt\n',
    # outside the file (past its end, far above it, an area which is not there), the clock: reads give zeros, writes are lost, the clock goes on
    'outside': ':pos data 128 0\n:one data 1 1\n:x data 16 "ab"\n:z data 16 "\\0\\0"\n:main block\ncopy &pos[96:97] &one\ncopy &pos[20:21] &one\nlong! &pos &x\n'
               'long@ &pos &z\nemit &z\ncopy &pos[100:101] &one\nlong@ &pos &z\nemit &z\nhalt\n',
    # the clock (the area 0): two reads, the second is not less than the first
    'clock': (':pos data 128 0\n:t1 data 64 0\n:t2 data 64 0\n:c data 17 0\n:y data 8 "Y"\n:n data 8 "N"\n:main block\nlong@ &pos &t1\n'
              'long@ &pos &t2\nlt &t2 &t1 &c\nif &c[16] &no &yes\n:yes block\nemit &y\nhalt\n:no block\nemit &n\nhalt\n'),
}


class Reference(unittest.TestCase):
    """The reference (no emulator)."""

    def test_tables_are_current(self):
        """The numbers of the tables in l4p.tw are what l3ctext.x_tables_text makes."""
        src = t.read('l4p.tw')
        a, b = src.index('# --- begin generated\n'), src.index('# --- end generated')
        self.assertEqual(src[a + len('# --- begin generated\n'):b], l3ctext.x_tables_text())

    def test_tool_is_in_its_subset(self):
        src = t.read('l4p.tw')
        out, err = l3ctext.encode(src)
        self.assertIsNone(err)
        c = l3ctext.Compiler()
        c.put(l3ctext.prelude())
        l3ctext.run(c, src.encode())
        self.assertLess(c.pos, l3ctext.LIMIT // 4)

    def test_the_request(self):
        """The layers of a put and of a get: the nibbles of op (6), direction, n; the position; the data or the answer; the jumps."""
        n, p, d, first = 0x2a5, 0xe1, 0x1e0, 0x300
        put = l3ctext.long_text(True, n, p, d, first).split('\n')
        get = l3ctext.long_text(False, n, p, d, first).split('\n')
        jumps = ['c a0 0 %x' % (first + 160 * (j + 1)) for j in range(11)]
        for lines in (put, get):
            self.assertEqual([x for x in lines if x.startswith('c a0 0')], jumps)
            self.assertEqual(lines[:2], ['c 4 fd200 &ta+30', jumps[0]])
            self.assertEqual(lines[-1], '')
        self.assertEqual(put[2:4], ['c 4 fd21c &ta+0', jumps[1]])
        self.assertEqual(get[2:4], ['c 4 fd21c &ta+8', jumps[1]])
        self.assertEqual([x for x in put if x.startswith('c 4 ')][2:], ['c 4 fd22c &ta+28', 'c 4 fd230 &ta+50', 'c 4 fd234 &ta+10',
                                                                       'c 4 fd238 &ta+0', 'c 4 fd23c &ta+0'])         # 8 times 5, a, 2, 0, 0
        self.assertEqual(put[14:16], ['c 80 fd24c e1', jumps[7]])
        self.assertEqual(put[16:], ['c 2a5 fd2cc 1e0', jumps[8], 'd 14 ffffa', 'd 14 ffffa', 'd 14 fd200', 'd 14 %x' % (l3ctext.QB + 204 + n), jumps[9],
                                    'z 50', jumps[10], ''])
        self.assertEqual(get[16:], ['d 14 ffffa', 'd 14 ffffa', 'd 14 fd200', 'd 14 fd2cc', jumps[8], 'd 14 fd2cc', 'd 14 %x' % (l3ctext.QB + 204 + n),
                                    'd 14 ffffa', 'd 14 ffffa', jumps[9], 'c 2a5 1e0 fd2cc', jumps[10], ''])
        # a read of less than 117 bits reads 117
        short = l3ctext.long_text(False, 8, p, d, first)
        self.assertIn('d 14 %x\nd 14 %x\nd 14 ffffa\nd 14 ffffa\n' % (l3ctext.QB + 204, l3ctext.QB + 204 + 117), short)
        self.assertEqual([x.count('\n') for x in (l3ctext.long_text(True, 5, p, d, first), l3ctext.long_text(False, 5, p, d, first))], [25, 28])

    def test_the_pass(self):
        """The text goes out as it is but for the placeholders; no placeholder, no change; the position of the next layer is 11 layers on."""
        for name in ('echo', 'branch', 'arith8'):
            l2 = l3ctext.encode(t.hoisted(name))[0]
            self.assertEqual(l3ctext.long_pass(l2), (l2, None))
        src = HEAD + 'long! &pos &pos\ncopy &pos[0:8] &pos[8:16]\nhalt\n'
        l2, err = l3ctext.encode(src)
        self.assertIsNone(err)
        out, perr = l3ctext.long_pass(l2)
        self.assertIsNone(perr)
        a, b = l2.decode(), out.decode()
        self.assertEqual(a.count('long\n'), 1)
        self.assertNotIn('long', b)
        i = a.index('long\n')
        first = int(re.search(r'd 14 [0-9a-f]+\nd 14 [0-9a-f]+\nd 14 [0-9a-f]+\nd 14 ([0-9a-f]+)\n', a[i:]).group(1), 16)
        j = b.index('c a0 0 %x\n' % (first + 160 * 11))
        self.assertTrue(re.match(r'c a0 0 %x\nc 8 [0-9a-f]+ [0-9a-f]+\nc a0 0 %x\n' % (first + 160 * 11, first + 160 * 12), b[j:]))

    def test_errors(self):
        """A placeholder cut or wrong: the report, the text before it stays."""
        head = 'ab\nc a0 0 0\n'
        for tail in ('long\n', 'long\nd 14 1\nd 14 2\nd 14 3\nd 14 4\n', 'long\nd 14 1\nd 14 2\nd 14 zz\nd 14 4\nc a0 0 5\n',
                     'long\nd 14 1\nd 14 2\nd 14 3\nd 14 4\nc a0 0 5', 'long\nd 14 A\nd 14 2\nd 14 3\nd 14 4\nc a0 0 5\n', 'long\nd 14 1\t\n'):
            out, err = l3ctext.long_pass((head + tail).encode() + b'\0')
            self.assertEqual((err, out), ('bad', head.encode()), tail)
        good = 'long\nd 14 1\nd 14 2 \nd 14 3\n d 14 04\n  c a0 0 0b\n'
        out, err = l3ctext.long_pass((head + good + 'x\0').encode())
        self.assertEqual(err, None)
        self.assertTrue(out.endswith(b'x\0'))
        self.assertEqual(l3ctext.long_pass(b'longer\nlon\nlong\0'), (b'longer\nlon\nlong\0', None))      # not lines of a placeholder

    def test_cli(self):
        import subprocess
        root = os.path.dirname(os.path.dirname(HERE))
        l2 = l3ctext.encode(HEAD + 'long@ &pos &pos\nhalt\n')[0]
        e = subprocess.run([sys.executable, '-B', 'tower/l3ctext.py', '-x'], input=l2, cwd=root, check=False, capture_output=True, timeout=120)
        self.assertEqual((e.returncode, e.stdout), (0, l3ctext.long_pass(l2)[0]))
        e = subprocess.run([sys.executable, '-B', 'tower/l3ctext.py', '-x'], input=b'long\n\0', cwd=root, check=False, capture_output=True, timeout=120)
        self.assertEqual((e.returncode, e.stderr), (1, b'l4p: bad text\n'))


class Tool(unittest.TestCase):
    """The pass on the chain against the reference."""

    def check(self, l2):
        r = l4p(l2)
        want, err = l3ctext.long_pass(l2)
        self.assertEqual(r.out, want, l2[-100:])
        self.assertEqual('l4p: ' in r.err, err is not None, (l2[-100:], r.err))
        if err:
            self.assertIn(l3ctext.LPMESSAGES[err], r.err)
        else:
            self.assertEqual(r.rc, 0)
        return r

    def test_tool_image(self):
        st = pass_tool()
        self.assertEqual((st['A'], st['P']), (20, 2))
        self.assertLess(len(st['image']) * 8, 1 << 20)

    def test_programs(self):
        for name, src in PROGRAMS.items():
            with self.subTest(name):
                l2, err = l3ctext.encode(src)
                self.assertIsNone(err)
                self.assertGreater(l2.count(b'long\n'), 0)
                self.check(l2)
        self.check(l3ctext.encode(t.hoisted('echo'))[0])           # no placeholder: the text as it is
        self.check(l3ctext.encode('pack\n' + readme_example())[0])

    def test_errors_and_edges(self):
        for l2 in (b'\0', b'long\0', b'long\nd 14 1\n\0', b'lon\0', b'lonf\nlong\nd 14 1\nd 14 2\nd 14 3\nd 14 400\nc a0 0 560\n\0',
                   b'long\nd 14 1\nd 14 2\nd 14 3\nd 14 400\nc a0 0 560\n\0', b'long\nd 14 80001\nd 14 e1\nd 14 1e0\nd 14 400\nc a0 0 560\nz 50\n\0',
                   b'long\nd 14 1\nd 14 zz\nd 14 3\nd 14 400\nc a0 0 560\n\0', b'ab\nlong\nd 14 1\nd 14 2 \nd 14 3\n d 14 04\n  c a0 0 0b\nlong\n\0',
                   b'long\nd 14 1\nd 14 2\nd 14 3\nd 14 400\nc a0 0\0', b'x long\nlong \nlong\nlong\n\0', b'd 14 A\nlong\nd 14 B\nlong\0'):
            with self.subTest(l2):
                self.check(l2)

    def test_mutations(self):
        """Texts of language 2 with placeholders spoiled at random (a character replaced, dropped, doubled, the text cut): the same bytes and reports."""
        rng = random.Random(2317)
        bases = [l3ctext.encode(PROGRAMS['rw'])[0].decode('latin-1'), l3ctext.encode(PROGRAMS['sizes'])[0].decode('latin-1')]
        for _ in range(30):
            s = rng.choice(bases)
            marks = [m.start() for m in re.finditer('long\n', s)]
            for _ in range(rng.choice((1, 1, 2))):
                i = rng.choice(marks) + rng.randrange(40)
                m = rng.randrange(4)
                if m == 0:
                    s = s[:i] + rng.choice('0123456789abcdefg xl\n#') + s[i + 1:]
                elif m == 1:
                    s = s[:i] + s[i + 1:]
                elif m == 2:
                    s = s[:i] + s[i] + s[i:]
                else:
                    s = s[:i] + '\0'
                    break
            if s.endswith('\0'):
                s = s[:-1]
            self.check(s.replace('\0', '').encode('latin-1') + b'\0')


class Programs(unittest.TestCase):
    """The images of the chain (l3c, l4p, l2l, seed) do the long copies as the images of the Python compiler: the same output and the same host file."""

    def both(self, src, data=FILE, pack=False):
        img, P = l5.chain_image(('pack\n' if pack else '') + src)
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
                rc, out, host, ticks = self.both(src)
                self.assertTrue(out)
                if name == 'rw':
                    self.assertEqual((out, host[:6]), (b'hello', bytes([FILE[0]]) + b'hello'))
                elif name == 'cat':
                    self.assertEqual(out, FILE[:24])
                elif name == 'clock':
                    self.assertEqual(out, b'Y')

    def test_packed_programs(self):
        """The same in pack mode (l3c, l4p, l3p): the output and the host file as the Python images, in fewer ticks than the serial."""
        for name in ('rw', 'sizes', 'outside'):
            with self.subTest(name):
                a = self.both(PROGRAMS[name])
                b = self.both(PROGRAMS[name], pack=True)
                self.assertEqual(a[:3], b[:3])
                self.assertLess(b[3], a[3])

    def test_readme_example(self):
        """The example of the README: `hello` is written at the bit 8 of the file and read back; the pack mode gives the same, in fewer ticks."""
        src = readme_example()
        rc, out, host, ticks = self.both(src)
        self.assertEqual((out, host[:6]), (b'hello', bytes([FILE[0]]) + b'hello'))
        self.assertEqual(host[6:], FILE[6:])
        _, out2, host2, ticks2 = self.both(src, pack=True)
        self.assertEqual((out2, host2), (out, host))
        self.assertLess(ticks2, ticks)

    def test_the_tools_of_the_chain(self):
        """The tools themselves: l3c (the image of Python) and l4p (made by the references) make the text, l2l and the seed the image."""
        src = PROGRAMS['rw']
        a = t.l3c(src)
        b = l4p(a.out)
        want, err = l3ctext.encode(src)
        self.assertEqual(a.out, want)
        self.assertEqual(b.out, l3ctext.long_pass(want)[0])
        img = t.image_of(b.out)
        self.assertEqual(img, l5.chain_image(src)[0])


if __name__ == '__main__':
    unittest.main()
