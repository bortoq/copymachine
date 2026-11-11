"""Tests of the far copy (26.2, 26.3, 7.2.44): copying between two spaces = two running emulators connected by the shell: the stdout of one
is the stdin of the other (the image of the program goes first, then the stream). Programs (language 3, tower/programs/far/):
  far_a.tw, far_b.tw    26.2, no answerer: A copies four bytes from its memory to its stdout, B reads them from its stdin and prints them to stderr;
  far_serve.tw          26.3, the answerer: the window of 8 cells of 8 bits; the record of a request is 6 bytes: op (0 stop, 1 get, 2 put),
                        pos (32 bits, the number of the byte; the window is pos < 8), dat (8 bits); get answers 1 byte (ones outside the window),
                        put answers nothing; the end of stdin is a stop (26.4: pos was 8 bits, now 32);
  far_get.tw            the asker: sends get/put by hand, keeps the answers in its cells, sends op = 0, prints the cells to stderr;
  far_copy.tw           26.4, the asker in language 4: `copy &x 0x2...` and `copy 0x2... &x` (the pass l4c makes the requests), built by the chain;
  far_file_a.tw, far_file_b.tw   26.5, the common file `-r path` as the second definition of the same copy: A writes the data and the flag, B polls the flag and reads;
  far_serve_ck.tw, far_get_ck.tw 26.6, the checked protocol (record of 7 bytes with the sum, answer of 2 bytes: the value and its complement, repeat of the request,
                        the prohibitive price when the tries are out); a go-between of this file (Mediator) changes given bytes of the traffic.
The pair tests connect the processes by os.pipe (the pairs are created here and given to subprocess.Popen) with a timeout: a blocking read is not
stopped by the limit of ticks (-t), so the test kills the processes itself and fails; it never hangs. The single runs (one program, the stdin
made by the test) use the checked emulator and give the ticks. Python is here only: the programs are language 3.
Run: make check-tower  or  python3 -B tower/tests/test_far.py"""
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time

sys.dont_write_bytecode = True
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import common
import l3ctext
import l5
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


def chain_program(name, src, pack=False):
    """A text of language 4 built by the chain (the pass l4c, l3c, [l3p], l2l, the seed; A = 20) and kept under `name` (not a file): the stats as of program()."""
    img, P = l5.chain_image(('pack\n' if pack else '') + src, True)
    _CACHE[name] = {'image': img, 'A': 20, 'P': P}
    return _CACHE[name]


def program(name):
    """The committed program name.tw compiled by the Python reference (the smallest A), or the one made by chain_program: its stats (image, A, P)."""
    if name not in _CACHE:
        with open(os.path.join(PROGRAMS, name + '.tw'), encoding='utf-8') as h:
            p, errs = text.compile_text(h.read())
        assert not errs, errs
        _CACHE[name] = p.stats
    return _CACHE[name]


def rec(op, pos, dat=0):
    """The record of a request: op 8 bits, pos 32 bits (the number of the byte), dat 8 bits, 6 bytes (the numbers as `key` stores them: the lowest bit first)."""
    return stream(op, 8) + stream(pos, 32) + stream(dat, 8)


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
        if op == GET:
            out += bytes([w[pos]]) if pos < 8 else ONES
        elif op == PUT and pos < 8:
            w[pos] = rev(dat, 8)
    return bytes(out), bytes(w)


def run_pair(asker, serve_limit=0, ask_limit=0, serve='far_serve'):
    """Q (the asker) and R (far_serve, or the answerer `serve`), two pipes: Q.stdout -> R.stdin, R.stdout -> Q.stdin; the image of each goes first into its stdin."""
    n = Net()
    q_r, q_w = n.link()                    # Q -> R
    r_r, r_w = n.link()                    # R -> Q
    rp = n.start(serve, q_r, r_w, limit=serve_limit)
    write_all(q_w, program(serve)['image'])
    qp = n.start(asker, r_r, q_w, limit=ask_limit)
    write_all(r_w, program(asker)['image'])
    n.close(q_r, q_w, r_r, r_w)
    res = n.finish()
    return res, rp, qp


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
        """pos >= 8 is the prohibitive price: all ones (also pos = 8, 9, 16, 128, 255, and those which have the low bits of a cell of the window: 256 + 1,
        2^16 + 2, 2^24 + 3, 2^31 + 4, 2^32 - 1: the high bits of the 32-bit field decide, not the low ones)."""
        poss = [8, 9, 15, 16, 64, 128, 200, 255, 257, 65538, 2 ** 24 + 3, 2 ** 31 + 4, 2 ** 32 - 1]
        r = single('far_serve', b''.join(rec(GET, p) for p in poss) + rec(STOP, 0))
        self.assertEqual((r.rc, r.out), (0, ONES * len(poss)))

    def test_put_changes_the_window_and_outside_changes_nothing(self):
        ops = [(PUT, 3, 77), (PUT, 8, 1), (PUT, 9, 2), (PUT, 200, 3), (PUT, 2 ** 32 - 5, 9), (PUT, 2 ** 16 + 1, 9), (PUT, 0, 250)] + [(GET, i, 0) for i in range(8)] + [(GET, 11, 0), (STOP, 0, 0)]
        r = single('far_serve', b''.join(rec(*o) for o in ops))
        out, _ = model(WINDOW, ops)
        self.assertEqual((r.rc, r.out), (0, out))
        self.assertEqual(r.out[:8], bytes([rev(250, 8)]) + WINDOW[1:3] + bytes([rev(77, 8)]) + WINDOW[4:], 'put 3 and 0 are in, 8, 9, 200 are not')

    def test_random_sessions(self):
        rnd = random.Random(26)
        for i in range(12):
            with self.subTest(i=i):
                ops = [(rnd.choice([GET, PUT, GET, PUT, 3]), rnd.choice([rnd.randrange(8), rnd.randrange(256), rnd.randrange(2 ** 32)]), rnd.randrange(256))
                       for _ in range(rnd.randrange(1, 40))] + [(STOP, 0, 0)]
                r = single('far_serve', b''.join(rec(*o) for o in ops))
                self.assertEqual((r.rc, r.out), (0, model(WINDOW, ops)[0]))

    def test_other_op_is_skipped(self):
        """Only op = 0 (all 8 bits) stops; op = 3, 4, 16, 255 ... is a spoiled record: nothing is answered, the next right request is served."""
        for bad in (3, 4, 16, 255, 128):
            with self.subTest(op=bad):
                r = single('far_serve', rec(bad, 1, 9) + rec(GET, 2) + rec(PUT, 0, 7) + rec(bad, 0, 5) + rec(GET, 0) + rec(STOP, 0), limit=100000)
                self.assertEqual((r.rc, r.out), (0, WINDOW[2:3] + bytes([rev(7, 8)])))

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
        """The measure (checked emulator): the ticks of one request. At the time of writing (pos of 32 bits, 26.4; op compared whole, 27.2): stop only 40, get 45 (outside the
        window 42), put 54 (outside 51); with the op bits tested (26.4) they were 44, 35 (32), 38 (35); with pos of 8 bits (26.3) they were 26, 17 (14), 20 (17); the bounds here are loose."""
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
        return run_pair('far_get', serve_limit, ask_limit)

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
        """The answerer is cut by the limit of ticks (-t 60: it is gone after the first answer, the exit is 0 and its stdout is closed): the asker
        gets EOF for the rest and ends, not hanging: the first answer is there, the others stay ones = the prohibitive price."""
        (rr, qr), _, _ = self.run_pair(serve_limit=60)
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


FAR_COPY = os.path.join(PROGRAMS, 'far_copy.tw')
FAR_CELLS = [b'COPYMACH', b'PYMA', b'OK', b'MOKH', ONES, b'KH' + ONES * 2, ONES * 4, b'Y']     # what far_copy.tw puts to stderr, cell by cell


def far(byte):
    """The far address of the byte number `byte` (the position in bits is 8 * byte; the link is 0): 0x2 and 32 hex digits."""
    return '0x2%032x' % (8 * byte)


def far_text(n, put):
    """A text of language 4 with one far copy of n bits from or to the byte 3 (the cell x of n bits)."""
    return ':x data %d 0\n:main block\n%s\nhalt\n' % (n, ('copy %s &x' if put else 'copy &x %s') % far(3))


class FarCopy(unittest.TestCase):
    """26.4: `copy &x 0x2...` and `copy 0x2... &x` in a text of language 4, built by the chain (l4c, l3c, [l3p], l2l, seed), against far_serve.tw in a second emulator."""

    @classmethod
    def setUpClass(cls):
        with open(FAR_COPY, encoding='utf-8') as h:
            cls.src = h.read()
        cls.names = {}
        for pack in (False, True):
            cls.names[pack] = 'far_copy:' + ('pack' if pack else 'serial')
            chain_program(cls.names[pack], cls.src, pack)

    # the requests which far_copy.tw makes (one byte each), in order, and the stop; the data of a put is the byte as it stands in memory (the number is its reversal)
    ops = ([(GET, i, 0) for i in range(8)] + [(GET, 2 + i, 0) for i in range(4)] + [(PUT, 5, rev(ord('O'), 8)), (PUT, 6, rev(ord('K'), 8))]
           + [(GET, 5, 0), (GET, 6, 0)] + [(GET, 4 + i, 0) for i in range(4)] + [(GET, 8, 0)] + [(GET, 6 + i, 0) for i in range(4)]
           + [(PUT, 8, rev(ord('O'), 8)), (PUT, 9, rev(ord('K'), 8))] + [(GET, 2 ** 28 + 3 + i, 0) for i in range(4)]
           + [(PUT, 2 ** 28 + 3, rev(ord('O'), 8))] + [(GET, 3, 0), (STOP, 0, 0)])

    def test_the_requests_are_the_records(self):
        """The asker alone (the answers are the test's): its stdout is the records of one byte per request, by the protocol; both layouts."""
        answers = model(WINDOW, self.ops)[0]
        want = b''.join(rec(*o) for o in self.ops)
        for pack in (False, True):
            with self.subTest(pack=pack):
                rc, out, err = single_err(self.names[pack], answers)
                self.assertEqual((rc, out, err), (0, want, b''.join(FAR_CELLS)))

    def test_a_closed_channel(self):
        """No answer (the channel is closed): the cells stay as they were (zeros), the requests are all sent, the asker stops and does not hang."""
        rc, out, err = single_err(self.names[False], b'')
        self.assertEqual((rc, out, err), (0, b''.join(rec(*o) for o in self.ops), bytes(28)))

    def test_pair(self):
        """The asker and far_serve: the bytes of the window, put changes the window, outside the window is ones, both end (the stop is in the program);
        a timeout would be a deadlock (the read before the write of the request). The serial layout and the packed one."""
        for pack in (False, True):
            with self.subTest(pack=pack):
                (rr, qr), _, _ = run_pair(self.names[pack])
                self.assertEqual(rr, (0, b''), 'the answerer stops by op = 0')
                self.assertEqual(qr, (0, b''.join(FAR_CELLS)))
        cells = b''.join(FAR_CELLS)
        self.assertEqual((cells[:8], cells[12:14], cells[14:18], cells[18:19], cells[19:21]), (WINDOW, b'OK', b'MOKH', ONES, b'KH'))
        self.assertEqual(cells[-1:], b'Y', 'put outside the window (also the far byte 2^28 + 3, which has the low bits of the cell 3) changed nothing')

    def test_chain_with_the_tool_l4c(self):
        """The pass made by the tool l4c itself (its image built by the references, run in the emulator) gives the text of the reference; the image of it is the same."""
        import test_l4p
        test_l4p.setUpModule()
        out = test_l4p.l4c(self.src.encode())
        self.assertEqual((out.rc, out.out), (0, l3ctext.l4c(self.src.encode() + b'\0')[0]))
        self.assertEqual(l5.chain_image(out.out[:-1].decode('latin-1'))[0], program(self.names[False])['image'])

    def test_the_forms_which_are_not_translated(self):
        """The far address which is not as told stays in the text as it was (l3c rejects it): the link is not 0, the position is not a multiple of 8 or over 2^32 bits,
        the width is not 8..64 whole bytes."""
        for tail in ('0x2%032x' % (1 << 96), '0x2%032x' % 4, '0x2%032x' % (1 << 32)):
            out = l3ctext.l4c((':x data 8 0\n:main block\ncopy &x %s\n' % tail).encode() + b'\0')[0]
            self.assertTrue(out.endswith(('copy &x %s\n' % tail).encode() + b'\0'), (tail, out[-60:]))
            self.assertIsNotNone(l3ctext.encode(out[:-1])[1], tail)
        for n in (1, 4, 12, 72, 2048):
            out = l3ctext.l4c(far_text(n, False).encode() + b'\0')[0]
            self.assertIn(b'copy &x 0x2', out[out.index(b':main'):], n)

    def test_ticks(self):
        """The measure: the ticks of one far copy of 8 and of 32 bits (the checked emulator): the asker (the copy between the two `halt`s: the difference to a program with
        no copy; the answers are given) and the answerer (the requests of the copy: the difference to the stop alone). At the time of writing the asker needs
        6 ticks for 8 bits and 18 for 32 bits for a get (the put: 5 and 14), the answerer 45 ticks per byte for a get and 54 for a put (45 and 180, 54 and 216; before 27.2: 35, 38)."""
        base_ask = single_ticks(chain_text(':x data 8 0\n:main block\nhalt\n'), b'')
        stop = single('far_serve', rec(STOP, 0)).ticks
        res = {}
        for n in (8, 32):
            for put in (False, True):
                t = single_ticks(chain_text(far_text(n, put)), b'\xaa' * 4) - base_ask
                reqs = b''.join(rec(PUT if put else GET, 3 + i, 0) for i in range(n // 8)) + rec(STOP, 0)
                res[n, put] = (t, single('far_serve', reqs).ticks - stop)
        for (n, put), (a, b) in res.items():
            with self.subTest(n=n, put=put):
                self.assertTrue(0 < a < 20 * n and 0 < b < 60 * n // 8 + 1, (a, b))
        self.assertGreater(res[32, False][0], res[8, False][0])
        self.assertGreater(res[32, True][1], res[8, True][1])
        sys.stderr.write('far copy ticks (asker, answerer): %s\n' % res)


# ---------------------------------------------------------------- 26.5: the common file

# far_file_a.tw / far_file_b.tw: the data are the bytes 0..3 of the file (32 bits), the flag is the byte 4 (the bit 32), 1 = ready
FILE_FLAG = b'\x80'                            # the byte of the file with the flag: the number 1 is the first bit of the byte (the bit 32 of the area is the high bit of the byte 4)
FILE_DATA = b'FILE'                            # the data of far_file_a.tw


def file_text(name, limit=None):
    """The text of far_file_a.tw / far_file_b.tw (the limit of the polls of B can be changed: the cell `limit`)."""
    with open(os.path.join(PROGRAMS, name + '.tw'), encoding='utf-8') as h:
        src = h.read()
    if limit is not None:
        assert ':limit data 32 300000\n' in src
        src = src.replace(':limit data 32 300000\n', ':limit data 32 %d\n' % limit)
    return src


def file_program(name, pack=False, limit=None):
    """The chain image (l4c, l3c, [l3p], l2l, seed) of far_file_a / far_file_b, kept in _CACHE under a name of its own."""
    key = '%s:%s:%s' % (name, 'pack' if pack else 'serial', limit)
    if key not in _CACHE:
        chain_program(key, file_text(name, limit), pack)
    return key


def file_start(key, path, limit=0):
    """One emulator of the space with the common file `-r path`; the image goes into its stdin."""
    st = _CACHE[key]
    p = subprocess.Popen([common.EMU, '-s', str(2 ** st['A'] - 6), '-p', str(st['P']), '-t', str(limit), '-r', path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    p.stdin.write(st['image'])
    p.stdin.flush()                                      # stays open (nothing reads it after the image): file_end closes it
    return p


def file_end(p, timeout=TIMEOUT):
    """(rc, stderr) of a space started by file_start; killed and AssertionError after the timeout (a hang is an error of the test)."""
    try:
        _, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        raise AssertionError('the process did not finish in %d s: killed' % timeout) from None
    return p.returncode, err


def file_kill(p):
    if p.poll() is None:
        p.kill()
    p.communicate()


def file_single(key, path, limit=200000):
    """One space alone on the file, the checked emulator: Result with out, err, rc, ticks (the stderr of the program is r.err without the audit lines; use file_err)."""
    st = _CACHE[key]
    return common.run(st['image'], st['A'], st['P'], checked=True, limit=limit, files=[path])


class SharedFile(unittest.TestCase):
    """26.5: two emulators run with the same `-r path`; A writes the data by `copy 0x1... &v` and then the flag, B polls the flag and then reads the data by `copy &y 0x1...`."""

    def setUp(self):
        d = tempfile.mkdtemp(prefix='tower-far-file-')
        self.addCleanup(shutil.rmtree, d, True)
        self.path = os.path.join(d, 'common.bin')

    def start(self, key, limit=0):
        p = file_start(key, self.path, limit)
        self.addCleanup(file_kill, p)
        return p

    def write_file(self, data):
        with open(self.path, 'wb') as h:
            h.write(data)

    def read_file(self):
        with open(self.path, 'rb') as h:
            return h.read()

    def test_a_writes_the_data_and_then_the_flag(self):
        for pack in (False, True):
            with self.subTest(pack=pack):
                self.write_file(b'')
                r = file_single(file_program('far_file_a', pack), self.path)
                self.assertEqual((r.rc, r.out), (0, b''))
                self.assertEqual(self.read_file(), FILE_DATA + FILE_FLAG, 'the data, then the flag in the byte 4 (the file did not exist: a new one)')

    def test_b_after_a(self):
        """A is done, then B: the flag is there at the first poll, no failed poll, B gets the data."""
        for pack in (False, True):
            with self.subTest(pack=pack):
                self.write_file(b'')
                file_end(self.start(file_program('far_file_a', pack)))
                rc, err = file_end(self.start(file_program('far_file_b', pack)))
                self.assertEqual((rc, err), (0, FILE_DATA + bytes(4)), 'y = the data of A, n = 0 failed polls')

    def test_b_waits_for_the_flag_and_does_not_read_the_data_before_it(self):
        """The file holds old data and no flag: B polls and does not end (the flag is 0), and when the test writes new data and then the flag B has the NEW data:
        B did not read the data before the flag (old data would be the answer then)."""
        for pack in (False, True):
            with self.subTest(pack=pack):
                self.write_file(b'OLD!')
                b = self.start(file_program('far_file_b', pack))
                time.sleep(0.5)
                self.assertIsNone(b.poll(), 'B must still poll: the flag is not there')
                with open(self.path, 'r+b') as h:                       # what A does, from outside: the data, then the flag
                    h.write(b'NEW!')
                    h.flush()
                    time.sleep(0.2)
                    self.assertIsNone(b.poll(), 'the data alone are not the flag')
                    h.seek(4)
                    h.write(FILE_FLAG)
                rc, err = file_end(b)
                self.assertEqual((rc, err[:4]), (0, b'NEW!'))
                self.assertGreater(int.from_bytes(bytes(rev(b, 8) for b in err[4:]), 'little'), 0, 'failed polls were counted')

    def test_pair_b_first_then_a(self):
        """B starts first (old data in the file), A 0.3 s later: B ends with the data of A; the number of the failed polls is not fixed (it depends on the time), at least one."""
        for pack in (False, True):
            with self.subTest(pack=pack):
                self.write_file(b'OLD!')
                b = self.start(file_program('far_file_b', pack))
                time.sleep(0.3)
                a = self.start(file_program('far_file_a', pack))
                self.assertEqual(file_end(a), (0, b''))
                rc, err = file_end(b)
                self.assertEqual((rc, err[:4]), (0, FILE_DATA))
                self.assertGreater(int.from_bytes(bytes(rev(b, 8) for b in err[4:]), 'little'), 0)

    def test_random_delays(self):
        """Both at once, a random pause (a fixed seed) before A: B always has the data of A (never old ones, never zeros)."""
        rnd = random.Random(265)
        for i in range(6):
            with self.subTest(i=i):
                self.write_file(b'OLD!')
                b = self.start(file_program('far_file_b', bool(i & 1)))
                time.sleep(rnd.random() * 0.2)
                a = self.start(file_program('far_file_a', bool(i & 1)))
                self.assertEqual(file_end(a)[0], 0)
                rc, err = file_end(b)
                self.assertEqual((rc, err[:4]), (0, FILE_DATA))

    def test_timeout_the_flag_does_not_come(self):
        """No A: after `limit` failed polls B does not read the data: y = all ones (the prohibitive price) and B ends (n = limit), not hanging. The cell limit is changed to 300."""
        for pack in (False, True):
            with self.subTest(pack=pack):
                self.write_file(FILE_DATA)                              # the data are there, the flag is not
                rc, err = file_end(self.start(file_program('far_file_b', pack, limit=300)))
                self.assertEqual((rc, err), (0, ONES * 4 + stream(300, 32)))

    def test_tick_limit_stops_the_polling(self):
        """The default limit (300000 polls) is far; the tick limit -t stops B: the exit is 0 (a poll is not a blocking read), y stays zeros: the data were not read."""
        self.write_file(FILE_DATA)
        rc, err = file_end(self.start(file_program('far_file_b'), limit=2000))
        self.assertEqual((rc, err), (0, b''), 'stopped by the limit before the print: no output, and no data taken before the flag')

    def test_ticks(self):
        """The measure (the checked emulator, ticks): A (the data 32 bits and the flag 8 bits) and B (one poll and the read of 32 bits; and one failed poll, from the difference
        of two limits) against the programs with no copy. At the time of writing, serial layout: A 18 - 1, B 31 - 1 with the first poll good; a failed poll about 150 (the 32-bit counter: add and lt over 8 nibbles)."""
        base = file_single(chain_text(':x data 8 0\n:main block\nhalt\n'), self.path).ticks
        res = {}
        for pack in (False, True):
            self.write_file(b'')
            ta = file_single(file_program('far_file_a', pack), self.path).ticks - base
            tb = file_single(file_program('far_file_b', pack), self.path).ticks - base          # the flag is set now: one poll and the read
            self.write_file(FILE_DATA)                                                       # no flag
            t10 = file_single(file_program('far_file_b', pack, limit=10), self.path, 10 ** 6).ticks
            t20 = file_single(file_program('far_file_b', pack, limit=20), self.path, 10 ** 6).ticks
            res[pack] = (ta, tb, (t20 - t10) / 10)
            self.assertTrue(0 < ta < 60 and 0 < tb < 80 and 5 < res[pack][2] < 300, res[pack])
        sys.stderr.write('common file ticks (A writes 32 bits + flag, B one poll + read 32 bits, one failed poll), serial / packed: %s\n' % res)


# ---------------------------------------------------------------- 26.6: the faults of the channel

CK_OPS = [(GET, 2, 0), (GET, 5, 0), (PUT, 3, 165), (GET, 3, 0), (GET, 8, 0), (PUT, 9, 77), (GET, 1, 0), (GET, 200, 0)]       # the requests of far_get_ck.tw
BAD = b'\0\0'                                  # the answer to a record with a wrong sum: not a pair


def ck_sum(op, pos, dat):
    return (op + sum(pos >> (8 * i) & 255 for i in range(4)) + dat) & 255


def rec_ck(op, pos, dat=0, ck=None):
    """The record of a request of the checked protocol: op 8 bits, pos 32 bits, dat 8 bits, ck 8 bits (the sum modulo 256 of the six bytes as numbers), 7 bytes; ck can be given wrong."""
    return stream(op, 8) + stream(pos, 32) + stream(dat, 8) + stream(ck_sum(op, pos, dat) if ck is None else ck, 8)


def pair(b):
    """The answer: the byte and its complement."""
    return bytes([b, 255 - b])


def model_ck(window, recs):
    """The checked answerer on a list of (op, pos, dat, ck): the bytes of its answers (two for every record up to the stop) and the final window.
    A record with the wrong ck, or an op other than 0, 1, 2, is answered by 0, 0 and changes nothing; op 0 with the right ck is the stop."""
    w, out = list(window), bytearray()
    for op, pos, dat, ck in recs:
        if ck != ck_sum(op, pos, dat):
            out += BAD
        elif op == GET:
            out += pair(w[pos]) if pos < 8 else pair(255)
        elif op == PUT:
            if pos < 8:
                w[pos] = rev(dat, 8)
            out += pair(w[pos]) if pos < 8 else pair(255)
        elif op == 0:
            break
        else:
            out += BAD
    return bytes(out), bytes(w)


def ck_cells():
    """What far_get_ck.tw puts to stderr with an answerer that works: the first byte of every answer (a get: the cell; a put: the cell read back, outside the window 255)."""
    ans, _ = model_ck(WINDOW, [(op, pos, dat, ck_sum(op, pos, dat)) for op, pos, dat in CK_OPS])
    return ans[0::2]


CK_ASKED = b''.join(rec_ck(*o) for o in CK_OPS) + rec_ck(STOP, 0)       # what the asker sends when all is well (the stop is the record of zeros)
CK_ANSWERS = b''.join(pair(c) for c in ck_cells())


def relay(src, dst, fault, count):
    """The go-between of one direction: the bytes of src go to dst one by one, the byte number i (from 0) is changed by xor with fault(i) (0 = unchanged);
    at the end of src dst is closed (the end of the channel passes through), count[0] = the number of bytes."""
    n = 0
    try:
        while True:
            b = os.read(src, 1)
            if not b:
                break
            try:
                os.write(dst, bytes([b[0] ^ fault(n)]))
            except OSError:                                  # the reader is gone: the rest is not carried
                pass
            n += 1
    finally:
        count[0] = n
        os.close(dst)
        os.close(src)


def run_mediated(req_fault=lambda i: 0, ans_fault=lambda i: 0, asker='far_get_ck', serve='far_serve_ck', timeout=TIMEOUT):
    """The asker and the answerer with a go-between (the threads of this test) in both pipes: the requests pass req_fault, the answers pass ans_fault (the faults are
    functions of the number of the byte in its stream, so the test is deterministic). The images go straight into the stdin of each. Returns
    ((rc, err) of the answerer, (rc, err) of the asker), the number of bytes of the requests and the number of bytes of the answers that were carried."""
    n = Net()
    q_out_r, q_out_w = os.pipe()                         # asker.stdout -> relay
    r_in_r, r_in_w = os.pipe()                           # relay -> answerer.stdin
    r_out_r, r_out_w = os.pipe()                         # answerer.stdout -> relay
    q_in_r, q_in_w = os.pipe()                           # relay -> asker.stdin
    n.start(serve, r_in_r, r_out_w)
    write_all(r_in_w, program(serve)['image'])
    n.start(asker, q_in_r, q_out_w)
    write_all(q_in_w, program(asker)['image'])
    for fd in (r_in_r, r_out_w, q_in_r, q_out_w):
        os.close(fd)
    nreq, nans = [0], [0]
    threads = [threading.Thread(target=relay, args=(q_out_r, r_in_w, req_fault, nreq), daemon=True),
               threading.Thread(target=relay, args=(r_out_r, q_in_w, ans_fault, nans), daemon=True)]
    for t in threads:
        t.start()
    try:
        res = n.finish(timeout=timeout, close=False)
    finally:
        for t in threads:
            t.join(5)
    return res[0], res[1], nreq[0], nans[0]


def plan_fault(plan):
    """A fault function from {byte number: xor mask}."""
    return lambda i: plan.get(i, 0)


def random_plan(seed, p, width, records):
    """A fixed plan from a seed: every record (of `width` bytes) is spoiled with the probability p: exactly one byte of it, by a mask of 1..255 (never two bytes of one record)."""
    rnd = random.Random(seed)
    plan = {}
    for k in range(records):
        if rnd.random() < p:
            plan[k * width + rnd.randrange(width)] = rnd.randrange(1, 256)
    return plan


class CheckedAnswerer(unittest.TestCase):
    """26.6: far_serve_ck.tw alone (the checked emulator; the records are made by the test)."""

    def test_the_answers_are_the_value_and_its_complement(self):
        recs = [(GET, i, 0) for i in range(8)] + [(GET, 8, 0), (GET, 2 ** 32 - 1, 0), (GET, 257, 0), (STOP, 0, 0)]
        r = single('far_serve_ck', b''.join(rec_ck(*o) for o in recs))
        self.assertEqual((r.rc, r.out), (0, b''.join(pair(c) for c in WINDOW) + pair(255) * 3), 'the window; outside 255 and its complement 0')
        self.assertEqual(pair(255), b'\xff\x00')

    def test_put_is_confirmed_by_the_cell_read_back(self):
        ops = [(PUT, 3, 77), (PUT, 8, 1), (PUT, 0, 250), (GET, 3, 0), (GET, 0, 0), (GET, 1, 0), (STOP, 0, 0)]
        r = single('far_serve_ck', b''.join(rec_ck(*o) for o in ops))
        out, _ = model_ck(WINDOW, [(*o, ck_sum(*o)) for o in ops])
        self.assertEqual((r.rc, r.out), (0, out))
        self.assertEqual(r.out[0:2], pair(rev(77, 8)), 'the answer to put: the cell now')
        self.assertEqual(r.out[2:4], pair(255), 'put outside the window: nothing is written, the answer is the prohibitive price')
        self.assertEqual(r.out[4:6], pair(rev(250, 8)))
        self.assertEqual(r.out[6:8], r.out[0:2], 'get after put: the same')
        self.assertEqual(r.out[10:12], pair(WINDOW[1]), 'the other cells are as they were')

    def test_a_wrong_sum_changes_nothing_and_is_answered_by_zeros(self):
        """Every byte of a put record changed (by every one of 8 masks): the answer is 0, 0, the window is as it was (a get after it)."""
        for byte in range(7):
            for mask in (1, 2, 4, 8, 16, 32, 64, 128):
                good = bytearray(rec_ck(PUT, 3, 77))
                good[byte] ^= mask
                with self.subTest(byte=byte, mask=mask):
                    r = single('far_serve_ck', bytes(good) + rec_ck(GET, 3) + rec_ck(STOP, 0))
                    self.assertEqual((r.rc, r.out), (0, BAD + pair(WINDOW[3])))

    def test_op_not_0_1_2(self):
        """A record with the right sum but another op (4, 8): 0, 0 for 4 and 8; op 0 with a right sum stops, with a wrong one it does not."""
        r = single('far_serve_ck', rec_ck(4, 1) + rec_ck(8, 1) + rec_ck(STOP, 0, 0, ck=5) + rec_ck(GET, 1) + rec_ck(STOP, 0))
        self.assertEqual((r.rc, r.out), (0, BAD * 3 + pair(WINDOW[1])))

    def test_op_3_16_255_do_not_stop(self):
        """op = 3 (was a get by its bit 0), 16, 255 with a right sum: 0, 0 like a wrong sum, nothing is changed, the answerer goes on and serves the next right record."""
        r = single('far_serve_ck', rec_ck(3, 1) + rec_ck(PUT, 1, 9) + rec_ck(16, 1, 9) + rec_ck(255, 0, 0) + rec_ck(GET, 1) + rec_ck(STOP, 0), limit=100000)
        self.assertEqual((r.rc, r.out), (0, BAD + pair(rev(9, 8)) + BAD * 2 + pair(rev(9, 8))))

    def test_random_sessions(self):
        rnd = random.Random(266)
        for i in range(10):
            with self.subTest(i=i):
                recs = []
                for _ in range(rnd.randrange(1, 30)):
                    op, pos, dat = rnd.choice([GET, PUT, GET, PUT, 3, 4]), rnd.choice([rnd.randrange(8), rnd.randrange(256), rnd.randrange(2 ** 32)]), rnd.randrange(256)
                    ck = ck_sum(op, pos, dat) if rnd.random() < 0.7 else rnd.randrange(256)
                    recs.append((op, pos, dat, ck))
                recs.append((STOP, 0, 0, 0))
                r = single('far_serve_ck', b''.join(rec_ck(*x[:3], ck=x[3]) for x in recs))
                self.assertEqual((r.rc, r.out), (0, model_ck(WINDOW, recs)[0]))

    def test_end_of_stdin_is_a_stop(self):
        """The channel is closed, with no stop record or in the middle of a record: the answerer answers what it has (a cut record: 0, 0) and stops by itself, not by the limit."""
        for tail in (b'', rec_ck(GET, 1)[:1], rec_ck(GET, 1)[:5], rec_ck(GET, 1)[:6]):
            with self.subTest(tail=tail):
                r = single('far_serve_ck', rec_ck(GET, 2) + tail, limit=100000)
                self.assertEqual(r.rc, 0)
                self.assertEqual(r.out[:2], pair(WINDOW[2]))
                self.assertIn(r.out[2:], (b'', BAD), 'a whole record answered, a cut one answered by the zeros')
                self.assertLess(r.ticks, 100000)


class CheckedAsker(unittest.TestCase):
    """26.6: far_get_ck.tw alone (the answers are given by the test), then with the answerer and the go-between."""

    def test_the_records_and_the_cells(self):
        rc, out, err = single_err('far_get_ck', CK_ANSWERS)
        self.assertEqual((rc, out, err), (0, CK_ASKED, ck_cells()))
        self.assertEqual(ck_cells(), b'PA' + bytes([rev(165, 8)] * 2) + ONES * 2 + b'O' + ONES)

    def test_a_pair_which_is_not_a_pair_is_asked_again(self):
        """The first answer is wrong (the byte changed): the same record is sent again, and the cells are all right."""
        for k in range(2):
            bad = bytearray(CK_ANSWERS[:2] + CK_ANSWERS)
            bad[k] ^= 16
            with self.subTest(byte=k):
                rc, out, err = single_err('far_get_ck', bytes(bad))
                self.assertEqual((rc, out, err), (0, CK_ASKED[:7] + CK_ASKED, ck_cells()))

    def test_four_tries_and_the_prohibitive_price(self):
        """The first four answers are all zeros: after the 4th try the cell is ones and the next request goes on (and gets its answer)."""
        rc, out, err = single_err('far_get_ck', BAD * 4 + CK_ANSWERS[2:])
        self.assertEqual((rc, err), (0, ONES + ck_cells()[1:]))
        self.assertEqual(out, CK_ASKED[:7] * 4 + CK_ASKED[7:])

    def test_a_closed_channel(self):
        """No answer at all (EOF): every request is sent 4 times, all cells are ones, the stop is sent, the asker ends and does not hang."""
        rc, out, err = single_err('far_get_ck', b'')
        self.assertEqual((rc, err), (0, ONES * 8))
        self.assertEqual(out, b''.join(rec_ck(*o) * 4 for o in CK_OPS) + rec_ck(STOP, 0))

    def test_ticks(self):
        """The measure (the checked emulator): the whole script of 8 requests, 6 get and 2 put (the answerer works: no repeat), and one repeat (the asker alone)."""
        ok = single('far_get_ck', CK_ANSWERS).ticks
        one = single('far_get_ck', BAD + CK_ANSWERS).ticks
        old = single('far_get', b'abcdef').ticks
        sys.stderr.write('checked asker ticks: 8 requests %d (far_get.tw: %d), one repeat +%d\n' % (ok, old, one - ok))
        self.assertTrue(old < ok < 2000 and 0 < one - ok < 300, (ok, one))


class CheckedChannel(unittest.TestCase):
    """26.6: the asker and the answerer through the go-between which changes given bytes. The records are 7 bytes (the number of the byte of the request stream: 7 * the number of
    the attempt + the field: 0 op, 1..4 pos, 5 dat, 6 ck), the answers 2 bytes (2 * the number of the attempt + 0 value, 1 complement). An attempt is a request sent: with no repeats attempt k is the request k."""

    cells = ck_cells()

    def run3(self, req=None, ans=None):
        r, q, nreq, nans = run_mediated(plan_fault(req or {}), plan_fault(ans or {}))
        return r, q, nreq, nans

    def test_no_faults_the_same_as_before(self):
        r, q, nreq, nans = self.run3()
        self.assertEqual((r, q), ((0, b''), (0, self.cells)))
        self.assertEqual((nreq, nans), (len(CK_ASKED), len(CK_ANSWERS)), 'every request once, one answer each, the stop')
        (rr, qr), _, _ = run_pair('far_get_ck', serve='far_serve_ck')              # with no go-between
        self.assertEqual((rr, qr), ((0, b''), (0, self.cells)))

    def test_one_spoiled_answer_the_copy_is_right_by_the_repeat(self):
        for k in range(8):
            for byte in (0, 1):
                with self.subTest(request=k, byte=byte):
                    r, q, nreq, nans = self.run3(ans={2 * k + byte: 0x5a})
                    self.assertEqual((r, q), ((0, b''), (0, self.cells)), 'the cells as with no fault')
                    self.assertEqual((nreq, nans), (len(CK_ASKED) + 7, len(CK_ANSWERS) + 2), 'one more attempt')

    def test_one_spoiled_request_the_copy_is_right_by_the_repeat(self):
        """Every byte of the request of a get (0) and of a put (2): the answerer does not do it (the sum), says 0, 0, the asker repeats. A put with a changed pos or dat writes nothing wrong."""
        for k in (0, 2, 5):
            for byte in range(7):
                for mask in (1, 0x80, 0xff):
                    with self.subTest(request=k, byte=byte, mask=mask):
                        r, q, nreq, nans = self.run3(req={7 * k + byte: mask})
                        self.assertEqual((r, q), ((0, b''), (0, self.cells)))
                        self.assertEqual((nreq, nans), (len(CK_ASKED) + 7, len(CK_ANSWERS) + 2))

    def test_all_the_tries_of_one_get_spoiled_ones_and_the_program_goes_on(self):
        """The answers of the 4 attempts of the request 0 (get 2) are all spoiled: the cell is ones (4 attempts, then the next request), all the others are right, nobody hangs."""
        r, q, nreq, nans = self.run3(ans={2 * a: 0x11 for a in range(4)})
        self.assertEqual((r, q), ((0, b''), (0, ONES + self.cells[1:])))
        self.assertEqual((nreq, nans), (len(CK_ASKED) + 3 * 7, len(CK_ANSWERS) + 3 * 2))

    def test_all_the_tries_of_a_put_spoiled_in_the_answer_the_put_was_done(self):
        """Put 3 <- 165 is the request 2 (attempts 2..5 when the first two went well): its answers are spoiled, the cell of the put is ones, but the answerer did the put (the request was right) and
        the next get of the cell 3 says so: a repeat of a put is harmless (idempotent)."""
        r, q, nreq, nans = self.run3(ans={2 * a + 1: 0x80 for a in range(2, 6)})
        want = self.cells[:2] + ONES + self.cells[3:]
        self.assertEqual((r, q), ((0, b''), (0, want)))
        self.assertEqual(want[3:4], bytes([rev(165, 8)]), 'get after the put: the put is there')

    def test_all_the_tries_of_a_put_spoiled_in_the_request_the_put_was_not_done(self):
        """The same put but the request of every attempt is spoiled (the sum fails): nothing is written, the cell of the put is ones and the get of the cell 3 gives the old byte of the window."""
        r, q, nreq, nans = self.run3(req={7 * a + 5: 0x01 for a in range(2, 6)})
        self.assertEqual((r, q), ((0, b''), (0, self.cells[:2] + ONES + WINDOW[3:4] + self.cells[4:])))
        self.assertEqual((nreq, nans), (len(CK_ASKED) + 3 * 7, len(CK_ANSWERS) + 3 * 2))

    def test_everything_spoiled_the_program_ends_with_ones(self):
        """One byte of every answer is changed (the first of each: a single fault of an answer is always seen), for ever: all the cells are ones, 4 attempts each, the asker ends."""
        r, q, nreq, nans = self.run3(ans={2 * a: 0x24 for a in range(40)})
        self.assertEqual((r, q), ((0, b''), (0, ONES * 8)))
        self.assertEqual((nreq, nans), (7 * 4 * 8 + 7, 2 * 4 * 8))

    def test_random_faults_never_a_wrong_cell(self):
        """Seeded plans (one byte of a record, the probability 0.3 both ways, masks 1..255): a cell is the right one or ones (the put 3 can also leave the old byte in the cell 3);
        some repeats did happen, and the pair always ends."""
        repeats = 0
        for seed in range(1, 9):
            req, ans = random_plan(seed, 0.3, 7, 40), random_plan(seed + 100, 0.3, 2, 40)
            with self.subTest(seed=seed):
                r, q, nreq, nans = self.run3(req, ans)
                self.assertEqual((r[0], q[0]), (0, 0))
                self.assertEqual(len(q[1]), 8)
                for i, c in enumerate(q[1]):
                    ok = {self.cells[i], ONES[0]} | ({WINDOW[3]} if i == 3 else set())
                    self.assertIn(c, ok, 'the cell %d: %r' % (i, q[1]))
                repeats += (nreq - len(CK_ASKED)) // 7
        self.assertGreater(repeats, 5)

    def test_the_answerer_is_cut_midway(self):
        """The answerer is cut by the limit of ticks: the asker gets EOF, repeats its tries to the end and puts ones; it ends. The cells are right up to the cut and ones after it."""
        (rr, qr), _, _ = run_pair('far_get_ck', serve_limit=300, serve='far_serve_ck')
        self.assertEqual((rr[0], qr[0]), (0, 0))
        cells = qr[1]
        self.assertEqual(len(cells), 8)
        self.assertEqual(cells[-1:], ONES)
        for i, c in enumerate(cells):
            self.assertIn(c, (self.cells[i], ONES[0]))
        self.assertLess(cells.count(ONES), 9)

    def test_ticks_and_sizes(self):
        """The measure: the answerer (the checked emulator; the difference to the stop alone), the asker (the whole script) and the images, the checked protocol against the old one (far_serve, far_get)."""
        stop = single('far_serve_ck', rec_ck(STOP, 0)).ticks
        base = single('far_serve', rec(STOP, 0)).ticks
        ck = {n: single('far_serve_ck', rec_ck(*o) + rec_ck(STOP, 0)).ticks - stop for n, o in [('get', (GET, 3)), ('get_out', (GET, 9)), ('put', (PUT, 3, 7)), ('put_out', (PUT, 9, 7)), ('bad', (GET, 3, 0, 0))]}
        old = {n: single('far_serve', rec(*o) + rec(STOP, 0)).ticks - base for n, o in [('get', (GET, 3)), ('put', (PUT, 3, 7))]}
        sizes = {n: len(program(n)['image']) for n in ('far_serve', 'far_serve_ck', 'far_get', 'far_get_ck')}
        sys.stderr.write('checked answerer ticks per request (stop alone %d): %s; old (stop alone %d): %s; images: %s\n' % (stop, ck, base, old, sizes))
        self.assertTrue(all(10 < v < 400 for v in ck.values()), ck)
        self.assertGreater(ck['get'], old['get'])
        self.assertGreater(ck['put'], old['put'])


def chain_text(src):
    """The stats of a text of language 4 built by the chain (the name is its text)."""
    if src not in _CACHE:
        chain_program(src, src)
    return src


def single_ticks(src, stdin):
    return single(src, stdin).ticks


if __name__ == '__main__':
    unittest.main()
