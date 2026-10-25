"""The comment word \\ is a generator of the language (14.8, src/primitives.fth GEN-BACKSLASH).

The compiler has no special case for it: the word is found in the dictionary and executed. It has the
need 8, so that the scan of the needs (FC-SCAN-USES) executes it too and does not count the words of the
comment. Checked on a program whose comments name `*`, `/`, `mod` and `kernel-layout` and which uses
none of them, and which writes the character `\\` (the raw word after [CHAR]):
1. the stream compiled by the definition on the host pForth equals the stream of the model (no
   subroutine of multiplication or division, no kernel layout) and runs on checked-emulator;
2. the kernel L0 on the emulator compiles the same program (its dictionary has the generator \\)
   and writes the same output.
"""
import subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_kernel, check_programs, host, paths

SOURCE = (
    '\\ a comment with * and / and mod and /mod and kernel-layout, and ( an open paren\n'
    ': main 65 emit \\ a trailing comment: 3 * 4 / 5 mod kernel-layout\n'
    '  ( a comment ) 66 emit\n'
    '  [char] \\ emit\n'
    '  10 emit ;')
WANT = b'AB\\\n'


def main():
    subprocess.run(['make', '-s', '-C', str(paths.VM2_ROOT), '-j1', 'checked-emulator'], check=True)
    executable = host.build()
    stream = check_programs.compile_on_host(executable, paths.source_bytes(paths.LIBRARY_FILES), SOURCE)
    sys.path[:0] = [str(paths.FORTH / 'scripts')]
    from forthc import model  # only the reference
    assert stream == model.compile_forth(SOURCE), 'the stream differs from the model'
    run = subprocess.run([str(paths.CHECKED), '-s', str(paths.SIZE), '-p', '8'], input=stream,
                         capture_output=True, timeout=600)
    assert run.returncode == 0 and run.stdout == WANT, (run.returncode, run.stdout)
    print('PASS host: comments with the words * / mod kernel-layout change nothing; the stream equals the model:',
          run.stdout)
    if not paths.EMULATOR.is_file():
        subprocess.run(['make', '-s', '-C', str(paths.EMULATOR_ROOT), '-j1', 'runtime-bitcopy'], check=True)
    got, seconds = check_kernel.run(paths.L0.read_bytes() + SOURCE.encode() + b'\0', 1800)
    assert got == WANT, got
    print(f'PASS kernel L0: the same program, the comment word is the generator of its dictionary ({seconds:.0f} s)')


if __name__ == '__main__':
    main()
