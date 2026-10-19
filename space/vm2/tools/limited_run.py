#!/usr/bin/env python3
"""Run a benchmark tree on one CPU with bounded memory, CPU time and duration."""
import argparse
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
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command or args.seconds < 1 or args.memory_mib < 64 or args.file_mib < 1:
        parser.error('command, positive duration/file limit and at least 64 MiB required')

    def limits():
        os.nice(15)
        if hasattr(os, 'sched_getaffinity'):
            os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
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
    child = subprocess.Popen(args.command, env=env, start_new_session=True, preexec_fn=limits)
    try:
        code = child.wait(timeout=args.seconds)
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
