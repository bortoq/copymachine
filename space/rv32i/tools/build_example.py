"""Build a finite RV32I guest; the universal interpreter is identical for all guests."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
from direct_target import compile_image
from vm2compile.artifact import save
words=[0x02a00513,0x05d00893,0x00000073] # a0=42, a7=exit, ECALL
from copycode.hostpaths import output_dir

target=output_dir(ROOT, 'build')/'example'
if target.exists():shutil.rmtree(target)
payload,m=compile_image(b''.join(w.to_bytes(4,'little') for w in words))
save(target,payload,m)
print('Stored example:',target)
