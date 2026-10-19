#!/usr/bin/env python3
"""Standalone self-patched copycode, streaming PCS2 audit and exact clocks."""
import io
import copy
import errno
from pathlib import Path
import os
import random
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
EMULATOR = Path(os.environ.get('SPACE_EMULATOR', ROOT.parent/'vm2/space')).resolve()
sys.path.insert(0,str(ROOT/'compat/vm2'))
from boundary import Format,field as slow_field,protocol,record
from terminal import TerminalFragment,numeric
from dynamic_trace import instrument,audit,field
from checkpoint import execute_segments
from transport import run_stream

rng=random.Random(412)
for _ in range(400):
    data=rng.randbytes(40);at=rng.randrange(80);width=rng.randrange(1,121)
    assert field(data,at,width)==slow_field(data,at,width)

with tempfile.TemporaryDirectory() as directory:
    tmp=Path(directory);input_path=tmp/'input';input_path.write_bytes(b'')
    comparisons=[]
    for mode in ('full','channels'):
        f=Format(262128,32);image=bytearray(2048)
        a,b,c,halt,cp=[i*f.layer_bits for i in range(1,6)]
        src1,src2,dst1,dst2=11000,11008,12000,12008
        committed,reads,writes,inp,out,remain,reload,status=range(14000,14512,64)
        image[src1//8:src1//8+2]=b'AB'
        image[committed//8:committed//8+8]=numeric(1,64)
        image[reload//8:reload//8+4]=numeric(1,32)
        image[status//8:status//8+4]=numeric(10,32)
        pointer=13000;image[pointer//8:pointer//8+8]=numeric(src2,64)
        def layer(home,rows,target):
            rows=list(rows)+[(0,0,0)]*(f.slots-1-len(rows))+[(f.layer_bits,0,target)]
            image[home//8:home//8+f.layer_bytes]=f.layer(rows)
        shared=dict(snapshot=True,input_cursor_address=inp,output_cursor_address=out,
                    guest_status_address=status,counter_addresses=dict(committed=committed,read_ops=reads,write_ops=writes),
                    phase_markers=True)
        checkpoint=TerminalFragment(f.space_bits,f.slots,len(image)*8,reason='limit',
             continuation=[(32,remain,reload),(f.layer_bits,0,c)],**shared)
        image.extend(checkpoint.data)
        final=TerminalFragment(f.space_bits,f.slots,len(image)*8,**shared);image.extend(final.data)
        layer(a,[(8,dst1,src1)],b)
        layer(b,[(f.a,c+f.z+f.a,pointer)],cp)
        layer(c,[(8,dst2,src1)],halt)
        layer(halt,[],final.entry);layer(cp,[],checkpoint.entry)
        manifest=dict(boundary=f.description,processor_n=f.slots,layer_bits=f.layer_bits,status_bit=status,
            labels=dict(start=a,patch=b,fetch=c,halt=halt,monitor_report=cp),monitor=dict(
            format='rv32i-commit-v1',segment_budget=1,remaining_bit=remain,reload_bit=reload,
            input_cursor_bit=inp,output_cursor_bit=out,counters_bit=dict(committed=committed,read_ops=reads,write_ops=writes),
            checkpoint_entry=checkpoint.entry,final_entry=final.entry,
            checkpoint_snapshot_entry=checkpoint.snapshot_entry,continuation_hex=f.layer([(f.layer_bits,0,c)]).hex(),
            checkpoint_report_ticks=checkpoint.report_ticks,final_report_ticks=final.report_ticks,final_snapshot=True))
        unwrapped=bytes(image);unwrapped_manifest=copy.deepcopy(manifest)
        instrument(image,manifest,[(a,0),(b,0),(c,0),(halt,2),(cp,1)],[],mode=mode,initial_label='start')
        path=tmp/(mode+'.bin');path.write_bytes(image)
        first=execute_segments(EMULATOR,path,manifest,input_path,tmp/(mode+'-first'))
        assert not first['complete']
        final_run=execute_segments(EMULATOR,None,manifest,input_path,tmp/(mode+'-end'),checkpoint_from=first['checkpoint'])
        assert final_run['complete']
        raw=(Path(final_run['checkpoint'])/'space.bin').read_bytes()
        assert raw[dst1//8:dst1//8+2]==b'AB'
        events=[];counts=0
        for run in (first,final_run):
            with (Path(run['checkpoint'])/'debug.bin').open('rb') as stream:
                summary=audit(stream,manifest,terminal=run['terminal'],on_event=events.append)
                counts+=summary['copies']
        assert counts==3
        if mode=='full':assert any(e['type']=='copy' and e['home']==c and e['src']==src2 for e in events)
        else:assert not any(e['type']=='copy' for e in events)
        comparisons.append(counts)
        # The exact physical clock includes the bootstrap, wrapper and report.
        metadata=__import__('json').loads((Path(first['checkpoint'])/'checkpoint.json').read_text())
        ticks=metadata['resources']['boot_ticks']+metadata['trace_audit']['physical_ticks']
        for delta,valid in ((0,True),(-1,False)):
            try:
                debug=io.BytesIO()
                result=run_stream(EMULATOR,io.BytesIO(image),f.space_bits,f.slots,ticks=ticks+delta,debug=debug)
                audit(io.BytesIO(debug.getvalue()),manifest,terminal=result.terminal)
            except ValueError:
                assert not valid
            else:assert valid and result.terminal['kind']=='checkpoint'
    assert comparisons==[3,3]
    raw=bytearray((Path(first['checkpoint'])/'space.bin').read_bytes())
    raw[status//8:status//8+4]=numeric(2,32)
    debug=io.BytesIO()
    result=run_stream(EMULATOR,io.BytesIO(raw),f.space_bits,f.slots,debug=debug)
    assert audit(io.BytesIO(debug.getvalue()),manifest,terminal=result.terminal)['stop']['outcome']=='error'

    # SYS replies must survive monitor interposition. A closed data device
    # gives an actual EBADF result, captured by the tracer's post-data FSTAT.
    image=bytearray(unwrapped);manifest=copy.deepcopy(unwrapped_manifest)
    ops,req,rsp=protocol(f.space_bits)
    request=record(req,dict(op=ops['CLOSE'],chan=f.devices['stdout']))
    image[pointer//8:pointer//8+len(request)]=request
    answer=13200
    layer(a,[(req[1],f.space_bits,pointer)],b)
    layer(b,[(rsp[1],answer,f.space_bits)],c)
    layer(c,[(8,f.devices['stdout'],src1)],halt)
    instrument(image,manifest,[(a,0),(b,0),(c,0),(halt,2),(cp,1)],[],mode='full',initial_label='start')
    debug=io.BytesIO();snapshot=io.BytesIO()
    result=run_stream(EMULATOR,io.BytesIO(image),f.space_bits,f.slots,debug=debug,snapshot=snapshot)
    events=[];audit(io.BytesIO(debug.getvalue()),manifest,terminal=result.terminal,on_event=events.append)
    failed=[e for e in events if e['type']=='channel']
    assert len(failed)==1 and failed[0]['status']['status']==errno.EBADF and failed[0]['status']['moved']==0
    assert slow_field(snapshot.getvalue(),answer+rsp[0]['op'][0],rsp[0]['op'][1])==ops['CLOSE']
    assert slow_field(snapshot.getvalue(),answer+rsp[0]['status'][0],rsp[0]['status'][1])==0
print('dynamic trace: patched operands, SYS isolation/IO errors, parity, resume, decoder and exact clocks passed')
