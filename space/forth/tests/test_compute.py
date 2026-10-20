"""Guest Forth compute library versus copycode.vm1.compute: identical streams.

One program uses the standard tables, a shared nibble-adder handler called
from two sites (return and result destination patched by each call), SUB,
compare/flags, XOR, three shifts, a flag-selected return, a multiway branch,
a stub and a halt that writes ten results. The guest stream must match the
host model byte for byte; on checked-emulator the results must be right.
"""
import subprocess
from guest_support import run_guest
import dependencies
from copycode.hostpaths import output_dir
from copycode.vm1.backend import Machine,Stream,Builder,copy,numeric
from copycode.vm1 import compute
from copycode.vm1.compute import Seq

SIZE=(1<<24)-16;CELL=1024
m=Machine(SIZE,8,CELL,4096)
D=3<<22;A_=D;B_=D+64;RES=D+128;W=D+192;U=D+256;Z=D+272;FLAGS=D+288;C2=D+304;ZERO=D+320;DISCARD=D+448
OPA=D+512;OPB=D+576;OUT=D+1024;K=D+2048;TAB=D+16384;TABEND=D+(1<<18)
AV,BV=0x89ABCDEF,0x13
MARKS=(0x11111111,0x22222222,0x33333333,0x44444444)

def host():
    st=Stream(m);b=Builder(st)
    T=compute.standard_tables(compute.Tables(st,TAB,TABEND))
    xw,x=compute.exit_layers(b,RES,DISCARD)
    halt=compute.halt(b,[(320,OUT)]);b.flush()
    s=Seq(b);s.adder(T['add'],RES,OPA,OPB,0);s.jump(xw);add=s.entry();b.flush()
    s=Seq(b);s.rows([]);row,bx=compute.flag_exit(s,C2,FLAGS);br=s.entry();b.flush()
    s=Seq(b)
    m1=s.layer()
    for r in [copy(32,OPA,A_),copy(32,OPB,B_)]+compute.call_rows(m,xw,K,K+24)+[copy(24,m.field(xw,0,0),K+48),copy(24,m.field(xw,0,1),K+72)]:m1.add(r)
    m2=s.layer();m1.next=add
    for r in [copy(32,OPA,OUT),copy(32,OPB,B_)]+compute.call_rows(m,xw,K+96,K+120)+[copy(24,m.field(xw,0,0),K+144),copy(24,m.field(xw,0,1),K+168)]:m2.add(r)
    m3=s.layer();m2.next=add
    s.adder(T['sub'],RES,A_,B_,1);s.rows([copy(32,OUT+64,RES)])
    compute.compare(s,T,RES,A_,B_,Z,FLAGS);s.rows([copy(12,OUT+96,FLAGS)])
    compute.logic(s,T['xor'],RES,A_,B_);s.rows([copy(32,OUT+128,RES)])
    compute.shift_right(s,T,RES,A_,B_,W,ZERO,False);s.rows([copy(32,OUT+160,RES)])
    compute.shift_right(s,T,RES,A_,B_,W,ZERO,True);s.rows([copy(32,OUT+192,RES)])
    compute.shift_left(s,T,RES,A_,B_,W,ZERO,U);s.rows([copy(32,OUT+224,RES)])
    g2=b.group(1)
    call=s.layer()
    for r in [copy(24,row+2*m.a,K+192),copy(24,row+3*m.a,K+216)]+compute.call_rows(m,bx,K+240,K+264):call.add(r)
    call.next=br;main=s.entry();b.flush()
    s=Seq(b);s.rows([]);g=s.decide(FLAGS+8,1);dec=s.entry();b.flush()
    Seq(b,g).rows([copy(32,OUT+288,K+352)]).next=halt
    compute.stub(Seq(b,g+CELL),OUT+288,K+384,halt);b.flush()
    Seq(b,g2).rows([copy(32,OUT+256,K+288)]).next=dec
    Seq(b,g2+CELL).rows([copy(32,OUT+256,K+320)]).next=dec;b.flush()
    st.put(A_,numeric(AV,4));st.put(B_,numeric(BV,4))
    L=m.layer_bits
    fields=[m2.cell,m2.cell+L,OUT,OUT+32,m3.cell,m3.cell+L,OUT+32,OUT+64,FLAGS+10,FLAGS+12,g2,g2+L]
    st.put(K,b''.join(numeric(v,3) for v in fields))
    st.put(K+288,b''.join(numeric(v,4) for v in MARKS))
    return st.finish(main),fields

def expected_results():
    a,b=AV,BV;sh=b&31;M=0xffffffff
    s=lambda v:v-(1<<32) if v>>31 else v
    r0=(a+b)&M;r1=(r0+b)&M;r2=(a-b)&M
    eq,lt,ltu=a==b,s(a)<s(b),a<b
    flags=sum(int(v)*3<<2*j for j,v in enumerate([eq,not eq,lt,not lt,ltu,not ltu]))
    sra=(s(a)>>sh)&M
    geu=not ltu
    return [r0,r1,r2,flags,a^b,a>>sh,sra,(a<<sh)&M,MARKS[1] if geu else MARKS[0],MARKS[3] if ltu else MARKS[2]]

stream,fields=host()
c=lambda v:str(v)
lines=['variable tl variable xw variable x variable halt variable add variable br variable row variable bx',
       'variable m2c variable m3c variable m1 variable m2 variable m3 variable g2 variable call variable main variable g variable dec',
       'create kbuf 64 allot create marks 16 allot',
       ': r ( row -- ) tl @ cc-row drop ;',': nl ( -- ) cc-layer tl ! ;',
       ': handlers',
       f'  {SIZE} 8 {CELL} 4096 cc-machine 2 cc-builder {TAB} {TABEND} cc-tables cc-standard-tables',
       f'  {RES} {DISCARD} 32 cc-exit-layers x ! xw !',
       f'  cc-halt-begin 320 {OUT} cc-halt-region cc-halt-end halt ! cc-flush',
       f'  -1 cc-seq cc-t-add @ {RES} {OPA} {OPB} 0 cc-adder xw @ cc-jump cc-entry add ! cc-flush',
       f'  -1 cc-seq cc-layer drop {C2} {FLAGS} cc-flag-exit bx ! row ! cc-entry br ! cc-flush ;',
       ': calls',
       f'  -1 cc-seq cc-layer dup m1 ! tl ! 32 {OPA} {A_} cc-copy r 32 {OPB} {B_} cc-copy r',
       f'  xw @ {K} {K+24} m1 @ cc-call-rows',
       f'  24 xw @ 0 0 cc-field {K+48} cc-copy r 24 xw @ 0 1 cc-field {K+72} cc-copy r',
       f'  cc-layer dup m2 ! dup cc-layer-cell m2c ! tl ! add @ m1 @ cc-next! 32 {OPA} {OUT} cc-copy r 32 {OPB} {B_} cc-copy r',
       f'  xw @ {K+96} {K+120} m2 @ cc-call-rows',
       f'  24 xw @ 0 0 cc-field {K+144} cc-copy r 24 xw @ 0 1 cc-field {K+168} cc-copy r',
       '  cc-layer dup m3 ! cc-layer-cell m3c ! add @ m2 @ cc-next! ;',
       ': work',
       f'  cc-t-sub @ {RES} {A_} {B_} 1 cc-adder nl 32 {OUT+64} {RES} cc-copy r',
       f'  {RES} {A_} {B_} {Z} {FLAGS} cc-compare nl 12 {OUT+96} {FLAGS} cc-copy r',
       f'  cc-t-xor @ {RES} {A_} {B_} cc-logic nl 32 {OUT+128} {RES} cc-copy r',
       f'  {RES} {A_} {B_} {W} {ZERO} 0 cc-shift-right nl 32 {OUT+160} {RES} cc-copy r',
       f'  {RES} {A_} {B_} {W} {ZERO} -1 cc-shift-right nl 32 {OUT+192} {RES} cc-copy r',
       f'  {RES} {A_} {B_} {W} {ZERO} {U} cc-shift-left nl 32 {OUT+224} {RES} cc-copy r',
       f'  1 cc-group g2 ! nl tl @ call ! 24 row @ {2*m.a} + {K+192} cc-copy r 24 row @ {3*m.a} + {K+216} cc-copy r',
       f'  bx @ {K+240} {K+264} call @ cc-call-rows br @ call @ cc-next! cc-entry main ! cc-flush ;',
       ': branches',
       f'  -1 cc-seq cc-layer drop {FLAGS+8} 1 cc-decide g ! cc-entry dec ! cc-flush',
       f'  g @ cc-seq nl 32 {OUT+288} {K+352} cc-copy r halt @ tl @ cc-next!',
       f'  g @ {CELL} + cc-seq {OUT+288} {K+384} halt @ cc-stub cc-flush',
       f'  g2 @ cc-seq nl 32 {OUT+256} {K+288} cc-copy r dec @ tl @ cc-next!',
       f'  g2 @ {CELL} + cc-seq nl 32 {OUT+256} {K+320} cc-copy r dec @ tl @ cc-next! cc-flush ;',
       ]
# Field constants depend on cells known only in the guest: store them there.
lines+=[': kput ( value i -- ) 3 * kbuf + 3 swap cc-numeric ;',
        ': data',
        f'  {AV} 4 {A_} cc-put-numeric {BV} 4 {B_} cc-put-numeric',
        '  m2c @ dup 0 kput cc-layer-bits + 1 kput',
        f'  {OUT} 2 kput {OUT+32} 3 kput m3c @ dup 4 kput cc-layer-bits + 5 kput',
        f'  {OUT+32} 6 kput {OUT+64} 7 kput {FLAGS+10} 8 kput {FLAGS+12} 9 kput',
        '  g2 @ 10 kput g2 @ cc-layer-bits + 11 kput',
        f'  {K} kbuf 36 cc-put',
        '  4 0 do i 1+ 286331153 * 4 marks i 4 * + cc-numeric loop',
        f'  {K+288} marks 16 cc-put main @ cc-finish ;',
        'handlers calls work branches data','bye']
run_guest('compute',['backend.fth','compute.fth'],lines,stream+b'\n',timeout=1400)
checked=output_dir(dependencies.VM2_ROOT,'build')/'checked-emulator'
result=subprocess.run([str(checked),'-s',str(SIZE),'-p','8'],input=stream,capture_output=True,timeout=300)
assert result.returncode==0,(result.returncode,result.stderr[-500:])
from copycode.vm1.machine import field as get
got=[get(result.stdout,32*k,32) for k in range(10)]
assert got==expected_results(),(got,expected_results())
print('PASS guest compute library:',len(stream),'stream bytes match the host model; results',
      [hex(v) for v in got],flush=True)
