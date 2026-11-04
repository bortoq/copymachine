#!/usr/bin/env python3
"""The word of disjointness DJ-PROVE (3.7.5, doc/isolation.md) on the host pForth.

A program is compiled in the mode of the program of the kernel (FC-GUARD 1) into an image of its layers
(a sink of LAY-PUT, as the kernel has) and DJ-PROVE reads the layers from the image.

1. The 37 programs of check-programs and a program with every word that computes a position (SPACE! SPACEC!
   SPACE@ SPACEC@ EXECUTE, the call and the return, * and /) and the program of the replacement
   (the concept cells that take the entry from the record of the word) are proved; so are the table of entries and the table of returns.
2. The same programs compiled for the whole space (FC-GUARD 0: the return writes all 32 bits of the
   link row) are refused, rule 2.
3. Violations built in the image of the program (a field of a row is changed in the image, then DJ-PROVE
   again, then the field is restored) are refused with the number of the rule: a row of the kernel block, a
   copy of two lengths, a patch that crosses its field or writes bits above the
   block, a start of an interval in the upper half of the data, a row that is not alone in the layer of the
   position of a program, a channel that is not stdin or stdout.
4. The long copy (18.24, rule 3): a program with long! and long@ is proved, and the violations of the request are refused:
   the header copied from the data, from a template that does not start with 6, written in part; a row into SYS that does not
   copy the whole request block (another start, another length, from the code); the answer of SYS into the kernel or patched
   in 29 bits.
"""
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import host
import paths

CELL = 1024
SLOT = 128
BASE2 = 1 << 30                     # the data block of the program (block 2)
BLOCK = 1 << 29
CELLS = 1 << 15                     # the image holds the cells below this, then the cells of the table of entries
TABLE = 1 << 12                     # and of the table of returns
RTABLE = 1 << 14
ETAB = 1 << 18                      # the first cell of the table of entries (fc-etab)
RTAB = ETAB + (1 << 14)             # the first cell of the table of returns (fc-rtab)

HARNESS = r'''
variable cap-buf variable cap-main variable cap-tab variable cap-rt
: cap-init ( main-bytes table-bytes returns-bytes -- )
  cap-rt ! cap-tab ! cap-main ! cap-main @ cap-tab @ + cap-rt @ + allocate throw cap-buf !
  cap-buf @ cap-main @ cap-tab @ + cap-rt @ + 0 fill ;
: cap-base ( byte-address -- offset|-1 ) \ the cells of the program, the table of entries, the table of returns
  dup fc-etab 3 rshift u< if dup cap-main @ u< 0= if drop -1 then exit then
  dup fc-rtab 3 rshift u< if
    fc-etab 3 rshift - dup cap-tab @ u< 0= if drop -1 exit then cap-main @ + exit then
  fc-rtab 3 rshift - dup cap-rt @ u< 0= if drop -1 exit then cap-main @ + cap-tab @ + ;
: cap-put ( bit-address src n -- ) rot 3 rshift cap-base dup 0< if drop 2drop exit then cap-buf @ + swap cmove ;
: cap-read ( bit-address -- x ) 3 rshift cap-base dup 0< if drop 0 exit then cap-buf @ + @ ;
: cap-w ( x bit-address -- ) 3 rshift cap-base cap-buf @ + ! ;
: cap-order 256 0 do i lay-rev i + c! loop ;
: cap-prove ( -- ) ." @@ " fc-first @ lay-next-cell @ dj-prove
  dup if drop fc-etab lay-cell-bit rshift dup fc-nwords @ 2* + dj-prove then
  dup if drop fc-rtab lay-cell-bit rshift dup fc-nret @ 2* + dj-prove then
  . dj-bad-rule @ . dj-bad-cell @ . lay-next-cell @ . cr ;
'''

BUF = BASE2 + (1 << 27)
LONGP = f': main {paths.host_pos(0)} {BUF} {BUF + 1024} long@ {paths.host_pos(1, 5)} {BUF} {BUF + 256} long! 65 emit ;'
REQ = BASE2 + (1 << 28) + 1024               # the request block of the long copy (lay-req)
REC, CAP, HDR = 88 + paths.HOST_POS_BITS, 1 << 16, 56   # lay-rec: op 8, chan 32, flags 16, arg 32, off

PROGRAM = '''variable v
: w 5 ;
: a 7 v @ + ;
: main 7 1207959552 space! 9 1207959553 spacec! 1207959552 space@ drop 1207959553 spacec@ drop
  ['] w execute drop ['] a execute drop 3 4 * 7 / drop 65 emit ;'''


def run_host(source, guard, tail, libraries):
    task = [HARNESS, f"{CELLS * CELL // 8} {TABLE * CELL // 8} {RTABLE * CELL // 8} cap-init cap-order {guard} fc-guard ! ' cap-put lay-sink ! "
                     "' cap-read dj-reader !"]
    task += ['fc| ' + line for line in source.split('\n')]
    task += ['fc-go', 'cap-prove', tail, 'bye']
    code, out, err = host.run(host.build(), libraries + ('\n'.join(task) + '\n').encode('latin-1'), 900)
    assert code == 0 and not err, (code, err[-300:])
    return out


def verdicts(out):
    return [tuple(int(x) for x in line.split()[1:5]) for line in out.decode('latin-1').split('\n') if line.startswith('@@ ')]


def image_of(out):
    mark = out.index(b'@@IMAGE\n') + 8
    return out[mark:mark + (CELLS + TABLE + RTABLE) * CELL // 8]


def index(bit):
    byte = bit // 8
    if byte >= RTAB * CELL // 8:
        return (CELLS + TABLE) * CELL // 8 + byte - RTAB * CELL // 8
    return CELLS * CELL // 8 + byte - ETAB * CELL // 8 if byte >= ETAB * CELL // 8 else byte


def word(img, bit):
    return int.from_bytes(img[index(bit):index(bit) + 4], 'little')


def row(img, cell, slot):
    base = cell * CELL + slot * SLOT
    return [word(img, base + 32 * f) for f in range(4)]


def field(cell, slot, f):
    return cell * CELL + slot * SLOT + 32 * f


def find(img, ncells, test):
    return [(c, s) for c in range(2, ncells) for s in range(8) if test(row(img, c, s))]


def sel_table(img):
    """The link row of the first layer of the table of entries."""
    for c in range(ETAB, ETAB + 2 * TABLE, 2):
        r = row(img, c, 7)
        if r[0] == 0 and r[1] == CELL and r[3] - r[2] == CELL:
            return c, 7
    raise AssertionError('no layer in the table of entries')


def sel_rtable(img):
    """The link row of the first layer of the table of returns."""
    for c in range(RTAB, RTAB + 2 * RTABLE, 2):
        r = row(img, c, 7)
        if r[1] == CELL and r[3] - r[2] == CELL and r[2] >= 2 * CELL:
            return c, 7
    raise AssertionError('no layer in the table of returns')


def cases(img, ncells):
    """Name -> (changes [(bit address of a field, new value)], rule). The rows are found in the image."""
    def sel(test):
        found = find(img, ncells, test)
        assert found, 'no row for the case'
        return found[0]
    def fld(cell, slot, f):
        return cell * CELL + slot * SLOT + 32 * f
    # SPACE!: the placeholder of the interval at the base of the data, the row alone in its layer
    store = sel(lambda r: r[0] == BASE2 and r[1] == BASE2 + 32 and r[3] - r[2] == 32)
    # the patch of the field dl of the row of SPACE!
    dl_patch = sel(lambda r: r[0] == fld(*store, 0))
    # a patch of the target of EXECUTE (the number of the word, 11 bits, to the bit 11 of a field of a link row)
    ex = sel(lambda r: r[1] - r[0] == 11 and r[0] % 32 == 11 and r[0] >= 2 * CELL)
    # a patch of the target of the return (the number of the point, 13 bits, to the bit 11 of a field of a link row)
    ret = sel(lambda r: r[1] - r[0] == 13 and r[0] % 32 == 11 and r[0] >= 2 * CELL)
    # the link row of a layer, a layer with two rows of data, the row of stdout
    link = sel(lambda r: r[0] == 0 and r[1] == CELL and r[3] - r[2] == CELL and r[2] >= 2 * CELL)
    two = None
    for c in range(2, ncells):
        data = [s for s in range(7) if row(img, c, s)[2] != row(img, c, s)[3] and row(img, c, s)[2] >= BASE2]
        if len(data) >= 2:
            two = (c, data[0], data[1])
            break
    assert two
    chan = sel(lambda r: r[0] == r[1] and r[0] >= 1 << 31 and r[3] > r[2])
    out = {}
    out['source of a link row in the kernel block'] = (
        [(fld(*link, 2), BLOCK + word(img, fld(*link, 2))), (fld(*link, 3), BLOCK + word(img, fld(*link, 3)))], 1)
    out['source of a copy in the kernel block'] = ([(fld(*store, 2), 3 * BLOCK + 4096), (fld(*store, 3), 3 * BLOCK + 4128)], 1)
    out['a copy of two lengths'] = ([(fld(*store, 3), word(img, fld(*store, 3)) + 1)], 1)
    out['a channel that is not stdin or stdout'] = (
        [(fld(*chan, 0), word(img, fld(*chan, 0)) + 1), (fld(*chan, 1), word(img, fld(*chan, 1)) + 1)], 1)
    c, a, b = two
    ra = row(img, c, a)
    n = ra[3] - ra[2]
    out['a memory interval across the border of the block'] = (
        [(fld(c, a, 2), 3 * BLOCK - n // 2), (fld(c, a, 3), 3 * BLOCK + n - n // 2)], 1)
    out['start of the destination in the upper half of the data'] = (
        [(fld(*store, 0), BASE2 + (1 << 28)), (fld(*store, 1), BASE2 + (1 << 28) + 32)], 2)
    out['patch of the destination of 29 bits instead of 28'] = (
        [(fld(*dl_patch, 1), row(img, *dl_patch)[1] + 1), (fld(*dl_patch, 3), row(img, *dl_patch)[3] + 1)], 2)
    out['patch of the number of a word of 21 bits instead of 11 (to the end of the field)'] = (
        [(fld(*ex, 1), row(img, *ex)[1] + 10), (fld(*ex, 3), row(img, *ex)[3] + 10)], 2)
    out['patch of the number of a return of 21 bits instead of 13 (to the end of the field)'] = (
        [(fld(*ret, 1), row(img, *ret)[1] + 8), (fld(*ret, 3), row(img, *ret)[3] + 8)], 2)
    rtab = sel_rtable(img)
    out['a table of returns layer that jumps into the kernel'] = (
        [(fld(*rtab, 2), BLOCK + word(img, fld(*rtab, 2))), (fld(*rtab, 3), BLOCK + word(img, fld(*rtab, 3)))], 1)
    tab = sel_table(img)
    out['a table of entries layer that jumps into the kernel'] = (
        [(fld(*tab, 2), BLOCK + word(img, fld(*tab, 2))), (fld(*tab, 3), BLOCK + word(img, fld(*tab, 3)))], 1)
    out['patch across the border of the field'] = (
        [(fld(*dl_patch, 0), row(img, *dl_patch)[0] + 8), (fld(*dl_patch, 1), row(img, *dl_patch)[1] + 8)], 2)
    free = next(t for t in range(7) if row(img, store[0], t) == [0, 0, 0, 0])
    out['a row of data in the layer of a position of the program'] = (
        [(fld(store[0], free, 0), BASE2 + 4096), (fld(store[0], free, 1), BASE2 + 4128),
         (fld(store[0], free, 2), BASE2 + 8192), (fld(store[0], free, 3), BASE2 + 8224)], 2)
    return out


def long_cases(img, ncells):
    """The violations of rule 3 for the program with long! and long@: name -> (changes, rule)."""
    def sel(test):
        found = find(img, ncells, test)
        assert found, 'no row for the case'
        return found[0]
    send = sel(lambda r: r[0] == r[1] == 1 << 31 and r[2] == REQ and r[3] == REQ + REC + CAP)
    head = sel(lambda r: r[0] == REQ and r[1] == REQ + HDR and r[2] < BASE2)
    tpl = sel(lambda r: r == [6, 0, 0, 0])
    answer = sel(lambda r: r == [BASE2, BASE2 + 1, 1 << 31, 1 << 31])
    patch = sel(lambda r: r[0] == field(*answer, 0))
    f = field
    hr = row(img, *head)
    out = {}
    out['the header of the request copied from the data'] = (
        [(f(*head, 2), BASE2 + 4096), (f(*head, 3), BASE2 + 4096 + HDR)], 3)
    out['the header copied from a template that does not start with 6'] = ([(f(*tpl, 0), 5)], 3)
    out['the header written in part'] = ([(f(*head, 0), hr[0] + 8), (f(*head, 1), hr[1] + 8)], 3)
    out['a row into SYS from another place of the data'] = (
        [(f(*send, 2), BASE2 + 4096), (f(*send, 3), BASE2 + 4096 + REC + CAP)], 3)
    out['a row into SYS of another length'] = ([(f(*send, 3), REQ + REC + CAP + 1)], 3)
    out['a row into SYS from the code'] = ([(f(*send, 2), 4096), (f(*send, 3), 4096 + REC + CAP)], 3)
    out['the answer of SYS into the kernel'] = (
        [(f(*answer, 0), 3 * BLOCK + 4096), (f(*answer, 1), 3 * BLOCK + 4097)], 2)
    out['the patch of the answer of 29 bits instead of 28'] = (
        [(f(*patch, 1), row(img, *patch)[1] + 1), (f(*patch, 3), row(img, *patch)[3] + 1)], 2)
    return out


def check_violations(program, libraries, cases_of):
    dump = "cr .( @@IMAGE) cr cap-buf @ %d type" % ((CELLS + TABLE + RTABLE) * CELL // 8)
    out = run_host(program, 1, dump, libraries)
    img = image_of(out)
    ncells = verdicts(out)[0][3]
    table = cases_of(img, ncells)
    tail = []
    for changes, _ in table.values():
        tail.append(' '.join(f'{new} {bit} cap-w' for bit, new in changes) + ' cap-prove ' +
                    ' '.join(f'{word(img, bit)} {bit} cap-w' for bit, _ in changes))
    out = run_host(program, 1, '\n'.join(tail), libraries)
    got = verdicts(out)[1:]
    assert len(got) == len(table), (len(got), len(table))
    for (name, (_, rule)), (flag, number, cell, _) in zip(table.items(), got, strict=True):
        assert flag == 0 and number == rule, (name, flag, number, cell, 'expected the rule', rule)
        print(f'PASS refused, rule {number}, cell {cell}: {name}')
    return len(table)


def main():
    libraries = paths.source_bytes(paths.LIBRARY_FILES)
    # 1. the programs are proved
    sources = {name: source for name, (source, _) in paths.programs().items()}
    sources['positions'] = PROGRAM
    sources['long copy'] = LONGP
    sources['replacement'] = runpy.run_path(str(Path(__file__).with_name('test_replace.py')), run_name='x')['REPLACE']
    for name, source in sources.items():
        out = run_host(source, 1, '', libraries)
        assert [v[:3] for v in verdicts(out)] == [(-1, 0, 0)], (name, verdicts(out), out[-200:])
    print(f'PASS DJ-PROVE proves the {len(sources) - 3} programs, a program of the positions, a program of the long copy and a program of the replacement compiled for the program of the kernel')
    # 2. compiled for the whole space the return is refused
    for name in ('calls', 'execute', 'positions'):
        out = run_host(sources[name], 0, '', libraries)
        flag, rule, cell = verdicts(out)[0][:3]
        assert flag == 0 and rule == 2, (name, verdicts(out))
    print('PASS the programs compiled for the whole space (the return writes 32 bits of the link row) are refused: rule 2')
    # 3. the built violations
    count = check_violations(PROGRAM, libraries, cases)
    print(f'ALL {count} violations of the word of disjointness are refused')
    # 4. the long copy
    count = check_violations(LONGP, libraries, long_cases)
    print(f'ALL {count} violations of the request of the long copy are refused')


if __name__ == '__main__':
    main()
