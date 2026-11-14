"""Tests of the proof of the output of a pass through the channel (25.7.2, 7.2.45): the program tower/programs/prove/provepass.tw (language 3) is the second space; its stdin
is the stdout of the first space, where a pass of the chain (seed, l2c) runs on a frozen input of tower/golden. Before the stream the test sends it the value known in advance:
n (24 bits, the length), s1 (32 bits, the sum of the bytes, the cells' values) and s2 (32 bits, the sum of the values of s1), all computed here from the frozen output of the
manifest (not from the run); the program counts the same three numbers of the stream, compares and says `proved n s1 s2` or `not proved n s1 s2` on stderr (the numbers it got, hex).
The two processes are connected by os.pipe through a go-between (a thread of this test): it records the stream and can change a byte, cut the stream or add bytes to its end.
Both run on the checked emulator (it counts ticks); a common deadline, no pauses: the test waits for the end of the processes and kills them at the deadline.
Python is here only: the program is language 3 (the passes are images of the chain, made as in test_golden.py; the prover is built by text.py, one test builds it by the chain too).
The measure (class Measure) prints a table to stderr.
Run: make check-tower  or  python3 -B tower/tests/test_provepass.py"""
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain
import common
import test_golden as golden
import text
from common import rev, stream
from golden_programs import hoist

PROGRAM = os.path.join(common.HERE, 'programs', 'prove', 'provepass.tw')
WORKERS = 4
TIMEOUT = 60                                  # seconds for a pair: far above the work (about a second); a hang is an error
# the frozen inputs (entries of golden/<pass>.jsonl with the output whole): empty, tiny, and the largest outputs (up to 1.7 KB)
CASES = {
    'seed': ['small-12', 'small-11', 'program-echo', 'program-and_hex', 'program-branch', 'program-loop_digits', 'program-add16_hex', 'program-arith8', 'program-array'],
    'l2c': ['small-20', 'small-16', 'small-25', 'random-03', 'random-13', 'random-14', 'hello.l2', 'program-echo'],
}
_CACHE = {}


def setUpModule():
    common.ensure_built()


def sums(data):
    """(n, s1, s2) of the stream: the cells' values (the byte with its bits reversed), n mod 2^24, the sums mod 2^32."""
    n = s1 = s2 = 0
    for b in data:
        s1 = (s1 + rev(b, 8)) & 0xFFFFFFFF
        s2 = (s2 + s1) & 0xFFFFFFFF
        n += 1
    return n & 0xFFFFFF, s1, s2


def known(data):
    """What the prover is told in advance: the three numbers of `data` as `key` stores them."""
    n, s1, s2 = sums(data)
    return stream(n, 24) + stream(s1, 32) + stream(s2, 32)


def message(verdict, data):
    return ('%s %06x %08x %08x\n' % ((verdict,) + sums(data))).encode()


def prover():
    """(image, A, P) of the committed program built by text.py (the smallest A)."""
    if 'py' not in _CACHE:
        with open(PROGRAM, encoding='utf-8') as h:
            p, errs = text.compile_text(h.read())
        assert not errs, errs
        _CACHE['py'] = (p.stats['image'], p.stats['A'], p.stats['P'])
    return _CACHE['py']


def command(img_a_p):
    _, A, P = img_a_p
    return [common.CHK, '-s', str(2 ** A - 6), '-p', str(P), '-t', '0']


def entry(pas, name):
    for e in golden.load(pas):
        if e['name'] == name:
            assert 'out' in e, (pas, name)
            return e
    raise AssertionError((pas, name))


def frozen(pas, name):
    """(the entry, the frozen output as bytes)."""
    e = entry(pas, name)
    return e, e['out'].encode('latin-1')


def write_all(fd, data):
    while data:
        data = data[os.write(fd, data):]


def relay(src, dst, fault, log, tail):
    """The go-between: the bytes of src go to dst; fault(i, byte) gives the byte to send (the byte number i, from 0), None cuts: that byte and all after it are dropped;
    log gets the bytes as they came; at the end of src the `tail` is added and dst is closed."""
    n = 0
    try:
        while True:
            chunk = os.read(src, 4096)
            if not chunk:
                break
            out = bytearray()
            for b in chunk:
                log.append(b)
                f = fault(n, b)
                n += 1
                if f is None:
                    return
                out.append(f)
            try:
                write_all(dst, bytes(out))
            except OSError:
                pass
        try:
            write_all(dst, tail)
        except OSError:
            pass
    finally:
        os.close(dst)
        os.close(src)


def audit(err):
    """(the program's own stderr, the ticks of the checked emulator)."""
    m = re.search(rb'VM1_AUDIT_TICKS=(\d+)', err)
    return err.split(b'VM1_AUDIT')[0], int(m.group(1)) if m else None


def prove(pas, name, told=None, fault=lambda i, b: b, tail=b'', image=None, timeout=TIMEOUT):
    """The pass `pas` on the frozen input `name` (first space) and the prover (second space), connected through the go-between. `told` is what the prover is told in advance
    (default: the numbers of the frozen output). Returns a dict: msg (stderr of the prover), prc, rc (of the pass), ticks of both, stream (what the pass wrote)."""
    e, out = frozen(pas, name)
    pimg = image or prover()
    told = known(out) if told is None else told
    pass_img = golden.tool(pas)
    pass_in = pass_img[0] + golden.stdin_of(pas, e, golden.text_of(e))
    i_r, i_w = os.pipe()                                 # the text -> pass.stdin
    a_r, a_w = os.pipe()                                 # pass.stdout -> go-between
    b_r, b_w = os.pipe()                                 # go-between -> prover.stdin
    procs, log, threads = [], bytearray(), []
    try:
        a = subprocess.Popen(command(pass_img), stdin=i_r, stdout=a_w, stderr=subprocess.PIPE)
        procs.append(a)
        p = subprocess.Popen(command(pimg), stdin=b_r, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        procs.append(p)
        for fd in (i_r, a_w, b_r):
            os.close(fd)
        write_all(i_w, pass_in)
        os.close(i_w)
        write_all(b_w, pimg[0] + told)                   # the image and what is known in advance; the stream follows
        t = threading.Thread(target=relay, args=(a_r, b_w, fault, log, tail), daemon=True)
        t.start()
        threads.append(t)
        end, res = time.monotonic() + timeout, []
        for q in procs:
            try:
                _, err = q.communicate(timeout=max(0.1, end - time.monotonic()))
            except subprocess.TimeoutExpired:
                raise AssertionError('the process did not finish in %d s (a blocked read): killed' % timeout) from None
            res.append((q.returncode, err))
        for t in threads:
            t.join(5)
    finally:
        for q in procs:
            if q.poll() is None:
                q.kill()
                q.communicate()
    (arc, aerr), (prc, perr) = res
    msg, pticks = audit(perr)
    _, aticks = audit(aerr)
    return dict(msg=msg, prc=prc, rc=arc, pticks=pticks, aticks=aticks, stream=bytes(log), out=out)


def every_case():
    return [(pas, name) for pas, names in CASES.items() for name in names]


def many(jobs):
    """Run the pairs (a list of (pas, name, kwargs of prove)) in WORKERS threads; the results in the order of the jobs."""
    with ThreadPoolExecutor(WORKERS) as ex:
        return list(ex.map(lambda j: prove(j[0], j[1], **j[2]), jobs))


def rejected(msg):
    """(the verdict is `not proved`, the length it got) of a message."""
    m = re.match(rb'not proved ([0-9a-f]{6}) ([0-9a-f]{8}) ([0-9a-f]{8})\n$', msg)
    return (m is not None, int(m.group(1), 16) if m else None)


class Proof(unittest.TestCase):
    def test_the_cases_are_whole(self):
        """5..10 inputs per pass, the outputs are in the manifest whole."""
        for pas, names in CASES.items():
            self.assertTrue(5 <= len(names) <= 10, pas)
            self.assertEqual(len(set(names)), len(names))
            for name in names:
                entry(pas, name)

    def test_the_frozen_outputs_are_proved(self):
        """The numbers computed by the test from the frozen output are what the prover counts in the stream of the pass: `proved`, with the numbers; the pass wrote exactly the frozen output."""
        cases = every_case()
        for (pas, name), r in zip(cases, many([(p, n, {}) for p, n in cases]), strict=True):
            with self.subTest(pas=pas, name=name):
                self.assertEqual((r['prc'], r['rc']), (0, entry(pas, name)['rc']))
                self.assertEqual(r['stream'], r['out'])
                self.assertEqual(r['msg'], message('proved', r['out']))

    def test_a_wrong_value_known_in_advance_is_not_proved(self):
        """The prover is told the numbers of another output (or of the same one with one more byte): not proved, and the numbers it got are those of the stream."""
        jobs, wants = [], []
        for pas, names in CASES.items():
            for name, other in zip(names, names[1:] + names[:1], strict=True):
                _, out = frozen(pas, name)
                jobs.append((pas, name, dict(told=known(frozen(pas, other)[1]))))
                wants.append((pas, name, out))
            jobs.append((pas, names[0], dict(told=known(frozen(pas, names[0])[1] + b'\0'))))
            wants.append((pas, names[0], frozen(pas, names[0])[1]))
        for (pas, name, out), r in zip(wants, many(jobs), strict=True):
            with self.subTest(pas=pas, name=name):
                self.assertEqual(r['msg'], message('not proved', out))

    def test_one_spoiled_byte_is_not_proved(self):
        """One byte of the stream is changed on the way (the first, one in the middle, the last; one bit or the whole byte): not proved, with the numbers of the spoiled stream or, when the
        spoiled stream has two bytes in a row equal to the preload (the end is taken too early), with a shorter length."""
        jobs, wants = [], []
        for pas, name in every_case():
            _, out = frozen(pas, name)
            for i, mask in sorted({(0, 0x01), (len(out) // 2, 0x01), (len(out) // 2, 0xFF), (len(out) - 1, 0x01)}):
                if 0 <= i < len(out):
                    bad = bytearray(out)
                    bad[i] ^= mask
                    jobs.append((pas, name, dict(fault=lambda n, b, i=i, mask=mask: b ^ mask if n == i else b)))
                    wants.append((pas, name, i, mask, bytes(bad)))
        for (pas, name, i, mask, bad), r in zip(wants, many(jobs), strict=True):
            with self.subTest(pas=pas, name=name, byte=i, mask=mask):
                ok, n = rejected(r['msg'])
                self.assertTrue(ok, r['msg'])
                self.assertTrue(r['msg'] == message('not proved', bad) or n < len(bad), r['msg'])

    def test_a_cut_stream_is_not_proved(self):
        """The stream is cut on the way (EOF earlier: in the middle, one byte short; the empty stream for the first input of a pass): not proved; the program ends, nothing hangs."""
        jobs, wants = [], []
        for pas, names in CASES.items():
            for name in names:
                _, out = frozen(pas, name)
                for keep in sorted({len(out) // 2, len(out) - 1} | ({0} if name == names[-1] else set())):
                    if 0 <= keep < len(out):
                        jobs.append((pas, name, dict(fault=lambda n, b, keep=keep: None if n >= keep else b)))
                        wants.append((pas, name, keep))
        for (pas, name, keep), r in zip(wants, many(jobs), strict=True):
            with self.subTest(pas=pas, name=name, kept=keep):
                ok, n = rejected(r['msg'])
                self.assertEqual((r['prc'], ok, n <= keep), (0, True, True), r['msg'])

    def test_a_longer_stream_is_not_proved(self):
        """The stream gets bytes at its end (a zero byte; a few for the first input of a pass): the length and the sums are not the known ones."""
        jobs, wants = [], []
        for pas, names in CASES.items():
            for name in names:
                _, out = frozen(pas, name)
                for tail in ((b'\0', b'\x00\xff\x01') if name == names[0] else (b'\0',)):
                    jobs.append((pas, name, dict(tail=tail)))
                    wants.append((pas, name, out + tail))
        for (pas, name, longer), r in zip(wants, many(jobs), strict=True):
            with self.subTest(pas=pas, name=name, longer=len(longer)):
                self.assertEqual(r['msg'], message('not proved', longer))

    def test_text_is_in_the_subset_of_l3c(self):
        """The chain compiler reads the prover (no word of Python only)."""
        with open(PROGRAM, encoding='utf-8') as h:
            out = chain.step('l3c', 'l3c', hoist(h.read()).encode('latin-1') + b'\0')      # a refusal (rc, a word on stderr) is an AssertionError
        self.assertGreater(len(out), 1000)

    def test_the_image_built_by_the_chain_proves_too(self):
        """The prover built by the chain itself (l3c -> l2l -> seed, the serial layout, A=20 P=2) gives the same answers on two outputs, right and spoiled."""
        image = chain_prover()
        for pas, name in (('seed', 'program-array'), ('l2c', 'hello.l2')):
            with self.subTest(pas=pas, name=name):
                r = prove(pas, name, image=image)
                self.assertEqual(r['msg'], message('proved', r['out']))
                r = prove(pas, name, image=image, fault=lambda n, b: b ^ 1 if n == 5 else b)
                bad = bytearray(r['out'])
                bad[5] ^= 1
                self.assertEqual(r['msg'], message('not proved', bytes(bad)))


def chain_prover():
    """(image, 20, 2) of provepass.tw by the chain (as test_golden builds l3p and l4c)."""
    if 'chain' not in _CACHE:
        with open(PROGRAM, 'rb') as h:
            src = h.read()
        l2 = golden._step('provepass l3c', golden.tool('l3c'), src + b'\0')
        l1 = golden._step('provepass l2l', golden.tool('l2l'), l2 + l2)
        _CACHE['chain'] = (golden._step('provepass seed', golden.tool('seed'), l1), 20, 2)
    return _CACHE['chain']


class Measure(unittest.TestCase):
    """The price of the proof (the ticks are counted by the checked emulator). The table goes to stderr; the bounds are loose."""

    def test_table(self):
        biggest = max(every_case(), key=lambda c: len(frozen(*c)[1]))
        _, out = frozen(*biggest)
        rows = []
        for label, image in (('text.py (packed, A=%d P=%d)' % prover()[1:], None), ('chain (serial, A=20 P=2)', chain_prover())):
            t0 = time.monotonic()
            r = prove(*biggest, image=image)
            self.assertEqual(r['msg'], message('proved', out))
            img = image or prover()
            rows.append((label, len(img[0]), r['pticks'], r['pticks'] / len(out), time.monotonic() - t0, r['aticks']))
        o = ['', 'prover                         image bytes   ticks of the proof   ticks per byte   seconds (pair)   (stream: %s %s, %d bytes, the pass itself: %d ticks)' % (
            biggest + (len(out), rows[0][5]))]
        for label, size, ticks, per, sec, _ in rows:
            o.append('%-30s %11d %20d %16.1f %16.2f' % (label, size, ticks, per, sec))
        big = 100 * 1024
        for label, _, _, per, _, _ in rows:
            o.append('%-30s a stream of 100 KB: %.1f million ticks' % (label, per * big / 1e6))
        sys.stderr.write('\n'.join(o) + '\n')
        for _, _, ticks, per, _, _ in rows:
            self.assertTrue(0 < ticks < 10 ** 6 and 30 < per < 400, (ticks, per))


if __name__ == '__main__':
    unittest.main()
