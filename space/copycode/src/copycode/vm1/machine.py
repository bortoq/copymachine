"""Validated four-index ISA codec and schedule verifier, emulator rev1."""
from dataclasses import dataclass
import hashlib
import json

NOP = (0, 0, 0, 0)

def field(data, at, width):
    return sum(((data[(at+k)//8] >> (7-(at+k)%8)) & 1) << k for k in range(width))

def put(data, at, width, value):
    if not 0 <= value < 1 << width:
        raise ValueError('field overflow')
    for k in range(width):
        mask=128 >> ((at+k)%8)
        data[(at+k)//8] = (data[(at+k)//8] & ~mask) | (mask if value >> k & 1 else 0)

@dataclass(frozen=True)
class Format:
    size: int = 65520
    slots: int = 8

    def __post_init__(self):
        if self.size < 1 or self.a > 64 or self.slots < 1 or self.layer_bits > self.size or self.size+5 >= 1 << self.a:
            raise ValueError('invalid emulator processor/memory/channel configuration')

    @property
    def a(self): return self.size.bit_length()
    @property
    def instruction_bits(self): return 4*self.a
    @property
    def layer_bits(self): return self.instruction_bits*self.slots
    @property
    def layer_bytes(self): return (self.layer_bits+7)//8
    @property
    def image_bytes(self): return (self.size+7)//8
    @property
    def channels(self): return dict(zip(('sys','stdin','stdout','debug','status','snapshot'),range(self.size,self.size+6)))

    def copy(self, n, dst, src):
        if n < 0: raise ValueError('negative length')
        if not n: return NOP
        return (dst, dst if dst >= self.size else dst+n, src, src if src >= self.size else src+n)

    def validate(self, rows):
        rows=list(rows)
        if len(rows) > self.slots: raise ValueError('too many slots')
        spans=[];devices=set();requests=0
        for row in rows:
            if len(row)!=4 or any(not isinstance(x,int) or not 0<=x<1<<self.a for x in row):
                raise ValueError('four unsigned A-bit endpoints required')
            dl,dh,sl,sh=row
            dc=dl==dh and dl>=self.size;sc=sl==sh and sl>=self.size
            if dc and sc: raise ValueError('channel to channel')
            if dc or sc:
                channel=dl if dc else sl
                lo,hi=(sl,sh) if dc else (dl,dh)
                if lo==hi: continue
                if channel!=self.size:
                    if (hi-lo)%8: raise ValueError('data channel length must be whole bytes')
                    if channel in devices: raise ValueError('multiple operations on data channel')
                    devices.add(channel)
                else:
                    # SYS consumes its entire record, independently of the nominal copy count.
                    if dc:
                        requests+=1
                        if requests>1:raise ValueError('multiple SYS requests')
                    hi=max(hi,lo+(120+self.a if dc else 97+self.a))
                spans.append((lo,hi))
            elif sl==sh: continue
            else:
                if dh-dl!=sh-sl: raise ValueError('unequal lengths')
                spans.extend(((dl,dh),(sl,sh)))
        if any(not 0<=lo<hi<=self.size for lo,hi in spans):raise ValueError('out of memory bounds')
        spans.sort()
        if any(hi>lo2 for (_,hi),(lo2,_) in zip(spans,spans[1:])):raise ValueError('overlapping operands including sources')
        return spans

    def layer(self, rows):
        rows=list(rows);self.validate(rows)
        data=bytearray(self.layer_bytes)
        for slot,row in enumerate(rows):
            for i,value in enumerate(row):put(data,(4*slot+i)*self.a,self.a,value)
        return bytes(data)

    def decode(self, data):
        return [tuple(field(data,(4*slot+i)*self.a,self.a) for i in range(4)) for slot in range(self.slots)]

    def describe(self):
        value=dict(schema='copycode-vm1-rev1',size=self.size,slots=self.slots,address_bits=self.a,instruction_bits=self.instruction_bits,channels=self.channels,bit_order='msb-first-bytes-lsb-first-fields',tick='completion-at-end',overlap='all-memory-operands-disjoint')
        value['layout_id']=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return value
