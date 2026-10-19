"""Shared streaming runner: real guest exit/status, optional snapshot and rejection paths."""
import json
import os
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'modules'))
from rv32i import Layout
from rv32i_bulk import BulkImage
from machine import space_bits_for_bytes
out=Path('tmp/stream-runner-check');out.mkdir(parents=True,exist_ok=True)
gen=BulkImage(io=True,memory_bytes=65536,layout=Layout(8*1024*1024)).build()
def addi(rd, imm): return (imm &4095)<<20 | rd<<7 | 0x13
for name, words, expected in [('exit7',[addi(10,7), addi(17,93),0x73],7),('illegal',[0],125)]:
 raw,manifest=gen.encode(b''.join(w.to_bytes(4,'little') for w in words))
 image=out/(name+'.bin');image.write_bytes(raw)
 sidecar=image.with_name(image.name+'.json');sidecar.write_text(json.dumps(manifest))
 command=[sys.executable,'-B',str(root/'scripts/rv32i/run.py'),str(image),'--new-emulator']
 result=subprocess.run(command,input=b'',capture_output=True,timeout=30)
 assert result.returncode==expected,(name,result)
 if expected==7:
  dump=out/'snapshot'; before=image.read_bytes()
  result=subprocess.run(command+['--dump-space',str(dump)],input=b'',capture_output=True,timeout=30)
  assert result.returncode==7 and dump.stat().st_size==(space_bits_for_bytes(8*1024*1024)+7)//8,result
  assert image.read_bytes()==before
  result=subprocess.run(command+['--ticks','1'],input=b'',capture_output=True,timeout=10)
  assert result.returncode==125,result
  sidecar.write_text(json.dumps(dict(manifest,boundary=dict(manifest['boundary'],schema='unknown'))))
  result=subprocess.run(command,input=b'',capture_output=True,timeout=10)
  assert result.returncode==125 and b'incompatible boundary' in result.stderr,result
 print('OK shared streaming runner',name)
