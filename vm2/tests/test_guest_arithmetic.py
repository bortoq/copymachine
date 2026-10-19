"""Real vm1 execution of blocked prefix arithmetic, checked independently."""
import os,random,re,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vm2guest.assembler import Assembler,Reg
from copycode.vm1.machine import Format
from copycode.vm1.boot import boot_stream

root=Path(__file__).resolve().parents[1]
binary=Path(os.environ.get('CHECKED_VM1',root/'build/checked-vm1'))
rng=random.Random(51503)
for scheduling in ('schedule','optimize'):
    f=Format((1<<26)-16,8);b=Assembler(f,1<<24,1<<25,scheduling=scheduling,arithmetic='prefix')
    output=b.alloc(8192);expected=[];offset=0
    for width in (1,2,3,4,5,7,8,15,16,17,24,31,32,63,64):
        mask=(1<<width)-1
        for case in range(6):
            x,y=(mask,1) if case==0 else (rng.getrandbits(width),rng.getrandbits(width))
            left=b.alloc(width,value=x);right=b.alloc(width,value=y)
            out=left if case==1 else right if case==2 else b.alloc(width)
            carry=b.alloc(1)
            # Exercise constants, zero/trailing zeros, negative increments,
            # register operands and both in-place destinations.
            operand=right
            if case>=3:
                operand=(0,4,-1)[case-3];y=operand&mask
            b.add(left.at,operand,out.at,width,carry.at)
            b.copy(width,output.at+offset,out.at);b.copy(1,output.at+offset+width,carry.at)
            expected.extend(((x+y)>>k)&1 for k in range(width))
            expected.append(int(x+y>mask));offset+=width+1
    b.emit([f.copy((offset+7)//8*8,f.size+2,output.at)],fence=True)
    b.emit(next=False,fence=True)
    image,meta=b.assemble()
    result=subprocess.run([str(binary),'-s',str(f.size),'-p8'],input=boot_stream(image,f),capture_output=True,timeout=30)
    assert result.returncode==0,(scheduling,result.stderr[-2000:])
    assert re.fullmatch(rb'VM1_AUDIT_TICKS=\d+\n',result.stderr),result.stderr
    bits=[(result.stdout[k//8]>>(7-k%8))&1 for k in range(offset)]
    assert bits==expected,(scheduling,next((i,x,y) for i,(x,y) in enumerate(zip(bits,expected)) if x!=y))
    print('PASS',scheduling,'90 prefix additions: widths 1..64, carries, constants, in-place, audited vm1',flush=True)
