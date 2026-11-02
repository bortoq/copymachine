# Tools of docs/measurements/dynamic-isolation.md. all37.py: ticks of the 37 programs through L0 (programs: language/tests/reference/forthc_programs.py,
# one file each in progs/, the source and the byte 0); ticks.py, clash.py: ticks per operation on L0. The emulator: a copy of emulator/src with the
# tick counter (HW_TICKS=1 prints "ticks N prog-hash H" on stderr).
"""ticks per operation: (ticks(9 iterations) - ticks(1)) / 8 minus the empty loop, program on L0 on the counting emulator."""
import os, subprocess, sys, json
emu, l0, tag = sys.argv[1], sys.argv[2], sys.argv[3]
form = sys.argv[4]   # old (lo hi) or new (lo only)
D = 1342177280 + 0     # a free place of the program data: 2^30 + 2^28 (old form)
if form == 'new': D = 1073741824 + (1 << 27)
def ticks(body, n, pre=''):
    src = f'{pre}\n: main {n} 0 do {body} loop ;\n'.encode()
    p = subprocess.run([emu, '-s', '2147483648', '-p', '8'], input=open(l0, 'rb').read() + src + b'\0',
                       capture_output=True, check=False, env=dict(os.environ, HW_TICKS='1'))
    err = p.stderr.decode().split()
    assert p.returncode == 0 and err, (body, p.stdout[:100], p.stderr[:200])
    return int(err[1]), p.stdout
def per(body, pre=''):
    t9, o9 = ticks(body, 9, pre); t1, o1 = ticks(body, 1, pre)
    return (t9 - t1) / 8, o9
if form == 'old':
    ops = {'space!': f'7 {D} {D+32} space!', 'spacec!': f'7 {D} {D+8} spacec!', 'space@': f'{D} {D+32} space@ drop',
           'spacec@': f'{D} {D+8} spacec@ drop'}
else:
    ops = {'space!': f'7 {D} space!', 'spacec!': f'7 {D} spacec!', 'space@': f'{D} space@ drop', 'spacec@': f'{D} spacec@ drop'}
ops.update({'call': 'w', 'execute': "['] w execute", 'catch': "['] w catch drop"})
pre = ': w ;'
res = {}
base, _ = per('', pre)
res['empty'] = base
for k, b in ops.items():
    try:
        v, out = per(b, pre)
        res[k] = round(v - base, 1)
    except AssertionError:
        res[k] = None
print(json.dumps(res))
json.dump(res, open(f'ticks-{tag}.json', 'w'))
