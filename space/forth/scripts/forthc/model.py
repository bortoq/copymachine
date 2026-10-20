"""Direct Forth compiler, host model (9.5): Forth source to emulator index code.

No RV32I and no inner interpreter: each word is compiled into layers of
copies. Inside straight-line code the compiler keeps the top stack items in
registers (a stack cache) and tracks the depth, so DUP, DROP, SWAP, OVER, ROT
cost nothing and literals are one copy. At every control boundary (branch,
loop, call, return) the cache is written to the data stack in memory.

Memory stacks hold 256 entries at a 64-bit stride; a stack pointer is kept
as eight copies of its 8-bit value, so several patches of one tick read
distinct sources. A call pushes the continuation's link fields (ret and
ret+layer, 48 bits) on the return stack; a return copies them straight into
the link fields of the return trampoline. Data addresses are byte addresses;
cells are 32-bit, at a 64-bit stride in the space, so a patched word address
never carries. @ and ! check the address: outside the data cells THROW -9,
unaligned THROW -23.

* / MOD /MOD call shared straight-line subroutines placed by a list scheduler
(Sched); the stack cache stays in registers across them. Division truncates
toward zero (C semantics, as pForth's /); a zero divisor throws -10. An
uncaught THROW halts.

Supported: decimal literals, : ; EXIT RECURSE, VARIABLE CONSTANT, + - * / MOD
/MOD AND OR XOR = < 0= DUP DROP SWAP OVER ROT >R R> R@ @ ! EMIT, IF ELSE THEN,
BEGIN UNTIL WHILE REPEAT AGAIN, DO LOOP I, EXECUTE ['] CATCH THROW. Output
goes to stdout.
"""
import sys
from pathlib import Path
from copycode.vm1.backend import Machine,Stream,Builder,copy,numeric
from copycode.vm1 import compute
from copycode.vm1.compute import Seq

SIZE=(1<<24)-16;CELL=1024
M=Machine(SIZE,8,CELL,4096)
L=M.layer_bits
D=3<<22
SP=D;RP=D+64                       # 8 copies of an 8-bit index each
HANDLER=D+128;CODE=D+192           # CATCH frame pointer (RP copies), THROW code
REGS=D+1024;NREGS=48               # cache registers, 64-bit stride
TMP=D+4096;XR=D+4160;Z=D+4224;IDX=D+4288  # IDX: 16 index registers, 16 bits
LINK=D+4608                        # assembled return entry (48 bits)
FLT=D+4672                         # address check: fault flag, copy, code
MA=D+4800;MB=D+4864;MP=D+4928;MQ=D+4992;MR=D+5056  # subroutine operands
ZERO=D+5120;CONSTS=D+8192;TAB=D+(1<<17)
STK=D+(1<<20);RSTK=STK+(1<<14);MEM=D+(1<<21);MW=12  # 4096 data cells
SCR=D+(1<<20)+(1<<16)              # scratch registers of the subroutines
HTAB=MEM+(1<<18)                   # tables of the subroutines, to the end
DATA_START=256

class CompileError(Exception):pass

def tables(t):
    T=compute.standard_tables(t)
    for c in range(-8,9):
        T['off',c]=t.table(8,7,[sum(((i+c)&255)<<8*k for k in range(8)) for i in range(256)])
    T['rev8']=t.table(8,4,[int(f'{i:08b}'[::-1],2) for i in range(256)])
    T['zero32']=t.table(4,6,[0xffffffff if i==0 else 0 for i in range(16)])
    T['nz2']=t.table(4,2,[3 if i else 0 for i in range(16)])
    T['lt32']=t.table(3,6,[0xffffffff if ((i>>1&1) if (i>>1&1)!=(i>>2&1) else not(i&1)) else 0 for i in range(8)])
    # Address check: OR of bits [14,22) and [22,30) (two tables, one layer);
    # chk: bits [30,32) nonzero, bits [0,2) nonzero; fault: flag, copy, code.
    T['or8b']=t.table(8,1,[int(i!=0) for i in range(256)])
    T['chk']=t.table(4,2,[int(i&3!=0)|int(i>>2!=0)<<1 for i in range(16)])
    def fault(i):
        code=-9 if i&7 else -23 if i&8 else 0
        return int(code!=0)*3|(code&0xffffffff)<<2
    T['fault']=t.table(4,6,[fault(i) for i in range(16)])
    T['xr2']=t.table(2,2,[((i^i>>1)&1)*3 for i in range(4)])
    return T

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
    are single assignment, so only read-after-write constraints exist."""
    def __init__(self,b,cell=None):self.seq=Seq(b,cell);self.layers=[];self.tables=[]
    def at(self,t):
        while len(self.layers)<=t:self.layers.append(self.seq.layer());self.tables.append(set())
        return self.layers[t]
    def place(self,row,t,table=None):
        while True:
            layer=self.at(t)
            if table not in self.tables[t]:
                try:
                    slot=layer.add(row)
                    if table is not None:self.tables[t].add(table)
                    return t,slot
                except ValueError:pass
            t+=1
    def copy(self,n,dst,src,ready):return self.place(copy(n,dst,src),ready)[0]+1
    def lookup(self,table,s,width,dst,segs,preset=0):
        """segs: (src, src for the upper endpoint, n, index offset, ready)."""
        placed=[];latest=-2
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
    def __init__(self):
        self.st=Stream(M);self.b=Builder(self.st)
        self.T=tables(compute.Tables(self.st,TAB,STK))
        self.consts={};self.words={};self.cache=[];self.s=None
        self.here=DATA_START;self.data={}
        self.halt=CELL  # the zero cell: the next fetch finds only NOPs
        tr=Seq(self.b);tr.rows([]).next=CELL;self.tramp=tr.entry();self.b.flush()
        ex=Seq(self.b);ex.rows([]).next=CELL;self.ex=ex.entry();self.b.flush()
        self.scr=SCR;self.helpers={};self.htables=compute.Tables(self.st,HTAB,M.size)
        self.thrower=self.build_thrower()
    def scratch(self,bits,align=64):
        at=-(-self.scr//align)*align;self.scr=at+bits
        if self.scr>MEM:raise CompileError('scratch registers exhausted')
        return at
    # --- data ------------------------------------------------------------
    def const(self,value,bits=32):
        key=(value&((1<<bits)-1),bits)
        if key not in self.consts:
            self.consts[key]=CONSTS+64*len(self.consts)
        return self.consts[key]
    def reg(self):
        used=set(self.cache)
        for k in range(NREGS):
            r=REGS+64*k
            if r not in used and r not in self.pinned:return r
        raise CompileError('stack cache exhausted')
    pinned=()
    # --- memory stacks ----------------------------------------------------
    def adjust(self,pointer,offsets,delta):
        """IDX+16k = pointer+offsets[k] (value, copy); pointer += delta."""
        items=[(self.T['off',c],7,16,IDX+16*k,[(pointer+8*k,8,0)],0) for k,c in enumerate(offsets)]
        items.append((self.T['off',delta],7,64,pointer,[(pointer+8*len(offsets),8,0)],0))
        self.s.lookups(items)
    def patched(self,rows,fields):
        """Rows whose endpoint fields get IDX+16k (and its copy) at bit 6."""
        s=self.s;n=len(rows)
        patches=[s.layer() for _ in range(-(-2*n//7))];s.layer()
        layer=s.layer();slots=[layer.add(r) for r in rows]
        for k,slot in enumerate(slots):
            for j,(f,src) in enumerate(((fields[0],IDX+16*k),(fields[1],IDX+16*k+8))):
                patches[(2*k+j)//7].add(copy(8,M.field(layer.cell,slot,f)+6,src))
    def mem_pop(self,base,pointer,n,width=32):
        regs=[self.reg_for_pop(k) for k in range(n)]
        self.adjust(pointer,[-n+k for k in range(n)],-n)
        self.patched([(r,r+width,base+64*k,base+64*k+width) for k,r in enumerate(regs)],(2,3))
        return regs
    def reg_for_pop(self,k):
        r=self.reg();self.pinned=tuple(self.pinned)+(r,);return r
    def mem_push(self,base,pointer,srcs,width=32):
        self.adjust(pointer,list(range(len(srcs))),len(srcs))
        self.patched([(base+64*k,base+64*k+width,r,r+width) for k,r in enumerate(srcs)],(0,1))
    def need(self,n):
        """Ensure n cached items, popping the missing ones from memory."""
        missing=n-len(self.cache)
        while missing>0:
            k=min(missing,7)
            regs=self.mem_pop(STK,SP,k);self.pinned=()
            self.cache=regs+self.cache;missing-=k
    def flush(self):
        while self.cache:
            part=self.cache[:7];self.cache=self.cache[7:]
            self.mem_push(STK,SP,part)
    def pop(self):self.need(1);return self.cache.pop()
    # --- control ----------------------------------------------------------
    def begin_block(self,cell=None):
        """Start a new layer run; the previous run continues into it."""
        cell=cell if cell is not None else self.b.new_cell()
        if self.s is not None and self.s.layers:self.s.jump(cell)
        self.b.flush();self.s=Seq(self.b,cell);self.s.layer();return cell
    def nonzero(self,r):
        """E = (r != 0, copy), for a two-way decision."""
        s=self.s
        s.lookups(compute.or_chunks(self.T,Z,r,0,32))
        s.lookups([(self.T['nz2'],2,2,XR,[(Z,4,0)],0)])
        return XR
    def branch(self,flag):
        """Decide on flag != 0: returns (zero cell, nonzero cell)."""
        e=self.nonzero(flag);g=self.s.decide(e,1);self.b.flush();self.s=None
        return g,g+CELL
    def call(self,entry):
        self.flush();cont=self.b.new_cell()
        self.mem_push(RSTK,RP,[self.const(cont|(cont+L)<<24,64)],48)
        self.s.jump(entry);self.b.flush();self.s=None
        self.begin_block(cont)
    def call_indirect(self,xt,cont=None):
        """Call the word whose entry cell address is in register xt.

        Entries are cells, so bits [10,24) select the target in both link
        endpoints; the low bits of the templates stay 0 and layer."""
        self.flush();cont=cont if cont is not None else self.b.new_cell()
        self.mem_push(RSTK,RP,[self.const(cont|(cont+L)<<24,64)],48)
        s=self.s;p0=s.layer();p1=s.layer();s.layer()
        p0.add(copy(14,M.field(self.ex,7,2)+10,xt+10));p1.add(copy(14,M.field(self.ex,7,3)+10,xt+10))
        s.jump(self.ex);self.b.flush();self.s=None
        return cont
    def catch(self):
        """Frame on the return stack: data stack pointer, previous handler,
        link to the throw continuation; HANDLER then points above it."""
        xt=self.pop();self.flush()
        thrown=self.b.new_cell();join=self.b.new_cell()
        # Entries are 48 bits (below the 64-bit stride); pointers are restored
        # from their first copy by the identity table, which replicates it.
        self.push_frame(thrown)
        normal=self.call_indirect(xt)
        self.begin_block(normal)
        _,prev,_=self.mem_pop(RSTK,RP,3,48);self.pinned=()
        self.s.lookups([(self.T['off',0],7,64,HANDLER,[(prev,8,0)],0)]);self.cache=[];self.literal(0);self.flush()
        self.s.jump(join);self.b.flush();self.s=None
        self.begin_block(thrown);r=self.reg();self.s.rows([copy(32,r,CODE)]);self.cache=[r];self.flush()
        self.s.jump(join);self.b.flush();self.s=None
        self.begin_block(join)
    def build_thrower(self):
        """Shared nonzero THROW, code in CODE: the frame at HANDLER restores
        both stacks and the handler, then its link continues at the catch."""
        self.cache=[];self.s=Seq(self.b);self.s.rows([copy(64,RP,HANDLER)]);entry=self.s.entry()
        saved,prev,link=self.mem_pop(RSTK,RP,3,48);self.pinned=()
        self.s.lookups([(self.T['off',0],7,64,SP,[(saved,8,0)],0),(self.T['off',0],7,64,HANDLER,[(prev,8,0)],0)])
        self.s.rows([copy(48,M.field(self.tramp,7,2),link)])
        self.s.layer();self.s.jump(self.tramp);self.b.flush();self.s=None
        return entry
    def throw(self):
        code=self.pop();self.flush()
        self.s.rows([copy(32,CODE,code)])
        zero,thrown=self.branch(code)
        Seq(self.b,thrown).rows([]).next=self.thrower;self.b.flush()
        self.begin_block(zero)
    def push_frame(self,thrown):
        self.mem_push(RSTK,RP,[SP,HANDLER,self.const(thrown|(thrown+L)<<24,64)],48)
        self.s.rows([copy(64,HANDLER,RP)])
    def ret(self):
        self.flush()
        self.adjust(RP,[-1],-1)
        s=self.s;p=s.layer();s.layer()
        layer=s.layer();slot=layer.add((M.field(self.tramp,7,2),M.field(self.tramp,7,2)+48,RSTK,RSTK+48))
        p.add(copy(8,M.field(layer.cell,slot,2)+6,IDX));p.add(copy(8,M.field(layer.cell,slot,3)+6,IDX+8))
        s.layer();s.jump(self.tramp);self.b.flush();self.s=None
    def check_address(self,a,access):
        """Check the byte address in register a, then continue in the ok cell.

        One round ORs the high bits [14,32) in three chunks and tests the low
        two bits; a second reads flag, copy and code from the fault table. The
        fault cell copies the code to CODE and throws. access(l0, l1, read,
        ok) adds the access: patches in l0/l1, rows in the read layer (run
        before the decision) or in a layer of the ok run."""
        s=self.s;T=self.T
        l0=s.layer();l1=s.layer();s.layer();r=s.layer()
        for table,sh,w,dst,segs in ((T['or8'],1,1,Z,[(a+14,8,0)]),(T['or8b'],1,1,Z+1,[(a+22,8,0)]),
                                    (T['chk'],2,2,Z+2,[(a+30,2,0),(a,2,2)])):
            slot=r.add((dst,dst+w,table,table+w))
            for src,n,off in segs:
                l0.add(copy(n,M.field(r.cell,slot,2)+sh+off,src));l1.add(copy(n,M.field(r.cell,slot,3)+sh+off,src))
        s.lookups([(T['fault'],6,34,FLT,[(Z,4,0)],0)])
        group=self.b.group(1);bit=M.cell_bits.bit_length()-1
        patch=s.layer();s.layer();x=s.layer();x.next=group
        patch.add(copy(1,M.field(x.cell,7,2)+bit,FLT));patch.add(copy(1,M.field(x.cell,7,3)+bit,FLT+1))
        ok=Seq(self.b,group);access(l0,l1,r,ok)
        Seq(self.b,group+CELL).rows([copy(32,CODE,FLT+2)]).next=self.thrower
        self.s=ok
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
                segs=[(MA+4*i,MA+4*i,4,0,0),(MB+4*j,MB+4*j,4,4,0)]
                if i:prev,t=P[i-1,j];segs.append((prev+4,prev+8,4,8,t))
                P[i,j]=(r,S.lookup(m4,4,12,r,segs))
        X={(0,k):P[k,0] for k in range(8)}
        for j in range(1,8):
            for k in range(j,8):
                x=self.scratch(8);a,ta=X[j-1,k];b,tb=P[k-j,j]
                segs=[(a,a,4,0,ta),(b,b,4,4,tb)]
                if k>j:c,tc=X[j,k-1];segs.append((c+4,c+5,1,8,tc))
                X[j,k]=(x,S.lookup(add,3,6,x,segs))
        for k in range(8):src,t=X[k,k];S.copy(4,MP+4*k,src,t)
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
        e=self.nonzero(MB);g=s.decide(e,1);self.b.flush();self.s=None
        Seq(self.b,g).rows([copy(32,CODE,self.const(-10))]).next=self.thrower
        S=Sched(self.b,g+CELL)
        sub=self.copies(3,9,3,[compute.sub_entry(i) for i in range(512)])
        qsel=self.htables.table(3,2,[((i>>2 if i&1 else i>>1)&1)*3 for i in range(8)])
        def nib(reg,t):return [(reg+4*i,t) for i in range(8)]
        def negate_select(value,t,sign,sign2,ts,dst,table):
            w=self.scratch(128,128);t1=S.copy(32,w,value,t)
            t2=S.chain(table,w+64,[None]*8,nib(value,t),t,carry=1)
            return S.lookup(w,0,32,dst,[(sign,sign2,1,6,max(ts,t1,t2))])
        absa,absb=self.scratch(32),self.scratch(32)
        ta=negate_select(MA,0,MA+31,MA+31,0,absa,sub[0]);tb=negate_select(MB,0,MB+31,MB+31,0,absb,sub[1])
        rem,tr=ZERO,0;Q=self.scratch(32);tq=0
        for k in range(31,-1,-1):
            w=self.scratch(256,256);L=self.scratch(32)
            def step(table,dst,i,carry_src,t,preset):
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
        sq=self.scratch(2);ts=S.lookup(T['xr2'],2,2,sq,[(MA+31,MA+31,1,0,0),(MB+31,MB+31,1,1,0)])
        negate_select(Q,tq,sq,sq+1,ts,MQ,sub[0]);negate_select(rem,tr,MA+31,MA+31,0,MR,sub[1])
        return entry,S.finish()
    def helper(self,name,args,outs):
        """Call a shared subroutine: operands to its inputs and the exit link
        patched with the continuation in one layer; results then to cache."""
        self.need(len(args));regs=self.cache[-len(args):];del self.cache[-len(args):]
        entry,exit_cell=self.helpers[name];cont=self.b.new_cell()
        rows=[copy(48,M.field(exit_cell,7,2),self.const(cont|(cont+L)<<24,64))]
        layer=self.s.rows(rows)
        for dst,src in zip(args,regs):
            try:layer.add(copy(32,dst,src))
            except ValueError:layer=self.s.rows([copy(32,dst,src)])  # DUP: one register
        self.s.jump(entry);self.b.flush();self.s=Seq(self.b,cont)
        res=[]
        for src in outs:r=self.reg();res.append(r);self.cache.append(r)
        self.s.rows([copy(32,r,src) for r,src in zip(res,outs)])
    # --- primitives ---------------------------------------------------------
    def binary(self,name):
        self.need(2);b=self.cache.pop();a=self.cache.pop();s=self.s
        if a==b:
            # DUP shares a register; one tick may not read it twice.
            self.cache.append(a);b=self.reg();self.cache.pop();s.rows([copy(32,b,a)])
        self.cache+= [a,b];r=self.reg();del self.cache[-2:]
        if name in ('+','-'):
            s.adder(self.T['add' if name=='+' else 'sub'],TMP,a,b,int(name=='-'));s.rows([copy(32,r,TMP)])
        elif name in ('and','or','xor'):compute.logic(s,self.T[name],r,a,b)
        elif name=='=':
            compute.logic(s,self.T['xor'],XR,a,b);s.lookups(compute.or_chunks(self.T,Z,XR,0,32))
            s.lookups([(self.T['zero32'],6,32,r,[(Z,4,0)],0)])
        elif name=='<':
            s.adder(self.T['sub'],TMP,a,b,1)
            s.lookups([(self.T['lt32'],6,32,r,[(TMP+32,1,0),(a+31,1,1),(b+31,1,2)],0)])
        self.cache.append(r)
    def primitive(self,name):
        s=self.s
        if name in ('+','-','and','or','xor','=','<'):self.binary(name)
        elif name=='*':self.helper('mul',(MA,MB),(MP,))
        elif name=='/':self.helper('div',(MA,MB),(MQ,))
        elif name=='mod':self.helper('div',(MA,MB),(MR,))
        elif name=='/mod':self.helper('div',(MA,MB),(MR,MQ))
        elif name=='0=':
            a=self.pop();r=self.reg()
            s.lookups(compute.or_chunks(self.T,Z,a,0,32));s.lookups([(self.T['zero32'],6,32,r,[(Z,4,0)],0)])
            self.cache.append(r)
        elif name=='dup':self.need(1);self.cache.append(self.cache[-1])
        elif name=='drop':
            if self.cache:self.cache.pop()
            else:self.adjust(SP,[],-1)
        elif name=='swap':self.need(2);self.cache[-2:]=self.cache[-1:-3:-1]
        elif name=='over':self.need(2);self.cache.append(self.cache[-2])
        elif name=='rot':self.need(3);self.cache.append(self.cache.pop(-3))
        elif name=='>r':r=self.pop();self.mem_push(RSTK,RP,[r])
        elif name=='r>':self.cache.append(self.mem_pop(RSTK,RP,1)[0]);self.pinned=()
        elif name in ('r@','i'):
            r=self.reg()
            self.adjust(RP,[-1],0);self.patched([(r,r+32,RSTK,RSTK+32)],(2,3));self.cache.append(r)
        elif name=='@':
            # The load runs before the decision; on a fault the cache is dead.
            a=self.pop();self.pinned=(a,);r=self.reg();self.pinned=()
            def load(p0,p1,layer,ok):
                slot=layer.add((r,r+32,MEM,MEM+32))
                p0.add(copy(MW,M.field(layer.cell,slot,2)+6,a+2));p1.add(copy(MW,M.field(layer.cell,slot,3)+6,a+2))
            self.check_address(a,load);self.cache.append(r)
        elif name=='!':
            self.need(2);a=self.cache.pop();v=self.cache.pop()
            def store(p0,p1,layer,ok):
                ok=ok.layer();slot=ok.add((MEM,MEM+32,v,v+32))
                p0.add(copy(MW,M.field(ok.cell,slot,0)+6,a+2));p1.add(copy(MW,M.field(ok.cell,slot,1)+6,a+2))
            self.check_address(a,store)
        elif name=='emit':
            c=self.pop();out=XR
            s.lookups([(self.T['rev8'],4,8,out,[(c,8,0)],0)])
            s.rows([(M.stdout,M.stdout,out,out+8)])
        else:raise CompileError('unknown word '+name)
    def literal(self,value):
        r=self.reg();self.s.rows([copy(32,r,self.const(value))]);self.cache.append(r)
    # --- source -------------------------------------------------------------
    def compile_source(self,text,main):
        tokens=[]
        for line in text.splitlines():
            words=line.split()
            if '\\' in words:words=words[:words.index('\\')]
            tokens+=words
        uses={t.lower() for t in tokens}
        if '*' in uses:self.helpers['mul']=self.build_mul()
        if uses&{'/','mod','/mod'}:self.helpers['div']=self.build_div()
        tokens=iter(tokens);control=[];word=None
        for tok in tokens:
            t=tok.lower()
            if t=='(':
                while next(tokens)!=')':pass
                continue
            if word is None:
                if t==':':
                    name=next(tokens).lower();entry=self.b.new_cell()
                    word=name;self.words[name]=('call',entry);self.s=None;self.cache=[]
                    self.begin_block(entry)
                elif t=='variable':
                    self.words[next(tokens).lower()]=('lit',self.here);self.here+=4
                elif t=='constant':raise CompileError('CONSTANT needs a literal before it')
                else:
                    try:value=int(t)
                    except ValueError:raise CompileError('only definitions at top level: '+tok)
                    if next(tokens).lower()!='constant':raise CompileError('expected CONSTANT')
                    self.words[next(tokens).lower()]=('lit',value)
                continue
            if t==';':
                if control:raise CompileError('unbalanced control structure')
                self.ret();word=None;continue
            if t=='exit':self.ret();self.begin_block();continue
            if t=='recurse':self.call(self.words[word][1]);continue
            if t=="[']":self.literal(self.words[next(tokens).lower()][1]);continue
            if t=='execute':
                xt=self.pop();self.begin_block(self.call_indirect(xt));continue
            if t=='catch':self.catch();continue
            if t=='throw':self.throw();continue
            if t=='if':
                f=self.pop();self.flush();zero,yes=self.branch(f)
                control.append(('if',zero));self.begin_block(yes);continue
            if t=='else':
                kind,zero=control.pop();self.flush();join=self.b.new_cell();self.s.jump(join)
                self.b.flush();self.s=None;control.append(('else',join));self.begin_block(zero);continue
            if t=='then':
                kind,target=control.pop();self.flush()
                if kind=='if':
                    join=self.b.new_cell();self.s.jump(join);self.b.flush()
                    Seq(self.b,target).rows([]).next=join;self.b.flush();self.s=None;self.begin_block(join)
                else:self.begin_block(target)
                continue
            if t=='begin':self.flush();control.append(('begin',self.begin_block()));continue
            if t in ('until','while'):
                f=self.pop();self.flush();zero,yes=self.branch(f)
                if t=='until':
                    kind,start=control.pop()
                    Seq(self.b,zero).rows([]).next=start;self.b.flush();self.begin_block(yes)
                else:control.append(('while',zero));self.begin_block(yes)
                continue
            if t in ('repeat','again'):
                if t=='repeat':_,exit_cell=control.pop()
                _,start=control.pop();self.flush();self.s.jump(start);self.b.flush();self.s=None
                if t=='repeat':self.begin_block(exit_cell)
                else:self.begin_block()
                continue
            if t=='do':
                self.need(2);index=self.cache.pop();limit=self.cache.pop();self.flush()
                self.mem_push(RSTK,RP,[limit,index]);control.append(('do',self.begin_block()));continue
            if t=='loop':
                kind,start=control.pop();self.flush()
                limit,index=self.mem_pop(RSTK,RP,2);self.pinned=()
                one=self.const(1);s=self.s;nxt=REGS+64*(NREGS-1)
                s.adder(self.T['add'],TMP,index,one,0);s.rows([copy(32,nxt,TMP)])
                compute.logic(s,self.T['xor'],XR,nxt,limit)
                zero,more=self.branch(XR)
                self.s=Seq(self.b,more);self.s.layer();self.mem_push(RSTK,RP,[limit,nxt])
                self.s.jump(start);self.b.flush();self.s=None
                self.begin_block(zero);continue
            if t in self.words:
                kind,value=self.words[t]
                if kind=='lit':self.literal(value)
                else:self.call(value)
                continue
            try:self.literal(int(t));continue
            except ValueError:pass
            self.primitive(t)
        if word is not None:raise CompileError('unfinished definition')
        if main not in self.words:raise CompileError('no main word')
        # Entry: a frame for an uncaught THROW (it halts), call main, halt.
        self.s=None;self.cache=[];start=self.begin_block();uncaught=self.b.new_cell()
        self.push_frame(uncaught);self.call(self.words[main][1])
        self.s.jump(self.halt);self.b.flush()
        Seq(self.b,uncaught).rows([]).next=self.halt;self.b.flush()
        st=self.st
        st.put(SP,numeric(0,8));st.put(RP,numeric(0,8));st.put(HANDLER,numeric(0,8));st.put(ZERO,bytes(16))
        for (value,bits),at in self.consts.items():st.put(at,numeric(value,(bits+7)//8))
        self.entry=start;return st.finish(start)

def compile_forth(text,main='main'):
    return Compiler().compile_source(text,main)
