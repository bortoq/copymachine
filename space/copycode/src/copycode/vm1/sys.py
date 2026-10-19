"""Guest SYS records, schema read from the declared emulator dependency."""
from pathlib import Path
from .machine import put
from ..vm2.protocol import parse

def schema(path):
    return parse(Path(path))

def record(fmt, schema_path, kind, **values):
    ops,req,rsp,_=schema(schema_path)
    if kind not in ('req','rsp'):raise ValueError('record kind')
    rows=req if kind=='req' else rsp
    fields={};at=0
    for name,literal,tag in rows:
        if tag=='PK_NF':raise ValueError('legacy VM2 schema is incompatible with emulator')
        width=literal if tag=='PK_LIT' else fmt.a
        fields[name]=(at,width);at+=width
    if set(values)-fields.keys():raise ValueError('unknown SYS field')
    data=bytearray((at+7)//8)
    for name,value in values.items():
        if name=='op' and isinstance(value,str):value=dict(ops)[value]
        offset,width=fields[name];put(data,offset,width,value)
    return bytes(data),at

def fstat(program, channel, request, answer, schema_path):
    """Submit and collect on separate ticks; callers use the reply later."""
    payload,n=record(program.fmt,schema_path,'req',op='FSTAT',chan=channel)
    _,m=record(program.fmt,schema_path,'rsp')
    program.store(request,payload)
    program.layer([program.fmt.copy(n,program.fmt.channels['sys'],request)])
    program.layer([program.fmt.copy(m,answer,program.fmt.channels['sys'])])
    return m
