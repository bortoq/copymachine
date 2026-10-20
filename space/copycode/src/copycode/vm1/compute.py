"""Computation by copies: table lookups with patched indices and their uses (MIT).

Host control model of the guest Forth library (forth/compute.fth); both must
produce the same bytes. A lookup reads a table entry whose index bits are
copied into both source endpoints of the read row. The patches must complete
two layers before the read: all lower-endpoint patches, then all upper-endpoint
patches (a source cannot be read twice in one tick), one gap, then the reads.
Entries use a stride wider than their width, so the patched index bits are
the same in both endpoints. Registers are plain bit addresses supplied by
the caller; numeric fields are least significant bit first.
"""
from .backend import Seq as Run,copy,numeric

class Seq(Run):
    """Layer runs with lookup, nibble-adder and multiway-branch patterns."""
    def lookups(self,items):
        """items: (table, s, width, out, segments[(src,n,index_offset)], preset)."""
        m=self.m;work=m.slots-1
        patches=[(i,src,n,off) for i,(_,_,_,_,segs,_) in enumerate(items) for src,n,off in segs]
        sl=[self.layer() for _ in range(-(-len(patches)//work))]
        sh=[self.layer() for _ in range(-(-len(patches)//work))]
        self.layer()
        reads=[];layer=None;used=set()
        for table,s,width,dst,_,preset in items:
            # Equal indices would make two reads of one table share a source.
            if layer is None or len(layer.rows)==work or table in used:layer=self.layer();used=set()
            used.add(table)
            base=table+(preset<<s)
            reads.append((layer,layer.add((dst,dst+width,base,base+width)),s))
        for k,(i,src,n,off) in enumerate(patches):
            layer,slot,s=reads[i]
            sl[k//work].add(copy(n,m.field(layer.cell,slot,2)+s+off,src))
            sh[k//work].add(copy(n,m.field(layer.cell,slot,3)+s+off,src))
    def adder(self,table,x,a,b,carry):
        """x = a + b (sub table: a + ~b + 1) in eight chained nibble steps.

        The table has 512 entries of 8 bits: index a nibble, b nibble, carry;
        entry sum nibble, carry, carry. Step i writes x[4i, 4i+6); x needs 34
        bits and ends with the carry and its copy at x+32."""
        m=self.m;layers=[self.layer() for _ in range(25)]
        reads=[]
        for i in range(8):
            base=table+(carry<<11 if i==0 else 0)
            reads.append(layers[3+3*i].add((x+4*i,x+4*i+6,base,base+6)))
        def patch(i,f,layer):
            r=layers[3+3*i]
            for src,off in ((a+4*i,3),(b+4*i,7)):
                layer.add(copy(4,m.field(r.cell,reads[i],f)+off,src))
        for i in range(8):
            if i<3:patch(i,2,layers[0]);patch(i,3,layers[1])
            else:patch(i,2,layers[3*i-1]);patch(i,3,layers[3*i])
            if i:
                r=layers[3+3*i]
                layers[3*i+1].add(copy(1,m.field(r.cell,reads[i],2)+11,x+4*i))
                layers[3*i+1].add(copy(1,m.field(r.cell,reads[i],3)+11,x+4*i+1))
    def decide(self,src,k):
        """Continue at group target value(src[0:k]); src[k:2k] holds a copy."""
        m=self.m;group=self.b.group(k);bit=m.branch_bit;link=m.slots-1
        patch=self.layer();self.layer();x=self.layer()
        x.next=group
        patch.add(copy(k,m.field(x.cell,link,2)+bit,src));patch.add(copy(k,m.field(x.cell,link,3)+bit,src+k))
        return group

class Tables:
    """Tables placed in [at, limit), each aligned to its size."""
    def __init__(self,stream,at,limit):self.stream=stream;self.at=at;self.limit=limit
    def table(self,bits,s,values):
        size=1<<(s+bits);self.at=(self.at+size-1)//size*size;base=self.at;self.at+=size
        if self.at>self.limit:raise ValueError('table area exhausted')
        per=(1<<s)//8 if s>=3 else 0
        if per:raw=b''.join(numeric(v,per) for v in values)
        else:
            raw=bytearray(size//8)
            for i,v in enumerate(values):
                for j in range(1<<s):
                    if v>>j&1:raw[(i<<s|j)//8]|=0x80>>((i<<s|j)%8)
            raw=bytes(raw)
        self.stream.put(base,raw);return base

def add_entry(i):v=(i&15)+(i>>4&15)+(i>>8);return v|v>>4<<5
def sub_entry(i):v=(i&15)+(~(i>>4)&15)+(i>>8);return v|v>>4<<5
def flags_entry(i):
    """Index: zero-test nibble flags, carry of a-b, sign of a, sign of b.

    Pairs (value, copy) of EQ, NE, LT, GE, LTU, GEU."""
    zero=not(i&15);ult=not(i>>4&1);a,b=i>>5&1,i>>6&1
    slt=a if a!=b else ult;bits=[zero,not zero,slt,not slt,ult,not ult]
    return sum(int(v)*3<<2*j for j,v in enumerate(bits))

def standard_tables(t):
    T={}
    T['add']=t.table(9,3,[add_entry(i) for i in range(512)])
    T['sub']=t.table(9,3,[sub_entry(i) for i in range(512)])
    for name,fn in (('xor',lambda a,b:a^b),('or',lambda a,b:a|b),('and',lambda a,b:a&b)):
        T[name]=t.table(8,3,[fn(i&15,i>>4) for i in range(256)])
    T['or8']=t.table(8,1,[int(i!=0) for i in range(256)])
    T['flags']=t.table(7,4,[flags_entry(i) for i in range(128)])
    T['not5']=t.table(5,4,[(31-i)|(31-i)<<5 for i in range(32)])
    T['sign32']=t.table(1,6,[0,0xffffffff])
    T['fill24']=t.table(1,5,[0,0xffffff])
    T['fill16']=t.table(1,5,[0,0xffff])
    T['inc1']=t.table(2,2,[i+1 for i in range(4)])
    T['inc2']=t.table(2,2,[i+2 for i in range(4)])
    return T

def or_chunks(T,out,src,lo,hi):
    """Lookups that OR bits [lo,hi) of src in chunks of 8 into out, out+1, ..."""
    return [(T['or8'],1,1,out+i,[(src+lo+8*i,min(8,hi-lo-8*i),0)],0) for i in range(-(-(hi-lo)//8))]

def compare(seq,T,res,a,b,z,flags):
    """After a sub adder into res: z = byte OR tests, flags = EQ..GEU pairs."""
    seq.lookups(or_chunks(T,z,res,0,32))
    seq.lookups([(T['flags'],4,12,flags,[(z,4,0),(res+32,1,4),(a+31,1,5),(b+31,1,6)],0)])

def logic(seq,table,res,a,b):
    """res = a op b, one nibble lookup per four result bits."""
    seq.lookups([(table,3,4,res+4*i,[(a+4*i,4,0),(b+4*i,4,4)],0) for i in range(8)])

def shift_right(seq,T,res,a,amount,w,zero,arithmetic):
    """res = a >> amount[0:5]: one copy from the 64-bit window w (64-aligned)."""
    m=seq.m
    if not arithmetic:
        l0=seq.rows([copy(32,w,a),copy(32,w+32,zero)]);l1=seq.rows([]);seq.rows([])
        sh=seq.rows([(res,res+32,w,w+32)])
        l0.add(copy(5,m.field(sh.cell,0,2),amount));l1.add(copy(5,m.field(sh.cell,0,3),amount))
        return
    l0=seq.rows([copy(32,w,a)]);l1=seq.rows([]);l2=seq.rows([]);seq.rows([])
    l4=seq.layer();sh=seq.rows([(res,res+32,w,w+32)])
    sign=l4.add((w+32,w+64,T['sign32'],T['sign32']+32))
    l0.add(copy(5,m.field(sh.cell,0,2),amount));l1.add(copy(5,m.field(sh.cell,0,3),amount))
    l1.add(copy(1,m.field(l4.cell,sign,2)+6,a+31));l2.add(copy(1,m.field(l4.cell,sign,3)+6,a+31))

def shift_left(seq,T,res,a,amount,w,zero,u):
    """res = a << amount[0:5]; u (10 bits) holds 31-amount and its copy."""
    m=seq.m
    l0=seq.rows([copy(31,w,zero),copy(32,w+31,a)]);l1=seq.rows([]);seq.rows([])
    l3=seq.layer();n=l3.add((u,u+10,T['not5'],T['not5']+10))
    l0.add(copy(5,m.field(l3.cell,n,2)+4,amount));l1.add(copy(5,m.field(l3.cell,n,3)+4,amount))
    l4=seq.rows([]);seq.rows([]);sh=seq.rows([(res,res+32,w,w+32)])
    l4.add(copy(5,m.field(sh.cell,0,2),u));l4.add(copy(5,m.field(sh.cell,0,3),u+5))

def flag_exit(seq,c2,flags):
    """Select flag pair (patched source of the returned row) into c2, then make
    it the branch bit of the exit link: a call returns to ret or ret+branch_step."""
    m=seq.m;b=seq.b;bit=m.branch_bit;link=m.slots-1
    d=seq.rows([copy(2,c2,flags)])
    e=seq.layer();seq.layer()
    x=Seq(b);x.rows([]).next=m.cell_bits;seq.jump(x.entry())
    e.add(copy(1,m.field(x.entry(),link,2)+bit,c2));e.add(copy(1,m.field(x.entry(),link,3)+bit,c2+1))
    return m.field(d.cell,0,0),x.entry()

def exit_layers(b,res,discard,width=32):
    """Shared returns: write res to a patched destination, or plain; both links
    are patched by the caller (unpatched they stop at the zero cell)."""
    m=b.m
    xw=Seq(b);xw.rows([copy(width,discard,res)]).next=m.cell_bits
    x=Seq(b);x.rows([]).next=m.cell_bits
    return xw.entry(),x.entry()

def call_rows(m,exit_cell,ret_lo_src,ret_hi_src):
    """Rows of a call site: patch the exit link with a stored return address
    (two A-bit constants: ret and ret+layer)."""
    link=m.slots-1
    return [copy(m.a,m.field(exit_cell,link,2),ret_lo_src),copy(m.a,m.field(exit_cell,link,3),ret_hi_src)]

def halt(b,regions):
    """Write each (bits, address) region to stdout, one per layer, then stop."""
    m=b.m;s=Seq(b)
    for n,src in regions:s.rows([(m.stdout,m.stdout,src,src+n)])
    s.jump(m.cell_bits);return s.entry()

def stub(seq,status,constant,halt_cell,rows=()):
    """Store a status constant (and extra rows), then halt."""
    seq.rows(list(rows)+[copy(32,status,constant)]).next=halt_cell
