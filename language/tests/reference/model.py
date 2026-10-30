"""Direct Forth compiler, host model (9.5): Forth source to emulator index code.

No RV32I and no inner interpreter: each word is compiled into layers of
copies. Inside straight-line code the compiler keeps the top stack items in
registers (a stack cache) and tracks the depth, so DUP, DROP, SWAP, OVER, ROT
cost nothing and literals are one copy. At every control boundary (branch,
loop, call, return) the cache is written to the data stack in memory.

The space has 2^31 bits and 32-bit address fields, room for the code of the
compiler itself. Memory stacks hold 256 entries, the data stack at a 64-bit
stride, the return stack at 128 bits; a stack pointer is kept as eight copies
of its 8-bit value, so several patches of one tick read distinct sources. A
call pushes the continuation's link fields (ret and ret+layer, 64 bits, from
the link pool) on the return stack; a return copies them straight into the
link fields of the return trampoline. Data addresses are byte addresses;
cells are 32-bit, at a 64-bit stride in the space, so a patched word address
never carries. @ and ! check the address: outside the 2^17 data cells
THROW -9, unaligned THROW -23.

* / MOD /MOD call shared straight-line subroutines placed by a list scheduler
(Sched); the stack cache stays in registers across them. Division truncates
toward zero (C semantics, as pForth's /); a zero divisor throws -10. An
uncaught THROW halts.

Supported: decimal literals, : ; EXIT RECURSE, VARIABLE CONSTANT, + - * / MOD
/MOD AND OR XOR = < 0= DUP DROP SWAP OVER ROT >R R> R@ @ ! EMIT, IF ELSE THEN,
BEGIN UNTIL WHILE REPEAT AGAIN, DO LOOP I, EXECUTE ['] CATCH THROW. Output
goes to stdout.

A source with KERNEL-LAYOUT is compiled to the upper half of the space (code
from cell 2^19, data region at 3*2^29): the kernel (kernel.fth) installs the
programs it compiles in the lower half with SPACE! and SPACEC! ( x lo hi -- ),
which write 32 or 8 bits anywhere in the space, and starts them with EXECUTE;
the entry of a program is therefore aligned as a word entry.
"""
import re

from copycode.vm1 import compute
from copycode.vm1.backend import Builder, Machine, Stream, copy, numeric
from copycode.vm1.compute import Seq

SIZE=1<<31;CELL=1024
M=Machine(SIZE,8,CELL,4096)
L=M.layer_bits;A=M.a;STEP=M.branch_step;BB=M.branch_bit
def layout(d):
    """Addresses of the data region based at d (cells, tables, stacks, memory)."""
    return dict(
        SP=d,RP=d+64,                       # 8 copies of an 8-bit index each
        HANDLER=d+128,CODE=d+192,           # CATCH frame pointer (RP copies), THROW code
        REGS=d+1024,                        # cache registers, 64-bit stride
        TMP=d+4096,XR=d+4160,Z=d+4224,IDX=d+4288,  # IDX: 16 index registers, 16 bits
        FLT=d+4672,                         # address check: fault flag, copy, code
        MA=d+4800,MB=d+4864,MP=d+4928,MQ=d+4992,MR=d+5056,  # subroutine operands
        ZERO=d+5120,W=d+5376,U=d+5440,KEY=d+5504,  # shift window and 31-n, input byte
        BP=d+5568,                          # bit offsets of a byte in its cell, both endpoints
        CONSTS=d+8192,TAB=d+(1<<19),
        STK=d+(1<<21),RSTK=d+(1<<21)+(1<<15),  # strides 64 and 128 bits
        SCR=d+(1<<21)+(1<<16),              # scratch registers of the subroutines
        LINKS=d+(1<<22),                    # link pool, written 512 at a time
        MEM=d+(1<<23),                      # 2^17 data cells (512 KiB)
        HTAB=d+(1<<24))                     # tables of the subroutines, to the end
# A program's code starts at cell 2 and its data region at 2^30. A kernel
# (a source with the word KERNEL-LAYOUT) goes to the upper half of both, so
# the programs it compiles and installs in its own space keep that layout.
D=1<<30;FIRST_CELL=2
KERNEL_D=3<<29;KERNEL_FIRST_CELL=1<<19
NREGS=48;NCONSTS=4096;NLINKS=1<<15;LINK_CHUNK=512;MW=17
globals().update(layout(D))
DATA_START=256

CAPACITY=128                       # pending layer records, as backend.fth
class CompileError(Exception):pass
BINARY=('+','-','and','or','xor','=','<','u<','lshift','rshift')
# Evaluated at compile time at the top level when their operands are known.
def _shift(f):return lambda a,b:f(a,b&31)&0xffffffff
CT_OPS={'+':(2,lambda a,b:(a+b)&0xffffffff),'-':(2,lambda a,b:(a-b)&0xffffffff),
        '*':(2,lambda a,b:(a*b)&0xffffffff),'and':(2,lambda a,b:a&b),'or':(2,lambda a,b:a|b),
        'xor':(2,lambda a,b:a^b),'lshift':(2,_shift(lambda a,b:a<<b)),'rshift':(2,_shift(lambda a,b:a>>b)),
        'cells':(1,lambda a:(a*4)&0xffffffff),'2*':(1,lambda a:(a*2)&0xffffffff),
        '1+':(1,lambda a:(a+1)&0xffffffff),'1-':(1,lambda a:(a-1)&0xffffffff),
        'cell+':(1,lambda a:(a+4)&0xffffffff)}

def tables(t):
    T=compute.standard_tables(t)
    for c in range(-8,9):
        T['off',c]=t.table(8,7,[sum(((i+c)&255)<<8*k for k in range(8)) for i in range(256)])
    T['rev8']=t.table(8,4,[int(f'{i:08b}'[::-1],2) for i in range(256)])
    T['zero32']=t.table(4,6,[0xffffffff if i==0 else 0 for i in range(16)])
    T['nz2']=t.table(4,2,[3 if i else 0 for i in range(16)])
    T['lt32']=t.table(3,6,[0xffffffff if ((i>>1&1) if (i>>1&1)!=(i>>2&1) else not(i&1)) else 0 for i in range(8)])
    # Address check: OR of bits [19,27) and [27,32) (two tables, one layer);
    # fault: index the two ORs and the low two address bits; flag, copy, code.
    T['or8b']=t.table(8,1,[int(i!=0) for i in range(256)])
    def fault(i):
        code=-9 if i&3 else -23 if i&12 else 0
        return int(code!=0)*3|(code&0xffffffff)<<2
    T['fault']=t.table(4,6,[fault(i) for i in range(16)])
    T['xr2']=t.table(2,2,[((i^i>>1)&1)*3 for i in range(4)])
    T['ult32']=t.table(1,6,[0xffffffff,0])
    T['bytepos']=t.table(2,4,[8*i|(8*i+8)<<6 for i in range(4)])
    return T

def number(t):
    """A decimal literal, optionally negative, modulo 2^32; else None."""
    return int(t)&0xffffffff if re.fullmatch('-?[0-9]+',t) else None

def mul_entry(i):
    """Index a nibble, b nibble, carry nibble; entry low nibble, carry, copy."""
    v=(i&15)*(i>>4&15)+(i>>8);return v&15|(v>>4)<<4|(v>>4)<<8

class Sched:
    """Straight-line code placed by a greedy list scheduler.

    Times are layer indices; an operation is placed at the earliest layer that
    has a free slot and no overlap with its rows (Layer.add checks that rows
    of one layer share no source and read nothing another writes) and returns
    the time its result can be read. A patch of a read row runs at least two
    layers before the read: the next layer is already fetched. Two reads of
    one table never share a layer: patched indices may become equal. Values
    are single assignment, so only read-after-write constraints exist.

    Each operation places nothing below the last WINDOW layers that existed
    when it started, and RING layers above that bound are the most it may
    reach: the guest keeps only these records, older ones are written out."""
    WINDOW=48;RING=64
    def __init__(self,b,cell=None):self.seq=Seq(b,cell);self.layers=[];self.tables=[];self.low=0
    def begin(self):self.low=max(0,len(self.layers)-self.WINDOW)
    def at(self,t):
        if t-self.low>=self.RING:raise CompileError('schedule window exceeded')
        while len(self.layers)<=t:self.layers.append(self.seq.layer());self.tables.append(set())
        return self.layers[t]
    def place(self,row,t,table=None):
        t=max(t,self.low)
        while True:
            layer=self.at(t)
            if table not in self.tables[t]:
                try:
                    slot=layer.add(row)
                    if table is not None:self.tables[t].add(table)
                    return t,slot
                except ValueError:pass
            t+=1
    def copy(self,n,dst,src,ready):self.begin();return self.place(copy(n,dst,src),ready)[0]+1
    def lookup(self,table,s,width,dst,segs,preset=0):
        """segs: (src, src for the upper endpoint, n, index offset, ready)."""
        self.begin();placed=[];latest=-2
        for src,src2,n,off,ready in segs:
            for f,x in ((2,src),(3,src2)):
                t,slot=self.place((0,0,x,x+n),ready);placed.append((t,slot,f,x,n,off));latest=max(latest,t)
        base=table+(preset<<s)
        t,slot=self.place((dst,dst+width,base,base+width),latest+2,table)
        cell=self.layers[t].cell
        for pt,ps,f,x,n,off in placed:self.layers[pt].rows[ps]=copy(n,M.field(cell,slot,f)+s+off,x)
        return t+1
    def chain(self,table,x,a,b,ready,carry=0,steps=8):
        """x = a + b (sub table: a + ~b + 1) nibble by nibble, as the adder.

        a, b: per nibble (src, ready) or None for a zero nibble; step i writes
        x[4i, 4i+6). Returns the time the carry x+4*steps is ready."""
        t=ready
        for i in range(steps):
            segs=[(src,src,4,off,r) for item,off in ((a[i],0),(b[i],4)) if item for src,r in [item]]
            if i:segs.append((x+4*i,x+4*i+1,1,8,t))
            t=self.lookup(table,3,6,x+4*i,segs,carry<<8 if i==0 else 0)
        return t
    def finish(self):
        """The last layer is the exit; callers patch its link."""
        self.layers[-1].next=CELL;return self.layers[-1].cell

class Compiler:
    def __init__(self,kernel=False):
        self.start(kernel)
    def start(self,kernel):
        """The layout, tables and shared code: the first output of the stream."""
        self.kernel=kernel;self.__dict__.update(layout(KERNEL_D if kernel else D))
        self.st=Stream(M);self.b=Builder(self.st,KERNEL_FIRST_CELL if kernel else FIRST_CELL,capacity=CAPACITY)
        self.T=tables(compute.Tables(self.st,self.TAB,self.STK))
        self.consts={};self.words={};self.cache=[];self.s=None
        self.here=DATA_START;self.data={}
        self.halt=CELL  # the zero cell: the next fetch finds only NOPs
        tr=Seq(self.b);tr.rows([]).next=CELL;self.tramp=tr.entry();self.b.flush()
        ex=Seq(self.b);ex.rows([]).next=0;self.ex=ex.entry();self.b.flush()
        self.scr=self.SCR;self.helpers={};self.htables=compute.Tables(self.st,self.HTAB,M.size)
        self.nlinks=0;self.link_buf=[]
        self.thrower=self.build_thrower()
    def scratch(self,bits,align=64):
        at=-(-self.scr//align)*align;self.scr=at+bits
        if self.scr>self.MEM:raise CompileError('scratch registers exhausted')
        return at
    # --- data ------------------------------------------------------------
    def const(self,value,bits=32):
        key=(value&((1<<bits)-1),bits)
        if key not in self.consts:
            if len(self.consts)==NCONSTS:raise CompileError('constants exhausted')
            self.consts[key]=self.CONSTS+64*len(self.consts)
        return self.consts[key]
    def link(self,cont):
        """A pool entry with the link fields of a continuation: cont, cont+layer.

        Entries are unique per call site, so they are not looked up; they go
        to the stream LINK_CHUNK at a time and the rest at the end."""
        if self.nlinks==NLINKS:raise CompileError('link pool exhausted')
        at=self.LINKS+64*self.nlinks;self.nlinks+=1;self.link_buf.append(cont|(cont+L)<<A)
        if len(self.link_buf)==LINK_CHUNK:self.put_links()
        return at
    def put_links(self):
        if self.link_buf:
            first=self.LINKS+64*(self.nlinks-len(self.link_buf))
            self.st.put(first,b''.join(numeric(v,8) for v in self.link_buf));self.link_buf=[]
    def reg(self):
        used=set(self.cache)
        for k in range(NREGS):
            r=self.REGS+64*k
            if r not in used and r not in self.pinned:return r
        raise CompileError('stack cache exhausted')
    pinned=()
    # --- memory stacks ----------------------------------------------------
    def adjust(self,pointer,offsets,delta):
        """IDX+16k = pointer+offsets[k] (value, copy); pointer += delta."""
        items=[(self.T['off',c],7,16,self.IDX+16*k,[(pointer+8*k,8,0)],0) for k,c in enumerate(offsets)]
        items.append((self.T['off',delta],7,64,pointer,[(pointer+8*len(offsets),8,0)],0))
        self.s.lookups(items)
    def patched(self,rows,fields,shift=6):
        """Rows whose endpoint fields get IDX+16k (and its copy) at bit shift."""
        s=self.s;n=len(rows)
        patches=[s.layer() for _ in range(-(-2*n//7))];s.layer()
        layer=s.layer();slots=[layer.add(r) for r in rows]
        for k,slot in enumerate(slots):
            for j,(f,src) in enumerate(((fields[0],self.IDX+16*k),(fields[1],self.IDX+16*k+8))):
                patches[(2*k+j)//7].add(copy(8,M.field(layer.cell,slot,f)+shift,src))
    def mem_pop(self,base,pointer,n,width=32):
        regs=[self.reg_for_pop(k) for k in range(n)];sh=7 if base==self.RSTK else 6
        self.adjust(pointer,[-n+k for k in range(n)],-n)
        self.patched([(r,r+width,base+(k<<sh),base+(k<<sh)+width) for k,r in enumerate(regs)],(2,3),sh)
        return regs
    def reg_for_pop(self,k):
        r=self.reg();self.pinned=tuple(self.pinned)+(r,);return r
    def mem_push(self,base,pointer,srcs,width=32):
        # One layer may not read a register twice (DUP shares one): split.
        k=1
        while k<len(srcs) and srcs[k] not in srcs[:k]:k+=1
        if k<len(srcs):
            self.mem_push(base,pointer,srcs[:k],width);self.mem_push(base,pointer,srcs[k:],width);return
        sh=7 if base==self.RSTK else 6
        self.adjust(pointer,list(range(len(srcs))),len(srcs))
        self.patched([(base+(k<<sh),base+(k<<sh)+width,r,r+width) for k,r in enumerate(srcs)],(0,1),sh)
    def need(self,n):
        """Ensure n cached items, popping the missing ones from memory."""
        missing=n-len(self.cache)
        while missing>0:
            k=min(missing,7)
            regs=self.mem_pop(self.STK,self.SP,k);self.pinned=()
            self.cache=regs+self.cache;missing-=k
    def flush(self):
        while self.cache:
            part=self.cache[:7];self.cache=self.cache[7:]
            self.mem_push(self.STK,self.SP,part)
    def pop(self):self.need(1);return self.cache.pop()
    # --- control ----------------------------------------------------------
    def begin_block(self,cell=None):
        """Start a new layer run; the previous run continues into it."""
        cell=cell if cell is not None else self.b.new_cell()
        if self.s is not None:self.jump(cell)
        self.b.flush();self.s=Seq(self.b,cell);self.s.layer();return cell
    def jump(self,target):
        """Continue at target; a run still without layers (the ok cell of an
        address check) gets an empty one."""
        if not self.s.layers:self.s.layer()
        self.s.jump(target)
    def nonzero(self,r):
        """E = (r != 0, copy), for a two-way decision."""
        s=self.s
        s.lookups(compute.or_chunks(self.T,self.Z,r,0,32))
        s.lookups([(self.T['nz2'],2,2,self.XR,[(self.Z,4,0)],0)])
        return self.XR
    def branch(self,flag):
        """Decide on flag != 0: returns (zero cell, nonzero cell)."""
        e=self.nonzero(flag);g=self.s.decide(e,1);self.b.flush();self.s=None
        return g,g+STEP
    def call(self,entry):
        self.flush();cont=self.b.new_cell()
        self.mem_push(self.RSTK,self.RP,[self.link(cont)],64)
        self.s.jump(entry);self.b.flush();self.s=None
        self.begin_block(cont)
    def call_indirect(self,xt,cont=None):
        """Call the word whose entry cell address is in register xt.

        Entries are aligned to the branch step, so bits [BB,32) select the
        target in both link endpoints; the low bits of the templates stay 0
        and layer."""
        self.flush();cont=cont if cont is not None else self.b.new_cell()
        self.mem_push(self.RSTK,self.RP,[self.link(cont)],64)
        s=self.s;p0=s.layer();p1=s.layer();s.layer()
        p0.add(copy(A-BB,M.field(self.ex,7,2)+BB,xt+BB));p1.add(copy(A-BB,M.field(self.ex,7,3)+BB,xt+BB))
        s.jump(self.ex);self.b.flush();self.s=None
        return cont
    def catch(self):
        """Frame on the return stack: data stack pointer, previous handler,
        link to the throw continuation; HANDLER then points above it."""
        xt=self.pop();self.flush()
        thrown=self.b.new_cell();join=self.b.new_cell()
        # Entries are 64 bits (below the 128-bit stride); pointers are restored
        # from their first copy by the identity table, which replicates it.
        self.push_frame(thrown)
        normal=self.call_indirect(xt)
        self.begin_block(normal)
        _,prev,_=self.mem_pop(self.RSTK,self.RP,3,64);self.pinned=()
        self.s.lookups([(self.T['off',0],7,64,self.HANDLER,[(prev,8,0)],0)]);self.cache=[];self.literal(0);self.flush()
        self.s.jump(join);self.b.flush();self.s=None
        self.begin_block(thrown);r=self.reg();self.s.rows([copy(32,r,self.CODE)]);self.cache=[r];self.flush()
        self.s.jump(join);self.b.flush();self.s=None
        self.begin_block(join)
    def build_thrower(self):
        """Shared nonzero THROW, code in CODE: the frame at HANDLER restores
        both stacks and the handler, then its link continues at the catch."""
        self.cache=[];self.s=Seq(self.b);self.s.rows([copy(64,self.RP,self.HANDLER)]);entry=self.s.entry()
        saved,prev,link=self.mem_pop(self.RSTK,self.RP,3,64);self.pinned=()
        self.s.lookups([(self.T['off',0],7,64,self.SP,[(saved,8,0)],0),(self.T['off',0],7,64,self.HANDLER,[(prev,8,0)],0)])
        self.s.rows([copy(64,M.field(self.tramp,7,2),link)])
        self.s.layer();self.s.jump(self.tramp);self.b.flush();self.s=None
        return entry
    def throw(self):
        code=self.pop();self.flush()
        self.s.rows([copy(32,self.CODE,code)])
        zero,thrown=self.branch(code)
        Seq(self.b,thrown).rows([]).next=self.thrower;self.b.flush()
        self.begin_block(zero)
    def push_frame(self,thrown):
        self.mem_push(self.RSTK,self.RP,[self.SP,self.HANDLER,self.link(thrown)],64)
        self.s.rows([copy(64,self.HANDLER,self.RP)])
    def ret(self):
        self.flush()
        self.adjust(self.RP,[-1],-1)
        s=self.s;p=s.layer();s.layer()
        layer=s.layer();slot=layer.add((M.field(self.tramp,7,2),M.field(self.tramp,7,2)+64,self.RSTK,self.RSTK+64))
        p.add(copy(8,M.field(layer.cell,slot,2)+7,self.IDX));p.add(copy(8,M.field(layer.cell,slot,3)+7,self.IDX+8))
        s.layer();s.jump(self.tramp);self.b.flush();self.s=None
    def check_address(self,a,access,byte=False):
        """Check the byte address in register a, then continue in the ok cell.

        Round 1 ORs the high bits [19,32) in two chunks (and for a byte access
        reads its bit offset: the low six bits of both endpoints, 8b and
        8b+8); round 2 reads flag, copy and code from the fault table, indexed
        for a cell access with the low two address bits as well. The fault
        cell copies the code to CODE and throws. access(rounds, ok) adds the
        access: rounds is ((l0, l1, read), (l2, l3, read2)), patch layers and
        read layer of each round; its rows run before the decision, a store
        goes to a layer of the ok run."""
        s=self.s;T=self.T
        l0=s.layer();l1=s.layer();s.layer();r=s.layer()
        hi=MW+2
        reads=[(T['or8'],1,1,self.Z,[(a+hi,8,0)]),(T['or8b'],1,1,self.Z+1,[(a+hi+8,A-hi-8,0)])]
        if byte:reads.append((T['bytepos'],4,12,self.BP,[(a,2,0)]))
        for table,sh,w,dst,segs in reads:
            slot=r.add((dst,dst+w,table,table+w))
            for src,n,off in segs:
                l0.add(copy(n,M.field(r.cell,slot,2)+sh+off,src));l1.add(copy(n,M.field(r.cell,slot,3)+sh+off,src))
        l2=s.layer();l3=s.layer();s.layer();r2=s.layer()
        slot=r2.add((self.FLT,self.FLT+34,T['fault'],T['fault']+34))
        for src,n,off in [(self.Z,2,0)] if byte else [(self.Z,2,0),(a,2,2)]:
            l2.add(copy(n,M.field(r2.cell,slot,2)+6+off,src));l3.add(copy(n,M.field(r2.cell,slot,3)+6+off,src))
        group=self.b.group(1);bit=BB
        patch=s.layer();s.layer();x=s.layer();x.next=group
        patch.add(copy(1,M.field(x.cell,7,2)+bit,self.FLT));patch.add(copy(1,M.field(x.cell,7,3)+bit,self.FLT+1))
        ok=Seq(self.b,group);access(((l0,l1,r),(l2,l3,r2)),ok)
        Seq(self.b,group+STEP).rows([copy(32,self.CODE,self.FLT+2)]).next=self.thrower
        self.s=ok
    def byte_patches(self,cell,slot,fields,lo,hi,a):
        """Byte address a: bit offset from BP, cell index a[2:] at bit 6."""
        for f,layer,src in ((fields[0],lo,self.BP),(fields[1],hi,self.BP+6)):
            layer.add(copy(6,M.field(cell,slot,f),src));layer.add(copy(MW,M.field(cell,slot,f)+6,a+2))
    # --- multiplication and division ---------------------------------------
    def build_mul(self):
        """MP = MA * MB mod 2^32. Row j: MA times nibble j of MB, a chain of
        mul4 lookups (product plus carry nibble); the rows are summed by
        nibble add chains, X_j = X_{j-1} + (row j << 4j), pipelined. The
        rows (about 450) bound it, not the chains: copies of the tables do
        not help."""
        S=Sched(self.b);P={};add=self.T['add']
        m4=self.htables.table(12,4,[mul_entry(i) for i in range(4096)])
        for j in range(8):
            for i in range(8-j):
                r=self.scratch(16)
                segs=[(self.MA+4*i,self.MA+4*i,4,0,0),(self.MB+4*j,self.MB+4*j,4,4,0)]
                if i:prev,t=P[i-1,j];segs.append((prev+4,prev+8,4,8,t))
                P[i,j]=(r,S.lookup(m4,4,12,r,segs))
        X={(0,k):P[k,0] for k in range(8)}
        for j in range(1,8):
            for k in range(j,8):
                x=self.scratch(8);a,ta=X[j-1,k];b,tb=P[k-j,j]
                segs=[(a,a,4,0,ta),(b,b,4,4,tb)]
                if k>j:c,tc=X[j,k-1];segs.append((c+4,c+5,1,8,tc))
                X[j,k]=(x,S.lookup(add,3,6,x,segs))
        for k in range(8):src,t=X[k,k];S.copy(4,self.MP+4*k,src,t)
        return S.seq.entry(),S.finish()
    def copies(self,n,bits,sh,values):
        """n copies of a table: reads of one table may not share a layer."""
        return [self.htables.table(bits,sh,values) for _ in range(n)]
    def build_div(self):
        """MQ, MR = MA / MB truncated, MA mod MB with the sign of MA.

        A zero MB throws -10. Absolute values are selected from 128-bit
        windows (value, negation) by the sign bit. 32 restoring steps divide
        them: t = rem*2 + bit and t - d by carry select: the low 16 bits in
        one sub chain, the high 16 bits in two chains for carry-in 0 and 1,
        in parallel. q = t >= d (from the three carries) and the low carry
        select the next remainder from a window (t, low|high0, t, low|high1);
        q is the quotient bit. |d| <= 2^31, so t fits 32 bits. The signs of
        the results are applied as for the operands."""
        T=self.T;s=self.s=Seq(self.b);s.layer();entry=s.entry()
        e=self.nonzero(self.MB);g=s.decide(e,1);self.b.flush();self.s=None
        Seq(self.b,g).rows([copy(32,self.CODE,self.const(-10))]).next=self.thrower
        S=Sched(self.b,g+STEP)
        sub=self.copies(3,9,3,[compute.sub_entry(i) for i in range(512)])
        qsel=self.htables.table(3,2,[((i>>2 if i&1 else i>>1)&1)*3 for i in range(8)])
        def nib(reg,t):return [(reg+4*i,t) for i in range(8)]
        def negate_select(value,t,sign,sign2,ts,dst,table):
            w=self.scratch(128,128);t1=S.copy(32,w,value,t)
            t2=S.chain(table,w+64,[None]*8,nib(value,t),t,carry=1)
            return S.lookup(w,0,32,dst,[(sign,sign2,1,6,max(ts,t1,t2))])
        absa,absb=self.scratch(32),self.scratch(32)
        ta=negate_select(self.MA,0,self.MA+31,self.MA+31,0,absa,sub[0]);tb=negate_select(self.MB,0,self.MB+31,self.MB+31,0,absb,sub[1])
        rem,tr=self.ZERO,0;Q=self.scratch(32);tq=0
        for k in range(31,-1,-1):
            w=self.scratch(256,256);L=self.scratch(32)
            def step(table,dst,i,carry_src,t,preset,k=k,rem=rem,tr=tr):  # k, rem, tr: used in this iteration only
                a=[(absa+k,absa+k,1,0,ta),(rem,rem,3,1,tr)] if i==0 else [(rem+4*i-1,rem+4*i-1,4,0,tr)]
                segs=a+[(absb+4*i,absb+4*i,4,4,tb)]
                if carry_src is not None:segs.append((carry_src,carry_src+1,1,8,t))
                return S.lookup(table,3,6,dst,segs,preset<<8)
            # Steps interleaved, so the three chains share the early layers.
            tl=t0=t1=0
            for i in range(4):
                tl=step(sub[0],L+4*i,i,L+4*i if i else None,tl,1 if i==0 else 0)
                t0=step(sub[1],w+64+16+4*i,4+i,w+64+16+4*i if i else None,t0,0)
                t1=step(sub[2],w+192+16+4*i,4+i,w+192+16+4*i if i else None,t1,1 if i==0 else 0)
            qr=self.scratch(2)
            tq_k=S.lookup(qsel,2,2,qr,[(L+16,L+17,1,0,tl),(w+96,w+97,1,1,t0),(w+224,w+225,1,2,t1)])
            tw=max(S.copy(16,w+64,L,tl),S.copy(16,w+192,L,tl))
            tw=max(tw,S.copy(31,w+1,rem,tr),S.copy(1,w,absa+k,ta),S.copy(31,w+129,rem,tr),S.copy(1,w+128,absa+k,ta))
            nxt=self.scratch(32)
            tr=S.lookup(w,0,32,nxt,[(qr,qr+1,1,6,tq_k),(L+16,L+17,1,7,max(tl,tw))]);rem=nxt
            tq=max(tq,S.copy(1,Q+k,qr,tq_k))
        sq=self.scratch(2);ts=S.lookup(T['xr2'],2,2,sq,[(self.MA+31,self.MA+31,1,0,0),(self.MB+31,self.MB+31,1,1,0)])
        negate_select(Q,tq,sq,sq+1,ts,self.MQ,sub[0]);negate_select(rem,tr,self.MA+31,self.MA+31,0,self.MR,sub[1])
        return entry,S.finish()
    def helper(self,name,args,outs):
        """Call a shared subroutine: operands to its inputs and the exit link
        patched with the continuation in one layer; results then to cache."""
        self.need(len(args));regs=self.cache[-len(args):];del self.cache[-len(args):]
        entry,exit_cell=self.helpers[name];cont=self.b.new_cell()
        rows=[copy(64,M.field(exit_cell,7,2),self.link(cont))]
        layer=self.s.rows(rows)
        for dst,src in zip(args,regs, strict=False):
            try:layer.add(copy(32,dst,src))
            except ValueError:layer=self.s.rows([copy(32,dst,src)])  # DUP: one register
        self.s.jump(entry);self.b.flush();self.s=Seq(self.b,cont)
        res=[]
        for _src in outs:r=self.reg();res.append(r);self.cache.append(r)
        self.s.rows([copy(32,r,src) for r,src in zip(res,outs, strict=False)])
    # --- primitives ---------------------------------------------------------
    def binary(self,name):
        self.need(2);b=self.cache.pop();a=self.cache.pop();s=self.s
        if a==b:
            # DUP shares a register; one tick may not read it twice.
            self.cache.append(a);b=self.reg();self.cache.pop();s.rows([copy(32,b,a)])
        self.cache+= [a,b];r=self.reg();del self.cache[-2:]
        if name in ('+','-'):
            s.adder(self.T['add' if name=='+' else 'sub'],self.TMP,a,b,int(name=='-'));s.rows([copy(32,r,self.TMP)])
        elif name in ('and','or','xor'):compute.logic(s,self.T[name],r,a,b)
        elif name=='=':
            compute.logic(s,self.T['xor'],self.XR,a,b);s.lookups(compute.or_chunks(self.T,self.Z,self.XR,0,32))
            s.lookups([(self.T['zero32'],6,32,r,[(self.Z,4,0)],0)])
        elif name=='<':
            s.adder(self.T['sub'],self.TMP,a,b,1)
            s.lookups([(self.T['lt32'],6,32,r,[(self.TMP+32,1,0),(a+31,1,1),(b+31,1,2)],0)])
        elif name=='u<':
            s.adder(self.T['sub'],self.TMP,a,b,1);s.lookups([(self.T['ult32'],6,32,r,[(self.TMP+32,1,0)],0)])
        elif name=='lshift':compute.shift_left(s,self.T,r,a,b,self.W,self.ZERO,self.U)
        elif name=='rshift':compute.shift_right(s,self.T,r,a,b,self.W,self.ZERO,False)
        self.cache.append(r)
    def primitive(self,name):
        s=self.s
        if name in BINARY:self.binary(name)
        elif name in ('cells','2*'):
            # Shift by copying: one layer.
            k=2 if name=='cells' else 1
            a=self.pop();self.pinned=(a,);r=self.reg();self.pinned=()
            s.rows([copy(32-k,r+k,a),copy(k,r,self.ZERO)]);self.cache.append(r)
        elif name in ('1+','1-','cell+'):
            a=self.pop();self.pinned=(a,);r=self.reg();self.pinned=()
            s.adder(self.T['sub' if name=='1-' else 'add'],self.TMP,a,self.const(4 if name=='cell+' else 1),int(name=='1-'))
            s.rows([copy(32,r,self.TMP)]);self.cache.append(r)
        elif name=='decimal':pass
        elif name=='key':
            # A cleared byte, then stdin: at the end of input it stays 0.
            r=self.reg();s.rows([copy(8,self.KEY,self.ZERO)]);s.rows([(self.KEY,self.KEY+8,M.stdin,M.stdin)]);s.layer()
            s.lookups([(self.T['rev8'],4,8,r,[(self.KEY,8,0)],0)]);s.rows([copy(24,r+8,self.ZERO)]);self.cache.append(r)
        elif name=='j':
            r=self.reg()
            self.adjust(self.RP,[-3],0);self.patched([(r,r+32,self.RSTK,self.RSTK+32)],(2,3),7);self.cache.append(r)
        elif name=='unloop':self.adjust(self.RP,[],-2)
        elif name=='c@':
            a=self.pop();self.pinned=(a,);r=self.reg();self.pinned=()
            def load(rounds,ok):
                _,(p0,p1,layer)=rounds
                slot=layer.add((r,r+8,self.MEM,self.MEM+8));layer.add(copy(24,r+8,self.ZERO))
                self.byte_patches(layer.cell,slot,(2,3),p0,p1,a)
            self.check_address(a,load,True);self.cache.append(r)
        elif name=='c!':
            self.need(2);a=self.cache.pop();v=self.cache.pop()
            def store(rounds,ok):
                _,(p0,p1,_)=rounds;ok=ok.layer();slot=ok.add((self.MEM,self.MEM+8,v,v+8))
                self.byte_patches(ok.cell,slot,(0,1),p0,p1,a)
            self.check_address(a,store,True)
        elif name=='*':self.helper('mul',(self.MA,self.MB),(self.MP,))
        elif name=='/':self.helper('div',(self.MA,self.MB),(self.MQ,))
        elif name=='mod':self.helper('div',(self.MA,self.MB),(self.MR,))
        elif name=='/mod':self.helper('div',(self.MA,self.MB),(self.MR,self.MQ))
        elif name=='0=':
            a=self.pop();r=self.reg()
            s.lookups(compute.or_chunks(self.T,self.Z,a,0,32));s.lookups([(self.T['zero32'],6,32,r,[(self.Z,4,0)],0)])
            self.cache.append(r)
        elif name=='dup':self.need(1);self.cache.append(self.cache[-1])
        elif name=='drop':
            if self.cache:self.cache.pop()
            else:self.adjust(self.SP,[],-1)
        elif name=='swap':self.need(2);self.cache[-2:]=self.cache[-1:-3:-1]
        elif name=='over':self.need(2);self.cache.append(self.cache[-2])
        elif name=='rot':self.need(3);self.cache.append(self.cache.pop(-3))
        elif name=='>r':r=self.pop();self.mem_push(self.RSTK,self.RP,[r])
        elif name=='r>':self.cache.append(self.mem_pop(self.RSTK,self.RP,1)[0]);self.pinned=()
        elif name in ('r@','i'):
            r=self.reg()
            self.adjust(self.RP,[-1],0);self.patched([(r,r+32,self.RSTK,self.RSTK+32)],(2,3),7);self.cache.append(r)
        elif name=='@':
            # The load runs before the decision; on a fault the cache is dead.
            a=self.pop();self.pinned=(a,);r=self.reg();self.pinned=()
            def load(rounds,ok):
                (p0,p1,layer),_=rounds;slot=layer.add((r,r+32,self.MEM,self.MEM+32))
                p0.add(copy(MW,M.field(layer.cell,slot,2)+6,a+2));p1.add(copy(MW,M.field(layer.cell,slot,3)+6,a+2))
            self.check_address(a,load);self.cache.append(r)
        elif name=='!':
            self.need(2);a=self.cache.pop();v=self.cache.pop()
            def store(rounds,ok):
                (p0,p1,_),_=rounds;ok=ok.layer();slot=ok.add((self.MEM,self.MEM+32,v,v+32))
                p0.add(copy(MW,M.field(ok.cell,slot,0)+6,a+2));p1.add(copy(MW,M.field(ok.cell,slot,1)+6,a+2))
            self.check_address(a,store)
        elif name in ('space!','spacec!'):
            # x lo hi: bits [lo,hi) of the space get the low 32 (8) bits of
            # x; a kernel installs code and data with it. The copy row's
            # destination is patched two layers ahead.
            n=32 if name=='space!' else 8
            self.need(3);hi=self.cache.pop();lo=self.cache.pop();x=self.cache.pop()
            if hi==lo:
                self.pinned=(x,lo);hi=self.reg();self.pinned=();s.rows([copy(32,hi,lo)])
            p=s.layer();s.layer();layer=s.layer();slot=layer.add((0,0,x,x+n))
            p.add(copy(32,M.field(layer.cell,slot,0),lo));p.add(copy(32,M.field(layer.cell,slot,1),hi))
        elif name=='emit':
            c=self.pop();out=self.XR
            s.lookups([(self.T['rev8'],4,8,out,[(c,8,0)],0)])
            s.rows([(M.stdout,M.stdout,out,out+8)])
        else:raise CompileError('unknown word '+name)
    def const_shift(self,right,k):
        a=self.pop()
        if k==0:self.cache.append(a);return
        self.pinned=(a,);r=self.reg();self.pinned=()
        if right:self.s.rows([copy(32-k,r,a+k),copy(k,r+32-k,self.ZERO)])
        else:self.s.rows([copy(32-k,r+k,a),copy(k,r,self.ZERO)])
        self.cache.append(r)
    def literal(self,value):
        r=self.reg();self.s.rows([copy(32,r,self.const(value))]);self.cache.append(r);self.last_lit=(r,value)
    # --- source -------------------------------------------------------------
    def string(self,data):
        """Bytes at HERE (cell aligned) in the data memory; returns the address."""
        self.here=(self.here+3)&~3;at=self.here
        for k,c in enumerate(data):
            byte=at+k;self.st.put(self.MEM+64*(byte>>2)+8*(byte&3),numeric(c,1))
        self.here+=len(data);self.check_here();return at
    def check_here(self):
        if self.here>4<<MW:raise CompileError('data memory exhausted')
    def define_data(self,name,size):
        self.here=(self.here+3)&~3;self.words[name]=('lit',self.here);self.here+=size;self.check_here()
    # --- source -------------------------------------------------------------
    def compile_source(self,text,main):
        tk=Tokens(text)
        uses=set()
        while tk.next():uses.add(tk.tok)
        if ('kernel-layout' in uses)!=self.kernel:self.start(not self.kernel)
        if '*' in uses:self.helpers['mul']=self.build_mul()
        if uses&{'/','mod','/mod'}:self.helpers['div']=self.build_div()
        tk=Tokens(text);self.control=[];self.word=None;self.ct=[];self.init=[];self.init_open=False
        self.last_lit=None
        while tk.next():
            t=tk.tok;prev=self.last_lit;self.last_lit=None
            if t=='(':
                while tk.need()!=')':pass
                continue
            if self.word is not None and not self.init_open:self.body_token(tk,t,prev)
            else:self.top_token(tk,t,prev)
        if self.word is not None and not self.init_open:raise CompileError('unfinished definition')
        self.close_init()
        if main not in self.words:raise CompileError('no main word')
        # Entry: a frame for an uncaught THROW (it halts), the top-level code,
        # main, halt. It is aligned as a word entry: a kernel that installs
        # the program in its own space starts it with EXECUTE.
        self.s=None;self.cache=[];start=self.begin_block(self.b.group(0));uncaught=self.b.new_cell()
        self.push_frame(uncaught)
        for entry in self.init:self.call(entry)
        self.call(self.words[main][1])
        self.jump(self.halt);self.b.flush()
        Seq(self.b,uncaught).rows([]).next=self.halt;self.b.flush()
        st=self.st
        st.put(self.SP,numeric(0,8));st.put(self.RP,numeric(0,8));st.put(self.HANDLER,numeric(0,8));st.put(self.ZERO,bytes(16))
        for (value,bits),at in self.consts.items():st.put(at,numeric(value,(bits+7)//8))
        self.put_links()
        self.entry=start;return st.finish(start)
    def close_init(self):
        if self.ct:raise CompileError('values left at the top level')
        if self.init_open:self.ret();self.init_open=False;self.word=None
    def top_token(self,tk,t,prev):
        """Definitions; constant expressions are evaluated here, other code runs
        before MAIN as parts of the top-level code, in order."""
        if t==':':
            self.close_init();name=tk.need();entry=self.b.group(0)
            self.word=name;self.words[name]=('call',entry);self.s=None;self.cache=[]
            self.begin_block(entry);return
        if t in ('variable','create'):self.define_data(tk.need(),4 if t=='variable' else 0);return
        if t in ('decimal','kernel-layout'):return
        if t in ('allot','constant'):
            if not self.ct:raise CompileError(t+' needs a value known at compile time')
            value=self.ct.pop()
            if t=='allot':self.here+=value if value<1<<31 else value-(1<<32);self.check_here()
            else:self.words[tk.need()]=('lit',value)
            return
        value=number(t)
        if value is None and t in self.words and self.words[t][0]=='lit':value=self.words[t][1]
        if value is not None:self.ct.append(value);return
        if t in CT_OPS and len(self.ct)>=CT_OPS[t][0]:
            n,f=CT_OPS[t];args=self.ct[-n:];del self.ct[-n:];self.ct.append(f(*args));return
        # Top-level code: a part of the initialization, a word of its own.
        if not self.init_open:
            entry=self.b.group(0);self.init.append(entry);self.init_open=True;self.word=''
            self.s=None;self.cache=[];self.begin_block(entry)
        values=self.ct;self.ct=[]
        for v in values:self.literal(v)
        self.body_token(tk,t,None)
        if self.word is None:raise CompileError('; at the top level')
    def do_entry(self):
        for entry in reversed(self.control):
            if entry[0]=='do':return entry
        raise CompileError('LEAVE outside a loop')
    def body_token(self,tk,t,prev):
        control=self.control
        if t==';':
            if control:raise CompileError('unbalanced control structure')
            self.ret();self.word=None;return
        if t=='exit':self.ret();self.begin_block();return
        if t=='recurse':self.call(self.words[self.word][1]);return
        if t=="[']":self.literal(self.words[tk.need()][1]);return
        if t=='[char]':
            if not tk.word():raise CompileError('unexpected end of the source')
            self.literal(tk.raw[0]);return
        if t=='s"':
            data=tk.string();self.literal(self.string(data));self.literal(len(data));return
        if t in ('*','lshift','rshift') and prev is not None and self.cache and self.cache[-1]==prev[0]:
            # A literal power of two or shift below 32: a shift by copying.
            v=prev[1];k=None
            if t=='*':
                if v and v&(v-1)==0:k=v.bit_length()-1
            elif v<32:k=v
            if k is not None:self.cache.pop();self.const_shift(t=='rshift',k);return
        if t in ('pick','roll'):
            if prev is None or not self.cache or self.cache[-1]!=prev[0]:raise CompileError(t+' needs a literal')
            self.cache.pop();n=prev[1];self.need(n+1)
            if t=='pick':self.cache.append(self.cache[-1-n])
            else:self.cache.append(self.cache.pop(-1-n))
            return
        if t=='execute':
            xt=self.pop();self.begin_block(self.call_indirect(xt));return
        if t=='catch':self.catch();return
        if t=='throw':self.throw();return
        if t=='if':
            f=self.pop();self.flush();zero,yes=self.branch(f)
            control.append(['if',zero]);self.begin_block(yes);return
        if t=='else':
            kind,zero=control.pop();self.flush();join=self.b.new_cell();self.jump(join)
            self.b.flush();self.s=None;control.append(['else',join]);self.begin_block(zero);return
        if t=='then':
            kind,target=control.pop();self.flush()
            if kind=='if':
                join=self.b.new_cell();self.jump(join);self.b.flush()
                Seq(self.b,target).rows([]).next=join;self.b.flush();self.s=None;self.begin_block(join)
            else:self.begin_block(target)
            return
        if t=='begin':self.flush();control.append(['begin',self.begin_block()]);return
        if t in ('until','while'):
            f=self.pop();self.flush();zero,yes=self.branch(f)
            if t=='until':
                kind,start=control.pop()
                Seq(self.b,zero).rows([]).next=start;self.b.flush();self.begin_block(yes)
            else:control.append(['while',zero]);self.begin_block(yes)
            return
        if t in ('repeat','again'):
            if t=='repeat':_,exit_cell=control.pop()
            _,start=control.pop();self.flush();self.jump(start);self.b.flush();self.s=None
            if t=='repeat':self.begin_block(exit_cell)
            else:self.begin_block()
            return
        if t=='do':
            self.need(2);index=self.cache.pop();limit=self.cache.pop();self.flush()
            self.mem_push(self.RSTK,self.RP,[limit,index]);control.append(['do',self.begin_block(),None]);return
        if t=='?do':
            # Equal limit and index skip the loop: straight to its leave cell.
            self.need(2);index=self.cache.pop();limit=self.cache.pop();self.flush()
            compute.logic(self.s,self.T['xor'],self.XR,index,limit);zero,yes=self.branch(self.XR)
            leave=self.b.new_cell();Seq(self.b,zero).rows([]).next=leave;self.b.flush()
            self.begin_block(yes);self.mem_push(self.RSTK,self.RP,[limit,index])
            control.append(['do',self.begin_block(),leave]);return
        if t=='leave':
            entry=self.do_entry();self.flush();self.adjust(self.RP,[],-2)
            if entry[2] is None:entry[2]=self.b.new_cell()
            self.jump(entry[2]);self.b.flush();self.s=None;self.begin_block();return
        if t=='loop':
            kind,start,leave=control.pop();self.flush()
            limit,index=self.mem_pop(self.RSTK,self.RP,2);self.pinned=()
            one=self.const(1);s=self.s;nxt=self.REGS+64*(NREGS-1)
            s.adder(self.T['add'],self.TMP,index,one,0);s.rows([copy(32,nxt,self.TMP)])
            compute.logic(s,self.T['xor'],self.XR,nxt,limit)
            zero,more=self.branch(self.XR)
            self.s=Seq(self.b,more);self.s.layer();self.mem_push(self.RSTK,self.RP,[limit,nxt])
            self.s.jump(start);self.b.flush();self.s=None
            if leave is not None:
                Seq(self.b,zero).rows([]).next=leave;self.b.flush();self.begin_block(leave)
            else:self.begin_block(zero)
            return
        if t in self.words:
            kind,value=self.words[t]
            if kind=='lit':self.literal(value)
            else:self.call(value)
            return
        value=number(t)
        if value is not None:self.literal(value);return
        self.primitive(t)

class Tokens:
    """Words of the source: runs of bytes above 32, ASCII letters folded to
    lower case (raw keeps the original); a word \\ ends the line."""
    def __init__(self,text):self.text=text.encode('latin-1');self.pos=0
    def word(self):
        """The next word, without comment handling ([CHAR] \\)."""
        t=self.text
        while self.pos<len(t) and t[self.pos]<33:self.pos+=1
        if self.pos==len(t):return False
        start=self.pos
        while self.pos<len(t) and t[self.pos]>32:self.pos+=1
        self.raw=t[start:self.pos]
        if len(self.raw)>255:raise CompileError('word too long')
        self.tok=self.raw.lower().decode('latin-1');return True
    def next(self):
        while self.word():
            if self.raw!=b'\\':return True
            t=self.text
            while self.pos<len(t) and t[self.pos]!=10:self.pos+=1
        return False
    def need(self):
        if not self.next():raise CompileError('unexpected end of the source')
        return self.tok
    def string(self):
        """S" text": one delimiter, then bytes up to the closing quote."""
        t=self.text;self.pos=min(self.pos+1,len(t));end=t.find(b'"',self.pos)
        if end<0:raise CompileError('unfinished string')
        data=t[self.pos:end];self.pos=end+1;return data

def compile_forth(text,main='main'):
    return Compiler().compile_source(text,main)
