"""Long tests of the compiler of language 3 (23.9, part 2), `make check-tower-long` (not in check-fast): the tools of the chain are
compiled by l3c (text of language 3 -> l3c -> l2l -> seed -> image) and the images work. The chain tool l3c agrees with the Python reference
(l3ctext) on the texts of seed, l2c and l2l (hoisted: data outside the blocks); the seed made by the chain turns seed.l1 into the
image of the seed (the fixed point of 23.7, now through the serial layout); the label tool l2l made by the chain turns hello_names.l2
into what the Python reference gives; 300 texts spoiled at random give the same bytes and reports in the chain and in Python; and
the FIXED POINT (23.9, part 3): l3c compiles its own text. The seed and the label tool are built on the emulator from seed.l1 and
l2l.l1 (no Python compiler on that path); the text of language 1 of l3c (programs/l3c.l1, made once with the Python image of the tool
and the chain) gives the image of l3c, and that image (l3c -> l2l -> seed) builds from l3c.tw the same text l3c.l1 and the same image, byte for
byte; the text of language 2 which it writes is what the reference gives, and so is the Python image. The names of l3c fill its table (1020 places) and the 1021st is bad label.
23.10: the same with the planner (pack mode: `pack` first, the pass programs/l3p.tw between l3c and l2l): the fixed point with the planner is
at the end (class PackedFixedPoint).
23.17: language 4 on the chain (class LongWords): the pass programs/l4p.tw made by the chain, and the programs with `long!` and `long@` made by
l3c -> l4p -> [l3p] -> l2l -> seed, step by step what the references give; the images work as the images of the Python compiler (the same output and host files).
Run: make check-tower-long  or  python3 -B tower/tests/long_l3c.py"""
import os
import random
import re
import shutil
import sys
import tempfile
import time

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import l1text
import l2ltext
import l3ctext
import l5
import test_l3c as t
import test_l4p as t4
import text
from common import run

BIG = 300 * 10 ** 6
SHARED = {}         # the seed, the label tool and the serial l3c made without Python (the classes FixedPoint and PackedFixedPoint use them)
REPORT = []         # (step, ticks, seconds) of the fixed point, printed at the end of the run (the numbers of docs/measurements/tower.md)


def step(name, image, A, P, stdin):
    """One run on the checked emulator: the output; the ticks and the seconds go to REPORT."""
    t0 = time.time()
    r = run(image, A, P, checked=True, limit=BIG, stdin=stdin)
    assert r.rc == 0 and r.ticks < BIG, (name, r.err)
    REPORT.append((name, r.ticks, time.time() - t0))
    return r.out


def tools():
    """The seed (the Python encoder, once), the label tool (the seed on l2l.l1) and l3c (the seed on l3c.l1: serial, A = 20, P = 2): no Python compiler."""
    if not SHARED:
        t.setUpModule()
        seed_st, l2l_st = t.compiled('seed').stats, t.compiled('l2l').stats
        seed = l1text.encode(t.read('seed.l1', 'rb') + b'\0')[0]
        assert seed == seed_st['image']
        l2l = step('seed on l2l.l1', seed, seed_st['A'], seed_st['P'], t.read('l2l.l1', 'rb') + b'\0')
        assert l2l == l2l_st['image']
        l3c = step('seed on l3c.l1', seed, seed_st['A'], seed_st['P'], t.read('l3c.l1', 'rb') + b'\0')
        SHARED.update(seed=(seed, seed_st['A'], seed_st['P']), l2l=(l2l, l2l_st['A'], l2l_st['P']), l3c=(l3c, 20, 2))
    return SHARED


def chain(tag, l3c, src, planner=None, longp=None):
    """text of language 3 -> l3c -> (l4p) -> (l3p) -> l2l (the text twice) -> seed -> the image: returns the text of language 2 (after the passes), of language 1,
    the image. l3c, longp, planner: (image, A, P)."""
    tl = tools()
    l2 = step(tag + ' l3c', l3c[0], l3c[1], l3c[2], src + b'\0')
    if longp:
        l2 = step(tag + ' l4p', longp[0], longp[1], longp[2], l2)
    if planner:
        l2 = step(tag + ' l3p', planner[0], planner[1], planner[2], l2)
    l1 = step(tag + ' l2l', tl['l2l'][0], tl['l2l'][1], tl['l2l'][2], l2 + l2)
    return l2, l1, step(tag + ' seed', tl['seed'][0], tl['seed'][1], tl['seed'][2], l1)


def serial_pass(name):
    """The pass programs/<name>.tw (l3p, l4p) made by the serial chain without Python (cached): the text of language 2, of language 1, the image (A = 20, P = 2)."""
    if name not in SHARED:
        src = t.read(name + '.tw', 'rb')
        l2, l1, img = chain(name + ' (serial chain)', tools()['l3c'], src)
        assert l2 == l3ctext.encode(src)[0] and l1 == l3ctext.language1(src)[0] + b'\0'
        SHARED[name] = (l2, l1, (img, 20, 2))
    return SHARED[name]


class Long(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t.setUpModule()
        cls.tool = t.tool()
        cls.l2l = t.compiled('l2l').stats
        cls.seed = t.compiled('seed').stats
        cls.made = {}

    def make(self, name):
        """The image of a tool made by the chain from its text of language 3 (cached)."""
        if name not in self.made:
            r = t.l3c(t.hoisted(name), limit=BIG)
            self.assertEqual(r.rc, 0, r.err)
            self.assertEqual(r.out, l3ctext.encode(t.hoisted(name))[0])
            a = run(self.l2l['image'], self.l2l['A'], self.l2l['P'], checked=True, limit=BIG, stdin=r.out + r.out)
            self.assertEqual(a.rc, 0, a.err)
            b = run(self.seed['image'], self.seed['A'], self.seed['P'], checked=True, limit=BIG, stdin=a.out)
            self.assertEqual(b.rc, 0, b.err)
            self.assertEqual(b.out, t.image_of(r.out))
            self.made[name] = b.out
        return self.made[name]

    def test_texts_of_the_tools(self):
        """l3c and the reference agree on seed.tw, l2c.tw and l2l.tw (the sizes of the layers are told in docs/measurements/tower.md)."""
        for name in ('seed', 'l2c', 'l2l'):
            with self.subTest(name):
                src = t.hoisted(name)
                r = t.l3c(src, limit=BIG)
                want, err = l3ctext.encode(src)
                self.assertIsNone(err)
                self.assertEqual((r.rc, r.out), (0, want))

    def test_seed_made_by_the_chain(self):
        """The seed compiled by l3c (serial layout) turns seed.l1 into the image of the seed: the same bytes as the seed of 23.7."""
        img = self.make('seed')
        src = t.read('seed.l1', 'rb') + b'\0'
        r = run(img, 20, 2, checked=True, limit=BIG, stdin=src)
        self.assertEqual(r.rc, 0, r.err)
        self.assertEqual(r.out, self.seed['image'])
        self.assertEqual(r.out, l1text.encode(src)[0])

    def test_l2l_made_by_the_chain(self):
        """The label tool compiled by l3c reads hello_names.l2 twice and writes what the reference writes."""
        img = self.make('l2l')
        s = t.read('hello_names.l2', 'rb')
        r = run(img, 20, 2, checked=True, limit=BIG, stdin=s + b'\0' + s + b'\0')
        self.assertEqual(r.rc, 0, r.err)
        self.assertEqual(r.out, l2ltext.encode(s, twice=True)[0])

    def test_mutations(self):
        rng = random.Random(2305)
        junk = ['&zz', '&a[', '&a[1:', '&a[3:2]', '"x', '"x"y', '1x', '0', '99999999', '&', '&a]', 'block', 'data', 'halt', 'ret', ':', '::a',
                ':1a', '#', '&main', '&a[0]', '"\\q"', '"\\n"', '&add4', '&sub4', '&hex4', 'zero', '&zero', 'data 8 0', 'table 1 1 5 6 7',
                ':zz table 1 1 1', 'call', 'if', 'lut', 'store', 'add', 'shl', 'key', 'emit']
        bases = [t.hoisted(n) for n in ('echo', 'branch', 'and_hex', 'loop_digits', 'array', 'arith8')]
        for _ in range(300):
            toks = re.split(r'(\s+)', rng.choice(bases))
            for _ in range(rng.choice((1, 1, 2, 3))):
                idx = [j for j in range(len(toks)) if toks[j].strip()]
                if not idx:
                    break
                j, m = rng.choice(idx), rng.randrange(4)
                if m == 0:
                    toks[j] = rng.choice(junk)
                elif m == 1:
                    toks[j] = ''
                elif m == 2:
                    toks.insert(j, rng.choice(junk) + ' ')
                else:
                    toks = toks[:j]
                    break
            src = ''.join(toks)
            r = t.l3c(src)
            want, err = l3ctext.encode(src)
            self.assertEqual(r.out, want, src)
            self.assertEqual('l3c: ' in r.err, err is not None, (src, r.err))


class FixedPoint(unittest.TestCase):
    """23.9, part 3: l3c builds itself (text of language 3 -> l3c -> l2l -> seed -> image) and the image it builds is the one that built it."""

    @classmethod
    def tearDownClass(cls):
        for name, ticks, sec in REPORT:
            sys.stderr.write('%-28s %12d ticks %7.1f s\n' % (name, ticks, sec))

    def chain(self, tag, l3c, P, src):
        """text of language 3 -> l3c (A = 20, P) -> l2l (the text twice) -> seed -> the image; returns the three outputs."""
        l2 = step(tag + ' l3c', l3c, 20, P, src + b'\0')
        l1 = step(tag + ' l2l', self.l2l_img, self.l2l_st['A'], self.l2l_st['P'], l2 + l2)
        return l2, l1, step(tag + ' seed', self.seed_img, self.seed_st['A'], self.seed_st['P'], l1)

    def test_fixed_point(self):
        src = t.read('l3c.tw', 'rb')
        want = l3ctext.encode(src)
        self.assertIsNone(want[1])
        l3c_l1 = t.read('l3c.l1', 'rb') + b'\0'
        # no Python on this path: seed.img(l3c.l1) is the image of l3c (A = 20, P = 2, serial layout); it builds l3c.l1 again and the same image
        img1 = tools()['l3c'][0]
        self.assertLess(len(img1) * 8, 1 << 20)
        l2, l1, img2 = self.chain('l3c (chain image)', img1, 2, src)
        self.assertEqual(l2, want[0])
        self.assertEqual(l1, l3c_l1)
        self.assertEqual(img2, img1)
        # the Python image of l3c (packed layout, P = 3) writes the same text of language 2: the first image was made by it
        self.assertEqual(step('l3c (Python image) l3c', l3ctext.tool_image(), 20, 3, src + b'\0'), want[0])
        # the tool the chain built works as the tool of Python: a few texts
        for name in ('echo', 'branch', 'array'):
            text = t.hoisted(name).encode()
            self.assertEqual(step('chain l3c on ' + name, img1, 20, 2, text + b'\0'), l3ctext.encode(text)[0])

    def test_all_the_names(self):
        """1020 names of a user fit in the table of l3c (and 4 of the tool), the 1021st is bad label: the same bytes as the reference."""
        for n, bad in ((1020, False), (1021, True)):
            src = ''.join(':a%d data 1 0\n' % i for i in range(n)) + ':main block\nhalt\n'
            r = run(self.tool_image, 20, 3, checked=False, limit=BIG, stdin=src.encode() + b'\0')
            want, err = l3ctext.encode(src)
            self.assertEqual(r.out, want)
            self.assertEqual((err, 'l3c: bad label' in r.err), ('lab', True) if bad else (None, False))

    @classmethod
    def setUpClass(cls):
        t.setUpModule()
        cls.tool_image = t.tool()['image']
        # the seed and the label tool without Python compilers: seed.l1 -> (the Python encoder, once) seed.img; l2l.l1 -> seed -> l2l.img
        sh = tools()
        (cls.seed_img, a, p), (cls.l2l_img, b, q) = sh['seed'], sh['l2l']
        cls.seed_st, cls.l2l_st = dict(A=a, P=p), dict(A=b, P=q)


class PackedFixedPoint(unittest.TestCase):
    """23.10: the fixed point with the planner. The serial chain (l3c, l2l, seed of 23.9, no Python) makes the planner l3p; with it in the chain the text
    `pack` + l3c.tw becomes the image of the packed l3c (P = 3); that image builds, with the same planner, the same text of language 2, the same text of language 1
    and the same image: it builds itself. The planner and the image are what the references of Python give; the packed tools made by it work."""

    @classmethod
    def setUpClass(cls):
        cls.first = len(REPORT)

    @classmethod
    def tearDownClass(cls):
        for name, ticks, sec in REPORT[cls.first:]:
            sys.stderr.write('%-34s %12d ticks %7.1f s\n' % (name, ticks, sec))

    def test_packed_fixed_point(self):
        t.setUpModule()
        tl = tools()
        src = b'pack\n' + t.read('l3c.tw', 'rb')
        want, err = l3ctext.encode(src)
        self.assertIsNone(err)
        want2, err = l3ctext.pack_pass(want)
        self.assertIsNone(err)
        # the planner by the serial chain
        planner = serial_pass('l3p')[2]
        # the packed l3c by the serial chain with the planner, and by the packed chain with the planner: the same image
        l2a, l1a, img0 = chain('packed l3c (serial chain)', tl['l3c'], src, planner)
        self.assertEqual(l2a, want2)
        self.assertEqual(l1a, l3ctext.language1(src)[0] + b'\0')
        self.assertEqual(img0, l5.chain_image(src.decode('latin-1'))[0])
        self.assertLess(len(img0) * 8, 1 << 20)
        l2b, l1b, img1 = chain('packed l3c (packed chain)', (img0, 20, 3), src, planner)
        self.assertEqual((l2b, l1b, img1), (l2a, l1a, img0))
        # the packed tools made by the packed chain work: the planner itself, the seed, the label tool
        l2c, l1c, pl_pack = chain('l3p (packed chain)', (img1, 20, 3), b'pack\n' + t.read('l3p.tw', 'rb'), planner)
        self.assertEqual(l1c, l3ctext.language1(b'pack\n' + t.read('l3p.tw', 'rb'))[0] + b'\0')
        self.assertEqual(step('packed l3p on l3c.tw', pl_pack, 20, 3, want), want2)
        _, _, seed_pack = chain('seed (packed chain)', (img1, 20, 3), b'pack\n' + t.hoisted('seed').encode(), planner)
        src1 = t.read('seed.l1', 'rb') + b'\0'
        self.assertEqual(step('packed seed on seed.l1', seed_pack, 20, 3, src1), l1text.encode(src1)[0])

    def test_names_fill_the_table_in_pack_mode(self):
        """1020 names and the 1021st: the same bytes and the same reports as the reference, in pack mode too."""
        t.setUpModule()
        img = tools()['l3c'][0]
        for n, bad in ((1020, False), (1021, True)):
            src = 'pack\n' + ''.join(':a%d data 1 0\n' % i for i in range(n)) + ':main block\nhalt\n'
            r = run(img, 20, 2, checked=False, limit=BIG, stdin=src.encode() + b'\0')
            want, err = l3ctext.encode(src)
            self.assertEqual(r.out, want)
            self.assertEqual((err, 'l3c: bad label' in r.err), ('lab', True) if bad else (None, False))


class LongWords(unittest.TestCase):
    """23.17: `long!` and `long@` on the chain without Python. The pass l4p is made by the serial chain; the programs go l3c -> l4p -> [l3p] -> l2l -> seed
    and every step is what the references give; the images work as the images of the Python compiler (the output and the host files)."""

    @classmethod
    def setUpClass(cls):
        cls.first = len(REPORT)
        t.setUpModule()

    @classmethod
    def tearDownClass(cls):
        for name, ticks, sec in REPORT[cls.first:]:
            sys.stderr.write('%-34s %12d ticks %7.1f s\n' % (name, ticks, sec))

    def host(self, image, A, P, data=t4.FILE):
        d = tempfile.mkdtemp(prefix='tower-long-')
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, 'f.bin')
        with open(f, 'wb') as h:
            h.write(data)
        r = run(image, A, P, checked=True, limit=BIG, files=[f])
        with open(f, 'rb') as h:
            return r.rc, r.out, h.read()

    def test_the_chain(self):
        tl = tools()
        longp, planner = serial_pass('l4p')[2], serial_pass('l3p')[2]
        self.assertEqual(longp[0], t4.pass_tool()['image'])
        example = t4.readme_example()
        for name, prog in [('readme', example)] + sorted(t4.PROGRAMS.items()):
            for pack in (False, True):
                if pack and name == 'cat':          # the two adds of 128 bits are blocks of more than 254 layers: too big for the planner
                    continue
                full = ('pack\n' if pack else '') + prog
                tag = '%s%s' % (name, ' pack' if pack else '')
                l2, l1, img = chain(tag, tl['l3c'], full.encode(), planner if pack else None, longp)
                want2, err = l3ctext.encode(full)
                self.assertIsNone(err)
                want2 = l3ctext.long_pass(want2)[0]
                if pack:
                    want2 = l3ctext.pack_pass(want2)[0]
                self.assertEqual(l2, want2, tag)
                self.assertEqual(l1, l3ctext.language1(full.encode())[0] + b'\0', tag)
                ref = l5.chain_image(full)
                self.assertEqual((img, 3 if pack else 2), ref, tag)
                py, errs = text.compile_text(prog)
                self.assertEqual(errs, [])
                a = self.host(img, 20, ref[1])
                b = self.host(py.stats['image'], py.stats['A'], py.stats['P'])
                self.assertEqual(a, b, tag)
                self.assertEqual(a[0], 0)
                if name == 'readme':
                    self.assertEqual(a[1:], (b'hello', bytes([t4.FILE[0]]) + b'hello' + t4.FILE[6:]))

    def test_errors_of_the_words(self):
        """The reports of l3c on the words of language 4: the same bytes and messages as the reference (`bad width`, `too big`, `bad text`)."""
        tl = tools()
        head = ':p data 128 0\n:p127 data 127 0\n:o data 40 "hello"\n:w data %d 0\n:main block\n' % (l3ctext.NMAX + 1)
        for body in ('long! &p127 &o', 'long@ &o &o', 'long! &p &w', 'long!x &p &o', 'long &p &o', 'long@ &p', 'long! &p &w[0:%d]' % l3ctext.NMAX):
            src = head + body + '\nhalt\n'
            r = run(tl['l3c'][0], 20, 2, checked=False, limit=BIG, stdin=src.encode() + b'\0')
            want, err = l3ctext.encode(src)
            self.assertEqual(r.out, want, body)
            self.assertEqual(('l3c: ' in r.err) and r.err.strip(), err is not None and l3ctext.MESSAGES[err].strip(), body)
        for l2 in (b'long\nd 14 1\nd 14 zz\nd 14 3\nd 14 400\nc a0 0 560\n\0', b'long\nd 14 1\n\0', b'x\nlong\0'):
            r = run(t4.pass_tool()['image'], 20, 2, checked=False, limit=BIG, stdin=l2)
            want, err = l3ctext.long_pass(l2)
            self.assertEqual((r.out, 'l4p: bad text' in r.err), (want, err is not None))


if __name__ == '__main__':
    unittest.main()
