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
never carries. No range or alignment checks are generated yet.

Supported: decimal literals, : ; EXIT RECURSE, VARIABLE CONSTANT, + - AND OR
XOR = < 0= DUP DROP SWAP OVER ROT >R R> R@ @ ! EMIT, IF ELSE THEN,
BEGIN UNTIL WHILE REPEAT AGAIN, DO LOOP I. Output goes to stdout.
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
ZERO=D+5120;CONSTS=D+8192;TAB=D+(1<<17)
STK=D+(1<<20);RSTK=STK+(1<<14);MEM=D+(1<<21);MW=12  # 4096 data cells
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
    return T

class Compiler:
    def __init__(self):
        self.st=Stream(M);self.b=Builder(self.st)
        self.T=tables(compute.Tables(self.st,TAB,STK))
        self.consts={};self.words={};self.cache=[];self.s=None
        self.here=DATA_START;self.data={}
        self.halt=CELL  # the zero cell: the next fetch finds only NOPs
        tr=Seq(self.b);tr.rows([]).next=CELL;self.tramp=tr.entry();self.b.flush()
        ex=Seq(self.b);ex.rows([]).next=CELL;self.ex=ex.entry();self.b.flush()
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
        self.mem_push(RSTK,RP,[SP,HANDLER,self.const(thrown|(thrown+L)<<24,64)],48)
        self.s.rows([copy(64,HANDLER,RP)])
        normal=self.call_indirect(xt)
        self.begin_block(normal)
        _,prev,_=self.mem_pop(RSTK,RP,3,48);self.pinned=()
        self.s.lookups([(self.T['off',0],7,64,HANDLER,[(prev,8,0)],0)]);self.cache=[];self.literal(0);self.flush()
        self.s.jump(join);self.b.flush();self.s=None
        self.begin_block(thrown);r=self.reg();self.s.rows([copy(32,r,CODE)]);self.cache=[r];self.flush()
        self.s.jump(join);self.b.flush();self.s=None
        self.begin_block(join)
    def throw(self):
        code=self.pop();self.flush()
        self.s.rows([copy(32,CODE,code)])
        zero,thrown=self.branch(code)
        self.s=Seq(self.b,thrown);self.s.rows([copy(64,RP,HANDLER)])
        saved,prev,link=self.mem_pop(RSTK,RP,3,48);self.pinned=()
        self.s.lookups([(self.T['off',0],7,64,SP,[(saved,8,0)],0),(self.T['off',0],7,64,HANDLER,[(prev,8,0)],0)])
        self.s.rows([copy(48,M.field(self.tramp,7,2),link)])
        self.s.layer();self.s.jump(self.tramp);self.b.flush();self.s=None
        self.begin_block(zero)
    def ret(self):
        self.flush()
        self.adjust(RP,[-1],-1)
        s=self.s;p=s.layer();s.layer()
        layer=s.layer();slot=layer.add((M.field(self.tramp,7,2),M.field(self.tramp,7,2)+48,RSTK,RSTK+48))
        p.add(copy(8,M.field(layer.cell,slot,2)+6,IDX));p.add(copy(8,M.field(layer.cell,slot,3)+6,IDX+8))
        s.layer();s.jump(self.tramp);self.b.flush();self.s=None
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
            a=self.pop();r=self.reg();self.pinned=(a,)
            p0=s.layer();p1=s.layer();s.layer();layer=s.layer()
            slot=layer.add((r,r+32,MEM,MEM+32))
            p0.add(copy(MW,M.field(layer.cell,slot,2)+6,a+2));p1.add(copy(MW,M.field(layer.cell,slot,3)+6,a+2))
            self.pinned=();self.cache.append(r)
        elif name=='!':
            self.need(2);a=self.cache.pop();v=self.cache.pop()
            p0=s.layer();p1=s.layer();s.layer();layer=s.layer()
            slot=layer.add((MEM,MEM+32,v,v+32))
            p0.add(copy(MW,M.field(layer.cell,slot,0)+6,a+2));p1.add(copy(MW,M.field(layer.cell,slot,1)+6,a+2))
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
        # Entry: call main, then halt.
        self.s=None;self.cache=[];start=self.begin_block();self.call(self.words[main][1])
        self.s.jump(self.halt);self.b.flush()
        st=self.st
        st.put(SP,numeric(0,8));st.put(RP,numeric(0,8));st.put(HANDLER,numeric(0,8));st.put(ZERO,bytes(16))
        for (value,bits),at in self.consts.items():st.put(at,numeric(value,(bits+7)//8))
        return st.finish(start)

def compile_forth(text,main='main'):
    return Compiler().compile_source(text,main)
