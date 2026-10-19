"""Source-free launch, transport, installation interface and rejected ABI inputs."""
import copy,json,os,select,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vm2compile import Program,Copy,Channel,Field,Memory,Value,Replace
from vm2compile.artifact import build,save,load
CLI=Path(os.environ.get('VM2C',ROOT/'vm2c'))

def cli(*args,**kw):return subprocess.run([str(CLI),*map(str,args)],capture_output=True,timeout=30,**kw)
def rejected(p):
    try:build(p)
    except (ValueError,OverflowError):return
    raise AssertionError('unsupported source accepted')
with tempfile.TemporaryDirectory() as name:
 d=Path(name);source=d/'source.json';obj=d/'artifact'
 source.write_bytes((ROOT/'examples/direct/hello.json').read_bytes())
 assert cli('compile',source,'-o',obj).returncode==0
 a,m=load(obj);aa,mm=build(Program.load(json.loads(source.read_text())))
 assert a==aa and m==json.loads(json.dumps(mm))
 source.unlink()
 for _ in range(2):
    r=cli('run',obj,input=b'');assert (r.returncode,r.stdout,r.stderr)==(0,b'copymachine\n',b''),r
 assert cli('check',obj).returncode==0
 assert cli('run',obj,'--physical-ticks','-1').returncode==2
 assert cli('run',obj,'--physical-ticks',str(1<<64)).returncode==2
 assert cli('run',obj,'--physical-ticks','1x').returncode==2
 assert cli('compile',d/'absent','-o',d/'new').returncode==2
 # No compiler is imported during source-free load/launch.
 code="from vm2compile.artifact import load;import sys;load(sys.argv[1]);assert 'vm2compile.compiler' not in sys.modules"
 subprocess.run([sys.executable,'-c',code,str(obj)],cwd=ROOT,check=True)
 for filename in ('image.bin','boot.bin','map.json'):
    path=obj/filename;original=path.read_bytes();path.write_bytes(original+b'x')
    assert cli('check',obj).returncode==2;path.write_bytes(original)
 path=obj/'manifest.json';original=path.read_bytes();bad=json.loads(original);bad['schema']='old-vm2';path.write_text(json.dumps(bad))
 assert cli('check',obj).returncode==2;path.write_bytes(original)
 (obj/'unexpected').write_bytes(b'');assert cli('check',obj).returncode==2;(obj/'unexpected').unlink()
 # Child must print before EOF; feeder must not block on an open input pipe.
 p=Program();x=p.bytes('prompt',b'>');buf=p.data('input',8)
 p.layer('prompt',[Copy(8,Channel('stdout'),x)],next='input');p.layer('input',[Copy(8,buf,Channel('stdin'))],next='echo');p.layer('echo',[Copy(8,Channel('stdout'),buf)])
 a,m=build(p);interactive=d/'interactive';save(interactive,a,m)
 child=subprocess.Popen([str(CLI),'run',str(interactive)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert select.select([child.stdout],[],[],10)[0],'prompt blocked until EOF'
 assert child.stdout.read(1)==b'>';child.stdin.write(b'Z');child.stdin.flush()
 assert select.select([child.stdout],[],[],10)[0],'input blocked until EOF'
 assert child.stdout.read(1)==b'Z';assert child.wait(timeout=10)==0;assert child.stderr.read()==b'';child.stdin.close()
 # inherited channels 3/4 and source-free checkpoint/resume through CLI.
 p=Program();x=p.bytes('a',b'A');y=p.bytes('b',b'B')
 p.layer('first',[Copy(8,Channel('status'),x),Copy(8,Channel('stdout'),y)],next='last',checkpoint=True)
 p.layer('last',[Copy(8,Channel('stdout'),x)])
 a,m=build(p);saved=d/'saved';save(saved,a,m);status=d/'status';snapshot=d/'snapshot'
 command=['sh','-c','exec "$1" run "$2" 3>"$3" 4>"$4"','fds',str(CLI),str(saved),str(status),str(snapshot)]
 r=subprocess.run(command,input=b'',capture_output=True,timeout=30);assert (r.returncode,r.stdout,r.stderr)==(0,b'BA',b''),r
 assert status.read_bytes()==b'A'
 assert cli('resume',saved,snapshot,'-o',d/'resumed').returncode==0
 r=cli('run',d/'resumed',input=b'');assert (r.returncode,r.stdout,r.stderr)==(0,b'A',b''),r
 (d/'wrong').write_bytes(b'x');assert cli('resume',saved,d/'wrong','-o',d/'wrong-obj').returncode==2
 # Regular stdin uses a seekable composite stream, not a pipe.
 with (d/'input').open('wb') as f:f.write(b'Q')
 with (d/'input').open('rb') as f:r=cli('run',interactive,stdin=f)
 assert (r.returncode,r.stdout,r.stderr)==(0,b'>Q',b''),r
# Static validation must fail instead of silently selecting the interpreter.
for kind in ('src-src','self','bounds','raw','count','channel-channel','field-bounds','entry','pointer-overlap'):
 p=Program();a=p.data('a',128);b=p.data('b',128);c=p.data('c',128)
 rows=[Copy(8,b,a)]
 if kind=='src-src':rows+=[Copy(8,c,a)]
 if kind=='self':rows=[Copy(8,a+1,a)]
 if kind=='bounds':rows=[Copy(16,b,a+120)]
 if kind=='raw':rows=[Copy(8,5,a)]
 if kind=='count':rows=[Copy(1<<63,b,a)]
 if kind=='channel-channel':rows=[Copy(8,Channel('stdout'),Channel('stdin'))]
 if kind=='field-bounds':rows=[Copy(30,b,Field('one',0,'src',10))]
 p.layer('one',rows)
 if kind=='entry':p.entry='missing'
 if kind=='pointer-overlap':p.layers['one'].following=a
 rejected(p)
for kind in ('limit','checkpoint','indirect','field-update','duplicate-source'):
 p=Program(limit=2 if kind=='limit' else 0);a=p.data('a',32);b=p.data('b',32)
 p.layer('replace',[Replace('target','template')],next='target')
 p.layer('target',[Copy(8,b,a)])
 rows=[Copy(1,Field('target',0,'n'),a)] if kind=='field-update' else [Copy(8,b,a)]
 ptr=p.pointer('ptr',Value('entry','target')) if kind=='indirect' else None
 p.layer('template',rows,next=ptr,checkpoint=kind=='checkpoint')
 if kind=='duplicate-source':
    p.layer('other',[Copy(8,b,a)])
    p.layers['replace'].copies.append(Replace('other','template'))
 rejected(p)
print('DIRECT CLI PASSED: persistence, integrity, live input, inherited channels, seekable stdin, resume, rejected sources')
