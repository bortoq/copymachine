import os, subprocess, sys, hashlib
from concurrent.futures import ThreadPoolExecutor
emu, l0, tag, ncpu = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
d = os.path.dirname(os.path.abspath(__file__))
names = sorted(f[:-4] for f in os.listdir(d+'/progs') if f.endswith('.fth'))
data0 = open(l0, 'rb').read()
def run(n):
    data = data0 + open(f'{d}/progs/{n}.fth', 'rb').read() + b'\0'
    p = subprocess.run([emu, '-s', '2147483648', '-p', '8'], input=data, capture_output=True, check=False, env=dict(os.environ, HW_TICKS='1'))
    err = p.stderr.decode().strip().split()
    return n, int(err[1]), err[3], hashlib.md5(p.stdout).hexdigest()[:12], p.returncode
with ThreadPoolExecutor(ncpu) as ex, open(f'{d}/all37-{tag}.txt','w') as fo:
    tot=0
    for r in ex.map(run, names):
        tot+=r[1]; fo.write('%s %d %s %s rc=%d\n'%r); fo.flush()
    fo.write(f'TOTAL {tot}\n')
