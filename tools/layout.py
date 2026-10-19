#!/usr/bin/env python3
"""Keep component outputs under the workspace build directory."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ('emulator', 'space/copycode', 'space/vm2', 'space/rv32i', 'space/forth')

def prepare(component, clean=False):
    component = component.resolve()
    relative = component.relative_to(ROOT).as_posix()
    if relative not in COMPONENTS:
        raise ValueError('unknown workspace component: '+relative)
    for name in ('build', 'dist', 'tmp'):
        link = component/name
        target = ROOT/'build'/relative/name
        if link.is_symlink():
            raise ValueError('output directory links are no longer supported: '+str(link))
        if link.exists():
            raise ValueError('outputs must be outside component sources: '+str(link))
        if clean and target.exists():
            # The downloaded host compiler is a build prerequisite, not a guest image.
            if relative == 'space/rv32i' and name == 'tmp':
                for child in target.iterdir():
                    if child.name == 'rv32i-toolchain':
                        continue
                    if child.is_dir() and not child.is_symlink():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
            else:
                shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', type=Path)
    parser.add_argument('--clean', action='store_true')
    args = parser.parse_args()
    for name in ([args.component] if args.component else [ROOT/c for c in COMPONENTS]):
        prepare(name, args.clean)
