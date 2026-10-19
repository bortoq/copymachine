#!/usr/bin/env python3
"""Stdin installation streams and cooperative in-space diagnostic modules.

No emulator extensions: every installed instruction is an ordinary copy.
Use `boot -s BITS -p SLOTS IMAGE -o BOOT` or `decode TRACE`.
"""
import argparse
from pathlib import Path
import struct
import sys

from .driver_gen import encode
from .machine import PROTOCOL, describe
from .schedule import validate, linked_layer

NOP = (0, 0, 0)
PROTO = PROTOCOL


def field(data, at, width):
    return sum(((data[(at+k)//8] >> (7-(at+k)%8)) & 1) << k
               for k in range(width))


def protocol(space_bits):
    desc = describe(space_bits, 1, protocol_path=PROTO)
    def layout(record):
        return ({f['name']: (f['offset_bits'], f['width_bits'])
                 for f in record['fields']}, record['bits'])
    return (desc['contract']['operations'], layout(desc['records']['req']),
            layout(desc['records']['rsp']))


def record(layout, values):
    fields, n = layout
    data = bytearray((n+7)//8)
    for name, value in values.items():
        at, width = fields[name]
        if not 0 <= value < 1 << width:
            raise ValueError('control field overflow: ' + name)
        for k in range(width):
            data[(at+k)//8] |= ((value >> k) & 1) << (7-(at+k)%8)
    return bytes(data)


class Format:
    def __init__(self, space_bits, slots):
        self.description = describe(space_bits, slots, protocol_path=PROTO)
        self.devices = {d['name']: d['position']
                        for d in self.description['channels']['devices']}
        self.space_bits, self.slots = space_bits, slots
        instruction = self.description['instruction']
        self.z = instruction['fields'][0]['width_bits']
        self.a = instruction['fields'][1]['width_bits']
        self.isz = instruction['bits']
        self.layer_bits = self.description['processor']['bits']
        self.layer_bytes = self.description['processor']['packet_bytes']
        self.space_bytes = self.description['image_bytes']
        self.max_bytes = self.description['boot']['payload_max_bytes']
        if not self.description['boot']['supported']:
            raise ValueError('stream loader needs at least 8 processor slots')

    def layer(self, rows):
        if len(rows) > self.slots:
            raise ValueError('too many instructions')
        for row in rows:
            if len(row) != 3 or any(not 0 <= v < 1 << w
                                  for v, w in zip(row, (self.z, self.a, self.a))):
                raise ValueError('instruction field overflow')
        validate(rows, self.space_bits)
        return encode(list(rows)+[NOP]*(self.slots-len(rows)), self.a, self.z)


def iter_boot(image, space_bits, slots, *, sparse=True, chunk_bytes=65536):
    """Yield bounded installation packets from a binary reader; no seeking.

    Omitted trailing bytes are zero in a fresh space. The entry processor
    is retained and installed last. Input errors propagate to the launcher.
    """
    fmt = Format(space_bits, slots)
    if chunk_bytes < 1:
        raise ValueError('chunk_bytes must be positive')
    limit = min(chunk_bytes, fmt.max_bytes)
    def read_up_to(n):
        data = bytearray()
        while len(data) < n:
            part = image.read(n-len(data))
            if not part:
                break
            data.extend(part)
        return bytes(data)
    entry = read_up_to(fmt.layer_bytes).ljust(fmt.layer_bytes, b'\0')
    start = fmt.layer_bytes
    while start < fmt.space_bytes:
        chunk = read_up_to(min(limit, fmt.space_bytes-start))
        if not chunk:
            break
        if start+len(chunk) == fmt.space_bytes and space_bits % 8:
            if chunk[-1] & ((1 << (8-space_bits % 8))-1):
                raise ValueError('nonzero bits beyond the space')
        tail = space_bits % 8 if start+len(chunk) == fmt.space_bytes else 0
        payload = chunk[:-1] if tail else chunk
        if payload and (not sparse or any(payload)):
            rows = [(len(payload)*8, start*8, fmt.devices['stdin']),
                    (3*fmt.isz, 0, 4*fmt.isz),
                    (fmt.z, 3*fmt.isz, 7*fmt.isz+fmt.z),
                    (0, 0, fmt.devices['stdin']), NOP, NOP, NOP,
                    (0, fmt.layer_bits, 0)]
            yield fmt.layer(rows)
            yield payload
        if tail and (not sparse or chunk[-1]):
            value = sum(((chunk[-1]>>(7-k))&1)<<k for k in range(tail))
            rows = [(tail, space_bits-tail, 7*fmt.isz+fmt.z+fmt.a),
                    (3*fmt.isz, 0, 4*fmt.isz),
                    (fmt.z, 3*fmt.isz, 7*fmt.isz+fmt.z),
                    (0,0,fmt.devices['stdin']), NOP, NOP, NOP,
                    (0,fmt.layer_bits,value)]
            yield fmt.layer(rows)
            # No payload bytes: the partial byte lives in a NOP field.
            # Keep two fragments per two-tick installer record for clocks.
            yield b''
        start += len(chunk)
    if image.read(1):
        raise ValueError('image exceeds the space')
    yield entry


def boot_stream(image, space_bits, slots, *, sparse=True):
    """Convenience byte wrapper; use iter_boot for bounded-memory transport."""
    import io
    return b''.join(iter_boot(io.BytesIO(image), space_bits, slots, sparse=sparse))


class Program:
    """Copycode library for finite, cooperative schedules.

    Steps use slots 0..p-2; the last slot is the library link. Diagnostics
    run between steps. The program owns its allocated code/record area;
    application writes must stay outside it and PROCESSOR. Trace tick
    numbers name application steps, not the extra physical monitor ticks.
    """
    def __init__(self, space_bits=65520, slots=8, *, code_base=None, trace=None):
        self.fmt = Format(space_bits, slots)
        if self.fmt.layer_bits % 8:
            raise ValueError('diagnostic modules need a byte-aligned processor (use -p 8/64/256)')
        if trace not in (None, 'full', 'channels'):
            raise ValueError('trace must be full or channels')
        self.trace = trace
        self.terminated = False
        self.image = bytearray(self.fmt.space_bytes)
        self.base = self.at = code_base if code_base is not None else self.fmt.layer_bytes*8
        if self.base < self.fmt.layer_bits or self.base % 8:
            raise ValueError('code_base must be byte aligned and beyond PROCESSOR')
        self.chain, self.tick = [], 0
        self.application_writes = []
        self.ops, self.req, self.rsp = protocol(space_bits)
        if trace:
            self.output(b'PCS1'+struct.pack('<QQB', space_bits, slots, trace == 'channels'), debug=True)

    def allocate(self, data):
        start = self.at
        self.at += len(data)*8
        if self.at > self.fmt.space_bits:
            raise ValueError('diagnostic program exceeds the space')
        self.image[start//8:self.at//8] = data
        return start

    def layer(self, rows=()):
        if len(rows) >= self.fmt.slots:
            raise ValueError('last slot is reserved for the link')
        at = self.allocate(self.fmt.layer(rows))
        self.chain.append(at)
        return at

    def output(self, data, *, debug=False):
        at = self.allocate(data)
        self.output_region(at, len(data)*8, debug=debug)

    def output_region(self, at, n, *, debug=False):
        if at % 8 or n % 8:
            raise ValueError('diagnostic output must be byte aligned')
        channel = self.fmt.devices['debug' if debug else 'stdout']
        for offset in range(0, n, self.fmt.max_bytes*8):
            self.layer([(min(n-offset, self.fmt.max_bytes*8), channel, at+offset)])

    def step(self, rows):
        rows = list(map(tuple, rows))
        if len(rows) >= self.fmt.slots:
            raise ValueError('last slot is reserved for the link')
        # Validate accesses; library control flow and records cannot be patched.
        for n, dst, src in rows:
            for pos in (src, dst):
                if n and pos < self.fmt.space_bits and pos+n > self.fmt.space_bits:
                    raise ValueError('application copy exceeds the space')
            if n and dst < self.fmt.layer_bits:
                raise ValueError('application steps must not overwrite PROCESSOR')
        validate(rows, self.fmt.space_bits)
        accessed = []
        for n, dst, src in rows:
            if not n:
                continue
            if dst < self.fmt.space_bits and src < self.fmt.space_bits:
                if dst < src+n and src < dst+n:
                    raise ValueError('overlapping source and destination')
            accessed.extend(pos for pos in (dst, src) if pos > self.fmt.space_bits)
        if len(set(accessed)) != len(accessed):
            raise ValueError('one operation per data channel per application step')
        self.application_writes.extend((dst, dst+n) for n, dst, _ in rows
                                       if n and dst < self.fmt.space_bits)
        self.tick += 1
        if self.trace:
            # Prefix contains copy counts, then a live instruction snapshot.
            copies = sum(bool(n) and dst < self.fmt.space_bits and src < self.fmt.space_bits
                         for n, dst, src in rows)
            selected = [i for i, (n, dst, src) in enumerate(rows)
                        if n and (dst > self.fmt.space_bits or src > self.fmt.space_bits)]
            if any(n and (self.fmt.space_bits in (src, dst) or
                          self.fmt.devices['debug'] in (src, dst)) for n, dst, src in rows):
                raise ValueError('traced steps reserve SYS and debug for the monitor')
            prefix = b'T'+struct.pack('<QQQ', self.tick, copies, len(selected))
            if self.trace == 'channels':
                # Fixed-field schedules need only a count of ordinary copies;
                # the debug stream carries channel instructions, not copy rows.
                prefix += b''.join(struct.pack('<QQQQ', slot, *rows[slot]) for slot in selected)
            self.output(prefix, debug=True)
            if self.trace == 'full':
                # Body home follows its prelude; patch the snapshot source.
                snapshot = self.layer([(self.fmt.layer_bits, self.fmt.devices['debug'], 0)])
        body = self.layer(rows)
        if self.trace:
            if self.trace == 'full':
                self.image[snapshot//8:(snapshot+self.fmt.layer_bits)//8] = self.fmt.layer(
                    [(self.fmt.layer_bits, self.fmt.devices['debug'], body)])
            for slot in selected:
                n, dst, src = rows[slot]
                channel = dst if dst > self.fmt.space_bits else src
                req = self.allocate(record(self.req, {'op': self.ops['FSTAT'], 'chan': channel}))
                answer = self.allocate(bytes((self.rsp[1]+7)//8))
                # Submit after data completion; read the committed reply next tick.
                self.layer([(self.req[1], self.fmt.space_bits, req)])
                self.layer([(self.rsp[1], answer, self.fmt.space_bits)])
                self.output(b'S'+struct.pack('<QQ', self.tick, slot), debug=True)
                self.output_region(answer, ((self.rsp[1]+7)//8)*8, debug=True)
        return body

    def checkpoint(self, continuation=(), *, reason='idle'):
        """Terminal full-space report; processor in snapshot is continuation.

        Other memory, including diagnostic code, is copied unchanged. The
        running reporter stops after output; restoring the snapshot with
        boot_stream starts continuation. External descriptors/cursors belong
        to the launcher; they are not silently reset by the emulator.
        """
        if reason not in ('idle', 'limit'):
            raise ValueError('stop reason must be idle or limit')
        if self.trace:
            self.output(b'X'+bytes([reason == 'limit']), debug=True)
        tail = self.fmt.space_bits % 8
        tail_byte = None
        if tail:
            tail_byte = self.allocate(b'\0')
            self.layer([(tail,tail_byte,self.fmt.space_bits-tail)])
        entry = self.allocate(self.fmt.layer(continuation))
        self.output_region(entry, self.fmt.layer_bits)
        rest = self.fmt.space_bytes-self.fmt.layer_bytes
        # Last partial byte has zero padding, as in the installation stream.
        for offset in range(0, rest, self.fmt.max_bytes):
            count = min(rest-offset, self.fmt.max_bytes)
            at = (self.fmt.layer_bytes+offset)*8
            n = min(count*8,self.fmt.space_bits-at)
            whole = n//8*8
            if whole: self.layer([(whole,self.fmt.devices['stdout'],at)])
            if n%8: self.layer([(8,self.fmt.devices['stdout'],tail_byte)])
        self.layer()
        self.terminated = True

    def finish(self):
        if not self.terminated:
            self.halt()
        for current, following in zip(self.chain, self.chain[1:]):
            rows = [(field(self.image,current+i*self.fmt.isz,self.fmt.z),
                     field(self.image,current+i*self.fmt.isz+self.fmt.z,self.fmt.a),
                     field(self.image,current+i*self.fmt.isz+self.fmt.z+self.fmt.a,self.fmt.a))
                    for i in range(self.fmt.slots-1)]
            encoded, _ = linked_layer(self.fmt, rows, following)
            self.image[current//8:current//8+self.fmt.layer_bytes] = encoded
        first = self.chain[0]//8
        self.image[:self.fmt.layer_bytes] = self.image[first:first+self.fmt.layer_bytes]
        for start, end in self.application_writes:
            if start < self.at and end > self.base:
                raise ValueError('application write overlaps diagnostic code/records')
        return bytes(self.image)

    def halt(self, *, reason='idle'):
        if reason not in ('idle', 'limit'):
            raise ValueError('stop reason must be idle or limit')
        if self.trace:
            self.output(b'X'+bytes([reason == 'limit']), debug=True)
        self.layer()
        self.terminated = True


def report_image(image, space_bits, slots, halt_address, *, code_base=None):
    """Attach terminal copycode dumping to a generated layered image.

    The caller supplies its halt-layer address (from its generator manifest).
    That layer must only link to an all-zero layer. No code discovery or
    instruction-set interpretation is done on the host. Code space must be
    unused; by default the reporter is appended after the supplied image.
    """
    image = bytes(image)
    program = Program(space_bits, slots, code_base=(len(image)*8 if code_base is None else code_base))
    fmt = program.fmt
    if halt_address % 8 or halt_address < fmt.layer_bits or halt_address+fmt.layer_bits > len(image)*8:
        raise ValueError('invalid halt-layer address')
    rows = [(field(image, halt_address+i*fmt.isz, fmt.z),
             field(image, halt_address+i*fmt.isz+fmt.z, fmt.a),
             field(image, halt_address+i*fmt.isz+fmt.z+fmt.a, fmt.a))
            for i in range(slots)]
    active = [row for row in rows if row[0]]
    if len(active) != 1 or active[0][:2] != (fmt.layer_bits, 0):
        raise ValueError('halt layer must only link to zeros')
    zero = active[0][2]
    if zero+fmt.layer_bits > len(image)*8 or any(field(image, zero+k, 1) for k in range(fmt.layer_bits)):
        raise ValueError('halt link does not target an all-zero layer')
    program.checkpoint()
    diagnostic = program.finish()
    if any(image[program.base//8:min(program.at//8, len(image))]):
        raise ValueError('reporter would overwrite existing image data')
    result = bytearray(image.ljust(fmt.space_bytes, b'\0'))
    if len(result) != fmt.space_bytes:
        raise ValueError('image exceeds the space')
    result[program.base//8:program.at//8] = diagnostic[program.base//8:program.at//8]
    result[halt_address//8:(halt_address+fmt.layer_bits)//8] = fmt.layer(
        [(fmt.layer_bits, 0, program.chain[0])])
    return bytes(result)


def run_image(emulator, image, space_bits, slots, halt_address, *, input_data=b'',
              timeout=120, code_base=None):
    """Run a generated image through stdin and return (process, raw_snapshot).

    stdout is application bytes followed by the terminal raw snapshot.
    Splitting that documented stream is a launcher operation; the emulator
    receives only -s/-p and ordinary stdin bytes. File cursors are the
    launcher's responsibility when resuming a saved continuation.
    """
    import subprocess
    packet = boot_stream(report_image(image, space_bits, slots, halt_address,
                                      code_base=code_base), space_bits, slots)
    result = subprocess.run([str(emulator), '-s', str(space_bits), '-p', str(slots)],
                            input=packet+input_data, capture_output=True, timeout=timeout)
    size = (space_bits+7)//8
    if result.returncode or len(result.stdout) < size:
        raise ValueError(f'image did not produce a complete terminal snapshot: {result.returncode}, {result.stderr[:200]!r}')
    snapshot = result.stdout[-size:]
    result.stdout = result.stdout[:-size]
    return result, snapshot


def decode_trace(raw):
    """Decode copycode-emitted binary records to copy-space-shaped text.

    Input coordinates are *positional data channels*, not old IN/OUT slots.
    Tick numbers exclude diagnostic microsteps. Host conversion only formats
    events already emitted by copycode; it never observes emulator memory.
    """
    if len(raw) < 21 or raw[:4] != b'PCS1':
        raise ValueError('not a PCS1 trace')
    bits, slots, channels_only = struct.unpack_from('<QQB', raw, 4)
    fmt = Format(bits, slots)
    _, _, rsp = protocol(bits)
    at, copies, channels = 21, 0, 0
    pending, lines, last_tick = {}, [], 0
    def take(n):
        nonlocal at
        if at+n > len(raw):
            raise ValueError('truncated trace')
        data = raw[at:at+n]
        at += n
        return data
    while at < len(raw):
        kind = take(1)
        if kind == b'T':
            if pending:
                raise ValueError('missing channel status')
            tick, ncopy, nchannel = struct.unpack('<QQQ', take(24))
            if tick != last_tick+1:
                raise ValueError('nonsequential trace tick')
            last_tick = tick
            copies += ncopy
            if channels_only:
                for _ in range(nchannel):
                    slot, n, dst, src = struct.unpack('<QQQQ', take(32))
                    if slot >= slots-1 or not n or max(dst, src) <= bits or (tick, slot) in pending:
                        raise ValueError('invalid channel instruction')
                    pending[(tick, slot)] = (n, dst, src)
            else:
                image = take(fmt.layer_bytes)
                actual_copies = 0
                for slot in range(slots-1):
                    pos = slot*fmt.isz
                    n = field(image, pos, fmt.z)
                    dst = field(image, pos+fmt.z, fmt.a)
                    src = field(image, pos+fmt.z+fmt.a, fmt.a)
                    if not n:
                        continue
                    if max(dst, src) >= bits:
                        pending[(tick, slot)] = (n, dst, src)
                    else:
                        actual_copies += 1
                        lines.append(f'copy {tick} {slot} {n} {dst} {src}')
                if actual_copies != ncopy:
                    raise ValueError('copy count mismatch')
            if len(pending) != nchannel:
                raise ValueError('channel count mismatch')
        elif kind == b'S':
            tick, slot = struct.unpack('<QQ', take(16))
            if (tick, slot) not in pending:
                raise ValueError('unexpected channel status')
            n, dst, src = pending.pop((tick, slot))
            data = take((rsp[1]+7)//8)
            values = {name: field(data, off, width) for name, (off, width) in rsp[0].items()}
            channels += 1
            # Old format's dst is the memory buffer, copied is a bit count.
            buf = src if dst > bits else dst
            channel = dst if dst > bits else src
            lines.append(f'channel {tick} {channel} {n} {buf} {values["moved"]*8} {int(values["status"] != 0)}')
        elif kind == b'X':
            reason = take(1)[0]
            if reason > 1 or pending or at != len(raw):
                raise ValueError('invalid stop record')
            if channels_only:
                lines.append(f'counts {copies} {channels}')
            lines.append('stop '+('limit' if reason else 'idle'))
            return '\n'.join(lines)+'\n'
        else:
            raise ValueError('unknown trace record')
    raise ValueError('trace has no cooperative stop record (host limit or interrupted run)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    boot = sub.add_parser('boot', help='wrap a raw image or snapshot as a stdin boot stream')
    boot.add_argument('-s', type=int, required=True)
    boot.add_argument('-p', type=int, required=True)
    boot.add_argument('image', type=Path)
    boot.add_argument('-o', type=Path, required=True)
    boot.add_argument('--dense', action='store_true', help='also install all-zero chunks')
    decode = sub.add_parser('decode', help='format copycode debug output as text')
    decode.add_argument('trace', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'boot':
            with args.image.open('rb') as source, args.o.open('wb') as target:
                for chunk in iter_boot(source, args.s, args.p, sparse=not args.dense):
                    target.write(chunk)
        else:
            sys.stdout.write(decode_trace(args.trace.read_bytes()))
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
