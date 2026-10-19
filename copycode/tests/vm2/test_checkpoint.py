#!/usr/bin/env python3
"""Archive publication, identity, immutable fork and incomplete-run checks."""
import json
from pathlib import Path
import os
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EMULATOR = Path(os.environ.get('SPACE_EMULATOR', ROOT.parent/'vm2/space')).resolve()
sys.path.insert(0, str(ROOT/'compat/vm2'))
from boundary import Format
from terminal import TerminalFragment, numeric
from checkpoint import execute_segments, digest

with tempfile.TemporaryDirectory() as directory:
    tmp = Path(directory)
    f = Format(65520, 8)
    committed, reads, writes, inp, out, remaining = 2048, 2112, 2176, 2240, 2304, 2368
    shared = dict(snapshot=True, input_cursor_address=inp, output_cursor_address=out,
                  counter_addresses=dict(committed=committed, read_ops=reads, write_ops=writes))
    final = TerminalFragment(65520, 8, 32768, **shared)
    continuation = [(f.layer_bits, 0, final.entry)]
    first = TerminalFragment(65520, 8, 16384, reason='limit', continuation=continuation, **shared)
    image = tmp/'image'
    with image.open('wb') as stream:
        stream.write(f.layer([(f.layer_bits, 0, first.entry)]))
        stream.seek(committed//8); stream.write(numeric(1,64))
        stream.seek(first.base//8); stream.write(first.data)
        stream.seek(final.base//8); stream.write(final.data)
    manifest = dict(boundary=f.description, processor_n=8, monitor=dict(
        format='rv32i-commit-v1', segment_budget=1, remaining_bit=remaining,
        continuation_hex=f.layer(continuation).hex(), input_cursor_bit=inp, output_cursor_bit=out,
        counters_bit=dict(committed=committed, read_ops=reads, write_ops=writes)))
    input_path = tmp/'input'; input_path.write_bytes(b'unchanged input')
    first_run = execute_segments(EMULATOR, image, manifest, input_path, tmp/'first')
    assert not first_run['complete']
    checkpoint = Path(first_run['checkpoint'])
    before = {p.name: digest(p) for p in checkpoint.iterdir()}
    for name in ('left', 'right'):
        result = execute_segments(EMULATOR, None, manifest, input_path, tmp/name,
                                  checkpoint_from=checkpoint)
        assert result['complete'] and result['terminal']['counts']['committed'] == 1
    assert before == {p.name:digest(p) for p in checkpoint.iterdir()}
    assert (tmp/'left/segment-000001/space.bin').read_bytes() == (tmp/'right/segment-000001/space.bin').read_bytes()
    corrupt = tmp/'corrupt'; shutil.copytree(checkpoint, corrupt)
    with (corrupt/'space.bin').open('r+b') as stream:
        stream.seek(4000); stream.write(b'changed')
    try:
        execute_segments('/missing-emulator', image, manifest, input_path, tmp/'bad',
                         checkpoint_from=corrupt)
    except ValueError:
        pass
    else:
        raise AssertionError('modified checkpoint accepted')
    assert not (tmp/'bad').exists()
    try:
        execute_segments(EMULATOR, image, manifest, input_path, tmp/'truncated', ticks=1)
    except ValueError:
        pass
    else:
        raise AssertionError('host tick truncation published a checkpoint')
    assert not list((tmp/'truncated').rglob('checkpoint.json'))
    assert not list((tmp/'truncated').glob('.incomplete-*'))
    print('checkpoint: SPT2, immutable forks, corruption rejection and no publication on host stop passed')
