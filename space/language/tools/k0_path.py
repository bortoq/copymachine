#!/usr/bin/env python3
"""Print the path of the stream K0: the kernel of space/forth compiled by its model.

K0 is the reference for L0 (14.1: L0 equals K0 byte for byte before any change of
the definition). The model (space/forth/scripts/forthc/model.py) compiles the copy
of the sources in space/language/src; the stream is built once and kept in the build
directory under a name that carries the digest of the sources and of the model.
Usage: k0_path.py [--rebuild]
"""
import hashlib, sys, time

import paths


def digest():
    h = hashlib.sha256()
    for name in paths.KERNEL_FILES:
        h.update(name.encode() + (paths.SRC / name).read_bytes())
    h.update((paths.FORTH / 'scripts/forthc/model.py').read_bytes())
    return h.hexdigest()[:16]


def k0():
    target = paths.BUILD / ('K0-' + digest() + '.boot')
    if target.is_file():
        return target
    sys.path[:0] = [str(paths.FORTH / 'scripts')]
    from forthc import model  # the model is only the reference
    start = time.monotonic()
    stream = model.Compiler().compile_source(paths.text(paths.KERNEL_FILES), 'main')
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_bytes(stream)
    temporary.replace(target)
    print(f'K0 built by the model: {len(stream)} bytes ({time.monotonic() - start:.0f} s)', file=sys.stderr)
    return target


if __name__ == '__main__':
    print(k0())
