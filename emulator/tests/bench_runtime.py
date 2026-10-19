#!/usr/bin/env python3
"""Optional real-process and actual cycle benchmark; JSON/CSV under build/."""
import csv
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from runtime_codec import copy, layer, program
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from output_paths import output_dir

OUT=output_dir(ROOT, 'build')/'measurements'

def measure(binary, packet, ticks, expected):
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    start=time.perf_counter()
    result=subprocess.run([str(binary),'-s','65520','-p','8','-t',str(ticks)],input=packet,capture_output=True,check=True)
    elapsed=time.perf_counter()-start
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    assert result.stdout==expected and not result.stderr
    # GNU time launches from a small C parent, avoiding the Python parent's
    # inherited RSS floor. Memory is a separate, equally checked process run.
    with tempfile.TemporaryDirectory(prefix='emulator-rss-') as directory:
        report=Path(directory)/'rss'
        memory_run=subprocess.run(['/usr/bin/time','-f','%M','-o',str(report),str(binary),
                                   '-s','65520','-p','8','-t',str(ticks)],
                                  input=packet,capture_output=True,check=True)
        assert memory_run.stdout==expected and not memory_run.stderr
        rss=int(report.read_text().strip())
    return dict(wall_s=elapsed,cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                maxrss_kib=rss)
if len(sys.argv)>1 and sys.argv[1]=='--child':
    variant,fixture=sys.argv[2:]
    if fixture=='startup':
        packet=layer([],65520,8);ticks=1;expected=b''
    else:
        packet,clocks=program([[copy(8,65522,24000,65520)]],data=[(24000,b'A')])
        ticks=clocks+1;expected=b'A'
    print(json.dumps(measure(output_dir(ROOT, 'build')/f'{variant}/emulator',packet,ticks,expected)))
    raise SystemExit
OUT.mkdir(parents=True,exist_ok=True)
metadata={'compiler':subprocess.check_output([os.environ.get('CC','cc'),'--version'],text=True).splitlines()[0],
          'flags':os.environ.get('CFLAGS',''), 'process_rounds':7,
          'core_rounds':5, 'core_cycles_per_round':16,
          'cpu':next((s.split(':',1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')),'unknown')}
(OUT/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
rows=[]
rng=random.Random(19019)
for round in range(7):
    tasks=[(v,f) for v in ['bitcopy','network'] for f in ['startup','output']]
    rng.shuffle(tasks)
    for variant,fixture in tasks:
        result=subprocess.check_output([sys.executable,'-B',__file__,'--child',variant,fixture],text=True)
        rows.append(dict(round=round,variant=variant,fixture=fixture,**json.loads(result)))
with (OUT/'process.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
summary={}
for variant in ['bitcopy','network']:
    output=subprocess.check_output([str(output_dir(ROOT, 'build')/f'{variant}/bench_core')],text=True)
    (OUT/f'{variant}-core.csv').write_text('fixture,round,seconds_per_cycle\n'+output)
    summary[variant]={}
    for fixture in ['startup','output']:
        vals=[row for row in rows if row['variant']==variant and row['fixture']==fixture]
        summary[variant][fixture]={k:statistics.median(v[k] for v in vals) for k in ['wall_s','cpu_s','maxrss_kib']}
    core=list(csv.DictReader(('fixture,round,seconds_per_cycle\n'+output).splitlines()))
    summary[variant]['cycles_ms']={str(i):1000*statistics.median(float(x['seconds_per_cycle']) for x in core if x['fixture']==str(i)) for i in range(4)}
    summary[variant]['binary_bytes']=(output_dir(ROOT, 'build')/f'{variant}/emulator').stat().st_size
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
