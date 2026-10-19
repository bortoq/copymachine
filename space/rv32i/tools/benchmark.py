"""Bounded real-process measurements for a stored RV32I guest."""
import hashlib,json,os,platform,re,statistics,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
import dependencies
from cli import compile_c
from rv32i_toolchain import Toolchain
from direct_target import compile_image
from vm2compile.artifact import save
from copycode.hostpaths import output_dir

emulator=Path(os.environ.get('EMULATOR',output_dir(dependencies.EMULATOR_ROOT, 'build')/'bitcopy/emulator'))
checked=Path(os.environ.get('CHECKED_EMULATOR',output_dir(dependencies.VM2_ROOT, 'build')/'checked-emulator'))
out=output_dir(ROOT, 'build')/'measurements';out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp);start=time.monotonic();program=compile_c([ROOT/'examples/rv32i/smoke.c'],tmp/'c');c_seconds=time.monotonic()-start
    start=time.monotonic();payload,m=compile_image(program);compile_seconds=time.monotonic()-start
    args=['-s',str(m['vm1']['size']),'-p',str(m['vm1']['slots'])]
    def execute(binary,extra=(),ticks=0,env=None):
        command=['sh','-c','exec "$1" "$2" "$3" "$4" "$5" -t "$6" 4>"$7"','bench',str(binary),*args,str(ticks),str(tmp/'snapshot')]
        if extra:
            command=['/usr/bin/time','-f','RSS_KIB=%M']+command
        start=time.monotonic();r=subprocess.run(command,input=payload['boot.bin'],capture_output=True,timeout=20,env=env)
        assert r.returncode==0
        return r,time.monotonic()-start
    audit,_=execute(checked,env=dict(os.environ,VM1_AUDIT_ENTRY=str(m['entry_bits'])))
    assert audit.stdout==b'OK\n'
    startup=int(re.search(rb'VM1_AUDIT_BOOT_TICKS=(\d+)',audit.stderr)[1]);total=int(re.search(rb'VM1_AUDIT_TICKS=(\d+)',audit.stderr)[1])
    samples=[];loads=[]
    for _ in range(3):
        r,elapsed=execute(emulator);assert r.stdout==b'OK\n' and not r.stderr;samples.append(elapsed)
        r,elapsed=execute(emulator,ticks=startup);assert not r.stdout and not r.stderr;loads.append(elapsed)
    r,_=execute(emulator,extra=('rss',));rss=int(re.search(rb'RSS_KIB=(\d+)',r.stderr)[1])
row=dict(schema='rv32i-measurement-v1',platform=platform.platform(),c_compile_seconds=c_seconds,translation_seconds=compile_seconds,
    vm1=m['vm1'],code_bits=m['code_bits'],data_bits=m['data_bits'],image_bytes=len(payload['image.bin']),boot_bytes=len(payload['boot.bin']),
    bootstrap_ticks=startup,execution_ticks=total-startup,stdout_hex=audit.stdout.hex(),wall_seconds=samples,median_seconds=statistics.median(samples),load_seconds=loads,rss_kib=rss,
    notes='Three sequential real processes including startup, stdin boot and final snapshot. Load-only sample stops at audited bootstrap boundary. No claim of steady-state throughput.')
sources=list((ROOT/'modules').glob('*.py'))+[Path(__file__),ROOT/'tests/test_direct.py',ROOT/'examples/rv32i/smoke.c']
row['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
row['binary_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (emulator,checked)}
row['dependency_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
    list((dependencies.VM2_ROOT/'vm2compile').glob('*.py'))+
    [dependencies.COPYCODE_ROOT/'src/copycode/vm2/arithmetic.py',dependencies.COPYCODE_ROOT/'src/copycode/vm1/assembler.py',dependencies.COPYCODE_ROOT/'src/copycode/vm1/schedule.py']}
row['compiler_version']=subprocess.run([Toolchain().compiler,'--version'],capture_output=True,text=True,check=True,timeout=5).stdout.splitlines()[0]
(out/'results.json').write_text(json.dumps(row,indent=2)+'\n')
print('RV32I C smoke:',round(row['median_seconds']*1000,3),'ms,',row['execution_ticks'],'execution ticks,',rss,'KiB RSS')
