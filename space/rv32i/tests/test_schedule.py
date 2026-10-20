"""Direct scheduler regressions: src/src, RAW, WAR, WAW and patched targets."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
from rv32i import Copy,Field

# The direct adapter delegates placement to the shared interval planner.
from vm2compile.legacy import adapt
from vm2compile.model import Field as SymbolicField,Channel

def packed(rows,packing=True):
    return adapt({'block':(rows,Copy(0,0,0))},[dict(name='memory',at=0,bits=100000)],
                 address_bits=24,count_bits=23,entry='block',packing=packing)
def home(program,dst,src):
    for name,layer in program.layers.items():
        for op in layer.copies:
            if getattr(op.dst,'offset',None)==dst and getattr(op.src,'offset',None)==src:return name
    raise AssertionError('copy missing')
for rows in ([Copy(8,50000,60000),Copy(8,51000,60000)],
             [Copy(8,50000,60000),Copy(8,51000,50000)],
             [Copy(8,50000,60000),Copy(8,60000,51000)],
             [Copy(8,50000,60000),Copy(8,50000,51000)]):
    p=packed(rows);assert home(p,rows[0].dst,rows[0].src)!=home(p,rows[1].dst,rows[1].src)
rows=[Copy(8,50000,60000),Copy(8,51000,61000)]
p=packed(rows);assert home(p,50000,60000)==home(p,51000,61000)
p=packed(rows,False);assert home(p,50000,60000)!=home(p,51000,61000)
rows=[Copy(8,50000+32*i,60000+32*i) for i in range(8)]
p=packed(rows);assert sorted(len(l.copies) for l in p.layers.values())==[0,1,7]
target=Copy(8,50000,60000)
p=packed([Copy(8,Field(target,'src',0),70000),Copy(8,Field(target,'src',8),71000),target])
patches=p.layers['legacy:block:0'].copies;assert len(patches)==2
# Direct ABI updates finish before the next logical layer: one layer suffices.
assert all(isinstance(c.dst,SymbolicField) and c.dst.layer=='legacy:block:1' and c.dst.slot==0 for c in patches)
p=packed([Copy(8,50000,60000),Copy(0,51000,Channel('stdin')),Copy(8,52000,62000)])
assert [len(l.copies) for l in p.layers.values()]==[1,1,1,0]
print('PASS direct packing: independent copies, slot limit, src/src, RAW/WAR/WAW, field relocation and patch/fetch delay, channel barrier and serial control')

# A dynamically sourced patch must still register its known code-field write.
target=Copy(8,50000,60000)
patch=Copy(8,Field(target,'src'),70000)
source_patch=Copy(8,Field(patch,'src'),71000)
p=packed([source_patch,patch,target])
assert home(p,50000,60000)=='legacy:block:2'
print('PASS dependent dynamic patches retain both fetch-delay constraints')
