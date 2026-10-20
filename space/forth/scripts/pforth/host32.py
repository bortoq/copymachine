"""32-bit host pForth with the image's dictionary: a fast stand-in for the guest.

The same pinned pForth core, port, prepared dictionary (pfdicdat.h), memory
pool and dictionary reserves as the RV32I image; only the C target differs
(i386 with Linux system calls, no libc). Tests run guest Forth libraries on
it quickly; the image itself still runs them for the record. The executable
is rebuilt when its compile command or any source changes."""
import hashlib, json, os, shlex, subprocess
from pathlib import Path

from common import ROOT, PORT, sources, flags
from copycode.hostpaths import output_dir


def build():
    target = output_dir(ROOT) / 'host32'
    executable = target / 'pforth32'
    command = shlex.split(os.environ.get('CC', 'cc')) + [
        '-m32', '-O2', '-std=c99', '-ffreestanding', '-nostdlib', '-fno-pie', '-no-pie',
        '-fno-stack-protector', '-Wl,--build-id=none', '-Wl,-e,_start', '-w',
    ] + flags(False) + [str(path) for path in sources(False)] + [str(PORT / 'bootstrap/linux32.c'),
                                                                '-o', str(executable)]
    digest = hashlib.sha256(json.dumps(command).encode())
    for path in sorted(set(sources(False) + [PORT / 'bootstrap/linux32.c']) |
                       set(PORT.rglob('*.h')) | set((ROOT / 'third_party/pforth/csrc').rglob('*.h'))):
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
