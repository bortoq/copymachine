"""The text of language 2 with long labels (host, Python, temporary): what the label tool `programs/l2l.tw` reads, and the Python
reference of it. It is the text of language 2 (l2text.py: `w r z s # c d o` and numbers) with names of any length up to 15 bytes
and references forward, as hex2 of stage0 after the labels of one letter:
  :name      a label: the position (bit) where the text stands now; the name is bytes a-z 0-9 _ (1 to 15 of them) and ends at a
             blank or a line break; after it the line goes on (`:a d 8 5`). A label is defined once
  &name      a number: the position of the label, defined before or after (forward); &name+k with a hex k adds k (mod 2^20)
Everything else is as in l2text.py (the origin `o`, numbers of at most 5 hex digits, positions count the bits of the image text).
Two passes. The chain reads stdin once, so the text is given twice: stdin is `text 0 text 0`, the first copy only defines the
labels (nothing goes out; a name not yet defined counts as 0), the second goes out as the text of language 1 and a zero byte.
At a label the second copy must give the position of the first (the table is in the image: 1024 names, 15 bytes each, 20 bits
for the position); a name defined in one copy and not in the other, or at another position, is `bad label`. With one copy only
(`text 0`) the second text is empty: the output is the zero byte alone.
Errors (stderr, halt, the output is cut where the error is; in the first copy nothing has gone out yet): `l2l: bad text` (an
unknown command or a wrong character, an empty name or a name over 15 bytes), `l2l: bad count`, `l2l: bad label` (a label
repeated, a name not defined, a label at another place in the second copy, the 1025th label). Not checked, but defined: numbers
over 5 digits, w z d over ff, the content of r s # lines.
Run: python3 tower/l2ltext.py -e < prog.l2 > prog.l1z   (the reference: it doubles the text itself, as `cat t t` does)"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import l2text
from l2text import ATTR, CODES, HEX, M, attr, rev8, table_lines   # noqa: F401  (the tables of l2c.tw are the same)

MESSAGES = {'bad': 'l2l: bad text\n', 'cnt': 'l2l: bad count\n', 'lab': 'l2l: bad label\n'}
NAME = frozenset(b'abcdefghijklmnopqrstuvwxyz0123456789_')
MAXLAB = 1024


def cls(c):
    """The class of a byte (14 bits), as l2text.cls, but bit 12 is a name byte (a-z 0-9 _), not a lowercase letter."""
    v = l2text.cls(c) & ~(1 << 12)
    return v | ((1 << 12) if c in NAME else 0)


def cls_table():
    return table_lines(lambda i: cls(rev8(i)), 8)


def split(data):
    """stdin -> (the first copy, the second copy), each with its zero byte. The chain reads up to the first zero, then up to the
    next; the stdin repeats its last byte, so a missing second copy is an empty text."""
    data = bytes(data)
    if 0 not in data:
        data += b'\0'
    i = data.index(0)
    rest = data[i + 1:]
    if 0 not in rest:
        rest = rest + b'\0'
    return data[:i + 1], rest[:rest.index(0) + 1]


def one_pass(data, labels, second, out):
    """One pass over a text (with its zero byte). Returns None, or the error ('bad', 'cnt', 'lab'). labels: {name: position}."""
    st = dict(echo=0, inN=0, inK=0, isS=0, inLab=0, amp=0, lbl=0, dig=0, V=0, W=0, need=0, cmd=0)
    X, pos, RB, name = [0, 0, 0], 0, 0, b''

    def endline():
        for k in ('echo', 'inN', 'inK', 'isS'):
            st[k] = 0

    def find():
        """The name in hand: checked, looked up. Returns (found, position) or the error."""
        if not name or len(name) > 15:
            return 'bad'
        return name in labels, labels.get(name, 0)

    def action():
        nonlocal pos, RB
        n, d, s = X
        cmd = st['cmd']
        if cmd == 1:
            RB = (X[2] & 255) << 2
        elif cmd == 3:
            pos = (pos + (X[2] & 255)) & M
        elif cmd == 6:
            if second:
                out.extend(('r %x %x %x %x\n' % (d, (d + n) & M, s, (s + n) & M)).encode())
            pos = (pos + RB) & M
        elif cmd == 7:
            k, v = X[1] & 255, X[2]
            if second:
                out.extend(b's ' + bytes(48 + (v >> i & 1 if i < 20 else 0) for i in range(k)) + b'\n')
            pos = (pos + k) & M
        elif cmd == 8:
            pos = 0

    for c in data:
        ch = chr(c)
        nul, nl, sep = c == 0, ch in '\n\0', ch in ' \t\r\n\0'
        hexd = ch in HEX
        if st['echo'] and not nul and second:
            out.append(c)
        if st['inN']:
            if st['amp']:
                if c in NAME:
                    name += bytes([c])
                    continue
                f = find()
                if f == 'bad':
                    return 'bad'
                found, val = f
                if not found and second:
                    return 'lab'
                st['V'], st['amp'], st['lbl'], name = val, 0, 1, b''
            if hexd:
                if st['lbl']:
                    return 'bad'
                st['W'] = (st['W'] << 4 | HEX.index(ch)) & M
                st['dig'] = 1
                continue
            if sep:
                if st['lbl'] or st['dig']:
                    if st['need'] == 0:
                        return 'cnt'
                    X[:] = [X[1], X[2], (st['V'] + st['W']) & M]
                    st.update(need=st['need'] - 1, V=0, W=0, lbl=0, dig=0)
                if nl:
                    if st['need']:
                        return 'cnt'
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
            return 'bad'
        if st['inK']:
            if st['isS'] and ch in '01':
                pos = (pos + 1) & M
            if nl:
                endline()
                if nul:
                    break
            continue
        if st['inLab']:
            if c in NAME:
                name += bytes([c])
                continue
            f = find()
            if f == 'bad':
                return 'bad'
            found, val = f
            if second:
                if not found or val != pos:
                    return 'lab'
            elif found or len(labels) >= MAXLAB:
                return 'lab'
            else:
                labels[name] = pos
            st['inLab'], name = 0, b''
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
                return 'bad'
            need, echo, num, skip, bits, _, row, _l = ATTR[code]
            st.update(need=need, echo=echo, inN=num, inK=skip, isS=bits, cmd=code)
            if echo and second:
                out.append(c)
            if row:
                pos = (pos + RB) & M
    return None


def encode(src, twice=False):
    """The reference of the tool: (bytes, error or None). src is the stdin (two copies of the text, see split); with twice=True
    src is one text and it is doubled here. The bytes are cut at the error; a good text ends with a zero byte."""
    data = bytes(src) if isinstance(src, (bytes, bytearray)) else src.encode('latin-1')
    if twice:
        data = data.rstrip(b'\0')
        data = data + b'\0' + data + b'\0'
    first, second = split(data)
    labels, out = {}, bytearray()
    err = one_pass(first, labels, False, out) or one_pass(second, labels, True, out)
    if err:
        return bytes(out), err
    out.append(0)
    return bytes(out), None


def main():
    image, err = encode(sys.stdin.buffer.read(), twice=True)
    sys.stdout.buffer.write(image)
    if err:
        sys.stderr.write(MESSAGES[err])
        sys.exit(1)


if __name__ == '__main__':
    if sys.argv[1:2] == ['-e']:
        main()
    else:
        sys.stderr.write(__doc__.splitlines()[-1] + '\n')
        sys.exit(2)
