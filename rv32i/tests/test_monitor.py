"""Commit checkpoints resume stored code; external input uses saved byte counters."""
import hashlib,json,os,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
import dependencies
from direct_target import compile_image
from vm2compile.artifact import save,resume
from rv32i_reference import execute

def get(raw,at,n):return sum(((raw[(at+k)//8]>>(7-(at+k)%8))&1)<<k for k in range(n))
def add(rd,value):return ((value&4095)<<20)|(rd<<7)|0x13
words=[0x73,add(10,0),0x73,add(17,93),add(10,0),0x73]
program=b''.join(w.to_bytes(4,'little') for w in words);data=b'ABCD'
regs={10:0,11:512,12:2,17:63}
io={'input':data};expected,memory,_=execute(program,regs,io=io)
payload,m=compile_image(program,registers=regs,checkpoint_every=1,frames=True)
mapping=json.loads(payload['map.json']);reg=mapping['regions']['registers']['at'];mem=mapping['regions']['guest']['at'];scratch=mapping['regions']['scratch']['at']
checked=Path(os.environ.get('CHECKED_VM1',dependencies.VM2_ROOT/'build/checked-vm1'))
frames=[];segments=[];consumed=0
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);original=folder/'original';save(original,payload,m);current=original
    for index in range(10):
        snap=folder/('snapshot-'+str(index))
        args=['sh','-c','exec "$1" -s "$2" -p "$3" 4>"$4"','monitor',str(checked),str(m['vm1']['size']),str(m['vm1']['slots']),str(snap)]
        r=subprocess.run(args,input=payload['boot.bin']+data[consumed:],capture_output=True,timeout=20)
        assert r.returncode==0 and r.stdout==b'',(index,r.returncode,r.stderr[-1000:])
        raw=snap.read_bytes();assert len(raw)==len(payload['image.bin'])
        debug=re.sub(rb'VM1_AUDIT_TICKS=\d+\n$',b'',r.stderr)
        assert len(debug)==136,(index,'one committed/final frame per segment',len(debug))
        frames.append([get(debug,k*32,32) for k in range(34)])
        consumed=get(raw,scratch+m['rv32i']['monitor_offsets']['input_bytes'],32)
        count=get(raw,scratch+m['rv32i']['monitor_offsets']['committed'],32)
        status=get(raw,reg+m['rv32i']['status_offset'],32)
        segments.append(dict(index=index,input_bytes=consumed,committed=count,status=status,snapshot_sha256=hashlib.sha256(raw).hexdigest(),audit=r.stderr[-50:].hex()))
        if status:
            assert status==10 and consumed==4
            assert raw[mem//8:mem//8+65536]==memory
            break
        assert count==index+1
        payload,m=resume(current,snap)
        current=folder/('resume-'+str(index));save(current,payload,m)
    else:raise AssertionError('monitor did not finish')
assert frames==expected,(frames,expected)
out=ROOT/'build/verification';out.mkdir(parents=True,exist_ok=True)
(out/'monitor.json').write_text(json.dumps(segments,indent=2)+'\n')
print('PASS RV32I monitor: six segments, commit frames, input cursors, source-free resume, final guest memory')
