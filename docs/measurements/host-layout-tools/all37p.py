import os, subprocess, sys, time, hashlib
from concurrent.futures import ThreadPoolExecutor
emu, l0, tag = sys.argv[1], sys.argv[2], sys.argv[3]
cpus = [int(x) for x in sys.argv[4].split(',')]
progs = os.environ['PROGS']   # the directory of the 37 programs (*.fth)
names = sorted(f[:-4] for f in os.listdir(progs) if f.endswith('.fth') and f != 'selfpart.fth')
data0 = open(l0, 'rb').read()
import queue
q = queue.Queue()
for c in cpus: q.put(c)
def run(n):
    c = q.get()
    try:
        data = data0 + open(f'{progs}/{n}.fth', 'rb').read()
        t0 = time.monotonic()
        p = subprocess.run([emu, '-s', '2147483648', '-p', '8'], input=data, capture_output=True,
                           env=dict(os.environ, HW_TICKS='1', **({'HW_HIST': os.environ['HISTDIR']+'/'+n+'.txt'} if 'HISTDIR' in os.environ else {})), preexec_fn=lambda: os.sched_setaffinity(0, {c}))
        s = time.monotonic() - t0
        err = p.stderr.decode().strip().split()
        return (n, int(err[1]), err[3], hashlib.md5(p.stdout).hexdigest()[:12], s, p.returncode)
    finally:
        q.put(c)
with ThreadPoolExecutor(len(cpus)) as ex:
    res = list(ex.map(run, names))
tt = sum(r[1] for r in res); ts = sum(r[4] for r in res)
with open(f'all37-{tag}.txt', 'w') as fo:
    for r in res: fo.write(f'{r[0]} {r[1]} {r[2]} {r[3]} {r[4]:.1f} rc={r[5]}\n')
    fo.write(f'TOTAL {tt} {ts:.1f}\n')
print(tag, 'TOTAL', tt, f'{ts:.1f}')
