"""Static RV32I to emulator index-code translator: host control implementation.

The guest Forth translator (forth/translate.fth) must produce the same bytes;
this module is its independent control and a fast development model. Each
RV32I word of the translated range [0, 2^cbits) gets a 4096-bit block of
four 1024-bit cells; slot 0 is the block entry. Decoding, register numbers
and immediates are resolved at translation time. Data-dependent work runs in
shared handlers built from table lookups whose addresses are patched by copies.

Layout (bit addresses, A=24, P=8, layer 768 bits, cell 1024 bits):
  [0,768)                processor; cell 0 is the entry layer
  cells 1..              handlers (cell 1 stays zero: the halt cell)
  CODE_BASE + 4096*w     block of instruction word w; CODE_BASE is aligned
                         to 2^(10+cbits), so a JALR target selects its block
                         by copying address bits [2,cbits) to bits [12,..)
  D = 3*2^22             registers x0..x31, PC, STATUS (1088 bits, dumped)
  MEM = D + 2^21         guest word w at MEM+64*w, bytes LSB first
At halt the program writes the 1088 state bits and then the memory region
to stdout. Statuses 0..10 follow the RV32I image; 11 means an untranslated
target and 12 a store into translated code (PC is the next instruction).
"""
A=24;S=(1<<24)-16;SLOTS=8;INST=4*A;L=SLOTS*INST;CELL=1024
STDIN=S+1;STDOUT=S+2
D=3<<22;STATE=D;PCREG=D+1024;STATUS=D+1056
SCR=D+4096
OPA=SCR;OPB=SCR+64;OPSEL=SCR+96;OPC=SCR+128;PCN=SCR+160;RES=SCR+192;EA=SCR+256
W=SCR+320;FLAGS=SCR+384;C2=SCR+400;Z=SCR+408;QK=SCR+416;CL=SCR+424;HB=SCR+440;U=SCR+448
DISCARD=SCR+512;ZERO=SCR+1024
KST=D+8192;TABLES=D+16384;SITES=D+(1<<18);MEM=D+(1<<21)
SITE=256;K1=144;SEL=176;K2=184;K3=216
RETLO,RETHI,WBLO,WBHI,FLLO,FLHI=0,24,48,72,96,120
CHUNK=4096
STATUS_UNTRANSLATED,STATUS_MODIFIED=11,12
from copycode.vm1 import backend
from copycode.vm1.backend import copy,numeric
M=backend.Machine(S,SLOTS,CELL,CHUNK)

def field(cell,slot,f):return M.field(cell,slot,f)
def out(n,src):return (STDOUT,STDOUT,src,src+n)
def encode(rows):return backend.encode(M,rows)
def Stream():return backend.Stream(M)
Builder=backend.Builder

from copycode.vm1 import compute
from copycode.vm1.compute import Seq

class Tables(compute.Tables):
    def __init__(self,stream):super().__init__(stream,TABLES,SITES)

def build_tables(t,mbits,cbits):
    T=compute.standard_tables(t)
    r=-(-(32-mbits)//8);k=-(-(mbits-cbits)//8)
    def cls(i):
        op=i&15;q=(i>>4)&((1<<r)-1);kk=(i>>(4+r))&((1<<k)-1);e=i>>(4+r+k)&3
        sub=0
        if op<=4:
            wb=(1,1,2,2,4)[op];c=9 if q else 10 if e%wb else op
        elif op<=7:
            wb=(1,2,4)[op-5];c=11 if q else 12 if e%wb else op;sub=int(not kk)
        elif op==8:
            c=13 if e&2 else 8;sub=1 if q else 2 if kk else 0
        else:c=15
        return c|c<<4|sub<<8|sub<<10
    T['class']=t.table(4+r+k+2,4,[cls(i) for i in range(1<<(4+r+k+2))])
    T['r'],T['k']=r,k
    return T

def build_handlers(b,T,mbits,cbits,code_base):
    """Shared code; returns entry and exit cell addresses."""
    H={}
    H['xw'],H['x']=compute.exit_layers(b,RES,DISCARD)
    H['halt']=compute.halt(b,[(1088,STATE),(16<<mbits,MEM)])
    b.flush()
    def stub(seq,code,rows=()):compute.stub(seq,STATUS,KST+32*code,H['halt'],rows)
    s=Seq(b);s.adder(T['add'],RES,OPA,OPB,0);s.jump(H['xw']);H['add']=s.entry();b.flush()
    s=Seq(b);s.adder(T['sub'],RES,OPA,OPB,1);g=s.decide(OPSEL,2);H['sub']=s.entry();b.flush()
    Seq(b,g).rows([]).next=H['xw']
    def compare(seq):compute.compare(seq,T,RES,OPA,OPB,Z,FLAGS)
    s=Seq(b,g+CELL);compare(s);s.jump(H['x']);b.flush()
    s=Seq(b,g+2*CELL);compare(s)
    H['flag_row'],H['bx']=compute.flag_exit(s,C2,FLAGS);b.flush()
    for name in ('xor','or','and'):
        s=Seq(b);compute.logic(s,T[name],RES,OPA,OPB)
        s.jump(H['xw']);H[name]=s.entry();b.flush()
    s=Seq(b);compute.shift_right(s,T,RES,OPA,OPB,W,ZERO,False);s.jump(H['xw']);H['srl']=s.entry();b.flush()
    s=Seq(b);compute.shift_right(s,T,RES,OPA,OPB,W,ZERO,True);s.jump(H['xw']);H['sra']=s.entry();b.flush()
    s=Seq(b);compute.shift_left(s,T,RES,OPA,OPB,W,ZERO,U);s.jump(H['xw']);H['sll']=s.entry();b.flush()
    # Memory operations and JALR share the effective address and its checks.
    r,k=T['r'],T['k']
    s=Seq(b);s.adder(T['add'],EA,OPA,OPB,0)
    checks=compute.or_chunks(T,QK,EA,mbits,32)+compute.or_chunks(T,QK+r,EA,cbits,mbits)
    s.lookups(checks)
    segs=[(OPSEL,4,0)]+([(QK,r+k,4)] if r+k else [])+[(EA,2,4+r+k)]
    s.lookups([(T['class'],4,12,CL,segs,0)])
    g=s.decide(CL,4);H['mem']=s.entry();b.flush()
    def address(seq,row_layer,slot,f_lo,f_hi,wb,inc):
        """Patch a guest word/byte address into one memory operand."""
        p0=seq.layers[-4];p1=seq.layers[-3]
        lo,hi=field(row_layer.cell,slot,f_lo),field(row_layer.cell,slot,f_hi)
        p0.add(copy(mbits-2,lo+6,EA+2));p1.add(copy(mbits-2,hi+6,EA+2))
        if wb<4:p0.add(copy(2,lo+3,EA));p0.add(copy(3,hi+3,HB))
    for op,(wb,signed) in enumerate(((1,1),(1,0),(2,1),(2,0),(4,0))):
        s=Seq(b,g+op*CELL)
        if wb<4:s.lookups([(T['inc1' if wb==1 else 'inc2'],2,3,HB,[(EA,2,0)],0)])
        else:s.rows([])
        s.rows([]);s.rows([]);s.rows([])
        ld=s.rows([(RES,RES+8*wb,MEM,MEM+8*wb)]);address(s,ld,0,2,3,wb,1)
        if wb<4 and not signed:ld.add(copy(32-8*wb,RES+8*wb,ZERO))
        if signed:
            fill=T['fill24' if wb==1 else 'fill16']
            s.lookups([(fill,5,32-8*wb,RES+8*wb,[(RES+8*wb-1,1,0)],0)])
        s.jump(H['xw']);b.flush()
    for op,wb in enumerate((1,2,4)):
        s=Seq(b,g+(5+op)*CELL)
        if wb<4:s.lookups([(T['inc1' if wb==1 else 'inc2'],2,3,HB,[(EA,2,0)],0)])
        else:s.rows([])
        s.rows([]);s.rows([]);s.rows([])
        st=s.rows([(MEM,MEM+8*wb,OPC,OPC+8*wb)]);address(s,st,0,0,1,wb,1)
        g2=s.decide(CL+8,2);b.flush()
        Seq(b,g2).rows([]).next=H['x']
        stub(Seq(b,g2+CELL),STATUS_MODIFIED,[copy(32,PCREG,PCN)]);b.flush()
    s=Seq(b,g+8*CELL)
    s.rows([copy(32,DISCARD,PCN)]);H['jw_row']=field(s.entry(),0,0)
    g2=s.decide(CL+8,2);b.flush()
    s=Seq(b,g2);s.rows([]);s.rows([]);s.rows([])
    t=Seq(b);t.rows([]).next=code_base
    s.layers[0].add(copy(cbits-2,field(t.entry(),7,2)+12,EA+2))
    s.layers[1].add(copy(cbits-2,field(t.entry(),7,3)+12,EA+2))
    s.jump(t.entry());H['tramp']=t.entry()
    target=[copy(31,PCREG+1,EA+1),copy(1,PCREG,ZERO)]
    stub(Seq(b,g2+CELL),4,target);stub(Seq(b,g2+2*CELL),STATUS_UNTRANSLATED,target);b.flush()
    for c,code in ((9,6),(10,7),(11,8),(12,9),(13,5)):stub(Seq(b,g+c*CELL),code);b.flush()
    return H

def signed(v,bits):return v-(1<<bits) if v>>(bits-1)&1 else v

def translate(program,*,memory_bytes=4096,cbits=None,registers=None,entry=0,initial_memory=None):
    """Return (stream bytes, info). program is loaded at guest address 0."""
    mbits=memory_bytes.bit_length()-1
    if memory_bytes!=1<<mbits or not 8<=mbits<=17:raise ValueError('memory must be 2^8..2^17 bytes')
    if cbits is None:cbits=max(4,(max(len(program),4)-1).bit_length())
    if not 4<=cbits<mbits or len(program)>1<<cbits:raise ValueError('translated range must hold the program and stay below memory')
    code_base=max(1<<19,1<<(10+cbits))
    if code_base+(1<<(10+cbits))+4096>D:raise ValueError('code range too large for this layout')
    registers={2:memory_bytes-16} if registers is None else registers
    stream=Stream();b=Builder(stream)
    T=build_tables(Tables(stream),mbits,cbits)
    H=build_handlers(b,T,mbits,cbits,code_base)
    assert b.cell*CELL<=code_base,'handlers exceed their area'
    memory=bytearray(memory_bytes)
    for at,data in (initial_memory or {}).items():memory[at:at+len(data)]=data
    memory[:len(program)]=program
    words=1<<(cbits-2)
    block=lambda pc:code_base+4096*(pc>>2)
    sites=[]
    for w in range(words+1):
        pc=4*w;word=int.from_bytes(memory[pc:pc+4],'little') if w<words else None
        rows,cells,record=site(pc,word,block,H,T,memory_bytes,cbits)
        sites.append(record)
        for slot,(cell_rows,nxt) in cells.items():
            stream.put(block(pc)+slot*CELL,encode(list(cell_rows)+[(0,0,0,0)]*(SLOTS-1-len(cell_rows))+[(0,L,nxt,nxt+L)]))
    state=[registers.get(i,0) if i else 0 for i in range(32)]+[entry,0]
    stream.put(STATE,b''.join(numeric(v,4) for v in state))
    stream.put(KST,b''.join(numeric(v,4) for v in range(16)))
    stream.put(ZERO,bytes(16))
    for w,record in enumerate(sites):stream.put(SITES+SITE*w,record)
    stream.put(MEM,b''.join(numeric(int.from_bytes(memory[4*w:4*w+4],'little'),4)+bytes(4) for w in range(memory_bytes//4)))
    data=stream.finish(block(entry))
    return data,dict(code_base=code_base,cbits=cbits,mbits=mbits,handler_cells=b.cell,words=words,
                     size=S,slots=SLOTS,stream_bytes=len(data))

def site(pc,word,block,H,T,memory_bytes,cbits):
    """Block cells {slot: (rows, next)} and the 256-bit constant record."""
    rec=bytearray(SITE//8)
    def put(off,value,nbytes):rec[off//8:off//8+nbytes]=numeric(value,nbytes)
    me=SITES+SITE*(pc>>2);K=lambda off:me+off
    nxt=block(pc+4)
    def ret(exit_cell,target):
        put(RETLO,target,3);put(RETHI,target+L,3)
        return [copy(24,field(exit_cell,7,2),K(RETLO)),copy(24,field(exit_cell,7,3),K(RETHI))]
    def wb(row_field,rd):
        dst=STATE+32*rd if rd else DISCARD
        put(WBLO,dst,3);put(WBHI,dst+32,3)
        return [copy(24,row_field,K(WBLO)),copy(24,row_field+A,K(WBHI))]
    def stub(code,pcv,extra=()):
        put(K2,pcv,4);put(K3,code,4)
        return {0:(list(extra)+[copy(32,PCREG,K(K2)),copy(32,STATUS,K(K3))],H['halt'])}
    def target_cells(t,rd_rows):
        """Static jump target: link, or a fault/fallback stub."""
        t&=0xffffffff
        if t%4:return None
        if t>=memory_bytes:return stub(4,t,rd_rows)
        if t>=1<<cbits:return stub(STATUS_UNTRANSLATED,t,rd_rows)
        return {0:(rd_rows,block(t))}
    if word is None:
        return None,(stub(4,pc) if pc>=memory_bytes else stub(STATUS_UNTRANSLATED,pc)),bytes(rec)
    op,rd,f3=word&127,word>>7&31,word>>12&7
    rs1,rs2,f7=word>>15&31,word>>20&31,word>>25
    imm=signed(word>>20,12)&0xffffffff
    x=lambda r:STATE+32*r
    illegal=lambda:(None,stub(3,pc),bytes(rec))
    alu={0:'add',4:'xor',6:'or',7:'and',1:'sll',5:'srl'}
    if op in (0x13,0x33):
        immediate=op==0x13
        if f3==0 and not immediate and f7 not in (0,32):return illegal()
        if f3==1 and f7!=0:return illegal()
        if f3==5 and f7 not in (0,32):return illegal()
        if not immediate and f3 not in (0,1,5) and f7!=0:return illegal()
        if rd==0:return None,{0:([],nxt)},bytes(rec)
        name=alu.get(f3)
        if f3==0 and not immediate and f7==32:name='sub'
        if f3==5 and f7==32:name='sra'
        if f3 in (2,3):name='cmp'
        put(K1,imm,4);put(SEL,{'sub':0,'cmp':5}.get(name,0),1)
        same=not immediate and rs1==rs2
        if name=='cmp' and same:return None,{0:([copy(32,x(rd),ZERO)],nxt)},bytes(rec)
        rows=[copy(32,OPA,x(rs1))]
        rows.append(copy(40,OPB,K(K1)) if immediate else copy(32,OPB,x(rs2)))
        if not immediate:rows.append(copy(8,OPSEL,K(SEL)))
        if same:
            # One register cannot be read twice in a tick: duplicate OPA next.
            rows.remove(copy(32,OPB,x(rs2)))
            rows+=ret(H['xw'],nxt)+wb(field(H['xw'],0,0),rd)
            return None,{0:(rows,block(pc)+CELL),1:([copy(32,OPB,OPA)],H[name])},bytes(rec)
        if name=='cmp':
            j=4 if f3==3 else 2
            rows+=ret(H['x'],block(pc)+CELL)
            return None,{0:(rows,H['sub']),1:([copy(1,x(rd),FLAGS+2*j),copy(31,x(rd)+1,ZERO)],nxt)},bytes(rec)
        rows+=ret(H['xw'],nxt)+wb(field(H['xw'],0,0),rd)
        return None,{0:(rows,H[name])},bytes(rec)
    if op in (0x37,0x17):
        value=(word&0xfffff000)+(pc if op==0x17 else 0)
        put(K1,value&0xffffffff,4)
        return None,{0:([copy(32,x(rd),K(K1))] if rd else [],nxt)},bytes(rec)
    if op==0x6f:
        off=(word>>31&1)<<20|(word>>12&255)<<12|(word>>20&1)<<11|(word>>21&1023)<<1
        put(K1,pc+4,4)
        rd_rows=[copy(32,x(rd),K(K1))] if rd else []
        cells=target_cells(pc+signed(off,21),rd_rows)
        return None,(cells if cells else stub(5,pc)),bytes(rec)
    if op==0x67:
        if f3:return illegal()
        put(K1,imm,4);put(SEL,8,1);put(K2,pc,4);put(K3,pc+4,4)
        rows=[copy(32,OPA,x(rs1)),copy(40,OPB,K(K1)),copy(32,PCREG,K(K2)),copy(32,PCN,K(K3))]
        rows+=wb(H['jw_row'],rd)
        return None,{0:(rows,H['mem'])},bytes(rec)
    if op==0x63:
        conds={0:0,1:1,4:2,5:3,6:4,7:5}
        if f3 not in conds:return illegal()
        off=(word>>31&1)<<12|(word>>7&1)<<11|(word>>25&63)<<5|(word>>8&15)<<1
        t=(pc+signed(off,13))&0xffffffff
        if rs1==rs2:
            # Equal operands: the condition is known now.
            if f3 in (0,5,7):return None,(target_cells(t,[]) or stub(5,pc)),bytes(rec)
            return None,{0:([],nxt)},bytes(rec)
        put(SEL,10,1)
        put(FLLO,FLAGS+2*conds[f3],3);put(FLHI,FLAGS+2*conds[f3]+2,3)
        rows=[copy(32,OPA,x(rs1)),copy(32,OPB,x(rs2)),copy(8,OPSEL,K(SEL))]
        rows+=ret(H['bx'],block(pc)+2*CELL)
        rows+=[copy(24,H['flag_row']+2*A,K(FLLO)),copy(24,H['flag_row']+3*A,K(FLHI))]
        taken=target_cells(t,[]) or stub(5,pc)
        return None,{0:(rows,H['sub']),2:([],nxt),3:taken[0]},bytes(rec)
    if op==0x03:
        sel={0:0,4:1,1:2,5:3,2:4}
        if f3 not in sel:return illegal()
        put(K1,imm,4);put(SEL,sel[f3],1);put(K2,pc,4)
        rows=[copy(32,OPA,x(rs1)),copy(40,OPB,K(K1)),copy(32,PCREG,K(K2))]
        rows+=ret(H['xw'],nxt)+wb(field(H['xw'],0,0),rd)
        return None,{0:(rows,H['mem'])},bytes(rec)
    if op==0x23:
        if f3 not in (0,1,2):return illegal()
        off=signed((word>>25)<<5|(word>>7&31),12)&0xffffffff
        put(K1,off,4);put(SEL,5+f3,1);put(K2,pc,4);put(K3,pc+4,4)
        rows=[copy(32,OPA,x(rs1)),copy(40,OPB,K(K1)),copy(32,PCREG,K(K2)),copy(32,PCN,K(K3))]
        rows+=ret(H['x'],nxt)
        if rs1==rs2:return None,{0:(rows,block(pc)+CELL),1:([copy(32,OPC,OPA)],H['mem'])},bytes(rec)
        return None,{0:(rows+[copy(32,OPC,x(rs2))],H['mem'])},bytes(rec)
    if op==0x0f:
        if f3:return illegal()
        return None,{0:([],nxt)},bytes(rec)
    if op==0x73:
        if word==0x73:return None,stub(1,pc),bytes(rec)
        if word==0x100073:return None,stub(2,pc),bytes(rec)
    return illegal()
