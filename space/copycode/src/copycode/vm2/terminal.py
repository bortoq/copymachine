"""Copycode terminal/status fragments, separate from application stdout.

SPT1 header is little-endian; copied numeric fields use the space bit order.
This module generates ordinary copies. It does not inspect guest execution.
"""
import struct
from .schedule import linked_layer
from .boundary import Format, field

HEADER = struct.Struct('<4sBBHQQ32s')
RECORD_BYTES = HEADER.size + 4 + 8 + 8 + 4
COUNTERS = ('committed', 'read_ops', 'write_ops')
MAX_RECORD_BYTES = RECORD_BYTES + 8*len(COUNTERS)
REASONS = {'idle': 0, 'limit': 1, 'error': 2}


def numeric(value, bits):
    if not 0 <= value < 1 << bits:
        raise ValueError('terminal numeric field overflow')
    data = bytearray(bits//8)
    for k in range(bits):
        data[k//8] |= ((value >> k) & 1) << (7-k%8)
    return data


def decode_terminal(raw, description):
    extended = raw[:4] == b'SPT2'
    if len(raw) != (MAX_RECORD_BYTES if extended else RECORD_BYTES):
        raise ValueError('missing or truncated terminal record')
    magic, kind, reason, flags, bits, snapshot_bytes, layout = HEADER.unpack_from(raw)
    if (magic not in (b'SPT1', b'SPT2') or kind not in (1, 2) or reason not in REASONS.values()
            or flags & ~7 or bits != description['space_bits']
            or layout.hex() != description['layout_id']
            or snapshot_bytes not in (0, description['image_bytes'])
            or (kind == 2 and not snapshot_bytes)):
        raise ValueError('incompatible or invalid SPT1 terminal record')
    result = dict(kind='checkpoint' if kind == 2 else 'terminal',
                reason=next(k for k, v in REASONS.items() if v == reason),
                exit_code=field(raw, HEADER.size*8, 32), snapshot_bytes=snapshot_bytes,
                input_cursor=field(raw, (HEADER.size+4)*8, 64) if flags & 1 else None,
                output_cursor=field(raw, (HEADER.size+12)*8, 64) if flags & 2 else None,
                guest_status=field(raw, (HEADER.size+20)*8, 32) if flags & 4 else None,
                layout_id=layout.hex())
    if extended:
        result['counts'] = {name: field(raw, (RECORD_BYTES+8*i)*8, 64)
                            for i, name in enumerate(COUNTERS)}
    return result


class TerminalFragment:
    """Small relocatable final report. No full-space Python buffer required.

    Supply live exit/cursor bit addresses at the generator's terminal boundary.
    Continuation is explicit copycode; dynamic checkpoint scheduling is owned
    by the generator (the next roadmap item).
    """
    def __init__(self, space_bits, slots, base, *, snapshot=False, continuation=(),
                 reason='idle', exit_code=0, exit_address=None,
                 input_cursor_address=None, output_cursor_address=None, guest_status_address=None,
                 counter_addresses=None, phase_markers=False):
        self.fmt = f = Format(space_bits, slots)
        if f.layer_bits % 8 or base % 8 or base < f.layer_bits:
            raise ValueError('terminal fragment needs byte-aligned processor and base')
        if reason not in REASONS or (continuation and not snapshot):
            raise ValueError('invalid terminal reason/continuation')
        self.base, self.data, self.chain = base, bytearray(), []
        flags = int(input_cursor_address is not None) | (int(output_cursor_address is not None) << 1)
        flags |= int(guest_status_address is not None) << 2
        if counter_addresses is not None and set(counter_addresses) != set(COUNTERS):
            raise ValueError('SPT2 requires committed/read_ops/write_ops counters')
        extended = counter_addresses is not None
        size = MAX_RECORD_BYTES if extended else RECORD_BYTES
        metadata = HEADER.pack(b'SPT2' if extended else b'SPT1', 2 if continuation else 1, REASONS[reason], flags,
                               space_bits, f.space_bytes if snapshot else 0,
                               bytes.fromhex(f.description['layout_id']))
        record = self.allocate(metadata + numeric(exit_code, 32) + bytes(size-HEADER.size-4))
        sources = [(exit_address, HEADER.size, 32),
                   (input_cursor_address, HEADER.size+4, 64),
                   (output_cursor_address, HEADER.size+12, 64),
                   (guest_status_address, HEADER.size+20, 32)]
        if extended:
            sources.extend((counter_addresses[name], RECORD_BYTES+8*i, 64)
                           for i, name in enumerate(COUNTERS))
        for source, offset, width in sources:
            if source is not None:
                if source < f.layer_bits or source+width > space_bits:
                    raise ValueError('terminal source must be outside the processor')
                self.layer([(width, record+offset*8, source)])
        if snapshot:
            tail = space_bits % 8
            self.tail_byte = None
            if tail:
                self.tail_byte = self.allocate(b'\0')
                self.layer([(tail,self.tail_byte,space_bits-tail)])
            if phase_markers:
                marker = self.allocate(b'PHT1S')
                self.emit(marker,40,'debug')
            entry = self.allocate(f.layer(continuation))
            self.snapshot_entry = entry
            self.emit(entry, f.layer_bits, 'snapshot')
            for start in range(f.layer_bytes, f.space_bytes, f.max_bytes):
                self.emit(start*8, min(f.max_bytes*8, space_bits-start*8), 'snapshot')
        self.emit(record, size*8, 'status')
        if phase_markers:
            marker = self.allocate(b'PHT1F')
            self.emit(marker,40,'debug')
        self.layer([])
        self.report_ticks = 0
        for current, following in zip(self.chain, self.chain[1:]):
            offset = (current-base)//8
            layer = self.data[offset:offset+f.layer_bytes]
            from .schedule import decode_layer
            rows = decode_layer(layer,space_bits,slots)[:-1]
            encoded, ticks = linked_layer(f,rows,following)
            self.data[offset:offset+f.layer_bytes] = encoded
            self.report_ticks += ticks
        for source, _, width in sources:
            if source is not None and source < base+len(self.data)*8 and source+width > base:
                raise ValueError('terminal live source overlaps fragment')

    def allocate(self, data):
        at = self.base + len(self.data)*8
        self.data.extend(data)
        if self.base+len(self.data)*8 > self.fmt.space_bits:
            raise ValueError('terminal fragment exceeds space')
        return at

    def layer(self, rows):
        if len(rows) >= self.fmt.slots:
            raise ValueError('last slot reserved for fragment link')
        at = self.allocate(self.fmt.layer(rows))
        self.chain.append(at)
        return at

    def emit(self, at, n, device):
        whole = n//8*8
        for offset in range(0, whole, self.fmt.max_bytes*8):
            self.layer([(min(whole-offset, self.fmt.max_bytes*8), self.fmt.devices[device], at+offset)])
        if n%8:
            self.layer([(8,self.fmt.devices[device],self.tail_byte)])

    @property
    def entry(self):
        return self.chain[0]


def attach_terminal(source, target, space_bits, slots, halt_address, **options):
    """Copy a seekable raw image to a file and patch its known halt label.

    Uses bounded buffers. Source is immutable. Caller guarantees unused tail
    for the fragment, and guest writes must preserve it throughout execution.
    """
    import shutil
    import io
    import os
    if source is target:
        raise ValueError('source and target must be different files')
    try:
        src_stat, dst_stat = os.fstat(source.fileno()), os.fstat(target.fileno())
    except (AttributeError, io.UnsupportedOperation):
        pass
    else:
        if (src_stat.st_dev, src_stat.st_ino) == (dst_stat.st_dev, dst_stat.st_ino):
            raise ValueError('source and target must be different files')
    source.seek(0, 2)
    length = source.tell()
    f = Format(space_bits, slots)
    if length > f.space_bytes or halt_address % 8 or halt_address < f.layer_bits:
        raise ValueError('invalid image/halt address')
    source.seek(halt_address//8)
    layer = source.read(f.layer_bytes)
    if len(layer) != f.layer_bytes:
        raise ValueError('halt layer outside image')
    rows = [(field(layer, i*f.isz, f.z), field(layer, i*f.isz+f.z, f.a),
             field(layer, i*f.isz+f.z+f.a, f.a)) for i in range(slots)]
    active = [r for r in rows if r[0]]
    if len(active) != 1 or active[0][:2] != (f.layer_bits, 0):
        raise ValueError('halt layer must only link to zeros')
    if active[0][2] % 8:
        raise ValueError('halt zero layer must be byte aligned')
    source.seek(active[0][2]//8)
    zero = source.read(f.layer_bytes)
    if len(zero) != f.layer_bytes or any(zero):
        raise ValueError('halt link must target a zero layer inside the image')
    fragment = TerminalFragment(space_bits, slots, length*8, **options)
    source.seek(0)
    target.seek(0)
    shutil.copyfileobj(source, target, length=65536)
    target.write(fragment.data)
    target.truncate()
    target.seek(halt_address//8)
    target.write(f.layer([(f.layer_bits, 0, fragment.entry)]))
    target.flush()
    target.seek(0)
    return fragment
