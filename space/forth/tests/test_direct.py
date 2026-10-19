"""pForth user programs execute in stored emulator copycode; retain native snapshots."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/pforth'))
from common import RV32I_ROOT
import dependencies
from vm2compile.artifact import load
from copycode.vm1.machine import field
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--case');selected=parser.parse_args().case
timeout=max(1,int(os.environ.get('PFORTH_TEST_SECONDS','360'))-10)
from copycode.hostpaths import output_dir

image=output_dir(ROOT, 'build')/'initialized';out=output_dir(ROOT, 'build')/'verification';out.mkdir(parents=True,exist_ok=True)
payload,manifest=load(image);mapping=json.loads(payload['map.json']);reg=mapping['regions']['registers']['at'];guest=mapping['regions']['guest']['at'];rows=json.loads((out/'results.json').read_text()) if (out/'results.json').exists() else []

def case(name,source,expected,code=0,*,live=False,input_error=False,output_error=False,job=None):
 if selected and name!=selected:return
 folder=out/name;folder.mkdir(exist_ok=True);(folder/'input.fth').write_bytes(source);snapshot=folder/'snapshot.bin'
 command=[str(ROOT/'pforth'),'run-job' if job else 'run',str(job or image),'--snapshot',str(snapshot)]
 (folder/'command.json').write_text(json.dumps(command,indent=2)+'\n');started=time.monotonic()
 with open('/dev/full','wb') as full, (folder/'stdout.bin').open('wb') as stdout_file, (folder/'stderr.bin').open('wb') as stderr_file:
  # A directory fd gives read(2) EISDIR on the input channel.
  env=dict(os.environ,EMULATOR=str(output_dir(ROOT, 'build')/'observe-emulator'),PFORTH_REG_BITS=str(reg))
  if input_error:env['PFORTH_INPUT_ERROR']=str(folder)
  if name=='job':env['EMULATOR']=os.environ.get('EMULATOR',str(output_dir(dependencies.EMULATOR_ROOT, 'build')/'bitcopy/emulator'))
  fd=None
  try:
   p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=full if output_error else stdout_file,stderr=stderr_file,env=env)
   try:
    if live:
     p.stdin.write(source);p.stdin.flush();p.wait(timeout=timeout);p.stdin.close()
    else:p.communicate(source,timeout=timeout)
   except BaseException:p.kill();p.wait();raise
  finally:
   if fd is not None:os.close(fd)
 stdout=(folder/'stdout.bin').read_bytes();stderr=(folder/'stderr.bin').read_bytes()
 assert p.returncode==code,(name,p.returncode,stderr[-500:])
 if expected is not None:assert stdout==expected,(name,stdout,expected)
 else:assert b'NO_SUCH_WORD' in stdout
 raw=snapshot.read_bytes();assert len(raw)==len(payload['image.bin'])
 assert field(raw,reg+manifest['rv32i']['status_offset'],32)==10
 assert field(raw,reg+manifest['rv32i']['exit_offset'],32)==code
 if name.startswith('language'):
  initial=(output_dir(ROOT, 'build')/'pforth.build/program.bin').read_bytes()
  for word in ({'language':(b'SQUARE',),'language-control':(b'SUM-TEN',),'language-memory':(b'AREA',)}[name]):
   assert word not in initial and word in raw[guest//8:guest//8+524288],word
 row=dict(name=name,exit_code=code,seconds=time.monotonic()-started,stdout_hex=stdout.hex(),stderr_hex=stderr.hex(),snapshot_sha256=hashlib.sha256(raw).hexdigest(),image_manifest_sha256=hashlib.sha256((image/'manifest.json').read_bytes()).hexdigest())
 rows[:]=[r for r in rows if r["name"]!=name];rows.append(row);(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS pForth',name,round(row['seconds'],3),'seconds',flush=True)

case('language',b'1 2 + . cr\n: square dup * ; 7 square . cr\n7 square . cr\nbye\n999 .\n',b'3 \n49 \n49 \n\n',live=True)
case('language-control',b': sign-test 0< if 111 else 222 then ; -1 sign-test . 1 sign-test . cr\n: sum-ten 0 10 0 do i + loop ; sum-ten . cr\n: down begin dup . 1- dup 0= until drop ; 3 down cr\nbye\n',b'111 222 \n45 \n3 2 1 \n\n')
case('language-memory',b'variable counter 123 counter ! counter @ . cr\nhex FFFFFFFF 1 + . decimal cr\ncreate area 60000 allot 42 area 59999 + c! area 59999 + c@ . cr\nbye\n',b'123 \n0 \n42 \n\n')
case('index-semantics',b""": abc 1 ;
: abc abc 1 + ; aBc .
: now 77 . ; immediate
: uses-now now 5 ; uses-now .
90 latest 1+ c! zses-now .
: abcd 6 ; 90 latest 4 + ! abcz .
latest 1+ 1 89 fill ybcz .
88 pad c! pad latest 1+ 1 cmove xbcz .
variable kept context @ kept !
: tempword 44 ; tempword .
kept @ context ! abc .
latest dup c@ 32 or swap c!
latest dup c@ 32 xor swap c!
context @ kept @ = .
""",b'2 77 5 5 6 6 6 44 2 -1 ')
case('index-length',b': unique-name 9 ; 4 latest c! uniq .',b'9 ')
case('eof',b'1 2 + .',b'3 ')
case('unknown',b'NO_SUCH_WORD\n',None,2)
case('unfinished',b': unfinished 1',b'pForth: unfinished definition\n',2)
case('long-line',b' '*256+b'\n',b'pForth: input line too long\n',2)
case('input-error',b'',b'',1,input_error=True)
case('output-error',b'1 .\n',b'',1,output_error=True)
if selected in (None,'job'):
 from build import job
 jobdir=output_dir(ROOT, 'build')/'job'
 import shutil
 if jobdir.exists():shutil.rmtree(jobdir)
 task=out/'job-source.fth';task.write_bytes(b'6 7 * . cr bye\n');job(image,task,jobdir);task.unlink()
 case('job',b'',b'42 \n\n',job=jobdir)
 original_task=(jobdir/'task.fth').read_bytes()
 (jobdir/'task.fth').write_bytes(b'bad')
 r=subprocess.run([str(ROOT/'pforth'),'run-job',str(jobdir)],capture_output=True,timeout=5)
 assert r.returncode==2 and b'checksum' in r.stderr
 (jobdir/'task.fth').write_bytes(original_task)
 print('PASS pForth job corruption rejected',flush=True)
