import os, subprocess, sys
emu, l0 = sys.argv[1], sys.argv[2]
def ticks(body, n):
    src = f'variable v create b 16 allot\n: main {n} 0 do {body} loop ;\n'.encode()
    p = subprocess.run([emu, '-s', '2147483648', '-p', '8'], input=open(l0, 'rb').read() + src + b'\0', capture_output=True, check=False, env=dict(os.environ, HW_TICKS='1'))
    err = p.stderr.decode().split(); assert p.returncode == 0 and err, p.stdout[:100]
    return int(err[1])
def per(b): return (ticks(b, 9) - ticks(b, 1)) / 8
base = per('')
print({k: round(per(b) - base, 1) for k, b in {'@': 'v @ drop', '!': '7 v !', 'c@': 'b c@ drop', 'c!': '7 b c!'}.items()})
