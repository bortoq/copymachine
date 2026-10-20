"""The kernel (9.6): the compiled compiler compiles and runs programs inside
its own space, and rebuilds itself.

The model (scripts/forthc/model.py) compiles the kernel's sources: the
compiler's (prelude.fth, backend.fth, compute.fth, forthc.fth, main.fth) and
kernel.fth. The result K0 is the boot stream of the kernel; its input is a
program up to a zero byte, the rest of stdin is the program's input. The
kernel installs the program in the lower half of its space and starts it in
the same emulator run.

1. Every program of forthc_programs.py run through K0 writes what its own
   boot stream (from the model) writes.
2. A program reads its input after the zero byte; a compile error prints
   "error N at WORD".
3. K0 compiles and runs the compiler (main.fth) as a program, and that
   compiler compiles the kernel's sources from the rest of stdin: the stream
   K1 must equal K0. Neither a C compiler nor Python is on this path.

  --programs-only   skip the rebuild (about an hour and a half)
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
COMPILER=[FORTHC/'prelude.fth',dependencies.COPYCODE_ROOT/'forth/backend.fth',
          dependencies.COPYCODE_ROOT/'forth/compute.fth',FORTHC/'forthc.fth',FORTHC/'main.fth']
KERNEL=COMPILER+[FORTHC/'kernel.fth']
EMULATOR=output_dir(dependencies.EMULATOR_ROOT,'build')/'bitcopy/emulator'

def run(data,timeout):
    # Files, not pipes: the streams are megabytes (see test_forthc_self.py).
    with tempfile.TemporaryFile() as stdin,tempfile.TemporaryFile() as stdout,tempfile.TemporaryFile() as stderr:
        stdin.write(data);stdin.seek(0)
        start=time.monotonic()
        r=subprocess.run([str(EMULATOR),'-s',str(model.SIZE),'-p','8'],stdin=stdin,stdout=stdout,stderr=stderr,timeout=timeout)
        seconds=time.monotonic()-start;stdout.seek(0);stderr.seek(0);out=stdout.read();err=stderr.read()
    assert r.returncode==0 and not err,(r.returncode,err[-300:])
    return out,seconds
def text(paths):return ''.join(path.read_text() for path in paths)

compiler_source=text(COMPILER);kernel_source=text(KERNEL)
start=time.monotonic();compiler=model.Compiler();k0=compiler.compile_source(kernel_source,'main')
assert compiler.kernel
print(f'PASS model compiles the kernel: {len(k0)} stream bytes,'
      f' {compiler.b.cell-model.KERNEL_FIRST_CELL} cells ({time.monotonic()-start:.1f} s)',flush=True)
results=dict(stream_bytes=len(k0),programs=[])
cases=dict(PROGRAMS);cases.update({name:source for name,(source,_) in EXPECTED.items()})
for name,source in cases.items():
    source=wrapped(source);want,_=run(model.compile_forth(source),600)
    got,seconds=run(k0+source.encode('latin-1')+b'\0',1800)
    assert got==want,(name,got[-200:],want[-200:])
    results['programs'].append(dict(name=name,output_bytes=len(got),seconds=round(seconds,1)))
    print(f'PASS kernel {name}: compiled and run in the space, output as its stream ({seconds:.1f} s)',flush=True)

echo=': main begin key dup while 1+ emit repeat drop ;\n'
got,_=run(k0+echo.encode()+b'\0'+b'HAL',600)
assert got==b'IBM',got
print('PASS kernel: the program reads the input after its source',flush=True)
got,_=run(k0+b': main 1 frobnicate ;\n\0',600)
assert got==b'error -13 at frobnicate\n',got
print('PASS kernel: a compile error is reported',flush=True)

if '--programs-only' not in sys.argv:
    k1,seconds=run(k0+compiler_source.encode('latin-1')+b'\0'+kernel_source.encode('latin-1'),6*3600)
    assert k1==k0,('the rebuilt kernel differs',len(k1),len(k0))
    results['rebuild_seconds']=round(seconds)
    print(f'PASS kernel rebuilds itself: K0 runs the compiler, which compiles the kernel:'
          f' {len(k1)} bytes equal to K0 ({seconds:.0f} s)',flush=True)
out=output_dir(ROOT)/'verification';out.mkdir(parents=True,exist_ok=True)
(out/'kernel.json').write_text(json.dumps(results,indent=1)+'\n')
print('ALL',len(cases),'programs compiled and run inside the space by the kernel',flush=True)
