"""Tests of the far copy (26.2, 26.3, 7.2.44): copying between two spaces = two running emulators connected by the shell: the stdout of one
is the stdin of the other (the image of the program goes first, then the stream). Programs (language 3, tower/programs/far/):
  far_a.tw, far_b.tw    26.2, no answerer: A copies four bytes from its memory to its stdout, B reads them from its stdin and prints them to stderr;
  far_serve.tw          26.3, the answerer: the window of 8 cells of 8 bits; the record of a request is 3 bytes: op (0 stop, 1 get, 2 put),
                        pos (8 bits; the window is pos < 8), dat (8 bits); get answers 1 byte (ones outside the window), put answers nothing;
                        the end of stdin is a stop;
  far_get.tw            the asker: sends get/put by hand, keeps the answers in its cells, sends op = 0, prints the cells to stderr.
The pair tests connect the processes by os.pipe (the pairs are created here and given to subprocess.Popen) with a timeout: a blocking read is not
stopped by the limit of ticks (-t), so the test kills the processes itself and fails; it never hangs. The single runs (one program, the stdin
made by the test) use the checked emulator and give the ticks. Python is here only: the programs are language 3.
Run: make check-tower  or  python3 -B tower/tests/test_far.py"""
import os
import random
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import common
import text
from common import rev, stream

PROGRAMS = os.path.join(HERE, '..', 'programs', 'far')
STOP, GET, PUT = 0, 1, 2
WINDOW = b'COPYMACH'                          # the initial window of far_serve.tw (8 cells of 8 bits)
ONES = b'\xff'                                # the prohibitive price: a byte of ones
A_VALUES = [165, 60, 1, 200]                  # far_a.tw: four values of 8 bits (numbers; the stream byte is the bits in memory order)
TIMEOUT = 20                                  # seconds for a pair: far above the work (milliseconds); a hang is an error
_CACHE = {}


def setUpModule():
    common.ensure_built()


def program(name):
    """The committed program name.tw compiled by the Python reference (the smallest A): its stats (image, A, P)."""
    if name not in _CACHE:
        with open(os.path.join(PROGRAMS, name + '.tw'), encoding='utf-8') as h:
            p, errs = text.compile_text(h.read())
        assert not errs, errs
        _CACHE[name] = p.stats
    return _CACHE[name]


def rec(op, pos, dat=0):
    """The record of a request: op, pos, dat, 3 bytes (the numbers as `key` stores them: the lowest bit first)."""
    return stream(op, 8) + stream(pos, 8) + stream(dat, 8)


def command(name, limit=0, checked=False):
    st = program(name)
    return [common.CHK if checked else common.EMU, '-s', str(2 ** st['A'] - 6), '-p', str(st['P']), '-t', str(limit)]


def single(name, stdin=b'', limit=2000000):
    """One space alone, the checked emulator: the image and then stdin (what a neighbour would send); the result has out, err, rc, ticks."""
    st = program(name)
    r = common.run(st['image'], st['A'], st['P'], checked=True, stdin=stdin, limit=limit)
    return r


def single_err(name, stdin=b'', limit=2000000):
    """The same, the stderr of the program as bytes (the audit lines are cut off, the program prints raw bytes)."""
    st = program(name)
    cmd = command(name, limit, checked=True)
    r = subprocess.run(cmd, input=st['image'] + stdin, capture_output=True, timeout=TIMEOUT, check=False)
    return r.returncode, r.stdout, r.stderr.split(b'VM1_AUDIT')[0]


def write_all(fd, data):
    while data:
        data = data[os.write(fd, data):]


class Net:
    """Spaces connected by pipes. link() makes a pipe (the read end for one space, the write end for the other); start() runs a space
    (the image is written into the pipe which is its stdin before anything else); finish() waits for all with one deadline, kills all on
    a timeout and raises AssertionError."""

    def __init__(self):
        self.procs, self.fds = [], []

    def link(self):
        r, w = os.pipe()
        self.fds += [r, w]
        return r, w

    def start(self, name, stdin, stdout, limit=0, image_to=None):
        """stdin, stdout: file descriptors. image_to: the descriptor into which the image is written first (the write end of the stdin)."""
        p = subprocess.Popen(command(name, limit), stdin=stdin, stdout=subprocess.DEVNULL if stdout is None else stdout, stderr=subprocess.PIPE)
        self.procs.append(p)
        if image_to is not None:
            write_all(image_to, program(name)['image'])
        return p

    def close(self, *fds):
        for fd in fds:
            if fd in self.fds:
                self.fds.remove(fd)
                os.close(fd)

    def finish(self, timeout=TIMEOUT, close=True):
        """close=False keeps the descriptors of the test open while waiting (a channel which stays open and silent)."""
        if close:
            self.close(*list(self.fds))
        end, res = time.monotonic() + timeout, []
        try:
            for p in self.procs:
                try:
                    _, err = p.communicate(timeout=max(0.1, end - time.monotonic()))
                except subprocess.TimeoutExpired:
                    raise AssertionError('the process did not finish in %d s (a blocked read): killed' % timeout) from None
                res.append((p.returncode, err))
        finally:
            for p in self.procs:
                if p.poll() is None:
                    p.kill()
                    p.communicate()
            self.close(*list(self.fds))
        return res


def model(window, ops):
    """The answerer on a list of (op, pos, dat): the bytes of its answers and the final window (op 0 or the end stops it)."""
    w, out = list(window), bytearray()
    for op, pos, dat in ops:
        if op == STOP:
            break
        if op & 1:
            out += bytes([w[pos]]) if pos < 8 else ONES
        elif op & 2 and pos < 8:
            w[pos] = rev(dat, 8)
    return bytes(out), bytes(w)


class Pair(unittest.TestCase):
    """26.2: A copies to the channel, B reads it (no answer)."""

    expect = bytes(rev(v, 8) for v in A_VALUES)

    def test_a_alone_writes_its_memory_to_stdout(self):
        r = single('far_a')
        self.assertEqual((r.rc, r.out), (0, self.expect))

    def test_a_to_b(self):
        n = Net()
        r, w = n.link()
        n.start('far_b', r, None, image_to=w)
        with tempfile.TemporaryFile() as f:                    # the image of A is its stdin (a file: nothing to wait for)
            f.write(program('far_a')['image'])
            f.seek(0)
            n.start('far_a', f.fileno(), w)
        n.close(r, w)                                          # w is now only in A: A's end is the EOF of B
        (rcb, errb), (rca, erra) = n.finish()
        self.assertEqual((rca, erra), (0, b''))
        self.assertEqual((rcb, errb), (0, self.expect), 'the bits of B are the bits of A')

    def test_b_gets_what_is_sent_and_zeros_at_eof(self):
        """B reads exactly four bytes; if the sender is gone after two (EOF) the rest stays as it was (zeros)."""
        rc, out, err = single_err('far_b', self.expect)
        self.assertEqual((rc, err), (0, self.expect))
        rc, out, err = single_err('far_b', self.expect[:2])
        self.assertEqual((rc, err), (0, self.expect[:2] + b'\0\0'))

    def test_a_without_a_reader_ends(self):
        """The reader of the channel is closed: the write fails (SIGPIPE is ignored), A does not hang and stops."""
        n = Net()
        r, w = n.link()
        n.close(r)
        with tempfile.TemporaryFile() as f:
            f.write(program('far_a')['image'])
            f.seek(0)
            n.start('far_a', f.fileno(), w)
            [(rc, err)] = n.finish()
        self.assertEqual((rc, err), (0, b''))

    def test_blocking_read_ignores_the_tick_limit(self):
        """B waits for a byte which does not come (the sender is alive and silent): the limit -t does not stop it (a blocked read passes no
        tick), the pair stays; the test kills it itself (here after 1.5 s) and so shows the hang as an error and does not hang."""
        n = Net()
        r, w = n.link()
        p = n.start('far_b', r, None, limit=100, image_to=w)      # w stays open: nobody writes, nobody closes
        time.sleep(1.5)
        self.assertIsNone(p.poll(), 'B must still wait')
        with self.assertRaises(AssertionError):
            n.finish(timeout=0.5, close=False)
        self.assertIsNotNone(p.poll(), 'killed')


class Answerer(unittest.TestCase):
    """26.3: far_serve.tw alone, the requests are made by the test (the checked emulator, ticks)."""

    def test_the_window_and_the_answers(self):
        r = single('far_serve', b''.join(rec(GET, i) for i in range(8)) + rec(STOP, 0))
        self.assertEqual((r.rc, r.out), (0, WINDOW), 'the window of the answerer')

    def test_outside_the_window_is_ones(self):
        """pos >= 8 is the prohibitive price: all ones (also pos = 8, 9, 16, 128, 255: the low bits alone must not decide)."""
        poss = [8, 9, 15, 16, 64, 128, 200, 255]
        r = single('far_serve', b''.join(rec(GET, p) for p in poss) + rec(STOP, 0))
        self.assertEqual((r.rc, r.out), (0, ONES * len(poss)))

    def test_put_changes_the_window_and_outside_changes_nothing(self):
        ops = [(PUT, 3, 77), (PUT, 8, 1), (PUT, 9, 2), (PUT, 200, 3), (PUT, 0, 250)] + [(GET, i, 0) for i in range(8)] + [(GET, 11, 0), (STOP, 0, 0)]
        r = single('far_serve', b''.join(rec(*o) for o in ops))
        out, _ = model(WINDOW, ops)
        self.assertEqual((r.rc, r.out), (0, out))
        self.assertEqual(r.out[:8], bytes([rev(250, 8)]) + WINDOW[1:3] + bytes([rev(77, 8)]) + WINDOW[4:], 'put 3 and 0 are in, 8, 9, 200 are not')

    def test_random_sessions(self):
        rnd = random.Random(26)
        for i in range(12):
            with self.subTest(i=i):
                ops = [(rnd.choice([GET, PUT, GET, PUT, 3]), rnd.choice([rnd.randrange(8), rnd.randrange(256)]), rnd.randrange(256))
                       for _ in range(rnd.randrange(1, 40))] + [(STOP, 0, 0)]
                r = single('far_serve', b''.join(rec(*o) for o in ops))
                self.assertEqual((r.rc, r.out), (0, model(WINDOW, ops)[0]))

    def test_end_of_stdin_is_a_stop(self):
        """The channel is closed with no op = 0 (or in the middle of a record): the answerer answers what it has and stops by itself."""
        for tail in (b'', rec(GET, 1)[:1], rec(GET, 1)[:2]):
            with self.subTest(tail=tail):
                r = single('far_serve', rec(GET, 2) + tail, limit=100000)
                self.assertEqual(r.rc, 0)
                self.assertEqual(r.out[:1], b'P')
                self.assertLess(r.ticks, 100000, 'stops by the end of input, not by the limit')

    def test_tick_limit_stops_a_running_answerer(self):
        """-t stops a run which has data: 300 requests, the limit of ticks is for a few: the exit is 0, only the first answers are there."""
        r = single('far_serve', rec(GET, 2) * 300 + rec(STOP, 0), limit=100)
        self.assertEqual(r.rc, 0)
        self.assertTrue(0 < len(r.out) < 300, len(r.out))

    def test_ticks(self):
        """The measure (checked emulator): the ticks of one request. At the time of writing: stop only 26, get 17 (outside the window 14),
        put 20 (outside 17); the bounds here are loose."""
        base = single('far_serve', rec(STOP, 0)).ticks
        cost = {}
        for name, o in [('get', (GET, 3)), ('get_out', (GET, 9)), ('put', (PUT, 3, 7)), ('put_out', (PUT, 9, 7))]:
            cost[name] = single('far_serve', rec(*o) + rec(STOP, 0)).ticks - base
        self.assertLess(base, 60)
        for name, v in cost.items():
            with self.subTest(name):
                self.assertTrue(5 < v < 60, v)
        self.assertGreater(cost['get'], cost['get_out'])
        self.assertGreater(cost['put'], cost['put_out'])


class Asker(unittest.TestCase):
    """26.3: far_get.tw alone (the answers are given by the test) and its pair with far_serve.tw."""

    ops = [(GET, 2, 0), (GET, 5, 0), (PUT, 3, 165), (GET, 3, 0), (GET, 8, 0), (PUT, 9, 77), (GET, 1, 0), (GET, 200, 0), (STOP, 0, 0)]

    def expected(self):
        """The requests (the stdout of the asker) and what the answerer says for them (the stdin of the asker = the cells g1..g6)."""
        out, _ = model(WINDOW, self.ops)
        return b''.join(rec(*o) for o in self.ops), out

    def test_asker_alone_sends_the_records(self):
        sent, answers = self.expected()
        self.assertEqual(len(answers), 6)
        rc, out, err = single_err('far_get', answers)
        self.assertEqual((rc, out, err), (0, sent, answers), 'the requests are the records, the cells are the answers')

    def test_asker_alone_and_a_closed_channel(self):
        """No answer at all (EOF): the cells keep their start, all ones = the prohibitive price; the asker stops, does not hang."""
        rc, out, err = single_err('far_get', b'')
        self.assertEqual((rc, err), (0, ONES * 6))
        self.assertEqual(out, self.expected()[0])

    def test_ticks(self):
        """The asker, the whole script (6 get, 2 put, the stop, the print): 42 ticks at the time of writing (4 for a get, 3 for a put)."""
        r = single('far_get', b'abcdef')
        self.assertTrue(10 < r.ticks < 100, r.ticks)

    def run_pair(self, serve_limit=0, ask_limit=0):
        """Q (far_get) and R (far_serve), two pipes: Q.stdout -> R.stdin, R.stdout -> Q.stdin; the image of each goes first into its stdin."""
        n = Net()
        q_r, q_w = n.link()                    # Q -> R
        r_r, r_w = n.link()                    # R -> Q
        rp = n.start('far_serve', q_r, r_w, limit=serve_limit)
        write_all(q_w, program('far_serve')['image'])
        qp = n.start('far_get', r_r, q_w, limit=ask_limit)
        write_all(r_w, program('far_get')['image'])
        n.close(q_r, q_w, r_r, r_w)
        res = n.finish()
        return res, rp, qp

    def test_pair(self):
        (rr, qr), _, _ = self.run_pair()
        _, answers = self.expected()
        self.assertEqual(rr, (0, b''), 'the answerer stops by op = 0')
        self.assertEqual(qr, (0, answers), 'the received bits: the window of the answerer, put changes it, outside is ones')
        self.assertEqual(answers[0:1], b'P')                                        # win[2]
        self.assertEqual(answers[2:3], bytes([rev(165, 8)]), 'get after put returns what was put')
        self.assertEqual(answers[3:4] + answers[5:6], ONES * 2, 'outside the window')
        self.assertEqual(answers[4:5], b'O', 'put outside did not touch the window')

    def test_pair_is_quick(self):
        t = time.monotonic()
        self.run_pair()
        self.assertLess(time.monotonic() - t, 10)

    def test_answerer_not_started_the_channel_closed(self):
        """The asker alone: the pipe to the answerer has no reader and the pipe from it has no writer (the answerer is not started or closed
        the channel). The reads see EOF: the cells stay all ones, the writes fail quietly; the asker stops with the prohibitive price."""
        n = Net()
        q_r, q_w = n.link()
        r_r, r_w = n.link()
        n.close(q_r)                                           # nobody reads the requests
        n.start('far_get', r_r, q_w)
        write_all(r_w, program('far_get')['image'])
        n.close(q_w, r_r, r_w)                                 # nobody will answer
        [(rc, err)] = n.finish()
        self.assertEqual((rc, err), (0, ONES * 6))

    def test_answerer_dies_midway(self):
        """The answerer is cut by the limit of ticks (-t 45: it is gone after the first answer, the exit is 0 and its stdout is closed): the asker
        gets EOF for the rest and ends, not hanging: the first answer is there, the others stay ones = the prohibitive price."""
        (rr, qr), _, _ = self.run_pair(serve_limit=45)
        self.assertEqual(rr[0], 0)
        self.assertEqual(qr, (0, b'P' + ONES * 5))

    def test_asker_dies_midway(self):
        """The asker closes the channel (here: only one request then EOF, no op = 0): the answerer stops by itself at the end of the input,
        not by the limit of ticks."""
        n = Net()
        q_r, q_w = n.link()
        r_r, r_w = n.link()
        n.start('far_serve', q_r, r_w, limit=100000)
        write_all(q_w, program('far_serve')['image'] + rec(GET, 4))
        n.close(q_r, q_w)
        out = os.read(r_r, 1)
        n.close(r_r, r_w)
        [(rc, err)] = n.finish()
        self.assertEqual((rc, err, out), (0, b'', WINDOW[4:5]))

    def test_silent_answerer_blocks_and_the_test_kills(self):
        """The answerer is alive (the channel is open) and does not answer: the asker waits in the read, the tick limit does not help;
        what ends it is the kill by the test (the timeout), which is an error of the test, not a hang."""
        n = Net()
        q_r, q_w = n.link()
        r_r, r_w = n.link()
        n.start('far_get', r_r, q_w, limit=1000)
        write_all(r_w, program('far_get')['image'])            # r_w stays open: the "answerer" says nothing
        n.close(q_r)
        with self.assertRaises(AssertionError):
            n.finish(timeout=1.0, close=False)


if __name__ == '__main__':
    unittest.main()
