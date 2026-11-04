"""The text of language 2 (host, Python, temporary): what the compiler of language 2 `programs/l2c.tw` reads, and the Python
reference of it. Language 2 is language 1 (its lines `w r z s #` are the same) with two more words, `copy` and `data`,
and the names of parts of space. The text is lines; a line starts with a command letter (blanks before it are free):
  c n d s    copy: n bits from s to d; the compiler writes the row `r d d+n s s+n` (language 1: four fields, here three)
  d n v      data: n bits (hex, at most ff) of the number v, the least significant bit first, bits over 20 are zero
  :x         a label: x is the position (bit) where the text stands now, counted from the start of the text, x is a
             lowercase letter; after it the line goes on (`:a d 8 5`). A label is defined once
  o          the origin: the position is 0 from here on (the bits before it are not in space: the boot packet)
  w r z s #  as in language 1 (l1text.py); they go out as they stand, the compiler only counts their bits
A number is hex (at most 5 digits, the older fall out; the sums are modulo 2^20), or `&x` (the position of the label x, it
must be defined before), or `&x+k` (the position and a hex k). Every number of c, d, w, z is so. Positions count the bits of
the image text in the order it goes out: a row is 4A bits (A is the last `w`), `z N` N bits, `s` its 0 and 1 characters, `d n`
n bits. What is not language 2 stays language 1: the rows of the channels (stdin, stdout, stderr: the destination and the source
differ in length) and the boot row are written as `r`.
Not checked, but defined (the lower language tells it): the content of r, s and # lines, a number over 5 digits, w z d over ff.
A wrong text is reported to stderr and the compiler halts (7.2.28), the output is cut at that place: `l2: bad text` (an unknown
command or a wrong character), `l2: bad count` (a wrong number of numbers in a line), `l2: bad label` (a label repeated, or used
before it is defined). A good text goes out as the text of language 1 and a zero byte (what the seed reads).
Run: python3 tower/l2text.py -e < prog.l2 > prog.l1z   (the reference compiler; the chain does the same on the emulator)
     python3 tower/l2text.py prog.l1 > prog.l2         (text of language 1 -> text of language 2: copy rows become c lines)"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

M = (1 << 20) - 1
HEX = '0123456789abcdef'
CODES = {'w': 1, 'r': 2, 'z': 3, 's': 4, '#': 5, 'c': 6, 'd': 7, 'o': 8, ':': 9}
# per command code: need (numbers), echo, numeric line, skipping line, bits line, valid, row line, label
ATTR = {1: (1, 1, 1, 0, 0, 1, 0, 0), 2: (0, 1, 0, 1, 0, 1, 1, 0), 3: (1, 1, 1, 0, 0, 1, 0, 0), 4: (0, 1, 0, 1, 1, 1, 0, 0),
        5: (0, 1, 0, 1, 0, 1, 0, 0), 6: (3, 0, 1, 0, 0, 1, 0, 0), 7: (2, 0, 1, 0, 0, 1, 0, 0), 8: (0, 0, 1, 0, 0, 1, 0, 0),
        9: (0, 0, 0, 0, 0, 1, 0, 1)}
ATTR_BITS = (6, 4, 5, 8, 9, 10, 11)         # the bit of: echo, numeric, skipping, bits, valid, row, label
MESSAGES = {'bad': 'l2: bad text\n', 'cnt': 'l2: bad count\n', 'lab': 'l2: bad label\n'}


def rev8(c):
    return int(format(c, '08b')[::-1], 2)


def cls(c):
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


def cls_table():
    """The table cls: the index is the number with the first bit of the byte the lowest, so a byte c stands at rev8(c)."""
    return table_lines(lambda i: cls(rev8(i)), 8)


def encode(src):
    """The reference of the compiler: (bytes, error or None). The error is 'bad', 'cnt' or 'lab' (the messages of the
    chain are MESSAGES); the bytes are cut at the place of the error; a good text ends with a zero byte."""
    out = bytearray()
    st = dict(echo=0, inN=0, inK=0, isS=0, inLab=0, amp=0, lbl=0, dig=0, V=0, W=0, need=0, cmd=0)
    X, lab, pos, RB = [0, 0, 0], {}, 0, 0
    data = bytes(src) if isinstance(src, (bytes, bytearray)) else src.encode('latin-1')
    if 0 not in data:
        data += b'\0'

    def bad(why):
        return bytes(out), why

    def endline():
        for k in ('echo', 'inN', 'inK', 'isS'):
            st[k] = 0

    def action():
        nonlocal pos, RB
        n, d, s = X
        cmd = st['cmd']
        if cmd == 1:
            RB = (X[2] & 255) << 2
        elif cmd == 3:
            pos = (pos + (X[2] & 255)) & M
        elif cmd == 6:
            out.extend(('r %x %x %x %x\n' % (d, (d + n) & M, s, (s + n) & M)).encode())
            pos = (pos + RB) & M
        elif cmd == 7:
            k, v = X[1] & 255, X[2]
            out.extend(b's ' + bytes(48 + (v >> i & 1 if i < 20 else 0) for i in range(k)) + b'\n')
            pos = (pos + k) & M
        elif cmd == 8:
            pos = 0

    for c in data:
        ch = chr(c)
        nul, nl, sep = c == 0, ch in '\n\0', ch in ' \t\r\n\0'
        hexd = ch in HEX
        low = 'a' <= ch <= 'z'
        if st['echo'] and not nul:
            out.append(c)
        if st['inN']:
            if st['amp']:
                if not low:
                    return bad('bad')
                if c not in lab:
                    return bad('lab')
                st['V'], st['amp'], st['lbl'] = lab[c], 0, 1
                continue
            if hexd:
                if st['lbl']:
                    return bad('bad')
                st['W'] = (st['W'] << 4 | HEX.index(ch)) & M
                st['dig'] = 1
                continue
            if sep:
                if st['amp']:
                    return bad('bad')
                if st['lbl'] or st['dig']:
                    if st['need'] == 0:
                        return bad('cnt')
                    X[:] = [X[1], X[2], (st['V'] + st['W']) & M]
                    st.update(need=st['need'] - 1, V=0, W=0, lbl=0, dig=0)
                if nl:
                    if st['need']:
                        return bad('cnt')
                    action()
                    endline()
                    if nul:
                        break
                continue
            if ch == '+' and st['lbl']:
                st['lbl'], st['dig'] = 0, 1
                continue
            if ch == '&' and not (st['lbl'] or st['dig']):
                st['amp'] = 1
                continue
            return bad('bad')
        if st['inK']:
            if st['isS'] and ch in '01':
                pos = (pos + 1) & M
            if nl:
                endline()
                if nul:
                    break
            continue
        if st['inLab']:
            if not low:
                return bad('bad')
            if c in lab:
                return bad('lab')
            lab[c], st['inLab'] = pos, 0
            continue
        if nl:
            endline()
            if nul:
                break
        elif sep:
            pass
        elif ch == ':':
            st['inLab'] = 1
        else:
            code = CODES.get(ch, 0)
            if not code:
                return bad('bad')
            need, echo, num, skip, bits, _, row, _l = ATTR[code]
            st.update(need=need, echo=echo, inN=num, inK=skip, isS=bits, cmd=code)
            if echo:
                out.append(c)
            if row:
                pos = (pos + RB) & M
    out.append(0)
    return bytes(out), None


def to_l2(text):
    """The text of language 1 -> the text of language 2: a row whose destination and source have the same length n > 0
    becomes `c n d s` (the other lines stay)."""
    out = []
    for line in text.splitlines():
        p = line.split()
        if len(p) == 5 and p[0] == 'r':
            d0, d1, s0, s1 = (int(x, 16) for x in p[1:])
            if d1 - d0 == s1 - s0 > 0:
                line = 'c %x %x %x' % (d1 - d0, d0, s0)
        out.append(line)
    return '\n'.join(out) + '\n'


def main():
    if sys.argv[1:2] == ['-e']:
        image, err = encode(sys.stdin.buffer.read())
        sys.stdout.buffer.write(image)
        if err:
            sys.stderr.write(MESSAGES[err])
            sys.exit(1)
        return
    with open(sys.argv[1], encoding='utf-8') as h:
        sys.stdout.write(to_l2(h.read()))


if __name__ == '__main__':
    main()
