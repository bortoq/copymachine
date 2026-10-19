"""Independent interval validation for schedules, not a kernel runtime check.

Channel endpoints name typed devices, not memory ranges. Memory buffers in
all device/SYS operations still obey one pairwise-disjoint interval rule.
"""


def memory_intervals(rows, space_bits, *, address_bits=None):
    a = space_bits.bit_length() if address_bits is None else address_bits
    intervals = []
    devices = set()
    requests = 0
    for slot, (n, dst, src) in enumerate(rows):
        if not n:
            continue
        if n < 0 or min(dst, src) < 0:
            raise ValueError('negative copy field')
        channel = max(dst, src) >= space_bits
        if channel and min(dst, src) >= space_bits:
            raise ValueError('channel-to-channel copy')
        if channel:
            device = max(dst,src)
            if device > space_bits:
                if device in devices: raise ValueError('multiple operations on one data channel')
                devices.add(device)
            elif dst == space_bits:
                requests += 1
                if requests > 1: raise ValueError('multiple SYS requests')
        for side, at in [('src', src), ('dst', dst)]:
            if at >= space_bits:
                continue
            width = n
            if channel:
                device = max(dst, src)
                if device == space_bits:
                    width = max(n, 120+a) if dst == device else 96+a
                else:
                    width = (n+7)//8*8
            if at+width > space_bits:
                raise ValueError(f'slot {slot} {side} exceeds space')
            intervals.append((at, at+width, slot, side))
    return intervals


def validate(rows, space_bits, *, address_bits=None):
    """Reject every pair of intersecting memory operands, including reads."""
    intervals = sorted(memory_intervals(rows, space_bits, address_bits=address_bits))
    for left, right in zip(intervals, intervals[1:]):
        if right[0] < left[1]:
            raise ValueError(f'overlapping intervals: slot {left[2]} {left[3]} '
                             f'[{left[0]},{left[1]}) and slot {right[2]} {right[3]} '
                             f'[{right[0]},{right[1]})')
    return intervals


def decode_layer(data, space_bits, slots):
    """Manual codec, independent of generator packing/decoding helpers."""
    a = space_bits.bit_length()
    def field(at, width):
        value = 0
        for k in range(width):
            value |= ((data[(at+k)//8] >> (7-(at+k)%8)) & 1) << k
        return value
    return [(field(i*(3*a-1), a-1), field(i*(3*a-1)+a-1, a),
             field(i*(3*a-1)+2*a-1, a)) for i in range(slots)]


def linked_layer(fmt, rows, following):
    """Encode a disjoint layer and its link; serialize observing the link's
    source if necessary, using only processor state and two execution ticks.
    """
    rows = list(rows)
    direct = rows+[(0,0,0)]*(fmt.slots-1-len(rows))+[(fmt.layer_bits,0,following)]
    try:
        validate(direct, fmt.space_bits)
    except ValueError:
        # One data operation may observe the next layer (e.g. whole-space
        # output). Use the same two-tick self-erasing transition as installer.
        active = [r for r in rows if r[0]]
        validate(active, fmt.space_bits)
        if len(active) != 1 or fmt.slots < 8:
            raise ValueError('layer needs a separate control-transfer step')
        result = [active[0], (3*fmt.isz,0,4*fmt.isz),
                  (fmt.z,3*fmt.isz,7*fmt.isz+fmt.z),
                  (0,0,following), (0,0,0), (0,0,0), (0,0,0),
                  (0,fmt.layer_bits,0)]
        validate(result,fmt.space_bits)
        return fmt.layer(result), 2
    return fmt.layer(direct), 1
