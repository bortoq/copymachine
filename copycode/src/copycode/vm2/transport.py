#!/usr/bin/env python3
"""Bounded-memory stdin boot and separate stdout/debug/status/snapshot relay."""
import argparse
from contextlib import ExitStack
import io
import os
from pathlib import Path
import selectors
import signal
import sys
import time
from dataclasses import dataclass

from .boundary import iter_boot
from .machine import describe, require_compatible
from .terminal import MAX_RECORD_BYTES, decode_terminal


class IncompleteRun(ValueError):
    pass


@dataclass
class RunResult:
    returncode: int
    terminal: dict
    stdout_bytes: int
    snapshot_bytes: int
    metrics: dict | None = None


def write_all(sink, data):
    if sink is None:
        return
    view = memoryview(data)
    while view:
        n = sink.write(view)
        if n is None or n <= 0:
            raise OSError('output sink did not accept bytes')
        view = view[n:]
    if hasattr(sink, 'flush'):
        sink.flush()


def run_stream(emulator, image, space_bits, slots, *, input_stream=None,
               stdout=None, debug=None, status=None, snapshot=None,
               timeout=120, ticks=0, description=None, command_prefix=()):
    """Stream an instrumented image, returning only bounded terminal metadata.

    POSIX launcher: descriptors 0..4 are installed with posix_spawn actions.
    File/pipe application input is readiness-driven and never read past child
    exit. Sources without fileno must provide nonblocking bounded read(n).
    Sinks accept synchronous writes; backpressure is intentional. A timeout
    or producer/sink error kills and reaps the emulator and propagates.
    """
    began = time.monotonic()
    desc = describe(space_bits, slots)
    if description is not None:
        require_compatible(description, space_bits, slots)
    if timeout is not None and timeout <= 0 or ticks < 0:
        raise ValueError('timeout must be positive and ticks nonnegative')
    boot = iter(iter_boot(image, space_bits, slots))
    owned, child_ends, parent_ends, actions = [], [], {}, []
    pid, reaped, code = None, False, None
    selector = selectors.SelectSelector()
    record = bytearray()
    boot_chunks, boot_bytes, usage = 0, 0, None
    counts = dict(stdout=0, debug=0, status=0, snapshot=0)
    sinks = dict(stdout=stdout, debug=debug, status=status, snapshot=snapshot)
    # Duplicates above target fds avoid source/target collisions in spawn.
    import fcntl
    try:
        for target, name in enumerate(['input', 'stdout', 'debug', 'status', 'snapshot']):
            r, w = os.pipe()
            owned.extend([r, w])
            child, parent = (r, w) if target == 0 else (w, r)
            duplicate = fcntl.fcntl(child, fcntl.F_DUPFD_CLOEXEC, 10)
            owned.append(duplicate)
            child_ends.append(duplicate)
            actions.append((os.POSIX_SPAWN_DUP2, duplicate, target))
            parent_ends[name] = parent
            os.close(child)
            owned.remove(child)
        command = list(command_prefix)+[str(emulator), '-s', str(space_bits), '-p', str(slots), '-t', str(ticks)]
        pid = os.posix_spawnp(command[0], command, os.environ, file_actions=actions,
                              setsigdef=(signal.SIGPIPE,))
        for fd in child_ends:
            os.close(fd)
            owned.remove(fd)
        for name, fd in parent_ends.items():
            os.set_blocking(fd, False)
            if name != 'input':
                selector.register(fd, selectors.EVENT_READ, name)
        input_fd = None
        if input_stream is not None:
            try:
                input_fd = input_stream.fileno()
            except (AttributeError, io.UnsupportedOperation):
                pass
        pending, boot_done, input_closed, source_registered = memoryview(b''), False, False, False
        started = time.monotonic()

        def stop_input():
            nonlocal input_closed, source_registered
            if input_closed:
                return
            fd = parent_ends['input']
            if fd in selector.get_map():
                selector.unregister(fd)
            if source_registered:
                selector.unregister(input_fd)
                source_registered = False
            os.close(fd)
            owned.remove(fd)
            input_closed = True

        while True:
            if not reaped:
                done, wait_status, child_usage = os.wait4(pid, os.WNOHANG)
                if done:
                    reaped = True
                    code = os.waitstatus_to_exitcode(wait_status)
                    usage = child_usage
                    stop_input()
            if reaped and not selector.get_map():
                break
            if timeout is not None and time.monotonic()-started > timeout:
                raise TimeoutError('emulator streaming timeout')
            if not input_closed and not pending:
                if not boot_done:
                    try:
                        pending = memoryview(next(boot))
                        boot_chunks += 1
                        boot_bytes += len(pending)
                    except StopIteration:
                        boot_done = True
                if boot_done and not pending:
                    if input_stream is None:
                        stop_input()
                    elif input_fd is not None:
                        if not source_registered:
                            selector.register(input_fd, selectors.EVENT_READ, 'source')
                            source_registered = True
                    else:
                        data = input_stream.read(65536)
                        if data:
                            pending = memoryview(data)
                        else:
                            stop_input()
                if pending and parent_ends['input'] not in selector.get_map():
                    selector.register(parent_ends['input'], selectors.EVENT_WRITE, 'input')
            for key, _ in selector.select(0.001 if not selector.get_map() else 0.05):
                name, fd = key.data, key.fd
                if name == 'source':
                    data = os.read(fd, 65536)
                    selector.unregister(fd)
                    source_registered = False
                    if data:
                        pending = memoryview(data)
                        selector.register(parent_ends['input'], selectors.EVENT_WRITE, 'input')
                    else:
                        stop_input()
                elif name == 'input':
                    try:
                        n = os.write(fd, pending)
                    except BrokenPipeError:
                        stop_input()
                        continue
                    pending = pending[n:]
                    if not pending:
                        selector.unregister(fd)
                else:
                    data = os.read(fd, 65536)
                    if not data:
                        selector.unregister(fd)
                        os.close(fd)
                        owned.remove(fd)
                        continue
                    counts[name] += len(data)
                    if name == 'status':
                        if len(record)+len(data) > MAX_RECORD_BYTES:
                            raise IncompleteRun('extra terminal status bytes')
                        record.extend(data)
                    write_all(sinks[name], data)
        if code:
            raise IncompleteRun(f'emulator exited with status {code}')
        terminal = decode_terminal(record, desc)
        if counts['snapshot'] != terminal['snapshot_bytes']:
            raise IncompleteRun('snapshot length differs from terminal record')
        return RunResult(code, terminal, counts['stdout'], counts['snapshot'], dict(
            wall_seconds=time.monotonic()-began, child_user_seconds=usage.ru_utime,
            child_system_seconds=usage.ru_stime, child_peak_rss_kib=usage.ru_maxrss,
            boot_bytes=boot_bytes, boot_ticks=boot_chunks))
    finally:
        selector.close()
        boot.close() if hasattr(boot, 'close') else None
        for fd in owned:
            os.close(fd)
        if pid is not None and not reaped:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(pid, 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path, help='raw image instrumented with TerminalFragment')
    parser.add_argument('--emulator', type=Path, required=True)
    parser.add_argument('-s', type=int, required=True)
    parser.add_argument('-p', type=int, required=True)
    parser.add_argument('--input', type=Path, help='default: live stdin')
    parser.add_argument('--output', type=Path, help='default: stdout')
    parser.add_argument('--debug', type=Path, help='default: stderr')
    parser.add_argument('--status', type=Path)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    try:
        import json
        with ExitStack() as stack:
            def stream(path, mode, default):
                return stack.enter_context(path.open(mode, buffering=0)) if path else default
            result = run_stream(args.emulator, stack.enter_context(args.image.open('rb')),
                args.s, args.p, input_stream=stream(args.input, 'rb', sys.stdin.buffer),
                stdout=stream(args.output, 'wb', sys.stdout.buffer),
                debug=stream(args.debug, 'wb', sys.stderr.buffer),
                status=stream(args.status, 'wb', None), snapshot=stream(args.snapshot, 'wb', None),
                timeout=args.timeout,
                description=json.loads(args.manifest.read_text()) if args.manifest else None)
            return result.terminal['exit_code'] & 255 if result.terminal['reason'] == 'idle' else 125
    except (ValueError, OSError, TimeoutError) as error:
        print(str(error), file=sys.stderr)
        return 125


if __name__ == '__main__':
    sys.exit(main())
