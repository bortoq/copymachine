"""Audit every physical operand of an actual indexed, packed pForth launch."""
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/pforth'))
import common
import dependencies
from vm2compile.artifact import load
from copycode.vm1.machine import field
from copycode.hostpaths import output_dir

image=output_dir(ROOT, 'build')/'pforth';payload,m=load(image);mapping=json.loads(payload['map.json'])
binary=output_dir(dependencies.VM2_ROOT, 'build')/'checked-emulator'
out=output_dir(ROOT, 'build')/'verification/native-audit';out.mkdir(parents=True,exist_ok=True);snapshot=out/'snapshot.bin'
source=b'1 2 + .';command=[str(ROOT/'pforth'),'run',str(image),'--snapshot',str(snapshot)]
env=dict(os.environ,EMULATOR=str(binary),VM1_AUDIT_ENTRY=str(m['entry_bits']))
start=time.monotonic();r=subprocess.run(command,input=source,capture_output=True,env=env,timeout=150)
(out/'input.fth').write_bytes(source);(out/'stdout.bin').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr)
assert r.returncode==0 and r.stdout==b'3 ',(r.returncode,r.stdout,r.stderr[-1000:])
ticks=int(re.search(rb'VM1_AUDIT_TICKS=(\d+)',r.stderr)[1]);raw=snapshot.read_bytes();reg=mapping['regions']['registers']['at']
assert len(raw)==len(payload['image.bin']) and field(raw,reg+m['rv32i']['status_offset'],32)==10 and field(raw,reg+m['rv32i']['exit_offset'],32)==0
report=dict(schema='pforth-native-audit-v1',command=command,seconds=time.monotonic()-start,ticks=ticks,input_hex=source.hex(),stdout_hex=r.stdout.hex(),stderr=r.stderr.decode(),snapshot_sha256=hashlib.sha256(raw).hexdigest(),manifest_sha256=hashlib.sha256((image/'manifest.json').read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS native pForth audit: every tick src/src, RAW memory operands, patched fields, fetch and devices;',ticks,'ticks,',round(report['seconds'],3),'s')
