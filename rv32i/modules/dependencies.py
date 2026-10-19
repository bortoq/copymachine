"""Resolve declared source dependencies, also in standalone vendored releases."""
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
def dependency(name, variable):
    bundled=ROOT/'vendor'/name
    return Path(os.environ.get(variable,bundled if bundled.is_dir() else ROOT.parent/name)).resolve()

VM2_ROOT=dependency('vm2','VM2_ROOT')
COPYCODE_ROOT=dependency('copycode','COPYCODE_ROOT')
VM1_ROOT=dependency('vm1','VM1_ROOT')
sys.path[:0]=[str(VM2_ROOT),str(COPYCODE_ROOT/'src')]
