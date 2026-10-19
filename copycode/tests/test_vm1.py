"""Real CLI and independent snapshot oracle; no import of emulator/test APIs."""
import io,json,os,random,subprocess,tempfile
from pathlib import Path
from copycode.vm1.machine import Format,field
from copycode.vm1.program import Program
from copycode.vm1.boot import boot_stream,iter_boot
from copycode.vm1.lib import add8,reverse_byte
from copycode.vm1 import checkpoint,monitor
from copycode.vm1.sys import fstat,record

ROOT=Path(__file__).resolve().parents[1]
VM1=Path(os.environ.get('VM1',ROOT.parent/'vm1/vm1')).resolve()
NETWORK=Path(os.environ.get('VM1_NETWORK',ROOT.parent/'vm1/build/network/vm1')).resolve()
PROTO=Path(os.environ.get('VM1_PROTO',ROOT.parent/'vm1/src/proto.def')).resolve()
f=Format()

def execute(image,limit=1000):
    """Independent bitwise snapshot machine checking every executed operand."""
    memory=bytearray(image);out=bytearray();cycles=0
    while cycles<limit:
        a=f.size.bit_length()
        # Decode manually, without Format.decode, and check pairwise sets.
        rows=[];positions=[]
        for i in range(f.slots):
            row=[]
            for k in range(4):
                at=(i*4+k)*a
                row.append(sum(((memory[(at+j)//8]>>(7-(at+j)%8))&1)<<j for j in range(a)))
            dl,dh,sl,sh=row
            if dl==dh and dl>=f.size:
                if sl==sh:continue
                positions.append(set(range(sl,sh)))
            elif sl==sh and sl>=f.size:
                if dl==dh:continue
                positions.append(set(range(dl,dh)))
            elif sl==sh:continue
            else:
                assert dh-dl==sh-sl>0
                positions.extend([set(range(dl,dh)),set(range(sl,sh))])
            rows.append(row)
        if not rows:break
        assert all(not(x&y) for i,x in enumerate(positions) for y in positions[i+1:]),rows
        before=bytes(memory)
        for dl,dh,sl,sh in rows:
            if dl>=f.size:
                assert dl==f.channels['stdout']
                for offset in range(0,sh-sl,8):
                    out.append(sum(((before[(sl+offset+k)//8]>>(7-(sl+offset+k)%8))&1)<<(7-k) for k in range(8)))
            else:
                assert sl<f.size
                for offset in range(dh-dl):
                    mask=128>>((dl+offset)%8)
                    bit=(before[(sl+offset)//8]>>(7-(sl+offset)%8))&1
                    memory[(dl+offset)//8]=(memory[(dl+offset)//8]&~mask)|(mask if bit else 0)
        cycles+=1
    else:raise AssertionError('oracle did not halt')
    return memory,bytes(out)

def run(program,binary=VM1,input_data=b''):
    with tempfile.TemporaryDirectory() as name:
        folder=Path(name);status=folder/'status';snapshot=folder/'snapshot'
        packet=program.boot()+input_data
        command=['sh','-c','exec "$1" -s "$2" -p "$3" 3>"$4" 4>"$5"',
                 'copycode-test',str(binary),str(program.fmt.size),str(program.fmt.slots),str(status),str(snapshot)]
        result=subprocess.run(command,input=packet,capture_output=True,timeout=30)
        assert result.returncode==0,(binary,result.stderr)
        return result.stdout,result.stderr,status.read_bytes(),snapshot.read_bytes()

# Independent all-pairs test, including channel buffers and SYS implicit width.
rng=random.Random(2811)
for _ in range(6000):
    triples=[(rng.randrange(9),rng.randrange(48),rng.randrange(48)) for _ in range(rng.randrange(1,7))]
    rows=[f.copy(*t) for t in triples]
    spans=[set(range(p,p+n)) for n,d,s in triples if n for p in (d,s)]
    expected=all(not(x&y) for i,x in enumerate(spans) for y in spans[i+1:])
    try:f.validate(rows);actual=True
    except ValueError:actual=False
    assert actual==expected
for rows in [[f.copy(8,1000,f.channels['stdin']),f.copy(8,2000,f.channels['stdin'])],
             [(f.size+1,f.size+1,f.size+2,f.size+2)],
             [f.copy(1,1000,f.channels['stdin'])],
             [f.copy(8,f.size,1000),f.copy(8,2000,1050)],
             [f.copy(8,1000,2000),f.copy(8,3000,2000)]]:
    try:f.validate(rows)
    except ValueError:pass
    else:raise AssertionError(rows)
print('PASS 6000 independent schedules and invalid channel/SYS/fan-out cases')

for binary in (VM1,NETWORK):
    assert binary.is_file(),binary
    for value in [0,1,128,165,255]:
        p=Program();p.store(44000,bytes([value]))
        for rows in reverse_byte(f,44008,44000):p.layer(rows)
        for rows in reverse_byte(f,44016,44008):p.layer(rows)
        p.layer([f.copy(8,f.channels['stdout'],44016)])
        memory,expected=execute(p.image());actual=run(p,binary)
        assert actual==(bytes([value]),b'',b'',b''),(binary,actual)
        assert expected==actual[0]
    for a,b in [(0,0),(255,1),(127,128),(255,255),(69,207)]:
        p=Program();layout=add8(p);p.store(layout['left'],bytes([a,b]))
        p.layer([f.copy(8,f.channels['stdout'],layout['result'])])
        expected,_=execute(p.image());got=run(p,binary)
        assert got==(bytes([(a+b)&255]),b'',b'',b''),(a,b,got)
        assert expected[layout['result']//8]==(a+b)&255
    # Input is used on a later tick. Snapshot observes every memory byte.
    p=Program();p.layer([f.copy(24,44000,f.channels['stdin'])])
    p.layer([f.copy(24,f.channels['stdout'],44000)])
    monitor.emit(p,44000,24);monitor.status(p,47000,7)
    checkpoint.snapshot(p,48000,[f.copy(24,f.channels['stdout'],44000),f.copy(f.layer_bits,0,4096)])
    out,debug,status,saved=run(p,binary,b'ABCtail')
    assert out==b'ABC' and debug==b'ABC' and status==b'VMS1\x07\0\0\0'
    assert len(saved)==f.image_bytes and saved[44000//8:44000//8+3]==b'ABC'
    q=Program();q.boot=lambda:boot_stream(saved,f)
    resumed=run(q,binary)
    assert resumed==(b'ABC',b'',b'',b''),resumed
    # Completion -> FSTAT request -> committed reply -> output reply.
    p=Program();p.layer([f.copy(40,44000,f.channels['stdin'])])
    m=fstat(p,f.channels['stdin'],45000,46000,PROTO)
    p.layer([f.copy((m+7)//8*8,f.channels['stdout'],46000)])
    reply=run(p,binary,b'XY')[0]
    assert field(reply,96,f.a)==2 and field(reply,96+f.a,1)==1,reply.hex()
    print('PASS actual',binary,'pack/add8/IO/SYS/status/snapshot/resume')

for _ in range(64):
    a,b=rng.randrange(256),rng.randrange(256)
    p=Program();layout=add8(p);p.store(layout['left'],bytes([a,b]))
    memory,_=execute(p.image())
    assert memory[layout['result']//8]==(a+b)&255
print('PASS 64 randomized full-memory independent add8 executions')

# Entire snapshot compared to independent whole-memory result, including patched code.
p=Program();layout=add8(p);p.store(layout['left'],b'\xef\x38')
p.layer([f.copy(8,f.channels['stdout'],layout['result'])])
# Snapshot continuation NOP. Its code and entry record are part of reference memory.
checkpoint.snapshot(p,48000)
image=p.image()
# Independent model uses stdout for snapshot channels, leaving its data semantics unchanged.
reference=bytearray(image)
for i in range(len(p.layers)):
    at=i*f.layer_bits//8
    rows=f.decode(reference[at:at+f.layer_bytes])
    for row in rows:
        if row[0]==row[1]==f.channels['snapshot']:
            # Patch only the wire channel words in reference.
            from copycode.vm1.machine import put
            slot=rows.index(row)
            put(reference,i*f.layer_bits+slot*4*f.a,f.a,f.channels['stdout'])
            put(reference,i*f.layer_bits+(slot*4+1)*f.a,f.a,f.channels['stdout'])
expected_memory,all_output=execute(reference)
# Patched reference descriptors differ in non-processor memory; restore those words
# from actual image, while retaining dynamically patched add8 endpoint fields.
for i in range(len(p.layers)):
    at=i*f.layer_bits
    original=f.decode(image[at//8:at//8+f.layer_bytes])
    for slot,row in enumerate(original):
        if row[0]==row[1]==f.channels['snapshot']:
            for k in (0,1):put(expected_memory,at+(slot*4+k)*f.a,f.a,row[k])
for binary in (VM1,NETWORK):
    actual=run(p,binary)
    assert actual[0]==all_output[:1]
    assert actual[3][:f.layer_bytes]==bytes(f.layer_bytes)
    assert actual[3][f.layer_bytes:]==expected_memory[f.layer_bytes:]
print('PASS complete snapshot bytes including self-modified code on both backends')

for bits,slots in [(1048576,8),(65520,128)]:
    fmt=Format(bits,slots);image=bytearray(fmt.image_bytes)
    image[:fmt.layer_bytes]=fmt.layer([fmt.copy(8,fmt.channels['stdout'],bits-8),fmt.copy(fmt.layer_bits,0,fmt.layer_bits)])
    image[-1]=0xA5
    packet=b''.join(iter_boot(io.BytesIO(image),fmt,chunk_bytes=37))
    result=subprocess.run([str(VM1),'-s',str(bits),'-p',str(slots)],input=packet,capture_output=True,timeout=10)
    assert result.returncode==0 and result.stdout==b'\xa5',result
print('PASS streaming multi-chunk boot on different layouts')
