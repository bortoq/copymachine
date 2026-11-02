import sys, os
W = sys.argv[1]; out = sys.argv[2]
sys.path.insert(0, W + '/language/tools')
import paths
P = paths.programs()
os.makedirs(out, exist_ok=True)
for n, (src, _) in P.items():
    open(f'{out}/{n}.fth', 'wb').write(src.encode('latin-1') + b'\0')
print(len(P))
