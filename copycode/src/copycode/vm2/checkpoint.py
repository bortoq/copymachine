#!/usr/bin/env python3
"""Immutable cooperative space checkpoints, segmented execution and forks.

Only file transport, identities and copycode-emitted metadata live here.
Guest stepping, budgets and logical IO accounting execute inside the space.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from .machine import identity, require_compatible
from .terminal import decode_terminal
from .transport import run_stream

SCHEMA = 'space-checkpoint-v1'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def manifest_layout(manifest):
    desc = manifest['boundary']
    require_compatible(desc, desc['space_bits'], manifest['processor_n'])
    monitor = manifest.get('monitor', {})
    if monitor.get('format') != 'rv32i-commit-v1':
        raise ValueError('image has no supported cooperative monitor; rebuild with segment_budget')
    return desc, monitor


def _read_field(stream, at, width):
    from .boundary import field
    offset, bit = divmod(at, 8)
    stream.seek(offset)
    return field(stream.read((bit+width+7)//8), bit, width)


def verify_state(snapshot, terminal, manifest):
    desc, monitor = manifest_layout(manifest)
    path = Path(snapshot)
    if path.stat().st_size != desc['image_bytes']:
        raise ValueError('checkpoint space size mismatch')
    with path.open('rb') as stream:
        processor = stream.read(desc['processor']['packet_bytes'])
        expected = bytes.fromhex(monitor['continuation_hex']) if terminal['kind'] == 'checkpoint' else bytes(len(processor))
        if processor != expected:
            raise ValueError('checkpoint processor does not contain the declared continuation')
        for name in ('input', 'output'):
            value = _read_field(stream, monitor[name+'_cursor_bit'], 64)
            if terminal[name+'_cursor'] != value:
                raise ValueError('checkpoint cursor disagrees with saved space')
        for name, at in monitor['counters_bit'].items():
            if terminal.get('counts', {}).get(name) != _read_field(stream, at, 64):
                raise ValueError('checkpoint counters disagree with saved space')
        if terminal['kind'] == 'checkpoint' and _read_field(stream, monitor['remaining_bit'], 32) != 0:
            raise ValueError('checkpoint was not produced at the cooperative budget boundary')


def load_checkpoint(folder, manifest, image_sha256, input_sha256):
    """Validate a checkpoint and all output ancestry before using its bytes."""
    desc, _ = manifest_layout(manifest)
    chain, seen, current = [], set(), Path(folder).resolve()
    while current is not None:
        if current in seen:
            raise ValueError('cyclic checkpoint ancestry')
        seen.add(current)
        record = json.loads((current/'checkpoint.json').read_text())
        if (record.get('schema') != SCHEMA or record.get('manifest_id') != identity(manifest)
                or record.get('image_sha256') != image_sha256
                or record.get('input_sha256') != input_sha256):
            raise ValueError('checkpoint image/input/manifest mismatch')
        for name in ('space.bin', 'stdout.bin', 'status.bin'):
            if digest(current/name) != record['sha256'][name]:
                raise ValueError('checkpoint file changed: '+name)
        if manifest.get('trace'):
            from .dynamic_trace import audit
            if digest(current/'debug.bin') != record['sha256'].get('debug.bin'):
                raise ValueError('checkpoint trace changed')
            with (current/'debug.bin').open('rb') as trace_stream:
                audited = audit(trace_stream,manifest,terminal=record['terminal'])
            if audited != record.get('trace_audit'):
                raise ValueError('checkpoint trace audit changed')
        terminal = decode_terminal((current/'status.bin').read_bytes(), desc)
        if terminal != record['terminal']:
            raise ValueError('checkpoint status metadata changed')
        verify_state(current/'space.bin', terminal, manifest)
        chain.append((current, record))
        current = Path(record['parent']).resolve() if record.get('parent') else None
    chain.reverse()
    previous = dict(input_cursor=0, output_cursor=0, counts=dict(committed=0, read_ops=0, write_ops=0))
    totals = {}
    for folder, record in chain:
        terminal = record['terminal']
        if terminal['output_cursor'] != previous['output_cursor']+(folder/'stdout.bin').stat().st_size:
            raise ValueError('checkpoint output cursor/ancestry mismatch')
        if terminal['input_cursor'] < previous['input_cursor'] or any(
                terminal['counts'][k] < previous['counts'][k] for k in previous['counts']):
            raise ValueError('checkpoint cumulative counters regressed')
        previous = terminal
        if manifest.get('trace'):
            totals = {k:totals.get(k,0)+v for k,v in record['trace_audit'].items() if isinstance(v,int)}
            if totals != record.get('trace_totals'):
                raise ValueError('checkpoint cumulative trace totals mismatch')
    if chain[-1][1]['terminal']['kind'] != 'checkpoint':
        raise ValueError('cannot resume a terminal dump')
    return chain


def execute_segments(emulator, image, manifest, input_path, directory, *,
                     max_segments=1, checkpoint_from=None, timeout=120, ticks=0):
    """Create a new run/fork; each completed segment is an immutable folder.

    Input is reopened/seeked by logical cursor before boot+input streaming.
    Output deltas form an immutable ancestry; aggregate stdout is materialised
    once per new session. Existing checkpoints and output roots are never edited.
    """
    desc, monitor = manifest_layout(manifest)
    if max_segments < 1:
        raise ValueError('max_segments must be positive')
    image = Path(image).resolve() if image is not None else None
    input_path, directory = Path(input_path).resolve(), Path(directory).resolve()
    if image is None and checkpoint_from is None:
        raise ValueError('an initial image or source checkpoint is required')
    image_hash = (digest(image) if image is not None else
                  json.loads((Path(checkpoint_from)/'checkpoint.json').read_text())['image_sha256'])
    input_hash = digest(input_path)
    chain = load_checkpoint(checkpoint_from, manifest, image_hash, input_hash) if checkpoint_from else []
    if checkpoint_from and directory.is_relative_to(Path(checkpoint_from).resolve()):
        raise ValueError('new session must be outside its source checkpoint')
    parent = chain[-1][0] if chain else None
    previous = chain[-1][1]['terminal'] if chain else dict(
        input_cursor=0, output_cursor=0, counts=dict(committed=0, read_ops=0, write_ops=0))
    if previous['input_cursor'] > input_path.stat().st_size:
        raise ValueError('checkpoint input cursor exceeds file length')
    directory.mkdir(parents=True, exist_ok=False)
    (directory/'image.json').write_text(json.dumps(manifest, indent=2)+'\n')
    reports = []
    trace_totals = chain[-1][1].get('trace_totals',{}) if chain else {}
    with (directory/'stdout.bin').open('wb') as aggregate:
        for folder, _ in chain:
            with (folder/'stdout.bin').open('rb') as source:
                shutil.copyfileobj(source, aggregate, length=65536)
        for index in range(1, max_segments+1):
            source_path = parent/'space.bin' if parent else image
            # A failed/host-killed run never publishes checkpoint.json.
            with tempfile.TemporaryDirectory(prefix='.incomplete-', dir=directory) as staging:
                stage = Path(staging)
                with source_path.open('rb') as source, input_path.open('rb', buffering=0) as inp, \
                     (stage/'space.bin').open('wb', buffering=0) as snapshot, \
                     (stage/'stdout.bin').open('wb', buffering=0) as output, \
                     (stage/'status.bin').open('wb', buffering=0) as status, \
                     (stage/'debug.bin').open('wb', buffering=0) as debug:
                    inp.seek(previous['input_cursor'])
                    result = run_stream(emulator, source, desc['space_bits'], manifest['processor_n'],
                        input_stream=inp, stdout=output, debug=debug, status=status, snapshot=snapshot,
                        description=desc, timeout=timeout, ticks=ticks)
                terminal = result.terminal
                verify_state(stage/'space.bin', terminal, manifest)
                if terminal['output_cursor'] != previous['output_cursor']+result.stdout_bytes:
                    raise ValueError('copycode output cursor does not match output delta')
                if not previous['input_cursor'] <= terminal['input_cursor'] <= input_path.stat().st_size:
                    raise ValueError('invalid copycode input cursor')
                if any(terminal['counts'][k] < previous['counts'][k] for k in previous['counts']):
                    raise ValueError('copycode cumulative counters regressed')
                metadata = dict(schema=SCHEMA, manifest_id=identity(manifest),
                    image_sha256=image_hash, input_sha256=input_hash,
                    parent=str(parent) if parent else None, terminal=terminal,
                    resources=result.metrics,
                    sha256={name: digest(stage/name) for name in ('space.bin', 'stdout.bin', 'status.bin','debug.bin')})
                if manifest.get('trace'):
                    from .dynamic_trace import audit
                    with (stage/'debug.bin').open('rb') as trace_stream:
                        metadata['trace_audit'] = audit(trace_stream,manifest,terminal=terminal)
                    trace_totals = {k:trace_totals.get(k,0)+v for k,v in metadata['trace_audit'].items()
                                    if isinstance(v,int)}
                    metadata['trace_totals'] = trace_totals
                (stage/'checkpoint.json').write_text(json.dumps(metadata, indent=2)+'\n')
                destination = directory/f'segment-{index:06d}'
                # Atomic publication within one filesystem; source is untouched.
                stage.rename(destination)
            with (destination/'stdout.bin').open('rb') as source:
                shutil.copyfileobj(source, aggregate, length=65536)
            aggregate.flush()
            parent, previous = destination, terminal
            reports.append(dict(path=str(destination), terminal=terminal))
            if terminal['kind'] == 'terminal':
                break
    return dict(directory=str(directory), checkpoint=str(parent), terminal=previous,
                segments=reports, complete=previous['kind'] == 'terminal')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path, nargs='?', help='initial image; optional with --from')
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True, help='new output session directory')
    parser.add_argument('--emulator', type=Path, required=True)
    parser.add_argument('--from', dest='checkpoint_from', type=Path)
    parser.add_argument('--max-segments', type=int, default=1)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    try:
        result = execute_segments(args.emulator, args.image, json.loads(args.manifest.read_text()),
            args.input, args.directory, max_segments=args.max_segments,
            checkpoint_from=args.checkpoint_from, timeout=args.timeout)
        print(json.dumps(result, indent=2))
        if not result['complete']:
            return 75
        terminal = result['terminal']
        return terminal['exit_code'] & 255 if terminal['reason'] == 'idle' and terminal['guest_status'] == 10 else 125
    except (OSError, ValueError, KeyError, TimeoutError) as error:
        import sys
        print(str(error), file=sys.stderr)
        return 125


if __name__ == '__main__':
    raise SystemExit(main())
