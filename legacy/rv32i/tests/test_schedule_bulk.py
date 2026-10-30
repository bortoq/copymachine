"""Historical bulk schedule checks; not part of normal make check."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"modules"))
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

