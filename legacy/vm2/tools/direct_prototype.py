#!/usr/bin/env python3
"""Build a real legacy RV32I memory/LUT/dispatch fragment through the public adapter."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vm2compile import Copy as LogicalCopy,Channel,Memory
from vm2compile.legacy import adapt
from vm2compile.artifact import build,save

def prototype(copy_space):
    path=Path(copy_space)/'modules/rv32i.py'
    spec=importlib.util.spec_from_file_location('legacy_rv32i_fragment',path);module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module;spec.loader.exec_module(module)
    image=module.Image(memory_bytes=65536,layout=module.Layout(8*1024*1024))
    # Real legacy memory_address, lookup and indirect jump builders. This is
    # a transport/dispatch fragment, not an implementation of the full ISA.
    image.start('fetch')
    read=module.Copy(32,module.RAW,image.layout.memory_bit)
    image.memory_address(read,'src');image.blocks[image.current][0].append(read)
    values=[int(f'{(i*17):08b}'[::-1],2) for i in range(16)]
    table=image.table(values,4);image.lookup(module.RESULT,table,list(range(module.RAW,module.RAW+4)),8,4)
    image.emit(32,module.EA,image.constant(10))
    write=module.Copy(8,image.layout.memory_bit,module.RESULT)
    image.memory_address(write,'dst');image.blocks[image.current][0].append(write);image.jump('dispatch')
    image.start('dispatch');targets=image.table(['halt','out'],5)
    image.lookup(module.JUMP,targets,[module.COND],image.layout.address_bits,5);image.jump()
    image.start('out');image.jump('halt');image.start('halt');image.jump('halt')
    # Make halt finite; the real owner normally selects its halt block itself.
    image.blocks['halt']=([],module.Copy(image.layout.layer_bits,0,0))
    scratch_value=(4<<(module.EA-module.SCRATCH))|(1<<(module.COND-module.SCRATCH))
    guest=bytearray(64);guest[4:8]=bytes.fromhex('1305a002') # an actual RV32I ADDI word, transported intact
    guest_value=sum(((guest[k//8]>>(7-k%8))&1)<<k for k in range(len(guest)*8))
    regions=[dict(name='registers',at=module.SCRATCH,bits=1024,value=scratch_value,align=1024),
             dict(name='guest',at=image.layout.memory_bit,bits=512,value=guest_value,align=512)]
    for name,start,bits in [('lut',table,16*16),('dispatch_table',targets,2*32)]:
        value=0;relocs=[]
        for at,width,item in image.data:
            if start<=at<start+bits:
                if isinstance(item,str):relocs.append((at-start,width,item))
                else:value|=item<<(at-start)
        regions.append(dict(name=name,at=start,bits=bits,value=value,align=bits,relocations=relocs))
    for value,at in image.constants.items():regions.append(dict(name='constant-'+str(value),at=at,bits=32,value=value))
    p=adapt(image.blocks,regions,address_bits=image.layout.address_bits,count_bits=image.layout.n_bits,entry='fetch')
    p.layers['legacy:out:end'].copies.append(LogicalCopy(8,Channel('stdout'),Memory('guest',80)))
    p.layers['legacy:halt:end'].checkpoint=True
    return p,dict(source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  operations='legacy memory_address load/store, LUT lookup, indirect dispatch',
                  full_rv32i=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--copy-space',type=Path,default=ROOT.parent.parent/'legacy/copy-space')
    p.add_argument('-o',type=Path,required=True);p.add_argument('--source',type=Path)
    args=p.parse_args();program,provenance=prototype(args.copy_space)
    if args.source:args.source.write_text(json.dumps(program.source(),sort_keys=True,indent=2)+'\n')
    payload,manifest=build(program);manifest['prototype']=provenance;save(args.o,payload,manifest)
    print(json.dumps(provenance,sort_keys=True))
if __name__=='__main__':main()
