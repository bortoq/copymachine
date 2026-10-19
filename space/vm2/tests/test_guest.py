"""Real emulator execution against an independent per-bit vm2 reference."""
import errno,hashlib,json,os,random,re,subprocess,tempfile,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vm2guest.compiler import compile_guest
from copycode.vm2.boundary import Format,boot_stream,protocol,record
from vm2_reference import run as reference,get,put,store_bytes

ROOT=Path(__file__).resolve().parents[1]
from copycode.hostpaths import output_dir

EMULATOR=Path(os.environ.get('EMULATOR',output_dir((ROOT.parent.parent if ROOT.parent.name == 'space' else ROOT.parent)/'emulator')/'bitcopy/emulator'))

CHECKED=Path(os.environ.get('CHECKED_EMULATOR',output_dir(ROOT, 'build')/'checked-emulator'))
cache={};cases=[]

def compiler(size,slots,ticks=0,snapshot=True,report=True,**generation):
    key=(size,slots,ticks,snapshot,report,tuple(sorted(generation.items())))
    if key not in cache:cache[key]=compile_guest(size,slots,ticks=ticks,snapshot=snapshot,report=report,**generation)
    return cache[key]

def run_case(name,stream,size=65520,slots=8,ticks=0,*,regular=False,bound=(1,2,3,4,5),stdout_error=0,binary=CHECKED,generation=None):
    expected=reference(stream,size,slots,ticks,regular=regular,bound=bound,stdout_error=stdout_error)
    _,boot,meta=compiler(size,slots,ticks,**(generation or {}))
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)
        # fd 3/4 are ordinary inherited files for both the guest and its optional reporter.
        redirects=('3>"$3"' if 4 in bound else '3>&-')+' '+('4>"$4"' if 5 in bound else '4>&-')
        command=['sh','-c','exec "$1" -s "$2" -p "$5" '+redirects,'guest-test',str(binary),str(meta['host']['size']),str(p/'r'),str(p/'s'),str(meta['host']['slots'])]
        with tempfile.TemporaryFile() as file:
            if regular:
                file.write(boot+stream);file.seek(0)
            begin=time.monotonic()
            result=subprocess.run(command,input=None if regular else boot+stream,stdin=file if regular else None,
                stdout=open('/dev/full','wb') if stdout_error else subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
            elapsed=time.monotonic()-begin
        assert result.returncode==0,(name,result.returncode,result.stderr[-2000:])
        actual_out=result.stdout or b'';actual_err=result.stderr
        match=re.search(rb'VM1_AUDIT_TICKS=(\d+)\n$',actual_err)
        microticks=int(match[1]) if match else None
        if match:actual_err=actual_err[:match.start()]
        assert actual_out==bytes(expected['channels'][2]['data']),(name,'stdout',actual_out,expected['channels'][2])
        assert actual_err==bytes(expected['channels'][3]['data']),(name,'stderr',actual_err)
        if 4 in bound:
            raw=(p/'r').read_bytes();report=raw[-12:] if expected['channels'][4]['used'] else b''
            if report:
                assert report[:4]==b'VM2R' and get(report,32,64)==expected['ticks'],(name,'tick report',report)
            assert raw[:len(raw)-len(report)]==bytes(expected['channels'][4]['data']),(name,'guest fd3')
        if 5 in bound:
            raw=(p/'s').read_bytes();snapshot=raw[-len(expected['memory']):] if expected['channels'][5]['used'] else b''
            if snapshot:assert snapshot==expected['memory'],(name,'memory',next((i,x,y) for i,(x,y) in enumerate(zip(snapshot,expected['memory'])) if x!=y))
            assert raw[:len(raw)-len(snapshot)]==bytes(expected['channels'][5]['data']),(name,'guest fd4')
        cases.append(dict(name=name,guest_ticks=expected['ticks'],host_ticks=microticks,seconds=elapsed,guest_bits=size,slots=slots))
        print('PASS',name,'guest ticks',expected['ticks'],'emulator ticks',microticks,flush=True)
        return expected,meta,microticks

def image_program(layers,data=(),size=65520,slots=8):
    f=Format(size,slots);image=bytearray((size+7)//8)
    # Keep the processor separate from homes and all application buffers.
    homes=[1024+i*((f.layer_bits+63)//64*64) for i in range(len(layers)+1)]
    image[:f.layer_bytes]=f.layer([(f.layer_bits,0,homes[0])])
    for i,rows in enumerate(layers):
        image[homes[i]//8:homes[i]//8+f.layer_bytes]=f.layer(list(rows)+[(f.layer_bits,0,homes[i+1])])
    for at,values in data:store_bytes(image,at,values)
    return boot_stream(image,size,slots),image,homes

# Fetch, NOP, seed and configured limit. Each row is packed at its native width.
f=Format(65520,8)
for ticks in (1,2,3,0):
    stream,_,_=image_program([[(8,65522,20000)]],[(20000,b'A')])
    run_case('seed-limit-'+str(ticks),stream,ticks=ticks)
run_case('ordinary-binary-unaligned',*([image_program([[(13,21003,20005)],[(16,65522,21003)]],[(20000,b'\xaa\x35\x92\xff')])[0]]))
# Destructively erase instructions still due to execute in this fetched layer.
image=bytearray(8190)
image[:f.layer_bytes]=f.layer([(3*f.isz,0,24000),(8,65522,20000),(f.z,3*f.isz,25000),(8,21000,20100)])
store_bytes(image,20000,b'X');store_bytes(image,20100,b'Y')
run_case('destroy-current-processor-after-fetch',boot_stream(image,65520,8))

rng=random.Random(4026)
for case in range(8):
    layers=[]
    for layer_index in range(4):
        points=rng.sample(list(range(20000,40000,128)),8)
        layers.append([(rng.randrange(1,90),points[2*k]+rng.randrange(8),points[2*k+1]+rng.randrange(8)) for k in range(4)])
    data=[(20000,bytes(rng.randrange(256) for _ in range(2500)))]
    stream,_,_=image_program(layers,data)
    run_case('random-layer-'+str(case),stream)

ops,req,rsp=protocol(65520);REQ=req[1];RSP=rsp[1]
def request(op,chan=65522,**fields):return record(req,dict(op=op,chan=chan,**fields))
def sys_program(name,layers,data,**options):
    stream,_,_=image_program(layers,data);return run_case(name,stream,**options)
# Request in slot 0, old answer in slot 1: the request may not affect that read.
sys_program('concurrent-old-sys-answer',[
    [(REQ,65520,20000),(RSP,21000,65520)],
    [(RSP,21200,65520)],[(RSP//8*8,65522,21000)],[(RSP//8*8,65522,21200)]],[(20000,request(4))])
sys_program('close-sys-preserves-old-in-closing-tick',[
    [(REQ,65520,20000)],[(REQ,65520,20200),(RSP,21000,65520)],
    [(RSP,21200,65520)],[(RSP,65522,21000)]],[(20000,request(4)),(20200,request(1,65520))])
# Transfer T, FSTAT T+1, old-answer read T+2, dependent output T+3.
stream,_,_=image_program([[(40,21000,65521)],[(REQ,65520,20000)],[(RSP,21200,65520)],[(40,65522,21000),(RSP,65523,21200)]],[(20000,request(3,65521))])
run_case('short-read-fstat-eof',stream+b'XY')
for op in (0,1,2,3,4,99):
    sys_program('sys-op-'+str(op),[[(REQ,65520,20000)],[(RSP,21000,65520)],[(RSP,65522,21000)]],[(20000,request(op,65522))])
for channel in (65520,65521,65522,65523,65524,65525,65526,65535,1234):
    sys_program('fstat-map-'+str(channel),[[(REQ,65520,20000)],[(RSP,21000,65520)],[(RSP,65522,21000)]],[(20000,request(3,channel))])
# Unbound positions have no data transfer, even if their numeric code is large.
sys_program('unbound-data-ignored',[[(8,65535,20000)],[(8,21000,65534)]],[(20000,b'Z')])
sys_program('close-data-channel',[[(REQ,65520,20000)],[(8,65522,20200)],[(REQ,65520,20400)],[(RSP,21000,65520)],[(RSP,65523,21000)]],[(20000,request(1)),(20200,b'X'),(20400,request(3))])
# EXEC copies command bytes and adjusts the advertised record count, not just chan.
for name,command,short in [('exec-exit',b'exit 7',False),('exec-output',b"printf 'ok'",False),('exec-short',b'echo forbidden',True),('exec-empty',b'',False)]:
    payload=request(5,arg=len(command))+command
    n=REQ if short else REQ+8*len(command)
    sys_program(name,[[(n,65520,20000)],[(RSP,21000,65520)],[(RSP,65523,21000)]],[(20000,payload)])
# Real seekable input; origin and size exclude the emulator interpreter's own boot.
stream,_,_=image_program([[(REQ,65520,20000)],[(RSP,21000,65520)],[(RSP,65522,21000)],
                        [(REQ,65520,20200)],[(8,21200,65521)],[(8,65522,21200)]],
                        [(20000,request(3,65521)),(20200,request(2,65521,arg=0,off=0))])
run_case('regular-stdin-size-and-seek-set',stream,regular=True)
# Negative relative offsets must not expose the emulator bootstrap prefix.
for origin in (0,1,2):
    stream,_,_=image_program([[(REQ,65520,20000)],[(RSP,21000,65520)],[(RSP,65522,21000)]],[(20000,request(2,65521,arg=origin,off=((1<<64)-10000)))])
    run_case('seek-before-guest-start-'+str(origin),stream,regular=True)
stream,_,_=image_program([[(16,21000,65521)],[(REQ,65520,20000)],[(16,21200,65521)],[(16,65522,21200)]],[(20000,request(2,65521,arg=1,off=(1<<64)-1))])
run_case('seek-cur-retains-logical-cursor',stream+b'ABC',regular=True)
stream,_,_=image_program([[(REQ,65520,20000)],[(16,21200,65521)],[(16,65522,21200)]],[(20000,request(2,65521,arg=2,off=(1<<64)-2))])
run_case('seek-end-retains-guest-origin',stream+b'END',regular=True)

# Other widths and non-byte-aligned guest processors/spaces.
for size,slots in [(30000,9),(65519,8),(1048560,8)]:
    stream,_,_=image_program([[(8,size+2,20000)]],[(20000,b'Q')],size,slots)
    run_case('layout-'+str(size)+'-'+str(slots),stream,size,slots)
# P=1 has no installer dependency; output observes its own n field.
for size in (1024,1041):
    a=size.bit_length();z=a-1;I=3*a-1;data=bytearray((I+7)//8)
    put(data,0,z,8);put(data,z,a,size+2);put(data,z+a,a,0)
    run_case('single-slot-'+str(size),bytes(data),size,1,2)

# Native instruction width, numeric carries and the endpoint exactly at S.
stream,_,_=image_program([[(9,65511,20000)],[(8,65522,65512)]],[(20000,b'\xde\xad')])
run_case('memory-end-equals-S',stream)
image=bytearray(8190);image[:f.layer_bytes]=f.layer([(30000,32000,1000)])
store_bytes(image,1000,bytes((i*19)%256 for i in range(3750)))
run_case('long-copy-no-guest-source-snapshot',boot_stream(image,65520,8),ticks=10)
# All declared data channels and optional absence/close retain their guest identity.
sys_program('optional-output-and-stat',[[(8,65524,20200),(8,65525,20400)],[(REQ,65520,20000)],[(RSP,21000,65520)],[(RSP,65522,21000)]],[(20000,request(3,65525)),(20200,b'T'),(20400,b'S')])
for bound in [(1,2,3,5),(1,2,3,4)]:
    sys_program('optional-absent-'+str(bound),[[(REQ,65520,20000)],[(RSP,21000,65520)],[(RSP,65522,21000)]],[(20000,request(3,65524 if 4 not in bound else 65525))],bound=bound)
sys_program('stdout-error-state',[[(8,65522,20200)],[(REQ,65520,20000)],[(RSP,21000,65520)],[(RSP,65523,21000)]],[(20000,request(3)),(20200,b'X')],stdout_error=errno.ENOSPC)
# Multiple answer reads get the same old response; neither reads the request result.
sys_program('multiple-old-answer-reads',[[(REQ,65520,20000)],[(RSP,21000,65520),(RSP,21200,65520),(REQ,65520,20200)],[(RSP,65522,21000),(RSP,65523,21200)]],[(20000,request(4)),(20200,request(99))])
for size in (30000,1048560):
    _,q,r=protocol(size);qb,rb=q[1],r[1]
    req_data=record(q,dict(op=4,chan=size+2))
    stream,_,_=image_program([[(qb,size,20000)],[(rb,21000,size)],[(rb,size+2,21000)]],[(20000,req_data)],size)
    run_case('sys-width-'+str(size),stream,size)
# The 8 MiB guest keeps its 77-bit triples, not padded emulator instructions.
size=(1<<26)-6
stream,_,_=image_program([[(8,size+2,20000)]],[(20000,b'W')],size)
run_case('wide-77-bit-guest',stream,size)
# A raw memory snapshot is restored with the ordinary guest stdin installer.
stream,_,_=image_program([[(8,65522,20000)],[(8,65522,20200)]],[(20000,b'A'),(20200,b'B')])
state,_,_=run_case('checkpoint-at-virtual-boundary',stream,ticks=5)
run_case('checkpoint-continuation',boot_stream(state['memory'],65520,8))

# The same frozen guest layer is executed by every ablation configuration.
# Dense and sparse P=64 layers exercise descriptor batching and NOPs whose
# address fields happen to name channels. They must remain inactive.
variants={'baseline':dict(scheduling='none',translation='serial',arithmetic='ripple',host_slots=8),
          'schedule':dict(scheduling='schedule',translation='serial',arithmetic='ripple',host_slots=8),
          'optimize':dict(scheduling='optimize',translation='serial',arithmetic='ripple',host_slots=8),
          'parallel':{}}
wide=Format(65520,64)
for active_copies in (1,63):
    image=bytearray(8190);homes=(4096,8192)
    image[:wide.layer_bytes]=wide.layer([(wide.layer_bits,0,homes[0])])
    for index,home in enumerate(homes):
        rows=[(0,65535,65535)]*63
        for k in range(active_copies):rows[62-k]=(13,40003+k*64,20005+k*64)
        image[home//8:home//8+wide.layer_bytes]=wide.layer(rows+[(wide.layer_bits,0,homes[1-index])])
    store_bytes(image,20000,bytes(rng.randrange(256) for _ in range(512)))
    stream=boot_stream(image,65520,64)
    for name,generation in variants.items():
        run_case('batch64-'+str(active_copies)+'-'+name,stream,65520,64,8,generation=generation)

# The production emulator executable, not only the audited harness, executes the guest.
stream,_,_=image_program([[(8,65522,20000)]],[(20000,b'P')])
_,meta,physical=run_case('production-emulator',stream,binary=EMULATOR)
result_path=Path(os.environ.get('VM2_GUEST_RESULTS',output_dir(ROOT, 'build')/'guest-tests/results.json'))
result_path.parent.mkdir(parents=True,exist_ok=True);result_path.write_text(json.dumps(cases,indent=2)+'\n')
print('ALL',len(cases),'vm2-on-vm1 cases passed',flush=True)
