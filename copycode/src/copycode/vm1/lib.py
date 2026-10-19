"""Disjoint bit packing and an eight-bit guest LUT adder; MIT.

Packing reverses physical byte bits into numeric least-significant-bit order.
Adder uses an eight-entry full-adder LUT; no host-computed operand result.
Inputs/output are packed physical bytes; low bit is physical position +7.
"""

def reverse_byte(fmt,dst,src):
    if fmt.slots<2:raise ValueError('packing requires a data slot and a link slot')
    rows=[fmt.copy(1,dst+k,src+7-k) for k in range(8)]
    # Split for the smallest supported p=8 because links consume one slot.
    return [rows[i:i+fmt.slots-1] for i in range(0,8,fmt.slots-1)]

def add8(program,left=44000,right=44008,result=44016,scratch=44024,table=45056):
    f=program.fmt
    if table%32:raise ValueError('LUT must be aligned to 32 bits')
    regions=sorted([(left,left+8),(right,right+8),(result,result+8),(scratch,scratch+2),(table,table+32)])
    if any(not 0<=lo<hi<=f.size for lo,hi in regions) or any(hi>lo2 for (_,hi),(lo2,_) in zip(regions,regions[1:])):
        raise ValueError('adder operands, scratch and LUT must be disjoint memory')
    # At index a+2b+4carry, two bits contain sum then next carry.
    lut=bytearray(4)
    for i in range(8):
        a,b,c=i&1,(i>>1)&1,(i>>2)&1
        for j,value in enumerate(((a^b^c),int(a+b+c>=2))):
            if value:lut[(i*4+j)//8]|=128>>((i*4+j)%8)
    program.store(table,lut);program.store(scratch,b'\0')
    for bit in range(8):
        first=len(program.layers)
        lookup=(first+3)*f.layer_bits
        sources=(left+7-bit,right+7-bit,scratch+1)
        program.layer([f.copy(1,lookup+2*f.a+2+k,src) for k,src in enumerate(sources)])
        program.layer([f.copy(1,lookup+3*f.a+2+k,src) for k,src in enumerate(sources)])
        program.layer()  # Patched layer must never be the link source in a patch tick.
        program.layer([f.copy(2,scratch,table)])
        program.layer([f.copy(1,result+7-bit,scratch)])
    return dict(left=left,right=right,result=result,scratch=scratch,table=table,ticks=40)
