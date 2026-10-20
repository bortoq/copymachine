"""Translated RV32I images versus the independent reference, audited per tick.

Every case is translated by modules/translate.py, executed on checked-emulator
(all operands of every tick are verified) and compared with rv32i_reference:
final registers, PC, status and the whole guest memory. A stop at an
untranslated target (11) or after a store into translated code (12) must hold
exactly the reference state at that point; the case then resumes on the
universal RV32I image from the dumped state and must finish like the reference.
"""
import json,os,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
import dependencies
import translate as T
from rv32i_reference import execute
from copycode.vm1.machine import field
from copycode.hostpaths import output_dir
from direct_target import compile_image
from vm2compile.artifact import load,save,seal

CHECKED=Path(os.environ.get('CHECKED_EMULATOR',output_dir(dependencies.VM2_ROOT,'build')/'checked-emulator'))
MEM=4096
def i(f=0,rd=3,rs=1,imm=0,op=0x13):return ((imm&4095)<<20)|(rs<<15)|(f<<12)|(rd<<7)|op
def r(f=0,rd=3,a=1,b=2,hi=0):return (hi<<25)|(b<<20)|(a<<15)|(f<<12)|(rd<<7)|0x33
def s(f=2,a=1,b=2,imm=0):return ((imm&4095)>>5<<25)|(b<<20)|(a<<15)|(f<<12)|((imm&31)<<7)|0x23
def branch(f=0,a=1,b=2,off=8):return ((off>>12&1)<<31)|((off>>5&63)<<25)|(b<<20)|(a<<15)|(f<<12)|((off>>1&15)<<8)|((off>>11&1)<<7)|0x63
def jal(rd=1,off=8):return ((off>>20&1)<<31)|((off>>1&1023)<<21)|((off>>11&1)<<20)|((off>>12&255)<<12)|(rd<<7)|0x6f
EBREAK=0x100073
results=[];coverage=set()

def run_translated(stream):
    result=subprocess.run([str(CHECKED),'-s',str(T.S),'-p',str(T.SLOTS)],input=stream,capture_output=True,timeout=600)
    assert result.returncode==0,(result.returncode,result.stderr[-2000:])
    out=result.stdout;assert len(out)==136+2*MEM,len(out)
    state=[field(out,32*k,32) for k in range(34)]
    memory=b''.join(field(out[136:],64*w,32).to_bytes(4,'little') for w in range(MEM//4))
    return state,memory,int(result.stderr.split(b'VM1_AUDIT_TICKS=')[1].split()[0])

def reference(program,registers,entry=0,initial=None):
    regs=dict(registers);pc=entry
    frames,memory,_=execute(program,regs,entry=entry,initial_memory=initial,max_steps=200000,
                            coverage=coverage,memory_bytes=MEM)
    return frames[-1],memory

def universal(state,memory):
    """Resume a dumped state on the universal RV32I image (no translation)."""
    template=output_dir(ROOT,'build')/'translate-universal'
    if not (template/'manifest.json').exists():
        payload,manifest=compile_image();save(template,payload,manifest)
    payload,manifest=load(template);mapping=json.loads(payload['map.json'])
    reg=mapping['regions']['registers']['at'];mem=mapping['regions']['guest']['at']
    image=bytearray(payload['image.bin'])
    def put(at,width,value):
        for k in range(width):
            mask=128>>((at+k)%8);image[(at+k)//8]=(image[(at+k)//8]&~mask)|(mask if value>>k&1 else 0)
    for k in range(34):put(reg+32*k,32,state[k] if k<33 else 0)
    image[mem//8:mem//8+65536]=bytes(65536);image[mem//8:mem//8+MEM]=memory
    sealed,m=seal(image,manifest,mapping)
    result=subprocess.run(['sh','-c','exec "$1" -s "$2" -p "$3" 4>"$4"','u',str(CHECKED),str(m['vm1']['size']),
                           str(m['vm1']['slots']),'/dev/stdout'],input=sealed['boot.bin'],capture_output=True,timeout=600)
    assert result.returncode==0,result.stderr[-1000:]
    raw=result.stdout[-len(image):]
    return [field(raw,reg+32*k,32) for k in range(34)],raw[mem//8:mem//8+MEM]

def case(name,words,registers=None,*,initial=None,entry=0,program=None,expect=None,cbits=None):
    program=program if program is not None else b''.join(w.to_bytes(4,'little') for w in words)
    registers={2:MEM-16} if registers is None else registers
    start=time.monotonic()
    stream,info=T.translate(program,memory_bytes=MEM,registers=registers,entry=entry,initial_memory=initial,cbits=cbits)
    generated=time.monotonic()-start
    state,memory,ticks=run_translated(stream)
    final,ref_memory=reference(program,registers,entry,initial)
    if state[33] in (T.STATUS_UNTRANSLATED,T.STATUS_MODIFIED):
        # Fallback: resuming the reference from the dumped state must reach
        # exactly the final state of an uninterrupted reference run.
        regs={k:v for k,v in enumerate(state[:32]) if k}
        resumed,resumed_memory=reference(b"",regs,state[32],{0:memory})
        assert resumed==final and resumed_memory==ref_memory,(name,'fallback state',state,final)
        if name.endswith('universal'):
            u_state,u_memory=universal(state,memory)
            assert u_state[:33]==final[:33] and u_state[33]==final[33] and u_memory==ref_memory,(name,'universal resume',u_state,final)
    else:
        assert state==final,(name,{k:(a,b) for k,(a,b) in enumerate(zip(state,final)) if a!=b})
        assert memory==ref_memory,(name,'memory',[k for k in range(MEM) if memory[k]!=ref_memory[k]][:8])
    if expect is not None:assert state[33]==expect,(name,state[33],expect)
    results.append(dict(name=name,status=state[33],ticks=ticks,generate_seconds=round(generated,3),
                        stream_bytes=len(stream),handler_cells=info['handler_cells'],cbits=info['cbits']))
    print('PASS translated',name,'status',state[33],'ticks',ticks,flush=True)

rng=random.Random(71021)
for f in range(8):
    for a,b in [(0xffffffff,1),(0x80000000,31),(rng.getrandbits(32),rng.getrandbits(32))]:
        case('register-'+str(f)+'-'+str(a),[r(f),EBREAK],{1:a,2:b})
for f in (0,2,3,4,6,7):case('immediate-'+str(f),[i(f,imm=-17),EBREAK],{1:0x80000007})
for f,hi in [(0,32),(5,32)]:case('subtract-arithmetic-shift-'+str(f),[r(f,hi=hi),EBREAK],{1:0x80000000,2:31})
for f in (1,5):
    for shift in (0,1,31):case('shift-'+str(f)+'-'+str(shift),[i(f,imm=shift),EBREAK],{1:0x87654321})
for amount in (0,1,13,31,32+5):
    case('register-shifts-'+str(amount),[r(1),r(5,rd=4),r(5,rd=5,hi=32),EBREAK],{1:0x87654321,2:amount})
case('srai',[i(5,imm=0x41f),EBREAK],{1:0x80000000})
case('lui-auipc',[0x123451b7,0x12345217,EBREAK])
case('x0-and-alias',[i(rd=0,imm=17),r(rd=1),i(rd=1,imm=-1),r(rd=0),EBREAK],{1:8,2:11})
for f in (0,1,4,5,6,7):
    for a,b in [(7,7),(7,8),(-1&0xffffffff,1),(1,-1&0xffffffff)]:
        case('branch-'+str(f)+'-'+str(a)+'-'+str(b),[branch(f),i(imm=15),EBREAK],{1:a,2:b})
case('jal',[0x008001ef,i(imm=1),EBREAK])
case('jalr',[i(rd=3,rs=1,imm=1,op=0x67),i(imm=2),EBREAK],{1:8})
case('jalr-same-register',[i(rd=1,rs=1,imm=8,op=0x67),EBREAK,EBREAK,EBREAK],{1:0})
for f in (0,1,2,4,5):
    for at in (512,513,514,515):
        if at%(1<<(f&3)):continue
        case('load-'+str(f)+'-'+str(at),[i(f,op=3),EBREAK],{1:at},initial={512:b'\x81\x82\x83\xf4'})
for f in (0,1,2):
    for at in (512,513,514,515):
        if at%(1<<f):continue
        case('store-'+str(f)+'-'+str(at),[s(f),EBREAK],{1:at,2:0xABCDEF81})
for name,word in [('add-same',r(0,3,1,1)),('sub-same',r(0,3,1,1,32)),('sll-same',r(1,3,1,1)),('slt-same',r(2,3,1,1)),
                  ('sltu-same',r(3,3,1,1)),('store-same',s(2,1,1,imm=-4))]:
    case(name,[word,EBREAK],{1:520})
for f in (0,1,4,5,6,7):case('branch-same-'+str(f),[branch(f,1,1),i(imm=15),EBREAK],{1:5})
case('load-negative-offset',[i(2,imm=-4,op=3),EBREAK],{1:520},initial={516:b'\x11\x22\x33\x44'})
case('store-offset',[s(2,imm=-12),i(2,rd=4,rs=1,imm=-12,op=3),EBREAK],{1:600,2:0x89abcdef})
for name,word,regs,status in [('illegal',0xffffffff,{},3),('mul-rejected',r(hi=1),{},3),('bad-shift',i(1,imm=0x401),{},3),
        ('load-align',i(2,op=3),{1:513},7),('load-access',i(2,op=3),{1:65536},6),('load-access-negative',i(0,op=3),{1:0xffffffff},6),
        ('store-align',s(),{1:514},9),('store-access',s(),{1:65536},8),('jump-align',i(op=0x67),{1:2},5),
        ('jalr-outside-memory',i(op=0x67),{1:MEM},4),('ecall',0x73,{},1),('bad-system',0x200073,{},3),
        ('bad-load',i(3,op=3),{},3),('bad-store',s(3),{},3),('bad-branch',branch(2),{},3),('bad-jalr',i(1,op=0x67),{},3),
        ('bad-fence',0x100f,{},3)]:
    case(name,[word,EBREAK],regs,expect=status)
case('fence',[0x0f,EBREAK])
case('jal-misaligned',[jal(off=6),EBREAK],expect=5)
case('jal-outside-memory',[jal(off=-8),EBREAK],expect=4)
case('branch-misaligned',[branch(0,1,1,off=6),EBREAK],expect=5)
case('branch-misaligned-not-taken',[branch(1,1,1,off=6),EBREAK],expect=2)
case('fall-through',[i(imm=1)]*4,cbits=4,expect=T.STATUS_UNTRANSLATED)
case('jalr-untranslated',[i(rd=1,rs=0,imm=1024,op=0x67)]+[EBREAK]*3,expect=T.STATUS_UNTRANSLATED)
case('jal-untranslated-universal',[jal(off=1024)]+[EBREAK]*3,expect=T.STATUS_UNTRANSLATED)
case('code-store-universal',[s(2,a=0,b=2,imm=8),i(imm=1),0xffffffff,EBREAK],{2:0x00100073},expect=T.STATUS_MODIFIED)
case('data-store-code-range',[s(2,a=0,b=2,imm=12),EBREAK,0,0],{2:5},expect=T.STATUS_MODIFIED)
# A loop: sum 1..10 with a counted branch and a memory accumulator.
loop=[i(rd=5,rs=0,imm=10),i(rd=6,rs=0,imm=0),r(0,6,6,5),i(rd=5,rs=5,imm=-1),branch(1,5,0,off=-8),
      s(2,a=0,b=6,imm=1024),i(2,rd=7,rs=0,imm=1024,op=3),EBREAK]
case('loop',loop)
# A call and return through JALR, with stack traffic.
call=[i(rd=2,rs=2,imm=-16),s(2,a=2,b=1,imm=12),jal(rd=1,off=20),s(2,a=0,b=10,imm=1028),i(2,rd=1,rs=2,imm=12,op=3),
      i(rd=2,rs=2,imm=16),EBREAK,i(rd=10,rs=0,imm=99),i(rd=0,rs=1,imm=0,op=0x67)]
case('call-return',call[:7]+call[7:])
rng=random.Random(9511)
for n in range(6):
    words=[]
    for _ in range(12):
        kind=rng.randrange(4)
        rd,a,b=rng.randrange(1,8),rng.randrange(8),rng.randrange(8)
        if kind==0:words.append(r(rng.choice([0,1,2,3,4,5,6,7]),rd,a,b,rng.choice([0,0,32]) if True else 0))
        elif kind==1:words.append(i(rng.choice([0,2,3,4,6,7]),rd,a,rng.randrange(-2048,2048)))
        elif kind==2:words.append(i(rng.choice([1,5]),rd,a,rng.randrange(32)|(rng.choice([0,0x400]) if True else 0)))
        else:words.append(rng.getrandbits(20)<<12|rd<<7|rng.choice([0x37,0x17]))
    words=[w if not (w&127==0x33 and (w>>25)==32 and (w>>12&7) not in (0,5)) else w&~(32<<25) for w in words]
    words=[w if not (w&127==0x13 and (w>>12&7)==1) else w&~(0x7f<<25) for w in words]
    case('random-'+str(n),words+[EBREAK],{k:rng.getrandbits(32) for k in range(1,8)})
out=output_dir(ROOT,'build')/'verification';out.mkdir(parents=True,exist_ok=True)
(out/'translate.json').write_text(json.dumps(results,indent=2)+'\n')
print('ALL',len(results),'translated RV32I cases passed; coverage',sorted(coverage),flush=True)
