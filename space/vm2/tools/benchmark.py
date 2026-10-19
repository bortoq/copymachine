#!/usr/bin/env python3
"""Standalone core benchmarks: fetch/copy density, bit alignment, channel IO.

No application generators or neighboring repositories are imported.
CPU/wall measurements include launch/boot; boot-only runs are retained.
Raw wait4 peak RSS can include the pre-exec parent's memory.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

from boundary import Format, iter_boot

def median(rows):
    return {k:statistics.median(r[k] for r in rows) for k in rows[0]}


def fixed_resource_run(command,chunks):
    """Finite primitive microbenchmarks; caller supplies exact ordinary input."""
    r,w=os.pipe();started=time.monotonic()
    null=os.open(os.devnull,os.O_WRONLY)
    actions=[(os.POSIX_SPAWN_DUP2,r,0),(os.POSIX_SPAWN_DUP2,null,1)]
    pid=os.posix_spawn(str(command[0]),list(map(str,command)),os.environ,file_actions=actions)
    os.close(r);os.close(null)
    try:
        for data in chunks:
            view=memoryview(data)
            while view:
                n=os.write(w,view);view=view[n:]
    except BrokenPipeError:pass
    finally:os.close(w)
    _,status,usage=os.wait4(pid,0)
    if os.waitstatus_to_exitcode(status):raise ValueError('microbenchmark failed')
    return dict(wall_seconds=time.monotonic()-started,child_user_seconds=usage.ru_utime,
                child_system_seconds=usage.ru_stime,child_peak_rss_kib=usage.ru_maxrss)


def microbench(emulator,repeats,ticks):
    results=[]
    def add_case(case,packet,f):
        boot=[fixed_resource_run([emulator,'-s',f.space_bits,'-p',f.slots,'-t',len(packet)],packet)
              for _ in range(repeats)]
        case['boot_runs']=boot;case['boot_median']=median(boot)
        total=case['median']['child_user_seconds']+case['median']['child_system_seconds']
        base=case['boot_median']['child_user_seconds']+case['boot_median']['child_system_seconds']
        case['compute_cpu_estimate_seconds']=total-base
        results.append(case)
    for bits in (65520,8*1024*1024*8-6):
        for slots in (64,256):
            f=Format(bits,slots)
            for active in (0,slots-1):
                home=f.layer_bits;source=bits-2*slots-64;dst=source+slots
                rows=[(1,dst+i,source+i) for i in range(active)]
                rows += [(0,0,0)]*(slots-1-len(rows))+[(f.layer_bits,0,home)]
                raw=f.layer(rows)*2
                packet=list(iter_boot(io.BytesIO(raw),bits,slots))
                runs=[fixed_resource_run([emulator,'-s',bits,'-p',slots,'-t',len(packet)+ticks],packet)
                      for _ in range(repeats)]
                add_case(dict(kind='fetch-copy',address_bits=f.a,slots=slots,active_data_copies=active,
                                    body_ticks=ticks,active_copies=ticks*active,runs=runs,median=median(runs)),packet,f)
    bits=8*1024*1024*8-6;f=Format(bits,8)
    for width in (1024,65536):
        for offset in (0,3):
            home=f.layer_bits;source=2*1024*1024+offset;dst=4*1024*1024+offset
            rows=[(width,dst,source),(f.layer_bits,0,home)]
            raw=f.layer(rows)*2
            packet=list(iter_boot(io.BytesIO(raw),bits,8))
            runs=[fixed_resource_run([emulator,'-s',bits,'-p',8,'-t',len(packet)+ticks],packet)
                  for _ in range(repeats)]
            add_case(dict(kind='bitcopy',bits_per_copy=width,offset_bits=offset,body_ticks=ticks,
                                payload_bits=width*ticks,runs=runs,median=median(runs)),packet,f)
    # Alternating read/write layers: one device exchange per tick.
    bits=8*1024*1024*8-6;f=Format(bits,8);block=4096;rounds=max(1,ticks//20)
    read_home=f.layer_bits;write_home=2*f.layer_bits;buf=8*f.layer_bits
    read=f.layer([(block*8,buf,f.devices['stdin']),(f.layer_bits,0,write_home)])
    write=f.layer([(block*8,f.devices['stdout'],buf),(f.layer_bits,0,read_home)])
    raw=read+read+write;packet=list(iter_boot(io.BytesIO(raw),bits,8))
    def input_chunks():
        yield from packet
        for _ in range(rounds):yield bytes(block)
    runs=[fixed_resource_run([emulator,'-s',bits,'-p',8,'-t',len(packet)+rounds*2],input_chunks())
          for _ in range(repeats)]
    add_case(dict(kind='channel-roundtrip',block_bytes=block,rounds=rounds,input_bytes=rounds*block,
                        output_bytes=rounds*block,runs=runs,median=median(runs)),packet,f)
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--micro-only',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--emulator',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--micro-ticks',type=int,default=100000)
    args=parser.parse_args()
    if args.repeats<1 or args.micro_ticks<1:parser.error('positive repetitions/ticks required')
    args.emulator=args.emulator.resolve()
    root=Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True,exist_ok=False)
    sources=['VERSION','proto.def','proto_gen.h','space.c','space.h','engine.c',
             'config.c','sys_ctrl.c','sys_ctrl.h','globals.c','bitcopy.c',
             'tools/benchmark.py','tools/schedule.py','tools/boundary.py','tools/machine.py']
    sources=['tests/reference/'+n if n in {'proto.def','proto_gen.h','space.c','space.h','engine.c','config.c','sys_ctrl.c','sys_ctrl.h','globals.c','bitcopy.c'} else n for n in sources]
    environment=dict(platform=platform.platform(),python=sys.version,
        emulator=str(args.emulator),emulator_sha256=hashlib.sha256(args.emulator.read_bytes()).hexdigest(),
        repeats=args.repeats,micro_ticks=args.micro_ticks,
        release_version=(root/'VERSION').read_text().strip(),
        memory_intervals='pairwise disjoint sources and destinations',
        rss_source='raw wait4 peak; may include pre-exec parent memory; not emulator-only RSS',
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in sources})
    settings=Path(str(args.emulator)+'.build-config')
    environment['build_config']=settings.read_text().splitlines() if settings.exists() else None
    if settings.exists():
        import shlex
        import subprocess
        compiler=shlex.split(environment['build_config'][0])
        environment['compiler_version']=subprocess.check_output(compiler+['--version'],text=True).splitlines()[0]
    report=dict(schema='space-core-bench-v3',environment=environment,
                micro=microbench(args.emulator,args.repeats,args.micro_ticks))
    (args.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Results:',args.output/'results.json',flush=True)


if __name__=='__main__':main()
