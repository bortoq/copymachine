import os, subprocess, sys, time
cpu, emu, l0, tag = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
names = sorted(f[:-4] for f in os.listdir('../res/progs') if f.endswith('.fth') and f != 'selfpart.fth')
data0 = open(l0, 'rb').read()
tot_t = 0; tot_s = 0.0
with open(f'res/all37-{tag}.txt', 'w') as fo:
    for n in names:
        data = data0 + open(f'../res/progs/{n}.fth', 'rb').read()
        t0 = time.monotonic()
        p = subprocess.run([emu, '-s', '2147483648', '-p', '8'], input=data, capture_output=True,
                           env=dict(os.environ, HW_TICKS='1'), preexec_fn=lambda: os.sched_setaffinity(0, {cpu}))
        s = time.monotonic() - t0
        err = p.stderr.decode().strip().split()
        ticks = int(err[1]); tot_t += ticks; tot_s += s
        import hashlib
        fo.write(f'{n} {ticks} {err[3]} {hashlib.md5(p.stdout).hexdigest()[:12]} {s:.1f} rc={p.returncode}\n'); fo.flush()
    fo.write(f'TOTAL {tot_t} {tot_s:.1f}\n')
