"""Paths and imports shared by the tools of space/language (standard library only)."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]            # space/language
WORKSPACE = ROOT.parents[1]
FORTH = Path(os.environ.get('FORTH_ROOT', WORKSPACE / 'space/forth')).resolve()
VM2_ROOT = Path(os.environ.get('VM2_ROOT', WORKSPACE / 'space/vm2')).resolve()
COPYCODE_ROOT = Path(os.environ.get('COPYCODE_ROOT', WORKSPACE / 'space/copycode')).resolve()
EMULATOR_ROOT = Path(os.environ.get('EMULATOR_ROOT', WORKSPACE / 'emulator')).resolve()
SRC = ROOT / "src"
SIZE = 1 << 31                                         # bits of the space (emulator -s), as model.SIZE
# Order of compilation of the language definition (as KERNEL in space/forth/tests/test_kernel.py,
# with primitives.fth, the generators of 14.3, after the compiler forthc.fth).
COMPILER_FILES = ['prelude.fth', 'backend.fth', 'compute.fth', 'forthc.fth', 'primitives.fth', 'main.fth']
KERNEL_FILES = COMPILER_FILES + ['kernel.fth']
# Libraries loaded natively into the host pForth (the compiler forthc.fth, what it needs and
# its generators).
LIBRARY_FILES = ['backend.fth', 'compute.fth', 'forthc.fth', 'primitives.fth']

sys.path[:0] = [str(COPYCODE_ROOT / 'src'), str(VM2_ROOT)]
from copycode.hostpaths import output_dir  # noqa: E402

BUILD = output_dir(ROOT, 'build')                     # build/space/language/build
OUT = BUILD.parent if (WORKSPACE / 'tools/workspace.mk').is_file() else BUILD   # build/space/language
L0 = OUT / 'L0.boot'


def text(names):
    return ''.join((SRC / n).read_text() for n in names)


def source_bytes(names):
    return b''.join((SRC / n).read_bytes() for n in names)


def programs():
    """PROGRAMS and EXPECTED of space/forth/tests/forthc_programs.py: {name: (source, expected or None)}."""
    sys.path[:0] = [str(FORTH / 'tests')]
    from forthc_programs import PROGRAMS, EXPECTED, wrapped
    cases = {name: (wrapped(source), None) for name, source in PROGRAMS.items()}
    cases.update({name: (wrapped(source), want) for name, (source, want) in EXPECTED.items()})
    return cases


CHECKED = output_dir(VM2_ROOT, 'build') / 'checked-emulator'
EMULATOR = output_dir(EMULATOR_ROOT, 'build') / 'bitcopy/emulator'
