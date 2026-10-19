"""Symbolic copycode. Raw executable addresses are intentionally not an input ABI."""
from dataclasses import dataclass,field as dataclass_field

@dataclass(frozen=True)
class Memory:
    name:str
    offset:int=0
    def __add__(self,n):return Memory(self.name,self.offset+n)
@dataclass(frozen=True)
class Field:
    layer:str
    slot:int
    name:str
    offset:int=0
    def __add__(self,n):return Field(self.layer,self.slot,self.name,self.offset+n)
@dataclass(frozen=True)
class Channel:
    name:str
@dataclass(frozen=True)
class Value:
    """An initial numeric value resolved after native placement."""
    kind:str
    name:str=''
    offset:int=0
@dataclass(frozen=True)
class LayerBits:pass
@dataclass(frozen=True)
class SysWidth:
    kind:str
@dataclass(frozen=True)
class Copy:
    n:object
    dst:object
    src:object
@dataclass(frozen=True)
class Replace:
    dst:str
    src:str
@dataclass
class Region:
    name:str
    bits:int
    value:int=0
    align:int=8
    at:object=None
    relocations:list=dataclass_field(default_factory=list)
    table:object=None
    record:object=None
@dataclass
class Layer:
    name:str
    copies:list
    following:object=None
    checkpoint:bool=False
    checkpoint_stop:bool=False

class Program:
    def __init__(self,*,size=65520,slots=8,entry=None,limit=0):
        self.size=size;self.slots=slots;self.entry=entry;self.limit=limit
        self.regions={};self.layers={}
    def data(self,name,bits,value=0,*,align=8,at=None):
        if name in self.regions:raise ValueError('duplicate region '+name)
        self.regions[name]=Region(name,bits,value,align,at);return Memory(name)
    def bytes(self,name,data,**options):
        value=sum(((data[k//8]>>(7-k%8))&1)<<k for k in range(len(data)*8))
        return self.data(name,len(data)*8,value,**options)
    def table(self,name,values,width,*,stride_bits=None):
        values=list(values)
        if not values or len(values)&(len(values)-1) or width<1:raise ValueError('power-of-two LUT size and positive width required')
        stride_bits=width.bit_length() if stride_bits is None else stride_bits
        if stride_bits<0 or 1<<stride_bits<=width:raise ValueError('LUT stride must exceed width for independent endpoint patches')
        stride=1<<stride_bits;bits=stride*len(values);value=0
        for index,item in enumerate(values):
            if not isinstance(item,int) or not 0<=item<1<<width:raise ValueError('LUT value overflow')
            value|=item<<(index*stride)
        ref=self.data(name,bits,value,align=bits)
        self.regions[name].table=dict(width=width,stride_bits=stride_bits,entries=len(values))
        return ref
    def pointer(self,name,value,**options):
        ref=self.data(name,0,**options);self.regions[name].relocations.append((0,'address',value));return ref
    def record(self,name,fields,**options):
        ref=self.data(name,0,**options);self.regions[name].record=list(fields);return ref
    def layer(self,name,copies=(),*,next=None,checkpoint=False,checkpoint_stop=False):
        if name in self.layers:raise ValueError('duplicate layer '+name)
        self.layers[name]=Layer(name,list(copies),next,checkpoint,checkpoint_stop)
        if self.entry is None:self.entry=name
        return self
    def source(self):
        def encode(value):
            if isinstance(value,int) or value is None or isinstance(value,str):return value
            if isinstance(value,(Memory,Field,Channel,Value,LayerBits,SysWidth)):
                return dict(type=type(value).__name__,**value.__dict__)
            raise ValueError('unsupported source value '+repr(value))
        return dict(schema='vm2-symbolic-v1',size=self.size,slots=self.slots,entry=self.entry,limit=self.limit,
            data=[dict(name=r.name,bits=encode(r.bits),value=hex(r.value),align=r.align,at=r.at,table=r.table,
                       record=[[name,width,encode(value)] for name,width,value in r.record] if r.record is not None else None,
                       relocations=[[at,width,encode(v)] for at,width,v in r.relocations]) for r in self.regions.values()],
            layers=[dict(name=l.name,next=encode(l.following),checkpoint=l.checkpoint,copies=[
                dict(type='Copy',n=encode(c.n),dst=encode(c.dst),src=encode(c.src)) if isinstance(c,Copy)
                else dict(type='Replace',dst=c.dst,src=c.src) for c in l.copies],
                **({'checkpoint_stop':True} if l.checkpoint_stop else {})) for l in self.layers.values()])
    @classmethod
    def load(cls,obj):
        if not isinstance(obj,dict) or obj.get('schema')!='vm2-symbolic-v1':raise ValueError('unsupported symbolic source schema')
        def decode(v):
            if isinstance(v,dict):
                kinds={c.__name__:c for c in (Memory,Field,Channel,Value,LayerBits,SysWidth)}
                if v.get('type') not in kinds:raise ValueError('unsupported typed reference')
                return kinds[v['type']](**{k:value for k,value in v.items() if k!='type'})
            if v is None or isinstance(v,(int,str)):return v
            raise ValueError('invalid reference')
        p=cls(size=obj['size'],slots=obj['slots'],entry=obj.get('entry'),limit=obj.get('limit',0))
        for r in obj.get('data',[]):
            p.data(r['name'],decode(r['bits']),int(str(r.get('value','0')),0),align=r.get('align',8),at=r.get('at'))
            p.regions[r['name']].table=r.get('table')
            p.regions[r['name']].record=[(n,w,decode(v)) for n,w,v in r['record']] if r.get('record') is not None else None
            p.regions[r['name']].relocations=[(at,width,decode(v)) for at,width,v in r.get('relocations',[])]
        for l in obj['layers']:
            ops=[]
            for c in l.get('copies',[]):
                if c['type']=='Copy':ops.append(Copy(decode(c['n']),decode(c['dst']),decode(c['src'])))
                elif c['type']=='Replace':ops.append(Replace(c['dst'],c['src']))
                else:raise ValueError('unsupported operation')
            p.layer(l['name'],ops,next=decode(l.get('next')),checkpoint=l.get('checkpoint',False),checkpoint_stop=l.get('checkpoint_stop',False))
        return p
