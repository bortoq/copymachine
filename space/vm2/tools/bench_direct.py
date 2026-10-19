#!/usr/bin/env python3
"""Real finite workloads: stored native artifact vs C-vm2 vs vm2 interpreter.

Compilation excluded from launch samples. The control packer is benchmark-only;
production never interprets legacy binaries to guess relocations.
"""
import argparse,hashlib,io,json,os,platform,re,resource,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vm2compile import Program,Copy,Field,Channel,Memory
from vm2compile.artifact import build
from copycode.vm1.machine import put
from copycode.vm2.boundary import Format,iter_boot
from vm2guest.compiler import compile_guest

def workload(kind,count):
 # Leave the same low code arena available for the independently packed
 # legacy control, including its explicit bridge/fetch layers.
 minimum=(1<<(4*(2*count+5)*64*95).bit_length())-16
 p=Program(size=max(65520,minimum),slots=64);src=p.bytes('src',bytes([0xA5])*1024);dst=p.data('dst',8192)
 if kind.startswith('patch'):
    index=p.data('index',8,1);table=p.table('lut',[65,66],8);out=p.data('out',8)
 for k in range(count):
    rows=[]
    if kind=='memory-1x8':rows=[Copy(8,dst,src)]
    if kind=='memory-63x8':rows=[Copy(8,dst+i*16,src+i*16) for i in range(63)]
    if kind=='memory-1x4096':rows=[Copy(4096,dst,src)]
    if kind.startswith('patch'):
        if kind=='patch-every-layer' or k==0:rows.append(Copy(1,Field('work:'+str((k+1)%count),0,'src',4),index))
        # Keep slot zero as the instruction patched by preceding layers.
        rows.insert(0,Copy(8,out,table))
    p.layer('work:'+str(k),rows,next='work:'+str(k+1) if k+1<count else 'emit')
 p.layer('emit',[Copy(8,Channel('stdout'),Memory('out') if kind.startswith('patch') else dst)])
 return p

def control(p,image,manifest,mapping,*,details=False):
 """Independently pack the equivalent triples, no production AOT compiler calls."""
 f=Format(manifest['vm1']['size'],manifest['vm1']['slots']);data=bytearray(f.space_bytes)
 homes={name:(2*i+1)*f.layer_bits for i,name in enumerate(p.layers)}
 halt=(2*len(homes)+1)*f.layer_bits
 assert halt+f.layer_bits<min(r['at'] for r in mapping['regions'].values())
 for r in mapping['regions'].values():
    for k in range(r['bits']):
        at=r['at']+k
        if image[at//8] & (128>>(at%8)):data[at//8]|=128>>(at%8)
 def addr(ref):
    if isinstance(ref,Memory):return mapping['regions'][ref.name]['at']+ref.offset
    if isinstance(ref,Channel):return f.space_bits+('sys','stdin','stdout','debug','status','snapshot').index(ref.name)
    if isinstance(ref,Field):return homes[ref.layer]+ref.slot*f.isz+dict(n=0,dst=f.z,src=f.z+f.a)[ref.name]+ref.offset
    raise ValueError(ref)
 data[:f.layer_bytes]=f.layer([(f.layer_bits,0,homes[p.entry])])
 for name,layer in p.layers.items():
    rows=[(c.n,addr(c.dst),addr(c.src)) for c in layer.copies]
    # A separate fetch layer prevents a field patch from overlapping the
    # source of the simultaneous next-layer fetch in the legacy ABI.
    bridge=homes[name]+f.layer_bits
    rows.append((f.layer_bits,0,bridge))
    at=homes[name]//8;data[at:at+f.layer_bytes]=f.layer(rows)
    at=bridge//8;data[at:at+f.layer_bytes]=f.layer([(f.layer_bits,0,homes[layer.following] if layer.following else halt)])
 fragments=list(iter_boot(io.BytesIO(data),f.space_bits,f.slots))
 packet=b''.join(fragments)
 return (packet,len(fragments)+1) if details else packet

from copycode.hostpaths import output_dir

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--repeats',type=int,default=7);ap.add_argument('--layers',type=int,default=32);a=ap.parse_args()
 if a.repeats<1 or a.layers<2:ap.error('positive repeats and >=2 layers required')
 emulator=Path(os.environ.get('EMULATOR',output_dir((ROOT.parent.parent if ROOT.parent.name == 'space' else ROOT.parent)/'emulator')/'bitcopy/emulator')).resolve();legacy=Path(os.environ.get('VM2_LEGACY',output_dir(ROOT)/'reference-space')).resolve();checked=output_dir(ROOT, 'build')/'checked-emulator'
 results=[];guests={}
 def execute(binary,size,slots,packet,ticks=0,env=None):
    return subprocess.run([str(binary),'-s',str(size),'-p',str(slots),'-t',str(ticks)],input=packet,capture_output=True,check=True,timeout=120,env=env)
 for name in ('memory-1x8','memory-63x8','memory-1x4096','patch-rare','patch-every-layer'):
    p=workload(name,a.layers);t=time.monotonic();packet,m=build(p);compile_time=time.monotonic()-t;mp=json.loads(packet['map.json']);S=m['vm1']['size'];P=m['vm1']['slots']
    packed=control(p,packet['image.bin'],m,mp)
    if (S,P) not in guests:
        t=time.monotonic();_,boot,guest=compile_guest(S,P);guests[S,P]=(boot,guest,time.monotonic()-t)
    boot,guest,guest_compile=guests[S,P]
    audited=execute(checked,S,P,packet['boot.bin'],env=dict(os.environ,VM1_AUDIT_ENTRY=str(m['entry_bits'])))
    physical=int(re.search(rb'VM1_AUDIT_TICKS=(\d+)',audited.stderr)[1]);startup=int(re.search(rb'VM1_AUDIT_BOOT_TICKS=(\d+)',audited.stderr)[1])
    configs={'direct':(emulator,S,P,packet['boot.bin']), 'c-vm2':(legacy,S,P,packed), 'interpreter':(emulator,guest['host']['size'],guest['host']['slots'],boot+packed)}
    expected=audited.stdout;samples={};startup_samples=[];rss={}
    for mode,args in configs.items():
        samples[mode]=[]
        for _ in range(a.repeats):
            before=resource.getrusage(resource.RUSAGE_CHILDREN);t=time.monotonic();r=execute(*args);elapsed=time.monotonic()-t;after=resource.getrusage(resource.RUSAGE_CHILDREN)
            assert r.stdout==expected and not r.stderr,(name,mode,r)
            samples[mode].append(dict(wall_seconds=elapsed,cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime))
        r=subprocess.run(['/usr/bin/time','-f','RSS_KIB=%M',str(args[0]),'-s',str(args[1]),'-p',str(args[2])],input=args[3],capture_output=True,check=True,timeout=120)
        assert r.stdout==expected;rss[mode]=int(r.stderr.decode().split('RSS_KIB=')[-1])
    for _ in range(a.repeats):
        t=time.monotonic();r=execute(emulator,S,P,packet['boot.bin'],startup);startup_samples.append(time.monotonic()-t);assert not r.stdout and not r.stderr
    row=dict(workload=name,source_layers=a.layers+1,patches=a.layers if name=='patch-every-layer' else int(name=='patch-rare'),
        source_sha256=m['source_sha256'],image_sha256=m['files']['image.bin']['sha256'],stdout_hex=expected.hex(),
        compile_seconds=compile_time,interpreter_compile_seconds=guest_compile,vm1=m['vm1'],code_bits=m['code_bits'],data_bits=m['data_bits'],image_bytes=len(packet['image.bin']),boot_bytes=len(packet['boot.bin']),
        vm1_ticks=physical,bootstrap_ticks=startup,execution_ticks=physical-startup,bootstrap_wall_seconds=startup_samples,
        samples=samples,rss_kib=rss,median_seconds={mode:statistics.median(s['wall_seconds'] for s in rows) for mode,rows in samples.items()})
    row['speedup_vs_interpreter']=row['median_seconds']['interpreter']/row['median_seconds']['direct'];row['slowdown_vs_c']=row['median_seconds']['direct']/row['median_seconds']['c-vm2']
    results.append(row);print(name,json.dumps(row['median_seconds']),row['execution_ticks'],'execution ticks',flush=True)
 a.output.mkdir(parents=True,exist_ok=True);(a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 # A genuinely cyclic immutable body, bounded by a logical layer counter in
 # the direct ABI and explicit equivalent physical/virtual control limits.
 p=Program(limit=2*a.layers);src=p.bytes('src',b'L');dst=p.data('dst',8)
 p.layer('loop',[Copy(8,dst,src)],next='emit');p.layer('emit',[Copy(8,Channel('stdout'),dst)],next='loop')
 t=time.monotonic();packet,m=build(p);translation=time.monotonic()-t;S=m['vm1']['size'];P=m['vm1']['slots']
 packed,boot_ticks=control(p,packet['image.bin'],m,json.loads(packet['map.json']),details=True)
 control_ticks=boot_ticks+4*a.layers
 _,guest_boot,guest=compile_guest(S,P,ticks=control_ticks)
 configs={'direct':(emulator,S,P,packet['boot.bin'],0),'c-vm2':(legacy,S,P,packed,control_ticks),
          'interpreter':(emulator,guest['host']['size'],guest['host']['slots'],guest_boot+packed,0)}
 cycle_samples={}
 for mode,args in configs.items():
    cycle_samples[mode]=[]
    for _ in range(a.repeats):
        t=time.monotonic();r=execute(*args);cycle_samples[mode].append(time.monotonic()-t)
        assert r.stdout==b'L'*a.layers and not r.stderr,(mode,'immutable cycle',r.stdout,r.stderr)
 audit=execute(checked,S,P,packet['boot.bin'],env=dict(os.environ,VM1_AUDIT_ENTRY=str(m['entry_bits'])))
 assert audit.stdout==b'L'*a.layers
 cycle=dict(iterations=a.layers,compile_seconds=translation,source_sha256=m['source_sha256'],vm1=m['vm1'],wall_seconds=cycle_samples,
    vm1_ticks=int(re.search(rb'VM1_AUDIT_TICKS=(\d+)',audit.stderr)[1]),bootstrap_ticks=int(re.search(rb'VM1_AUDIT_BOOT_TICKS=(\d+)',audit.stderr)[1]),
    control_virtual_ticks=control_ticks,control_bootstrap_ticks=boot_ticks,
    note='Two immutable logical layers in a real cycle. Direct limit counter is in-space; C physical and interpreter virtual limits include boot and explicit fetch bridges. Includes process startup and loop output.')
 (a.output/'immutable-cycle.json').write_text(json.dumps(cycle,indent=2)+'\n')
 # Real owner-generated RV32I transport fragment: measured independently of
 # the synthetic controls, whose packer intentionally has a smaller ABI.
 p=Program.load(json.loads((ROOT/'examples/direct/rv32i-fragment.json').read_text()))
 t=time.monotonic();packet,m=build(p);translation=time.monotonic()-t
 S=m['vm1']['size'];P=m['vm1']['slots']
 audit=execute(checked,S,P,packet['boot.bin'],env=dict(os.environ,VM1_AUDIT_ENTRY=str(m['entry_bits'])))
 startup=int(re.search(rb'VM1_AUDIT_BOOT_TICKS=(\d+)',audit.stderr)[1]);total=int(re.search(rb'VM1_AUDIT_TICKS=(\d+)',audit.stderr)[1])
 samples=[]
 for _ in range(a.repeats):
    t=time.monotonic();r=execute(emulator,S,P,packet['boot.bin']);samples.append(time.monotonic()-t)
    assert r.stdout==audit.stdout and not r.stderr
 fragment=dict(source_sha256=m['source_sha256'],compile_seconds=translation,vm1=m['vm1'],image_bytes=len(packet['image.bin']),boot_bytes=len(packet['boot.bin']),
    code_bits=m['code_bits'],data_bits=m['data_bits'],bootstrap_ticks=startup,execution_ticks=total-startup,stdout_hex=audit.stdout.hex(),wall_seconds=samples,
    scope='Direct execution only; owner-generated memory load/store, LUT and indirect jump; not a full RV32I CPU')
 (a.output/'rv32i-fragment.json').write_text(json.dumps(fragment,indent=2)+'\n')
 import copycode.vm1.optimize,copycode.vm1.assembler,copycode.vm1.schedule
 sources=list((ROOT/'vm2compile').glob('*.py'))+[Path(__file__),ROOT/'tools/limited_run.py',ROOT/'examples/direct/rv32i-fragment.json',Path(copycode.vm1.assembler.__file__),Path(copycode.vm1.schedule.__file__),Path(copycode.vm1.optimize.__file__)]
 metadata=dict(platform=platform.platform(),cpu=next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),repeats=a.repeats,layers=a.layers,
    binary_sha256={str(binary.relative_to(ROOT.parent)):hashlib.sha256(binary.read_bytes()).hexdigest() for binary in (emulator,legacy,checked)},
    source_sha256={str(path.relative_to(ROOT.parent)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
    notes='Same finite logical workloads; independently packed triples for C/interpreter, with explicit separate next-layer fetches to avoid patch/fetch overlap. All samples real processes including startup/boot, compilation excluded. Load-only measured with audited bootstrap limit. RSS includes process image. No FPGA resource claim.')
 (a.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
if __name__=='__main__':main()
