"""Cost counters of the vm2 reference oracle (layers, copies, bits, channel_bits)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vm2_reference import run,put

SIZE=65520;SLOTS=8
A=SIZE.bit_length();Z=A-1;I=3*A-1;L=I*SLOTS   # a=16, z=15, I=47, L=376
LOAD=L   # tick 1: the bootstrap slot copies L bits from channel 1 (stdin) over the slot table

def program(slots):
    buf=bytearray(L//8)
    for i,(n,d,s) in enumerate(slots):
        put(buf,i*I,Z,n);put(buf,i*I+Z,A,d);put(buf,i*I+Z+A,A,s)
    return bytes(buf)

def counters(slots,**kw):
    r=run(program(slots),SIZE,SLOTS,counters=True,**kw)
    return r,r['cost']

# Default call is unchanged: no counters in the result.
assert 'cost' not in run(program([]),SIZE,SLOTS)

# 1. One copy and stop. Tick 1: load (1 copy, 0 bits, 376 channel bits).
# Tick 2: slot0 copies 8 bits, slot1 copies 62 bits of zeros over slot0 and slot1.n (stop).
# Tick 3: all n are 0, halt without a tick. layers=2, copies=1+2=3, bits=8+62=70, channel_bits=376.
r,c=counters([(8,1100,1000),(62,0,2000)])
assert c==dict(layers=2,copies=3,bits=70,channel_bits=376),c
assert r['ticks']==2

# 2. Several ticks in a row: slot0 (8 bits) and slot1 (15 bits) never stop; limit=4 ticks.
# Tick 1: load. Ticks 2..4: 2 copies each. layers=4, copies=1+3*2=7, bits=3*(8+15)=69, channel_bits=376.
r,c=counters([(8,1100,1000),(15,2000,3000)],limit=4)
assert c==dict(layers=4,copies=7,bits=69,channel_bits=376),c

# 3. NOP (n=0, not counted) with stdout output. slot0 writes 16 bits to channel 2 (stdout),
# slot1 is NOP, slot2 copies 109 bits of zeros over slots 0..2 n fields (stop).
# Tick 1: load. Tick 2: stdout write (copy, 16 channel bits) + 109-bit copy.
# layers=2, copies=1+2=3, bits=109, channel_bits=376+16=392.
r,c=counters([(16,SIZE+2,1000),(0,0,0),(109,0,2000)])
assert c==dict(layers=2,copies=3,bits=109,channel_bits=392),c
assert bytes(r['channels'][2]['data'])==b'\0\0'

print('ok')
