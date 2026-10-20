"""Physical emulator ticks per RV32I instruction class on the direct image.

Each class runs 64 copies of one instruction followed by EBREAK; the cost of a
lone EBREAK is subtracted. The audited emulator checks every tick's operands,
so a result is also an execution check. Ticks do not depend on CPU load.
"""
import argparse,json,os,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
import dependencies
from direct_target import compile_image
from vm2compile.artifact import seal
from copycode.hostpaths import output_dir

def put(data,at,width,value):
    for k in range(width):
        mask=128>>((at+k)%8);data[(at+k)//8]=(data[(at+k)//8]&~mask)|(mask if value>>k&1 else 0)
def i(f=0,rd=3,rs=1,imm=0,op=0x13):return ((imm&4095)<<20)|(rs<<15)|(f<<12)|(rd<<7)|op
def r(f=0,rd=3,a=1,b=2,hi=0):return (hi<<25)|(b<<20)|(a<<15)|(f<<12)|(rd<<7)|0x33
def s(f=2,a=1,b=2,imm=0):return ((imm&4095)>>5<<25)|(b<<20)|(a<<15)|(f<<12)|((imm&31)<<7)|0x23
def br(f=0,a=1,b=2,off=4):return ((off>>12&1)<<31)|((off>>5&63)<<25)|(b<<20)|(a<<15)|(f<<12)|((off>>1&15)<<8)|((off>>11&1)<<7)|0x63
def jal(rd=0,off=4):return ((off>>20&1)<<31)|((off>>1&1023)<<21)|((off>>11&1)<<20)|((off>>12&255)<<12)|(rd<<7)|0x6f
EBREAK=0x100073
CASES={'addi':i(),'add':r(),'sub':r(hi=32),'xor':r(4),'and':r(7),'slt':r(2),'sltu':r(3),
       'slli 1':i(1,imm=1),'slli 31':i(1,imm=31),'srai 7':i(5,imm=1024|7),'sll':r(1),
       'lui':(0x12345<<12)|(3<<7)|0x37,'auipc':(1<<12)|(3<<7)|0x17,
       'lw':i(2,rs=5,op=0x03),'lb':i(0,rs=5,op=0x03),'lbu':i(4,rs=5,op=0x03),'sw':s(2,a=5),'sb':s(0,a=5),
       'beq not taken':br(0),'bne taken':br(1),'blt taken':br(4,a=2,b=1),'jal':jal()}
REGISTERS={1:0x12345678,2:0x0f0f0f0f,5:4096}
COPIES=64

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('-o',type=Path,help='JSON result')
    a=p.parse_args()
    binary=os.environ.get('CHECKED_EMULATOR',str(output_dir(dependencies.VM2_ROOT,'build')/'checked-emulator'))
    payload,manifest=compile_image()
    mapping=json.loads(payload['map.json'])
    registers=mapping['regions']['registers']['at'];memory=mapping['regions']['guest']['at']
    def ticks(words):
        image=bytearray(payload['image.bin'])
        for k,v in REGISTERS.items():put(image,registers+32*k,32,v)
        program=b''.join(w.to_bytes(4,'little') for w in words);image[memory//8:memory//8+len(program)]=program
        sealed,m=seal(image,manifest,mapping)
        with tempfile.TemporaryDirectory() as folder:
            command=['sh','-c','exec "$1" -s "$2" -p "$3" 4>"$4"','ticks',binary,str(m['vm1']['size']),str(m['vm1']['slots']),folder+'/snapshot']
            result=subprocess.run(command,input=sealed['boot.bin'],capture_output=True,timeout=600)
        assert result.returncode==0,result.stderr[-1000:]
        return int(re.search(rb'VM1_AUDIT_TICKS=(\d+)',result.stderr)[1])
    base=ticks([EBREAK]);rows={}
    for name,word in CASES.items():
        rows[name]=(ticks([word]*COPIES+[EBREAK])-base)/COPIES
        print(f'{name:14s} {rows[name]:8.1f}',flush=True)
    if a.o:a.o.write_text(json.dumps(dict(schema='rv32i-instruction-ticks-v1',copies=COPIES,registers=REGISTERS,
        ebreak_ticks=base,ticks_per_instruction=rows),indent=1)+'\n')

if __name__=='__main__':main()
