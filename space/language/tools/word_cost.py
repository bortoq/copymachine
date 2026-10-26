#!/usr/bin/env python3
"""The records of the words (14.11, space/language/doc/word.md) as the compiler makes them.

The host pForth compiles a text with the definition of the language (forthc.fth with FC| lines and
FC-GO, as check-programs) and then prints the records of the dictionary: for every word (kind 1)
its name, the cell of its index definition, the price (size, bits, copies, layers, known), whether
its concept cell is its own and holds the index definition, the definitions of the copy and the
host space, the proof (proved, unproved with the checked set, other) and the stack of definitions;
then the trampoline, the thrower and the price of the helpers of * and / (if built).

Usage: word_cost.py [FILE]     a program (default: the definition of the language, src/ in the
                               order of the kernel): a summary of the prices of its words.
"""
import argparse, collections, sys

import check_programs
import host
import paths

# Host Forth after FC-GO (lines below the input limit of pForth).
DUMP = r'''
: wd.d dup 10 / ?dup if recurse then 10 mod 48 + emit ;
: wd.n dup 0< if 45 emit negate then wd.d 32 emit ;
: wd.proof 14 cells + @ dup fc-proved = if drop 1 exit then
  dup fc-unproved = if drop 0 exit then drop 2 ;
: wd.checked 14 cells + @ dup fc-proved = if drop 0 0 0 else
  dup 2 cells + @ swap dup cell+ @ swap @ then wd.n wd.n wd.n ;
: wd.rec dup @ fc-names @ + over cell+ @ type 32 emit
  dup 6 cells + @ wd.n 14 9 do dup i cells + @ wd.n loop
  dup 5 cells + @ over 3 cells + = wd.n dup 3 cells + @ over 6 cells + @ = wd.n
  dup 7 cells + @ wd.n dup 8 cells + @ wd.n dup wd.proof wd.n
  dup wd.checked 15 cells + @ wd.n ;
: wd.helper 4 0 do dup i cells + @ wd.n loop drop cr ;
: wd.all fc-nwords @ 0 ?do i fc-wt@ dup 2 cells + @ 1 = if ." W " wd.rec cr else drop then loop
  ." T " fc-tramp @ wd.n fc-thrower @ wd.n cr
  fc-uses @ 1 and if ." H mul " fc-mul-cost wd.helper then
  fc-uses @ 2 and if ." H div " fc-div-cost wd.helper then ;
'''
MARK = b'\n@@WORDS@@\n'
FIELDS = ('entry', 'size', 'bits', 'copies', 'layers', 'known', 'own_concept', 'concept_is_index',
          'copy', 'host', 'proof', 'checked', 'checked_bits', 'way', 'stack')


def compile_with_records(source, before='', sizes=''):
    """(stream, records, info): records {name: dict(FIELDS)} of the newest record of each name, in the
    order of definition; info: dict(tramp, thrower, mul, div, versions) (a helper: bits copies layers
    known; versions: {(name, n): record} of every record, n-th definition of the name)."""
    executable = host.build()
    task = (before + sizes + '\n' + '\n'.join('fc| ' + line for line in source.split('\n'))
            + '\nfc-go\n' + DUMP + 'cr .( ' + MARK.decode().strip() + ') cr wd.all\nbye\n')
    out = check_programs.run_host(executable, paths.source_bytes(paths.LIBRARY_FILES) + task.encode('latin-1'))
    at = out.rindex(MARK)
    stream, text = out[:at], out[at + len(MARK):].decode('latin-1')
    records, info = collections.OrderedDict(), {'versions': {}}
    for line in text.split('\n'):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == 'W':
            record = dict(zip(FIELDS, map(int, parts[2:])))
            records.pop(parts[1], None)
            records[parts[1]] = record
            version = 1 + sum(1 for name, _ in info['versions'] if name == parts[1])
            info['versions'][(parts[1], version)] = record
        elif parts[0] == 'T':
            info['tramp'], info['thrower'] = int(parts[1]), int(parts[2])
        elif parts[0] == 'H':
            info[parts[1]] = dict(zip(('bits', 'copies', 'layers', 'known'), map(int, parts[2:])))
    return stream, records, info


def definition():
    """The records of the words of the definition of the language, compiled by itself on the host."""
    import boot
    return compile_with_records(paths.text(paths.KERNEL_FILES), sizes=boot.SIZES)


def summary(records):
    known = [r for r in records.values() if r['known']]
    lines = [f'words {len(records)}, price known at compile time {len(known)}, by execution {len(records) - len(known)}']
    if known:
        for key in ('size', 'bits', 'copies', 'layers'):
            values = sorted(r[key] for r in known)
            lines.append(f'  {key}: min {values[0]}, median {values[len(values) // 2]}, max {values[-1]}')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', nargs='?')
    args = parser.parse_args()
    if args.file:
        _, records, info = compile_with_records(open(args.file).read())
    else:
        _, records, info = definition()
    for name, r in records.items():
        state = 'known' if r['known'] else 'by execution'
        print(f'{name:24} size {r["size"]:5}  bits {r["bits"]:8}  copies {r["copies"]:6}  layers {r["layers"]:5}  {state}')
    print(summary(records))
    for helper in ('mul', 'div'):
        if helper in info:
            print(helper, info[helper])


if __name__ == '__main__':
    sys.exit(main())
