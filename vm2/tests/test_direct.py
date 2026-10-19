"""Direct artifacts against independent logical oracle and real audited vm1."""
import copy,json,os,random,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vm2compile import Program,Copy,Memory,Field,Channel,Replace,Value,SysWidth
from vm2compile.artifact import build,save,load,resume,static_code_digest
from vm2compile.sdk import sys_record,request,response,stdin_position,construct
from direct_reference import run as oracle
from vm2_reference import get,payload

CHECKED=Path(os.environ.get('CHECKED_VM1',ROOT/'build/checked-vm1'))
VM1=Path(os.environ.get('VM1',ROOT.parent/'vm1/build/bitcopy/vm1'))
cases=[];rng=random.Random(61023)

def run(name,p,stream=b'',*,regular=False,snapshot=True,binary=CHECKED,stdout_error=0):
    if snapshot:
        p=copy.deepcopy(p)
        for layer in list(p.layers.values()):
            if layer.following is None and not layer.checkpoint:layer.following='test:final'
        p.layer('test:final',checkpoint=True)
    a,m=build(p);mp=json.loads(a['map.json']);expected=oracle(p.source(),m,mp,stream,regular=regular,stdout_error=stdout_error,boot=a['boot.bin'])
    with tempfile.TemporaryDirectory() as d:
        d=Path(d);saved=d/'memory';status=d/'status'
        command=['sh','-c','exec "$1" -s "$2" -p "$3" 3>"$4" 4>"$5"','direct-test',str(binary),str(m['vm1']['size']),str(m['vm1']['slots']),str(status),str(saved)]
        with tempfile.TemporaryFile() as f:
            if regular:f.write(a['boot.bin']+stream);f.seek(0)
            result=subprocess.run(command,input=None if regular else a['boot.bin']+stream,stdin=f if regular else None,
                                  stdout=open('/dev/full','wb') if stdout_error else subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        assert result.returncode==0,(name,result.returncode,result.stderr[-2000:])
        error=re.sub(rb'VM1_AUDIT_TICKS=\d+\n$',b'',result.stderr)
        assert result.stdout is None and stdout_error or result.stdout==bytes(expected['channels'][2]['data']),(name,'stdout',result.stdout,expected['channels'][2])
        assert error==bytes(expected['channels'][3]['data']),(name,'debug',error)
        assert status.read_bytes()==bytes(expected['channels'][4]['data']),(name,'status')
        raw=saved.read_bytes()
        if snapshot and raw:
            image=raw[-((m['vm1']['size']+7)//8):]
            assert len(image)==(m['vm1']['size']+7)//8,(name,len(image))
            for r in mp['regions'].values():
                assert get(image,r['at'],r['bits'])==get(expected['memory'],r['at'],r['bits']),(name,'data',r)
            for fields in mp['fields'].values():
                for r in fields.values():assert get(image,r['at'],r['bits'])==get(expected['memory'],r['at'],r['bits']),(name,'field',r)
            assert static_code_digest(image,m)==m['static_code_sha256'],(name,'unexpected code change')
        elif snapshot:raise AssertionError((name,'missing snapshot'))
    assert Program.load(p.source()).source()==p.source()
    cases.append(dict(name=name,source_layers=expected['ticks'],vm1_bits=m['vm1']['size'],code_bits=m['code_bits']))
    print('PASS direct',name,flush=True)
    return a,m,mp

# Static pure data, native channels, unaligned operands and full source fetch.
for i in range(20):
    p=Program(slots=16);src=p.data('source',2048,rng.getrandbits(2048));dst=p.data('dest',2048)
    for layer in range(3):
        rows=[Copy(rng.randrange(1,50),dst+k*128+rng.randrange(8),src+k*128+rng.randrange(8)) for k in range(8)]
        p.layer(str(layer),rows,next=str(layer+1) if layer<2 else None)
    run('random-static-'+str(i),p)
p=Program();buf=p.bytes('binary',b'\x00\xff\x81\x7e');dest=p.data('read',32)
p.layer('read',[Copy(32,dest,Channel('stdin'))],next='write')
p.layer('write',[Copy(29,Channel('stdout'),dest),Copy(24,Channel('debug'),buf)],next='optional')
p.layer('optional',[Copy(16,Channel('status'),buf),Copy(16,Channel('snapshot'),buf+16)])
run('all-data-channels-short-read',p,b'XY')

# A LUT selector updates both ends without an adder, including non-byte fields.
for width in (1,2,7,8,13):
    p=Program();index=p.data('index',8,5);table=p.table('lut',[rng.getrandbits(width) for _ in range(8)],width)
    out=p.data('out',32);shift=p.regions['lut'].table['stride_bits']
    p.layer('patch',[Copy(3,Field('read',0,'src',shift),index)],next='read')
    p.layer('read',[Copy(width,out,table)])
    _,_,mp=run('lut-'+str(width),p);assert set(mp['updates'].values())=={'bit-slices'}
p=Program();index=p.data('index',8,5);table=p.table('lut',range(8),3);out=p.data('out',8)
p.layer('low',[Copy(1,Field('read',0,'src',2),index)],next='high')
p.layer('high',[Copy(2,Field('read',0,'src',3),index+1)],next='read')
p.layer('read',[Copy(3,out,table)])
_,_,mp=run('separate-selector-patches',p);assert set(mp['updates'].values())=={'bit-slices'}

# Partial n and address changes must recompute carries across the whole word.
for value in (0,1,7,8,13,31):
    p=Program(size=1048560);count=p.data('count',32,value);src=p.data('source',64,rng.getrandbits(64));out=p.data('out',64)
    p.layer('patch',[Copy('count',Field('copy',0,'n'),count)],next='copy');p.layer('copy',[Copy(8,out,src)])
    run('new-count-'+str(value),p)
for attr in ('src','dst'):
    for value in (1,7,17,33):
        p=Program(size=1048560);offset=p.data('offset',8,value);src=p.data('source',128,rng.getrandbits(128),align=256);dst=p.data('dest',128,align=256)
        p.layer('patch',[Copy(6,Field('copy',0,attr),offset)],next='copy');p.layer('copy',[Copy(13,dst,src)])
        run('address-carry-'+attr+'-'+str(value),p)
# n changes after an earlier address patch; fast-path proofs must use all writes.
p=Program(size=1048560);offset=p.data('offset',8,17);count=p.data('count',32,19);src=p.data('source',128,rng.getrandbits(128),align=256);dst=p.data('out',128)
p.layer('address',[Copy(6,Field('copy',0,'src'),offset)],next='length')
p.layer('length',[Copy('count',Field('copy',0,'n'),count)],next='copy');p.layer('copy',[Copy(8,dst,src)])
run('address-then-length',p)
# Updating the currently fetched description takes effect on the next visit.
p=Program(size=1048560,limit=4);index=p.data('index',8,1);table=p.table('lut',[0,1],1);out=p.data('out',8)
p.layer('loop',[Copy(1,Field('loop',1,'src',1),index),Copy(1,out,table)],next='emit')
p.layer('emit',[Copy(8,Channel('stdout'),out)],next='loop')
run('current-layer-fetch',p,snapshot=False)
# A partial n patch exercises bit slices and carry recomputation together.
p=Program(size=1048560);bit=p.data('bit',8,1);src=p.data('src',64,0xABCDEF);out=p.data('out',64)
p.layer('patch',[Copy(1,Field('copy',0,'n'),bit)],next='copy');p.layer('copy',[Copy(8,out,src)])
run('partial-count-bit',p)
# A dynamically changed stream count is byte rounded; C,C stays unchanged.
for count in (0,7,13):
    p=Program(size=1048560);n=p.data('count',32,count);src=p.bytes('src',b'XYZ')
    p.layer('patch',[Copy('count',Field('write',0,'n'),n)],next='write')
    p.layer('write',[Copy(8,Channel('stdout'),src)])
    run('dynamic-stream-count-'+str(count),p)
p=Program(size=1048560);n=p.data('count',32,16);src=p.bytes('src',b'XY')
p.layer('patch',[Copy('count',Field('write',0,'n'),n)],next='write')
p.layer('write',[Copy(0,Channel('stdout'),src)])
run('activate-zero-count-stream',p)
# Read logical fields through the sparse state, rather than native raw code bits.
p=Program();src=p.data('src',128,0xBEEF);out=p.data('out',128);view=p.data('view',64)
p.layer('inspect',[Copy('address',view,Field('copy',0,'src'))],next='copy');p.layer('copy',[Copy(19,out,src)])
run('logical-field-read',p)
# Whole-layer replacement, followed by a field update of the replaced target.
p=Program(size=1048560);x=p.bytes('x',b'A');y=p.bytes('y',b'B');view=p.data('view',32);count=p.data('count',32,8)
p.layer('replace',[Replace('target','template')],next='change')
p.layer('change',[Copy('count',Field('target',0,'n'),count)],next='target')
p.layer('target',[Copy(8,view,x)],next='emit');p.layer('template',[Copy(8,view,y)],next='emit')
p.layer('emit',[Copy(8,Channel('stdout'),view)])
run('replace-and-update',p)
# Dynamically build a previously empty description using the common SDK.
p=Program(size=1048560);x=p.bytes('x',b'D');out=p.data('out',16)
p.layer('build',construct(p,'new',0,n=8,dst=Value('data','out'),src=Value('data','x')),next='new')
p.layer('new',[Copy(0,out,x)],next='emit');p.layer('emit',[Copy(8,Channel('stdout'),out)])
run('new-description',p)
# Native indirect control uses a typed relocated pointer, frozen at source fetch.
p=Program();ptr=p.pointer('ptr',Value('entry','out'));data=p.bytes('msg',b'J')
p.layer('dispatch',next=ptr);p.layer('wrong',[Copy(8,Channel('debug'),data)]);p.layer('out',[Copy(8,Channel('stdout'),data)])
run('indirect-jump',p)

# Native SYS widths, old/new answer, short reads, errors and explicit stdin origin.
for op in ('NONE','FSTAT','IOCTL','CLOSE'):
    p=Program();q=sys_record(p,'request',op=op,chan=Channel('stdout'));old=sys_record(p,'old',kind='rsp');answer=sys_record(p,'answer',kind='rsp')
    p.layer('request',[request(q),response(old)],next='answer');p.layer('answer',[response(answer)])
    run('sys-'+op,p)
p=Program();q=sys_record(p,'request',op='CLOSE',chan=Channel('sys'));old=sys_record(p,'old',kind='rsp');answer=sys_record(p,'answer',kind='rsp')
p.layer('close',[request(q),response(old)],next='read');p.layer('read',[response(answer)])
run('close-sys-old-answer',p)
p=Program();buf=p.data('buffer',40);q=sys_record(p,'stat',op='FSTAT',chan=Channel('stdin'));r=sys_record(p,'reply',kind='rsp')
p.layer('read',[Copy(40,buf,Channel('stdin'))],next='stat');p.layer('stat',[request(q)],next='reply');p.layer('reply',[response(r)])
run('short-read-fstat',p,b'AB')
p=Program();q=sys_record(p,'seek',op='SEEK',chan=Channel('stdin'),off=stdin_position(1));r=sys_record(p,'reply',kind='rsp');buf=p.data('buffer',16)
p.layer('seek',[request(q)],next='reply');p.layer('reply',[response(r)],next='read');p.layer('read',[Copy(16,buf,Channel('stdin'))],next='out');p.layer('out',[Copy(16,Channel('stdout'),buf)])
run('native-seek-with-origin',p,b'ABC',regular=True)
for width in (8,13,24):
    p=Program();src=p.bytes('source',b'XYZ');r=sys_record(p,'reply',kind='rsp');q=sys_record(p,'request',op='FSTAT',chan=Channel('stdout'))
    p.layer('write',[Copy(width,Channel('stdout'),src)],next='stat');p.layer('stat',[request(q)],next='reply');p.layer('reply',[response(r)])
    run('stdout-error-'+str(width),p,stdout_error=28)

# Snapshot resumes compiled code and sparse state without source/recompilation.
p=Program();x=p.bytes('x',b'A');y=p.bytes('y',b'B')
p.layer('first',[Copy(8,Channel('stdout'),x)],next='second',checkpoint=True,checkpoint_stop=True);p.layer('second',[Copy(8,Channel('stdout'),y)])
a,m=build(p)
with tempfile.TemporaryDirectory() as folder:
 folder=Path(folder);obj=folder/'object';save(obj,a,m);raw=folder/'snapshot'
 cmd=['sh','-c','exec "$1" -s "$2" -p "$3" 4>"$4"','snapshot',str(CHECKED),str(m['vm1']['size']),str(m['vm1']['slots']),str(raw)]
 r=subprocess.run(cmd,input=a['boot.bin'],capture_output=True,check=True);assert r.stdout==b'A'
 native,mm=resume(obj,raw);rr=subprocess.run([str(CHECKED),'-s',str(mm['vm1']['size']),'-p',str(mm['vm1']['slots'])],input=native['boot.bin'],capture_output=True,check=True)
 assert rr.stdout==b'B'
 bad=bytearray(raw.read_bytes());bad[m['entry_bits']//8]^=1;(folder/'wrong').write_bytes(bad)
 try:resume(obj,folder/'wrong')
 except ValueError:pass
 else:raise AssertionError('incompatible snapshot accepted')
 print('PASS direct snapshot/resume and code/ABI identity',flush=True)
# Portable source captured from real RV32I owner builders; archive needs no owner checkout.
p=Program.load(json.loads((ROOT/'examples/direct/rv32i-fragment.json').read_text()))
run('legacy-rv32i-fragment',p)
# Production executable is also exercised, not only the audit harness.
p=Program();data=p.bytes('out',b'production');p.layer('out',[Copy(80,Channel('stdout'),data)])
run('production-vm1',p,binary=VM1)
result=ROOT/'build/direct-tests/results.json';result.parent.mkdir(parents=True,exist_ok=True);result.write_text(json.dumps(cases,indent=2)+'\n')
print('ALL',len(cases),'direct cases passed',flush=True)
