"""Check and proof (14.12, language/doc/proof.md).

CHECK-TABLE ( xt in-bits out-bits table -- ok ) executes the word xt on all 2^in-bits inputs
(an input is one number on the stack, 0 ... 2^in-bits - 1; the table has a cell for each) and compares
the low out-bits of the result with the cell of the table. ACCURACY ( xt -- n ) is the share of the
inputs that agreed, in millionths. A full agreement makes the word proved: its record in the registry
of the proofs of the program refers to the common word "proved" (PROVED? is true). The programs run
on checked-emulator; the expected output is computed here, not by the definition.

1. 1-bit and, or, xor: proved by their tables; PROVED? is false before the check and true after it;
   the same word against a wrong table: not ok, 50 % accuracy, not proved (the last check decides).
2. A 4-bit adder in two definitions (shifts and +; half-adders in a loop): the tables made by running
   them are equal, both are proved by the table of the sum made by loops. The adder spoiled at one
   sum (17 -> 16: 14 inputs of 256) does not pass: accuracy 945312, not proved.
3. Arguments that are not valid (in-bits above 31, out-bits 0 or above 32): not ok, nothing checked
   (accuracy 0); only the low out-bits are compared (out-bits 4 for a 5-bit sum). A 12-bit word spoiled
   at one input: accuracy below 1000000 (the count is cut to 11 bits for the product in 32 bits).
4. The registry has 32 words: the 33rd throws -8 (caught).
5. The words of the proof are in the program only when its source names them: the stream of a program
   that does not equals the stream of the model; the definition of the language has none of them.
6. The kernel L0 on the emulator compiles and runs the program of 1 and writes the same output.
"""
import subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_kernel, check_programs, host, paths, word_cost

PRINT = (': d. ( u -- ) dup 10 < if 48 + emit exit then dup 10 / recurse 10 mod 48 + emit ;\n'
         ': n. ( n -- ) dup 0 < if 45 emit 0 swap - then d. 32 emit ;\n')
GATES = PRINT + '''
: and1 dup 1 and swap 1 rshift and ;
: or1 dup 1 and swap 1 rshift or ;
: xor1 dup 1 and swap 1 rshift xor ;
create t-and 16 allot create t-or 16 allot create t-xor 16 allot
: set swap cells + ! ;
0 0 t-and set 0 1 t-and set 0 2 t-and set 1 3 t-and set
0 0 t-or set 1 1 t-or set 1 2 t-or set 1 3 t-or set
0 0 t-xor set 1 1 t-xor set 1 2 t-xor set 0 3 t-xor set
: main
  ['] and1 proved? n.
  ['] and1 2 1 t-and check-table n. ['] or1 2 1 t-or check-table n. ['] xor1 2 1 t-xor check-table n.
  ['] and1 proved? n. ['] or1 proved? n. ['] xor1 proved? n. ['] and1 accuracy n.
  ['] or1 2 1 t-and check-table n. ['] or1 proved? n. ['] or1 accuracy n.
  10 emit ;
'''
GATES_WANT = b'0 -1 -1 -1 -1 -1 -1 1000000 0 0 500000 \n'
ADDERS = PRINT + '''
: add4a dup 15 and swap 4 rshift 15 and + ;
: add4b dup 15 and swap 4 rshift 15 and 5 0 do over over and 2* >r xor r> loop + ;
: add4x dup 15 and swap 4 rshift 15 and + dup 17 = if drop 16 then ;
create ref 1024 allot create ta 1024 allot create tb 1024 allot
: build 16 0 do 16 0 do i j + j i 4 lshift or cells ref + ! loop loop ;
variable xtv
: tabulate ( xt table -- ) swap xtv ! 256 0 do i xtv @ execute over i cells + ! loop drop ;
variable acc
: same? ( t1 t2 -- f ) -1 acc ! 256 0 do over i cells + @ over i cells + @ = acc @ and acc ! loop drop drop acc @ ;
: main
  build ['] add4a ta tabulate ['] add4b tb tabulate
  ta tb same? n. ta ref same? n. tb ref same? n.
  ['] add4a 8 5 ref check-table n. ['] add4b 8 5 ref check-table n.
  ['] add4a proved? n. ['] add4b proved? n. ['] add4a accuracy n.
  ['] add4x 8 5 ref check-table n. ['] add4x proved? n. ['] add4x accuracy n.
  ['] add4a 32 5 ref check-table n. ['] add4a 8 0 ref check-table n. ['] add4a 8 33 ref check-table n.
  ['] add4a proved? n. ['] add4a accuracy n.
  ['] add4b 8 5 ref check-table n. ['] add4b 8 4 ref check-table n. ['] add4b proved? n. ['] add4b accuracy n.
  10 emit ;
'''
ADDERS_WANT = (b'-1 -1 -1 -1 -1 -1 -1 1000000 0 0 945312 0 0 0 0 0 -1 -1 -1 1000000 \n')
WIDE = PRINT + '''
create idt 16384 allot
: fill-id 4096 0 do i idt i cells + ! loop ;
: id12 ;
: bad12 dup 7 = if drop 0 then ;
: main fill-id ['] id12 12 12 idt check-table n. ['] id12 proved? n. ['] id12 accuracy n.
  ['] bad12 12 12 idt check-table n. ['] bad12 proved? n. ['] bad12 accuracy n. 10 emit ;
'''
WIDE_WANT = b'-1 -1 1000000 0 0 999511 \n'     # 4095 >> 1 = 2047 of 2048
FULL = 32


def registry_source():
    words = '\n'.join(f': g{i} ;' for i in range(FULL + 1))
    checks = '\n'.join(f"['] g{i} 0 1 t check-table drop" for i in range(FULL + 1))
    return PRINT + f'create t 4 allot\n{words}\n: all\n{checks} ;\n: main [\'] all catch n. 10 emit ;\n'


def run_checked(stream):
    run = subprocess.run([str(paths.CHECKED), '-s', str(paths.SIZE), '-p', '8'], input=stream,
                         capture_output=True, timeout=600)
    assert run.returncode == 0, (run.returncode, run.stderr[-300:])
    return run.stdout


def compile_run(source):
    return run_checked(check_programs.compile_on_host(host.build(), paths.source_bytes(paths.LIBRARY_FILES), source))


def check_gates():
    got = compile_run(GATES)
    assert got == GATES_WANT, (got, GATES_WANT)
    print('PASS gates: and, or, xor proved by their 1-bit tables (unproved before the check); the same word '
          'against a wrong table: not ok, accuracy 500000, not proved:', got.decode().strip())


def check_adders():
    got = compile_run(ADDERS)
    assert got == ADDERS_WANT, (got, ADDERS_WANT)
    print('PASS adders: the tables of two 4-bit adders equal, both proved; the spoiled one: not ok, '
          'accuracy 945312 (242 of 256); invalid arguments: not ok, accuracy 0; low out-bits only:',
          got.decode().strip())
    got = compile_run(WIDE)
    assert got == WIDE_WANT, (got, WIDE_WANT)
    print('PASS 12 bits: a word spoiled at one input of 4096: not ok, accuracy 999511 (cut to 11 bits)')


def check_registry():
    got = compile_run(registry_source())
    assert got == b'-8 \n', got
    print('PASS the registry has 32 words: the 33rd word throws -8')


def check_library_only_when_named():
    sys.path[:0] = [str(paths.REFERENCE)]
    import model
    source = PRINT + ': main 65 emit 10 emit ;'
    assert check_programs.compile_on_host(host.build(), paths.source_bytes(paths.LIBRARY_FILES),
                                          source) == model.compile_forth(source)
    _, records, _ = word_cost.compile_with_records(GATES)
    assert {'%check', '%acc', '%prv', '%slot', 'check-table', 'accuracy', 'proved?'} <= set(records), list(records)[:12]
    _, records, _ = word_cost.definition()
    assert not [name for name in records if name.startswith('%') or name in ('check-table', 'accuracy')], 'in the definition'
    print('PASS the words of the proof are compiled only into a program that names them (the stream of '
          'another equals the model; the definition of the language has none)')


def check_kernel_l0():
    if not paths.EMULATOR.is_file():
        subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'runtime-bitcopy'], check=True)
    got, seconds = check_kernel.run(paths.L0.read_bytes() + GATES.encode() + b'\0', 3000)
    assert got == GATES_WANT, (got, GATES_WANT)
    print(f'PASS kernel L0: compiles and runs the program of gates, the same output ({seconds:.0f} s)')


def main():
    subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'checked'], check=True)
    check_gates()
    check_adders()
    check_registry()
    check_library_only_when_named()
    check_kernel_l0()


if __name__ == '__main__':
    main()
