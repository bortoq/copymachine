"""Real looping RV32I snapshots, logical IO cursors and immutable forks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]/'legacy/copy-space'
EMULATOR = Path(os.environ.get("SPACE_EMULATOR", str(ROOT.parent.parent/"space/vm2/space")))
sys.path.insert(0, str(ROOT/'modules'))
sys.path.insert(0, str(ROOT/'tests'))
from rv32i import Layout, REGS
from rv32i_bulk import BulkImage
from rv32i_reference import execute
from checkpoint import execute_segments, digest
from boundary import Format, field, iter_boot
import io

OUT = Path('tmp/dynamic-checkpoint-tests')
OUT.mkdir(parents=True, exist_ok=True)
# Unique session folder: keep reviewable artifacts from each test invocation.
import tempfile
out = Path(tempfile.mkdtemp(prefix='run-', dir=OUT))

def addi(rd, rs, n): return (n & 4095) << 20 | rs << 15 | rd << 7 | 0x13
def bne(rs, offset):
    n = offset & 8191
    return ((n >> 12 & 1) << 31 | (n >> 5 & 63) << 25 | rs << 15 | 1 << 12 |
            (n >> 1 & 15) << 8 | (n >> 11 & 1) << 7 | 0x63)
words = [addi(5,0,3), addi(10,0,0), addi(11,0,1024), addi(12,0,2), addi(17,0,63), 0x73,
         addi(12,10,0), addi(10,0,1), addi(17,0,64), 0x73,
         addi(5,5,-1), bne(5,-40), addi(10,0,9), addi(17,0,93), 0x73]
program = b''.join(x.to_bytes(4,'little') for x in words)
data = b'A\0\xffBC'
inp = out/'input.bin'; inp.write_bytes(data)
images = {}
for name, budget in [('whole', 1000), ('split',7)]:
    raw, manifest = BulkImage(io=True,memory_bytes=65536,layout=Layout(8*1024*1024),
                             segment_budget=budget).build().encode(program)
    path = out/(name+'.bin'); path.write_bytes(raw)
    path.with_name(path.name+'.json').write_text(json.dumps(manifest))
    images[name] = path, manifest
whole_image, whole_manifest = images['whole']
whole = execute_segments(EMULATOR, whole_image, whole_manifest,
                         inp, out/'whole', max_segments=1)
assert whole['complete'], whole
split_image, manifest = images['split']
first = execute_segments(EMULATOR, split_image, manifest,
                         inp, out/'first', max_segments=1)
assert not first['complete'] and first['terminal']['counts']['committed'] == 7
assert first['terminal']['input_cursor'] == 2, first
checkpoint = Path(first['checkpoint'])
source_hashes = {p.name:digest(p) for p in checkpoint.iterdir() if p.is_file()}
left = execute_segments(EMULATOR, split_image, manifest,
                        inp, out/'left', max_segments=20, checkpoint_from=checkpoint)
right = execute_segments(EMULATOR, split_image, manifest,
                         inp, out/'right', max_segments=20, checkpoint_from=checkpoint)
assert left['complete'] and right['complete']
assert {p.name:digest(p) for p in checkpoint.iterdir() if p.is_file()} == source_hashes
expected_io = dict(input=data, output=b'')
frames, memory, fetches = execute(program, registers={2:65520}, memory_bytes=65536, io=expected_io)
assert expected_io['output'] == data and expected_io['exit_code'] == 9
snapshots = []
for run in [whole,left,right]:
    assert (Path(run['directory'])/'stdout.bin').read_bytes() == data
    terminal = run['terminal']
    assert terminal['input_cursor'] == 5 and terminal['output_cursor'] == 5
    assert terminal['counts']['read_ops'] == 3 and terminal['counts']['write_ops'] == 3
    assert terminal['exit_code'] == 9 and terminal['guest_status'] == 10
    raw = (Path(run['checkpoint'])/'space.bin').read_bytes()
    registers = [field(raw, REGS+j*32,32) for j in range(34)]
    assert registers == frames[-1], (registers, frames[-1])
    start=manifest['guest_memory_bit']//8
    assert raw[start:start+65536] == memory
    snapshots.append(raw)
assert whole['terminal']['counts'] == left['terminal']['counts'] == right['terminal']['counts']
assert whole['terminal']['counts']['committed'] == len(fetches)
# Forked final spaces are byte-identical; the differently-budgeted baseline
# agrees on all guest state, IO and cumulative event counts.
assert snapshots[1] == snapshots[2]
print('OK looping/branching RV32I: uninterrupted == segmented == two immutable forks', flush=True)

# Verify installation independently: the wire's last processor packet must
# equal the saved continuation; a transient processor reads back all other
# memory before executing any application instruction.
f = Format(manifest['boundary']['space_bits'],256)
raw = (checkpoint/'space.bin').read_bytes()
packets = list(iter_boot(io.BytesIO(raw), f.space_bits,256))
assert packets[-1] == raw[:f.layer_bytes]
start = f.layer_bytes
first_n = min(f.max_bytes, f.space_bytes-start)
second_start = start+first_n
second_n = f.space_bytes-second_start
assert 0 < second_n <= f.max_bytes
rows = [(first_n*8,f.devices['stdout'],start*8),
        (f.a,f.z+f.a,7*f.isz+f.z),
        (f.z,0,6*f.isz+f.z),
        (4*f.isz,f.isz,12*f.isz),
        (f.z,5*f.isz,11*f.isz+f.z),
        (0,0,12*f.isz), (0,second_n*8,0), (0,second_start*8,0),
        (0,0,0),(0,0,0),(0,0,0),(0,6*f.isz,0)]
packets[-1] = f.layer(rows)
probe = subprocess.run([str(EMULATOR),'-s',str(f.space_bits),'-p','256'],
                       input=b''.join(packets),capture_output=True,timeout=15)
assert probe.returncode == 0 and not probe.stderr
assert probe.stdout == raw[f.layer_bytes:]
print('OK exact snapshot install: continuation packet + byte-for-byte nonprocessor readback',flush=True)

# Mismatch/corruption rejection precedes launch and never edits the source.
changed = out/'changed-input';changed.write_bytes(data+b'X')
for label, source_input, chosen_manifest, damage in [
    ('input', changed, manifest, False),
    ('manifest', inp, dict(manifest, entry=4), False),
    ('snapshot', inp, manifest, True)]:
    if damage:
        corrupt=out/'corrupt'
        import shutil
        shutil.copytree(checkpoint,corrupt)
        with (corrupt/'space.bin').open('r+b') as stream:
            stream.seek(4000);stream.write(b'X')
        chosen_checkpoint=corrupt
    else:chosen_checkpoint=checkpoint
    try:
        execute_segments('/nonexistent-emulator', split_image, chosen_manifest, source_input,
                         out/('bad-'+label), checkpoint_from=chosen_checkpoint)
    except ValueError:pass
    else:raise AssertionError(label+' accepted')
    assert not (out/('bad-'+label)).exists()
assert {p.name:digest(p) for p in checkpoint.iterdir() if p.is_file()} == source_hashes
print('OK immutable checkpoint and explicit input/manifest/snapshot rejection',flush=True)
print('Artifacts:',out,flush=True)

# Counter arithmetic must propagate beyond a 32-bit boundary.
from terminal import numeric
from transport import run_stream
short_program = b''.join(w.to_bytes(4,'little') for w in [addi(10,0,7),addi(17,0,93),0x73])
raw,m = BulkImage(io=True,memory_bytes=65536,layout=Layout(8*1024*1024),segment_budget=100).build().encode(short_program, image_bytes=4*1024*1024+len(short_program))
assert m["monitor"]["checkpoint_entry"] >= m["guest_memory_bit"]+m["guest_memory_bytes"]*8
raw = bytearray(raw)
at = m['monitor']['counters_bit']['committed']//8
raw[at:at+8] = numeric((1<<32)-2,64)
r = run_stream(EMULATOR,io.BytesIO(raw),m['boundary']['space_bits'],256)
assert r.terminal['counts']['committed'] == (1<<32)+1
print('OK cumulative counter carry across 32 bits',flush=True)

# CLI checkpoint + resume uses the same immutable archive path.
command = [sys.executable, '-B', str(ROOT/'scripts/rv32i/run.py'), str(split_image),
           '--new-emulator', '--in', str(inp)]
cli = subprocess.run(command+['--segments', str(out/'cli-first')], capture_output=True, timeout=30)
assert cli.returncode == 75, cli
cli = subprocess.run(command+['--segments', str(out/'cli-resume'), '--max-segments', '20',
           '--checkpoint-from', str(out/'cli-first/segment-000001')],capture_output=True,timeout=30)
assert cli.returncode == 9 and (out/'cli-resume/stdout.bin').read_bytes() == data, cli
print('OK CLI cooperative stop 75 and resumed guest exit 9',flush=True)
