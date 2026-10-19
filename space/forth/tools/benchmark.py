"""Paired cold Forth executions: linear/serial, indexed/serial, indexed/packed."""
import hashlib,json,os,re,subprocess,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/pforth'))
from build import build
from common import RV32I_ROOT
import dependencies
from vm2compile.artifact import load
from copycode.vm1.machine import field
from copycode.hostpaths import output_dir

out=output_dir(ROOT, 'build')/'performance';out.mkdir(parents=True,exist_ok=True)
variants=[('linear-serial',False,False),('index-serial',True,False),('index-packed',True,True)]
rows=[];identities={}
for name,indexed,packing in variants:
 image=out/name
 if image.exists():shutil.rmtree(image)
 start=time.monotonic();m=build(image,indexed=indexed,packing=packing)
 identities[name]=dict(compile_seconds=time.monotonic()-start,program_sha256=m['pforth']['program_sha256'],manifest_sha256=hashlib.sha256((image/'manifest.json').read_bytes()).hexdigest(),code_bits=m['code_bits'],source_layers=m['rv32i']['source_layers'],vm1=m['vm1'],index=m['pforth']['index'])
 print('Built',name,'layers',m['rv32i']['source_layers'],flush=True)
assert identities['index-serial']['program_sha256']==identities['index-packed']['program_sha256']
# Same exact inputs, one real native process per case/variant; no steady-state claim.
cases=[('lookup',b'0 dup drop drop',b'',0),('arithmetic',b'1 2 + .',b'3 ',0),('definition',b': sq dup * ; 7 sq .',b'49 ',0)]
for case,source,expected,code in cases:
 for name,_,_ in variants:
  image=out/name;payload,m=load(image);mapping=json.loads(payload['map.json']);reg=mapping['regions']['registers']['at'];guest=mapping['regions']['guest']['at']
  folder=out/case/name;folder.mkdir(parents=True,exist_ok=True);snapshot=folder/'snapshot.bin'
  env=dict(os.environ,EMULATOR=str(output_dir(ROOT, 'build')/'observe-emulator'),PFORTH_REG_BITS=str(reg))
  command=[str(ROOT/'pforth'),'run',str(image),'--snapshot',str(snapshot)]
  (folder/'input.fth').write_bytes(source);(folder/'command.json').write_text(json.dumps(command,indent=2)+'\n')
  start=time.monotonic();r=subprocess.run(command,input=source,capture_output=True,env=env,timeout=150);elapsed=time.monotonic()-start
  (folder/'stdout.bin').write_bytes(r.stdout);(folder/'stderr.txt').write_bytes(r.stderr)
  assert r.returncode==code and r.stdout==expected,(case,name,r.returncode,r.stdout,r.stderr[-1000:])
  raw=snapshot.read_bytes();status=field(raw,reg+m['rv32i']['status_offset'],32);exit_code=field(raw,reg+m['rv32i']['exit_offset'],32)
  assert len(raw)==len(payload['image.bin']) and status==10 and exit_code==code
  ticks=int(re.search(rb'stop ticks=(\d+)',r.stderr)[1])
  row=dict(case=case,variant=name,seconds=elapsed,ticks=ticks,input_hex=source.hex(),stdout_hex=r.stdout.hex(),status=status,exit_code=exit_code,
           guest_sha256=hashlib.sha256(raw[guest//8:guest//8+m['rv32i']['memory_bytes']]).hexdigest(),registers=[field(raw,reg+32*i,32) for i in range(34)],
           snapshot_sha256=hashlib.sha256(raw).hexdigest(),trace=r.stderr.decode())
  if name=='index-packed':
   previous=next(v for v in rows if v['case']==case and v['variant']=='index-serial')
   assert row['guest_sha256']==previous['guest_sha256'] and row['registers']==previous['registers'],case
  rows.append(row)
  result=dict(schema='pforth-performance-v1',notes='Sequential cold launches on one CPU, nice=15. Includes startup, bootstrap, pForth initialization and final snapshot. Sparse observer adds equal tick logging to all variants; no steady-state claim.',variants=identities,cases=rows,
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'pforth',*sorted((ROOT/'scripts/pforth').glob('*.py')),*sorted((ROOT/'runtime/pforth').glob('*.[ch]')),Path(__file__)]},
    dependencies={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [RV32I_ROOT/'modules/direct_target.py',dependencies.VM2_ROOT/'vm2compile/legacy.py',dependencies.COPYCODE_ROOT/'src/copycode/vm1/schedule.py',dependencies.EMULATOR_ROOT/'src/runtime.c',output_dir(dependencies.EMULATOR_ROOT, 'build')/'bitcopy/emulator',output_dir(ROOT, 'build')/'observe-emulator']})
  (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
  print('PASS benchmark',case,name,round(elapsed,3),'s',ticks,'ticks',flush=True)
for case,_,_,_ in cases:
 samples={r['variant']:r for r in rows if r['case']==case}
 before=samples['linear-serial'];hashed=samples['index-serial'];packed=samples['index-packed']
 print(case,'index speedup',round(before['seconds']/hashed['seconds'],2),'packing speedup',round(hashed['seconds']/packed['seconds'],2),'total',round(before['seconds']/packed['seconds'],2),flush=True)
