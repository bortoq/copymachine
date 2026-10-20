"""Tick costs of the direct compiler model (9.5) next to pForth on RV32I.

Operation costs are differences of loop iteration counts (the same code, so
the boot stream does not enter): (9 - 1 iterations) / 8 for compiled code,
(20 - 10) / 10 for pForth, each minus the empty loop. Task costs are
differences of two task sizes. Ticks do not depend on the host, so the runs
may share CPUs. Writes doc/measurements/forthc/result.json.
"""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts/pforth'),str(ROOT/'scripts')]
from common import RV32I_ROOT
import dependencies
from copycode.hostpaths import output_dir
from forthc import model

CHECKED=output_dir(dependencies.VM2_ROOT,'build')/'checked-emulator'
IMAGE=output_dir(ROOT)/'initialized';OBSERVER=output_dir(ROOT)/'observe-emulator'
OPS=['7 drop','5 6 + drop','x @ drop','5 x !','123456 789 * drop','-1234567 89 / drop','1234567 89 mod drop',
     '1234567 89 /mod drop drop']
TASKS={'fib(15) - fib(10)':(': fib dup 2 < if exit then dup 1 - recurse swap 2 - recurse + ;\n: main {n} fib drop ;',15,10),
       'acc @ i + acc ! loop, 1000 - 100':('variable acc\n: main 0 acc ! {n} 0 do acc @ i + acc ! loop ;',1000,100)}

def compiled(source):
    r=subprocess.run([str(CHECKED),'-s',str(model.SIZE),'-p','8'],input=model.compile_forth(source),capture_output=True,timeout=900)
    assert r.returncode==0,r.stderr[-300:]
    return int(r.stderr.split(b'VM1_AUDIT_TICKS=')[1].split()[0])
def pforth(source):
    reg=json.loads((IMAGE/'map.json').read_text())['regions']['registers']['at']
    env=dict(os.environ,EMULATOR=str(OBSERVER),PFORTH_REG_BITS=str(reg))
    r=subprocess.run([str(ROOT/'pforth'),'run',str(IMAGE)],input=(source+'\nmain bye\n').encode(),capture_output=True,env=env,timeout=1800)
    assert r.returncode==0,r.stderr[-300:]
    return int(r.stderr.split(b'stop ticks=')[1].split()[0])
def op_cost(run,unit,hi,lo):
    loop=lambda n:run(f'variable x\n: main {n} 0 do {unit} loop ;')
    return (loop(hi)-loop(lo))/(hi-lo)

if __name__=='__main__':
    result={'operations':{},'tasks':{}}
    empty=(op_cost(compiled,'',9,1),op_cost(pforth,'',20,10))
    result['operations']['empty loop iteration']=dict(compiled=empty[0],pforth=empty[1])
    for unit in OPS:
        c=op_cost(compiled,unit,9,1)-empty[0];p=op_cost(pforth,unit,20,10)-empty[1]
        result['operations'][unit]=dict(compiled=c,pforth=p,ratio=round(p/c) if c else None)
        print(f'{unit:28} {c:8.1f} {p:10.1f}',flush=True)
    for name,(source,hi,lo) in TASKS.items():
        c=compiled(source.format(n=hi))-compiled(source.format(n=lo))
        p=pforth(source.format(n=hi))-pforth(source.format(n=lo))
        result['tasks'][name]=dict(compiled=c,pforth=p,ratio=round(p/c))
        print(f'{name:28} {c:8} {p:10}',flush=True)
    target=ROOT/'doc/measurements/forthc/result.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=1)+'\n');print('wrote',target)
