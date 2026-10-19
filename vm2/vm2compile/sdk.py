"""One native ABI adapter for builders, channels and future guest linkers."""
import os
from pathlib import Path
from copycode.vm1.sys import schema
from .model import Value,Channel,SysWidth,Copy,Memory

def protocol_path():
    installed=Path(__file__).with_name('vm1-proto.def')
    if 'VM1_ROOT' not in os.environ and installed.is_file():return installed
    root=Path(__file__).resolve().parents[1]
    default=root/'vendor/vm1' if (root/'vendor/vm1').is_dir() else root.parent/'vm1'
    return Path(os.environ.get('VM1_ROOT',default))/'src/proto.def'

def sys_record(program,name,kind='req',**values):
    ops,req,rsp,_=schema(protocol_path())
    if kind not in ('req','rsp'):raise ValueError('SYS record kind')
    fields=req if kind=='req' else rsp;known={n for n,_,_ in fields}
    if set(values)-known:raise ValueError('unknown SYS field')
    entries=[]
    for field,literal,tag in fields:
        if tag=='PK_NF':raise ValueError('legacy SYS widths are not native ABI')
        width=literal if tag=='PK_LIT' else 'address'
        value=values.get(field,0)
        if field=='op' and isinstance(value,str):value=dict(ops)[value]
        if field=='chan' and isinstance(value,Channel):value=Value('channel',value.name)
        entries.append((field,width,value))
    return program.record(name,entries)

def request(record):return Copy(SysWidth('req'),Channel('sys'),record)
def response(record):return Copy(SysWidth('rsp'),record,Channel('sys'))
def stdin_position(offset=0):
    """SEEK_SET of an application offset; boot prefix is resolved in artifact."""
    return Value('stdin-origin',offset=offset)

def construct(program,layer,slot,*,n,dst,src):
    """Build a description in an existing typed slot; commit after the layer.

    Memory arguments name stored numeric values; Value arguments are symbolic
    constants resolved at link time. There is no host runtime code generation.
    """
    from .model import Field
    result=[]
    for attr,value in (('n',n),('dst',dst),('src',src)):
        if isinstance(value,Value):
            name='construct:'+str(len(program.regions));value=program.pointer(name,value)
        elif isinstance(value,int):
            name='construct:'+str(len(program.regions));value=program.data(name,'address',value)
        if not isinstance(value,(Memory,Field)):raise ValueError('description field needs a stored value or relocation')
        result.append(Copy('count' if attr=='n' else 'address',Field(layer,slot,attr),value))
    return result
