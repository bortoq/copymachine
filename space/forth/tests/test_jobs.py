"""Job identity/tampering and persisted artifact validation."""
import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/pforth'))
from build import job
from copycode.hostpaths import output_dir

with tempfile.TemporaryDirectory() as d:
 d=Path(d);source=d/'input.fth';source.write_bytes(b'1 2 + .');target=d/'job'
 job(output_dir(ROOT, 'build')/'pforth',source,target);source.unlink()
 for file in ['task.fth','image/manifest.json','image/boot.bin']:
  p=target/file;original=p.read_bytes();p.write_bytes(original+b'bad')
  r=subprocess.run([str(ROOT/'pforth'),'run-job',str(target)],capture_output=True,timeout=5)
  assert r.returncode==2,(file,r.returncode,r.stderr)
  p.write_bytes(original)
print('PASS deleted task source and corrupt job/task/image rejection')
