"""The numbers of the generated tables of the texts of the passes: the formulas which the Python references l2text, l2ltext, l3ctext (gone, 25.7.3.4) made them by, kept here for the tests:
the tables cls and attr of programs/l2c.tw, cls of l2l.tw, the tables between `# --- begin generated` and `# --- end generated` of l3c.tw, l3p.tw and l4c.tw, the words of the
links of l4c.tw (FARWORDS) and the sizes the passes fit (MAXSYM, MAXLAB, MAXTOK). A test compares the text of each .tw with the text made here: the text of the pass is the
definition, the formula only tells where the numbers come from. Only the generation of the tables: no encoder.
Run: python3 -B tower/tests/tables.py   (prints whether the tables in the texts are the ones made here);  python3 -B tower/tests/tables.py -p l3c   (prints the tables of l2c, l2l, l3c, l3p or l4c)"""
import os
import sys

sys.dont_write_bytecode = True



# ---- l2c.tw (language 2): the classes of the bytes (14 bits) and the attributes of the commands (12 bits)
M = (1 << 20) - 1
HEX = '0123456789abcdef'
CODES = {'w': 1, 'r': 2, 'z': 3, 's': 4, '#': 5, 'c': 6, 'd': 7, 'o': 8, ':': 9}
ATTR = {1: (1, 1, 1, 0, 0, 1, 0, 0), 2: (0, 1, 0, 1, 0, 1, 1, 0), 3: (1, 1, 1, 0, 0, 1, 0, 0), 4: (0, 1, 0, 1, 1, 1, 0, 0),
        5: (0, 1, 0, 1, 0, 1, 0, 0), 6: (3, 0, 1, 0, 0, 1, 0, 0), 7: (2, 0, 1, 0, 0, 1, 0, 0), 8: (0, 0, 1, 0, 0, 1, 0, 0),
        9: (0, 0, 0, 0, 0, 1, 0, 1)}
ATTR_BITS = (6, 4, 5, 8, 9, 10, 11)         # the bit of: echo, numeric, skipping, bits, valid, row, label
def rev8(c):
    return int(format(c, '08b')[::-1], 2)
def l2c_cls(c):
    """The class of a byte (14 bits). 0 bit char 0/1, 1 hex digit, 2 separator, 3 line break or zero byte, 4-7 the value
    of a digit, or (not a digit) 5 `&`, 6 `+`; 8-11 the code of the command letter (: is 9), 12 a lowercase letter, 13 zero byte."""
    ch = chr(c)
    v = 0
    if ch in '01':
        v |= 1
    if ch in HEX:
        v |= 2 | HEX.index(ch) << 4
    if ch in ' \t\r\n\0':
        v |= 4
    if ch in '\n\0':
        v |= 8
    v |= {'&': 1 << 5, '+': 1 << 6}.get(ch, 0)
    v |= CODES.get(ch, 0) << 8
    if 'a' <= ch <= 'z':
        v |= 1 << 12
    if c == 0:
        v |= 1 << 13
    return v
def attr(code):
    """The attributes of a command code (12 bits): 0-3 need, 4 numeric, 5 skipping, 6 echo, 8 bits, 9 valid, 10 row, 11 label."""
    n, *fl = ATTR.get(code, (0,) * 8)
    return n | sum(f << b for f, b in zip(fl, ATTR_BITS, strict=True))
def table_lines(f, n, per=16):
    """The values of a table of 2**n entries as lines of the text of language 3."""
    vals = [f(i) for i in range(1 << n)]
    return '\n'.join('  ' + ' '.join(str(v) for v in vals[i:i + per]) for i in range(0, len(vals), per))
def l2c_cls_table():
    """The table cls: the index is the number with the first bit of the byte the lowest, so a byte c stands at rev8(c)."""
    return table_lines(lambda i: l2c_cls(rev8(i)), 8)


# ---- l2l.tw: the same, but the bit 12 of the class is a name byte
NAME = frozenset(b'abcdefghijklmnopqrstuvwxyz0123456789_')
MAXLAB = 1024


def l2l_cls(c):
    """The class of a byte (14 bits), as l2c_cls, but bit 12 is a name byte (a-z 0-9 _), not a lowercase letter."""
    v = l2c_cls(c) & ~(1 << 12)
    return v | ((1 << 12) if c in NAME else 0)


def l2l_cls_table():
    return table_lines(lambda i: l2l_cls(rev8(i)), 8)


# ---- l3c.tw, l3p.tw, l4c.tw (language 3): the words, the shapes of their arguments, the tables of the library
A = 20
RB, JB = 4 * A, 8 * A                 # a row, a layer (the row and the jump)
LIMIT = 0xfa000                        # the place of the tables of the library (bits): the image of a pass of A = 20 is smaller
MAXSYM = 1020                          # the symbols of a user (with add4, sub4, hex4, zero they fill the 1024 places)
ZERO_ADDR, ONE_ADDR, START = JB, JB + 64, JB + 65
WS = b' \t\r\n'
IDENT = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_')
DIGITS = frozenset(b'0123456789')
ESC = {ord('n'): 10, ord('t'): 9, ord('r'): 13, ord('0'): 0, ord('\\'): 92, ord('"'): 34}
WORDS = ['data', 'table', 'array', 'copy', 'shl', 'shr', 'lut', 'store', 'block', 'word', 'goto', 'if', 'call', 'ret', 'halt',
         'emit', 'warn', 'key', 'add', 'sub', 'band', 'lt', 'eq', 'pack']
DEFINING = ('data', 'table', 'array', 'block', 'word')

SHAPE = {'data': ('N1:65536', 'V'), 'table': ('N1:10', 'N1:64'), 'array': ('N1:10', 'N1:64'), 'copy': ('R', 'R'),
         'shl': ('R', 'R', 'N0:64'), 'shr': ('R', 'R', 'N0:64'), 'block': (), 'word': (), 'goto': ('B',), 'if': ('R', 'B', 'B'),
         'call': ('B', 'B'), 'ret': (), 'halt': (), 'emit': ('R',), 'warn': ('R',), 'key': ('R',)}
for _w in ('add', 'sub', 'band', 'lt', 'eq'):
    SHAPE[_w] = ('R', 'R', 'R')
SHAPE['pack'] = ()
SHAPE['lut'] = SHAPE['store'] = ('T',)         # the rest depends on the table

# the tables the tool makes at the end: name -> (label, index widths, out, function of the indices)

BUILTIN = {
    'add4': ('ta', (4, 4, 1), 5, lambda a, b, c: a + b + c),
    'sub4': ('ts', (4, 4, 1), 5, lambda a, b, c: (a - b - c) & 31),
    'and4': ('tn', (4, 4), 4, lambda a, b: a & b),
    'lt4c': ('tl', (4, 4, 1), 1, lambda a, b, c: int(a < b or (a == b and c))),
    'eq4c': ('te', (4, 4, 1), 1, lambda a, b, c: int(a == b and c)),
    'hex4': ('th', (4,), 8, lambda x: rev8(ord('0123456789abcdef'[x]))),
}
EXPLICIT = ('add4', 'sub4', 'hex4')       # the tables which a text may name (the others are made for add sub band lt eq)
KR, KB, KV, KT, KND, KNK, KNO, KNS = 1, 2, 3, 4, 5, 6, 7, 8
NRANGE = {KND: (1, 65536), KNK: (1, 10), KNO: (1, 64), KNS: (0, 64)}
KINDS = {'R': KR, 'B': KB, 'V': KV, 'T': KT, 'N1:65536': KND, 'N1:10': KNK, 'N1:64': KNO, 'N0:64': KNS}
LIBP = {  # builtin, nins, step, odel, cdel, fc (first carry is a constant), c0 (1: one), the width of the result
    'add': (0, 3, 4, 0, 0, 1, 0, 0), 'sub': (1, 3, 4, 0, 0, 1, 0, 0), 'band': (2, 2, 4, 0, 0, 0, 0, 1),
    'lt': (3, 3, 1, 1, 1, 0, 0, 3), 'eq': (4, 3, 1, 0, 1, 1, 1, 2)}


def shape_kind(wd, na):
    w = WORDS[wd]
    if w == 'table':
        return (KNK, KNO)[na] if na < 2 else KV
    if w in ('lut', 'store'):
        return KT if na == 0 else KR
    sh = SHAPE[w]
    return KINDS[sh[na]] if na < len(sh) else 0


def tvals(vals, per=16):
    return '\n'.join('  ' + ' '.join(str(v) for v in vals[i:i + per]) for i in range(0, len(vals), per))


def istr(b):
    """A string of bytes as a text of language 3 (escapes for what is not a letter)."""
    return '"' + ''.join('\\0' if c == 0 else '\\n' if c == 10 else chr(c) for c in b) + '"'


def l3c_cls(c):
    v = 0
    ch = chr(c)
    if c == 0:
        v |= 1
    if ch in ' \t\r\n':
        v |= 2
    if ch == '\n':
        v |= 4
    v |= {'#': 8, '"': 16, '\\': 32, ':': 64, '&': 128, '[': 256, ']': 512}.get(ch, 0)
    if ch.isdigit() and c < 128:
        v |= 1024 | int(ch) << 12
    if c < 128 and (ch.isalnum() or ch == '_'):
        v |= 2048
    return v


def generated():
    """name -> (K, out, lines of values) for the tables of l3c.tw made by this module."""
    T = {}
    T['cls'] = (8, 16, tvals([l3c_cls(rev8(i)) for i in range(256)]))
    T['escv'] = (8, 9, tvals([(256 | rev8(ESC[rev8(i)])) if rev8(i) in ESC else 0 for i in range(256)]))
    kws = ['"' + '\\0' * (5 - len(w)) + w + '"' for w in WORDS] + ['"\\0\\0\\0\\0\\0"'] * (32 - len(WORDS))
    T['kw'] = (5, 40, '\n'.join('  ' + ' '.join(kws[i:i + 4]) for i in range(0, 32, 4)))
    T['shape'] = (8, 4, tvals([shape_kind(i >> 3, i & 7) if i >> 3 < len(WORDS) else 0 for i in range(256)], 8))
    T['wcl'] = (5, 4, tvals([(1 if w == 'table' else 0) | (2 if w in ('lut', 'store') else 0) | (4 if w == 'data' else 0)
                             | (8 if w == 'array' else 0) for w in WORDS + [''] * (32 - len(WORDS))]))
    T['defn'] = (5, 1, tvals([int(w in DEFINING) for w in WORDS + [''] * (32 - len(WORDS))]))
    T['isdecl'] = (5, 1, tvals([int(w in ('data', 'table', 'array')) for w in WORDS + [''] * (32 - len(WORDS))]))
    T['ar0'] = (5, 1, tvals([int(w != '' and not SHAPE[w]) for w in WORDS + [''] * (32 - len(WORDS))]))
    T['isret'] = (5, 1, tvals([int(w == 'ret') for w in WORDS + [''] * (32 - len(WORDS))]))
    T['isp'] = (5, 1, tvals([int(w == 'pack') for w in WORDS + [''] * (32 - len(WORDS))]))
    T['lp'] = (5, 16, tvals([(lambda p: p[0] | p[1] << 3 | p[2] << 5 | p[3] << 8 | p[4] << 9 | p[5] << 10 | p[6] << 11 | p[7] << 12)(
        LIBP[w]) if w in LIBP else 0 for w in WORDS + [''] * (32 - len(WORDS))]))
    T['mm'] = (2, 20, tvals([(2 * n + 1) * JB for n in range(4)]))
    T['fa'] = (1, 20, tvals([2 * A, 0]))
    T['fb'] = (1, 20, tvals([3 * A, A]))
    T['p2e'] = (5, 20, tvals([1 << e if e < 20 else 0 for e in range(32)]))
    T['mask'] = (5, 20, tvals([(1 << e) - 1 if e < 20 else 0 for e in range(32)]))
    T['jt'] = (7, 3, tvals([min(i.bit_length(), 7) for i in range(128)]))
    T['strd'] = (3, 8, tvals([1 << j for j in range(8)]))
    T['m20'] = (3, 5, tvals([min(1 << j, 20) for j in range(8)]))
    T['nlo'] = (4, 20, tvals([NRANGE[k][0] if k in NRANGE else 0 for k in range(16)]))
    T['nhi'] = (4, 20, tvals([NRANGE[k][1] if k in NRANGE else 0 for k in range(16)]))
    T['inc8'] = (8, 8, tvals([(i + 1) & 255 for i in range(256)]))
    names = list(EXPLICIT) + ['zero']
    T['bn'] = (2, 32, '\n'.join('  ' + istr(n.encode()) for n in names))
    idx = [list(BUILTIN).index(n) for n in EXPLICIT]
    T['bk'] = (2, 3, tvals([4] * 3 + [1]))
    T['ba'] = (2, 8, tvals(idx + [ZERO_ADDR]))
    allin = [(BUILTIN[n][1], BUILTIN[n][2]) for n in BUILTIN]
    T['bi'] = (3, 19, tvals([sum(k << (4 * i) for i, k in enumerate(a)) | o << 12 for a, o in allin] + [0, 0]))
    T['bfk'] = (3, 5, tvals([sum(i[0]) for i in [(BUILTIN[n][1],) for n in BUILTIN]] + [0, 0]))
    T['bfe'] = (3, 5, tvals([sum(BUILTIN[n][1]) + BUILTIN[n][2].bit_length() for n in BUILTIN] + [0, 0]))
    T['bfw'] = (3, 5, tvals([min(1 << BUILTIN[n][2].bit_length(), 20) for n in BUILTIN] + [0, 0]))
    T['bfc'] = (3, 8, tvals([rev8(ord(BUILTIN[n][0][1])) for n in BUILTIN] + [0, 0]))
    return T


def p_generated():
    """name -> (K, out, lines of values) for the tables of programs/l3p.tw made by this module (the pass of 23.10)."""
    T = {}
    T['cls'] = (8, 4, tvals([(1 if c == 0 else 0) | (2 if c == 32 else 0) | (4 if c == 10 else 0) | (8 if c == 38 else 0) for c in map(rev8, range(256))]))
    T['hexv'] = (8, 5, tvals([(int(chr(c), 16) | 16) if chr(c) in '0123456789abcdef' else 0 for c in map(rev8, range(256))]))
    T['fcl'] = (8, 3, tvals([{0: 7, ord(':'): 1, ord('#'): 2, ord('o'): 3, ord('c'): 4, ord('z'): 5, ord('d'): 6}.get(c, 0) for c in map(rev8, range(256))]))
    T['tbase'] = (8, 20, tvals([TBASE + 0x1000 * TNUM[chr(c)] if chr(c) in TNUM else 0 for c in map(rev8, range(256))]))
    T['mu'] = (2, 20, tvals([80 * i for i in range(4)]))
    T['mask'] = (5, 20, tvals([(1 << e) - 1 if e < 20 else 0 for e in range(32)]))
    T['p2e'] = (5, 20, tvals([1 << e if e < 20 else 0 for e in range(32)]))
    T['inc8'] = (8, 8, tvals([(i + 1) & 255 for i in range(256)]))
    return T


TBASE = 0xfa000                          # the place of the table of the library 'ta ts tn tl te th' (a, s, n, l, e, h): +0x1000 * its number


TNUM = {'a': 0, 's': 1, 'n': 2, 'l': 3, 'e': 4, 'h': 5}


def cc(c):
    """The class of a byte for programs/l4c.tw: bits 0 zero byte, 1 blank, 2 #, 3 ", 4 \\, 5 line break, 6 letter digit or _, 7 digit."""
    v = int(c == 0) | int(c in WS) << 1 | int(c == 35) << 2 | int(c == 34) << 3 | int(c == 92) << 4 | int(c == 10) << 5
    v |= int(c in IDENT) << 6 | int(c in DIGITS) << 7
    return v


def x_generated():
    """name -> (K, out, lines of values) for the tables of programs/l4c.tw made by this module (the pass of language 4)."""
    T = {}
    T['cc'] = (8, 8, tvals([cc(c) for c in map(rev8, range(256))]))
    T['hexv'] = (8, 5, tvals([(int(chr(c), 16) | 16) if chr(c) in '0123456789abcdefABCDEF' else 0 for c in map(rev8, range(256))]))
    # the text of a nibble source `&l4n1[4:8]`, a byte at an index k + 16 v (v: the nibble, k: the place in the text), 0 after its end
    T['nsrc'] = (8, 8, '\n'.join('  ' + ' '.join(istr(bytes([_nib(v)[k].encode()[0]])) if k < len(_nib(v)) else '0' for k in range(16)) for v in range(16)))
    T['tlok'] = (7, 1, tvals([int(i < MAXTOK) for i in range(128)]))
    return T


def x_tables_text():
    return '\n'.join(':%s table %d %d\n%s' % (n, K, w, v) for n, (K, w, v) in x_generated().items()) + '\n'


def p_tables_text():
    return '\n'.join(':%s table %d %d\n%s' % (n, K, w, v) for n, (K, w, v) in p_generated().items()) + '\n'


def tables_text():
    return '\n'.join(':%s table %d %d\n%s' % (n, K, w, v) for n, (K, w, v) in generated().items()) + '\n'


# ---- l4c.tw (language 4): the constants of the pass and the words of the far links
NBUF = 2048                           # the bits of data of a long copy (the buffer l4q has 204 + NBUF)
L4N = (274960, 624485, 974010, 15)    # the nibbles 0..4, 5..9, 10..14, 15 (20 bits, a nibble in 4 bits, low first)
MAXTOK = 120                          # a longer token is cut (l3c takes none so long)
def _nib(v):
    return '&l4n%d[%d:%d]' % (v // 5, 4 * (v % 5), 4 * (v % 5) + 4)
FARASK = (':l4ask word\ncopy &l4q[400:404] &l4z[0:4]\ngoto &l4a1\n:l4a1 block\ncopy &l4q[56:72] &l4z[0:16]\n'
          'add &l4q[0:8] &l4q[8:16] &l4q[410:419]\nadd &l4q[410:418] &l4q[16:24] &l4q[420:429]\nadd &l4q[420:428] &l4q[24:32] &l4q[430:439]\n'
          'add &l4q[430:438] &l4q[32:40] &l4q[440:449]\nadd &l4q[440:448] &l4q[40:48] &l4q[450:459]\ncopy &l4q[48:56] &l4q[450:458]\n'
          'emit &l4q[0:56]\nkey &l4q[56:72]\ngoto &l4a2\n:l4a2 block\ncopy &l4q[460:464] &l4n3[0:4]\ncopy &l4q[464:468] &l4n3[0:4]\n'
          'add &l4q[56:64] &l4q[64:72] &l4q[470:479]\neq &l4q[470:478] &l4q[460:468] &l4q[480:482]\nif &l4q[481] &l4a3 &l4a4\n:l4a3 block\nret\n'
          ':l4a4 block\nadd &l4q[400:404] &l4n0[4:8] &l4q[490:495]\ncopy &l4q[400:404] &l4q[490:494]\nlt &l4q[400:404] &l4n0[16:20] &l4q[500:502]\n'
          'if &l4q[501] &l4a1 &l4a5\n:l4a5 block\ncopy &l4q[56:60] &l4n3[0:4]\ncopy &l4q[60:64] &l4n3[0:4]\nret\n')
FARFLAG = (':l4flag word\ncopy &l4q[44:64] &l4z[0:20]\ncopy &l4q[44:48] &l4n0[16:20]\ncopy &l4q[82] &l4n0[4]\ncopy &l4q[204:208] &l4n0[4:8]\n'
           'copy 1048570 &l4q[0:208]\nret\n')
FARGET = (':l4fget word\ncopy &l4q[420:440] &l4q[44:64]\ncopy &l4q[44:64] &l4z[0:20]\ncopy &l4q[44:48] &l4n0[16:20]\ncopy &l4q[82] &l4n0[4]\n'
          'copy &l4q[400:420] &l4z[0:20]\ncopy &l4q[440:460] &l4z[0:20]\ncopy &l4q[440:444] &l4n0[4:8]\ncopy &l4q[460:480] &l4z[0:20]\n'
          'copy &l4q[476:480] &l4n0[16:20]\ngoto &l4g1\n:l4g1 block\ncopy 1048570 &l4q[0:204]\ncopy &l4q[204:321] 1048570\n'
          'if &l4q[204] &l4g2 &l4g3\n:l4g2 block\ncopy &l4q[44:64] &l4q[420:440]\ncopy &l4q[82] &l4z[0]\ncopy 1048570 &l4q[0:204]\n'
          'copy &l4q[204:321] 1048570\nret\n:l4g3 block\nadd &l4q[400:420] &l4q[440:460] &l4q[490:511]\ncopy &l4q[400:420] &l4q[490:510]\n'
          'lt &l4q[400:420] &l4q[460:480] &l4q[520:526]\nif &l4q[525] &l4g1 &l4g4\n:l4g4 block\ncopy &l4q[204:208] &l4n3[0:4]\n'
          'copy &l4q[208:212] &l4q[204:208]\ncopy &l4q[212:220] &l4q[204:212]\ncopy &l4q[220:236] &l4q[204:220]\ncopy &l4q[236:268] &l4q[204:236]\nret\n')
FARWORDS = (FARASK, FARFLAG, FARGET)         # the words of the links 1 and 2, put once at the end of the text if a far copy used them (in this order)


# ---- the tables as the texts of the passes have them

BEGIN, END = '# --- begin generated\n', '# --- end generated'


def generated_block(src):
    """The text between the marks `# --- begin generated` and `# --- end generated` of a text of language 3."""
    return src[src.index(BEGIN) + len(BEGIN):src.index(END)]


def l2_tables():
    """The two tables of the text l2c.tw as it has them (the lines between the labels are the numbers)."""
    return [':cls table 8 14\n' + l2c_cls_table() + '\n', ':attr table 4 12\n' + table_lines(attr, 4) + '\n']


def l2l_tables():
    """The table cls of l2l.tw (the table attr is the same as in l2c.tw)."""
    return [':cls table 8 14\n' + l2l_cls_table() + '\n', ':attr table 4 12\n' + table_lines(attr, 4) + '\n']


def main():
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programs')

    def read(n):
        with open(os.path.join(here, n), encoding='utf-8') as h:
            return h.read()
    if sys.argv[1:2] == ['-p']:                      # the tables of a text, to put between its marks: -p l2c | l2l | l3c | l3p | l4c
        made = {'l2c': ''.join(l2_tables()), 'l2l': ''.join(l2l_tables()), 'l3c': tables_text(), 'l3p': p_tables_text(), 'l4c': x_tables_text()}
        sys.stdout.write(made[sys.argv[2]])
        return
    ok = all(t in read('l2c.tw') for t in l2_tables()) and all(t in read('l2l.tw') for t in l2l_tables())
    for n, made in (('l3c', tables_text()), ('l3p', p_tables_text()), ('l4c', x_tables_text())):
        ok = ok and generated_block(read(n + '.tw')) == made
    print('the tables of the texts are the ones made here' if ok else 'THE TABLES OF THE TEXTS DIFFER')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
