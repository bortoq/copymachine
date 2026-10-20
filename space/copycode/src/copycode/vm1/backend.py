"""Index-code construction and the emulator boot stream (MIT).

Host control model of the guest Forth backend (forth/backend.fth); both must
produce the same bytes. Code is a set of layers placed in cells: a cell is a
power-of-two bit range at least one processor layer long, and cell 0 holds
the entry layer. A layer has slots-1 work rows and a link row in its last slot
that loads the next layer into the processor. Addresses are allocated when a
layer is created, so a forward reference is just an address of a cell that is
filled later. Rows are four-index pseudo-instructions (dl, dh, sl, sh).

The stream is the emulator stdin seed: for each chunk a loader layer and its
payload, finally the entry layer. Contiguous puts (gaps up to 32 bytes) share
a chunk of at most chunk_bytes.
"""
from dataclasses import dataclass

REV=bytes(int(f'{b:08b}'[::-1],2) for b in range(256))

@dataclass(frozen=True)
class Machine:
    size: int
    slots: int = 8
    cell_bits: int = 1024
    chunk_bytes: int = 4096
    def __post_init__(self):
        if self.a%8 or self.slots<8 or self.size%8 or self.size+5>=1<<self.a:
            raise ValueError('byte-sized address fields, at least 8 slots and a byte-sized space required')
        if self.cell_bits&(self.cell_bits-1) or self.cell_bits<self.layer_bits:
            raise ValueError('cell must be a power of two holding a layer')
        if not 0<self.chunk_bytes<1<<(self.a-4):raise ValueError('invalid chunk size')
    @property
    def a(self):return self.size.bit_length()
    @property
    def inst(self):return 4*self.a
    @property
    def layer_bits(self):return self.slots*self.inst
    @property
    def stdin(self):return self.size+1
    @property
    def stdout(self):return self.size+2
    def field(self,cell,slot,f):return cell+slot*self.inst+f*self.a
    def link(self,target):return (0,self.layer_bits,target,target+self.layer_bits)

def copy(n,dst,src):return (dst,dst+n,src,src+n)
def numeric(value,nbytes):return bytes(REV[(value>>(8*k))&255] for k in range(nbytes))

def encode(m,rows):
    """slots rows of four fields; numeric bits LSB first in each byte."""
    rows=list(rows)
    if len(rows)>m.slots:raise ValueError('too many rows')
    raw=bytearray();width=m.a//8
    for row in rows+[(0,0,0,0)]*(m.slots-len(rows)):
        for value in row:
            if not 0<=value<1<<m.a:raise ValueError(('field overflow',row))
            raw+=numeric(value,width)
    return bytes(raw)

class Stream:
    """Boot stream: loader layer + payload per chunk, the entry layer last."""
    def __init__(self,m):self.m=m;self.data=bytearray();self.start=None;self.buf=bytearray()
    def put(self,at,raw):
        m=self.m
        if at%8 or at<m.cell_bits or at+8*len(raw)>m.size:raise ValueError('put outside the loadable space')
        byte=at//8;raw=bytes(raw)
        if self.start is not None:
            end=self.start+len(self.buf)
            if end<=byte<=end+32 and byte-self.start+len(raw)<=m.chunk_bytes:
                self.buf+=bytes(byte-end)+raw;return
            self.flush()
        while len(raw)>m.chunk_bytes:
            self.start,self.buf=byte,bytearray(raw[:m.chunk_bytes]);self.flush()
            byte+=m.chunk_bytes;raw=raw[m.chunk_bytes:]
        self.start,self.buf=byte,bytearray(raw)
    def flush(self):
        if self.start is None:return
        m=self.m;n=len(self.buf)*8;at=self.start*8;i=m.inst
        rows=[(at,at+n,m.stdin,m.stdin),(0,3*i,4*i,7*i),(3*i+m.a,3*i+2*m.a,7*i,7*i+m.a),
              (0,0,m.stdin,m.stdin)]+[(0,0,0,0)]*(m.slots-5)+[(m.layer_bits,0,0,0)]
        self.data+=encode(m,rows)+self.buf;self.start=None;self.buf=bytearray()
    def finish(self,entry):
        """Close the stream; the processor then starts at cell address entry."""
        self.flush();m=self.m
        self.data+=encode(m,[(0,0,0,0)]*(m.slots-1)+[m.link(entry)]);return bytes(self.data)

class Layer:
    def __init__(self,m,cell):self.m=m;self.cell=cell;self.rows=[];self.next=None
    def add(self,row):
        m=self.m
        if len(self.rows)>=m.slots-1:raise ValueError('layer full')
        for other in self.rows:
            for x in (row[:2],row[2:]):
                for y in (other[:2],other[2:]):
                    if x[0]<x[1] and y[0]<y[1] and x[0]<y[1] and y[0]<x[1] and x[0]<m.size and y[0]<m.size:
                        raise ValueError(('overlap',row,other))
        self.rows.append(row);return len(self.rows)-1
    def encoded(self):
        if self.next is None:raise ValueError('unlinked layer')
        m=self.m
        return encode(m,list(self.rows)+[(0,0,0,0)]*(m.slots-1-len(self.rows))+[m.link(self.next)])

class Builder:
    """Cells are allocated in order; pending layers go to the stream at flush."""
    def __init__(self,stream,first_cell=2):self.m=stream.m;self.stream=stream;self.cell=first_cell;self.pending=[]
    def new_cell(self):c=self.cell;self.cell+=1;return c*self.m.cell_bits
    def group(self,k):
        """2^k consecutive cells aligned to 2^k cells; a link bit slice selects one."""
        self.cell=(self.cell+(1<<k)-1)>>k<<k;base=self.cell;self.cell+=1<<k;return base*self.m.cell_bits
    def flush(self):
        for layer in self.pending:self.stream.put(layer.cell,layer.encoded())
        self.pending=[]

class Seq:
    """A linear run of layers; each new layer is linked from the previous."""
    def __init__(self,b,cell=None):self.b=b;self.m=b.m;self.layers=[];self.first=cell
    def layer(self):
        cell=self.first if not self.layers and self.first is not None else self.b.new_cell()
        layer=Layer(self.m,cell)
        if self.layers:self.layers[-1].next=cell
        self.layers.append(layer);self.b.pending.append(layer);return layer
    def entry(self):return self.layers[0].cell
    def jump(self,target):self.layers[-1].next=target
    def rows(self,rows):
        layer=self.layer()
        for row in rows:layer.add(row)
        return layer
