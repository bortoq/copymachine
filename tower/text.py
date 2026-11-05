"""Text of programs of the tower (seed, host, temporary): the parser of the compiler of language N.
One syntax for all languages: words separated by spaces and line breaks, numbers (decimal, 0x hex),
labels `:name` (definition) and `&name` (reference, as in hex2 of stage0; `&name[lo:hi]` or `&name[k]`
is a part of space), strings "..." and characters 'c', comments `# ...`. Every language has its own set of
words (WORDS: the level of the language, the grammar of the arguments); the text is read by the grammar
alone: an unknown word, a wrong number or kind of arguments, an undefined or repeated label, a width which
the lower language cannot write are reported at parse time and the program is rejected. What is accepted
is turned into calls of the constructors of the same languages (Parsed.build), which cannot fail
(the names are only here: the image has none). The words:
  2 (copy, data): data copy shl shr
  3 (tables, blocks, library): table array lut store block word goto if call ret halt emit warn key
    add sub band lt eq stack push pop rec
  4 (long copy): long! long@
Run: python3 -m tower.text [-l LEVEL] < prog.tw > image   (A and P of the image go to stderr)."""
import os
import re
import sys
from collections import namedtuple

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import l3
from common import bytes_value, rev

TOKEN = re.compile(r'''\s+|#[^\n]*|("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|\S+)''')
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
RESERVED = re.compile(r'(add4|sub4|and4|lt4c|eq4c|hex4|dec\d+|inc\d+_\d|dec\d+_\d|if\d+|zero)\Z')
REF = re.compile(r'&([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)(?::(\d+))?\])?\Z')
ESC = {'n': 10, 't': 9, 'r': 13, '0': 0, '\\': 92, '"': 34, "'": 39}
Tok = namedtuple('Tok', 'text line col')
Tab = namedtuple('Tab', 'name ins out array')            # a table which lut and store can use
Stk = namedtuple('Stk', 'k w')                           # a stack: pointer bits, entry bits (0: a link)
Lab = namedtuple('Lab', 'kind bits tab stk')
Rf = namedtuple('Rf', 'name lo hi')


def tokens(text):
    line, pos = 1, 0
    for m in TOKEN.finditer(text):
        if m.group(1):
            line += text.count('\n', pos, m.start())
            pos = m.start()
            yield Tok(m.group(1), line, m.start() - (text.rfind('\n', 0, m.start()) + 1) + 1)


def wordlike(t):
    return t.text[0].isalpha() or t.text[0] == ':'


def number(s):
    if re.match(r'0[xX][0-9a-fA-F]+\Z', s):
        return int(s, 16)
    return int(s) if re.match(r'[0-9]+\Z', s) else None


def unescape(body):
    out, i = bytearray(), 0
    while i < len(body):
        c = body[i]
        if c != '\\':
            if ord(c) > 255:
                return None
            out.append(ord(c))
        elif body[i + 1:i + 2] == 'x' and re.match(r'[0-9a-fA-F]{2}\Z', body[i + 2:i + 4]):
            out.append(int(body[i + 2:i + 4], 16)); i += 3
        elif body[i + 1:i + 2] in ESC:
            out.append(ESC[body[i + 1]]); i += 1
        else:
            return None
        i += 1
    return bytes(out)


def builtin(name):
    """The tables which the compiler knows by name (created at the first use, as the lower language does)."""
    if name in ('add4', 'sub4'):
        return Tab(name, (4, 4, 1), 5, False)
    if name == 'hex4':
        return Tab(name, (4,), 8, False)
    m = re.match(r'dec([0-9]+)\Z', name)
    if m and 1 <= int(m.group(1)) <= 10:
        return Tab(name, (int(m.group(1)),), 12, False)


def fixed(*kinds):
    return lambda a: kinds[len(a)] if len(a) < len(kinds) else None


def lut_shape(a):
    return 'tab' if not a else ('ref' if len(a) < len(a[0].ins) + 2 else None)


def table_shape(a):
    if len(a) < 2:
        return ('num:1:10', 'num:1:64')[len(a)]
    return 'tval' if len(a) < 2 + (1 << a[0]) else None


class Parser:
    def __init__(self, text, level):
        self.level, self.errors, self.steps = level, [], []
        self.toks = list(tokens(text))
        self.defined = {t.text[1:] for t in self.toks if t.text[0] == ':'}
        self.labels, self.pending, self.cur = {'zero': Lab('data', 1, None, None)}, None, None   # cur: [name, word, ended]
        self.touched, self.recs, self.uses = set(), set(), []      # words used (rec must come first)

    def err(self, t, msg):
        self.errors.append('%d:%d: %s' % (t.line, t.col, msg))

    # --- arguments
    def arg(self, kind, t, args):
        s = t.text
        k = kind.split(':')
        if k[0] == 'num':
            v = number(s)
            if v is None or not int(k[1]) <= v <= int(k[2] if len(k) > 2 else 1 << 64):
                return None, 'a number %s..%s expected, found %s' % (k[1] if len(k) > 1 else 0, k[2] if len(k) > 2 else '', s)
            return v, None
        if k[0] in ('val', 'tval'):
            return self.value(k[0], t, args)
        if k[0] == 'wid':
            if s == 'link':
                return 0, None
            return self.arg('num:1:64', t, args)
        m = REF.match(s)
        if not m:
            return None, 'a reference &name expected, found %s' % s
        name = m.group(1)
        lab = self.labels.get(name) or (Lab('table', 0, builtin(name), None) if builtin(name) else None)
        if k[0] in ('blk', 'wrd'):
            if m.group(2):
                return None, 'a label of a block expected, found %s' % s
            self.uses.append((name, k[0], t))
            return name, None
        if lab is None:
            return None, ('label &%s is defined after its use (data and tables first)' if name in self.defined
                          else 'undefined label &%s') % name
        if k[0] == 'ref':
            if lab.kind != 'data':
                return None, '&%s is a %s, not a part of space' % (name, lab.kind)
            lo = int(m.group(2) or 0)
            hi = int(m.group(3)) if m.group(3) else (lo + 1 if m.group(2) else lab.bits)
            if not 0 <= lo < hi <= lab.bits:
                return None, 'part [%d:%d] is outside &%s (%d bits)' % (lo, hi, name, lab.bits)
            return Rf(name, lo, hi), None
        if m.group(2) or lab.kind not in (('table', 'array') if k[0] == 'tab' else ('stack',)):
            return None, '&%s is a %s, not a %s' % (name, lab.kind, 'table' if k[0] == 'tab' else 'stack')
        return (lab.tab if k[0] == 'tab' else (name, lab.stk)), None

    def value(self, kind, t, args):
        s = t.text
        bits = args[0] if kind == 'val' else args[1]
        if s[0] in '"\'':
            body = unescape(s[1:-1]) if len(s) >= 2 and s[-1] == s[0] else None
            if body is None:
                return None, 'a bad string or character %s' % s
            if s[0] == "'":
                if len(body) != 1 or kind == 'val' or bits != 8:
                    return None, "a character 'c' is a value of a table of 8-bit entries"
                return rev(body[0], 8), None
            if kind == 'val' and 8 * len(body) > bits or kind == 'tval' and 8 * len(body) != bits:
                return None, 'a string of %d bytes does not fit %d bits' % (len(body), bits)
            return bytes_value(body), None
        v = number(s)
        if v is None or v >> bits:
            return None, 'a number below 2^%d expected, found %s' % (bits, s)
        return v, None

    # --- the text
    def run(self):
        toks, i, n = self.toks, 0, len(self.toks)
        while i < n:
            t = toks[i]; i += 1
            if t.text[0] == ':':
                if not NAME.match(t.text[1:]):
                    self.err(t, 'a bad label %s' % t.text)
                elif self.pending:
                    self.err(self.pending, 'label %s is followed by another label' % self.pending.text)
                    self.pending = t
                else:
                    self.pending = t
                continue
            w = WORDS.get(t.text)
            if not wordlike(t) or w is None or w[0] > self.level:
                self.pending = None
                self.err(t, ('unknown word %s (in language %d)' % (t.text, self.level)) if wordlike(t)
                         else 'unexpected %s (an extra argument, or a word is missing)' % t.text)
                while i < n and not wordlike(toks[i]):
                    i += 1
                continue
            args, ok = [], True
            while True:
                kind = w[1](args)
                if kind is None:
                    break
                if i >= n or wordlike(toks[i]) and not (kind == 'wid' and toks[i].text == 'link'):
                    self.err(t, 'missing argument %d of %s (%s expected)' % (len(args) + 1, t.text, kind.split(':')[0]))
                    ok = False
                    break
                a, e = self.arg(kind, toks[i], args)
                if e:
                    self.err(toks[i], e)
                    ok = False
                    break
                args.append(a); i += 1
            if ok and i < n and not wordlike(toks[i]):
                self.err(toks[i], 'extra argument of %s' % t.text)
                ok = False
            while i < n and not wordlike(toks[i]):
                i += 1
            if ok:
                w[2](self, t, args)
            elif self.pending:
                self.pending = None
        self.finish()

    def finish(self):
        if self.pending:
            self.err(self.pending, 'label %s has no word after it' % self.pending.text)
        if self.cur and not self.cur[2]:
            self.errors.append('end: block %s has no end (goto, if, call, ret or halt)' % self.cur[0])
        for name, kind, t in self.uses:
            lab = self.labels.get(name)
            if lab is None:
                self.err(t, 'undefined label &%s' % name)
            elif lab.kind not in (('word',) if kind == 'wrd' else ('block', 'word')):
                self.err(t, '&%s is a %s, not a %s' % (name, lab.kind, 'word' if kind == 'wrd' else 'block'))
        if self.level >= 3 and not any(lab.kind in ('block', 'word') for lab in self.labels.values()):
            self.errors.append('end: the program has no block')

    # --- helpers of the words
    def define(self, t, kind, bits=0, tab=None, stk=None):
        """tab, stk: functions of the name."""
        """The label before the word (every defining word needs one)."""
        lab, self.pending = self.pending, None
        if lab is None:
            self.err(t, '%s needs a label (:name before it)' % t.text)
            return None
        name = lab.text[1:]
        if name in self.labels or builtin(name) or RESERVED.match(name):
            self.err(lab, 'label %s is %s' % (lab.text, 'reserved' if RESERVED.match(name) else 'repeated'))
            return None
        self.labels[name] = Lab(kind, bits, tab and tab(name), stk and stk(name))
        return name

    def plain(self, t):
        """A word which defines nothing must have no label before it."""
        if self.pending:
            self.err(self.pending, 'label %s is before %s, which defines nothing' % (self.pending.text, t.text))
            self.pending = None

    def inblock(self, t):
        self.plain(t)
        if self.level < 3:                       # the words of language 2 alone: the grammar, no blocks
            return True
        if self.cur is None or self.cur[2]:
            self.err(t, '%s %s' % (t.text, 'outside a block (:name block before it)' if self.cur is None
                                   else 'after the end of the block %s' % self.cur[0]))
            return False
        return True

    def write(self, t, r):
        if r.name == 'zero':
            self.err(t, 'zero is read-only')

    def width(self, t, r, n, what):
        if r.hi - r.lo != n:
            self.err(t, '%s: %d bits expected, found %d' % (what, n, r.hi - r.lo))

    def enter(self, t, word):
        name = self.define(t, 'word' if word else 'block')
        if self.cur and not self.cur[2]:
            self.err(t, 'block %s has no end (goto, if, call, ret or halt)' % self.cur[0])
        if name:
            self.cur = [name, name if word else (self.cur[1] if self.cur else None), False]
        return name


def R(r):
    return lambda e: e[r.name][r.lo:r.hi]


def table_of(tab):
    """The table for lut and store: a user table or array (made by its word), or one the compiler knows."""
    if builtin(tab.name):
        return lambda p, e: {'add4': p.t_add, 'sub4': p.t_sub, 'hex4': p.t_hex}.get(tab.name, lambda: p.t_dec(tab.ins[0]))()
    return lambda p, e: e[tab.name]


# --- the words: (level, the kind of the next argument, the meaning)

def w_data(c, t, a):
    name = c.define(t, 'data', a[0])
    if name:
        c.steps.append(lambda p, e: e.__setitem__(name, p.var(name, a[0], a[1])))


def w_table(c, t, a):
    name = c.define(t, 'table', tab=lambda n: Tab(n, (a[0],), a[1], False))
    if name:
        vals = a[2:]
        c.steps.append(lambda p, e: e.__setitem__(name, p.table(name, (a[0],), a[1], lambda x: vals[x])))


def w_array(c, t, a):
    name = c.define(t, 'array', tab=lambda n: Tab(n, (a[0],), a[1], True))
    if name:
        c.steps.append(lambda p, e: e.__setitem__(name, p.array(name, (a[0],), a[1])))


def w_stack(c, t, a):
    name = c.define(t, 'stack', stk=lambda n: Stk(*a))
    if name:
        c.steps.append(lambda p, e: e.__setitem__(name, p.stack(name, a[0], a[1] or 2 * p.A)))


def w_copy(c, t, a):
    if c.inblock(t):
        d, s = a
        c.width(t, s, d.hi - d.lo, 'copy')
        c.write(t, d)
        if d.name == s.name and d.lo < s.hi and s.lo < d.hi:
            c.err(t, 'copy of a part of space onto itself')
        c.steps.append(lambda p, e: p.copy(R(d)(e), R(s)(e)))


def w_emit(c, t, a):
    if c.inblock(t):
        c.steps.append(lambda p, e: p.emit(R(a[0])(e)))


def w_warn(c, t, a):
    if c.inblock(t):
        c.steps.append(lambda p, e: p.warn(R(a[0])(e)))


def w_key(c, t, a):
    if c.inblock(t):
        c.write(t, a[0])
        if (a[0].hi - a[0].lo) % 8:
            c.err(t, 'key: stdin gives whole bytes, found %d bits' % (a[0].hi - a[0].lo))
        c.steps.append(lambda p, e: p.key(R(a[0])(e)))


def w_lut(c, t, a):
    if c.inblock(t):
        T, args, out = a[0], a[1:-1], a[-1]
        for k, (x, n) in enumerate(zip(args, T.ins, strict=True)):
            c.width(t, x, n, 'lut %s, argument %d' % (T.name, k + 1))
        c.width(t, out, T.out, 'lut %s, result' % T.name)
        c.write(t, out)
        get = table_of(T)
        c.steps.append(lambda p, e: p.lut(get(p, e), [R(x)(e) for x in args], R(out)(e)))


def w_store(c, t, a):
    if c.inblock(t):
        T, args, src = a[0], a[1:-1], a[-1]
        if not T.array:
            c.err(t, 'store: &%s is a table, not an array' % T.name)
        for k, (x, n) in enumerate(zip(args, T.ins, strict=True)):
            c.width(t, x, n, 'store %s, index %d' % (T.name, k + 1))
        c.width(t, src, T.out, 'store %s, value' % T.name)
        c.steps.append(lambda p, e: p.store(e[T.name], [R(x)(e) for x in args], R(src)(e)))


def w_block(c, t, a):
    name = c.enter(t, False)
    if name:
        c.steps.append(lambda p, e: p.block(name))


def w_word(c, t, a):
    name = c.enter(t, True)
    if name:
        c.touched.add(name)
        c.steps.append(lambda p, e: p.word(name))


def end(c, t):
    c.cur[2] = True


def w_goto(c, t, a):
    if c.inblock(t):
        end(c, t)
        c.steps.append(lambda p, e: p.goto(a[0]))


def w_halt(c, t, a):
    if c.inblock(t):
        end(c, t)
        c.steps.append(lambda p, e: p.halt())


def w_ret(c, t, a):
    if c.inblock(t):
        if c.cur[1] is None:
            c.err(t, 'ret outside a word')
        end(c, t)
        c.steps.append(lambda p, e: p.ret())


def w_if(c, t, a):
    if c.inblock(t):
        c.width(t, a[0], 1, 'if: the condition')
        end(c, t)
        c.steps.append(lambda p, e: p.if_(R(a[0])(e), a[1], a[2]))


def w_call(c, t, a):
    if c.inblock(t):
        c.touched.add(a[0])
        end(c, t)
        c.steps.append(lambda p, e: p.call(a[0], a[1]))


def w_rec(c, t, a):
    c.plain(t)
    word, (sname, stk) = a
    if stk.w:
        c.err(t, 'rec: &%s is not a stack of links (stack K link)' % sname)
    if word in c.touched or word in c.recs:
        c.err(t, 'rec: the word %s is used before this rec' % word)
    c.recs.add(word)
    c.steps.append(lambda p, e: p.rec(word, e[sname]))


def w_push(c, t, a):
    if c.inblock(t):
        (sname, stk), r = a
        if not stk.w:
            c.err(t, '%s: &%s is a stack of links, used by rec only' % (t.text, sname))
        else:
            c.width(t, r, stk.w, '%s &%s' % (t.text, sname))
        if t.text == 'pop':
            c.write(t, r)
        c.steps.append(lambda p, e: (p.push if t.text == 'push' else p.pop)(e[sname], R(r)(e)))


def lib(op):
    """add sub band lt eq: widths in nibbles, as the library demands; the result has its own size."""
    def f(c, t, a):
        if c.inblock(t):
            x, y, r = a
            n = x.hi - x.lo
            if n % 4:
                c.err(t, '%s: a number of whole nibbles expected, found %d bits' % (op, n))
            c.width(t, y, n, op + ', the second operand')
            want = {'add': n + 1, 'sub': n + 1, 'band': n, 'eq': n // 4}.get(op)
            if op == 'lt':
                if r.hi - r.lo < n // 4 + 1:
                    c.err(t, 'lt: the result needs %d bits, found %d' % (n // 4 + 1, r.hi - r.lo))
            else:
                c.width(t, r, want, op + ', the result')
            c.write(t, r)
            c.steps.append(lambda p, e: getattr(p, op)(R(x)(e), R(y)(e), R(r)(e)))
    return f


def w_shift(c, t, a):
    if c.inblock(t):
        x, r, k = a
        c.width(t, r, x.hi - x.lo, t.text)
        c.write(t, r)
        if x.name == r.name:
            c.err(t, '%s: the result must be another part of space' % t.text)
        c.steps.append(lambda p, e: getattr(p, t.text)(R(x)(e), R(r)(e), k))


def w_long(c, t, a):
    if c.inblock(t):
        pos, d = a
        c.width(t, pos, 128, '%s: the position' % t.text)
        if not 0 < d.hi - d.lo < 1 << 32:
            c.err(t, '%s: the length is 1..2^32-1 bits' % t.text)
        if t.text == 'long@':
            c.write(t, d)
        c.steps.append(lambda p, e: (p.long_put if t.text == 'long!' else p.long_get)(R(pos)(e), R(d)(e)))


WORDS = {
    'data': (2, fixed('num:1:65536', 'val'), w_data),
    'copy': (2, fixed('ref', 'ref'), w_copy),
    'shl': (2, fixed('ref', 'ref', 'num:0:65536'), w_shift),
    'shr': (2, fixed('ref', 'ref', 'num:0:65536'), w_shift),
    'table': (3, table_shape, w_table),
    'array': (3, fixed('num:1:10', 'num:1:64'), w_array),
    'lut': (3, lut_shape, w_lut),
    'store': (3, lut_shape, w_store),
    'block': (3, fixed(), w_block),
    'word': (3, fixed(), w_word),
    'goto': (3, fixed('blk'), w_goto),
    'if': (3, fixed('ref', 'blk', 'blk'), w_if),
    'call': (3, fixed('wrd', 'blk'), w_call),
    'ret': (3, fixed(), w_ret),
    'halt': (3, fixed(), w_halt),
    'emit': (3, fixed('ref'), w_emit),
    'warn': (3, fixed('ref'), w_warn),
    'key': (3, fixed('ref'), w_key),
    'stack': (3, fixed('num:1:8', 'wid'), w_stack),
    'push': (3, fixed('stk', 'ref'), w_push),
    'pop': (3, fixed('stk', 'ref'), w_push),
    'rec': (3, fixed('wrd', 'stk'), w_rec),
    'long!': (4, fixed('ref', 'ref'), w_long),
    'long@': (4, fixed('ref', 'ref'), w_long),
}
for _op in ('add', 'sub', 'band', 'lt', 'eq'):
    WORDS[_op] = (3, fixed('ref', 'ref', 'ref'), lib(_op))


class Parsed:
    def __init__(self, c):
        self.errors, self.steps = c.errors, c.steps

    def build(self, p):
        """The calls of the constructors of the program p (a l3.Program); cannot fail for an accepted text."""
        env = {'zero': p.zero}
        for s in self.steps:
            s(p, env)


def parse(text, level=4):
    """Read the text with the words of language `level` (2..4): Parsed with .errors (empty when accepted)."""
    c = Parser(text, level)
    c.run()
    return Parsed(c)


def compile_text(text, level=4):
    """(program, errors): the program of l3 (laid out in the smallest A) or None with the messages."""
    r = parse(text, level)
    if level < 3 and not r.errors:
        return None, ['end: a text of language %d has no block, there is nothing to run' % level]
    if r.errors:
        return None, r.errors
    try:
        return l3.compile_program(r.build), []
    except MemoryError as e:
        return None, ['end: the program does not fit (%s)' % e]


def main():
    level = 4
    if sys.argv[1:2] == ['-l']:
        level = int(sys.argv[2])
    p, errors = compile_text(sys.stdin.read(), level)
    if errors:
        sys.stderr.write('\n'.join(errors) + '\n')
        sys.exit(1)
    st = p.stats
    sys.stderr.write('A=%d P=%d image %d bytes\n' % (st['A'], st['P'], len(st['image'])))
    sys.stdout.buffer.write(st['image'])


if __name__ == '__main__':
    main()
