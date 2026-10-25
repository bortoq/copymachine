"""Host 32-bit pForth with a large memory pool: the first executor of the language definition.

The same pinned pForth core, port and prepared dictionary as space/forth/scripts/pforth/host32.py
(which is imported for its build recipe, not changed); only the pool of ALLOCATE is larger,
because the definition of the language is compiled with the sizes of main.fth (fc-sizes)
and the host pForth of space/forth has a pool of 64 KiB.
The executable is rebuilt when its compile command or any source changes.
"""
import hashlib, json, os, shlex, subprocess, sys
from pathlib import Path

import paths
sys.path[:0] = [str(paths.FORTH / 'scripts/pforth')]
from common import PORT, sources, flags  # noqa: E402  (space/forth/scripts/pforth/common.py)

POOL_BYTES = int(os.environ.get('LANGUAGE_POOL_BYTES', 16 * 1024 * 1024))


def build():
    target = paths.BUILD / 'host'
    executable = target / 'pforth32'
    host_flags = [('-DPF_MEM_POOL_SIZE=' + str(POOL_BYTES)) if f.startswith('-DPF_MEM_POOL_SIZE=') else f
                  for f in flags(False)]
    command = shlex.split(os.environ.get('CC', 'cc')) + [
        '-m32', '-O2', '-std=c99', '-ffreestanding', '-nostdlib', '-fno-pie', '-no-pie',
        '-fno-stack-protector', '-Wl,--build-id=none', '-Wl,-e,_start', '-w',
    ] + host_flags + [str(p) for p in sources(False)] + [str(PORT / 'bootstrap/linux32.c'), '-o', str(executable)]
    digest = hashlib.sha256(json.dumps(command).encode())
    for path in sorted(set(sources(False) + [PORT / 'bootstrap/linux32.c']) |
                       set(PORT.rglob('*.h')) | set((paths.FORTH / 'third_party/pforth/csrc').rglob('*.h'))):
        digest.update(str(path).encode() + Path(path).read_bytes())
    stamp = target / 'build.sha256'
    if executable.is_file() and stamp.is_file() and stamp.read_text() == digest.hexdigest():
        return executable
    target.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('32-bit host pForth build failed:\n' + result.stderr[-3000:])
    stamp.write_text(digest.hexdigest())
    return executable


if __name__ == '__main__':
    print(build())
