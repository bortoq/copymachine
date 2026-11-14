"""The proof of a level (23.21, 7.2.35): the word `copy n d s` of language 2, defined by the row `r d d+n s s+n`, checked against
its promise on the emulator. The harness only builds texts and compares bytes; the work is done by the chain on the emulator:
text of language 2 -> l2c (image) -> language 1 text -> seed (image) -> emulator (checked). Python is the oracle (the promise).

The promise of `copy n d s` (positions in bits, S the number of positions, A the width of a field, S < 2^A <= 2^20):
  domain: 0 < n, 0 <= d, s, d+n <= S, s+n <= S, [d,d+n) and [s,s+n) disjoint, and no other row of the same tick touches them
          (the contract of the emulator: every active interval of a tick is disjoint, source/source too);
  promise: after the tick, bits [d,d+n) equal the earlier bits [s,s+n), every other bit is as it was;
  n = 0 is a NOP (nothing changes), if d and s are not both S (two channel codes).
The program of a case (layout, bits): 0..8A the processor (2 rows), the rest of the image is 3 layers of 2 rows,
  L0 loads the window [b,b+W) from stdin and jumps to L1, L1 is the word under test and a jump to L2, L2 writes the window to
  stdout; -t 5 stops after the tick of L2 (ticks: boot, install, L0, L1, L2).
Contents of the window are on stdin after the image, so one chain run (l2c, seed) serves every content.
Parametricity: the emulator moves bits and does not read them, so the promise for all 2^W contents is the promise for the
routing; a content with the bit k of the position number in every position (k < K, 2^K >= W), the all-zero content and the
all-one content read the routing off: out[j] = in[sigma(j)] with sigma(j) = the number of the code, or a constant."""
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common
import l1text
from common import run

PROGRAMS = os.path.join(common.HERE, 'programs')
LIMIT = 40 * 10 ** 6
TICKS = 5


def h(x):
    return '%x' % x


def read(name):
    with open(os.path.join(PROGRAMS, name), 'rb') as f:
        return f.read()


class Tools:
    """seed.img (the first one by l1text, as in test_l2c) and l2c.img (made by the seed on l2c.l1: the chain)."""

    def __init__(self, build=True):
        if build:
            common.ensure_built()
        self.seed = l1text.encode(read('seed.l1'))[0]
        r = run(self.seed, 16, 7, checked=False, limit=LIMIT, stdin=read('l2c.l1') + b'\0')
        assert r.rc == 0, r.err
        self.l2c = r.out

    def l2(self, text):
        """Text of language 2 -> text of language 1 (the chain, l2c: A=18, P=19)."""
        r = run(self.l2c, 18, 19, checked=False, limit=LIMIT, stdin=text.encode() + b'\0')
        assert r.rc == 0 and 'l2: ' not in r.err, (text, r.err)
        return r.out

    def l1(self, text1):
        """Text of language 1 (with its zero byte) -> image (the chain, seed: A=16, P=7)."""
        r = run(self.seed, 16, 7, checked=False, limit=LIMIT, stdin=text1)
        assert r.rc == 0 and 'l1: ' not in r.err, (text1, r.err)
        return r.out


def program(A, b, W, n, d, s):
    """The text of language 2 of the case; the word under test is the line `c n d s`."""
    S = 2 ** A - 6
    return '\n'.join((
        'w %s' % h(A),
        'r 0 %s %s %s' % (h(24 * A), h(S + 1), h(S + 1)),          # boot: install the rest of the image
        'z %s' % h(4 * A),
        'o',
        'r %s %s %s %s' % (h(b), h(b + W), h(S + 1), h(S + 1)),    # L0: the window from stdin
        'c %s 0 %s' % (h(8 * A), h(8 * A)),                        # L0: jump to L1
        'c %s %s %s' % (h(n), h(d), h(s)),                         # L1: the word under test
        'c %s 0 %s' % (h(8 * A), h(16 * A)),                       # L1: jump to L2
        'r %s %s %s %s' % (h(S + 2), h(S + 2), h(b), h(b + W)),    # L2: the window to stdout
        'z %s' % h(4 * A))) + '\n'


def pack(bits):
    out = bytearray(len(bits) // 8)
    for i, v in enumerate(bits):
        if v:
            out[i >> 3] |= 128 >> (i & 7)
    return bytes(out)


def unpack(bs):
    return [bs[i >> 3] >> (7 - (i & 7)) & 1 for i in range(8 * len(bs))]


def contents(W, rnd=None, nrandom=0):
    """The contents of the window: zeros, ones, the planes of the position number, random ones."""
    K = max(1, (W - 1).bit_length())
    cs = [[0] * W, [1] * W] + [[i >> k & 1 for i in range(W)] for k in range(K)]
    if nrandom:
        cs += [[rnd.getrandbits(1) for _ in range(W)] for _ in range(nrandom)]
    return cs


def route(bits, n, d, s):
    """The promise as a function: window bits (d, s are offsets from the window start) -> bits after the tick."""
    out = list(bits)
    out[d:d + n] = bits[s:s + n]
    return out


def check_case(tools, A, b, W, n, d, s, rnd=None, nrandom=0, text=None):
    """Chain, emulator, comparison. Returns None if the promise holds, else a text of the difference.
    text: a program other than the standard one (a test of the test: a wrong word must be found)."""
    img = tools.l1(tools.l2(text or program(A, b, W, n, d, s)))
    S = 2 ** A - 6
    cs = contents(W, rnd, nrandom)
    tag = 'A=%d b=%d W=%d n=%d d=%d s=%d' % (A, b, W, n, d, s)
    res = []
    for c in cs:
        r = run(img, A, 2, checked=True, limit=TICKS, stdin=pack(c))
        if r.rc != 0 or r.ticks != TICKS or len(r.out) != W // 8:
            return '%s: rc=%d ticks=%s out=%d %s' % (tag, r.rc, r.ticks, len(r.out), r.err[:200])
        res.append(unpack(r.out))
    # the routing: out[j] = in[sigma(j)] must be the promise's sigma(j) (and no constants)
    zero, one, planes = res[0], res[1], res[2:len(cs) - nrandom]
    want = route(list(range(W)), n, d - b, s - b)
    for j in range(W):
        code = sum(p[j] << k for k, p in enumerate(planes))
        if zero[j] != 0 or one[j] != 1 or code != want[j]:
            return '%s: bit %d is %d/%d/%d, want the copy of %d (S=%d)' % (tag, j, zero[j], one[j], code, want[j], S)
    for c, o in zip(cs[len(cs) - nrandom:], res[len(cs) - nrandom:], strict=True):
        if o != route(c, n, d - b, s - b):
            return '%s: random content differs' % tag
    return None


def valid_cases(W, b=0):
    """All (n, d, s) with 0 < n, the intervals inside [b, b+W] and disjoint."""
    for n in range(1, W // 2 + 1):
        for d in range(b, b + W - n + 1):
            for s in range(b, b + W - n + 1):
                if abs(d - s) >= n:
                    yield n, d, s


def overlapping_cases(W, b=0):
    for n in range(2, W + 1):
        for d in range(b, b + W - n + 1):
            for s in range(b, b + W - n + 1):
                if 0 < abs(d - s) < n:
                    yield n, d, s


_tools = None


def _init():
    global _tools
    _tools = Tools(build=False)


def _work(args):
    A, b, W, cases, seed, nrandom = args
    rnd = random.Random(seed)
    return [x for x in (check_case(_tools, A, b, W, *c, rnd=rnd, nrandom=nrandom) for c in cases) if x]


def sweep(tools, A, b, W, cases, threads=4, rnd=None, nrandom=0, procs=0):
    """Check all cases; returns (number of cases, list of failures). procs > 0: that many processes (large sweeps; the
    threads of one process wait for each other in Python), else threads."""
    cases = list(cases)
    if procs:
        chunks = [cases[i:i + 200] for i in range(0, len(cases), 200)]
        with ProcessPoolExecutor(procs, initializer=_init) as ex:
            out = [x for r in ex.map(_work, [(A, b, W, c, i, nrandom) for i, c in enumerate(chunks)]) for x in r]
        return len(cases), out
    with ThreadPoolExecutor(threads) as ex:
        out = list(ex.map(lambda c: check_case(tools, A, b, W, *c, rnd=rnd, nrandom=nrandom), cases))
    return len(cases), [x for x in out if x]


def rejected(tools, A, b, W, n, d, s):
    """The checked emulator on a case outside the domain (overlap): its return code and the report."""
    img = tools.l1(tools.l2(program(A, b, W, n, d, s)))
    r = run(img, A, 2, checked=True, limit=TICKS, stdin=pack([1, 0] * (W // 2)))
    return r.rc, r.err[:100]


def nop_case(tools, A, d, s):
    """n = 0, d and s anywhere in [0,S]: the program runs and the window is unchanged. Returns (rc, ok)."""
    b, W = 24 * A, 16
    img = tools.l1(tools.l2(program(A, b, W, 0, d, s)))
    c = pack([1, 0] * (W // 2))
    r = run(img, A, 2, checked=True, limit=TICKS, stdin=c)
    return r.rc, r.out == c


def expected_text(n, d, s):
    """What l2c must write for `c n d s` (sums modulo 2^20, hex without leading zeros)."""
    m = (1 << 20) - 1
    return 'r %s %s %s %s\n' % (h(d), h((d + n) & m), h(s), h((s + n) & m))


def l2c_lines(tools, triples):
    """One l2c run over many `c n d s` lines, compared with the formula. Returns the mismatches (at most 5)."""
    text = ''.join('c %s %s %s\n' % (h(n), h(d), h(s)) for n, d, s in triples)
    out = tools.l2(text).decode()
    want = ''.join(expected_text(*t) for t in triples)
    if out == want + '\0':
        return []
    ol, wl = out.split('\n'), want.split('\n')
    return [(w, o) for w, o in zip(wl, ol, strict=False) if w != o][:5] or [('length', len(out))]


def carry_triples():
    """Every pattern of one nibble step at each of the five positions: the digits (a, b) and the carry in (the lower nibble f+1)."""
    out = []
    for k in range(5):
        for a in range(16):
            for bb in range(16):
                for cin in (0, 1):
                    if cin and k == 0:
                        continue
                    d, n = a << 4 * k, bb << 4 * k
                    if cin:
                        d |= 0xf << 4 * (k - 1)
                        n |= 1 << 4 * (k - 1)
                    out.append((n, d, (a ^ 0xa) << 4 * k))
    return out


def seed_encoding(tools, rnd):
    """The seed writes a field as the low A bits of the number, the lowest first, for every A: compared with the contract."""
    bad = []
    for A in range(1, 25):
        vals = {0, 0xfffff, 2 ** A - 1 & 0xfffff} | {1 << k for k in range(min(A + 1, 20))} | {rnd.getrandbits(20) for _ in range(8)}
        rows = sorted(vals)
        rows += [0] * (-len(rows) % 4)
        text = 'w %s\n' % h(A) + ''.join('r %s %s %s %s\n' % tuple(h(v) for v in rows[i:i + 4]) for i in range(0, len(rows), 4))
        bits = []
        for v in rows:
            bits += [v >> k & 1 for k in range(A)]
        if len(bits) % 8:
            text += 'z %s\n' % h(8 - len(bits) % 8)
            bits += [0] * (8 - len(bits) % 8)
        if tools.l1(text.encode() + b'\0') != pack(bits):
            bad.append(A)
    return bad
