"""Direct Forth compiler model (9.5) versus pForth on RV32I: same output.

Each program is compiled by scripts/forthc/model.py into index code and run
on checked-emulator (every tick's operands verified); the same source runs in
pForth on the universal RV32I image. The EMIT output must be identical.
Ticks of both are recorded.
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

PROGRAMS={
'arithmetic':': main 65 emit 3 4 + 60 + emit 100 33 - emit 6 7 and 64 or emit 70 3 xor emit ;',
'stack':': main 65 66 swap emit emit 67 68 over emit emit emit 69 70 71 rot emit emit emit 72 dup emit emit 73 74 drop emit ;',
'compare':': b ( f -- ) if 89 else 78 then emit ;\n'
          ': main 3 3 = b 3 4 = b 3 4 < b 4 3 < b -1 0 < b 0 -1 < b 0 0= b 5 0= b ;',
'if-nested':': c ( n -- ) dup 0 < if drop 45 else dup 0= if drop 48 else 10 < if 115 else 76 then then then emit ;\n'
            ': main -5 c 0 c 7 c 70 c ;',
'begin-until':': main 0 begin dup 48 + emit 1 + dup 5 = until drop ;',
'while-repeat':': main 10 begin dup while dup 64 + emit 2 - repeat drop ;',
'do-loop':': main 5 0 do i 48 + emit loop 3 0 do 2 0 do i j 0 + emit drop loop loop ;',
'variables':'variable x variable y\n: main 5 x ! 7 y ! x @ y @ + 48 + emit x @ 1 + x ! x @ 48 + emit ;',
'return-stack':': main 65 >r 66 >r r@ emit r> emit r> emit ;',
'calls':': sq dup + ; : quad sq sq ; : main 3 quad 48 + emit 10 quad emit ;',
'recursion':': fact ( n -- n! ) dup 1 < if drop 1 else dup 1 - recurse * then ;',
'fib':': fib ( n -- f ) dup 2 < if exit then dup 1 - recurse swap 2 - recurse + ;\n'
      ': main 10 fib emit 12 fib 100 - emit ;',
'constant':'48 constant zero 7 constant seven\n: main zero seven + emit ;',
'loop-sum':'variable acc\n: main 0 acc ! 101 1 do acc @ i + acc ! loop acc @ 255 and emit acc @ 256 / emit ;',
}
PROGRAMS['execute']=': a 65 emit ; : b 66 emit ; : main [\'] a execute [\'] b execute [\'] a dup execute execute ;'
PROGRAMS['catch']=(': f 3 throw 65 emit ; : g 66 emit ; : h 7 f 8 ; : ok 0 throw 67 emit ;\n'
                   ': main 65 66 [\'] f catch 48 + emit emit emit [\'] g catch 48 + emit'
                   ' [\'] h catch 48 + emit [\'] ok catch 48 + emit 1 [\'] h catch 48 + emit 48 + emit ;')
# No multiplication/division in the subset: replace the programs that need them.
PROGRAMS['recursion']=': sum ( n -- s ) dup 0= if exit then dup 1 - recurse + ;\n: main 10 sum emit 3 sum 48 + emit ;'
PROGRAMS['loop-sum']='variable acc\n: main 0 acc ! 21 1 do acc @ i + acc ! loop acc @ emit ;'
PROGRAMS['do-loop']=': main 5 0 do i 48 + emit loop 3 0 do 2 0 do i 48 + emit loop loop ;'

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
for name,source in PROGRAMS.items():
    got,ticks,size,seconds=run_compiled(source)
    want,pticks=run_pforth(source)
    assert got==want,(name,got,want)
    results.append(dict(name=name,output=got.decode('latin-1'),ticks=ticks,pforth_ticks=pticks,stream_bytes=size,
                        compile_seconds=round(seconds,2)))
    print(f'PASS forthc {name}: {got!r} in {ticks} ticks (pForth {pticks}), {size} bytes',flush=True)
out=output_dir(ROOT)/'verification';out.mkdir(parents=True,exist_ok=True)
(out/'forthc.json').write_text(json.dumps(results,indent=1)+'\n')
print('ALL',len(results),'direct-compiled programs match pForth',flush=True)
