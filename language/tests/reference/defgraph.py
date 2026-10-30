#!/usr/bin/env python3
"""Definition graph of kernel K: word -> words in its definition (13.1).

Usage: python3 -B language/tests/reference/defgraph.py [--out-dir docs/research]
Standard library only.

Model (as in forthc.fth): `:` makes the name visible at once (the body may
name itself); variable/create/constant likewise. Source is read in the
compilation order of forth/tests/test_kernel.py (KERNEL), then the
other copycode/forth files as group "aux" (own namespace, falling back to the
final K namespace). A reference goes to the version visible at the point of
use. Words not defined in the sources are externals (pForth/forthc primitives).
Tokens: case folded, `\\` to end of line, `( ... )`, `s" ..."`, `[char] c`.
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FC = 'forth/scripts/forthc/'
CF = 'copycode/forth/'
K_ORDER = [FC + 'prelude.fth', CF + 'backend.fth', CF + 'compute.fth',
           FC + 'forthc.fth', FC + 'main.fth', FC + 'kernel.fth']
AUX_ORDER = [CF + n for n in ('integers.fth', 'bitfields.fth', 'format.fth', 'arena.fth',
                              'instructions.fth', 'operations.fth', 'evaluate.fth')]
DEFINERS = {':', 'variable', 'constant', 'create', 'value'}
STACK_WORDS = {'dup', 'drop', 'swap', 'over', 'rot', '-rot', 'nip', 'tuck', '2dup', '2drop',
               '2swap', '2over', '>r', 'r>', 'r@', 'pick', 'roll', '?dup', '+', '-', '*', '1+', '1-',
               'cells', 'cell+', 'here', 'allot', ','}
VECTOR_NAMES = set()     # variables executed as `V @ execute` / `V @ ?dup if execute`


def find_exec_vector(toks, i):
    """Variable V for the `execute` at toks[i] in `V @ execute` or `V @ ?dup if execute`."""
    for back in range(1, 5):
        if i - back - 1 >= 0 and toks[i - back][0] == '@':
            return toks[i - back - 1][0]
    return None


def find_receiver(toks, j, span=12):
    """After ['] X: first word that is not a literal, string or stack word (takes the xt)."""
    for k in range(j, min(j + span, len(toks))):
        t = toks[k][0]
        if t in (';', ':') or t in ("'", "[']"):
            return None
        if t in ('"str"', '[char]') or is_number(t) or t in STACK_WORDS:
            continue
        return t
    return None


def tokenize(path):
    """Yield (token, line, raw) with comments and strings removed."""
    with open(os.path.join(ROOT, path), encoding='utf-8') as f:
        lines = f.read().split('\n')
    out = []
    in_paren = False
    for ln, text in enumerate(lines, 1):
        pos, n = 0, len(text)
        while pos < n:
            while pos < n and text[pos] <= ' ':
                pos += 1
            if pos >= n:
                break
            st = pos
            while pos < n and text[pos] > ' ':
                pos += 1
            raw = text[st:pos]
            tok = raw.lower()
            if in_paren:
                if tok == ')':
                    in_paren = False
                continue
            if tok == '\\':
                break
            if tok == '(':
                in_paren = True
                continue
            if tok == 's"' or tok == '."':
                e = text.find('"', pos + 1)
                pos = n if e < 0 else e + 1
                out.append(('"str"', ln, raw))
                continue
            if tok == '[char]':
                while pos < n and text[pos] <= ' ':
                    pos += 1
                st = pos
                while pos < n and text[pos] > ' ':
                    pos += 1
                out.append(('[char]', ln, text[st:pos]))
                continue
            out.append((tok, ln, raw))
    return out


def is_number(t):
    return re.fullmatch(r'-?\d+', t) is not None


class Graph:
    def __init__(self):
        self.nodes = []          # dicts
        self.k = {}              # name -> node id (latest), K namespace
        self.aux = {}
        self.versions = collections.Counter()
        self.edges = {}          # (from,to,kind,via) -> dict
        self.externals = collections.Counter()
        self.unresolved = collections.defaultdict(list)  # name -> [(node,file,line)]
        self.executes = []       # dicts for EXECUTE sites
        self.stack_writes = []   # `V !` into a vector
        self.defined_lines = {}

    def new_node(self, name, kind, file, line, group):
        self.versions[(group == 'aux', name)] += 1
        v = self.versions[(group == 'aux', name)]
        nid = name if v == 1 else '%s~%d' % (name, v)
        if group == 'aux':
            nid = 'aux:' + nid
        self.nodes.append({'id': nid, 'name': name, 'version': v, 'kind': kind,
                           'file': file, 'line': line, 'group': group})
        (self.aux if group == 'aux' else self.k)[name] = nid
        return nid

    def add_edge(self, a, b, kind, line, via=None, sub=None, receiver=None):
        key = (a, b, kind, via, sub, receiver)
        e = self.edges.get(key)
        if e:
            e['count'] += 1
        else:
            self.edges[key] = {'from': a, 'to': b, 'kind': kind, 'count': 1, 'line': line}
            if via:
                self.edges[key]['via'] = via
            if sub:
                self.edges[key]['sub'] = sub
            if receiver:
                self.edges[key]['receiver'] = receiver

    def lookup(self, name, group):
        if group == 'aux' and name in self.aux:
            return self.aux[name]
        return self.k.get(name)


def process(g, path, group):
    toks = tokenize(path)
    initid = None
    cur = None          # current word being compiled (node id) or None
    i, n = 0, len(toks)
    ns_k = group != 'aux'

    def init_node(line):
        nonlocal initid
        if initid is None:
            initid = '%s::init' % path
            g.nodes.append({'id': initid, 'name': initid, 'version': 1, 'kind': 'init',
                            'file': path, 'line': line, 'group': group})
        return initid

    def ref(owner, name, line, kind='direct', via=None, sub=None, receiver=None):
        t = g.lookup(name, group)
        if t is not None:
            g.add_edge(owner, t, kind, line, via, sub, receiver)
        elif not is_number(name):
            g.externals[name] += 1
            g.unresolved[name].append((owner, path, line))
        return t

    top_buf = []  # (index in toks) of pending top-level tokens, for constant init
    while i < n:
        tok, ln, raw = toks[i]
        if cur is None:
            if tok in (':', 'variable', 'create', 'constant', 'value') and i + 1 < n:
                if tok == ':':
                    cur = g.new_node(toks[i + 1][0], 'colon', path, toks[i + 1][1], group)
                    i += 2
                    continue
                if tok in ('constant', 'value'):
                    nid_name = toks[i + 1][0]
                    # initial value: tokens of the same line before the definer
                    owner_tokens = []
                    j = len(top_buf)
                    while j > 0 and top_buf[j - 1][1] == ln:
                        j -= 1
                    owner_tokens = top_buf[j:]
                    del top_buf[j:]
                    nid = g.new_node(nid_name, tok, path, toks[i + 1][1], group)
                    for t2, l2, _ in owner_tokens:
                        if t2 not in ('"str"', '[char]') and not is_number(t2):
                            ref(nid, t2, l2)
                    i += 2
                    continue
                if tok == 'variable':
                    g.new_node(toks[i + 1][0], 'variable', path, toks[i + 1][1], group)
                    i += 2
                    continue
                if tok == 'create':
                    nid = g.new_node(toks[i + 1][0], 'create', path, toks[i + 1][1], group)
                    j = i + 2
                    # body: up to and including the first allot, else end of the line
                    while j < n:
                        t2, l2, _ = toks[j]
                        if t2 in DEFINERS and t2 != 'value':
                            break
                        if l2 != toks[i + 1][1] and t2 != 'allot':
                            # continue only if a multi-line expression ends in allot on a later line
                            break
                        if t2 == 'allot':
                            j += 1
                            break
                        if t2 not in ('"str"', '[char]') and not is_number(t2):
                            ref(nid, t2, l2)
                        j += 1
                    i = j
                    continue
            top_buf.append(toks[i])
            if tok in ('"str"', '[char]') or is_number(tok):
                pass
            else:
                ref(init_node(ln), tok, ln)
                if tok in ("'", "[']") and i + 1 < n:
                    pass
            # top-level tick handling
            if tok in ("'", "[']") and i + 1 < n:
                target = toks[i + 1][0]
                via = find_via(toks, i + 2)
                if via in VECTOR_NAMES:
                    ref(init_node(ln), target, ln, 'indirect', via, 'vector-write')
                else:
                    rcv = find_receiver(toks, i + 2)
                    ref(init_node(ln), target, ln, 'indirect', None, 'xt-arg' if rcv else 'tick', rcv)
                top_buf.append(toks[i + 1])
                i += 2
                continue
            i += 1
            continue
        # inside a colon definition
        if tok == ';':
            cur = None
            i += 1
            continue
        if tok in ('"str"', '[char]') or is_number(tok):
            i += 1
            continue
        if tok == 'recurse':
            g.add_edge(cur, cur, 'direct', ln, sub='recurse')
            i += 1
            continue
        if tok in ("'", "[']") and i + 1 < n:
            target = toks[i + 1][0]
            via = find_via(toks, i + 2)
            if via in VECTOR_NAMES:
                ref(cur, target, toks[i + 1][1], 'indirect', via, 'vector-write')
            else:
                rcv = find_receiver(toks, i + 2)
                ref(cur, target, toks[i + 1][1], 'indirect', None, 'xt-arg' if rcv else 'tick', rcv)
            i += 2
            continue
        if tok == '!' and i > 0 and toks[i - 1][0] in VECTOR_NAMES:
            ticked = False     # `['] X ... V !` is already a vector-write edge
            for k in range(i - 1, max(i - 10, 0), -1):
                if toks[k][0] in (';', ':'):
                    break
                if toks[k][0] in ("'", "[']") and find_via(toks, k + 2) == toks[i - 1][0]:
                    ticked = True
                    break
            if not ticked:
                g.stack_writes.append({'in': cur, 'vector': toks[i - 1][0], 'line': ln})
        if tok == 'execute':
            vec = find_exec_vector(toks, i)
            g.executes.append({'in': cur, 'file': path, 'line': ln, 'vector': vec})
            if vec and g.lookup(vec, group):
                g.add_edge(cur, g.lookup(vec, group), 'indirect', ln, via=vec, sub='execute-vector')
            ref(cur, tok, ln)
            i += 1
            continue
        ref(cur, tok, ln)
        i += 1
    if cur is not None:
        raise SystemExit('%s: unterminated definition %s' % (path, cur))


def find_via(toks, j, span=8):
    """After ['] X: the variable stored into, ['] X ... V !, within `span` tokens."""
    for k in range(j, min(j + span, len(toks))):
        t = toks[k][0]
        if t == '!':
            if k - 1 < j:
                return None
            v = toks[k - 1][0]
            if v == '+' and k - 2 >= j:   # indexed vector: base i cells + !
                v = toks[k - 2][0]
            return v
        if t in (';', ':') or t in ("'", "[']"):
            return None
    return None


def tarjan(nodes, adj):
    index, low, onst, st, res = {}, {}, set(), [], []
    counter = [0]
    sys.setrecursionlimit(100000)

    def sc(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        st.append(v)
        onst.add(v)
        for w in adj.get(v, ()):
            if w not in index:
                sc(w)
                low[v] = min(low[v], low[w])
            elif w in onst:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = st.pop()
                onst.discard(w)
                comp.append(w)
                if w == v:
                    break
            res.append(comp)
    for v in nodes:
        if v not in index:
            sc(v)
    return res


def reach_counts(nodes, radj, skip):
    """For each node: number of non-skipped nodes reaching it (reverse BFS)."""
    out = {}
    for v in nodes:
        seen = {v}
        stack = [v]
        while stack:
            x = stack.pop()
            for w in radj.get(x, ()):
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        seen.discard(v)
        out[v] = len([w for w in seen if w not in skip])
    return out


def main():
    out_dir = os.path.join(ROOT, 'docs/research')
    if '--out-dir' in sys.argv:
        out_dir = os.path.abspath(sys.argv[sys.argv.index('--out-dir') + 1])
    g = Graph()
    for p in K_ORDER + AUX_ORDER:
        t = tokenize(p)
        for i, x in enumerate(t):
            if x[0] == 'execute':
                v = find_exec_vector(t, i)
                if v:
                    VECTOR_NAMES.add(v)
    for p in K_ORDER:
        process(g, p, 'K')
    for p in AUX_ORDER:
        process(g, p, 'aux')
    edges = list(g.edges.values())
    ids = [x['id'] for x in g.nodes]
    byid = {x['id']: x for x in g.nodes}
    init_ids = {x['id'] for x in g.nodes if x['kind'] == 'init'}

    def build(kinds):
        adj, radj = collections.defaultdict(set), collections.defaultdict(set)
        for e in edges:
            if e['kind'] in kinds:
                adj[e['from']].add(e['to'])
                radj[e['to']].add(e['from'])
        return adj, radj

    cycles = []
    for scope, kinds in (('direct', {'direct'}), ('all', {'direct', 'indirect'})):
        adj, _ = build(kinds)
        for comp in tarjan(ids, adj):
            if len(comp) > 1:
                cycles.append({'scope': scope, 'type': 'scc', 'nodes': sorted(comp)})
            elif comp[0] in adj.get(comp[0], ()):
                subs = sorted({e.get('sub', '') or 'name' for e in edges
                               if e['from'] == e['to'] == comp[0] and e['kind'] in kinds})
                cycles.append({'scope': scope, 'type': 'loop', 'nodes': comp, 'via': subs})
    adj_a, radj_a = build({'direct', 'indirect'})
    adj_d, radj_d = build({'direct'})
    ta = reach_counts(ids, radj_a, init_ids)
    td = reach_counts(ids, radj_d, init_ids)
    dependents = {}
    for v in ids:
        if v in init_ids:
            continue
        dependents[v] = {'direct': len({w for w in radj_a.get(v, ()) if w != v and w not in init_ids}),
                         'transitive_direct_edges': td[v], 'transitive_all_edges': ta[v]}
    nodes = []
    for x in g.nodes:
        nodes.append(x)
    # vectors
    vec = collections.defaultdict(lambda: {'writes': [], 'executors': []})
    for e in edges:
        if e.get('sub') == 'vector-write':
            vec[e['via']]['writes'].append({'in': e['from'], 'target': e['to'], 'line': e['line']})
    for x in g.stack_writes:
        vec[x['vector']]['writes'].append({'in': x['in'], 'target': None, 'line': x['line']})
    for x in g.executes:
        if x['vector']:
            vec[x['vector']]['executors'].append({'in': x['in'], 'line': x['line'], 'file': x['file']})
    forward = {}
    defined = {x['name'] for x in g.nodes if x['kind'] != 'init'}
    for name, uses in g.unresolved.items():
        if name in defined:
            forward[name] = [{'in': a, 'file': f, 'line': l} for a, f, l in uses[:5]]
    data = {
        'order': {'K': K_ORDER, 'aux': AUX_ORDER},
        'nodes': nodes, 'edges': edges, 'cycles': cycles, 'dependents': dependents,
        'vectors': {k: v for k, v in sorted(vec.items())},
        'execute_sites': g.executes,
        'externals': dict(sorted(g.externals.items(), key=lambda kv: (-kv[1], kv[0]))),
        'forward_references': forward,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'definition-graph.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    write_md(os.path.join(out_dir, 'definition-graph.md'), data, byid, init_ids)


def loc(x):
    return '%s:%d' % (x['file'].replace('space/', ''), x['line'])


def write_md(path, d, byid, init_ids):
    nodes, edges = d['nodes'], d['edges']
    words = [x for x in nodes if x['kind'] != 'init']
    kw = [x for x in words if x['group'] == 'K']
    L = []
    w = L.append
    w('# Граф определений ядра K\n')
    w('Сгенерировано `language/tests/reference/defgraph.py`; данные в `docs/research/definition-graph.json`.\n')
    w('Порядок компиляции K (из `forth/tests/test_kernel.py`): ' +
      ', '.join('`%s`' % p.split('/')[-1] for p in d['order']['K']) +
      '. Прочие файлы `copycode/forth/` (группа aux) разобраны отдельно, в конце, '
      'со своим пространством имён; они не входят в K.\n')
    w('Правило видимости как в `forthc.fth`: имя видимо с момента `:`; ссылка идёт к последней '
      'определённой на этот момент версии. Слова без определения в исходниках (примитивы) — внешние, рёбер не создают.\n')
    w('## Циклы\n')
    cyc = d['cycles']
    if not cyc:
        w('Циклов нет.\n')
    else:
        w('| Охват рёбер | Тип | Узлы | Через |')
        w('|---|---|---|---|')
        for c in cyc:
            w('| %s | %s | %s | %s |' % ('прямые' if c['scope'] == 'direct' else 'прямые+косвенные',
                                        'сильно связная компонента' if c['type'] == 'scc' else 'петля',
                                        ', '.join('`%s`' % x for x in c['nodes']),
                                        ', '.join(c.get('via', [])) or ''))
        w('')
    nd = [c for c in cyc if c['scope'] == 'direct']
    w('Сильно связных компонент больше одного узла: %d (прямые), %d (все рёбра). Петель: %d (прямые), %d (все).\n' % (
        sum(1 for c in cyc if c['scope'] == 'direct' and c['type'] == 'scc'),
        sum(1 for c in cyc if c['scope'] == 'all' and c['type'] == 'scc'),
        sum(1 for c in cyc if c['scope'] == 'direct' and c['type'] == 'loop'),
        sum(1 for c in cyc if c['scope'] == 'all' and c['type'] == 'loop')))
    w('Ссылки вперёд (имя использовано до определения, но определено позже): %d.\n' % len(d['forward_references']))
    if d['forward_references']:
        w('| Имя | Где |')
        w('|---|---|')
        for k, v in d['forward_references'].items():
            w('| `%s` | %s |' % (k, ', '.join('`%s`:%d' % (x['file'].split('/')[-1], x['line']) for x in v)))
        w('')
    w('## Косвенные ссылки\n')
    ind = [e for e in edges if e['kind'] == 'indirect']
    by_sub = collections.Counter(e.get('sub', '') for e in ind)
    w('Косвенных рёбер: %d (%s).\n' % (len(ind), ', '.join('%s: %d' % kv for kv in sorted(by_sub.items()))))
    w('### Векторы исполнения (переменные, исполняемые как `V @ execute` или `V @ ?dup if execute`)\n')
    w('Запись `[\'] слово ... V !` учитывается только для таких V; запись xt из стека (`... V !`) показана как «xt из стека».\n')
    w('| Вектор | Записывают (слово → цель) | Исполняют |')
    w('|---|---|---|')
    for k, v in d['vectors'].items():
        wr = collections.OrderedDict()
        for x in v['writes']:
            wr.setdefault((x['in'], x['target']), 0)
            wr[(x['in'], x['target'])] += 1
        ws = '; '.join('`%s` → %s%s' % (a, '`%s`' % b if b else 'xt из стека', ' ×%d' % c if c > 1 else '')
                       for (a, b), c in wr.items()) or '—'
        ex = '; '.join(sorted({'`%s`' % x['in'] for x in v['executors']})) or '—'
        w('| `%s` | %s | %s |' % (k, ws, ex))
    w('')
    xa = [e for e in ind if e.get('sub') == 'xt-arg']
    w('### xt-аргументы (`[\'] слово` передаётся принимающему слову, а не записывается в вектор)\n')
    w('| Слово | Передаваемый xt | Получатель (receiver) | Файл:строка |')
    w('|---|---|---|---|')
    for e in xa:
        w('| `%s` | `%s` | `%s` | %s:%d |' % (e['from'], e['to'], e['receiver'], byid[e['from']]['file'].replace('space/', ''), e['line']))
    w('')
    w('### Прочие ссылки через `\'`/`[\']` (без записи в вектор)\n')
    w('| Слово | Цель | Файл:строка |')
    w('|---|---|---|')
    for e in ind:
        if e.get('sub') == 'tick':
            w('| `%s` | `%s` | %s:%d |' % (e['from'], e['to'], byid[e['from']]['file'].replace('space/', ''), e['line']))
    w('')
    ex_nov = [x for x in d['execute_sites'] if not x['vector']]
    w('### Места EXECUTE\n')
    w('Всего %d; с видимым вектором (`V @ execute`): %d; с адресом из стека (цель не видна статически): %d.\n' % (
        len(d['execute_sites']), len(d['execute_sites']) - len(ex_nov), len(ex_nov)))
    if ex_nov:
        w('| Слово | Файл:строка |')
        w('|---|---|')
        for x in ex_nov:
            w('| `%s` | %s:%d |' % (x['in'], x['file'].replace('space/', ''), x['line']))
        w('')
    w('## Число зависимых\n')
    w('Для слова — число слов (узлов-определений, без неявных узлов верхнего уровня), использующих его прямо или транзитивно; '
      'считается по всем рёбрам (прямые и косвенные). Столбец «только прямые рёбра» — то же без косвенных рёбер. '
      'Топ-30 по первому числовому столбцу.\n')
    dep = d['dependents']
    top = sorted(dep.items(), key=lambda kv: (-kv[1]['transitive_all_edges'], kv[0]))[:30]
    w('| # | Слово | Вид | Файл:строка | Прямых | Транзитивно (все рёбра) | Транзитивно (только прямые рёбра) |')
    w('|---|---|---|---|---|---|---|')
    for r, (k, v) in enumerate(top, 1):
        x = byid[k]
        w('| %d | `%s` | %s | %s | %d | %d | %d |' % (r, k, x['kind'], loc(x), v['direct'],
                                                    v['transitive_all_edges'], v['transitive_direct_edges']))
    w('')
    w('## Итог\n')
    kinds = collections.Counter(x['kind'] for x in words)
    ver = [x for x in words if x['version'] > 1]
    redefs = collections.Counter(x['name'] for x in words if x['group'] == 'K' and x['version'] > 1)
    maxn = max(dep.items(), key=lambda kv: kv[1]['transitive_all_edges'])
    zero = sum(1 for v in dep.values() if v['transitive_all_edges'] == 0)
    kdirect = sum(1 for e in edges if e['kind'] == 'direct')
    w('| Показатель | Значение |')
    w('|---|---|')
    w('| Узлов-определений всего (K + aux) | %d |' % len(words))
    w('| В K | %d (по файлам: %s) |' % (len(kw), ', '.join(
        '%s %d' % (p.split('/')[-1], sum(1 for x in kw if x['file'] == p)) for p in d['order']['K'])))
    w('| Виды | %s |' % ', '.join('%s %d' % kv for kv in sorted(kinds.items())))
    w('| Повторно определённых имён (версия > 1) | %d узлов |' % len(ver))
    if ver:
        w('| Они | %s |' % ', '.join('`%s`' % x['id'] for x in ver[:20]))
    w('| Рёбер (прямых / косвенных) | %d / %d |' % (kdirect, len(ind)))
    w('| Циклы (прямые рёбра): компонент > 1 / петель | %d / %d |' % (
        sum(1 for c in cyc if c['scope'] == 'direct' and c['type'] == 'scc'),
        sum(1 for c in cyc if c['scope'] == 'direct' and c['type'] == 'loop')))
    w('| Циклы (все рёбра): компонент > 1 / петель | %d / %d |' % (
        sum(1 for c in cyc if c['scope'] == 'all' and c['type'] == 'scc'),
        sum(1 for c in cyc if c['scope'] == 'all' and c['type'] == 'loop')))
    w('| Мест EXECUTE | %d |' % len(d['execute_sites']))
    w('| Внешних имён (примитивы, нет определения в исходниках) | %d различных, %d использований |' % (
        len(d['externals']), sum(d['externals'].values())))
    w('| Больше всего зависимых | `%s`: %d транзитивно |' % (maxn[0], maxn[1]['transitive_all_edges']))
    w('| Слов без зависимых | %d из %d |' % (zero, len(dep)))
    w('')
    w('Векторов исполнения: %d\n' % sum(1 for v in d['vectors'].values() if v['executors']))
    w('xt-аргументов: %d\n' % sum(1 for e in edges if e.get('sub') == 'xt-arg'))
    w('Внешние имена, чаще всего используемые: ' + ', '.join(
        '`%s` %d' % kv for kv in list(d['externals'].items())[:25]) + '.\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
