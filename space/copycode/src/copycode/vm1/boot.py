"""Bounded stdin installer, derived from emulator's independent runtime fixture."""
from .machine import NOP

def iter_boot(image, fmt, *, chunk_bytes=32768):
    if fmt.slots<8 or fmt.layer_bits%8 or fmt.size%8 or chunk_bytes<1:
        raise ValueError('installer needs >=8 slots, byte-sized processor/space and positive chunk size')
    def read(n):
        out=bytearray()
        while len(out)<n:
            part=image.read(n-len(out))
            if not part:break
            out.extend(part)
        return bytes(out)
    entry=read(fmt.layer_bytes).ljust(fmt.layer_bytes,b'\0')
    start=fmt.layer_bytes
    while start<fmt.image_bytes:
        payload=read(min(chunk_bytes,fmt.image_bytes-start))
        if not payload:break
        if any(payload):
            inst=fmt.instruction_bits
            rows=[fmt.copy(len(payload)*8,start*8,fmt.channels['stdin']),
                  fmt.copy(3*inst,0,4*inst),fmt.copy(fmt.a,3*inst+fmt.a,7*inst),
                  (0,0,fmt.channels['stdin'],fmt.channels['stdin']),NOP,NOP,NOP,(fmt.layer_bits,0,0,0)]
            yield fmt.layer(rows)
            yield payload
        start+=len(payload)
    if image.read(1):raise ValueError('image exceeds space')
    yield entry

def boot_stream(image, fmt, **options):
    import io
    return b''.join(iter_boot(io.BytesIO(image),fmt,**options))
