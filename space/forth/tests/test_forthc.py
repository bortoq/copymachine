"""Direct Forth compiler model (9.5) versus pForth on RV32I: same output.

Each program is compiled by scripts/forthc/model.py into index code and run
on checked-emulator (every tick's operands verified); the same source runs in
pForth on the universal RV32I image. The EMIT output must be identical.
Ticks of both are recorded. Where pForth is no reference, EXPECTED programs
are checked against values computed in forthc_programs.py, including random
products and quotients.
"""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts/pforth'),str(ROOT/'scripts')]
from common import RV32I_ROOT
import dependencies
from copycode.hostpaths import output_dir
from forthc import model

CHECKED=output_dir(dependencies.VM2_ROOT,'build')/'checked-emulator'
IMAGE=output_dir(ROOT)/'initialized';OBSERVER=output_dir(ROOT)/'observe-emulator'

from forthc_programs import PROGRAMS,EXPECTED

def run_compiled(source):
    start=time.monotonic();stream=model.compile_forth(source);compile_seconds=time.monotonic()-start
    r=subprocess.run([str(CHECKED),'-s',str(model.SIZE),'-p','8'],input=stream,capture_output=True,timeout=600)
    assert r.returncode==0,(r.returncode,r.stderr[-800:])
    return r.stdout,int(r.stderr.split(b'VM1_AUDIT_TICKS=')[1].split()[0]),len(stream),compile_seconds

def run_pforth(source):
    mapping=json.loads((IMAGE/'map.json').read_text());reg=mapping['regions']['registers']['at']
    env=dict(os.environ,EMULATOR=str(OBSERVER),PFORTH_REG_BITS=str(reg))
    r=subprocess.run([str(ROOT/'pforth'),'run',str(IMAGE)],input=(source+'\nmain bye\n').encode(),
                     capture_output=True,env=env,timeout=900)
    assert r.returncode==0,(r.returncode,r.stdout[-300:],r.stderr[-300:])
    out=r.stdout[:-1] if r.stdout.endswith(b'\n') else r.stdout
    return out,int(r.stderr.split(b'stop ticks=')[1].split()[0])

results=[]
for name,(source,want) in EXPECTED.items():
    got,ticks,size,seconds=run_compiled(source)
    assert got==want,(name,got,want)
    results.append(dict(name=name,output=got.decode('latin-1'),ticks=ticks,stream_bytes=size,compile_seconds=round(seconds,2)))
    print(f'PASS forthc {name}: {len(got)} bytes as expected in {ticks} ticks, {size} bytes',flush=True)
for name,source in PROGRAMS.items():
    got,ticks,size,seconds=run_compiled(source)
    want,pticks=run_pforth(source)
    assert got==want,(name,got,want)
    results.append(dict(name=name,output=got.decode('latin-1'),ticks=ticks,pforth_ticks=pticks,stream_bytes=size,
                        compile_seconds=round(seconds,2)))
    print(f'PASS forthc {name}: {got!r} in {ticks} ticks (pForth {pticks}), {size} bytes',flush=True)
out=output_dir(ROOT)/'verification';out.mkdir(parents=True,exist_ok=True)
(out/'forthc.json').write_text(json.dumps(results,indent=1)+'\n')
print('ALL',len(results),'direct-compiled programs:',len(PROGRAMS),'match pForth,',len(EXPECTED),'expected outputs',flush=True)
