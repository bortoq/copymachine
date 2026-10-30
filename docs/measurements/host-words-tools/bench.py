#!/usr/bin/env python3
"""bench.py CPU emu L0 prog [repeat]: runs the emulator pinned to one CPU, prints ticks, hash, wall, user+sys CPU seconds."""
import os, subprocess, sys, time, resource
cpu, emu, l0, prog = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
rep = int(sys.argv[5]) if len(sys.argv) > 5 else 1
data = open(l0, 'rb').read() + open(prog, 'rb').read()
for k in range(rep):
    t0 = time.monotonic()
    p = subprocess.Popen([emu, '-s', '2147483648', '-p', '8'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=dict(os.environ, HW_TICKS='1'), preexec_fn=lambda: os.sched_setaffinity(0, {cpu}))
    out, err = p.communicate(data)
    t1 = time.monotonic()
    ru = os.wait4(p.pid, 0)[2] if False else None
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    print(os.path.basename(emu), os.path.basename(l0), os.path.basename(prog), 'run', k, err.decode().strip().replace('\n', ' | '), 'out', len(out), 'wall %.2f' % (t1 - t0), 'cpu(cum) %.2f' % (r.ru_utime + r.ru_stime), flush=True)
