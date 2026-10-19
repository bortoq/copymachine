#!/usr/bin/env python3
"""Benchmark actual emulator processes; physical tick counts from the test audit."""
import argparse,hashlib,json,os,platform,resource,statistics,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vm2guest.compiler import compile_guest
from copycode.vm2.boundary import Format,boot_stream
from copycode.vm1.machine import field

from copycode.hostpaths import output_dir

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=5);p.add_argument('--ticks',type=int,default=32)
    p.add_argument('--variant',choices=('baseline','schedule','optimize','parallel','parallel-ripple','parallel-prefix'),default='parallel')
    p.add_argument('--host-slots',type=int)
    args=p.parse_args()
    if args.repeats<1 or args.ticks<8:p.error('need repeats>=1 and ticks>=8')
    emulator=Path(os.environ.get('EMULATOR',output_dir((ROOT.parent.parent if ROOT.parent.name == 'space' else ROOT.parent)/'emulator')/'bitcopy/emulator')).resolve()
    legacy=Path(os.environ.get('VM2_LEGACY',output_dir(ROOT)/'reference-space')).resolve();checked=output_dir(ROOT, 'build')/'checked-emulator'
    f=Format(65520,64);results=[]
    options={'baseline':dict(scheduling='none',translation='serial',arithmetic='ripple'),
             'schedule':dict(scheduling='schedule',translation='serial',arithmetic='ripple'),
             'optimize':dict(scheduling='optimize',translation='serial',arithmetic='ripple'),
             'parallel':dict(scheduling='optimize',translation='parallel',arithmetic='hybrid'),
             'parallel-prefix':dict(scheduling='optimize',translation='parallel',arithmetic='prefix'),
             'parallel-ripple':dict(scheduling='optimize',translation='parallel',arithmetic='ripple')}[args.variant]
    options['host_slots']=args.host_slots
    began=time.monotonic();_,boot,meta=compile_guest(65520,64,ticks=args.ticks,snapshot=True,report=True,**options)
    compile_seconds=time.monotonic()-began
    for active,length,workload in [(1,8,'memory'),(63,8,'memory'),(1,4096,'memory'),(1,8,'stdout')]:
        image=bytearray(f.space_bytes);homes=(4096,8192)
        source,dest=(32768,49152) if length==8 else (20000,40000)
        if workload=='stdout':dest=65522
        rows=[(length,dest+i*16,source+i*16) for i in range(active)]
        image[:f.layer_bytes]=f.layer([(f.layer_bits,0,homes[0])])
        for i,at in enumerate(homes):image[at//8:at//8+f.layer_bytes]=f.layer(rows+[(f.layer_bits,0,homes[1-i])])
        image[source//8:source//8+(length+7)//8]=bytes([0xA5])*((length+7)//8)
        guest_input=boot_stream(image,65520,64)
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);report=base/'report';snapshot=base/'snapshot'
            def command(binary,physical_limit=0):
                argv=['sh','-c','exec "$1" -s "$2" -p "$3" -t "$4" 3>"$5" 4>"$6"','bench',str(binary),str(meta['host']['size']), str(meta['host']['slots']),str(physical_limit),str(report),str(snapshot)]
                return argv
            audit=subprocess.run(command(checked),input=boot+guest_input,capture_output=True,timeout=120,check=True,
                                 env=dict(os.environ,VM1_AUDIT_ENTRY=str(meta['entry_bits'])))
            physical=int(audit.stderr.decode().split('VM1_AUDIT_TICKS=')[-1])
            boot_ticks=int(audit.stderr.decode().split('VM1_AUDIT_BOOT_TICKS=')[-1].split('\n')[0])
            expected_stdout=audit.stdout
            assert field(report.read_bytes(),32,64)==args.ticks
            full_snapshot=snapshot.read_bytes();assert len(full_snapshot)==f.space_bytes
            startup=[]
            for _ in range(args.repeats):
                began=time.monotonic()
                run=subprocess.run(command(emulator,boot_ticks),input=boot+guest_input,capture_output=True,timeout=120,check=True)
                startup.append(time.monotonic()-began)
                assert not run.stdout and not run.stderr and not report.read_bytes() and not snapshot.read_bytes()
            # Cross-check measured physical count through the production CLI limit.
            for limit,complete in [(physical-1,False),(physical,True)]:
                run=subprocess.run(command(emulator,limit),input=boot+guest_input,capture_output=True,timeout=120,check=True)
                assert bool(report.read_bytes())==complete and not run.stderr
            samples=[]
            for _ in range(args.repeats):
                before=resource.getrusage(resource.RUSAGE_CHILDREN);began=time.monotonic()
                run=subprocess.run(command(emulator),input=boot+guest_input,capture_output=True,timeout=120,check=True)
                elapsed=time.monotonic()-began;after=resource.getrusage(resource.RUSAGE_CHILDREN)
                assert run.stdout==expected_stdout and not run.stderr and snapshot.read_bytes()==full_snapshot
                samples.append(dict(wall_seconds=elapsed,cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime))
            old=[]
            for _ in range(args.repeats):
                began=time.monotonic();run=subprocess.run([str(legacy),'-p64','-t'+str(args.ticks)],input=guest_input,capture_output=True,timeout=10,check=True)
                assert run.stdout==expected_stdout and not run.stderr;old.append(time.monotonic()-began)
            measured=subprocess.run(['/usr/bin/time','-f','RSS_KIB=%M',*command(emulator)],input=boot+guest_input,capture_output=True,timeout=120,check=True)
            rss=int(measured.stderr.decode().split('RSS_KIB=')[-1])
        result=dict(active_copies=active,copy_bits=length,guest_ticks=args.ticks,vm1_ticks=physical,vm1_ticks_per_guest_tick=physical/args.ticks,compile_seconds=compile_seconds,code_bits=meta['code_bits'],data_bits=meta['data_bits'],host_bits=meta['host']['size'],guest_bits=65520,boot_bytes=meta['bootstrap_bytes'],rss_kib=rss,samples=samples,wall_median_seconds=statistics.median(s['wall_seconds'] for s in samples),legacy_wall_seconds=old,legacy_wall_median_seconds=statistics.median(old))
        result['process_slowdown_vs_legacy']=result['wall_median_seconds']/result['legacy_wall_median_seconds']
        result['variant']=args.variant;result['generation']=options
        result['workload']=workload;result['host_slots']=meta['host']['slots']
        result['guest_snapshot_sha256']=hashlib.sha256(full_snapshot).hexdigest()
        result['stdout_sha256']=hashlib.sha256(expected_stdout).hexdigest()
        result['bootstrap_ticks']=boot_ticks;result['bootstrap_wall_seconds']=startup
        result['bootstrap_wall_median_seconds']=statistics.median(startup)
        results.append(result);print(json.dumps(result,sort_keys=True),flush=True)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    metadata=dict(platform=platform.platform(),cpu=Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0].split(':',1)[1].strip(),vm1_sha256=hashlib.sha256(emulator.read_bytes()).hexdigest(),legacy_sha256=hashlib.sha256(legacy.read_bytes()).hexdigest(),repeats=args.repeats,notes='Physical count includes emulator bootstrap and optional boundary snapshot/report; logical ticks include vm2 seed/installer; no speed or FPGA area claims beyond these workloads.')
    metadata['compiler']=subprocess.check_output([os.environ.get('CC','cc'),'--version'],text=True).splitlines()[0]
    metadata['vm1_build_config']=(emulator.parent/'build-config').read_text() if (emulator.parent/'build-config').is_file() else None
    config=legacy.with_name(legacy.name+'.build-config')
    metadata['legacy_build_config']=config.read_text() if config.is_file() else None
    import copycode.vm1.optimize,copycode.vm1.schedule
    sources=list((ROOT/'vm2guest').glob('*.py'))+[Path(copycode.vm1.schedule.__file__),Path(copycode.vm1.optimize.__file__)]
    metadata['generator_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
if __name__=='__main__':main()
