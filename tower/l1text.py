"""The text of language 1 (host, Python, temporary): what the seed encoder `programs/seed.tw` reads, and the Python
reference of it. The text is lines, a line starts with a command letter (blanks before it are free):
  w N        the width A of a field of a row, bits (hex, at most ff)
  r a b c d  a row dl dh sl sh: four hex numbers, each is written as A bits, the least significant bit first
  z N        N zero bits (hex, at most ff)
  s 0101     raw bits in the order of memory (the first is the 0x80 bit of a byte); blanks between them are free
  # ...      a comment (the layers and the named parts of space are marked so)
The image is the bits in the order of the text; the text ends with a zero byte. Nothing else is in the text:
no addresses (a layer is at the place where its rows stand), no names. A wrong text is reported and cut at that place
(an unknown command or a wrong character, a wrong number of numbers, a row before w, bits which are not whole bytes).
Not checked, but defined: a number over 5 digits (the older digits fall out), a value over A bits (dropped), w and z
over ff (modulo 256).
Run: python3 tower/l1text.py prog.tw > prog.l1     (the program of language 3 and up -> the text of its image)
     python3 tower/l1text.py -e < prog.l1 > image  (the reference encoder; the seed does the same on the emulator)"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import text

LETTERS = {'w': 1, 'r': 2, 'z': 3, 's': 4, '#': 5}
HEX = '0123456789abcdef'
ZRUN = 16                       # a run of zeros which is at least so long goes as `z`


def encode(src):
    """The reference of the seed: (image bytes, error or None). The error is 'bad', 'cnt' or 'end' (as the messages of
    the seed: `l1: bad text`, `l1: bad count`, `l1: bad end byte`); the image is cut at the place of the error."""
    out, acc, ctr = bytearray(), 0, 0
    st = dict(S=0, C=0, N=0, R=0, Z=0, num=0, na=0, need=1, V=0, A=0)

    def put(bit):
        nonlocal acc, ctr
        acc = acc << 1 | bit
        ctr += 1
        if ctr == 8:
            out.append(acc)
            acc, ctr = 0, 0

    def line_end(c):
        st['S'] = st['C'] = st['N'] = 0
        if c == 0:
            return None if ctr == 0 else 'end'
        return False

    data = bytes(src) if isinstance(src, (bytes, bytearray)) else src.encode('latin-1')
    if 0 not in data:
        data += b'\0'
    for c in data:
        ch = chr(c)
        hexd = ch in HEX
        sep, nl = ch in ' \t\r\n\0', ch in '\n\0'
        val = HEX.index(ch) if hexd else (6 if c == 0 else LETTERS.get(ch, 0))
        r = False
        if st['S']:
            if ch in '01':
                put(val)
            elif nl:
                r = line_end(c)
            elif not sep:
                return bytes(out), 'bad'
        elif st['C']:
            if nl:
                r = line_end(c)
        elif st['N']:
            if hexd:
                st['V'] = (st['V'] << 4 | val) & 0xfffff
                st['num'] = 1
            elif not sep:
                return bytes(out), 'bad'
            else:
                if st['num']:
                    if st['na'] == st['need']:
                        return bytes(out), 'cnt'
                    st['num'] = 0
                    st['na'] = (st['na'] + 1) & 15
                    V = st['V']
                    if st['R']:
                        for i in range(st['A']):
                            put(V >> i & 1 if i < 20 else 0)
                    elif st['Z']:
                        for _ in range(V & 255):
                            put(0)
                    else:
                        st['A'] = V & 255
                    st['V'] = 0
                if nl:
                    if st['na'] != st['need']:
                        return bytes(out), 'cnt'
                    r = line_end(c)
        else:                                       # the start of a line
            if nl:
                r = line_end(c)
            elif sep:
                pass
            elif hexd or val == 0 or val == 6:
                return bytes(out), 'bad'
            elif val == 4:
                st['S'] = 1
            elif val == 5:
                st['C'] = 1
            elif val == 2 and st['A'] == 0:
                return bytes(out), 'bad'
            elif val in (1, 2, 3):
                st.update(R=int(val == 2), Z=int(val == 3), need=4 if val == 2 else 1, N=1, na=0, num=0)
        if r == 'end':
            return bytes(out), 'end'
        if r is None:
            return bytes(out), None
    return bytes(out), 'bad'


MESSAGES = {'bad': 'l1: bad text\n', 'cnt': 'l1: bad count\n', 'end': 'l1: bad end byte\n'}


def to_bits(image):
    return ''.join(format(b, '08b') for b in image)


def bits_lines(bits):
    """Raw bits as `s` lines: 64 bits in a line, eight groups of eight."""
    for i in range(0, len(bits), 64):
        part = bits[i:i + 64]
        yield 's ' + ' '.join(part[k:k + 8] for k in range(0, len(part), 8))


def data_lines(bits):
    """Bits which are not rows: long runs of zeros as `z`, the rest as `s`."""
    i, n, pend = 0, len(bits), ''
    while i < n:
        j = i
        while j < n and bits[j] == '0':
            j += 1
        if j - i >= ZRUN or (j == n and j - i):
            yield from bits_lines(pend)
            pend = ''
            for k in range(i, j, 255):
                yield 'z %x' % min(255, j - k)
            i = j
        else:
            k = j
            while k < n and bits[k] == '1':
                k += 1
            pend += bits[i:k]
            i = k
    yield from bits_lines(pend)


def dump(image, A, rows, marks=None, title=''):
    """The text of an image. rows: positions (bit) where rows of 4A bits start; marks: {position: comment}."""
    bits, RB = to_bits(image), 4 * A
    rows = sorted(r for r in set(rows) if r + RB <= len(bits))
    marks = marks or {}
    lines = ['# ' + title, 'w %x' % A] if title else ['w %x' % A]
    cuts = sorted(set(rows) | {p for p in marks if p < len(bits)} | {len(bits)})
    pos, rowset = 0, set(rows)
    while pos < len(bits):
        for m in marks.get(pos, ()):
            lines.append('# ' + m)
        if pos in rowset:
            f = [int(bits[pos + k * A:pos + (k + 1) * A][::-1], 2) for k in range(4)]
            lines.append('r %x %x %x %x' % tuple(f))
            pos += RB
            continue
        nxt = min(c for c in cuts if c > pos)
        lines.extend(data_lines(bits[pos:nxt]))     # a piece of data ends at a row, a mark or the end
        pos = nxt
    return '\n'.join(lines) + '\n'


def program_text(p, title=''):
    """The text of the image of a compiled program (l3.Program): its rows are the rows of the layers."""
    st, A, RB = p.stats, p.A, p.RB
    bo = st['boot_bytes'] * 8
    rows, marks = [0], {}
    for i, l in enumerate(p.layers):
        for base in ([l.addr] if l.addr is not None else []) + ([0] if i == 0 else []):
            rows += [bo + base + s * RB for s in range(len(l.rows + l.jumps))]
    for b in p.blocks.values():
        for k, l in enumerate(b.layers):
            if l.addr is not None:
                marks.setdefault(bo + l.addr, []).append('layer %d of %s' % (k, b.name))
    views, groups = {id(T.data) for T in p.tables.values()}, {}
    for T in p.tables.values():
        groups.setdefault('grp_' + str(T.gid), []).append('%s (%d-bit entries at +%d, step %d)' % (T.name, T.out, T.off, 1 << T.j))
    for d in [d for d in p.datas if id(d) not in views] + p.gdatas:
        if d.addr is not None and d.bits:
            what = 'tables ' + ', '.join(groups[d.name]) if d.name in groups else 'data %s, %d bits' % (d.name, d.bits)
            marks.setdefault(bo + d.addr, []).append(what)
    marks.setdefault(0, []).insert(0, 'boot packet: the row which copies the rest of the image')
    marks.setdefault(bo, []).insert(0, 'snapshot')
    return dump(st['image'], A, rows, marks, title)


def main():
    if sys.argv[1:2] == ['-e']:
        image, err = encode(sys.stdin.buffer.read())
        sys.stdout.buffer.write(image)
        if err:
            sys.stderr.write(MESSAGES[err])
            sys.exit(1)
        return
    with open(sys.argv[1], encoding='utf-8') as h:
        p, errors = text.compile_text(h.read())
    if errors:
        sys.stderr.write('\n'.join(errors) + '\n')
        sys.exit(1)
    sys.stdout.write(program_text(p, 'the image of %s (A=%d, P=%d), generated by tower/l1text.py' % (
        os.path.basename(sys.argv[1]), p.stats['A'], p.stats['P'])))


if __name__ == '__main__':
    main()
