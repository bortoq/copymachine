"""Cost counters of the vm2 reference oracle (layers, copies, bits, channel_bits, sys_bits)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vm2_reference import run,put,get

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

# copies counts only instructions with n>0 that changed memory or moved a bit through a channel/SYS.
# bits counts n of every memory-to-memory copy (as in 13.4), changed or not.

# 1. One copy and stop. Tick 1: load (1 copy, 0 bits, 376 channel bits).
# Tick 2: slot0 copies 8 zero bits onto zeros (memory unchanged: not a copy, but 8 bits),
# slot1 copies 62 zero bits over slot0.n and slot1.n (changed, stop): 1 copy, 62 bits.
# Tick 3: all n are 0, halt without a tick. layers=2, copies=1+1=2, bits=8+62=70, channel_bits=376.
def test_1():
    r,c=counters([(8,1100,1000),(62,0,2000)])
    assert c==dict(layers=2,copies=2,bits=70,channel_bits=376,sys_bits=0),c
    assert r['ticks']==2

# 2. Several ticks: slot0 (8 bits) and slot1 (15 bits) copy zeros onto zeros, limit=4 ticks.
# Tick 1: load (1 copy). Ticks 2..4: no memory change, so no copies; bits=3*(8+15)=69.
# layers=4, copies=1, channel_bits=376.
def test_2():
    r,c=counters([(8,1100,1000),(15,2000,3000)],limit=4)
    assert c==dict(layers=4,copies=1,bits=69,channel_bits=376,sys_bits=0),c

# 3. NOP (n=0, not counted) with stdout output. slot0 writes 16 bits to channel 2 (stdout),
# slot1 is NOP, slot2 copies 109 zero bits over slots 0..2 n fields (changed, stop).
# Tick 1: load. Tick 2: stdout write (copy, 16 channel bits) + 109-bit copy (copy, 109 bits).
# layers=2, copies=1+2=3, bits=109, channel_bits=376+16=392.
def test_3():
    r,c=counters([(16,SIZE+2,1000),(0,0,0),(109,0,2000)])
    assert c==dict(layers=2,copies=3,bits=109,channel_bits=392,sys_bits=0),c
    assert bytes(r['channels'][2]['data'])==b'\0\0'

# 4. stdin with a short remainder (EOF): the stream is 6 bytes = 48 bits (slot0 and one bit
# of slot1), the load asks for 47 bytes. Slot0 = (62,0,2000) clears itself and stops.
# Tick 1: load moves 6 bytes: 1 copy, 48 channel bits, eof=1, moved=6.
# Tick 2: 62-bit copy of zeros changes slot0.n: 1 copy, 62 bits. layers=2, copies=2.
def test_4():
    short=program([(62,0,2000)])[:6]
    r=run(short,SIZE,SLOTS,counters=True);c=r['cost']
    assert c==dict(layers=2,copies=2,bits=62,channel_bits=48,sys_bits=0),c
    assert r['channels'][1]['eof']==1 and r['channels'][1]['moved']==6

# 4b. Empty stdin: the load moves 0 bytes (EOF), memory is unchanged, so it is not a copy.
# The bootstrap slot repeats; limit=2: layers=2, copies=0, bits=0, channel_bits=0.
def test_4b():
    r=run(b'',SIZE,SLOTS,2,counters=True);c=r['cost']
    assert c==dict(layers=2,copies=0,bits=0,channel_bits=0,sys_bits=0),c

# 5. FSTAT through SYS (S). Stream = program image (47 bytes) + 17 request bytes
# C0 8F FF 00.. = op 3, target SIZE+1 (stdin), rest zero.
# slot0 (136,2000,SIZE+1) reads the request from stdin in tick 2;
# slot1 (15,94,203) copies 136 (low bits of slot4.d) into slot2.n, slot2 (0,SIZE,2000) is SYS write;
# slot3 (62,0,5000) zeroes slot0..slot1.n; slot4 (0,136,0) is data; slot5 (112,4000,SIZE) reads the response.
# Tick 1: load, 1 copy, 376 channel bits.
# Tick 2: stdin read 136 bits (copy, 136 channel bits), slot1 15 bits (changed, copy),
#   slot3 62 bits (changed, copy), slot5 reads the response (97+15=112 sys bits, copy): copies 4,
#   bits 15+62=77, sys_bits 112.
# Tick 3: slot2 SYS write max(136,120+16)=136 sys bits (copy), slot3 62 zero bits (unchanged, 62 bits),
#   slot5 reads the old response again (112 sys bits, copy): copies 2, bits 62, sys_bits 248.
# layers=3, copies=1+4+2=7, bits=139, channel_bits=376+136=512, sys_bits=112+248=360.
def test_5():
    req=bytes([0xC0,0x8F,0xFF])+bytes(14)
    r=run(program([(136,2000,SIZE+1),(15,94,203),(0,SIZE,2000),(62,0,5000),(0,136,0),(112,4000,SIZE)])+req,SIZE,SLOTS,3,counters=True);c=r['cost']
    assert c==dict(layers=3,copies=7,bits=139,channel_bits=512,sys_bits=360),c
    assert get(r['response'],0,8)==3   # FSTAT reply op

# 6. Copy into a closed channel: stdout (channel 2) is not bound. slot0 would write 16 bits,
# slot1 copies 109 zero bits and stops. The closed write is not counted (compare with 3: copies=3).
# copies=1(load)+1=2, bits=109, channel_bits=376, nothing reaches stdout.
def test_6():
    r,c=counters([(16,SIZE+2,1000),(109,0,2000)],bound=(1,3,4,5))
    assert c==dict(layers=2,copies=2,bits=109,channel_bits=376,sys_bits=0),c
    assert bytes(r['channels'][2]['data'])==b''

# 7. Write failing with stdout_error: same numbers as 6, the failed write is neither a copy nor channel bits.
def test_7():
    r,c=counters([(16,SIZE+2,1000),(109,0,2000)],stdout_error=5)
    assert c==dict(layers=2,copies=2,bits=109,channel_bits=376,sys_bits=0),c
    assert bytes(r['channels'][2]['data'])==b''

test_1()
test_2()
test_3()
test_4()
test_4b()
test_5()
test_6()
test_7()
print('ok')
