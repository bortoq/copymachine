"""Execute local fixtures with independent per-tick interval and channel conflict checks.

The temporary test harness is never a release executable or public mode.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='space-schedules-') as directory:
    root = Path(directory)
    for pattern in ('*.c', '*.h', 'proto.def', 'Makefile', 'VERSION'):
        for source in ROOT.glob(pattern): shutil.copy2(source, root/source.name)
    shutil.copytree(ROOT/'tests', root/'tests', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT/'tools', root/'tools', ignore=shutil.ignore_patterns('__pycache__'))
    compiler = os.environ.get('CC', 'gcc')
    import shlex
    command = shlex.split(compiler)
    for name,default in [('CPPFLAGS',''),('CFLAGS','-std=c11 -Wall -Wextra -O3'),('LDFLAGS','')]:
        command += shlex.split(os.environ.get(name,default))
    subprocess.run(command+['-o',str(root/'space'),'space.c','tests/checked_execution.c',
                           'config.c','sys_ctrl.c','globals.c','bitcopy.c']+shlex.split(os.environ.get('LDLIBS','')),cwd=root,check=True)
    # Never inherit the parent runner's selected binary for this independent
    # harness; all fixture children must execute the temporary checked core.
    fixture_env = dict(os.environ,SPACE_EMULATOR=str(root/'space'),COPYCODE_ROOT=str(ROOT.parent/'copycode'))
    for script in ('tests/test_core_cli.py','tests/test_boundary.py','tests/test_transport.py',
                   'tests/test_checkpoint.py','tests/test_dynamic_trace.py','tests/sys_e2e.sh',
                   'tests/wide.sh','tests/boot.sh','tests/copycode/sys_driver.sh'):
        print('Validating executed schedules:',script,flush=True)
        subprocess.run((['python3','-B'] if script.endswith('.py') else ['sh'])+[script],
                       cwd=root,env=fixture_env,check=True,timeout=180)
    long_text='one transfer, many bytes'
    generated=subprocess.run(['python3','-B','tools/driver_gen.py','-s','65520','-p','8',
                              '--write',long_text],cwd=root,env=fixture_env,capture_output=True,check=True)
    result=subprocess.run([str(root/'space'),'-p','8'],input=generated.stdout,
                          capture_output=True,check=True,timeout=10)
    assert result.stdout==long_text.encode()
    subprocess.run(['python3','-B','tools/benchmark.py','--micro-only','--micro-ticks','40',
                    '--repeats','1','--emulator',str(root/'space'),'--output',str(root/'tmp/micro')],
                   cwd=root,env=fixture_env,check=True,timeout=60)
print('All local executable fixtures passed independent operand-interval and channel conflict validation')
