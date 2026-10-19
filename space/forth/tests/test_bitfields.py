"""Execute the Forth image codec in the guest; compare with independent Python bytes."""
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/pforth'))
from common import RV32I_ROOT
import dependencies
from copycode.hostpaths import output_dir
from copycode.vm1.machine import field, put

source_path = dependencies.COPYCODE_ROOT / 'forth/bitfields.fth'
source = source_path.read_text()
lines = [source, 'create codec-buffer 16 allot',
         ': codec-dump codec-buffer 16 type cr ;']
expected = []
rng = random.Random(1909)
cases = 0


def check(at, width, value, *, reset=True):
    global cases, data
    if reset:
        byte = rng.randrange(256)
        data = bytearray([byte] * 16)
        lines.append(f'codec-buffer 16 {byte} fill')
    put(data, at, width, value)
    low, high = value & 0xffffffff, value >> 32
    lines.extend([
        f'{low} {high} codec-buffer 16 {at} {width} cc-field!',
        f'codec-buffer 16 {at} {width} cc-field@ swap . . cr',
        'codec-dump',
    ])
    observed = field(data, at, width)
    def signed(value):
        return value if value < 1 << 31 else value - (1 << 32)
    expected.extend([f'{signed(observed & 0xffffffff)} {signed(observed >> 32)} \n'.encode(),
                     bytes(data) + b'\n'])
    cases += 1


for i, width in enumerate((0, 1, 32, 33, 64)):
    # Cover the empty field, partial byte, single/double-cell boundary and
    # full double value. Force the top bit to exercise unsigned cells too.
    value = (rng.getrandbits(width) | (1 << (width - 1))) if width else 0
    check(i % 8, width, value)
# Sequential overlapping fields must preserve every bit outside each write.
check(7, 9, 0, reset=False)
check(8, 32, 0x80000001, reset=False)
check(128, 0, 0, reset=False)

# Errors must occur before mutation. CATCH is invoked on no-argument words,
# so its restored data stack cannot hide leaked arguments from a test call.
invalid = [
    ('0 0 codec-buffer 16 0 65 cc-field!', -24),
    ('0 0 codec-buffer 16 0 -1 cc-field!', -24),
    ('0 0 codec-buffer 16 -1 1 cc-field!', -9),
    ('0 0 codec-buffer 16 128 1 cc-field!', -9),
    ('0 0 codec-buffer -1 0 1 cc-field!', -9),
    ('0 0 codec-buffer 268435456 0 1 cc-field!', -9),
    ('256 0 codec-buffer 16 3 8 cc-field!', -24),
    ('0 1 codec-buffer 16 3 32 cc-field!', -24),
    ('0 2 codec-buffer 16 3 33 cc-field!', -24),
    ('1 0 codec-buffer 16 128 0 cc-field!', -24),
    ('codec-buffer 16 127 2 cc-field@ 2drop', -9),
    ('codec-buffer 16 0 65 cc-field@ 2drop', -24),
]
for i, (call, code) in enumerate(invalid):
    lines.extend([f': codec-bad-{i} {call} ;',
                  f"' codec-bad-{i} catch . cr", 'codec-dump'])
    expected.extend([f'{code} \n'.encode(), bytes(data) + b'\n'])
lines.extend(['depth . cr', 'bye'])
expected.extend([b'0 \n', b'\n'])
task = ('\n'.join(lines) + '\n').encode()
assert all(len(line) < 255 for line in task.splitlines())
folder = output_dir(ROOT) / 'verification/bitfields'
folder.mkdir(parents=True, exist_ok=True)
(folder / 'input.fth').write_bytes(task)
command = [str(ROOT / 'pforth'), 'run', str(output_dir(ROOT) / 'initialized')]
timeout = max(1, int(os.environ.get('PFORTH_BITFIELD_SECONDS', '600')) - 10)
with (folder / 'stdout.bin').open('wb') as stdout, (folder / 'stderr.bin').open('wb') as stderr:
    result = subprocess.run(command, input=task, stdout=stdout, stderr=stderr, timeout=timeout)
actual = (folder / 'stdout.bin').read_bytes()
errors = (folder / 'stderr.bin').read_bytes()
assert result.returncode == 0, (result.returncode, actual[-1000:], errors[-1000:])
assert actual == b''.join(expected), (actual, b''.join(expected))
assert not errors, errors
(folder / 'result.json').write_text(json.dumps(dict(
    source_sha256=hashlib.sha256(source.encode()).hexdigest(),
    input_sha256=hashlib.sha256(task).hexdigest(),
    stdout_sha256=hashlib.sha256(actual).hexdigest(),
    valid_cases=cases, rejected_cases=len(invalid), stack_depth=0,
    guest_execution=True, result='PASS'), indent=2) + '\n')
print(f'PASS guest Forth bitfields: {cases} byte-exact cases, {len(invalid)} rejected cases, balanced stack')
