"""Shared 32-bit carry arithmetic for symbolic copy builders.

SPDX-License-Identifier: Apache-2.0
Extracted from copy-space/modules/rv32i.py; original algorithm preserved.
The caller supplies scratch signals; no RV32I addresses or decoding here.
"""

def add32(builder,dst,a,b,*,carry,pair,temp,subtract=False):
    if "adder" not in builder.gates:
        # Eight entries, two bits per entry: sum followed by carry.
        builder.gates["adder"] = builder.table([
            ((i & 1) + ((i >> 1) & 1) + ((i >> 2) & 1)) for i in range(8)
        ], 1)
    builder.emit(1, carry, builder.constant(int(subtract)))
    for i in range(32):
        second = b + i
        if subtract:
            builder.gate("not", temp + i, [second])
            second = temp + i
        builder.lookup(pair, builder.gates["adder"], [a+i, second, carry], 2, 1)
        builder.emit(1, dst+i, pair)
        builder.emit(1, carry, pair+1)



def add32_digits(builder,dst,a,b,*,carry,temp,subtract=False):
    """Same result as add32, four bits per step.

    A 512-entry table maps (a nibble, b nibble, carry) to five bits: the sum
    nibble and the carry out. Subtraction uses a table of a+~b+carry, so no
    inversion pass is needed. temp provides two alternating 5-bit results.
    """
    key = "adder4-subtract" if subtract else "adder4"
    if key not in builder.gates:
        builder.gates[key] = builder.table([
            (i & 15) + ((~(i >> 4) if subtract else i >> 4) & 15) + ((i >> 8) & 1)
            for i in range(512)
        ], 3)
    previous = builder.constant(int(subtract))
    for digit in range(8):
        out = temp + (digit % 2) * 8
        indices = [a+4*digit+k for k in range(4)] + [b+4*digit+k for k in range(4)] + [previous]
        builder.lookup(out, builder.gates[key], indices, 5, 3)
        builder.emit(4, dst+4*digit, out)
        previous = out + 4
    builder.emit(1, carry, previous)
