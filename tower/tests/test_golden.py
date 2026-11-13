"""Frozen checks of the passes of the chain (25.7.1): for each pass (seed, l2c, l2l, l3c, l3p, l4c) tower/golden/<pass>.jsonl lists inputs and
expected outputs (a line per input: stdin, the exit code, stderr, the output whole when it is short, else its length and sha256). The test
runs the pass ON THE CHAIN (the image of the pass on the checked emulator) and compares byte for byte; it imports none of the Python
references l2text, l2ltext, l3ctext. The images are made here without them: the seed from seed.l1 by l1text (the first image, as hex0), then
l2c, l2l, l3c by the seed from their texts of language 1 (*.l1), l3p and l4c by the chain itself (l3c -> l2l -> seed from l3p.tw, l4c.tw; the
serial layout). Fast part: tier "fast" (here); the rest, "long" (l3p, l4c and the dear inputs), is in long_golden.py.
Update the manifest (after a change of a pass or of an input):  GOLDEN_UPDATE=1 python3 -B tower/tests/test_golden.py
(the update still needs the Python references: it takes the expected values from them and tells where the chain differs).
Run: make check-tower  or  python3 -B tower/tests/test_golden.py"""
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import common
import l1text
from common import run

PROGRAMS = os.path.join(common.HERE, 'programs')
GOLDEN = os.path.join(common.HERE, 'golden')
PASSES = ('seed', 'l2c', 'l2l', 'l3c', 'l3p', 'l4c')
LIMIT = 300 * 10 ** 6
INLINE_IN, INLINE_OUT = 4096, 2048
FAST_TICKS = 3 * 10 ** 6            # an input of the passes up to l3c is "fast" when the chain needs no more ticks than this
WORKERS = 4
# the chain is the specification here: the table of names of l4c keeps 63 names (test_l4p.py, test_table_of_names_is_full), the reference keeps more
CHAIN_ONLY = {('l4c', 'names-70')}


def setUpModule():
    common.ensure_built()


def read(name, mode='rb'):
    with open(os.path.join(PROGRAMS, name), mode) as h:
        return h.read()


# ---- the images of the passes (no Python references of l2, l2l, l3c)

_TOOLS, _LOCKS, _GUARD = {}, {}, threading.Lock()


def header(name):
    """(A, P) from the first line of programs/<name>.l1."""
    m = re.search(rb'\(A=(\d+), P=(\d+)\)', read(name + '.l1').split(b'\n')[0])
    return (int(m.group(1)), int(m.group(2))) if m else (20, 2)


def _step(name, tl, stdin):
    img, A, P = tl
    r = run(img, A, P, checked=True, limit=LIMIT, stdin=stdin)
    assert r.rc == 0 and r.ticks < LIMIT, (name, r.rc, r.err)
    return r.out


def tool(name):
    """(image, A, P) of a pass or of a tool (cached; built once under a lock of its own)."""
    with _GUARD:
        lock = _LOCKS.setdefault(name, threading.Lock())
    with lock:
        if name not in _TOOLS:
            if name == 'seed':
                img, err = l1text.encode(read('seed.l1') + b'\0')
                assert err is None, err
                _TOOLS[name] = (img,) + header('seed')
            elif name in ('l2c', 'l2l', 'l3c'):
                A, P = header(name)
                _TOOLS[name] = (_step(name, tool('seed'), read(name + '.l1') + b'\0'), A, P)
            else:                                   # l3p, l4c: text of language 3 -> l3c -> l2l (twice) -> seed
                l2 = _step(name + ' l3c', tool('l3c'), read(name + '.tw') + b'\0')
                l1 = _step(name + ' l2l', tool('l2l'), l2 + l2)
                _TOOLS[name] = (_step(name + ' seed', tool('seed'), l1), 20, 2)
        return _TOOLS[name]


def stdin_of(pas, e, text):
    """What the pass reads: the text and a zero byte; l2l reads it twice in the mode `twice`; l3p and l2l without the mode read the text as it is."""
    if pas == 'l3p' or (pas == 'l2l' and e.get('mode') != 'twice'):
        return text
    return text + b'\0' + (text + b'\0' if pas == 'l2l' else b'')


def says(r):
    """What the pass wrote to stderr (without the audit line of the checking emulator)."""
    return r.err.split('VM1_AUDIT')[0]


def chain_run(pas, e, text):
    img, A, P = tool(pas)
    return run(img, A, P, checked=True, limit=LIMIT, stdin=stdin_of(pas, e, text))


# ---- the manifest

def text_of(e):
    """The input of an entry: inline (latin-1 in JSON) or a file (in/... of golden, programs/... of the tower)."""
    if 'in' in e:
        return e['in'].encode('latin-1')
    base = common.HERE if e['file'].startswith('programs/') else GOLDEN
    with open(os.path.join(base, e['file']), 'rb') as h:
        return h.read()


def load(pas):
    with open(os.path.join(GOLDEN, pas + '.jsonl'), encoding='utf-8') as h:
        return [json.loads(x) for x in h if x.strip()]


def compare(e, r):
    """The problems of one run against the entry (empty when it agrees)."""
    bad = []
    if r.rc != e['rc']:
        bad.append('rc %r, expected %r' % (r.rc, e['rc']))
    if says(r) != e['err']:
        bad.append('stderr %r, expected %r' % (says(r), e['err']))
    if 'out' in e:
        if r.out != e['out'].encode('latin-1'):
            bad.append('output differs')
    elif (len(r.out), hashlib.sha256(r.out).hexdigest()) != (e['len'], e['sha']):
        bad.append('output length %d sha %s, expected %d %s' % (len(r.out), hashlib.sha256(r.out).hexdigest()[:12], e['len'], e['sha'][:12]))
    return bad


def check_tier(tc, pas, long):
    """Run the entries of a pass in the tier on the chain and compare."""
    es = [e for e in load(pas) if bool(e.get('long')) == long]
    tc.assertTrue(es, pas)
    tool(pas)
    with ThreadPoolExecutor(WORKERS) as ex:
        runs = list(ex.map(lambda e: chain_run(pas, e, text_of(e)), es))
    for e, r in zip(es, runs, strict=True):
        with tc.subTest(pas=pas, name=e['name']):
            tc.assertEqual(compare(e, r), [], e['name'])
    return len(es)


class Golden(unittest.TestCase):
    """The fast tier of the passes up to l3c."""

    def test_manifest_is_whole(self):
        for pas in PASSES:
            es = load(pas)
            self.assertEqual(len({e['name'] for e in es}), len(es), pas)
            for e in es:
                self.assertEqual(('in' in e) + ('file' in e), 1, e['name'])
                self.assertEqual(('out' in e) + ('sha' in e), 1, e['name'])
                if 'file' in e:
                    self.assertTrue(os.path.exists(os.path.join(common.HERE if e['file'].startswith('programs/') else GOLDEN, e['file'])), e['file'])

    def test_seed(self):
        check_tier(self, 'seed', False)

    def test_l2c(self):
        check_tier(self, 'l2c', False)

    def test_l2l(self):
        check_tier(self, 'l2l', False)

    def test_l3c(self):
        check_tier(self, 'l3c', False)


# ---- the update (needs the Python references; the test itself does not)

def sha(b):
    return hashlib.sha256(b).hexdigest()


def cases():
    """[(pass, name, text, mode or None)] with the inputs of the existing tests (the same lists, the same seeds)."""
    import l2text
    import l3ctext
    import text as tw

    out = []

    def add(pas, name, text, mode=None):
        text = text.encode('latin-1') if isinstance(text, str) else bytes(text)
        out.append((pas, name, text, mode))

    def prog(name):
        return read(name + '.tw', 'r').encode()

    def compiled(name):
        p, errs = tw.compile_text(prog(name).decode())
        assert not errs, errs
        return p

    def spoil(rnd, base, alphabet, n):
        for k in range(n):
            t = list(base)
            for _ in range(rnd.randint(1, 3)):
                i = rnd.randrange(len(t))
                kind = rnd.randrange(3)
                if kind == 0:
                    t[i] = rnd.choice(alphabet)
                elif kind == 1:
                    del t[i]
                else:
                    t.insert(i, rnd.choice(alphabet))
            yield k, ''.join(t)

    skip = ('calls', 'fib', 'l3c', 'l3p', 'l4c', 'forth', 'forthgen')
    names = [f[:-3] for f in sorted(os.listdir(PROGRAMS)) if f.endswith('.tw') and f[:-3] not in skip]

    def program_text(n):
        return l1text.program_text(compiled(n), 'the image of %s.tw' % n)

    def hoist(n):
        return l3ctext.hoist(prog(n).decode())

    # seed (test_seed.py)
    for k, src in enumerate(('w 10\nr 1 2 3 4\n', 'w 8\nr ff 0 1 80\n', 'z 8\n', 's 11110000\n', 's 1 0 1 0 1 0 1 0\n', 'w 4\nr 1 2 3 4\n',
                             '# nothing\n\n  \t w 3\n z 3\ns 01\n', 'w 10\nr 1 2 3 4\nz 18\ns 1\nz 6\n', 'w 10\nr 1 2 3 4', 'w 10\nr 12345 2 3 4\n',
                             'w 10\nr 123456 2 3 4\n', 'w 12\nr 3fffa 3fffb 2 3\n', 'w 0\n', 'z 100\n', 'w 100\nz ff\n', '', 'w 5 \n z 3 \n',
                             'w 10\r\nr 1 2 3 4\r\n')):
        add('seed', 'small-%02d' % k, src)
    for k, src in enumerate(('q\n', 'a 1\n', '1\n', 'w\n', 'w 1 2\n', 'w 10\nr 1 2 3\n', 'w 10\nr 1 2 3 4 5\n', 'r 1 2 3 4\n', 'w 10\nr 1 2 3 g\n',
                             'w 10\nr 1 2 3 4 # c\n', 's 012\n', 's 1', 's 1\nz 3\n', 'w 10\nz 4\ns 1\n', 'z\n', 'z 1 2\n', 'W 10\n', '# c\nwx\n',
                             's 11111111\nq\n')):
        add('seed', 'rejected-%02d' % k, src)
    rnd = random.Random(237)
    for k, src in spoil(rnd, 'w 6\nr 1 2 3 4\nz 4\ns 0101 1100 0\n# c\nz 3\nw a\nz 8\ns 1\nz 7\n', 'wrzs# 01abfg\n\tx\r2', 60):
        add('seed', 'random-%02d' % k, src)
    for n in names:
        add('seed', 'program-' + n, program_text(n))
    add('seed', 'seed.l1', read('seed.l1'))
    # l2c (test_l2c.py)
    for k, src in enumerate((
            'c 8 10 20\n', 'c 1 2 3\n', 'c 0 0 0\n', 'c fffff 1 1\n', 'c 1 fffff 0\n', 'c 4 123456 0\n', 'd 8 5\n', 'd 0 0\n', 'd 14 fffff\n', 'd 3 7\n',
            'w 10\nr 1 2 3 4\nz 5\ns 0101\n# c\n', 'w 10\nc 4 1 2\nc 4 3 4\n', ':a d 8 5\nc 4 &a+1 &a\n', ':a\n:b c 1 &a &b\n',
            'w 8\nr 1 2 3 4\n:c c 1 &c &c+4\n', 'w 8\nz 8\n:a o\nc 1 &a 1\n', 'w 8\nr 0 0 0 0\n:a d 4 1\no\n:b c 1 &b &b\n', '\n  \t c 1 2 3  \n\n',
            'c 1 2 3\r\n', 'c 1 2 3', '', '\n', ':a d 8 5\n\t:b c 8 &a &b\n', 'z 3\ns 1 1 1\n:a :b\nc 1 &a &b\n', 'w 5 \n z 3 \n',
            'w 10\nr 1 2 3 4\n:a d 8 5\nc 4 &a+1 &a\n')):
        add('l2c', 'small-%02d' % k, src)
    for k, src in enumerate(('x\n', 'q', '1\n', '&a\n', ': \n', '::\n', ':A\n', ':1\n', ':\n', 'c 1 2 3 4\n', 'c 1 2\n', 'c\n', 'c 1 2', 'd 1\n',
                             'd 1 2 3\n', 'w\n', 'z 1 2\n', 'o 1\n', ':a\n:a\n', 'c 1 &a 2\n', ':a c 1 &b 2\n', 'c 1 &A 2\n', 'c 1 &1 2\n', 'c 1 & 2\n',
                             'c 1 &\n', 'c 1 2& 3\n', 'c 1 2+3 4\n', 'c 1 +1 2\n', ':a c 1 &a4 2\n', ':a c 1 &a&a 2\n', ':a c 1 &a++1 2\n', 'c 1 g 2\n',
                             'c 1 2 3 # x\n', 'w 10\nr 1\nc 1 2 3 4\n', 's 11\nc 1 2\n', 'w 10\nr 1 2 3 4\nq\n', 'w 10\nr 1 2 3 4\nc 1 &a 2\n')):
        add('l2c', 'rejected-%02d' % k, src)
    rnd = random.Random(238)
    for k, src in spoil(rnd, 'w 10\n# c\nr 1 2 3 4\n:a d 8 5\n:b z 8\ns 0101 11\n  c 4 &a+1 &b\nc ff fff 1\nd 10 abcde\no\n:c c 1 &a &c\nz 3\n',
                        'wrzsdco#: 01abfg&+\n\tx\r2zq', 60):
        add('l2c', 'random-%02d' % k, src)
    for n in ('echo', 'add', 'branch', 'array'):
        add('l2c', 'program-' + n, l2text.to_l2(program_text(n)))
    add('l2c', 'seed-in-l2', l2text.to_l2(read('seed.l1', 'r')))
    for f in ('hello.l2', 'l2c.l2', 'l2l.l2'):
        add('l2c', f, read(f))
    # l2l (test_labels.py); the text is given twice (mode twice) unless it is the whole stdin
    for k, src in enumerate((
            'c 8 10 20\n', 'c 0 0 0\n', 'c fffff 1 1\n', 'd 8 5\n', 'd 14 fffff\n', 'w 10\nr 1 2 3 4\nz 5\ns 0101\n# c\n', ':a d 8 5\nc 4 &a+1 &a\n',
            ':a\n:b c 1 &a &b\n', 'w 8\nr 1 2 3 4\n:c c 1 &c &c+4\n', 'w 8\nz 8\n:a o\nc 1 &a 1\n', '\n  \t c 1 2 3  \n\n', 'c 1 2 3\r\n', 'c 1 2 3', '',
            '\n', 'z 3\ns 1 1 1\n:a :b\nc 1 &a &b\n', 'w 5 \n z 3 \n', 'c 1 &f 2\n:f d 8 1\n', 'w 10\nc 1 &end 2\nc 1 &end &end+1\n:end',
            ':a c 1 &b &c\n:b c 1 &c &a\n:c\n', 'c 1 &x+ff &x+0\n:x\n', 'c 1 &a+fffff &a\n:a\n', ':a1 :b2 :c3 c 1 &c3 &a1\nc 1 &b2 &c3+2\n',
            'c 1 &a &b\n:a\n:b\n', ':a :b\nc 1 &b &a\n', 'o\n:a c 1 &a &a\n', ':z c 1 &z 1\n', ':_ c 1 &_ 1\n', ':0 c 1 &0 1\n', ':9 c 1 &9 1\n',
            ':a d 4 3\nd 4 &a\n', 'd 8 &a\n:a\n', 'w &a\n:a d 8 4\n', 'z &a\n:a\n', 'w 10\nr 1 2 3 4\nc 4 &after &here\n:here d 8 5\n:after',
            'w 10\nc 1 &n0 &n1\n:n0 d 1 1\n:n1', 'w 10\nr 1 2 3 4\n:alpha d 8 5\nc 1 &alpha &alpha\n',
            'w 10\nc 1 &fwd 2\n:fwd d 1 1\nc 1 &fwd+3 &fwd\n', ':a:b d 8 5\nc 4 &a &b\nc 1 &c &a\n:c')):
        add('l2l', 'small-%02d' % k, src, 'twice')
    for n in ('a', 'ab', 'z' * 7, 'z' * 8, 'z' * 14, 'z' * 15, 'a_1b_2c_3d_4e_5f', 'x' * 15, 'label_15_bytes_'):
        add('l2l', 'name-' + n[:20], ':%s d 8 1\nc 1 &%s &%s+1\n' % (n, n, n), 'twice')
    add('l2l', 'names-prefixes', ':abcdefghijklmno d 8 1\n:bcdefghijklmno d 8 2\n:abcdefghijklmn d 8 3\n:a d 8 4\n:aa d 8 5\n:ba d 8 6\n:b d 8 7\n'
        'c 1 &abcdefghijklmno &bcdefghijklmno\nc 1 &abcdefghijklmn &a\nc 1 &aa &ba\nc 1 &b &a\n:x1 :x2 :x3 :xx1\nc 1 &x1 &x2\nc 1 &x3 &xx1\n', 'twice')
    for k, bad in enumerate((':abcdefghijklmnop\n', 'c 1 &abcdefghijklmnop 2\n:abcdefghijklmnop\n', ':' + 'q' * 40 + '\n', 'c 1 &' + 'q' * 17 + ' 2\n')):
        add('l2l', 'longname-bad-%d' % k, bad, 'twice')
    for k, src in enumerate((
            'x\n', 'q', '1\n', '&a\n', ': \n', '::\n', ':A\n', ':\n', ':a+\n', ':a-b\n', ':a.b\n', 'c 1 2 3 4\n', 'c 1 2\n', 'c\n', 'd 1\n', 'w\n',
            'z 1 2\n', 'o 1\n', ':a\n:a\n', ':a :a\n', 'c 1 &a 2\n', ':a c 1 &b 2\n', 'c 1 &A 2\n', 'c 1 & 2\n', 'c 1 &\n', 'c 1 2& 3\n', 'c 1 2+3 4\n',
            'c 1 +1 2\n', ':a c 1 &a&a 2\n', ':a c 1 &a++1 2\n', 'c 1 g 2\n', 'c 1 2 3 # x\n', ':a c 1 &a-b 2\n', ':a c 1 &a:b 2\n', ':a c 1 &a#\n',
            'c 1 &a+x 2\n:a\n', 'c 1 &a &a &a\n:a\n', 'c 1 &a\n:a\n', 'w 10\nr 1\nc 1 2 3 4\n', 'w 10\nr 1 2 3 4\nq\n', ':a\n:b\n:a\n', 'c 1 2 3\n:a\n:a\n',
            'w 10\nr 1 2 3 4\nc 1 &a 2\n', 'w 10\nr 1 2 3 4\n:a c 1 &a 2\nq\n')):
        add('l2l', 'rejected-%02d' % k, src, 'twice')
    for k, (a, b) in enumerate(((b':a d 8 1\n:b\n', b'd 8 1\n:a d 8 1\n:b\n'), (b':a\n', b':a\n:b\n'), (b':a :b\n', b':a\n'), (b':a d 8 1\n', b':a d 8 2\n'),
                                (b'c 1 &a 2\n:a\n', b'c 1 &b 2\n:b\n'), (b'd 8 1\n', b'd 8 2\nd 8 3\n'), (b'', b'c 1 2 3\n'), (b'c 1 2 3\n', b''),
                                (b':a\n', b':a\n:b\n'))):
        add('l2l', 'two-copies-%d' % k, a + b'\0' + b + b'\0')
    add('l2l', 'one-copy', b'c 1 2 3\n\0')
    same = ['ab', 'cb', 'xxab', 'yyab', 'zzzzzzzzzzzzzab']
    src = ''.join(':%s d 1 1\n' % n for n in same) + 'c 1 &ab &zzzzzzzzzzzzzab\nc 1 &yyab &cb\n'
    for k, s in enumerate((src, src + ':xxab\n', src + 'c 1 &aab 1\n', ':ba d 1 1\n:ae d 1 1\nc 1 &ba &ae\nc 1 &ae &ba\n', ':ba d 1 1\n:ae d 1 1\n:ba\n')):
        add('l2l', 'hash-chain-%d' % k, s, 'twice')
    rnd = random.Random(239)
    for k, src in spoil(rnd, 'w 10\n# c\nr 1 2 3 4\n:alpha d 8 5\n:beta_2 z 8\ns 0101 11\n  c 4 &alpha+1 &gamma\nc ff fff 1\nd 10 abcde\no\n'
                        ':gamma c 1 &alpha &delta_long_name\nz 3\n:delta_long_name c 1 &beta_2+3 &gamma\n', 'wrzsdco#: 01abfg&+\n\tx\r2zq_ZAlphagmn', 60):
        add('l2l', 'random-%02d' % k, src, 'twice')
    add('l2l', 'hello_names.l2', read('hello_names.l2'), 'twice')
    add('l2l', 'l2l.l2', read('l2l.l2'), 'twice')
    nm = ['n%d' % i for i in range(1024)]
    add('l2l', 'labels-1024', ''.join(':%s d 1 1\n' % n for n in nm) + 'c 1 &n0 &n1023\nc 1 &n127 &n1023+1\nc 1 &n512 &n999\n', 'twice')
    add('l2l', 'labels-1025', ''.join(':%s\n' % n for n in nm) + ':one_more\n', 'twice')
    # l3c (test_l3c.py, test_l3p.py, long_l3c.py)
    small = ['echo', 'branch', 'add16_hex', 'and_hex', 'arith8', 'arith16', 'array', 'loop_digits']
    for n in names:
        if n not in ('seed', 'l2c', 'l2l'):
            add('l3c', 'hoisted-' + n, hoist(n))
    for n in small:
        add('l3c', 'packed-' + n, 'pack\n' + hoist(n))
    head = ':a data 16 "ab"\n:b data 16 0\n:main block\n'
    for k, src in enumerate((head + 'copy 1048572 &a\nhalt\n', head + 'copy 1048573 &a[0:8]\nhalt\n', head + 'copy &b 1048571\nhalt\n',
                             head + 'copy &b[8:12] 1048575\nhalt\n', head + 'copy 1048570 &a[3:20]\nhalt\n', head + 'copy &a[3:20] 1048570\nhalt\n',
                             head + 'copy 1048569 &a\nhalt\n', head + 'copy &a 1048569\nhalt\n', head + 'copy 1048572 1048571\nhalt\n',
                             head + 'emit 1048572\nhalt\n', head + 'copy 1048576 &a\nhalt\n', head + 'copy 1048572\nhalt\n',
                             head + 'shl &a 1048572 3\nhalt\n',
                             'pack\n' + head.replace(':main block\n', '') + ':main block\ncopy 1048570 &a\ncopy &b 1048570\nhalt\n')):
        add('l3c', 'channel-%02d' % k, src)
    add('l3c', 'channel-copy', ':b data 16 0\n:main block\ncopy &b[0:8] 1048571\ncopy &b[8:16] 1048571\ncopy 1048572 &b\ncopy 1048572 &b[8:16]\nhalt\n')
    calls = ''':msg data 24 "ab\\n"
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
    add('l3c', 'calls-and-stores', calls)
    add('l3c', 'calls-and-stores-packed', 'pack\n' + calls)
    for k, src in enumerate((':main block\nhalt\n', ':a data 8 "ab"\n:t table 2 8 1 2 3 4\n:x array 3 5\n:w word\nret\n:main block\ncall &w &m2\n:m2 block\n'
                             'lut &t &a[0:2] &a[0:8]\nstore &x &a[0:3] &a[0:5]\nshl &a &a 3\nhalt\n',
                             ':a data 16 0\n:b data 17 0\n:c data 16 0\n:main block\nadd &a &c &b\nsub &a &c &b\nshr &a &c 4\nkey &a\nwarn &a\nhalt\n',
                             ':t table 2 24 "abc" "def" "ghi" "jkl"\n:main block\nhalt\n', ':a data 40 1048575\n:b data 21 0\n:main block\nhalt\n')):
        add('l3c', 'data-tables-words-%d' % k, src)
    for k, src in enumerate((
            'foo', ':a :b data 1 0', ':a data 1 0 7', ':a block\n:b block', '&a', '"x', ':a data 8 "abc" ', ':A\n', ':a data 8 5x', ':main block\nret\nhalt',
            ':main block\ncopy &a &a\nhalt', ':a data 1 0\n:a data 1 0', ':zero data 1 0', ':add4 data 1 0',
            ':a data 8 0\n:b data 9 0\n:main block\ncopy &a &b\nhalt', ':a data 8 0\n:main block\ncopy &a[0:9] &a\nhalt',
            ':a data 3 0\n:main block\nadd &a &a &a\nhalt', ':a data 8 0\n:main block\nkey &a[0:4]\nhalt', ':a data 8 "abc"', ':main block\n:b block',
            ':main block\ngoto &main\nhalt', 'halt', ':main block\n:a data 1 0\nhalt', ':a data 8 0\n:main block\nkey &a', ':t table 1 8 "ab" "cd"',
            ':t table 1 16 "ab" "c"', ':t table 1 4 1', ':a data 8 "\\q"', ':a data 8 "' + 'x' * 33 + '"', ':abcdefghijklmno data 1 0',
            ':a data 8 0\n:main block\nlut &add4 &a[0:4] &a[0:4] &a[0:1] &a[0:5]\nhalt', ':a data 8 0\n:main block\nlut &hex4 &a[0:4]\nhalt',
            ':a data 1 0\n:b array 1 1\n:main block\nstore &b &a &a\nhalt', ':a data 1 0\n:b table 1 1 0 1\n:main block\nstore &b &a &a\nhalt',
            ':a data 1 0\n:main block\nif &a &main\n', ':a data 8 0\n:main block\ncopy 1048572 &a[0:9]\nhalt', ':main block\nemit &zero',
            ':a data 0 1', ':a data 8 0\n:main block\nlut &a &a &a\nhalt',
            ':a data 8 0\n:b data 9 0\n:main block\ncopy 1048572 &a\ncopy &a &b\nhalt')):
        add('l3c', 'error-%02d' % k, src)
    add('l3c', 'too-big', ''.join(':a%d array 8 64\n' % i for i in range(40)) + ':main block\nhalt\n')
    add('l3c', 'names-300', ''.join(':a%d data 1 0\n' % i for i in range(300)) + ':main block\nhalt\n')
    for k, src in enumerate(('pack\n:main block\nhalt\n:a data 1 0\n', 'pack\n:main block\nhalt\n:a table 1 1 1 0\n', ':a data 1 0\npack\n:main block\nhalt\n',
                             'pack pack\n', 'pack\n:a data 1 0\n:main block\nhalt\n', 'pack', 'pack\n\n# x\n:t table 3 2 1 2 3 0 1 2 3 0\n:main block\nhalt\n',
                             'pack\n:a :b data 1 0', 'pack\n:x array 4 7\n:main block\nstore &x &x[0:4] &x[0:7]\nhalt\n', '@\n', '# c\n@\n',
                             'pack\n:a data 8 0\n:main block\nif &a &main &main\nadd &a &a &a\n', 'pack\n:a data 8 5\n:main block\nhalt\n',
                             'pack\n:t table 2 4 1 2 3 4\n:main block\nhalt\n',
                             'pack\n:main block\nif &zero &y &n\n:y block\nhalt\n:n block\nhalt\n', '\n:main block\nhalt\n')):
        add('l3c', 'pack-mode-%02d' % k, src)

    def mutate(rng, bases, junk, n, ops):
        for k in range(n):
            toks = re.split(r'(\s+)', rng.choice(bases))
            for _ in range(rng.choice(ops)):
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
            yield k, ''.join(toks)
    junk = ['&zz', '&a[', '&a[1:', '&a[3:2]', '"x', '1x', '0', '99999999', '&', 'block', 'data', 'halt', 'ret', ':', '::a', ':1a', '#', '&main', '&a[0]',
            '"\\n"', '&add4', '&hex4', 'zero', '&zero', 'data 8 0', 'table 1 1 5 6 7']
    for k, src in mutate(random.Random(23), [hoist(n) for n in ('echo', 'branch', 'and_hex')], junk, 40, (1, 1, 2)):
        add('l3c', 'mutation-%02d' % k, src)
    junk2 = junk + ['"x"y', '"\\q"', '&sub4', 'call', 'if', 'lut', 'store', 'add', 'shl', 'key', 'emit', ':zz table 1 1 1']
    for k, src in mutate(random.Random(2305), [hoist(n) for n in ('echo', 'branch', 'and_hex', 'loop_digits', 'array', 'arith8')], junk2, 100, (1, 1, 2, 3)):
        add('l3c', 'mutation-long-%03d' % k, src)
    for n in ('seed', 'l2c', 'l2l'):
        add('l3c', 'tool-' + n, hoist(n))
    for n in ('l3c', 'l3p', 'l4c'):
        add('l3c', 'tool-' + n, prog(n))
    add('l3c', 'tool-l3p-packed', b'pack\n' + prog('l3p'))
    add('l3c', 'names-1020', ''.join(':a%d data 1 0\n' % i for i in range(1020)) + ':main block\nhalt\n')
    add('l3c', 'names-1021', ''.join(':a%d data 1 0\n' % i for i in range(1021)) + ':main block\nhalt\n')
    # l4c (test_l4p.py)
    l4 = l4_cases()
    for name, src in l4:
        add('l4c', name, src)
    for name, src in l4:
        if name.startswith('program-'):
            after = l3ctext.l4c(src + b'\0')[0][:-1]
            add('l3c', 'after-l4c-' + name[8:], after)
            add('l3c', 'after-l4c-packed-' + name[8:], b'pack\n' + after)

    # l3p: the output of l3c in pack mode (test_l3p.py)
    def l3out(src):
        o, err = l3ctext.encode(src)
        assert err is None, err
        return o
    for n in ('echo', 'branch', 'arith8', 'and_hex', 'loop_digits', 'arith16', 'add16_hex'):
        add('l3p', 'program-' + n, l3out('pack\n' + hoist(n)))
    add('l3p', 'program-seed', l3out('pack\n' + hoist('seed')))
    add('l3p', 'program-calls-and-stores', l3out('pack\n' + calls))
    host = '0x%x' % (1 << 128 | 1 << 96 | 8)
    add('l3p', 'long-words-plan', l3out(l3ctext.l4c(('pack\n:w data 200 0\n:x data 8 0\n:main block\ncopy &w[0:16] %s\ncopy &x &w[0:8]\ncopy %s &w[0:16]\n'
                                                      'halt\n' % (host, host)).encode() + b'\0')[0][:-1]))
    add('l3p', 'long-words', l3out(l3ctext.l4c(('pack\n:w data 200 0\n:x data 8 0\n:main block\ncopy &w[0:16] %s\ncopy &x &w[0:8]\ncopy %s &w\ncopy &w %s\n'
                                                'halt\n' % (host, host, host)).encode() + b'\0')[0][:-1]))
    for k, src in enumerate(('pack\n:a data 8 1\n:b data 8 2\n:main block\ncopy &b &a\nemit &b\nhalt\n',
                             'pack\n:a data 8 1\n:b data 8 2\n:c data 8 3\n:d data 8 4\n:e data 8 5\n:f data 8 6\n:o data 8 0\n:main block\ncopy &a &b\n'
                             'copy &c &d\ncopy &e &f\nhalt\n',
                             'pack\n:t table 1 8 7 9\n:d data 8 4\n:o data 8 0\n:main block\nlut &t &d[0] &o\nhalt\n',
                             'pack\n:main block\nhalt\n')):
        add('l3p', 'rules-%d' % k, l3out(src))
    good = l3out('pack\n' + hoist('branch')).decode()
    head_text = good[:good.index(':bmain\n')]
    tails = [':bmain\nw 1\n', ':bmain\nc 1 2\n', ':bmain\nz 51\nc a0 0 0\n:e\n', ':bmain\nz 50\nz 50\n', ':bmain\nd 14 1\nc 1 1 1\n',
             ':bmain\nz 50\nc a0 0 200\n:e\n', ':bmain\nd 14 1\nd 14 1\nd 14 1\nc a0 0 0\n', ':bmain\nz 50\nc a0 0 0\n# a 3 5\nc 1 1 1\n:e\n', '# a 2 3\n',
             ':bmain\nz 50\nc a0 0 &e\n# a 3 5\nz 4\n:e\n', ':bmain\nz 50\nc a0 0 &e\n:e\nz 5', ':bmain\nc 1 2 3\nc a0 0 100\n', ':bmain\nz 50\n',
             ':bmain\n' + 'c 1 2 3\nc a0 0 4\n' * 253 + 'z 50\nc a0 0 &e\n:e\n', ':bmain\n' + 'c 1 2 3\nc a0 0 4\n' * 254 + 'z 50\nc a0 0 &e\n:e\n',
             ':bmain\nc 1 2 3\nc a0 0 &e\n:bx\nc 4 1 2\nc a0 0 0\n:e\n', ':bmain\nz 50\nc 1 2 2e0\nc a0 0 &e\n:e\n',
             ':bmain\nz 50\nc 1 %x 2\nc a0 0 &e\n:e\n' % 0x1e1, ':bmain\nz 50\nc a0 0 &e\n:e\n']
    for k, tail in enumerate(tails):
        add('l3p', 'error-%02d' % k, (head_text + tail).encode() + b'\0')
    base = l3out('pack\n:t table 2 8 1 2 3 4\n:a data 8 1\n:b data 8 2\n:main block\nlut &t &a[0:2] &b\nif &b[0] &y &n\n:y block\n'
                 'emit &a\ncall &w &z\n:z block\nhalt\n:n block\nhalt\n:w word\nkey &a\nret\n').decode()
    pj = ['c', 'z 50', 'd 14 1', 'c a0 0 &e', 'c a0 0 0', 'c 1 2', '# a 3 4', ':bx', '', 'q', 'c a0 0 &bmain', 'c f0 0 12', 'o', 'z ff', '# a 9 0',
          '# a 3', '# b 3 4', '#a 3 4', '# a', 'w 14 1 2 3', 'c a0 0 0 0']
    lines = base.split('\n')[:-1]
    rng = random.Random(2310)
    for k in range(80):
        ls = list(lines)
        for _ in range(rng.choice((1, 1, 2))):
            i = rng.randrange(len(ls))
            m = rng.randrange(4)
            if m == 0:
                ls[i] = rng.choice(pj)
            elif m == 1:
                del ls[i]
            elif m == 2:
                ls.insert(i, rng.choice(pj))
            else:
                ls = ls[:i]
                break
            if not ls:
                break
        add('l3p', 'mutation-%02d' % k, ('\n'.join(ls) + '\n').encode('latin-1') + b'\0')
    return out


def l4_cases():
    """[(name, text)] for l4c: the programs, the edges, the far and channel forms, names, and texts spoiled (test_l4p.py)."""
    def host(area, bit):
        return '0x%x' % (1 << 128 | area << 96 | bit)

    def farad(bit, link=0):
        return '0x2%032x' % (link << 96 | bit)
    HOSTA = host(1, 8)
    FAR = farad(8 * 3)
    programs = {
        'rw': ':out data 40 "hello"\n:got data 40 "\\0\\0\\0\\0\\0"\n:main block\ncopy %s &out\ncopy &got %s\nemit &got\nhalt\n' % (host(1, 8), host(1, 8)),
        'cat': ':buf data 64 0\n:main block\n' + ''.join('copy &buf %s\nemit &buf\n' % host(1, 64 * k) for k in range(3)) + 'halt\n',
        'sizes': (':x data 200 "abcdefghijklmnopqrstuvwxy"\n:w data 200 0\n:v data 120 0\n:u data 8 0\n:main block\n'
                  'copy %(a)s &x\ncopy &w %(a)s\nemit &w\ncopy &v[0:117] %(a)s\nemit &v[0:112]\n'
                  'copy &v[0:116] %(a)s\nemit &v[0:112]\ncopy %(a)s &x[0:1]\ncopy &u[0:5] %(a)s\nemit &u\n'
                  'copy %(b)s &x[8:13]\ncopy &u %(b)s\nemit &u\nhalt\n') % {'a': host(1, 2), 'b': host(1, 7)},
        'outside': (':x data 16 "ab"\n:z data 16 "\\0\\0"\n:main block\ncopy %(a)s &x\ncopy &z %(a)s\nemit &z\ncopy &z %(b)s\nemit &z\nhalt\n')
                   % {'a': host(1, 1 << 20), 'b': host(17, 1 << 20)},
        'clock': (':t1 data 64 0\n:t2 data 64 0\n:c data 17 0\n:y data 8 "Y"\n:n data 8 "N"\n:main block\ncopy &t1 %(a)s\n'
                  'copy &t2 %(a)s\nlt &t2 &t1 &c\nif &c[16] &no &yes\n:yes block\nemit &y\nhalt\n:no block\nemit &n\nhalt\n') % {'a': host(0, 0)},
    }
    out = [('program-' + k, v) for k, v in programs.items()]
    with open(os.path.join(common.HERE, 'README.md'), encoding='utf-8') as h:
        doc = h.read()
    example = re.search(r'### 3\.5\..*?```tw\n(.*?)```', doc, re.S).group(1)
    out.append(('readme-example', example))
    out.append(('readme-example-packed', 'pack\n' + example))
    edges = [
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
    far_edges = [
        (':x data 64 0\n:y data 8 0\n:z data 16 0\n:main block\ncopy &x {a}\ncopy {a} &x\ncopy &y {a}\ncopy {a} &z\nhalt\n'.format(a=FAR)).encode(),
        ':x data 64 0\n:main block\ncopy &x[8:24] {a}\ncopy {a} &x[32:64]\ncopy &x[0:8] {b}\nhalt\n'.format(a=FAR, b=farad(8 * 255)).encode(),
        ':x data 64 0\n:main block\ncopy &x {a}\ncopy {a} &x\nhalt\n'.format(a=farad(8 * (1 << 28) - 8 * 3)).encode(),
        ':x data 64 0\n:main block\ncopy &x {a}\ncopy {a} &x\ncopy &x {b}\nhalt\n'.format(a=farad(8 * 0xfff0), b=farad(8 * 0x7fffff8 - 8 * 100)).encode(),
        ':x data 64 0\n:b data 4 0\n:w data 72 0\n:t table 1 8 1 2\n:main block\ncopy &x {l}\ncopy {l} &x\ncopy &x {m}\ncopy {m} &x\ncopy &x {g}\ncopy {g} &x\ncopy &b {a}\n'
        'copy {a} &w\ncopy &t {a}\ncopy &q {a}\ncopy &x[3] {a}\ncopy &x[0:12] {a}\ncopy &x[5:5] {a}\ncopy {a} {a}\ncopy {a} {h}\ncopy {h} {a}\nhalt\n'.format(
            l=farad(0, 1), m=farad(12), g=farad(1 << 32), a=FAR, h=HOSTA).encode(),
        ':x data 8 0\n:main block\ncopy &x 0x2{d31}\ncopy &x 0x2{d33}\ncopy &x 0x2000\ncopy &x 0x2\ncopy &x 0X2{d32}\ncopy &x 0x3{d32}\ncopy &x 0x2{d32}g\nhalt\n'.format(
            d31='0' * 31, d32='0' * 32, d33='0' * 33).encode(),
        b':x data 16 0\n:main block\ncopy &x ' + FAR.encode() + b'  # copy &x ' + FAR.encode() + b'\n:s data 8 "copy &x ' + FAR.encode() + b'"\ncopy ' + FAR.encode() + b'\n',
        b'copy &x ' + FAR.encode(), b':x data 16 0\ncopy &x ' + FAR.encode(), b':x data 16 0\ncopy ' + FAR.encode() + b' &x',
        b':x data 8 0\n:main block\ncopy +2 ' + FAR.encode() + b'\n',
        b'pack\n:x data 24 0\n:main block\ncopy &x ' + FAR.encode() + b'\ncopy ' + FAR.encode() + b' &x\nhalt\n',
        b':x data 9000 0\n:y data 16 0\n:main block\ncopy &x[9890:9906] ' + FAR.encode() + b'\ncopy &x[9899:9915] ' + FAR.encode() + b'\ncopy &x[9900:9916] '
        + FAR.encode() + b'\ncopy &y ' + FAR.encode() + b'\n',
    ]
    chan_forms = ':a data 8 "A"\n:e data 8 "E"\n:b data 8 0\n:main block\ncopy +2 &a\ncopy +3 &e\ncopy &b +1\ncopy +2 &b\ncopy +3 &b\nhalt\n'
    chan_words = ':a data 8 "A"\n:e data 8 "E"\n:b data 8 0\n:main block\nemit &a\nwarn &e\nkey &b\nemit &b\nwarn &b\nhalt\n'
    chan_edges = [
        b':a data 8 0\n:main block\ncopy +2 &a\ncopy &a +1\ncopy +0 &a\ncopy +3 &a  # c\n:t data 8 "copy +2 &a"\n', b'copy +2', b'copy +2 +3', b'copy +5 +4 copy +1 +2',
        b':a data 8 0\n:main block\ncopy +6 &a\ncopy +12 &a\ncopy + &a\ncopy +a &a\ncopy -2 &a\ncopy ++ &a\ncopy &a[0:4] +4\n',
        b':a data 8 0\n:main block\ncopy +2 ' + HOSTA.encode() + b'\ncopy ' + HOSTA.encode() + b' +1\ncopy &a ' + HOSTA.encode() + b'\n',
        b'pack\n:a data 8 0\n:main block\ncopy +2 &a\nhalt\n', b':a data 8 "+2"\n:main block\ncopy  +2   &a   copy &a\t+1\n',
    ]
    for k, b in enumerate(edges):
        out.append(('edge-%02d' % k, b))
    for k, b in enumerate(far_edges):
        out.append(('far-%02d' % k, b))
    for k, b in enumerate(chan_edges):
        out.append(('channel-%02d' % k, b))
    out.append(('channel-forms', chan_forms))
    out.append(('channel-words', chan_words))
    out.append(('channel-all-k', ':a data 8 0\n:main block\ncopy +2 &a\ncopy &a +1\ncopy +3 &a\ncopy +4 &a\ncopy +5 &a\ncopy +0 &a\n'))
    out.append(('channel-string', ':t data 8 "copy +2 &a" # copy +2 &a\n'))
    out.append(('string-comment', ':a data 8 "copy &a 0x1"\n:out data 40 "hello"  # x\n:main block\ncopy &a %s\n  copy %s &out[0:8]\nhalt\n' % (HOSTA, HOSTA)))
    for k, tail in enumerate((':main block\ncopy 0x1 0x1\n', ':a data 8 0\n:main block\ncopy &a &a\n', ':t table 1 8 1 2\n:main block\ncopy &t %s\n' % HOSTA,
                              ':main block\ncopy &q %s\n' % HOSTA, ':c data 2049 0\n:main block\ncopy &c %s\n' % HOSTA,
                              ':c data 8 0\n:main block\ncopy &c[3:3] %s\n' % HOSTA)):
        out.append(('unchanged-%d' % k, tail))
    pre = ':x data 64 0\n:b data 4 0\n:y data 9000 0\n:t table 1 8 1 2\n:main block\n'
    reasons = ['&x %s' % farad(0, 1), '%s &x' % farad(5, 7), '&x %s' % farad(12), '%s &x' % farad(1 << 32), '&x %s' % farad(1 << 64), '&x %s' % farad(8 * 3 + 4),
               '&b %s' % FAR, '&x[3] %s' % FAR, '&t %s' % FAR, '&q %s' % FAR, '%s &x[0:12]' % FAR, '%s %s' % (FAR, FAR), '%s %s' % (FAR, HOSTA),
               '&y[9900:9908] %s' % FAR, '%s &y[9950:9958]' % FAR]
    for k, pair in enumerate(reasons):
        out.append(('far-refusal-%02d' % k, pre + 'copy %s\nhalt\n' % pair))
    out.append(('far-refusal-among', pre + 'copy &t %s\ncopy %s &x\n' % (HOSTA, farad(12))))
    out.append(('far-257', ':x data 64 0\n:main block\n' + 'copy &x %s\n' % FAR * 257))
    out.append(('far-with-host', programs['rw'] + '\n' + far_edges[0].decode()))

    def name_hash(name):
        h = 0
        for c in name.encode():
            h = (h * 8 + c) & 4095
        return h

    def names_program(names, widths):
        a = host(1, 8)
        return (''.join(':%s data %d 0\n' % (n, w) for n, w in zip(names, widths, strict=True)) + ':main block\n'
                + ''.join('copy &%s %s\ncopy %s &%s[1:3]\n' % (n, a, a, n) for n in names) + 'halt\n')
    by = {}
    for a in 'abcdefghijklmnopqrstuvwxyz':
        for b in 'abcdefghijklmnopqrstuvwxyz':
            for c in 'abcdefghijkl':
                by.setdefault(name_hash(a + b + c), []).append(a + b + c)
    groups = [v for v in by.values() if len(v) >= 4][:6]
    names = [n for g in groups for n in g[:4]]
    out.append(('hash-names', names_program(names, list(range(5, 5 + len(names))))))
    out.append(('hash-names-twice', names_program(names + names[::-1], list(range(5, 5 + 2 * len(names))))))
    rng = random.Random(2531)
    for k in range(4):
        pool = [n for g in groups for n in g] + [''.join(rng.choice('abxyz_09') for _ in range(rng.randrange(1, 15))) for _ in range(10)]
        nm = [n for n in rng.sample(pool, 30) if n[0] not in '0123456789']
        out.append(('hash-names-random-%d' % k, names_program(nm, [rng.randrange(1, 300) for _ in nm])))
    out.append(('names-70', names_program(['n%d' % i for i in range(70)], [8] * 70)))

    def spoiled(seed, bases, count, a1, a2):
        rng = random.Random(seed)
        for k in range(count):
            b = bytearray(rng.choice(bases))
            for _ in range(rng.choice((1, 2, 3))):
                i = rng.randrange(len(b))
                m = rng.randrange(3)
                if m == 0:
                    b[i] = rng.choice(a1)
                elif m == 1:
                    del b[i]
                else:
                    b.insert(i, rng.choice(a2))
            yield k, bytes(b).replace(b'\0', b' ')
    for k, b in spoiled(2644, far_edges[:6], 30, b'0123456789abcdefx&[]:# "\n\\', b'02x&[]: "\n\\#'):
        out.append(('far-mutation-%02d' % k, b))
    for k, b in spoiled(2317, [edges[9], edges[10], edges[12], programs['rw'].encode()], 30, b'0123456789abcdefx&[]:# "\n\\', b'0x&[]: "\n\\#'):
        out.append(('mutation-%02d' % k, b))
    return [(n, s.encode('latin-1') if isinstance(s, str) else s) for n, s in out]


def reference(pas, text, mode):
    """(output, stderr) of the Python reference of a pass for an input; stderr is None for l4c (the reference has none of its own)."""
    import l2ltext
    import l2text
    import l3ctext
    if pas == 'seed':
        o, err = l1text.encode(text)
        return o, l1text.MESSAGES.get(err, '')
    if pas == 'l2c':
        o, err = l2text.encode(text)
        return o, l2text.MESSAGES.get(err, '')
    if pas == 'l2l':
        o, err = l2ltext.encode(text, twice=True) if mode == 'twice' else l2ltext.encode(text)
        return o, l2ltext.MESSAGES.get(err, '')
    if pas == 'l3c':
        o, err = l3ctext.encode(text)
        return o, l3ctext.MESSAGES.get(err, '')
    if pas == 'l3p':
        o, err = l3ctext.pack_pass(text)
        return o, l3ctext.PMESSAGES.get(err, '')
    return l3ctext.l4c(text + b'\0')[0], None


def update():
    """Write tower/golden/*.jsonl: the expected values from the Python references, the exit code (and the stderr of l4c) from the chain, then compare
    the chain with the references and tell the differences (not repaired)."""
    entries = [dict(pas=p, name=n, text=t, mode=m) for p, n, t, m in cases()]
    keys = [(e['pas'], e['name']) for e in entries]
    assert len(set(keys)) == len(keys), [k for k in keys if keys.count(k) > 1]
    os.makedirs(os.path.join(GOLDEN, 'in'), exist_ok=True)
    for f in os.listdir(os.path.join(GOLDEN, 'in')):
        os.remove(os.path.join(GOLDEN, 'in', f))
    t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        runs = list(ex.map(lambda e: chain_run(e['pas'], e, e['text']), entries))
    refs = [reference(e['pas'], e['text'], e['mode']) for e in entries]
    diffs, files = [], {p: [] for p in PASSES}
    for e, r, (out, err) in zip(entries, runs, refs, strict=True):
        pas = e['pas']
        if err is None:
            err = says(r)
        if (pas, e['name']) in CHAIN_ONLY:
            out = r.out
        if r.out != out or says(r) != err:
            diffs.append('%s %s: chain out %d bytes %s, reference %d bytes %s; stderr %r vs %r' % (
                pas, e['name'], len(r.out), sha(r.out)[:10], len(out), sha(out)[:10], says(r), err))
        fast = pas in ('seed', 'l2c', 'l2l', 'l3c') and r.ticks <= FAST_TICKS
        line = {'name': e['name']}
        if e['mode']:
            line['mode'] = e['mode']
        text = e['text']
        if len(text) <= INLINE_IN:
            line['in'] = text.decode('latin-1')
        else:
            src = None
            for f in ('seed.l1', 'l2c.l2', 'l2l.l2', 'hello.l2', 'hello_names.l2', 'l2c.l1', 'l2l.l1'):
                if text == read(f):
                    src = 'programs/' + f
            if src is None:
                src = 'in/%s-%s.txt' % (pas, e['name'])
                with open(os.path.join(GOLDEN, src), 'wb') as h:
                    h.write(text)
            line['file'] = src
        line['rc'] = r.rc
        line['err'] = err
        if len(out) <= INLINE_OUT:
            line['out'] = out.decode('latin-1')
        else:
            line['len'], line['sha'] = len(out), sha(out)
        if not fast:
            line['long'] = True
        files[pas].append(line)
    for pas in PASSES:
        with open(os.path.join(GOLDEN, pas + '.jsonl'), 'w', encoding='utf-8') as h:
            for line in files[pas]:
                h.write(json.dumps(line, separators=(',', ':')) + '\n')
    n = {p: (sum(1 for x in files[p] if not x.get('long')), sum(1 for x in files[p] if x.get('long'))) for p in PASSES}
    sys.stderr.write('golden: %s (fast, long) in %.0f s\n' % (n, time.time() - t0))
    sys.stderr.write('%d differences chain/reference%s\n' % (len(diffs), ''.join('\n  ' + d for d in diffs)))
    return diffs


if __name__ == '__main__':
    if os.environ.get('GOLDEN_UPDATE'):
        common.ensure_built()
        sys.exit(1 if update() else 0)
    unittest.main()
