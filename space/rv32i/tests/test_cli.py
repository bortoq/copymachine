"""Stored artifact CLI: launch after deleting source, exit code, faults and validation."""
import os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
from direct_target import compile_image
from vm2compile.artifact import save
CLI=ROOT/'rv32i'
with tempfile.TemporaryDirectory() as tmp:
    d=Path(tmp);source=d/'program';source.write_bytes(b''.join(w.to_bytes(4,'little') for w in (0x02a00513,0x05d00893,0x73)))
    payload,m=compile_image(source.read_bytes());save(d/'artifact',payload,m);source.unlink()
    for _ in range(2):
        r=subprocess.run([str(CLI),'run',str(d/'artifact')],input=b'',capture_output=True,timeout=20)
        assert (r.returncode,r.stdout,r.stderr)==(42,b'',b''),r
    r=subprocess.run([str(CLI),'run',str(d/'artifact'),'--physical-ticks','-1'],input=b'',capture_output=True,timeout=10)
    assert r.returncode==2
    r=subprocess.run([str(CLI),'build',str(d/'missing'),'-o',str(d/'bad')],capture_output=True,timeout=10)
    assert r.returncode==2 and not (d/'bad').exists()
print('PASS RV32I CLI: source-free repeated runs, guest exit, invalid inputs')
