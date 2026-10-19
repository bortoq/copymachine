"""Legacy scheduler regressions: src/src, RAW, WAR, WAW and patched targets."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
from rv32i import Copy,Field,Layout
from rv32i_bulk import BulkImage
b=BulkImage(memory_bytes=65536,layout=Layout(8*1024*1024))
try:BulkImage(phase_markers=True)
except ValueError:pass
else:raise AssertionError('unsupported phase-only profile accepted')
for rows in ([Copy(8,50000,60000),Copy(8,51000,60000)],
             [Copy(8,50000,60000),Copy(8,51000,50000)],
             [Copy(8,50000,60000),Copy(8,60000,51000)],
             [Copy(8,50000,60000),Copy(8,50000,51000)]):
    b._level(rows,None);assert rows[1]._level>rows[0]._level
target=Copy(8,50000,60000);patch=Copy(8,Field(target,'src'),70000)
b._level([patch,target],None);assert target._level>=patch._level+2
rows=[Copy(8,50000,60000),Copy(8,51000,61000)]
b._level(rows,None);assert rows[0]._level==rows[1]._level
print('PASS legacy schedule: src/src, RAW/WAR/WAW, patch/fetch gap, independent packing')

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
assert all(isinstance(c.dst,SymbolicField) and c.dst.layer=='legacy:block:2' and c.dst.slot==0 for c in patches)
assert not p.layers['legacy:block:1'].copies
p=packed([Copy(8,50000,60000),Copy(0,51000,Channel('stdin')),Copy(8,52000,62000)])
assert [len(l.copies) for l in p.layers.values()]==[1,1,1,0]
print('PASS direct packing: independent copies, slot limit, src/src, RAW/WAR/WAW, field relocation and patch/fetch delay, channel barrier and serial control')

# A dynamically sourced patch must still register its known code-field write.
target=Copy(8,50000,60000)
patch=Copy(8,Field(target,'src'),70000)
source_patch=Copy(8,Field(patch,'src'),71000)
p=packed([source_patch,patch,target])
assert home(p,50000,60000)=='legacy:block:4'
print('PASS dependent dynamic patches retain both fetch-delay constraints')
