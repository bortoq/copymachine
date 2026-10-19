#!/usr/bin/env python3
"""Check actual rebuild/selection, including switching back to a cached backend."""
import os
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
env={k:v for k,v in os.environ.items() if k not in ('BACKEND','MAKEFLAGS','MFLAGS','MAKEOVERRIDES')}
for selection,expected in [('network','network'),(None,'bitcopy'),('network','network'),('bitcopy','bitcopy')]:
    args=['make']+([f'BACKEND={selection}'] if selection else [])
    subprocess.run(args,cwd=ROOT,env=env,check=True,capture_output=True)
    assert (ROOT/'vm1').read_bytes()==(ROOT/f'build/{expected}/vm1').read_bytes()
flags=env.get('CFLAGS','-Wall -Wextra -pedantic -std=c11 -O2')
original=(ROOT/'build/bitcopy/vm1').stat().st_mtime_ns
subprocess.run(['make',f'CFLAGS={flags} -DVM1_REBUILD_CHECK=1'],cwd=ROOT,env=env,check=True,capture_output=True)
assert (ROOT/'build/bitcopy/vm1').stat().st_mtime_ns!=original
assert '-DVM1_REBUILD_CHECK=1' in (ROOT/'build/bitcopy/build-config').read_text()
subprocess.run(['make',f'CFLAGS={flags}'],cwd=ROOT,env=env,check=True,capture_output=True)
assert '-DVM1_REBUILD_CHECK=1' not in (ROOT/'build/bitcopy/build-config').read_text()
default_env=dict(env)
default_env.pop('CFLAGS',None)
output=subprocess.check_output(['make','--no-print-directory','-s',
    '--eval=vm1-test-default-flags:;@echo $(CFLAGS)','vm1-test-default-flags'],
    cwd=ROOT,env=default_env,text=True)
assert '-O2' in output and '-std=c11' in output, output
print('build selection: network/default/network/bitcopy and changed/restored flags passed')
