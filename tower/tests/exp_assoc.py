"""The experiment of 25.2: the associative space on a small space, the hash against the tree of tables. Not a test (not in check-fast):
the size of the image and of the tables, the ticks of the emulator of one command (W, K, V, R) on the workloads, as numbers for the report.
The ticks of one command are the difference of the ticks of two runs which differ by this command (the commands before it the same).
Run: python3 -B tower/tests/exp_assoc.py [quick]"""
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import common
import test_assoc as ta
from test_assoc import K, R, V, W, Model, Space

SIZES = [(8, 8, 4), (8, 8, 5), (16, 8, 4), (16, 8, 5)]
NOP = (8,)


def index_names(method):
    return {'hash': ('hd', 'cn', 'hx'), 'tree': ('nt', 'cnt', 'nfl', 'ptx', 'isn', 'incn', 'rt', 'dep1', 'lvdec', 'lz4', 'up3', 'down3', 'lz3')}[method]


def memory(sp):
    p = sp.prog
    tabs = {n: (1 << sum(t.ins)) * t.out for n, t in p.tables.items()}
    index = sum(v for n, v in tabs.items() if n in index_names(sp.method))
    views = {id(t.data) for t in p.tables.values()}
    data = sum(d.bits for d in p.datas if id(d) not in views)
    return sum(tabs.values()), index, data


def workload_random(sp, rng, n=400):
    ks = [rng.randrange(sp.onesk) for _ in range(2 * sp.n)]
    vs = [rng.randrange(sp.onesv) for _ in range(sp.n)]
    ops = []
    for _ in range(n):
        x = rng.random()
        ops.append((W, rng.choice(ks), rng.choice(vs)) if x < 0.45 else (R, rng.choice(ks)) if x < 0.65 else
                   (K, rng.choice(ks)) if x < 0.85 else (V, rng.choice(vs)))
    return ops


def workload_bucket(sp):
    """All keys with the same low bits and the values too (the hash chain is as long as it can be), then reads of every key and value."""
    h = sp.c
    ks = [((j << h) + 3) & sp.onesk for j in range(1, sp.n)]
    ks = list(dict.fromkeys(ks))
    vs = [((j << h) + 5) & sp.onesv for j in range(1, sp.n)]
    ops = [(W, k, vs[i % len(vs)]) for i, k in enumerate(ks)]
    ops += [(K, k) for k in ks] + [(V, v) for v in dict.fromkeys(vs)] + [(W, k, vs[0]) for k in ks[:3]] + [(R, k) for k in ks]
    return ops


def workload_ring(sp):
    """All keys with one value (the ring of synonyms is as long as it can be), reads, then the rollbacks."""
    ks = list(range(1, sp.n + 1))
    ops = [(W, k, 7) for k in ks] + [(K, k) for k in ks] + [(V, 7)] + [(W, k, 9) for k in ks[:4]] + [(R, k) for k in ks]
    return ops


def per_command(sp, ops):
    """[(op, ticks)] for the ops which changed something (a write with no free cell is skipped), from the prefixes."""
    m, out = Model(sp), []
    base = sp.session([], checked=True)[1].ticks
    ticks = [base]
    for i in range(len(ops)):
        ticks.append(sp.session(ops[:i + 1], checked=True)[1].ticks)
    for i, op in enumerate(ops):
        stored = op[0] != W or not (op[1] == sp.onesk or op[2] == sp.onesv or m.used >= sp.n)
        hit = {K: op[1] in m.st if op[0] == K else None, V: bool(m.keys_of(op[1])) if op[0] == V else None}.get(op[0])
        ta.apply(m, op)
        if stored:
            out.append((op[0], ticks[i + 1] - ticks[i], hit))
    return out


def stats(rows, kind, hit=None):
    t = [x[1] for x in rows if x[0] == kind and (hit is None or x[2] == hit)]
    return (sum(t) / len(t), max(t), len(t)) if t else (0, 0, 0)


def main():
    quick = sys.argv[1:] == ['quick']
    common.ensure_built()
    results = {}
    print('| method | key bits | cells | A | P | image B | tables bits (index) | data bits | NOP ticks |\n|---|---|---|---|---|---|---|---|---|')
    for method in ('hash', 'tree'):
        for size in SIZES:
            if method == 'tree' and size == (16, 8, 5):
                print('| tree | 16 | 32 | does not fit: the pool needs 2^9 nodes of 4 entries, a table has at most 2^10 entries |||||||')
                continue
            sp = Space.get(method, size)
            tb, ix, data = memory(sp)
            nop = sp.session([NOP], checked=True)[1].ticks - sp.session([], checked=True)[1].ticks
            print('| %s | %d | %d | %d | %d | %d | %d (%d) | %d | %d |' % (method, size[0], 1 << size[2], sp.prog.A, sp.stats['P'], len(sp.stats['image']), tb, ix, data, nop), flush=True)
            rng = random.Random(7)
            wl = {'random': workload_random(sp, rng, 120 if quick else 400), 'bucket': workload_bucket(sp), 'ring': workload_ring(sp)}
            results[method, size] = {name: per_command(sp, ops) for name, ops in wl.items()}
    print('\n| method | key bits | cells | workload | W avg / max | K avg / max | V avg / max | R avg / max |\n|---|---|---|---|---|---|---|---|')
    for (method, size), r in results.items():
        for name, rows in r.items():
            cells = ' | '.join('%.0f / %d' % stats(rows, kind)[:2] for kind in (W, K, V, R))
            print('| %s | %d | %d | %s | %s |' % (method, size[0], 1 << size[2], name, cells))
    print('\nworst case over the workloads (and the average of the random one):')
    print('| method | key bits | cells | W avg / worst | K avg / worst | V avg / worst | R avg / worst |\n|---|---|---|---|---|---|---|')
    for (method, size), r in results.items():
        cells = []
        for kind in (W, K, V, R):
            worst = max(stats(rows, kind)[1] for rows in r.values())
            cells.append('%.0f / %d' % (stats(r['random'], kind)[0], worst))
        print('| %s | %d | %d | %s |' % (method, size[0], 1 << size[2], ' | '.join(cells)))


if __name__ == '__main__':
    main()
