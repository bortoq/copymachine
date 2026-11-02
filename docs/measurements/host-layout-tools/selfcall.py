import sys, hashlib, subprocess, time, os
W = os.environ['WORK']   # the root of the working copy
sys.path.insert(0, W + '/language/tools')
import paths, boot_call
emu, l0f, words, out = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4]
l0 = open(l0f, 'rb').read()
data = l0 + paths.source_bytes(paths.COMPILER_FILES) + b'\0' + boot_call.kernel_text(words).encode('latin-1')
t = time.monotonic()
with open(out, 'wb') as fo:
    r = subprocess.run(['taskset', '-c', os.environ.get('CPU', '9'), emu, '-s', '2147483648', '-p', '8'], input=data, stdout=fo, stderr=subprocess.PIPE,
                       env=dict(os.environ, HW_TICKS='1', HOST_STATS='1'))
l1 = open(out, 'rb').read()
print('rc', r.returncode, 'equal', l1 == l0, len(l1), len(l0), hashlib.sha256(l1).hexdigest(), 'seconds', round(time.monotonic() - t), r.stderr.decode().strip(), flush=True)
