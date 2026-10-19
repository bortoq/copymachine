"""Rebuild deterministic API/source and generated-image identities."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from copycode.vm1.machine import Format
from copycode.vm1.program import Program
from copycode.vm1.lib import add8,reverse_byte
from copycode.vm2.boundary import Program as V2Program,boot_stream
from copycode.vm2.terminal import TerminalFragment

contracts=[]
for p in sorted((ROOT/'src').rglob('*.py')):
    text=p.read_text();tree=ast.parse(text)
    imports=sorted({ast.unparse(n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))})
    api=[]
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
            rows=[node]+(node.body if isinstance(node,ast.ClassDef) else [])
            for n in rows:
                if not isinstance(n,(ast.FunctionDef,ast.ClassDef)):continue
                api.append(dict(name=(node.name+'.' if n is not node else '')+n.name,
                    signature=ast.unparse(n.args) if isinstance(n,ast.FunctionDef) else None,
                    contract=ast.get_docstring(n),line=n.lineno))
    contracts.append(dict(source=str(p.relative_to(ROOT)),architecture='vm1-rev1' if '/vm1/' in str(p) else 'vm2-triples' if '/vm2/' in str(p) else 'host',source_bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),dependencies=imports,api=api))
(ROOT/'doc/contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
measurements=[]
def save(name,target,data,**extra):
    measurements.append(dict(name=name,target=target,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),**extra))
f=Format();p=Program();add8(p);image=p.image()
save('add8','vm1-rev1',image,generated_code_bits=40*f.layer_bits,code_and_stop_bits=41*f.layer_bits,application_layers=40,space_bits=f.size,slots=f.slots)
for module in ['byte_to_bits','bits_to_byte']:
    p=Program()
    for rows in reverse_byte(f,44008,44000):p.layer(rows)
    save(module,'vm1-rev1',p.image(),generated_code_bits=len(p.layers)*f.layer_bits,application_layers=len(p.layers),space_bits=f.size,slots=f.slots)
for mode in ['full','channels']:
    p=V2Program(trace=mode,code_base=8192)
    p.step([(8,1088,1024)]);p.step([(8,65522,1088)]);p.checkpoint()
    image=p.finish();save('monitor-checkpoint-'+mode,'vm2-triples',image,library_bytes=(p.at-p.base)//8,layers=len(p.chain),boot_bytes=len(boot_stream(image,65520,8)),layout_id=p.fmt.description['layout_id'])
t=TerminalFragment(65520,8,32768,snapshot=True,exit_code=7)
save('terminal','vm2-triples',bytes(t.data),layers=len(t.chain),report_ticks=t.report_ticks,layout_id=t.fmt.description['layout_id'])
(ROOT/'doc/generated.json').write_text(json.dumps(measurements,indent=2)+'\n')
print('Recorded',len(contracts),'module contracts and',len(measurements),'generated identities')
