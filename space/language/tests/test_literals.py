"""Literals, digits, numbers (14.7, space/language/doc/literals.md).

The compiler has no number parsing: a word not found in the dictionary goes to the word
`literal` of the definition (src/primitives.fth), which builds a number from the digits 0..9,
words of the language (synonyms of literals). Checked:
1. on the host pForth (the definition compiles the program, checked-emulator runs the stream):
   the numbers 0, 1, 255, 2^31-1, -1 (and 2^32-1, 007, -0) in a definition and at the top level
   (values known at compile time) give the expected output; a literal is one copy of a
   constant (the stream of a word with one literal equals that of the model);
2. a word that is neither in the dictionary nor a number gives `error -13 at WORD`
   (host: the same text as the kernel prints);
3. the word `literal` is replaceable: a definition that registers another generator under the
   name `literal` (here: hexadecimal $NN, else the decimal word) changes the numbers;
4. the kernel L0 on the emulator compiles the same program (its numbers go through `literal`
   too) and reports the unknown word as `error -13 at WORD`.
"""
import subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_kernel, check_programs, host, paths

PRINT = (': d. ( u -- ) dup 10 < if 48 + emit exit then dup 10 / recurse 10 mod 48 + emit ;\n'
         ': n. ( n -- ) dup 0 < if 45 emit 0 swap - then d. 32 emit ;\n')
NUMBERS = PRINT + (
    '0 constant c0 1 constant c1 255 constant c255 2147483647 constant cmax -1 constant cm1\n'
    '255 1 + constant c256\n'
    ': main 0 n. 1 n. 255 n. 2147483647 n. -1 n. 4294967295 n. 007 n. -0 n. -1 255 and n. -1 1 rshift n.'
    ' 5 3 - n. c0 n. c1 n. c255 n. cmax n. cm1 n. c256 n. ;')
WANT = b'0 1 255 2147483647 -1 -1 7 0 255 2147483647 2 0 1 255 2147483647 -1 256 '
ERRORS = {
    ': main 1 frobnicate ;': b'frobnicate',      # a word in a definition
    ': main 12a ;': b'12a',                     # digits, then not a digit
    ': main --1 ;': b'--1',
    'frob\n: main ;': b'frob',                  # at the top level
    ': main 2drop ;': b'2drop',                 # not in the dictionary of a program
}
# The host reports a compile error as the kernel does (kernel.fth: MAIN).
HOST_REPORT = (': h.n dup 0< if 45 emit negate then dup 10 / ?dup if recurse then 10 mod 48 + emit ;\n'
               ': try [\'] fc-go catch ?dup if ." error " h.n ."  at " fc-tok fc-tl @ type 10 emit then ;\n')
# Another word LITERAL: $ and hexadecimal digits, else the decimal word of the definition.
HEX = (': gen-hex ( -- )\n'
       '  fc-tok c@ [char] $ = if\n'
       '    0 fc-tok fc-tl @ 1 /string over + swap do\n'
       '      16 * i c@ dup [char] a < if [char] 0 - else [char] a - 10 + then +\n'
       '    loop fc-defining? if fc-literal else fc-ct+ then exit\n'
       '  then gen-literal ;\n'
       ': hex-generators ( -- ) fc-generators s" literal" [\'] gen-hex 0 fc-generator ;\n'
       "' hex-generators fc-gens !\n")


def host_compile(source, before=''):
    executable = host.build()
    task = before + HOST_REPORT + '\n'.join('fc| ' + line for line in source.split('\n')) + '\ntry bye\n'
    return check_programs.run_host(executable, paths.source_bytes(paths.LIBRARY_FILES) + task.encode('latin-1'))


def run_checked(stream):
    run = subprocess.run([str(paths.CHECKED), '-s', str(paths.SIZE), '-p', '8'], input=stream,
                         capture_output=True, timeout=600)
    assert run.returncode == 0, (run.returncode, run.stderr[-300:])
    return run.stdout


def main():
    subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'checked'], check=True)
    stream = host_compile(NUMBERS)
    got = run_checked(stream)
    assert got == WANT, (got, WANT)
    print('PASS host: numbers 0 1 255 2^31-1 -1 2^32-1 007 -0, in a definition and at the top level:',
          got.decode().strip())
    sys.path[:0] = [str(paths.FORTH / 'scripts')]
    from forthc import model  # only the reference: it compiles a number as one copy of a constant
    for source in (': main 255 emit ;', ': main 0 1 2147483647 -1 drop drop drop emit ;'):
        assert host_compile(source) == model.compile_forth(source), source
    print('PASS host: a literal is one copy of a constant (the streams equal those of the model)')
    for source, word in ERRORS.items():
        out = host_compile(source)
        assert out.endswith(b'error -13 at ' + word + b'\n'), (source, out[-80:])
    print('PASS host: unknown words give error -13 at WORD:', b' '.join(ERRORS.values()).decode())
    got = run_checked(host_compile(': main $41 emit $ff 190 - emit 66 emit 10 emit ;', HEX))
    assert got == b'AAB\n', got
    print('PASS host: the word literal is replaceable ($41 $ff hexadecimal, 190 66 10 decimal)')
    if not paths.EMULATOR.is_file():
        subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'runtime-bitcopy'], check=True)
    l0 = paths.L0.read_bytes()
    got, seconds = check_kernel.run(l0 + NUMBERS.encode() + b'\0', 1800)
    assert got == WANT, (got, WANT)
    print(f'PASS kernel L0: the same numbers compiled and run in the space ({seconds:.0f} s)')
    for source in (': main 1 frobnicate ;', ': main 12a ;'):
        got, seconds = check_kernel.run(l0 + source.encode() + b'\0', 1800)
        assert got == b'error -13 at ' + ERRORS[source] + b'\n', got
    print('PASS kernel L0: error -13 at frobnicate, error -13 at 12a')


if __name__ == '__main__':
    main()
