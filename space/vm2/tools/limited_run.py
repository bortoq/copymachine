#!/usr/bin/env python3
"""Run a benchmark tree on one CPU with bounded memory, CPU time and duration.

Each run takes the lowest-numbered CPU not held by another limited run (a
per-CPU lock file), so sequential runs always use the same CPU and parallel
runs get distinct CPUs. Wall and CPU time are reported on stderr at the end.
"""
import argparse
import fcntl
import tempfile
import time
import os
import resource
import signal
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=180)
    parser.add_argument('--memory-mib', type=int, default=768)
    parser.add_argument('--file-mib', type=int, default=16, help='maximum size of an output or sparse test file')
    parser.add_argument('--cpus', type=int, default=1, help='CPUs reserved for the whole tree (parallel checks)')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command or args.seconds < 1 or args.memory_mib < 64 or args.file_mib < 1:
        parser.error('command, positive duration/file limit and at least 64 MiB required')

    cpus = sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else []
    if os.environ.get('COPYMACHINE_LIMITED') == '1':
        cpus = []  # nested: the outer run already holds and pinned the CPUs
    need = max(1, min(args.cpus, len(cpus) or 1))
    locks, chosen = [], []
    while cpus and len(chosen) < need:
        for cpu in cpus:
            if cpu in chosen:
                continue
            handle = open(os.path.join(tempfile.gettempdir(), f'copymachine-cpu-{cpu}.lock'), 'w')
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                continue
            locks.append(handle);chosen.append(cpu)
            if len(chosen) == need:
                break
        else:
            time.sleep(0.5)

    def limits():
        os.nice(15)
        if chosen:
            os.sched_setaffinity(0, set(chosen))
        ceiling = args.memory_mib * 1024 * 1024
        existing = resource.getrlimit(resource.RLIMIT_AS)[0]
        if existing != resource.RLIM_INFINITY:
            ceiling = min(ceiling, existing)
        resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
        cpu = resource.getrlimit(resource.RLIMIT_CPU)[0]
        cpu = args.seconds if cpu == resource.RLIM_INFINITY else min(cpu, args.seconds)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        file_ceiling = args.file_mib * 1024 * 1024
        existing_file = resource.getrlimit(resource.RLIMIT_FSIZE)[1]
        if existing_file != resource.RLIM_INFINITY:
            file_ceiling = min(file_ceiling, existing_file)
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_ceiling, file_ceiling))

    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', COPYMACHINE_LIMITED='1')
    started = time.monotonic();used = resource.getrusage(resource.RUSAGE_CHILDREN)
    child = subprocess.Popen(args.command, env=env, start_new_session=True, preexec_fn=limits)
    try:
        code = child.wait(timeout=args.seconds)
        now = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu_seconds = now.ru_utime + now.ru_stime - used.ru_utime - used.ru_stime
        print(f'TIME {time.monotonic() - started:.1f} s wall, {cpu_seconds:.1f} s CPU, cpu {",".join(map(str, chosen))}, exit {code}: '
              + ' '.join(args.command[-2:]), file=sys.stderr, flush=True)
        return code if code >= 0 else 128 - code
    except subprocess.TimeoutExpired:
        print('Benchmark stopped: duration limit reached', file=sys.stderr)
        return 124
    finally:
        # Descendants must also stop, including a VM left by a failed benchmark.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait()


if __name__ == '__main__':
    raise SystemExit(main())
