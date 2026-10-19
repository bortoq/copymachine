"""Execute the Forth four-index encoder and compare its bytes with Python."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/pforth'))
from common import RV32I_ROOT
import dependencies
from copycode.hostpaths import output_dir
from copycode.vm1.machine import Format, put
from guest_support import library_image

sources = {name: (dependencies.COPYCODE_ROOT / 'forth' / name).read_bytes()
           for name in ('bitfields.fth', 'instructions.fth')}
lines = []
lines += ['create indices 8 cells allot', 'create encoded 16 allot',
          ': encoded-dump encoded 16 type cr ;']
expected = []


def row(values):
    for i, value in enumerate(values):
        low, high = value & 0xffffffff, value >> 32
        lines.append(f'{low} indices {2*i} cells + ! {high} indices {2*i+1} cells + !')


def valid(values, at, width):
    row(values)
    lines.extend(['encoded 16 165 fill',
                  f'indices encoded 16 {at} {width} cc-instruction!',
                  'encoded-dump', 'depth . cr'])
    data = bytearray([165] * 16)
    for i, value in enumerate(values):
        put(data, at + i * width, width, value)
    expected.extend([bytes(data) + b'\n', b'0 \n'])
    return data


# A legal memory copy in the production 27-bit ABI; field starts are unaligned.
fmt = Format(size=134217712)
values = (800, 808, 1024, 1032)
fmt.validate([values])
data = valid(values, 3, fmt.a)
# Smallest encoding, last possible bit offset, zero fields and no padding loss.
data = valid((0, 1, 0, 1), 124, 1)

# The final endpoint overflows: earlier valid endpoints must not be written.
row((1, 2, 3, 1 << 27))
invalid = [
    ('indices encoded 16 0 27 cc-instruction!', -24),
    ('indices encoded 16 0 0 cc-instruction!', -24),
    ('indices encoded 16 0 65 cc-instruction!', -24),
    ('indices encoded 16 -1 1 cc-instruction!', -9),
    ('indices encoded 16 21 27 cc-instruction!', -9),
    ('indices encoded 16 0 64 cc-instruction!', -9),
    ('indices encoded -1 0 1 cc-instruction!', -9),
    ('indices indices 32 0 1 cc-instruction!', -9),
]
for i, (call, code) in enumerate(invalid):
    lines += [f': bad-instruction-{i} {call} ;',
              f"' bad-instruction-{i} catch . cr", 'encoded-dump']
    expected += [f'{code} \n'.encode(), bytes(data) + b'\n']
lines += ['indices 32 type cr', 'depth . cr', 'bye']
# Alias rejection must also preserve the source row.
expected += [b''.join(value.to_bytes(8, 'little') for value in (1, 2, 3, 1 << 27)) + b'\n',
             b'0 \n', b'\n']
task = ('\n'.join(lines) + '\n').encode()
assert all(len(line) < 255 for line in task.splitlines())
folder = output_dir(ROOT) / 'verification/instructions'
folder.mkdir(parents=True, exist_ok=True)
(folder / 'result.json').unlink(missing_ok=True)
(folder / 'input.fth').write_bytes(task)
timeout = max(1, int(os.environ.get('PFORTH_INSTRUCTION_SECONDS', '600')) - 10)
image = library_image(['bitfields.fth', 'instructions.fth'])
with (folder / 'stdout.bin').open('wb') as stdout, (folder / 'stderr.bin').open('wb') as stderr:
    result = subprocess.run([str(ROOT / 'pforth'), 'run', str(image)],
                            input=task, stdout=stdout, stderr=stderr, timeout=timeout)
actual = (folder / 'stdout.bin').read_bytes()
errors = (folder / 'stderr.bin').read_bytes()
assert result.returncode == 0, (result.returncode, actual[-1000:], errors[-1000:])
assert actual == b''.join(expected), (actual, b''.join(expected))
assert not errors, errors
(folder / 'result.json').write_text(json.dumps(dict(
    sources_sha256={name: hashlib.sha256(data).hexdigest() for name, data in sources.items()},
    library_manifest_sha256=hashlib.sha256((image / 'manifest.json').read_bytes()).hexdigest(),
    input_sha256=hashlib.sha256(task).hexdigest(),
    stdout_sha256=hashlib.sha256(actual).hexdigest(),
    valid_cases=2, rejected_cases=len(invalid), stack_depth=0,
    guest_execution=True, result='PASS'), indent=2) + '\n')
print('PASS guest Forth instructions: 2 byte-exact cases, 8 rejected cases, balanced stack')
