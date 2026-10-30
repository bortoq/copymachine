"""Independent test/example codec; no import from an emulator implementation."""
NOP = (0, 0, 0, 0)

def put_field(data, at, width, value):
    if not 0 <= value < (1 << width):
        raise ValueError('field overflow')
    for k in range(width):
        mask = 128 >> ((at+k) % 8)
        if value >> k & 1:
            data[(at+k)//8] |= mask
        else:
            data[(at+k)//8] &= ~mask

def copy(n, dst, src, size):
    if not n:
        return NOP
    return (dst, dst if dst >= size else dst+n,
            src, src if src >= size else src+n)

def validate(rows, size):
    intervals = []
    for dl, dh, sl, sh in rows:
        if dl == dh and dl >= size:
            if sl == sh:
                continue
            intervals.append((sl, sh))
        elif sl == sh and sl >= size:
            if dl == dh:
                continue
            intervals.append((dl, dh))
        elif sl == sh:
            continue
        else:
            if dh-dl != sh-sl:
                raise ValueError('unequal lengths')
            intervals.extend(((dl, dh), (sl, sh)))
    for lo, hi in intervals:
        if not 0 <= lo < hi <= size:
            raise ValueError('out of bounds')
    intervals.sort()
    if any(b > c for (_, b), (c, _) in zip(intervals, intervals[1:], strict=False)):
        raise ValueError('overlapping source/destination intervals')

def layer(rows, size, slots):
    if len(rows) > slots:
        raise ValueError('too many instructions')
    validate(rows, size)
    a = size.bit_length()
    data = bytearray((4*a*slots+7)//8)
    for i, row in enumerate(rows):
        for k, v in enumerate(row):
            put_field(data, (i*4+k)*a, a, v)
    return bytes(data)

def boot(image, size, slots, chunk_bytes=32768):
    """A two-tick copycode installer; the emulator only reads channel bytes.

    First tick loads a body chunk, clears three instructions from NOP slots,
    and patches the high destination endpoint of a dormant stdin instruction.
    Second tick that instruction reads the next processor packet.
    """
    a = size.bit_length()
    inst = 4*a
    bits = inst*slots
    if slots < 8 or bits % 8 or len(image)*8 > size:
        raise ValueError('fixture installer requires >=8 slots, byte-sized processor/image')
    packet = bits//8
    image = image.ljust((size+7)//8, b'\0')
    stream = bytearray()
    records = 0
    for start in range(packet, len(image), chunk_bytes):
        payload = image[start:start+chunk_bytes]
        if not any(payload):
            continue
        rows = [copy(len(payload)*8, start*8, size+1, size),
                copy(3*inst, 0, 4*inst, size),
                copy(a, 3*inst+a, 7*inst, size),
                (0, 0, size+1, size+1), NOP, NOP, NOP,
                (bits, 0, 0, 0)]
        stream.extend(layer(rows, size, slots))
        stream.extend(payload)
        records += 1
    stream.extend(image[:packet])
    return bytes(stream), 1+2*records

def program(layers, size=65520, slots=8, data=()):
    a = size.bit_length()
    bits = slots*4*a
    if bits % 8:
        raise ValueError('byte-sized processor required for fixture')
    image = bytearray(size//8)
    for i, rows in enumerate(layers):
        rows = list(rows) + [copy(bits, 0, (i+1)*bits, size)]
        encoded = layer(rows, size, slots)
        image[i*bits//8:(i+1)*bits//8] = encoded
    for at, payload in data:
        if at % 8:
            raise ValueError('byte data required')
        image[at//8:at//8+len(payload)] = payload
    return boot(bytes(image), size, slots)
