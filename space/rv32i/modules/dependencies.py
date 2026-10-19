"""Resolve declared source dependencies, also in standalone vendored releases."""
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
def dependency(name, variable):
    bundled=ROOT/'vendor'/name
    parent = ROOT.parent.parent if name == 'emulator' and ROOT.parent.name == 'space' else ROOT.parent
    return Path(os.environ.get(variable,bundled if bundled.is_dir() else parent/name)).resolve()

VM2_ROOT=dependency('vm2','VM2_ROOT')
COPYCODE_ROOT=dependency('copycode','COPYCODE_ROOT')
EMULATOR_ROOT=dependency('emulator','EMULATOR_ROOT')
sys.path[:0]=[str(VM2_ROOT),str(COPYCODE_ROOT/'src')]
