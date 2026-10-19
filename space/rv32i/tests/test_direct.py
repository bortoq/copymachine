"""Independent RV32I oracle versus audited execution of the stored emulator image."""
import hashlib,json,os,random,re,subprocess,sys,tempfile,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
import dependencies
from direct_target import compile_image
from cli import compile_c
from vm2compile.artifact import build,seal,load,save,resume
from rv32i_reference import execute

def get(data,at,width):return sum(((data[(at+k)//8]>>(7-(at+k)%8))&1)<<k for k in range(width))
def put(data,at,width,value):
    for k in range(width):
        mask=128>>((at+k)%8);data[(at+k)//8]=(data[(at+k)//8]&~mask)|(mask if value>>k&1 else 0)
def i(f=0,rd=3,rs=1,imm=0,op=0x13):return ((imm&4095)<<20)|(rs<<15)|(f<<12)|(rd<<7)|op
def r(f=0,rd=3,a=1,b=2,hi=0):return (hi<<25)|(b<<20)|(a<<15)|(f<<12)|(rd<<7)|0x33
def s(f=2,a=1,b=2,imm=0):return ((imm&4095)>>5<<25)|(b<<20)|(a<<15)|(f<<12)|((imm&31)<<7)|0x23
def branch(f=0,a=1,b=2,off=8):return ((off>>12&1)<<31)|((off>>5&63)<<25)|(b<<20)|(a<<15)|(f<<12)|((off>>1&15)<<8)|((off>>11&1)<<7)|0x63
EBREAK=0x100073
coverage=set();results=[]
from copycode.hostpaths import output_dir

template=output_dir(ROOT, 'build')/'template'
if template.exists():shutil.rmtree(template)
if not template.exists():
    start=time.monotonic();a,m=compile_image(frames=True);save(template,a,m)
    print('Compiled universal image in',round(time.monotonic()-start,3),'seconds',flush=True)
BASE,M=load(template);MAP=json.loads(BASE['map.json']);REG=MAP['regions']['registers']['at'];MEM=MAP['regions']['guest']['at']
CHECKED=Path(os.environ.get('CHECKED_EMULATOR',output_dir(dependencies.VM2_ROOT, 'build')/'checked-emulator'))
EMULATOR=Path(os.environ.get('EMULATOR',output_dir(dependencies.EMULATOR_ROOT, 'build')/'bitcopy/emulator'))

def run_case(name,words,registers=None,*,data=b'',initial=None,io_options=None,raw_program=None,binary=CHECKED):
    program=raw_program if raw_program is not None else b''.join(w.to_bytes(4,'little') for w in words)
    registers={2:65520} if registers is None else registers
    io=dict(io_options or {},input=data)
    frames,memory,fetches=execute(program,registers,initial_memory=initial,coverage=coverage,io=io)
    image=bytearray(BASE['image.bin']);image[REG//8:REG//8+512]=bytes(512)
    for reg,value in registers.items():
        if reg:put(image,REG+32*reg,32,value)
    image[MEM//8:MEM//8+65536]=bytes(65536)
    for at,chunk in (initial or {}).items():image[MEM//8+at:MEM//8+at+len(chunk)]=chunk
    image[MEM//8:MEM//8+len(program)]=program
    a,m=seal(image,M,MAP)
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder);snapshot=folder/'snapshot'
        command=['sh','-c','exec "$1" -s "$2" -p "$3" 4>"$4"','rv32i-test',str(binary),str(m['vm1']['size']),str(m['vm1']['slots']),str(snapshot)]
        with open('/dev/full','wb') as sink:
            start=time.monotonic();result=subprocess.run(command,input=a['boot.bin']+data,
                stdout=sink if io.get('write_error') else subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        assert result.returncode==0,(name,result.returncode,result.stderr[-1500:])
        observed= None if io.get('write_error') else result.stdout
        assert observed is None or observed==io['output'],(name,'stdout',observed,io['output'])
        raw=snapshot.read_bytes();assert len(raw)==len(image),(name,'snapshot',len(raw))
        actual=[get(raw,REG+k*32,32) for k in range(34)]
        assert actual==frames[-1],(name,{k:(want,got) for k,(want,got) in enumerate(zip(frames[-1],actual)) if want!=got})
        assert raw[MEM//8:MEM//8+65536]==memory,(name,'guest memory')
        debug=re.sub(rb'VM1_AUDIT_TICKS=\d+\n$',b'',result.stderr)
        observed_frames=[[get(debug,offset*8+k*32,32) for k in range(34)] for offset in range(0,len(debug),136)]
        assert observed_frames==frames,(name,'committed/final state frames',len(observed_frames),len(frames))
        ticks=re.search(rb'VM1_AUDIT_TICKS=(\d+)',result.stderr)
        row=dict(name=name,instructions=len(frames),vm1_ticks=int(ticks[1]) if ticks else None,seconds=time.monotonic()-start,
            program_sha256=hashlib.sha256(program).hexdigest(),stdout_hex=(observed or b'').hex(),
            frames=actual,states=observed_frames,program_hex=program.hex(),input_hex=data.hex(),registers=registers,
            initial_memory={str(at):chunk.hex() for at,chunk in (initial or {}).items()},
            guest_sha256=hashlib.sha256(memory).hexdigest(),audit=result.stderr[-80:].hex())
        results.append(row)
    print('PASS RV32I',name,'guest steps',len(frames),flush=True)

rng=random.Random(71021)
for f in range(8):
    for a,b in [(0xffffffff,1),(0x80000000,31),(rng.getrandbits(32),rng.getrandbits(32))]:
        run_case('register-'+str(f)+'-'+str(a),[r(f),EBREAK],{1:a,2:b})
for f in (0,2,3,4,6,7):run_case('immediate-'+str(f),[i(f,imm=-17),EBREAK],{1:0x80000007})
for f,hi in [(0,32),(5,32)]:run_case('subtract-arithmetic-shift-'+str(f),[r(f,hi=hi),EBREAK],{1:0x80000000,2:31})
for f in (1,5):
    for shift in (0,1,31):run_case('shift-'+str(f)+'-'+str(shift),[i(f,imm=shift),EBREAK],{1:0x87654321})
run_case('srai',[i(5,imm=0x41f),EBREAK],{1:0x80000000})
run_case('lui-auipc',[0x123451b7,0x12345217,EBREAK])
run_case('x0-and-alias',[i(rd=0,imm=17),r(rd=1),i(rd=1,imm=-1),EBREAK],{1:8,2:11})
for f in (0,1,4,5,6,7):
    for b in (7,8):run_case('branch-'+str(f)+'-'+str(b),[branch(f),i(imm=15),EBREAK],{1:7,2:b})
run_case('jal',[0x008001ef,i(imm=1),EBREAK])
run_case('jalr',[i(rd=3,rs=1,imm=1,op=0x67),i(imm=2),EBREAK],{1:8})
for f in (0,1,2,4,5):run_case('load-'+str(f),[i(f,op=3),EBREAK],{1:512},initial={512:b'\x81\x82\x83\x84'})
for f in (0,1,2):run_case('store-'+str(f),[s(f),EBREAK],{1:512,2:0xABCDEF81})
for name,word,regs in [('illegal',0xffffffff,{}),('mul-rejected',r(hi=1),{}),('bad-shift',i(1,imm=0x401),{}),
        ('load-align',i(2,op=3),{1:513}),('load-access',i(2,op=3),{1:65536}),
        ('store-align',s(),{1:513}),('store-access',s(),{1:65536}),('jump-align',i(op=0x67),{1:2})]:
    run_case(name,[word,EBREAK],regs)
run_case('fence',[0x0f,EBREAK])
for name,op,fd,ptr,count,inp in [('read-short',63,0,512,5,b'AB'),('read-eof',63,0,512,5,b''),
        ('write',64,1,512,3,b''),('bad-fd',64,0,512,3,b''),('bad-pointer',63,0,65535,2,b''),
        ('zero-count',63,0,0xffffffff,0,b''),('enosys',999,0,0,0,b''),('exit',93,37,0,0,b'')]:
    run_case(name,[0x73,EBREAK],{10:fd,11:ptr,12:count,17:op},data=inp,initial={512:b'XYZ'})
run_case('write-error',[0x73,EBREAK],{10:1,11:512,12:3,17:64},initial={512:b'XYZ'},io_options={'write_error':True})
run_case('production-emulator',[i(imm=42),EBREAK],binary=EMULATOR)
with tempfile.TemporaryDirectory() as folder:
    fixture=ROOT/'examples/rv32i/smoke.c'
    program=compile_c([fixture],Path(folder)/'c')
    run_case('compiled-c',[],raw_program=program)
out=output_dir(ROOT, 'build')/'verification';out.mkdir(parents=True,exist_ok=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
(out/'coverage.json').write_text(json.dumps(sorted(coverage),indent=2)+'\n')
print('ALL',len(results),'RV32I cases passed; coverage',sorted(coverage),flush=True)
