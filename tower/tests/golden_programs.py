"""Frozen whole chains of programs and the fixed points of the passes (25.7.3.1), the second half of tower/golden (see test_golden.py and tower/golden/README).
tower/golden/programs.jsonl has a line for every program laid out in a layout (serial or `pack`): the text (a file of tower/ or of golden/in, or inline), how it
goes through the chain (`hoist`: the data and tables moved out of the blocks as the tests of l3c do; `lang4`: the pass l4c first), the length and sha256 of the image
which the chain makes of it (l4c -> l3c -> [l3p] -> l2l -> seed, every pass is an image on the checked emulator, as in test_golden.tool), the runs of that image
(stdin, the host file `-r` when the program uses the host: rc, stderr, output, ticks on the checked emulator), the cost of the layout (rows, layers, bits of the layers)
and the price of language 5 (32 rows + 32 layers + bits + 64 ticks of the first run; the cheaper layout of a program is the one with the smaller price). The lines
named fixed/... freeze the fixed points: l3c (and l3c with the planner, `pack`) builds its own text into the text l3c.l1 and the image which built it.
The images are made by chain.py (the passes made by the chain itself); the update
(`GOLDEN_UPDATE=1 python3 -B tower/tests/test_golden.py`) freezes what the chain gives now (the image, the runs, the cost counted from the texts of language 2 which l3c
and l3p write) and prints what it changes first."""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import chain
import common
import l1text
import test_golden as g
from common import run

FILE = os.path.join(g.GOLDEN, 'programs.jsonl')
RUN_LIMIT = 10 ** 7             # ticks of a run of a program (a program which does not end by then is cut: the rest of the line says how)
HOSTFILE = bytes(range(1, 65))      # the host file given to a program which uses the host (test_l4p.py: FILE)
PRICE_W = (32, 32, 1, 64)           # rows, layers, bits, ticks (as l5.PRICE_W)
SHORTCUT = {'l3c/serial': 'l3c', 'l3p/serial': 'l3p', 'l4c/serial': 'l4c'}     # their images are those of g.tool (built by the chain, the fixed points check them again)
BIG = 300 * 10 ** 6


def sha(b):
    return hashlib.sha256(b).hexdigest()


def hoist(src):
    """The text with its data, tables and arrays moved out of the blocks (to the top, in their order) and 0x numbers written in decimal: what l3c takes
    (the host helper of the tests of l3c; the declarations are one line each, or the lines of a table up to the next label or word)."""
    src = re.sub(r'\b0[xX]([0-9a-fA-F]+)\b', lambda m: str(int(m.group(1), 16)), src)
    decl, rest, lines, i = [], [], src.split('\n'), 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r':\w+\s+(data|table|array)\b', ln):
            decl.append(ln)
            i += 1
            while i < len(lines) and not re.match(r'\s*(:|#|[a-z!@]+\s)', lines[i]) and lines[i].strip() and not re.match(r'\s*(ret|halt)\s*$', lines[i]):
                decl.append(lines[i])
                i += 1
            continue
        rest.append(ln)
        i += 1
    return '\n'.join(decl + rest)


# ---- the chain

step = chain.step                    # one pass on the plain emulator (the passes are audited on the checked one in test_golden.py)


def build_image(src, pack=False, lang4=False):
    """text of language 3 (4 with lang4) -> [l4c] -> l3c -> [l3p] -> l2l (the text twice) -> seed -> the image; pack: the word `pack` first (chain.build)."""
    return chain.build(('pack\n' if pack else '').encode() + src, lang4)[0]


def source(e):
    """The text of an entry: inline, or a file (of tower/ or of golden/), hoisted when told."""
    if 'in' in e:
        return e['in'].encode('latin-1')
    with open(os.path.join(common.HERE if e['file'].startswith('programs/') else g.GOLDEN, e['file']), 'rb') as h:
        b = h.read()
    return hoist(b.decode()).encode() if e.get('hoist') else b


def image_of(e):
    if e['name'] in SHORTCUT:
        return g.tool(SHORTCUT[e['name']])[0]
    return build_image(source(e), e['pack'], e.get('lang4', False))


def run_image(img, pack, spec):
    """One run on the checked emulator: spec is {'in': stdin (latin-1), 'host': True when the host file is given}; returns the result and the host file after."""
    d = tempfile.mkdtemp(prefix='golden-prog-')
    try:
        f = os.path.join(d, 'f.bin')
        with open(f, 'wb') as h:
            h.write(HOSTFILE)
        r = run(img, 20, 3 if pack else 2, checked=True, limit=RUN_LIMIT, stdin=spec.get('in', '').encode('latin-1'), files=[f] if spec.get('host') else ())
        with open(f, 'rb') as h:
            return r, h.read()
    finally:
        shutil.rmtree(d, True)


def run_line(r, hfile, spec):
    line = dict(spec)
    line['rc'], line['err'], line['ticks'] = r.rc, g.says(r), r.ticks
    if len(r.out) <= g.INLINE_OUT:
        line['out'] = r.out.decode('latin-1')
    else:
        line['len'], line['sha'] = len(r.out), sha(r.out)
    if spec.get('host'):
        if len(hfile) <= g.INLINE_OUT:
            line['hfile'] = hfile.decode('latin-1')
        else:
            line['hlen'], line['hsha'] = len(hfile), sha(hfile)
    return line


def price(cost, ticks):
    return sum(a * b for a, b in zip(PRICE_W, list(cost) + [ticks], strict=True))


# ---- the manifest

def load():
    with open(FILE, encoding='utf-8') as h:
        return [json.loads(x) for x in h if x.strip()]


def check_entry(e):
    """The problems of one entry of an image (empty when the chain agrees with it)."""
    bad = []
    img = image_of(e)
    if (len(img), sha(img)) != (e['len'], e['sha']):
        bad.append('image length %d sha %s, expected %d %s' % (len(img), sha(img)[:12], e['len'], e['sha'][:12]))
    for want in e.get('runs', []):
        spec = {k: want[k] for k in ('in', 'host') if k in want}
        r, hfile = run_image(img, e['pack'], spec)
        got = run_line(r, hfile, spec)
        if got != want:
            bad.append('run %r: %r, expected %r' % (spec.get('in', '')[:20], {k: v for k, v in got.items() if got[k] != want.get(k)}, {k: want.get(k) for k in got if got[k] != want.get(k)}))
    if 'price' in e:
        if e['price'] != price(e['cost'], e['runs'][0]['ticks']):
            bad.append('price %r, expected %r' % (e['price'], price(e['cost'], e['runs'][0]['ticks'])))
    return bad


def check_tier(tc, tier):
    """The image lines of the tier ('fast', 'long' or 'full', g.tier_of): the chain makes the image, the runs and the prices are those of the manifest."""
    es = [e for e in load() if 'fixed' not in e and g.tier_of(e) == tier]
    tc.assertTrue(es)
    with ThreadPoolExecutor(g.WORKERS) as ex:
        res = list(ex.map(check_entry, es))
    for e, bad in zip(es, res, strict=True):
        with tc.subTest(name=e['name']):
            tc.assertEqual(bad, [], e['name'])
    return len(es)


def cheaper(name):
    """The layout of a program the price chooses (language 5, layout.replace_layout): 'serial' or 'pack' (serial when equal), from the manifest."""
    p = {e['name']: e['price'] for e in load() if e['name'] in (name + '/serial', name + '/pack')}
    return 'pack' if p[name + '/pack'] < p[name + '/serial'] else 'serial'


# ---- the fixed points

_FUTURES = {}


def start(with_fixed=True):
    """Long tier: build at once, side by side, the tools made by the chain (l3p and l4c, three passes each; the disk cache of chain.py has them already after the first
    run) and the fixed points; the tests take the results. Three threads (with the pool of the tests at most four processes of the emulator and, under
    tools/limited_run.py, the arenas of malloc fit in 768 MiB)."""
    pool = ThreadPoolExecutor(3)
    _FUTURES['l3p'] = pool.submit(g.tool, 'l3p')
    _FUTURES['l4c'] = pool.submit(g.tool, 'l4c')
    if with_fixed:
        _FUTURES['fixed'] = pool.submit(fixed)
    pool.shutdown(wait=False)


def _serial():
    """l3c.tw -> (the image of l3c) -> l2 -> l2l -> the text of language 1 of l3c: the same text; the seed on it is the image which made it (g.tool('l3c'))."""
    out, eq = {}, {}
    l3c_tw = g.read('l3c.tw')
    out['l2'] = l2 = g.cached_run('l3c', l3c_tw + b'\0').out         # the tool-l3c entry of l3c.jsonl is the same run
    out['l1'] = l1 = step('l2l', 'l2l', l2 + l2)
    eq['serial: l3c builds the text of language 1 it was made from'] = l1 == g.read('l3c.l1') + b'\0'
    out['img'] = g.tool('l3c')[0]
    return out, eq


def _packed():
    """`pack` + l3c.tw -> l3c (serial) -> l3p -> l2l -> seed: the packed l3c (P = 3); it builds the same text of language 2 from the same text."""
    out, eq = {}, {}
    src = b'pack\n' + g.read('l3c.tw')
    out['p_l2'] = p_l2 = step('l3c', 'l3c', src + b'\0')
    out['p_l2_planned'] = planned = step('l3p', 'l3p', p_l2)
    out['p_l1'] = p_l1 = step('l2l', 'l2l', planned + planned)
    out['p_img'] = img0 = step('seed', 'seed', p_l1)
    again = run(img0, 20, 3, checked=False, limit=BIG, stdin=src + b'\0')
    eq['packed: the packed l3c builds the same text of language 2'] = (again.rc, again.out) == (0, p_l2)
    return out, eq


def fixed():
    """The fixed points on the chain, no Python: l3c builds its own text. Returns ({step: bytes}, {what holds: bool}).
    Serial: the image of l3c (the seed on l3c.l1; A = 20, P = 2, serial) turns l3c.tw into a text of language 2 which l2l turns into l3c.l1 again, so that the seed
    turns it into the same image (the seed on the same text, the image it made). With the planner (`pack` first): the serial l3c and the planner l3p make of
    `pack` + l3c.tw the packed l3c (P = 3); that image makes, from the same text, the same text of language 2, so with the planner, l2l and the seed (the same
    tools on the same texts) the same text of language 1 and the same image: it builds itself."""
    (o1, e1), (o2, e2) = _serial(), _packed()
    return {**o1, **o2}, {**e1, **e2}


def fixed_line():
    out, eq = fixed()
    line = {'name': 'fixed/l3c', 'fixed': True}
    for k, v in out.items():
        line[k] = [len(v), sha(v)]
    return line, eq


def check_fixed(tc):
    """The long tier: the fixed points hold and the texts and images are those of the manifest."""
    out, eq = _FUTURES['fixed'].result() if 'fixed' in _FUTURES else fixed()
    want = next(e for e in load() if e.get('fixed'))
    for k, v in eq.items():
        with tc.subTest(k):
            tc.assertTrue(v, k)
    for k, v in out.items():
        with tc.subTest(k):
            tc.assertEqual([len(v), sha(v)], want[k], k)


# ---- the update (GOLDEN_UPDATE=1: what the chain gives now; the checks above are made against the manifest)

STDINS = {
    'echo': [b'hello, chain\0', b'\0tail'],
    'arith8': [b'\xa5\x3c', b'\x00\x80', b'\xff\xff'],
    'arith16': [b'\x12\x34\x56\x78', b'\x00\x00\x00\x00', b'\xff\xff\x00\x01'],
    'far_get': [b'abcdef'],
    'far_get_ck': [b'P\xafA\xbe\xa5Z\xa5Z\xff\x00\xff\x00O\xb0\xff\x00'],
    'far_serve': [b'', b'\x80@\x00\x00\x00\x00', b'\x80@\x00\x00\x00\x00\x80\x80'],
    'far_serve_ck': [b'', b'\x80@\x00\x00\x00\x00\xc0\x80'],
    'assoc_hash': [b'', b'\x80\x00\x00\x80\x08\x88\x80\x04D\x80\x80\xc0\x80\xb2\xb2\x80\x01\x80\x80\x13&\x80\x7f\x7f\x00'],
    'assoc_tree': [b'', b'\x80\x80\xe0\x80H\xe0\x00', b'\x80\x00\x00\x80\x08\x88\x80\x04D\x80\x80\xc0\x80\xb2\xb2\x80\x01\x80\x80\x13&\x80\x7f\x7f\x00'],
    'seed': [b'w 10\nr 1 2 3 4\n\0', b's 11110000\nq\n\0'],
    'l2c': [b'c 8 10 20\n\0', b'c 1 &a 2\n\0'],
    'l2l': [b':a d 8 5\nc 4 &a+1 &a\n\0:a d 8 5\nc 4 &a+1 &a\n\0', b'c 1 &x 2\n\0c 1 &x 2\n\0'],
    'l3c': [b':a data 8 5\n:main block\nhalt\n\0', b'foo\0'],
    'l4c': [b':a data 8 0\n:main block\ncopy &a 0x100000000000000010000000000000008\nhalt\n\0'],
}
HOST_TEXT = re.compile(rb'0x1[0-9a-f]{32}\b')
PACKED_FORTH = ['return_stack', 'constant', 'pick_roll', 'execute', 'stack', 'calls', 'shifts', 'variables', 'begin_until', 'strings']     # long_forth37.py
CLOCK = {'long_clock'}              # reads the clock of the host: its output is the time, no run is frozen
NO_PACK = {'l3c', 'l3p', 'l4c'}     # the packed tools take minutes: their fixed points are in fixed/
FAST_IMAGE = 2600                   # a serial image of a program of language 3 up to this size (bytes) is in the fast tier, the rest is long


def variants(src, hoisted_first):
    """(hoist, lang4) by which the chain takes the text (the first that is without an error), or None. The programs of programs/ are hoisted first, as the
    tests of l3c take them (the text with the data out of the blocks); the others (far, assoc, prove, forth37) as they are: their tests give the text itself."""
    for hoist_, lang4 in (((True, False), (False, False), (False, True), (True, True)) if hoisted_first else ((False, False), (False, True), (True, False), (True, True))):
        text = hoist(src.decode()) if hoist_ else src.decode()
        try:
            chain.build(text, lang4)
        except AssertionError:                      # a pass of the chain refused the text
            continue
        return hoist_, lang4
    return None


def specs():
    """[(name, how to read the text, the stdins of the runs)] of the programs the manifest freezes, and the programs that do not go through the chain."""
    out, left = [], []
    top = sorted(f for f in os.listdir(g.PROGRAMS) if f.endswith('.tw'))
    rels = top + ['far/' + f for f in sorted(os.listdir(os.path.join(g.PROGRAMS, 'far')))] + ['assoc/' + f for f in sorted(os.listdir(os.path.join(g.PROGRAMS, 'assoc')))] \
        + ['prove/' + f for f in sorted(os.listdir(os.path.join(g.PROGRAMS, 'prove')))] + ['forth37/' + f for f in sorted(os.listdir(os.path.join(g.PROGRAMS, 'forth37'))) if f.endswith('.tw')]
    for rel in rels:
        if rel in ('forth.tw', 'forthgen.tw'):
            left.append((rel, 'images of 80..100 KB: the chain needs minutes'))
            continue
        with open(os.path.join(g.PROGRAMS, rel), 'rb') as h:
            src = h.read()
        v = variants(src, '/' not in rel)
        if v is None:
            left.append((rel, 'not a text of the chain (l3c refuses it)'))
            continue
        base = os.path.basename(rel)[:-3]
        stdins = STDINS.get(base, [b''])
        if base == 'seed':
            stdins = stdins + [g.read('seed.l1') + b'\0']             # the fixed point of the seed: its own text gives its own image (the image made by the chain too)
        out.append(dict(rel=rel, name=rel[:-3], hoist=v[0], lang4=v[1], stdins=stdins, host=bool(v[1] and HOST_TEXT.search(src))))
        if base in CLOCK:
            out[-1]['stdins'] = []
    return out, left


def extra_programs():
    """The programs of the tests which are not files: the programs of test_l4p.py (host files), the README example, the channel forms, the texts of Forth made by forth.tw."""
    import test_far as tfar
    import test_l4p as t4
    out = []
    for n, src in sorted(t4.PROGRAMS.items()):
        out.append(dict(name='l4p/' + n, text=src.encode(), lang4=True, hoist=False, stdins=[b''], host='0x1' in src))
    out.append(dict(name='l4p/readme', text=t4.readme_example().encode(), lang4=True, hoist=False, stdins=[b''], host=True))
    out.append(dict(name='l4p/channel-forms', text=t4.CHAN_FORMS.encode(), lang4=True, hoist=False, stdins=[b'Z'], host=False))
    out.append(dict(name='far/copy-at', text=tfar.FarCopyAt.SRC.encode(), lang4=True, hoist=False, stdins=[b''], host=False))        # test_far.py: built by the chain
    for n, tw_text in forth_texts():                              # the texts of language 3 which forth.tw writes (test_forth.py: built serial by the chain)
        out.append(dict(name='forth/' + n, text=tw_text, lang4=False, hoist=False, stdins=[b''], host=False, serial_only=True))
    head = ':a data 8 1\n:b data 8 2\n:c data 8 3\n:d data 8 4\n:e data 8 5\n:f data 8 6\n:t table 1 8 7 9\n:o data 8 0\n:main block\n'
    for k, body in enumerate(('copy &a &b\ncopy &c &d\nhalt\n', 'copy &a &b\ncopy &c &d\ncopy &e &f\nhalt\n', 'copy &a &b\ncopy &c &a\nhalt\n', 'copy &a &b\ncopy &d &b\nhalt\n',
                              'copy &a &b\ncopy &d &a\ncopy &b &d\nhalt\n', 'copy &a &b\nhalt\n', 'lut &t &d[0] &o\nhalt\n', 'lut &t &d[0] &o\ncopy &e &f\nhalt\n',
                              'lut &t &d[0] &o\nlut &t &e[0] &f\nhalt\n')):          # test_l3p.py, the rules of the schedule: the layers of the planner are 1 2 2 2 3 1 4 4 5
        out.append(dict(name='sched/%d' % k, text=(head + body).encode(), lang4=False, hoist=False, stdins=[b''], host=False))
    out.append(dict(name='sched/example', text=b':a data 8 5\n:b data 8 0\n:main block\ncopy &b &a\nemit &b\nhalt\n', lang4=False, hoist=False, stdins=[b''], host=False))   # (5, 3, 480), (4, 2, 400)
    out.append(dict(name='l5/empty-main', text=b':main block\nhalt\n', lang4=False, hoist=False, stdins=[b''], host=False))        # test_l3p.py, class Price: nothing to pack, serial is cheaper
    out.append(dict(name='l4p/channel-words', text=t4.CHAN_WORDS.encode(), lang4=True, hoist=False, stdins=[b'Z'], host=False))
    return out


def forth37_expected():
    out = {}
    with open(os.path.join(g.PROGRAMS, 'forth37', 'expected.txt'), encoding='utf-8') as h:
        for line in h:
            if line.strip() and not line.startswith('#'):
                n, v = line.split()
                out[n] = bytes.fromhex(v)
    return out


PACK_P = 3                          # the slots of the first layer of a packed block (l3p)


def layout_cost(l2, packed):
    """(rows, layers, bits) of the blocks of a text of language 2 which l3c writes (serial layout) or l3p writes (packed layout), counted from the text: a block is
    the lines from `:b...` up to the jump row whose target is 0 or a label; its slots are the rows (`c n d s`, four `d 14 x` lines, `z 50`) and the jump rows
    (`c n 0 target`); layers are the jump rows, rows are the rows which do something (not `z 50`) with the jump rows, bits 160 a layer when serial, 80 a slot when
    packed. The empty slots of a packed layer follow its jump row; those of the last layer are not told from the pad of a table which may follow the block, so they
    are counted by the rule of l3p: a layer has as many slots as the dearer of it and the layer before (the first one has PACK_P), the slots are its rows and its jump."""
    lines, i, slots, empty = l2.decode('latin-1').split('\n'), 0, 0, 0
    jumps = 0
    while i < len(lines):
        if not lines[i].startswith(':b'):
            i += 1
            continue
        i += 1
        w, cur = [], 0
        while True:
            ln = lines[i]
            i += 4 if ln.startswith('d') else 1
            slots += 1
            p = ln.split()
            if ln == 'z 50':
                empty += 1
            elif ln.startswith('c ') and p[2] == '0':
                jumps += 1
                w.append(cur + 1)
                cur = 0
                if p[3] == '0' or p[3][0] == '&':
                    break
            else:
                cur += 1
        if packed:
            pad = max(0, w[-2] - w[-1]) if len(w) > 1 else PACK_P - w[0]
            slots += pad
            empty += pad
    return slots - empty, jumps, (80 * slots if packed else 160 * jumps)


def cost_of(text, pack, lang4):
    """[rows, layers, bits] of the program in its layout, from the texts which l3c (and l3p when packed) write; None when the planner does not take the text (the data
    in the blocks: the texts of forth.tw, l3c refuses them in the pack mode)."""
    src = ('pack\n' + text.decode('latin-1').removeprefix('pack\n')).encode('latin-1')
    if lang4:
        src = step('l4c', 'l4c', src + b'\0')[:-1]
    r = chain.run_pass('l3c', src + b'\0')
    if 'l3c: bad block' in r.err:                         # (the stderr of l3c: the data in the blocks)
        return None
    assert r.rc == 0 and not r.err.strip(), (r.rc, r.err)
    l2 = r.out
    if pack:
        l2 = step('l3p', 'l3p', l2)
    rows, layers, bits = layout_cost(l2, pack)
    return [rows, layers, bits]


def update_lines(diffs=None):
    """The lines of programs.jsonl as the chain makes them now: (the lines, what is not frozen, {the files of golden/in to write: bytes}); nothing is written here."""
    todo, files = [], {}
    sp, left = specs()
    sp += extra_programs()
    for s in sp:
        if 'text' not in s:
            with open(os.path.join(g.PROGRAMS, s['rel']), 'rb') as h:
                s['text'] = h.read()
            s['file'] = 'programs/' + s['rel']
        text = hoist(s['text'].decode()).encode() if s['hoist'] else s['text']
        for pack in (False, True):
            base = os.path.basename(s['name'])
            if pack and (base in NO_PACK or s.get('serial_only')):          # (the texts of forth.tw have the data in the blocks: no pack mode)
                continue
            todo.append((s, text, pack))

    def one(item):
        s, text, pack = item
        e = {'name': s['name'] + ('/pack' if pack else '/serial')}
        if 'file' in s:
            e['file'] = s['file']
        elif len(s['text']) <= g.INLINE_IN:
            e['in'] = s['text'].decode('latin-1')
        else:
            e['file'] = 'in/prog-%s.txt' % s['name'].replace('/', '-')
            files[e['file']] = s['text']
        if s['hoist']:
            e['hoist'] = True
        if s['lang4']:
            e['lang4'] = True
        e['pack'] = pack
        img = build_image(text, pack, s['lang4'])
        e['len'], e['sha'] = len(img), sha(img)
        runs = []
        for stdin in s['stdins']:
            spec = {}
            if stdin:
                spec['in'] = stdin.decode('latin-1')
            if s['host']:
                spec['host'] = True
            r, hfile = run_image(img, pack, spec)
            runs.append(run_line(r, hfile, spec))
        if s['name'].startswith('forth37/'):                    # the output is that of expected.txt (long_forth37.py)
            want = forth37_expected()[os.path.basename(s['name'])]
            if (runs[0]['rc'], runs[0].get('out', '').encode('latin-1')) != (0, want) and diffs is not None:
                diffs.append('%s: the output %r, expected.txt %r' % (e['name'], runs[0].get('out', runs[0].get('sha')), want))
        e['runs'] = runs
        cost = cost_of(text, pack, s['lang4'])
        if cost:
            e['cost'] = cost
            if runs:
                e['price'] = price(cost, runs[0]['ticks'])
        if pack or s['lang4'] or len(img) > FAST_IMAGE or e['name'] in SHORTCUT or s['name'].startswith(('forth37/', 'forth/')):        # the fast tier has the tools up to l3c: no planner, no l4c, small images
            e['long'] = True
        return e

    with ThreadPoolExecutor(g.WORKERS) as ex:
        lines = list(ex.map(one, todo))
    fl, eq = fixed_line()
    lines.append(fl)
    for k, v in eq.items():
        if not v and diffs is not None:
            diffs.append('fixed point: %s does not hold' % k)
    return lines, [(n, why) for n, why in left], files


def write_lines(lines):
    with open(FILE, 'w', encoding='utf-8') as h:
        for e in lines:
            h.write(json.dumps(e, separators=(',', ':')) + '\n')


def forth_texts():
    """[(name, text of language 3 without the zero byte)] which forth.tw (the chain: seed on forth.l1) writes for the Forth texts of test_forth.py."""
    import test_forth as tf
    tl = tf.tools()
    fs_texts = [(n, tf.source(n)) for n in tf.SMALL]
    fs_texts.append(('other-words', (b'\\ a comment\n: sq dup * ; 5 sq 48 + emit ( a comment ) \n'
                                    b': verylongname 3 ; : again verylongname 1+ ; again 48 + emit\n'
                                    b': f dup 3 < if 1+ recurse then ; 0 f 48 + emit\n'
                                    b'create tab 4 allot 7 tab c! tab c@ 48 + emit s" abcdefghij" swap drop 48 + emit\n'
                                    b': main 2 0 do 2 0 do j 48 + emit i 48 + emit loop loop 9 0 ?do 66 emit leave loop ; \\ the end\n')))
    out = []
    for n, fs in fs_texts:
        tw_text = tf.step('forth', tl['forth'], fs + b'\0').out
        assert tw_text.endswith(b'\0')
        out.append((n, tw_text[:-1]))
    return out


def extra_cases():
    """[(pass, name, text, mode)]: the inputs of the tests of the passes against the references which test_golden.cases() does not have (25.7.3.1): the lists and
    the seeds of test_l4p.py (language 4) and long_l3c.py (spoiled texts), the texts of language 1 and 2 of the programs as the tests make them, the texts of
    Forth made by forth.tw, forth37, the pack mode on 1020/1021 names. The texts the passes make for each other (the inputs of l2l, seed, l3p in the chains) are
    the chains of the manifest of the programs. The ones that cases() has are left out (the same text of the same pass and mode)."""
    import random

    import test_far as tfar
    import test_l3c as t3
    import test_l3p as tp
    import test_l4p as t4
    import text as tw
    out = []

    def add(pas, name, text, mode=None):
        out.append((pas, name, text.encode('latin-1') if isinstance(text, str) else bytes(text), mode))

    def compiled(n):
        p, errs = tw.compile_text(g.read(n + '.tw', 'r'))
        assert not errs, errs
        return p

    title = 'the image of %s.tw (A=%d, P=%d), generated by tower/l1text.py'
    for n in ('add', 'branch', 'calls', 'echo', 'array', 'arith8', 'long_cat', 'and_hex'):          # test_seed.py, test_l2c.py: the default title
        add('seed', 'program-plain-' + n, l1text.program_text(compiled(n)))
    for n in ('seed', 'l2c', 'l2l'):
        st = compiled(n).stats
        add('seed', 'program-titled-' + n, l1text.program_text(compiled(n), title % (n, st['A'], st['P'])))
    add('seed', 'l2c-of-hello', chain.step('l2c', 'l2c', g.read('hello.l2') + b'\0').removesuffix(b'\0'))               # (their outputs end with the zero byte: the seed adds its own)
    add('seed', 'l2l-of-hello_names', chain.step('l2l', 'l2l', g.read('hello_names.l2') + b'\0' + g.read('hello_names.l2') + b'\0').removesuffix(b'\0'))
    for n in ('echo', 'add', 'branch', 'calls', 'array'):
        add('l2c', 'program-plain-' + n, g.to_l2(l1text.program_text(compiled(n))))
    # l3c: the packed calls (test_l3p.py), the pack mode on 1020 and 1021 names (long_l3c.py), the programs of the chain
    add('l3c', 'packed-calls', 'pack\n' + hoist(g.read('calls.tw', 'r')))
    for n in (1020, 1021):
        add('l3c', 'names-%d-pack' % n, 'pack\n' + ''.join(':a%d data 1 0\n' % i for i in range(n)) + ':main block\nhalt\n')
    add('l3c', 'provepass', g.read('prove/provepass.tw'))
    for n in sorted(f[:-3] for f in os.listdir(os.path.join(g.PROGRAMS, 'forth37')) if f.endswith('.tw')):
        src = g.read('forth37/' + n + '.tw')
        add('l3c', 'forth37-' + n, src)
        if n in PACKED_FORTH:
            add('l3c', 'forth37-packed-' + n, b'pack\n' + src)
    for n, tw_text in forth_texts():
        add('l3c', 'forth-' + n, tw_text)
    # long_l3c.py: 300 texts spoiled at random
    rng = random.Random(2305)
    junk = ['&zz', '&a[', '&a[1:', '&a[3:2]', '"x', '"x"y', '1x', '0', '99999999', '&', '&a]', 'block', 'data', 'halt', 'ret', ':', '::a', ':1a', '#', '&main', '&a[0]', '"\\q"',
            '"\\n"', '&add4', '&sub4', '&hex4', 'zero', '&zero', 'data 8 0', 'table 1 1 5 6 7', ':zz table 1 1 1', 'call', 'if', 'lut', 'store', 'add', 'shl', 'key', 'emit']
    bases = [hoist(g.read(n + '.tw', 'r')) for n in ('echo', 'branch', 'and_hex', 'loop_digits', 'array', 'arith8')]
    for k in range(300):
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
        add('l3c', 'mutation-3-%03d' % k, ''.join(toks))
    # l3p: the output of l3c on the packed calls (test_l3p.py)
    add('l3p', 'program-calls', step('l3c', 'l3c', tp.packed_of('calls').encode('latin-1') + b'\0'))
    # l4c: the lists and the seeds of test_l4p.py and long_l3c.py
    def spoiled(seed, bases, count, a1, a2):
        r = random.Random(seed)
        for k in range(count):
            b = bytearray(r.choice(bases))
            for _ in range(r.choice((1, 2, 3))):
                i = r.randrange(len(b))
                m = r.randrange(3)
                if m == 0:
                    b[i] = r.choice(a1)
                elif m == 1:
                    del b[i]
                else:
                    b.insert(i, r.choice(a2))
            yield k, bytes(b).replace(b'\0', b' ')
    for name, lst in (('edges', t4.EDGES), ('far-edges', t4.FAR_EDGES), ('chan-edges', t4.CHAN_EDGES), ('comp-edges', t4.COMP_EDGES)):
        for k, b in enumerate(lst):
            add('l4c', '%s-%02d' % (name, k), b)
    for pack in ('', 'pack\n'):
        for n, src in sorted(t4.PROGRAMS.items()):
            add('l4c', 'program-%s%s' % ('packed-' if pack else '', n), pack + src)
        add('l4c', 'channel-forms-%s' % ('packed' if pack else 'plain'), pack + t4.CHAN_FORMS)
        add('l4c', 'channel-words-%s' % ('packed' if pack else 'plain'), pack + t4.CHAN_WORDS)
        add('l4c', 'readme-%s' % ('packed' if pack else 'plain'), pack + t4.readme_example())
    add('l4c', 'echo-no-host', t3.hoisted('echo'))
    add('l4c', 'program-far-copy', g.read('far/far_copy.tw'))                       # test_far.py: the asker built by the chain, and the asker of the window above 8
    add('l4c', 'far-copy-at', tfar.FarCopyAt.SRC)
    for reason, copies in (('far-link', ['&x %s' % t4.farad(0, 3), '%s &x' % t4.farad(5, 7), '&x %s' % t4.farad(0, 1 << 24)]),
                           ('far-pos', ['&x %s' % t4.farad(12), '%s &x' % t4.farad(1 << 32), '&x %s' % t4.farad(1 << 64), '&x %s' % t4.farad(8 * 3 + 4)]),
                           ('far-width', ['&b %s' % t4.FAR, '&x[3] %s' % t4.FAR, '&t %s' % t4.FAR, '&q %s' % t4.FAR, '%s &x[0:12]' % t4.FAR, '%s %s' % (t4.FAR, t4.FAR),
                                          '%s %s' % (t4.FAR, t4.HOSTA)]),
                           ('far-limit', ['&y[9900:9908] %s' % t4.FAR, '%s &y[9950:9958]' % t4.FAR])):
        for k, pair in enumerate(copies):
            add('l4c', 'refusal-%s-%d' % (reason, k), ':x data 64 0\n:b data 4 0\n:y data 9000 0\n:t table 1 8 1 2\n:main block\n' + 'copy %s\nhalt\n' % pair)
    for reason, copies in t4.COMP_BAD.items():
        for k, pair in enumerate(copies):
            add('l4c', 'comp-refusal-%s-%02d' % (reason.replace(' ', '-'), k), t4.COMP_PRE + 'copy %s\nhalt\n' % pair)
    for k, pair in enumerate(t4.COMP_GOOD):
        add('l4c', 'comp-good-%02d' % k, t4.COMP_PRE + 'copy %s\nhalt\n' % pair)
    add('l4c', 'comp-refusal-among', t4.COMP_PRE + 'copy &x &a@&i\ncopy &q@&i &x\ncopy &y &a@&i\ncopy &a@&i &x\n')
    add('l4c', 'far-257-chain', ':x data 64 0\n:main block\n' + 'copy &x %s\n' % t4.FAR * 257)
    add('l4c', 'far-among-others', ':x data 64 0\n:b data 4 0\n:y data 9000 0\n:t table 1 8 1 2\n:main block\ncopy &t %s\ncopy %s &x\n' % (t4.HOSTA, t4.farad(12)))
    decl = ''.join((':d%d data 8 0\n' if k % 2 else ':d%d array 3 8\n') % k for k in range(70))
    for k in (0, 1, 58, 60, 62, 64, 69):
        add('l4c', 'names-cells-%d' % k, ':i data 3 0\n:x data 8 0\n' + decl + ':main block\ncopy &x &d%d@&i\nhalt\n' % k)
    for k, b in spoiled(2646, t4.FAR_LINKS[:12], 24, b'0123456789abcdefx&[]:# "\n\\', b'012x&[]: "\n\\#'):
        add('l4c', 'far-link-mutation-%02d' % k, b)
    for k, b in spoiled(2504, t4.COMP_EDGES[:4] + t4.COMP_EDGES[6:8], 40, b'0123456789abcdefx&[]:@# "\n\\tr', b'02x&[]:@ "\n\\#'):
        add('l4c', 'comp-mutation-%02d' % k, b)
    for k, b in spoiled(2318, t4.EDGES[9:13], 40, b'0123456789abcdefx&[]:# "\n\\', b'0x&[]: "\n\\#'):
        add('l4c', 'edge-mutation-%02d' % k, b)
    return out
