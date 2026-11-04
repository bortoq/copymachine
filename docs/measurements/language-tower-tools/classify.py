#!/usr/bin/env python3
"""21.1: split the words of the core of the language (language/doc/core.md) into the nested languages.

Usage: python3 -B classify.py [--cost FILE] [--tsv words.tsv]
  --cost FILE  output of `language/tools/word_cost.py` (size of a word in cells of the image);
               make it: (cd language/tools; LANGUAGE_OUT=/tmp/x python3 word_cost.py > FILE)
Reads language/tools/check_closure.py (core_nodes: the same graph as core.md). Writes nothing in the repo
but --tsv. Standard library only. Rules: NAMES (by name, first), then RANGES (file, lines), then the
generator-name inherits the group of its generator word (gen-*), the digits are LIT.
A word whose group is set by hand is marked `hand` in the column `how`.
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(ROOT, 'language/tools'))
sys.dont_write_bytecode = True
import check_closure as cc  # noqa: E402

# group -> (title, tower rank). Rank: the position in the tower; a use of a word of a higher rank by a lower one
# is a violation of nesting. Groups outside the tower get the rank of the language that they compile for/serve.
GROUPS = collections.OrderedDict([
    ('L1', ('L1 индексное: строка/слой/останов (dl dh sl sh)', 1)),
    ('L2', ('L2 сокращённая инструкция: копия (длина, куда, откуда)', 2)),
    ('L3', ('L3 лут: таблицы, значения функций через L2', 3)),
    ('L4', ('L4 длинное: пространство хоста (long, SYS, каналы, часы)', 4)),
    ('L5p', ('L5 экономное: цена (price/cost, путь, журнал слоёв)', 5)),
    ('L5r', ('L5 экономное: замена определений (replace, записи слов, концепты)', 5)),
    ('L5h', ('L5 экономное: определения на хосте, платформы, библиотека', 5)),
    ('ENC', ('Кодер L1 в образ: поток загрузки, буферы, форматы (компилятор L1 в L0)', 1)),
    ('SCH', ('Планировщик расписаний: размещение строк в слоях (lay-clash.., fc-s*)', 2)),
    ('PRF', ('Доказательство/непересечение: dj-*, proved/unproved', 1)),
    ('GRD', ('Изоляция ядра: fc-guard, проверки адресов', 3)),
    ('CAL', ('Входы и возвраты: таблицы xt/return, вызов, tick, execute', 3)),
    ('CTL', ('Управляющие структуры Форта: if/loop/exit, переход', 3)),
    ('STK', ('Стек, регистры, переменные и данные Форта (dup.., variable, spill)', 3)),
    ('MEM', ('Память Форта: @ ! c@ c! (доступ по вычисляемому адресу)', 3)),
    ('LIT', ('Литералы и константы: цифры, fc-const, ссылки, свёртка', 3)),
    ('TXT', ('Разбор текста, словарь, генераторы-имена, компилятор (fc-text, fc-find..)', 3)),
    ('DRV', ('Запуск: kernel.fth, main, размеры буферов', 3)),
    ('DIA', ('Вывод и диагностика: fc-reject, fc-.n, fc-tok', 0)),
    ('HF', ('Хост-Форт (pForth): prelude — слова стека/строк, нужны хосту', 0)),
    ('LAY', ('Раскладка пространства: константы адресов блоков/регистров/таблиц', 0)),
    ('UNK', ('Не ложится', 0)),
])

# --- by name (hand) ---
NAMES = {}
def put(group, names):
    for n in names.split():
        NAMES[n] = group

put('DIA', 'fc-tok fc-tl fc-.n fc-reject type')
put('HF', 'nip tuck -rot 2dup 2drop 2swap 2over ?dup negate invert > u> <> 0< 0> 0<> max min +! 2@ 2! fill-cell fill '
          'cmove cmove> /string compare source >in')
put('L1', 'lay-pending@ lay-size lay-a lay-slots lay-cell-bits lay-inst lay-layer-bits lay-lbytes lay-field-check lay-start lay-len '
          'lay-rows lay-row! lay-clear-rows lay-max-layers lay-record lay-pending lay-head lay-next-cell lay-seq# '
          'lay-seq-first lay-seq-entry lay-seq-last lay-foff lay-foff-init lay-machine lay-field lay-link-row '
          'lay-builder lay-new-cell lay-branch-bit lay-branch-step lay-group lay-layer-cell lay-next! lay-count '
          'lay-row-addr lay-new-record lay-lone lay-seq lay-last lay-layer lay-entry lay-jump lay-l1 lay-h1 lay-l2 '
          'lay-h2 lay-ra lay-rb lay-cur lay-row')
put('L2', 'lay-copy')                                   # hand: 3 arguments (n dst src) = the 2nd language already
put('ENC', 'lay-chunk lay-chunk-buf lay-lbuf lay-pool lay-ebuf lay-dest lay-sink lay-start-cell lay-rev lay-rev-init '
           'lay-stdin lay-stdout lay-bits lay-numeric lay-numeric4 lay-encode lay-loader lay-stream-flush '
           'lay-begin-chunk lay-put lay-scratch lay-put-numeric lay-chunk-mem lay-lbuf-mem lay-ebuf-mem lay-pool-mem '
           'lay-bufs lay-encode-layer lay-write lay-write-oldest lay-flush lay-finish')
put('L5p', 'lay-on-write')
put('L4', 'lay-pos lay-cells lay-rec lay-hdr lay-cap lay-req')
put('SCH', 'lay-clash? lay-row-clash? lay-new-row lay-row-set lay-full? lay-clashes? lay-fits?')
# forthc.fth variables/constants of the layout
put('LAYOUT_L2', 'fc-size fc-cellb fc-l fc-a fc-d fc-first fc-bbits fc-abits fc-layout fc-d+ fc-data-start')
put('GRD', 'fc-guard fc-chk-read fc-chk-seg fc-check')
put('CAL', 'fc-ebits fc-etab fc-rbits fc-rtab fc-xt fc-xtn fc-callee fc-entry-cell fc-concept')
put('STK', 'fc-sp fc-rp fc-regs fc-nregs fc-tmp fc-xr fc-z fc-idx fc-stk fc-rstk fc-scr0 fc-sw fc-su fc-bp '
           'fc-r-at fc-pop-pinned fc-sk fc-cache fc-n fc-pin fc-npin fc-inits fc-ninit fc-init-open fc-close-init '
           'fc-open-init fc-align fc-check-here fc-define-data fc-sat fc-store-string fc-here')
put('MEM', 'fc-ma fc-mb fc-mp fc-mq fc-mr fc-mem fc-mw')
put('LIT', 'fc-zero fc-consts fc-links fc-max-links fc-link-chunk fc-literal fc-ct fc-nct fc-ct+ fc-ct- fc-ct2 '
           'fc-const-shift fc-lit? fc-mul-lit? fc-shift-lit? fc-pick-roll fc-digit@ fc-fold? fc-eight fc-zeros '
           'fc-bit0 fc-bit1 fc-length fc-lit-of fc-lit fc-load')
put('L4', 'fc-key fc-read-key gen-emit gen-key fc-cp fc-copy-row fc-forbidden fc-num fc-long-host fc-ltpl fc-lpos '
          'fc-llo fc-lhi fc-lcn fc-ldir fc-lp0 fc-lp1 fc-lpl fc-ltemplate fc-lhead fc-lsend fc-lpop fc-lput fc-lget '
          'fc-long-kernel fc-long emit key')
put('L3', 'fc-off fc-oc')
put('STK', 'fc-c@')
put('TXT', 'fc-htab fc| fc-ck-mem fc-stabs-mem fc-cbk-mem fc-link-mem fc-wt-mem fc-names-mem fc-wbk-mem fc-log-mem fc-decs-mem fc-calls-mem fc-pend-mem')
put('L3', 'fc-tab fc-binary fc-or-zero fc-ba fc-bb fc-br fc-shift-copy fc-inc fc-row-or-new fc-call-helper '
          'fc-result1 fc-result2 fc-s1 fc-s2 fc-r1')
put('L5p', 'fc-cost fc-mul-cost fc-div-cost fc-helpers-cost fc-price-word fc-known-xt fc-forbid gen-cost gen-price '
           'fc-time-price')
put('PRF', 'fc-proved fc-unproved fc-mechanisms fc-proved? gen-proved?')
put('L5r', 'fc-rt fc-rta fc-poke fc-concept-record fc-concepts fc-replacement')
put('L5h', 'fc-eval fc-nhost fc-platform fc-library gen-library gen-host fc-cpos fc-hn fc-cdepth fc-hname fc-hb '
           'fc-c, fc-c1 fc-c-gen fc-c-body')
put('CTL', 'fc-live fc-tramp fc-ex fc-halt fc-jump fc-end fc-begin-block fc-rows1 fc-nonzero fc-branch fc-ctl fc-nctl '
           'fc-cleave fc-ctl@ fc-ctl+ fc-ctl- fc-do-entry fc-ctl-leave fc-ctl-leave! fc-loop-leave fc-di fc-dl fc-lv '
           'gen-j')
put('DRV', 'fc-read fc-sizes kn-at kn-put kn-order kn-get kn-compile main fc-compile fc-go')
put('TXT', 'fc-install-generators fc-name2 fc-generators fc-generator fc-literal-name fc-gens fc-words fc-known '
           'fc-defining? fc-code fc-top-only fc-not-found fc-word-token fc-token fc-synonym-of fc-synonym fc-sy '
           'fc-synonym? fc-uses fc-word fc-scan-uses fc-init fc-define fc-lookup fc-find fc-word-of fc-hash '
           'fc-text-mem fc-text fc-tlen fc-pos fc-text-size fc-reset fc-append fc\\ fc-ch fc-more? fc-next fc-next! '
           'fc-is? fc-raw fc-string-token fc-names-size fc-max-words fc-names fc-names-used fc-wt fc-nwords fc-wbk '
           'fc-wt@ fc-max-consts fc-nbuckets')
# the generators of the words of the language: group of the word = group of its compiler (gen-*), set below.
GEN = {
    **{n: 'L3' for n in 'gen+ gen- gen-and gen-or gen-xor gen= gen< gen-u< gen-lshift gen-rshift gen-0= gen-cells '
       'gen-2* gen-1+ gen-1- gen-cell+ gen* gen/ gen-mod gen/mod'.split()},
    **{n: 'STK' for n in 'gen-dup gen-drop gen-swap gen-over gen-rot gen-pick gen-roll gen->r gen-r> gen-r@ '
       'gen-variable gen-create gen-allot gen-constant'.split()},
    **{n: 'MEM' for n in 'gen-@ gen-! gen-c@ gen-c!'.split()},
    **{n: 'L3' for n in 'gen-space! gen-spacec! gen-space@ gen-spacec@'.split()},
    **{n: 'CTL' for n in 'gen-if gen-else gen-then gen-begin gen-until gen-while gen-repeat gen-again gen-do gen-?do '
       'gen-loop gen-leave gen-unloop gen-exit gen-bye gen-recurse'.split()},
    **{n: 'CAL' for n in 'gen-tick gen-call gen-execute'.split()},
    **{n: 'TXT' for n in 'gen-colon gen-semicolon gen-decimal gen-kernel-layout gen-backslash gen-paren gen-char '
       'gen-string'.split()},
    **{n: 'LIT' for n in 'gen-literal'.split()},
}
# space of 8 and 32 bits and the computed copy: lines of forthc.fth (compile of SPACE! SPACE@)
RANGES = [
    ('forthc.fth', 34, 63, 'L3'),        # tables: fc-off, fc-t-*, entries, fc-tables, mul4, qsel
    ('forthc.fth', 66, 112, 'LIT'),      # constants and literals (14.7)
    ('forthc.fth', 114, 193, 'STK'),     # push/pop of registers, spill of the stack to memory
    ('forthc.fth', 194, 230, 'L5p'),     # log of layers of a word, per-word price (14.11)
    ('forthc.fth', 243, 288, 'CAL'),     # returns: table of returns, call, call-indirect
    ('forthc.fth', 289, 322, 'MEM'),     # access to memory of the program
    ('forthc.fth', 323, 373, 'SCH'),     # straight-line scheduler (model: Sched)
    ('forthc.fth', 374, 388, 'L3'),      # negate chain/select of the adder
    ('forthc.fth', 389, 479, 'L3'),      # multiplication and division by tables
    ('forthc.fth', 480, 545, 'L5p'),     # the longest path (14.11)
    ('forthc.fth', 744, 770, 'L3'),      # SPACE! SPACE@ (computed position, adder)
    ('primitives.fth', 4, 143, 'UNK'),   # gen-*: by GEN
]
GROUP_FOR_LAYOUT = 'LAY'


def classify(node, kind, target_group):
    name, file, line = node['name'], os.path.basename(node['file']), node['line']
    if kind == 'literal':
        return 'LIT', 'auto'
    if file == 'compute.fth' and name in ('lay-l1', 'lay-l2'):
        return 'L3', 'hand'
    if name in GEN:
        return GEN[name], 'hand'
    if name in NAMES:
        g = NAMES[name]
        if g == 'LAYOUT_L2':
            g = GROUP_FOR_LAYOUT
        return g, 'hand'
    if kind == 'generator' and target_group:
        return target_group, 'auto-gen'
    for f, lo, hi, g in RANGES:
        if file == f and lo <= line <= hi:
            return g, 'range'
    if file == 'compute.fth':
        return 'L3', 'range'
    if file == 'backend.fth' and name.startswith('dj-'):
        return 'PRF', 'range'
    if file == 'prelude.fth':
        return 'HF', 'range'
    return 'UNK', 'none'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cost')
    ap.add_argument('--tsv')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()
    graph, rows, _unused, _numbers, _entries = cc.core_nodes()
    byid = {r['node']['id']: r for r in rows}
    out = collections.defaultdict(set)         # edges inside the core (not self)
    gen_target = {}
    for e in graph.edges.values():
        if e['from'] in byid and e['to'] in byid and e['from'] != e['to']:
            out[e['from']].add(e['to'])
            if e.get('sub') == 'generator':
                gen_target[e['from']] = e['to']
    # step 1: non-generator nodes
    grp, how = {}, {}
    for r in rows:
        n = r['node']
        if r['kind'] != 'generator' or n['name'] in NAMES:
            grp[n['id']], how[n['id']] = classify(n, r['kind'], None)
    for r in rows:                              # step 2: names of generators from the compiler word
        n = r['node']
        if n['id'] not in grp:
            tg = grp.get(gen_target.get(n['id']))
            grp[n['id']], how[n['id']] = classify(n, r['kind'], tg)
    size = {}
    if a.cost:
        for line in open(a.cost):
            m = re.match(r'(\S+)\s+size\s+(\d+)\s+bits\s+(\d+)\s+copies\s+(\d+)\s+layers\s+(\d+)', line)
            if m:
                size[m.group(1)] = int(m.group(2))
    rank = {k: v[1] for k, v in GROUPS.items()}
    cnt = collections.Counter(grp.values())
    kinds = collections.defaultdict(collections.Counter)
    cells = collections.Counter()
    uniq = collections.defaultdict(set)
    seen_size = set()
    for r in rows:
        n = r['node']
        g = grp[n['id']]
        kinds[g][r['kind']] += 1
        uniq[g].add(n['name'])
        if r['kind'] == 'colon' and n['name'] in size and n['name'] not in seen_size:
            seen_size.add(n['name'])
            cells[g] += size[n['name']]
    total = sum(cells.values())
    print('words (nodes) %d, names %d' % (len(rows), len({r['node']['name'] for r in rows})))
    print('%-4s %5s %5s %5s %5s %6s %7s  %s' % ('grp', 'nodes', 'names', 'colon', 'var', 'cells', 'share', 'title'))
    for g, (title, _rk) in GROUPS.items():
        c = kinds[g]
        print('%-4s %5d %5d %5d %5d %6d %6.1f%%  %s' % (
            g, cnt[g], len(uniq[g]), c['colon'], c['variable'] + c['create'] + c['constant'] + c['value'], cells[g],
            100.0 * cells[g] / total if total else 0, title))
    print('total cells', total)
    # violations: lower rank word uses higher rank word
    viol = collections.defaultdict(list)
    ops = collections.defaultdict(set)
    opw = collections.defaultdict(set)
    matrix = collections.Counter()
    for r in rows:
        n = r['node']
        gf = grp[n['id']]
        for t in out[n['id']]:
            gt = grp[t]
            matrix[(gf, gt)] += 1
            if rank[gf] and rank[gt] and rank[gf] < rank[gt]:
                tk = byid[t]['kind']
                if tk in ('generator', 'literal'):          # an operator of the Forth text (+ dup @ if 3 ...)
                    ops[(gf, gt)].add(byid[t]['node']['name'])
                    opw[(gf, gt)].add(n['name'])
                else:
                    viol[(gf, gt)].append((n['name'], byid[t]['node']['name']))
    print('\nVIOLATIONS between subsystems (not Forth operators) (from, to): count; examples')
    for (gf, gt), lst in sorted(viol.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        ex = ', '.join('%s>%s' % x for x in lst[:6])
        print('%s -> %s: %d edges, %d words from; %s' % (gf, gt, len(lst), len({x[0] for x in lst}), ex))
    print('\nOPERATORS OF FORTH (from, to): distinct operators; words from')
    for (gf, gt), st in sorted(ops.items()):
        print('%s -> %s: %d operators, %d words: %s' % (gf, gt, len(st), len(opw[(gf, gt)]), ' '.join(sorted(st)[:14])))
    if a.verbose:
        print('\nMATRIX')
        for (gf, gt), c in sorted(matrix.items()):
            print(gf, gt, c)
    unk = [byid_id for byid_id in grp if grp[byid_id] == 'UNK']
    print('\nUNK:', [byid[i]['node']['name'] + ':' + str(byid[i]['node']['line']) for i in unk])
    if a.tsv:
        with open(a.tsv, 'w') as f:
            f.write('no\tword\tkind\tfile:line\tgroup\thow\tcells\tuses_words\n')
            for i, r in enumerate(rows, 1):
                n = r['node']
                f.write('%d\t%s\t%s\t%s:%d\t%s\t%s\t%s\t%s\n' % (
                    i, n['name'], r['kind'], n['file'].replace('language/', ''), n['line'], grp[n['id']], how[n['id']],
                    size.get(n['name'], '') if r['kind'] == 'colon' else '',
                    ' '.join(sorted({byid[t]['node']['name'] for t in out[n['id']]}))))
    return viol, matrix


if __name__ == '__main__':
    main()
