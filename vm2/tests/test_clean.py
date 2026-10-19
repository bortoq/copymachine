"""Exercise make clean against generated artifacts and source sentinels."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    base=Path(directory)
    root=base/'project with spaces'
    root.mkdir()
    source_names=['Makefile','VERSION','dist.manifest','tools/clean.py',
                  'kernel.c','proto_gen.h','tests/stub/nop.bin']
    for name in source_names:
        path=root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        if name in ('Makefile','VERSION','tools/clean.py'):
            shutil.copy2(ROOT/name,path)
        elif name=='dist.manifest':
            path.write_text(''.join(n+'\n' for n in sorted(source_names)))
        else:
            path.write_bytes(b'source fixture')
    before={name:(root/name).read_bytes() for name in source_names}
    outside=base/'outside';outside.mkdir();(outside/'keep').write_bytes(b'keep')
    artifacts=['space','space-dev','space.build-config','old.o','old.build-config.tmp',
               'build/space','build/space.build-config','tests/test_bitcpy',
               'other/alternate','other/alternate.build-config',
               'tmp/snapshot.bin','tmp/sub/trace.bin','dist/archive.tar.gz',
               'artifacts/releases/archive.tar.gz','artifacts/bench/results.json',
               'tools/__pycache__/old.pyc','tests/__pycache__/old.pyc','tools/orphan.pyc']
    for name in artifacts:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'generated')
    (root/'tmp/link').symlink_to(outside,target_is_directory=True)
    # Agent/SCM state is never make-clean output, even with matching suffixes.
    for name in ('.git/keep.o','.opencode/keep.pyc'):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'keep')
    env=dict(os.environ)
    for name in ('MAKEFLAGS','MFLAGS','MAKELEVEL','SPACE_EMULATOR'):
        env.pop(name,None)
    command=['make','clean','BIN=build/space','DISTDIR=artifacts/releases','BENCH_OUTPUT=artifacts/bench']
    result=subprocess.run(command,cwd=root,env=env,capture_output=True)
    assert result.returncode==0,result.stderr
    for name in artifacts:assert not (root/name).exists(),name
    for name in ('tmp','dist','build','other','artifacts','tools/__pycache__','tests/__pycache__'):
        assert not (root/name).exists(),name
    assert (outside/'keep').read_bytes()==b'keep'
    assert (root/'.git/keep.o').read_bytes()==b'keep'
    assert (root/'.opencode/keep.pyc').read_bytes()==b'keep'
    for name,data in before.items():assert (root/name).read_bytes()==data,name
    # Repeated cleanup is harmless. Bad parameters cannot delete source data
    # or partially clean other targets before discovering the mistake.
    assert subprocess.run(command,cwd=root,env=env,capture_output=True).returncode==0
    (root/'tmp').mkdir();(root/'tmp/pending').write_bytes(b'keep')
    for parameter in ('BIN=kernel.c','DISTDIR=tests','BENCH_OUTPUT='+str(outside)):
        result=subprocess.run(['make','clean',parameter],cwd=root,env=env,capture_output=True)
        assert result.returncode!=0,(parameter,result)
        assert (root/'tmp/pending').exists()
        for name,data in before.items():assert (root/name).read_bytes()==data,name
print('clean: generated artifacts removed; sources, fixtures, symlink targets and environment state preserved')
