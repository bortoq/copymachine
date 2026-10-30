"""Paths and imports shared by the tools of language (standard library only)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]            # language
WORKSPACE = ROOT.parent
BOOT = ROOT / 'boot'                                   # the host pForth32: upstream, port, common.py
REFERENCE = ROOT / 'tests/reference'                   # independent references: model K0, programs, counters
EMULATOR_ROOT = Path(os.environ.get('EMULATOR_ROOT', WORKSPACE / 'emulator')).resolve()
SRC = ROOT / "src"
SIZE = 1 << 31                                         # bits of the space (emulator -s), as model.SIZE
# Order of compilation of the language definition (as KERNEL in forth/tests/test_kernel.py of the archive,
# with primitives.fth, the generators of 14.3, after the compiler forthc.fth).
COMPILER_FILES = ['prelude.fth', 'backend.fth', 'compute.fth', 'forthc.fth', 'primitives.fth', 'main.fth']
KERNEL_FILES = COMPILER_FILES + ['kernel.fth']
# Libraries loaded natively into the host pForth (the compiler forthc.fth, what it needs and
# its generators).
LIBRARY_FILES = ['backend.fth', 'compute.fth', 'forthc.fth', 'primitives.fth']

sys.path[:0] = [str(REFERENCE)]

BUILD = ROOT / 'build'                                # language/build
OUT = BUILD
L0 = OUT / 'L0.boot'


def text(names):
    return ''.join((SRC / n).read_text() for n in names)


def source_bytes(names):
    return b''.join((SRC / n).read_bytes() for n in names)


def programs():
    """PROGRAMS and EXPECTED of language/tests/reference/forthc_programs.py: {name: (source, expected or None)}."""
    from forthc_programs import EXPECTED, PROGRAMS, wrapped
    cases = {name: (wrapped(source), None) for name, source in PROGRAMS.items()}
    cases.update({name: (wrapped(source), want) for name, (source, want) in EXPECTED.items()})
    return cases


CHECKED = EMULATOR_ROOT / 'build/checked-emulator'
# EMULATOR=path (15.1) chooses the executor: any emulator binary, for example the one built from the
# definition of the word "space" (emulator/src, language/build/space/emulator).
EMULATOR = Path(os.environ['EMULATOR']).resolve() if os.environ.get('EMULATOR') else EMULATOR_ROOT / 'build/bitcopy/emulator'
# The executor of check-programs: EMULATOR if given, else checked-emulator.
EXECUTOR = EMULATOR if os.environ.get('EMULATOR') else CHECKED
