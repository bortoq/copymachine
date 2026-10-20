"""The direct Forth compiler compiles itself (9.5.4).

The model (scripts/forthc/model.py) compiles the compiler's own sources:
prelude.fth, backend.fth, compute.fth, forthc.fth and main.fth. The result
S1 is the compiler as index code: on the emulator it reads a source on stdin
and writes the boot stream. For every program of forthc_programs.py that
stream must equal the model's, byte for byte. Finally S1 compiles its own
sources, and the stream must be S1 itself: the compiled compiler, the Forth
compiler under pForth and the model agree on the compiler.

  --programs-only   skip the self-compilation (about half an hour)
"""
import json,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts/pforth'),str(ROOT/'scripts')]
from common import RV32I_ROOT
import dependencies
from copycode.hostpaths import output_dir
from forthc import model
from forthc_programs import PROGRAMS,EXPECTED,wrapped

FORTHC=ROOT/'scripts/forthc'
SOURCES=[FORTHC/'prelude.fth',dependencies.COPYCODE_ROOT/'forth/backend.fth',
         dependencies.COPYCODE_ROOT/'forth/compute.fth',FORTHC/'forthc.fth',FORTHC/'main.fth']
EMULATOR=output_dir(dependencies.EMULATOR_ROOT,'build')/'bitcopy/emulator'

def run(stream,text,timeout):
    with tempfile.TemporaryFile() as stdin:
        stdin.write(stream+text.encode('latin-1'));stdin.seek(0)
        start=time.monotonic()
        r=subprocess.run([str(EMULATOR),'-s',str(model.SIZE),'-p','8'],stdin=stdin,capture_output=True,timeout=timeout)
    assert r.returncode==0 and not r.stderr,(r.returncode,r.stderr[-300:])
    return r.stdout,time.monotonic()-start

source=''.join(path.read_text() for path in SOURCES)
start=time.monotonic();compiler=model.Compiler();s1=compiler.compile_source(source,'main')
print(f'PASS model compiles the compiler: {len(s1)} stream bytes, {compiler.b.cell} cells,'
      f' {len(compiler.consts)} constants, {compiler.nlinks} call sites ({time.monotonic()-start:.1f} s)',flush=True)
results=dict(stream_bytes=len(s1),programs=[])
cases=dict(PROGRAMS);cases.update({name:text for name,(text,_) in EXPECTED.items()})
for name,text in cases.items():
    text=wrapped(text);want=model.compile_forth(text);got,seconds=run(s1,text,1800)
    assert got==want,(name,len(got),len(want))
    results['programs'].append(dict(name=name,stream_bytes=len(want),seconds=round(seconds,1)))
    print(f'PASS compiled compiler {name}: {len(want)} stream bytes as the model ({seconds:.1f} s)',flush=True)
if '--programs-only' not in sys.argv:
    s2,seconds=run(s1,source,4*3600)
    assert s2==s1,('self-compilation differs',len(s2),len(s1))
    results['self_seconds']=round(seconds)
    print(f'PASS compiled compiler compiles itself: {len(s2)} bytes equal to S1 ({seconds:.0f} s)',flush=True)
out=output_dir(ROOT)/'verification';out.mkdir(parents=True,exist_ok=True)
(out/'forthc-self.json').write_text(json.dumps(results,indent=1)+'\n')
print('ALL',len(cases),'programs compiled by the compiled compiler equal the model',flush=True)
