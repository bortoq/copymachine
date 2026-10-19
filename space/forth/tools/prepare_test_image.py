"""Amortize cold guest initialization; stop before the first guest read."""
import hashlib,json,os,subprocess,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/pforth'))
from common import RV32I_ROOT
from vm2compile.artifact import load,resume,save
from copycode.hostpaths import output_dir

cold=output_dir(ROOT, 'build')/'pforth';target=output_dir(ROOT, 'build')/'initialized';folder=output_dir(ROOT, 'build')/'verification/initialize';folder.mkdir(parents=True,exist_ok=True)
payload,m=load(cold);mapping=json.loads(payload['map.json']);raw=folder/'snapshot.bin'
command=[str(output_dir(ROOT, 'build')/'observe-emulator'),'-s',str(m['vm1']['size']),'-p',str(m['vm1']['slots'])]
env=dict(os.environ,PFORTH_REG_BITS=str(mapping['regions']['registers']['at']),PFORTH_STOP_AT_READ='1',PFORTH_DUMP=str(raw))
started=time.monotonic();r=subprocess.run(command,input=payload['boot.bin'],capture_output=True,env=env,timeout=170)
(folder/'stderr.txt').write_bytes(r.stderr);(folder/'stdout.bin').write_bytes(r.stdout);(folder/'command.json').write_text(json.dumps(command,indent=2)+'\n')
assert r.returncode==0 and r.stdout==b'',(r.returncode,r.stderr[-1000:])
from copycode.vm1.machine import field
assert field(raw.read_bytes(),mapping['regions']['registers']['at']+1024,32)==20
payload,m=resume(cold,raw)
if target.exists():shutil.rmtree(target)
save(target,payload,m)
(folder/'result.json').write_text(json.dumps(dict(seconds=time.monotonic()-started,snapshot_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),cold_manifest_sha256=hashlib.sha256((cold/'manifest.json').read_bytes()).hexdigest()),indent=2)+'\n')
print('PASS cold pForth initialized inside emulator; paused before first read',round(time.monotonic()-started,3),'seconds',flush=True)
