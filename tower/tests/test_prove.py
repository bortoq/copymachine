"""Tests of the proof of an associative space through the channel (28.1, 7.2.45): the program tower/programs/assoc/assoc_prove.tw (language 3) is the second
space; it is connected by two pipes to a definition of the associative space (assoc_hash.tw or assoc_tree.tw, the same protocol), sends it a script fixed in
advance (8 writes, K for all 256 keys, V for all 256 values, 5 more versions, K for all keys, 5 rollbacks, K and V again) and compares every answer with the value
known in advance; it says `proved` or `not proved at XXX` (the number of the first wrong answer, hex) on stderr. The unchanged prover proves both definitions.
The processes are connected by os.pipe through a go-between (the threads of this test: it records the traffic and can change a given answer byte); both run on the
checked emulator (it counts ticks); a common deadline, no pauses: the test waits for the end of the processes and kills them at the deadline. Python is here only:
the programs are language 3. The measure (class Measure) prints a table to stderr.
Run: make check-tower  or  python3 -B tower/tests/test_prove.py"""
import os
import random
import subprocess
import sys
import threading
import time

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import common
import l3ctext
import text
from common import rev, stream

PROGRAMS = os.path.join(HERE, '..', 'programs', 'assoc')
STOP, W, K, V, R = 0, 1, 2, 3, 4
ONES = 255
TIMEOUT = 60                                  # seconds for a pair: far above the work (about a second); a hang is an error
METHODS = ('hash', 'tree')
# the script of assoc_prove.tw (the same numbers; the test checks the traffic against them)
P1 = [(0, 0), (16, 17), (32, 34), (1, 3), (77, 77), (128, 1), (200, 100), (254, 254)]
P2 = [(16, 170), (77, 171), (1, 172), (254, 173), (99, 60)]
RB = [99, 254, 77, 1, 16]
SWEEP_K1, SWEEP_V1, SWEEP_K2, SWEEP_K3, SWEEP_V3 = 8, 8 + 256, 8 + 512 + 5, 8 + 512 + 5 + 256, 8 + 512 + 5 + 512
ANSWERS = 8 + 256 + 256 + 5 + 256 + 256 + 256
_CACHE = {}


def setUpModule():
    common.ensure_built()


def read_source(name):
    with open(os.path.join(PROGRAMS, name + '.tw'), encoding='utf-8') as h:
        return h.read()


def stats(name):
    """The committed program compiled by the Python reference (the smallest A): image, A, P."""
    if name not in _CACHE:
        p, errs = text.compile_text(read_source(name))
        assert not errs, errs
        _CACHE[name] = p.stats
    return _CACHE[name]


def command(name, limit=0):
    st = stats(name)
    return [common.CHK, '-s', str(2 ** st['A'] - 6), '-p', str(st['P']), '-t', str(limit)]


def script():
    """The script as the list of (op, key or value) and the expected answers: None for the answer of a write (a cell, any but all ones)."""
    ops, exp = [], []
    def write(k, v):
        ops.append((W, k, v))
        exp.append(None)

    def sweep(cmd, table):
        for x in range(256):
            ops.append((cmd, x, 0))
            exp.append(table.get(x, ONES))
    stacks = {}
    for k, v in P1:
        write(k, v)
        stacks.setdefault(k, []).append(v)
    top = lambda: {k: s[-1] for k, s in stacks.items()}
    inv = lambda: {s[-1]: k for k, s in stacks.items()}
    sweep(K, top())
    sweep(V, inv())
    for k, v in P2:
        write(k, v)
        stacks.setdefault(k, []).append(v)
    sweep(K, top())
    for k in RB:
        ops.append((R, k, 0))
        stacks[k].pop()
        if not stacks[k]:
            del stacks[k]
    sweep(K, top())
    sweep(V, inv())
    return ops, exp


OPS, EXPECTED = script()


def requests(ops, stop=True):
    """The bytes the prover sends: a command byte and its arguments as `key` stores them (the lowest bit first)."""
    out = bytearray()
    for op, a, b in ops:
        out += stream(op, 8) + stream(a, 8)
        if op == W:
            out += stream(b, 8)
    return bytes(out) + (stream(STOP, 8) if stop else b'')


def write_all(fd, data):
    while data:
        data = data[os.write(fd, data):]


def relay(src, dst, fault, log):
    """One direction: the bytes of src go to dst; fault(i, byte) gives the byte to send (the byte number i of this direction, from 0); log gets the bytes as they were;
    when fault returns None the byte and all after it are dropped and dst is closed (a definition which falls silent); at the end of src dst is closed."""
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
            except OSError:                              # the reader is gone: the rest is not carried
                pass
    finally:
        os.close(dst)
        os.close(src)


def audit(err):
    """(the program's own stderr, the ticks of the checked emulator)."""
    import re
    m = re.search(rb'VM1_AUDIT_TICKS=(\d+)', err)
    return err.split(b'VM1_AUDIT')[0], int(m.group(1)) if m else None


def prove(method, fault=lambda i, b: b, ask=lambda i, b: b, definition=None, timeout=TIMEOUT):
    """The prover and the definition (assoc_<method>) connected through the go-between: `fault` is applied to the answers (definition -> prover), `ask` to the requests.
    The image of each program goes first into its stdin. Returns a dict: msg (the stderr of the prover), rcs, ticks of both, the traffic (requests, answers)."""
    dname = definition or 'assoc_' + method
    d_in_r, d_in_w = os.pipe()                           # relay -> definition.stdin
    d_out_r, d_out_w = os.pipe()                         # definition.stdout -> relay
    p_in_r, p_in_w = os.pipe()                           # relay -> prover.stdin
    p_out_r, p_out_w = os.pipe()                         # prover.stdout -> relay
    procs = []
    reqs, ans = bytearray(), bytearray()
    try:
        d = subprocess.Popen(command(dname), stdin=d_in_r, stdout=d_out_w, stderr=subprocess.PIPE)
        procs.append(d)
        p = subprocess.Popen(command('assoc_prove'), stdin=p_in_r, stdout=p_out_w, stderr=subprocess.PIPE)
        procs.append(p)
        for fd in (d_in_r, d_out_w, p_in_r, p_out_w):
            os.close(fd)
        write_all(d_in_w, stats(dname)['image'])
        write_all(p_in_w, stats('assoc_prove')['image'])
        threads = [threading.Thread(target=relay, args=(d_out_r, p_in_w, fault, ans), daemon=True),
                   threading.Thread(target=relay, args=(p_out_r, d_in_w, ask, reqs), daemon=True)]
        for t in threads:
            t.start()
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
    (drc, derr), (prc, perr) = res
    msg, pticks = audit(perr)
    dmsg, dticks = audit(derr)
    return dict(msg=msg, drc=drc, prc=prc, dmsg=dmsg, dticks=dticks, pticks=pticks, requests=bytes(reqs), answers=bytes(ans))


def expected_msg(i):
    return b'not proved at %03x\n' % i


class Proof(unittest.TestCase):
    def test_the_script_is_what_the_prover_sends_and_the_definitions_answer_right(self):
        """The unchanged prover proves both definitions; its traffic is the script of this test and the answers of the definition are the model's (the writes: a cell 1..15)."""
        self.assertEqual(len(EXPECTED), ANSWERS)
        self.assertEqual(len(OPS), ANSWERS + len(RB))                  # the rollbacks have no answer
        for method in METHODS:
            with self.subTest(method):
                r = prove(method)
                self.assertEqual((r['prc'], r['drc'], r['msg']), (0, 0, b'proved\n'))
                self.assertEqual(r['requests'], requests(OPS))
                self.assertEqual(len(r['answers']), ANSWERS)
                cells = []
                for i, (got, want) in enumerate(zip((rev(b, 8) for b in r['answers']), EXPECTED, strict=True)):
                    if want is None:
                        self.assertTrue(1 <= got <= 15, (i, got))
                        cells.append(got)
                    else:
                        self.assertEqual(got, want, i)
                self.assertEqual(len(cells), len(P1) + len(P2))

    def test_one_spoiled_answer_the_first_difference_is_found(self):
        """One answer of the definition is changed on the way (a K or V answer: one bit; the answer of a write: all ones, the refusal): not proved at exactly that number, for both
        definitions; the prover then sends the stop and nothing more."""
        rng = random.Random(28)
        picks = [0, 7, SWEEP_K1, SWEEP_K1 + 1, SWEEP_K1 + 100, SWEEP_V1 - 1, SWEEP_V1, SWEEP_V1 + 17, SWEEP_V1 + 255, SWEEP_V1 + 256, SWEEP_V1 + 260,
                 SWEEP_K2, SWEEP_K2 + 99, SWEEP_K3, SWEEP_K3 + 254, SWEEP_V3, SWEEP_V3 + 255, ANSWERS - 1]
        picks += rng.sample(range(ANSWERS), 10)
        for method in METHODS:
            for i in picks:
                with self.subTest(method=method, answer=i):
                    flip = (lambda n, b, i=i: (ONES if EXPECTED[i] is None else b ^ 1) if n == i else b)
                    r = prove(method, fault=flip)
                    self.assertEqual((r['prc'], r['drc']), (0, 0))
                    self.assertEqual(r['msg'], expected_msg(i))
                    self.assertEqual(r['requests'], requests(OPS[:self.asked(i)]))

    @staticmethod
    def asked(i):
        """The number of the steps of OPS sent before the stop when the answer i is the first wrong: the request of the answer i is the last (rollbacks have no answer
        but they are before the request of the next answer)."""
        count = -1
        for j, (op, _, _) in enumerate(OPS):
            if op != R:
                count += 1
                if count == i:
                    return j + 1
        raise AssertionError(i)

    def test_the_two_answers_wrong_the_first_is_named(self):
        for method in METHODS:
            with self.subTest(method):
                r = prove(method, fault=lambda n, b: b ^ 0x80 if n in (300, 301, 900) else b)
                self.assertEqual(r['msg'], expected_msg(300))

    def test_a_definition_which_falls_silent_is_not_proved_at_the_first_present_key(self):
        """The answers stop after the answer number 20 (the channel is closed): a silent definition = the prohibitive price for every key; the keys which are not there
        answer so, therefore the first wrong one is the first present key (16: the answer 8 + 16 = 24); nothing hangs."""
        for method in METHODS:
            with self.subTest(method):
                r = prove(method, fault=lambda n, b: None if n >= 20 else b)
                self.assertEqual(r['msg'], expected_msg(SWEEP_K1 + 16))

    def test_no_definition_at_all(self):
        """The channel is closed from the start: the first write is not answered, not proved at 000."""
        for method in METHODS:
            with self.subTest(method):
                r = prove(method, fault=lambda n, b: None)
                self.assertEqual(r['msg'], expected_msg(0))

    def test_text_is_in_the_subset_of_l3c(self):
        """The chain compiler reads the prover (no word of Python only)."""
        out, err = l3ctext.encode(l3ctext.hoist(read_source('assoc_prove')))
        self.assertIsNone(err)
        self.assertGreater(len(out), 1000)


def alone_ticks(method, stdin):
    st = stats('assoc_' + method)
    r = common.run(st['image'], st['A'], st['P'], checked=True, stdin=stdin, limit=10 ** 8)
    assert r.rc == 0, (r.rc, r.err)
    return r.ticks


def lookup_costs(method, cmd):
    """The ticks of one lookup (cmd K: a key, V: a value) in the state after the first 8 writes, for all 256 arguments: the run with the lookup minus the run without it."""
    setup = requests(OPS[:len(P1)], stop=False)
    base = alone_ticks(method, setup + stream(STOP, 8))
    return [alone_ticks(method, setup + stream(cmd, 8) + stream(x, 8) + stream(STOP, 8)) - base for x in range(256)]


def worst_costs(method, cmd):
    """The worst case of the definition itself, not of the script: all 15 cells in one bucket of the hash (the keys, or the values, with the same low 4 bits) and the lookup of every
    one of them and of the free ones with the same low bits: the longest chain. The result: the largest ticks of one lookup."""
    mul = lambda j: (j << 4) + 3
    setup = b''
    for j in range(1, 16):
        k, v = (mul(j), 100 + j) if cmd == K else (j, mul(j))
        setup += stream(W, 8) + stream(k, 8) + stream(v, 8)
    base = alone_ticks(method, setup + stream(STOP, 8))
    xs = [mul(j) for j in range(16)] + [mul(16) & 255]
    return max(alone_ticks(method, setup + stream(cmd, 8) + stream(x, 8) + stream(STOP, 8)) - base for x in xs)


class Measure(unittest.TestCase):
    """The price of the definitions and of the proof (the ticks are counted by the checked emulator). The table goes to stderr; the bounds are loose."""

    def test_table(self):
        rows, proof = {}, {}
        for method in METHODS:
            r = prove(method)
            self.assertEqual(r['msg'], b'proved\n')
            kc, vc = lookup_costs(method, K), lookup_costs(method, V)
            whole = alone_ticks(method, requests(OPS))
            self.assertEqual(whole, r['dticks'], 'waiting for the channel costs no ticks: the pair and the replay agree')
            rows[method] = dict(whole=whole, k_worst=worst_costs(method, K), v_worst=worst_costs(method, V), k_avg=sum(kc) / 256, k_max=max(kc), v_avg=sum(vc) / 256, v_max=max(vc),
                                image=len(stats('assoc_' + method)['image']), A=stats('assoc_' + method)['A'], P=stats('assoc_' + method)['P'])
            proof = dict(ticks=r['pticks'], image=len(stats('assoc_prove')['image']), A=stats('assoc_prove')['A'], P=stats('assoc_prove')['P'])
        out = ['', 'definition  ticks on the whole proof (%d answers)   K lookup avg / worst   V lookup avg / worst   image bytes (A, P)' % ANSWERS]
        for m, x in rows.items():
            out.append('%-11s %10d %27.1f / %-6d %14.1f / %-6d %10d (%d, %d)' % (m, x['whole'], x['k_avg'], x['k_max'], x['v_avg'], x['v_max'], x['image'], x['A'], x['P']))
        for m, x in rows.items():
            out.append('%-11s the worst case of the definition itself (15 cells in one bucket): K %d, V %d' % (m, x['k_worst'], x['v_worst']))
        out.append('prover      ticks %d, image %d bytes (A=%d, P=%d)' % (proof['ticks'], proof['image'], proof['A'], proof['P']))
        sys.stderr.write('\n'.join(out) + '\n')
        for x in rows.values():
            self.assertTrue(0 < x['k_avg'] <= x['k_max'] < 5000 and 0 < x['v_avg'] <= x['v_max'] < 5000, x)
        self.assertTrue(0 < proof['ticks'] < 10 ** 6)


if __name__ == '__main__':
    unittest.main()
