#!/usr/bin/env python3
"""Streaming, live IO, split reports, failure cleanup and bounded relay memory."""
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tracemalloc

ROOT = Path(__file__).resolve().parents[2]
EMULATOR = Path(os.environ.get('SPACE_EMULATOR', ROOT.parent/'vm2/space')).resolve()
sys.path.insert(0, str(ROOT/'compat/vm2'))
from boundary import Format, iter_boot, boot_stream
from machine import space_bits_for_bytes, require_compatible, describe
from terminal import TerminalFragment, attach_terminal, decode_terminal, numeric
from transport import run_stream


class Counter:
    def __init__(self):
        self.n, self.hash = 0, hashlib.sha256()
    def write(self, data):
        self.n += len(data)
        self.hash.update(data)
        return len(data)


def fixture(path, bits=65520, *, snapshot=False, live=False, exit_code=7, sparse_size=None):
    f = Format(bits, 8)
    prompt, buf, codeword, cursor = 8000, 8104, 8200, 8304
    layer2, layer3, halt, zero = [f.layer_bits*i for i in (2, 3, 4, 5)]
    image = bytearray(2048)
    def put(at, data):
        image[at//8:at//8+len(data)] = data
    put(prompt, b'go?')
    put(buf, b'\x00\xffX')
    put(codeword, numeric(exit_code, 32))
    put(cursor, numeric(123, 64))
    put(0, f.layer([(24, f.devices['stdout'], prompt),
                    (24, f.devices['debug'], buf), (f.layer_bits, 0, layer2)]))
    put(layer2, f.layer(([(24, buf, f.devices['stdin'])] if live else [])+
                        [(f.layer_bits, 0, layer3)]))
    put(layer3, f.layer([(24, f.devices['stdout'], buf), (f.layer_bits, 0, halt)]))
    put(halt, f.layer([(f.layer_bits, 0, zero)]))
    fragment = TerminalFragment(bits, 8, 16384, snapshot=snapshot,
                                exit_address=codeword, input_cursor_address=cursor)
    with path.open('wb') as target:
        target.write(image)
        target.write(fragment.data)
        if sparse_size:
            target.truncate(sparse_size)
        target.seek(halt//8)
        target.write(f.layer([(f.layer_bits, 0, fragment.entry)]))
    return f, halt


with tempfile.TemporaryDirectory() as directory:
    tmp = Path(directory)
    image = tmp/'image'
    f, halt = fixture(image, snapshot=True, live=True)
    r, w = os.pipe()
    output, debug, status, snapshot = io.BytesIO(), io.BytesIO(), io.BytesIO(), io.BytesIO()
    class PromptSink:
        fired = False
        def write(self, data):
            output.write(data)
            if b'go?' in output.getvalue() and not self.fired:
                self.fired = True
                os.write(w, b'A\x00\xff')
            return len(data)
    try:
        with image.open('rb') as source, os.fdopen(r, 'rb', buffering=0) as app_input:
            result = run_stream(EMULATOR, source, 65520, 8, input_stream=app_input,
                                stdout=PromptSink(), debug=debug, status=status,
                                snapshot=snapshot, timeout=5)
        # Writer remains open: child exit must cancel input readiness waiting.
        assert output.getvalue() == b'go?A\x00\xff'
        assert debug.getvalue() == b'\x00\xffX'
        assert result.terminal['exit_code'] == 7 and result.terminal['input_cursor'] == 123
        assert result.terminal['output_cursor'] is None
        assert len(snapshot.getvalue()) == f.space_bytes
        assert snapshot.getvalue()[:f.layer_bytes] == bytes(f.layer_bytes)
        assert decode_terminal(status.getvalue(), f.description) == result.terminal
    finally:
        os.close(w)
    print('ok: live prompt/input, binary stdout, debug, status and snapshot separated; open input cancelled')

    # Streaming installation preserves padding bits, accepts short reader chunks.
    class ShortReader(io.BytesIO):
        def read(self, n=-1):
            assert 0 <= n <= 65536
            return super().read(min(n, 17))
    for bits, slots in [(65520, 8), (30000, 9)]:
        f2 = Format(bits, slots)
        raw = bytes((i*17)%256 for i in range(1000))
        assert b''.join(iter_boot(ShortReader(raw), bits, slots)) == boot_stream(raw, bits, slots)
    for raw in [bytes(f.space_bytes+1), bytes(f.space_bytes-1)+b'\x01']:
        try:
            list(iter_boot(io.BytesIO(raw), 65520 if len(raw)>f.space_bytes else 65518, 8))
        except ValueError:
            pass
        else:
            raise AssertionError('invalid image accepted')
    print('ok: incremental boot, short source reads and invalid image rejection')

    # Terminal status without a dump, including dynamic guest exit bits.
    fixture(image, snapshot=False)
    with image.open('rb') as source:
        result = run_stream(EMULATOR, source, 65520, 8, stdout=Counter(), debug=Counter())
    assert result.terminal['exit_code'] == 7 and result.snapshot_bytes == 0
    cli = subprocess.run([sys.executable, str(ROOT/'compat/vm2/transport.py'), str(image),
                           '--emulator', str(EMULATOR), '-s', '65520', '-p', '8'],
                          input=b'', capture_output=True, timeout=5)
    assert cli.returncode == 7 and cli.stdout == b'go?\x00\xffX' and cli.stderr == b'\x00\xffX', cli
    print('ok: guest exit without snapshot; CLI propagates exit code')

    # File patching leaves the source intact; no zero-filled space buffer.
    source_image = tmp/'raw'
    fixture(source_image)
    # Construct a plain source whose halt still points at a zero layer.
    with source_image.open('r+b') as stream:
        stream.seek(halt//8)
        stream.write(f.layer([(f.layer_bits, 0, f.layer_bits*5)]))
    before = source_image.read_bytes()
    patched = tmp/'patched'
    with source_image.open('rb') as source, patched.open('w+b') as target:
        attach_terminal(source, target, 65520, 8, halt, exit_address=8200)
    assert source_image.read_bytes() == before
    with patched.open('rb') as source:
        assert run_stream(EMULATOR, source, 65520, 8).terminal['exit_code'] == 7
    print('ok: immutable source and bounded terminal attachment')

    # Explicit continuation and metadata can be transported and restored;
    # this is a static boundary, not dynamic segment scheduling.
    f, halt = fixture(image)
    resume = TerminalFragment(65520, 8, 32768, exit_code=9)
    first = TerminalFragment(65520, 8, 16384, snapshot=True, reason='limit',
                             continuation=[(24, f.devices['stdout'], 8104),
                                           (f.layer_bits, 0, resume.entry)])
    with image.open('r+b') as target:
        target.seek(first.base//8); target.write(first.data)
        target.seek(resume.base//8); target.write(resume.data)
        target.seek(halt//8); target.write(f.layer([(f.layer_bits, 0, first.entry)]))
    saved = io.BytesIO()
    with image.open('rb') as source:
        checkpoint = run_stream(EMULATOR, source, 65520, 8, snapshot=saved)
    assert checkpoint.terminal['kind'] == 'checkpoint' and checkpoint.terminal['reason'] == 'limit'
    resumed_output = io.BytesIO()
    restored = run_stream(EMULATOR, io.BytesIO(saved.getvalue()), 65520, 8,
                          stdout=resumed_output)
    assert restored.terminal['exit_code'] == 9 and resumed_output.getvalue() == b'\x00\xffX'
    print('ok: checkpoint metadata, separate snapshot and explicit static continuation restore')

    # Source/sink failures, timeout and host truncation propagate and reap.
    class BadSource:
        def read(self, n):
            raise OSError('source failed')
    class BadSink:
        def write(self, data):
            raise OSError('sink failed')
    for name, source, kwargs in [
        ('source', BadSource(), {}),
        ('sink', image.open('rb'), dict(stdout=BadSink())),
        ('host truncation', image.open('rb'), dict(ticks=1)),
    ]:
        try:
            run_stream(EMULATOR, source, 65520, 8, timeout=5, **kwargs)
        except (OSError, ValueError):
            pass
        else:
            raise AssertionError(name+' did not fail')
        if hasattr(source, 'close'):
            source.close()
    fixture(image, live=True)
    r, w = os.pipe()
    try:
        with image.open('rb') as source, os.fdopen(r, 'rb', buffering=0) as app_input:
            try:
                run_stream(EMULATOR, source, 65520, 8, input_stream=app_input, timeout=.2)
            except TimeoutError:
                pass
            else:
                raise AssertionError('blocked live input did not time out')
    finally:
        os.close(w)
    try:
        os.waitpid(-1, os.WNOHANG)
    except ChildProcessError:
        pass
    else:
        raise AssertionError('unreaped child')
    print('ok: producer/sink errors, early stop, timeout and process cleanup')

    # Same executable at 8/64/256 MiB. Full sparse raw images, full dumps;
    # relay memory is independent of both stream and image lengths.
    peaks = []
    for mib in (8, 64, 256):
        bits = space_bits_for_bytes(mib*1024*1024)
        f, _ = fixture(image, bits, snapshot=True, sparse_size=(bits+7)//8)
        counter = Counter()
        with image.open('rb') as source:
            tracemalloc.start()
            result = run_stream(EMULATOR, source, bits, 8, snapshot=counter, timeout=30)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        peaks.append(peak)
        assert counter.n == f.space_bytes == result.snapshot_bytes
        assert result.terminal['exit_code'] == 7
        assert peak < 2*1024*1024, (mib, peak)
        print(f'ok: {mib} MiB stdin boot + separate full snapshot; relay peak {peak} bytes')

print('transport: all checks passed')
