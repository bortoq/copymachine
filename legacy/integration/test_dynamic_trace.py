"""Dynamic full/channel traces of repeated, patched layers and resume."""
import io,json,sys,tempfile,os,gzip,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'legacy/copy-space'
EMULATOR=Path(os.environ.get("SPACE_EMULATOR",str(ROOT.parent.parent/"space/vm2/space")))
sys.path.insert(0,str(ROOT/'modules'));sys.path.insert(0,str(ROOT/'tests'))
from rv32i import Layout, REGS
from rv32i_bulk import BulkImage
from rv32i_reference import execute
from checkpoint import execute_segments,digest
from dynamic_trace import audit,frames
from boundary import field

def addi(rd,rs,n):return(n&4095)<<20|rs<<15|rd<<7|0x13
def bne(rs,n):
 n&=8191
 return(n>>12&1)<<31|(n>>5&63)<<25|rs<<15|1<<12|(n>>1&15)<<8|(n>>11&1)<<7|0x63
words=[addi(5,0,2),addi(10,0,0),addi(11,0,1024),addi(12,0,2),addi(17,0,63),0x73,
       addi(12,10,0),addi(10,0,1),addi(17,0,64),0x73,addi(5,5,-1),bne(5,-40),addi(10,0,7),addi(17,0,93),0x73]
program=b''.join(w.to_bytes(4,'little') for w in words);data=b'A\0\xff'
base=Path('tmp/trace-tests');base.mkdir(exist_ok=True,parents=True)
out=Path(tempfile.mkdtemp(prefix='run-',dir=base));inp=out/'input';inp.write_bytes(data)
results={};all_events={}
for mode in ('full','channels'):
 raw,m=BulkImage(io=True,memory_bytes=65536,layout=Layout(8*1024*1024),segment_budget=7,trace=mode).build().encode(program)
 image=out/(mode+'.bin');image.write_bytes(raw)
 result=execute_segments(EMULATOR,image,m,inp,out/mode,max_segments=15)
 assert result['complete'] and result['terminal']['exit_code']==7
 assert result['terminal']['input_cursor']==3 and result['terminal']['output_cursor']==3
 assert (out/mode/'stdout.bin').read_bytes()==data
 cumulative={};events=[];homes={};copy_events=0
 for segment in result['segments']:
  path=Path(segment['path']);meta=json.loads((path/'checkpoint.json').read_text())
  local=[]
  with (path/'debug.bin').open('rb') as stream:summary=audit(stream,m,terminal=segment['terminal'],on_event=local.append)
  copy_events+=sum(e['type']=='copy' for e in local)
  events.extend((e['type'],e['committed'],e['slot'],e['n'],e['dst']>=m['boundary']['space_bits'],
                 e['src']>=m['boundary']['space_bits'],e['status']['moved'],e['status']['status'],e['status']['eof'])
                for e in local if e['type']=='channel')
  for k,v in summary.items():
   if isinstance(v,int):cumulative[k]=cumulative.get(k,0)+v
  assert cumulative==meta['trace_totals']
  with (path/'debug.bin').open('rb') as stream:
   for e in frames(stream,m):
    if e['type']=='layer':homes[e['home']]=homes.get(e['home'],0)+1
 assert max(homes.values())>1
 assert (copy_events>0)==(mode=='full')
 all_events[mode]=events
 final=(Path(result['checkpoint'])/'space.bin').read_bytes()
 oracle_io=dict(input=data,output=b'');expected,memory,fetch=execute(program,registers={2:65520},memory_bytes=65536,io=oracle_io)
 assert [field(final,REGS+j*32,32) for j in range(34)]==expected[-1]
 start=m['guest_memory_bit']//8;assert final[start:start+65536]==memory
 results[mode]=(result,m,cumulative)
 print('OK',mode,'dynamic trace:',cumulative,flush=True)
assert all_events['full']==all_events['channels']
for key in ('layers','copies','monitor_copies','data_ops','sys_ops','input_bytes','output_bytes'):
 assert results['full'][2][key]==results['channels'][2][key],key
assert [e[6] for e in all_events['full']]==[2,2,1,1]
# Streaming parser accepts arbitrarily fragmented reads and rejects truncation.
r,m,_=results['channels'];first=Path(r['segments'][0]['path']);trace=(first/'debug.bin').read_bytes()
class Short(io.BytesIO):
 def read(self,n=-1):return super().read(min(n,1))
assert audit(Short(trace),m)==json.loads((first/'checkpoint.json').read_text())['trace_audit']
for invalid in (trace[:-1],trace[:-100],trace+trace,trace.replace(b'PCS2',b'PCS9',1)):
 try:audit(io.BytesIO(invalid),m)
 except ValueError:pass
 else:raise AssertionError('invalid trace accepted')
# Restore a traced checkpoint and re-audit ancestry, then detect damaged trace.
fork=execute_segments(EMULATOR,out/'channels.bin',m,inp,out/'fork',
                      checkpoint_from=first,max_segments=15)
assert fork['complete'] and (out/'fork/stdout.bin').read_bytes()==data
assert digest(Path(fork['checkpoint'])/'space.bin')==digest(Path(r['checkpoint'])/'space.bin')
print('OK full/channels agree, partial IO, streaming audit, truncated/corrupt trace rejection, resume/fork',flush=True)
print('Artifacts:',out,flush=True)

# The consumer auditor reads raw and compressed PCS2; legacy dispatch is explicit.
from space_trace_audit import audit_copycode_trace,audit_trace
compressed=out/'first.pcs2.gz'
with gzip.open(compressed,'wb') as target:target.write(trace)
assert audit_copycode_trace(compressed,m)==audit_copycode_trace(first/'debug.bin',m)
assert audit_trace(compressed,boundary_manifest=m,channels_only=True)[2]==b'stop limit\n'
from space_segments import execute_segments as consumer_segments
consumer=consumer_segments(EMULATOR,out/'consumer-fork',inp,
    space_bytes=m['boundary']['image_bytes'],layer_bytes=m['layer_bits']//8,
    ticks=None,timeout=120,compression='raw',initial_core=out/'channels.bin',
    max_parts=15,channels_only=True,fork_from=first,boundary_manifest=m)
assert consumer['complete'] and (out/'consumer-fork/stdout.bin').read_bytes()==data
command=[sys.executable,'-B',str(ROOT/'scripts/rv32i/run.py'),str(out/'channels.bin'),
    '--new-emulator','--in',str(inp),'--segments',str(out/'cli'),'--max-segments','15',
    '--trace',str(out/'trace-index.json'),'--space',str(EMULATOR)]
# run.py reads a build sidecar, exactly as the normal build CLI writes it.
(out/'channels.bin.json').write_text(json.dumps(m))
cli=subprocess.run(command,capture_output=True,timeout=120)
assert cli.returncode==7,cli
index=json.loads((out/'trace-index.json').read_text())
assert index['format']=='PCS2-index-v1' and index['segments'][-1]['totals']==results['channels'][2]
# Resource accounting belongs to the ordinary launcher.
first_meta=json.loads((first/'checkpoint.json').read_text())
assert first_meta['resources']['boot_ticks']>0 and first_meta['resources']['child_peak_rss_kib']>0
print('OK compressed auditor, consumer segment adapter, CLI trace index and resource accounting',flush=True)
