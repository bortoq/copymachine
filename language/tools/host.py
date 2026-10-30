"""Host 32-bit pForth with a large memory pool: the first executor of the language definition.

The same pinned pForth core, port and prepared dictionary as forth/scripts/pforth/host32.py
(which is imported for its build recipe, not changed); only the pool of ALLOCATE and the free areas of the dictionary are larger,
because the definition of the language is compiled with the sizes of main.fth (fc-sizes)
and the host pForth of forth has a pool of 64 KiB.
The executable is rebuilt when its compile command or any source changes.
"""
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import paths

sys.path[:0] = [str(paths.BOOT)]
from common import PORT, flags, sources  # noqa: E402  (boot/common.py)

POOL_BYTES = int(os.environ.get('LANGUAGE_POOL_BYTES', 16 * 1024 * 1024))


# The prepared dictionary of forth (runtime/pforth/pfdicdat.h) keeps 32 KiB of free names and 64 KiB
# of free code; the definition of the language, loaded into the host as native words, left 856 bytes of
# the code free at 14.12 (past the end pForth fails with a segmentation fault, without a message). The
# host takes a copy of the dictionary image with larger free areas (zeros after the image); the image
# itself and the guest are not changed.
EXTRA_NAMES, EXTRA_CODE = 64 * 1024, 256 * 1024


def dictionary(target):
    """The directory of the copy of pfdicdat.h with the larger arrays MinDicNames and MinDicCode."""
    text = (PORT / 'pfdicdat.h').read_text()
    for name, extra in (('MinDicNames', EXTRA_NAMES), ('MinDicCode', EXTRA_CODE)):
        text, count = re.subn(r'(static uint8_t %s\[)(\d+)(\])' % name,
                              lambda m, extra=extra: m.group(1) + str(int(m.group(2)) + extra) + m.group(3), text)
        assert count == 1, name
    directory = target / 'dictionary'
    directory.mkdir(parents=True, exist_ok=True)
    if not (directory / 'pfdicdat.h').is_file() or (directory / 'pfdicdat.h').read_text() != text:
        (directory / 'pfdicdat.h').write_text(text)
    return directory


def build():
    target = paths.BUILD / 'host'
    executable = target / 'pforth32'
    host_flags = [('-DPF_MEM_POOL_SIZE=' + str(POOL_BYTES)) if f.startswith('-DPF_MEM_POOL_SIZE=') else f
                  for f in flags(False)]
    command = shlex.split(os.environ.get('CC', 'cc')) + ['-I' + str(dictionary(target))] + [
        '-m32', '-O2', '-std=c99', '-ffreestanding', '-nostdlib', '-fno-pie', '-no-pie',
        '-fno-stack-protector', '-Wl,--build-id=none', '-Wl,-e,_start', '-w',
    ] + host_flags + [str(p) for p in sources(False)] + [str(PORT / 'bootstrap/linux32.c'), '-o', str(executable)]
    digest = hashlib.sha256(json.dumps(command).encode())
    for path in sorted(set(sources(False) + [PORT / 'bootstrap/linux32.c']) |
                       set(PORT.rglob('*.h')) | set((paths.BOOT / 'csrc').rglob('*.h'))):
        digest.update(str(path).encode() + Path(path).read_bytes())
    stamp = target / 'build.sha256'
    if executable.is_file() and stamp.is_file() and stamp.read_text() == digest.hexdigest():
        return executable
    target.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError('32-bit host pForth build failed:\n' + result.stderr[-3000:])
    stamp.write_text(digest.hexdigest())
    return executable


if __name__ == '__main__':
    print(build())


def run(executable, data, timeout):
    """(returncode, stdout, stderr) of the pForth fed with data. The stdout goes through a file: pForth writes it
    a byte at a time, and a pipe read on another CPU (parallel checks) gets single bytes, gigabytes of chunks."""
    with tempfile.TemporaryFile() as out:
        result = subprocess.run([str(executable)], input=data, stdout=out, stderr=subprocess.PIPE, timeout=timeout,
                                check=False)
        out.seek(0)
        return result.returncode, out.read(), result.stderr
