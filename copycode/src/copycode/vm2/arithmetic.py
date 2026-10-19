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

