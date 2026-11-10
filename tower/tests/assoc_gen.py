"""The sizes of the associative space (25.2): the parts of programs/assoc/assoc_*.tw between the lines
`# === sizes begin` and `# === sizes end` (data and tables) and `# === words begin` and `# === words end` (the small words which depend on the widths) is made
here from four numbers: KB (key bits), VB (value bits), C (cell bits: 2^C cells) and the method; the rest of the
text does not depend on them. Not a tool of the chain: only a test and the measurement run it (Python is only in tests).
Run: python3 -B tower/tests/assoc_gen.py   (rewrites the sizes of the committed programs)."""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAMS = os.path.join(HERE, '..', 'programs', 'assoc')
G = 2                                         # the width of a part of a key in the tree (fixed in the text)
BEGIN, END = '# === sizes begin', '# === sizes end'
WBEGIN, WEND = '# === words begin', '# === words end'
DEFAULT = {'hash': (8, 8, 4), 'tree': (8, 8, 4)}


def tab(name, k, w, vals):
    rows = [' '.join(str(x) for x in vals[i:i + 16]) for i in range(0, len(vals), 16)]
    return ':%s table %d %d\n  %s\n' % (name, k, w, '\n  '.join(rows))


def nodes(kb, vb, c):
    """The pool of the tree: node numbers 1..2^NB-1; two roots, and for every one of the 2^C-1 cells at most
    one new path in the tree of keys and one in the tree of values (the worst case; full trees are smaller)."""
    def side(bits):
        d = bits // G
        return min(sum(4 ** i for i in range(1, d)), ((1 << c) - 1) * (d - 1))
    need = 2 + side(kb) + side(vb)
    nb = 1
    while (1 << nb) - 1 < need:
        nb += 1
    return nb, need


def sizes(method, kb, vb, c):
    w = max(kb, vb)
    assert kb % 8 == 0 and vb % 8 == 0 and 1 <= c <= 8 and method in ('hash', 'tree')
    n = 1 << c
    s = [BEGIN + ' (made by tower/tests/assoc_gen.py: %s, key %d bits, value %d bits, %d cells)' % (method, kb, vb, n),
         '# the entity of a cell: key (sel=0) or value (sel=1) padded with zeros to W bits',
         ':cmd data 8 0', ':k data %d 0' % kb, ':v data %d 0' % vb, ':e data %d 0' % w, ':t data %d 0' % w,
         ':zw data %d 0' % w, ':onesw data %d %d' % (w, (1 << w) - 1), ':onesk data %d %d' % (kb, (1 << kb) - 1),
         ':onesv data %d %d' % (vb, (1 << vb) - 1), ':mk data %d 0' % (kb // 4), ':mv data %d 0' % (vb // 4),
         ':mq data %d 0' % (w // 4), ':mp data 2 0',
         ':sel data 1 0', ':selone data 1 1', ':fl data 1 0', ':fz data 1 0',
         ':ic data %d 0' % c, ':ac data %d 0' % c, ':dc data %d 0' % c, ':nc data %d 0' % c, ':wc data %d 0' % c,
         ':ot data %d 0' % c, ':pv data %d 0' % c, ':xr data %d 0' % c, ':yr data %d 0' % c,
         ':qa data %d 0' % c, ':qb data %d 0' % c, ':pr data %d 0' % c, ':tc data %d 0' % c, ':zc data %d 0' % c,
         ':fh data %d 0' % c, ':tp data %d 1' % c, ':ix data %d 0' % (c + 1),
         ':ixc0 data %d 0' % (c + 1), ':ixc1 data %d %d' % (c + 1, 1 << c),
         ':pa data 8 0', ':pb8 data 8 0', ':pb data 8 0', ':pq data 8 0', ':ffb data 8 255',
         ':ce array %d %d' % (c + 1, w), ':cp array %d %d' % (c, c), ':sy array %d %d' % (c, c),
         tab('isz', c, 1, [1] + [0] * (n - 1)).rstrip('\n'), tab('inc', c, c, [(i + 1) % n for i in range(n)]).rstrip('\n')]
    words = [
        ':mke_k word', 'copy &e &zw', 'copy &e[0:%d] &k' % kb, 'ret',
        ':mke_v word', 'copy &e &zw', 'copy &e[0:%d] &v' % vb, 'ret',
        ':mkix word', 'copy &ix[0:%d] &ic' % c, 'copy &ix[%d:%d] &sel' % (c, c + 1), 'ret',
        ':eqe word', 'eq &e &t &mq', 'copy &fl &mq[%d]' % (w // 4 - 1), 'ret',
        ':eqp word', 'copy &pa[0:%d] &qa' % c, 'copy &pb8[0:%d] &qb' % c, 'eq &pa &pb8 &mp', 'copy &fl &mp[1]', 'ret',
        ':chk_k word', 'eq &k &onesk &mk', 'copy &fl &mk[%d]' % (kb // 4 - 1), 'ret',
        ':chk_v word', 'eq &v &onesv &mv', 'copy &fl &mv[%d]' % (vb // 4 - 1), 'ret',
        ':outk word', 'emit &t[0:%d]' % kb, 'ret',
        ':outv word', 'emit &t[0:%d]' % vb, 'ret',
        ':outc word', 'copy &pb[0:%d] &qa' % c, 'emit &pb', 'ret',
        ':getq word', 'copy &ic &pq[0:%d]' % c, 'ret',
    ]
    if method == 'hash':
        h = c
        s += [':hx data %d 0' % (h + 1), ':hd array %d %d' % (h + 1, c), ':cn array %d %d' % (c + 1, c)]
        words += [':mkh word', 'copy &hx[0:%d] &e[0:%d]' % (h, h), 'copy &hx[%d:%d] &sel' % (h, h + 1), 'ret']
    else:
        nb, need = nodes(kb, vb, c)
        pw = max(nb, c)
        s += ['# the pool of the tree: nodes 1..%d, at most %d in use' % ((1 << nb) - 1, need),
              ':nd data %d 0' % nb, ':nx data %d 0' % nb, ':nn data %d 0' % nb, ':nf data %d 0' % nb,
              ':ntp data %d 3' % nb, ':tx data %d 0' % (nb + G), ':ent data %d 0' % pw, ':zp data %d 0' % pw,
              ':w data %d 0' % w, ':wy data %d 0' % w, ':lv data 4 0', ':li data 3 0', ':z3 data 3 0', ':c3 data 3 0',
              ':nt array %d %d' % (nb + G, pw), ':cnt array %d 3' % nb, ':nfl array %d %d' % (nb, nb),
              ':ptx array 3 %d' % (nb + G),
              tab('isn', nb, 1, [1] + [0] * ((1 << nb) - 1)).rstrip('\n'),
              tab('incn', nb, nb, [(i + 1) % (1 << nb) for i in range(1 << nb)]).rstrip('\n'),
              tab('rt', 1, nb, [1, 2]).rstrip('\n'), tab('dep1', 1, 4, [kb // G - 1, vb // G - 1]).rstrip('\n')]
        words += [':mktx word', 'copy &tx[0:%d] &w[0:%d]' % (G, G), 'copy &tx[%d:%d] &nd' % (G, G + nb), 'ret',
                  ':tx2nd word', 'copy &nd &tx[%d:%d]' % (G, G + nb), 'ret',
                  ':ent2ic word', 'copy &ic &ent[0:%d]' % c, 'ret',
                  ':ent2nx word', 'copy &nx &ent[0:%d]' % nb, 'ret',
                  ':ic2ent word', 'copy &ent &zp', 'copy &ent[0:%d] &nc' % c, 'ret',
                  ':nx2ent word', 'copy &ent &zp', 'copy &ent[0:%d] &nx' % nb, 'ret']
    return '\n'.join(s) + '\n' + END + '\n', WBEGIN + ' (made by tower/tests/assoc_gen.py)\n' + '\n'.join(words) + '\n' + WEND + '\n'


def render(text, method, kb, vb, c):
    """The text with its region of sizes replaced by the sizes of (kb, vb, c)."""
    d, w = sizes(method, kb, vb, c)
    a, b = text.index(BEGIN), text.index(END)
    text = text[:a] + d + text[text.index('\n', b) + 1:]
    a, b = text.index(WBEGIN), text.index(WEND)
    return text[:a] + w + text[text.index('\n', b) + 1:]


def source(method, kb=None, vb=None, c=None):
    d = DEFAULT[method]
    with open(os.path.join(PROGRAMS, 'assoc_%s.tw' % method), encoding='utf-8') as h:
        text = h.read()
    return render(text, method, kb or d[0], vb or d[1], c or d[2])


def main():
    for method, (kb, vb, c) in DEFAULT.items():
        path = os.path.join(PROGRAMS, 'assoc_%s.tw' % method)
        with open(path, encoding='utf-8') as h:
            text = h.read()
        with open(path, 'w', encoding='utf-8') as h:
            h.write(render(text, method, kb, vb, c))


if __name__ == '__main__':
    main()
