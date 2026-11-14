"""The images of the passes made by the chain itself (25.7.3.2), the one cache for all the tests: no Python reference of a pass is imported here. The first image, `seed`, is made from seed.l1 by l1text (as hex0); then every pass is made by the passes already made, on the plain emulator:
    seed        = l1text(seed.l1)
    l2c, l2l, l3c, l3p, l4c = seed(<pass>.l1)                         (the texts of language 1 of the passes; those of l3c, l3p, l4c are what l2l(l3c(<pass>.tw), twice)
                                                                       gives: test_l1_current.py checks the record, long_l1_current.py makes them again)
    a program   = seed(l2l(l3p(l3c(l4c(text)))))                        (l4c only for a text of language 4, l3p only when the text starts with `pack`)
The images of the passes are cached on disk between the processes of the tests (the directory COPYMACHINE_CHAIN_CACHE, else <tmp>/copymachine-chain-<uid>; never in the
repository): the file name holds the key, the hash of the emulator, of l1text.py, of this file, of the texts the pass is made from and of the keys of the passes which make it,
so a change of any of them makes the image again; a file is written whole to a temporary name and renamed, and one build under a lock of the file at a time (the other
process waits and takes the result); a temporary file older than an hour is removed. The images of the programs are kept in the memory of the process and on the
disk too (prog-<key>.img: the key holds the text, the layout and the keys of all the passes; a file not used for 3 days is removed when a pass is made again).
tool(name, pack=False) -> (image, A, P)    image(name) -> bytes    build(text, lang4=False) -> (image, P)    run_image(image, P, ...) -> Result"""
import fcntl
import hashlib
import os
import re
import sys
import tempfile
import threading
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
TOWER = os.path.join(HERE, '..')
sys.path.insert(0, TOWER)
import common
import l1text

PROGRAMS = os.path.join(common.HERE, 'programs')
LIMIT = 300 * 10 ** 6               # ticks of a pass on the plain emulator (the chain makes the biggest image in about 10 ** 8)
PASSES = ('seed', 'l2c', 'l2l', 'l3c', 'l3p', 'l4c')
FROM_L1 = ('l2c', 'l2l', 'l3c', 'l3p', 'l4c')     # the passes which the seed makes from their texts of language 1 (the pack variants of l3c, l3p, l4c: from .tw)
TIMES = {}                          # {name: seconds} of the passes made by this process (not taken from the disk)
_MEMO, _LOCKS, _GUARD, _KEYS = {}, {}, threading.Lock(), {}


def read(name):
    with open(os.path.join(PROGRAMS, name), 'rb') as h:
        return h.read()


def sha(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(len(p).to_bytes(8, 'big') + p)
    return h.hexdigest()


def _lock(key):
    with _GUARD:
        return _LOCKS.setdefault(key, threading.Lock())


def cache_dir():
    d = os.environ.get('COPYMACHINE_CHAIN_CACHE') or os.path.join(tempfile.gettempdir(), 'copymachine-chain-%d' % os.getuid())
    os.makedirs(d, exist_ok=True)
    return d


def is_pack(text):
    """Does the text of language 3 begin with the word `pack` (comments and blank lines before it are free)?"""
    for line in bytes(text if isinstance(text, (bytes, bytearray)) else text.encode('latin-1')).split(b'\n'):
        words = line.split(b'#')[0].split()
        if words:
            return words[0] == b'pack'
    return False


def header(name):
    """(A, P) from the first line of programs/<name>.l1."""
    m = re.search(rb'\(A=(\d+), P=(\d+)\)', read(name + '.l1').split(b'\n')[0])
    return (int(m.group(1)), int(m.group(2))) if m else (20, 2)


def _hashes():
    """The hashes of the files whose change makes every image again: the emulator, l1text.py, this file."""
    with _GUARD:
        if 'emu' not in _KEYS:
            for k, path in (('emu', common.EMU), ('l1text', os.path.join(TOWER, 'l1text.py')), ('chain', os.path.abspath(__file__))):
                with open(path, 'rb') as h:
                    _KEYS[k] = hashlib.sha256(h.read()).hexdigest()
        return _KEYS['emu'], _KEYS['l1text'], _KEYS['chain']


def key(name, pack=False):
    """The key of the image of a pass: the emulator, l1text.py, chain.py, the text it is made from, and the keys of the passes which make it."""
    emu, l1t, me = _hashes()
    if name == 'seed':
        return sha(b'seed', emu.encode(), l1t.encode(), me.encode(), read('seed.l1'))
    if name in FROM_L1 and not pack:
        deps, src = [('seed', False)], read(name + '.l1')
    else:
        deps = [('seed', False), ('l2l', False), ('l3c', False)] + ([('l3p', False)] if pack else [])
        src = read(name + '.tw')
    return sha(name.encode(), b'pack' if pack else b'', emu.encode(), me.encode(), src, *(key(d, p).encode() for d, p in deps))


def run_pass(name, stdin, checked=False):
    """The Result of a run of the serial pass `name` (no check of the answer: a pass may refuse its input)."""
    img, A, P = tool(name)
    return common.run(img, A, P, checked=checked, limit=LIMIT, stdin=stdin)


def step(tag, name, stdin):
    """The output of the serial pass `name` on the plain emulator for stdin; the pass must end by itself without a word on stderr."""
    r = run_pass(name, stdin)
    assert r.rc == 0 and not r.err.strip(), (tag, r.rc, r.err)
    return r.out


def _make(name, pack):
    if name == 'seed':
        img, err = l1text.encode(read('seed.l1') + b'\0')
        assert err is None, err
        return img
    if name in FROM_L1 and not pack:
        return step(name, 'seed', read(name + '.l1') + b'\0')
    return step(name, 'seed', language1(read(name + '.tw'), pack=pack))


def language1(text, lang4=False, pack=False):
    """The text of language 1 (with its zero byte) of a text of language 3 by the passes of the chain: [l4c] -> l3c -> [l3p] -> l2l (the text twice);
    a text of language 4 goes through l4c first (lang4); the planner l3p works when the text begins with `pack` (or pack: the word is put first)."""
    src = text.encode('latin-1') if isinstance(text, str) else bytes(text)
    if pack:
        src = b'pack\n' + src
    if lang4:
        src = step('l4c', 'l4c', src + b'\0')[:-1]
    l2 = step('l3c', 'l3c', src + b'\0')
    if is_pack(src):
        l2 = step('l3p', 'l3p', l2)
    return step('l2l', 'l2l', l2 + l2)


def _file(name, k):
    return os.path.join(cache_dir(), '%s-%s.img' % (name.replace('/', '-'), k[:40]))


def tool(name, pack=False):
    """(image, A, P) of a pass; with pack the pass made by the chain with the planner (l3c, l3p, l4c: P = 3). Made once: by the process, by the disk cache, else by the chain."""
    mk = (name, pack)
    with _lock(mk):
        if mk not in _MEMO:
            label = name + ('-pack' if pack else '')
            path = _file(label, key(name, pack))
            img = _load(path)
            if img is None:
                with open(path + '.lock', 'w') as lk:
                    fcntl.flock(lk, fcntl.LOCK_EX)              # one process makes the image, the others wait for it
                    img = _load(path)
                    if img is None:
                        t0 = time.time()
                        img = _make(name, pack)
                        TIMES[label] = time.time() - t0
                        tmp = '%s.%d.%d.tmp' % (path, os.getpid(), threading.get_ident())
                        with open(tmp, 'wb') as h:
                            h.write(img)
                        os.replace(tmp, path)
                        _prune(label, os.path.basename(path))
            A, P = header(name) if name in ('seed',) + FROM_L1 and not pack else (20, 3 if pack else 2)
            _MEMO[mk] = (img, A, P)
        return _MEMO[mk]


def _load(path):
    try:
        with open(path, 'rb') as h:
            return h.read()
    except OSError:
        return None


def _prune(name, keep):
    """After the image `keep` of the pass `name` is made: the images of the same pass made with other keys go; so do the temporary files older than an
    hour (a process which died) and the images of the programs not used for 3 days (their keys hold the keys of the passes, so after a change of a pass they are never asked for)."""
    pre, now, d = name.replace('/', '-') + '-', time.time(), cache_dir()
    for f in os.listdir(d):
        path = os.path.join(d, f)
        old = (f.endswith('.tmp') and 3600) or (f.startswith('prog-') and 3 * 86400)
        try:
            if f.startswith(pre) and re.fullmatch(r'[0-9a-f]{40}\.img(\.lock)?', f[len(pre):]) and not f.startswith(keep) or old and now - os.stat(path).st_mtime > old:
                os.remove(path)
        except OSError:
            pass


def image(name, pack=False):
    return tool(name, pack)[0]


def build(text, lang4=False):
    """The image of a text of language 3 (4 with lang4: l4c goes first) built by the chain and its P: 3 in the pack mode, else 2.
    Once per text: by the process, by the disk cache (the key: the text, lang4 and the keys of all the passes), else by the chain."""
    src = text.encode('latin-1') if isinstance(text, str) else bytes(text)
    mk = ('program', src, lang4)
    with _lock(mk):
        if mk not in _MEMO:
            path = os.path.join(cache_dir(), 'prog-%s.img' % sha(b'program', b'4' if lang4 else b'3', src, *(key(n).encode() for n in PASSES))[:40])
            img = _load(path)
            if img is None:
                img = step('seed', 'seed', language1(src, lang4))
                tmp = '%s.%d.%d.tmp' % (path, os.getpid(), threading.get_ident())
                with open(tmp, 'wb') as h:
                    h.write(img)
                os.replace(tmp, path)
            else:
                os.utime(path)
            _MEMO[mk] = (img, 3 if is_pack(src) else 2)
        return _MEMO[mk]


def run_image(img, P=2, stdin=b'', checked=True, limit=10 ** 7, files=()):
    """One run of an image made by the chain (A = 20) on the checked emulator (or the plain one): the Result of common.run (out, rc, err, ticks)."""
    return common.run(img, 20, P, checked=checked, limit=limit, stdin=stdin, files=files)


def says(r):
    """What a run wrote to stderr (without the audit line of the checking emulator)."""
    return r.err.split('VM1_AUDIT')[0]
