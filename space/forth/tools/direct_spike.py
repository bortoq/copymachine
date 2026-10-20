"""Spike 9.5.1: compile a few Forth primitives straight into emulator index code.

Host model only (copycode.vm1.compute); the question is the cost in emulator
ticks, which does not depend on the language of the generator. Two variants:

  static  the compiler tracks stack depth; stack cells are fixed registers,
          so DUP/DROP are copies or nothing, + is one adder, @/! patch only
          the memory address.
  memory  the data stack lives in memory; every access patches the address
          from the stack pointer, which is updated by table lookups.

Memory words (and memory stack cells) sit at a 64-bit stride, so a patched
word address never carries into the bits of the upper endpoint. Loop control
uses fixed index/limit registers in both variants. No range or alignment
checks are generated: costs are a lower bound for checked code.
"""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/pforth'))
from common import RV32I_ROOT
import dependencies
from copycode.hostpaths import output_dir
from copycode.vm1.backend import Machine,Stream,Builder,copy,numeric
from copycode.vm1 import compute
from copycode.vm1.compute import Seq

SIZE=(1<<24)-16;CELL=1024
M=Machine(SIZE,8,CELL,4096)
D=3<<22
REG=D                     # static stack registers at a 64-bit stride
TMP=D+2048;IDX=D+2112;LIM=D+2176;ONE=D+2240;XR=D+2304;Z=D+2368;E=D+2376
SP=D+2400;T1=D+2416;T2=D+2432  # memory variant: index, copy (8+8 bits each)
VA=D+2496;VB=D+2560;ZERO=D+2624;OUT=D+3072;K=D+4096;TAB=D+16384
STK=D+(1<<19);MEM=D+(1<<20)
MW=10                     # memory words (1024 words = 4 KiB)

class Compiler:
    def __init__(self,variant):
        self.variant=variant;self.st=Stream(M);self.b=Builder(self.st)
        t=compute.Tables(self.st,TAB,STK);self.T=compute.standard_tables(t)
        self.T['inc8']=t.table(8,5,[((i+1)&255)*257 for i in range(256)])
        self.T['dec8']=t.table(8,5,[((i-1)&255)*257 for i in range(256)])
        self.T['nz2']=t.table(4,2,[3 if i else 0 for i in range(16)])
        self.consts={};self.depth=0;self.s=None
    def const(self,v):
        if v not in self.consts:self.consts[v]=K+32*len(self.consts)
        return self.consts[v]
    def reg(self,d):return REG+64*d
    # --- patterns ---------------------------------------------------------
    def sliced(self,row,fields,src,n,off,dup=None):
        """Row whose two endpoint fields get src[0:n] at bit off; returns layer."""
        s=self.s;p0=s.layer();p1=p0 if dup is not None else s.layer();s.layer();r=s.layer()
        slot=r.add(row)
        p0.add(copy(n,M.field(r.cell,slot,fields[0])+off,src))
        p1.add(copy(n,M.field(r.cell,slot,fields[1])+off,dup if dup is not None else src))
        return r
    def load(self,dst,addr):
        self.sliced((dst,dst+32,MEM,MEM+32),(2,3),addr+2,MW,6)
    def store(self,addr,src):
        self.sliced((MEM,MEM+32,src,src+32),(0,1),addr+2,MW,6)
    def stack_read(self,dst,index):
        self.sliced((dst,dst+32,STK,STK+32),(2,3),index,8,6,dup=index+8)
    def stack_write(self,index,src):
        self.sliced((STK,STK+32,src,src+32),(0,1),index,8,6,dup=index+8)
    def move_sp(self,table):
        self.s.lookups([(self.T[table],5,16,r,[(r,8,0)],0) for r in (SP,T1,T2)])
    def add(self,dst,a,b):
        self.s.adder(self.T['add'],TMP,a,b,0);self.s.rows([copy(32,dst,TMP)])
    # --- primitives ------------------------------------------------------
    def op(self,name,*arg):
        s=self.s
        if self.variant=='static':
            d=self.depth
            if name=='lit':s.rows([copy(32,self.reg(d),self.const(arg[0]))]);self.depth+=1
            elif name=='dup':s.rows([copy(32,self.reg(d),self.reg(d-1))]);self.depth+=1
            elif name=='drop':self.depth-=1
            elif name=='+':self.add(self.reg(d-2),self.reg(d-2),self.reg(d-1));self.depth-=1
            elif name=='@':self.load(self.reg(d-1),self.reg(d-1))
            elif name=='!':self.store(self.reg(d-1),self.reg(d-2));self.depth-=2
            return
        if name=='lit':self.stack_write(SP,self.const(arg[0]));self.move_sp('inc8')
        elif name=='dup':self.stack_read(VA,T1);self.stack_write(SP,VA);self.move_sp('inc8')
        elif name=='drop':self.move_sp('dec8')
        elif name=='+':
            self.stack_read(VB,T1);self.stack_read(VA,T2);self.add(VA,VA,VB);self.stack_write(T2,VA);self.move_sp('dec8')
        elif name=='@':self.stack_read(VA,T1);self.load(VB,VA);self.stack_write(T1,VB)
        elif name=='!':
            self.stack_read(VA,T1);self.stack_read(VB,T2);self.store(VA,VB);self.move_sp('dec8');self.move_sp('dec8')
    def loop(self,count,body):
        """count iterations of body, index and limit in fixed registers."""
        s=self.s;s.rows([copy(32,IDX,self.const(0)),copy(32,LIM,self.const(count))])
        start=s.layer()
        for item in body:self.op(*item)
        s.adder(self.T['add'],TMP,IDX,ONE,0);s.rows([copy(32,IDX,TMP)])
        compute.logic(s,self.T['xor'],XR,IDX,LIM)
        s.lookups(compute.or_chunks(self.T,Z,XR,0,32))
        s.lookups([(self.T['nz2'],2,2,E,[(Z,4,0)],0)])
        g=s.decide(E,1)
        self.b.flush()
        Seq(self.b,g+CELL).rows([]).next=start.cell
        self.s=Seq(self.b,g)
    def compile(self,program):
        """program: ops; ('loop', n, [ops]) repeats ops n times."""
        self.halt=compute.halt(self.b,[(32*8,OUT)]);self.b.flush()
        self.s=Seq(self.b);entry=None
        self.s.layer();entry=self.s.entry()
        for item in program:
            if item[0]=='loop':self.loop(item[1],item[2])
            else:self.op(*item)
        # Results: static stack registers, or the memory stack, and memory word 16.
        s=self.s
        if self.variant=='static':
            s.rows([copy(32,OUT+32*k,self.reg(k)) for k in range(min(self.depth,6))])
        else:
            s.rows([copy(32,OUT+32*k,STK+64*k) for k in range(6)])
        s.rows([copy(32,OUT+224,MEM+64*16)])
        s.jump(self.halt);self.b.flush()
        st=self.st
        st.put(ONE,numeric(1,4))
        if self.variant=='memory':st.put(SP,numeric(0,2)+numeric(255*257,2)+numeric(254*257,2))
        for v,at in self.consts.items():st.put(at,numeric(v&0xffffffff,4))
        st.put(MEM+64*16,numeric(5,4))
        return st.finish(entry)

def run(stream):
    checked=output_dir(dependencies.VM2_ROOT,'build')/'checked-emulator'
    r=subprocess.run([str(checked),'-s',str(SIZE),'-p','8'],input=stream,capture_output=True,timeout=600)
    assert r.returncode==0,r.stderr[-500:]
    from copycode.vm1.machine import field
    return [field(r.stdout,32*k,32) for k in range(8)],int(r.stderr.split(b'VM1_AUDIT_TICKS=')[1].split()[0])

X=64  # Forth address of memory word 16
def measure(variant):
    def ticks(program):return run(Compiler(variant).compile(program))
    base_out,base=ticks([('lit',1)])
    rows={}
    for name,unit in [('lit',[('lit',7)]),('dup',[('dup',)]),('drop',[('lit',7),('drop',)]),
                      ('+',[('lit',7),('+',)]),('@',[('lit',X),('@',),('drop',)]),('!',[('lit',9),('lit',X),('!',)])]:
        reps=8
        _,t=ticks([('lit',1)]+unit*reps)
        rows[name]=(t-base)/reps
    # Composite units are corrected by the measured lit/drop costs.
    rows['drop']-=rows['lit'];rows['+']-=rows['lit'];rows['@']-=rows['lit']+rows['drop'];rows['!']-=2*rows['lit']
    body=[('lit',X),('@',),('+',),('lit',X),('@',),('lit',1),('+',),('lit',X),('!',)]
    out,t10=ticks([('lit',0),('loop',10,body)])
    _,t1=ticks([('lit',0),('loop',1,body)])
    _,e10=ticks([('lit',0),('loop',10,[])]);_,e1=ticks([('lit',0),('loop',1,[])])
    rows['loop iteration']=(e10-e1)/9
    rows['sample iteration']=(t10-t1)/9
    assert out[0]==sum(range(5,15)) and out[7]==15,(variant,out)
    return rows

def pforth_reference():
    """Ticks per iteration of the same work in pForth on the universal RV32I."""
    image=output_dir(ROOT)/'initialized';observer=output_dir(ROOT)/'observe-emulator'
    mapping=json.loads((image/'map.json').read_text());reg=mapping['regions']['registers']['at']
    def ticks(task):
        env=dict(os.environ,EMULATOR=str(observer),PFORTH_REG_BITS=str(reg))
        r=subprocess.run([str(ROOT/'pforth'),'run',str(image)],input=task.encode(),capture_output=True,env=env,timeout=900)
        return int(r.stderr.split(b'stop ticks=')[1].split()[0])
    out={}
    for name,body in [('loop iteration',''),('sample iteration','x @ + x @ 1 + x !')]:
        a=ticks(f'variable x 5 x ! : t 0 101 1 do {body} loop drop ; t bye\n')
        b=ticks(f'variable x 5 x ! : t 0 11 1 do {body} loop drop ; t bye\n')
        out[name]=(a-b)/90
    return out

if __name__=='__main__':
    result={}
    for variant in ('static','memory'):
        start=time.monotonic();result[variant]=measure(variant);result[variant+'_seconds']=round(time.monotonic()-start,1)
        print(variant,{k:round(v,1) for k,v in result[variant].items()},flush=True)
    result['pforth_rv32i']=pforth_reference()
    print('pforth on RV32I',{k:round(v) for k,v in result['pforth_rv32i'].items()},flush=True)
    target=ROOT/'doc/measurements/direct-spike/result.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=1)+'\n');print('wrote',target)
