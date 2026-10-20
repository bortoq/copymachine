"""Direct Forth compiler in Forth (forthc.fth) versus its model: same stream.

scripts/forthc/forthc.fth is loaded after backend.fth and compute.fth; each
program is given at run time with FC| lines and compiled by FC-GO, which
types the boot stream. It must equal the stream of scripts/forthc/model.py
byte for byte. All programs of forthc_programs.py run on the 32-bit host
pForth with the image's dictionary and memory (scripts/pforth/host32.py);
the image itself (pForth on RV32I) compiles GUEST_PROGRAM, and that stream
runs on checked-emulator with the expected output.
"""
import json,subprocess,sys,time
from pathlib import Path
from guest_support import ROOT,run_guest
sys.path[:0]=[str(ROOT/'scripts/pforth'),str(ROOT/'scripts')]
import dependencies,host32
from copycode.hostpaths import output_dir
from forthc import model
from forthc_programs import PROGRAMS,EXPECTED,wrapped

LIBRARIES=['backend.fth','compute.fth',Path('scripts/forthc/forthc.fth')]
GUEST_PROGRAM='arithmetic'
CHECKED=output_dir(dependencies.VM2_ROOT,'build')/'checked-emulator'

def library_source():
    return b''.join((ROOT/name if isinstance(name,Path) else dependencies.COPYCODE_ROOT/'forth'/name).read_bytes()
                    for name in LIBRARIES)
def task(text):
    return ['fc| '+line for line in wrapped(text).split('\n')]+['fc-go','bye']

pforth32=host32.build();libraries=library_source();results=[]
cases=dict(PROGRAMS);cases.update({name:source for name,(source,_) in EXPECTED.items()})
for name,text in cases.items():
    want=model.compile_forth(wrapped(text))
    start=time.monotonic()
    r=subprocess.run([str(pforth32)],input=libraries+('\n'.join(task(text))+'\n').encode('latin-1'),
                     capture_output=True,timeout=600)
    seconds=time.monotonic()-start
    assert r.returncode==0 and not r.stderr,(name,r.returncode,r.stdout[-500:],r.stderr[-500:])
    assert r.stdout==want+b'\n',(name,len(r.stdout),len(want),r.stdout[-300:])
    results.append(dict(name=name,stream_bytes=len(want),host32_seconds=round(seconds,2)))
    print(f'PASS forthc.fth {name}: {len(want)} stream bytes as the model ({seconds:.1f} s on host32)',flush=True)

text=PROGRAMS[GUEST_PROGRAM];stream=model.compile_forth(wrapped(text))
run_guest('forthc-'+GUEST_PROGRAM,LIBRARIES,task(text),stream+b'\n',timeout=20000)
r=subprocess.run([str(CHECKED),'-s',str(model.SIZE),'-p','8'],input=stream,capture_output=True,timeout=600)
assert r.returncode==0 and r.stdout==b'ACCFE',(r.returncode,r.stdout,r.stderr[-300:])
print(f'PASS forthc.fth in the image: {GUEST_PROGRAM} compiled, the stream runs: {r.stdout!r}',flush=True)
out=output_dir(ROOT)/'verification';out.mkdir(parents=True,exist_ok=True)
(out/'forthc-forth.json').write_text(json.dumps(dict(host32=results,guest=GUEST_PROGRAM),indent=1)+'\n')
print('ALL',len(results),'programs: forthc.fth streams equal the model; the image compiles',GUEST_PROGRAM,flush=True)
