#!/usr/bin/env python3
"""Provisional, versioned description of the space/copycode boundary.

This describes source contracts; it is not a handshake with a running binary.
Consumers configure PYTHONPATH independently of the emulator executable.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .protocol import parse

PROTOCOL = Path(__file__).with_name('legacy-proto.def')
SCHEMA = 'space-boundary-v1'


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def space_bits_for_bytes(image_bytes, *, protocol_path=PROTOCOL):
    """Reserve table positions without widening a byte-budget's address field."""
    if image_bytes < 1:
        raise ValueError('image byte budget must be positive')
    capacity = 1 + len(parse(protocol_path)[3])
    ceiling = image_bytes*8
    address_limit = 1 << ((ceiling-1).bit_length())
    bits = min(ceiling, address_limit-capacity)
    if bits < 1:
        raise ValueError('no room for space and channel table')
    return bits


def describe(space_bits, slots, *, protocol_path=PROTOCOL):
    """Resolve actual proto.def fields and device table for a machine layout."""
    if space_bits < 1 or slots < 1:
        raise ValueError('space bits and processor slots must be positive')
    a = space_bits.bit_length()
    if a > 64:
        raise ValueError('emulator fields are limited to 64 bits')
    z, isz = a-1, 3*a-1
    ops, req, rsp, devices = parse(protocol_path)
    layer_bits = slots*isz
    if layer_bits > min(space_bits, (1 << z)-1):
        raise ValueError('processor/seed does not fit')
    if space_bits+1+len(devices) > 1 << a:
        raise ValueError('no room for SYS and pre-bound devices')

    def fields(rows):
        at, resolved = 0, []
        for name, literal, kind in rows:
            width = literal if kind == 'PK_LIT' else a if kind == 'PK_ADDR' else z
            resolved.append(dict(name=name, offset_bits=at, width_bits=width))
            at += width
        return dict(bits=at, fields=resolved)

    contract = dict(schema=SCHEMA, status='provisional',
                    operations=dict(ops), symbolic_fields=dict(
                        req=[list(row) for row in req], rsp=[list(row) for row in rsp]),
                    devices=[dict(descriptor=d, name=n, direction=m, index=i+1)
                             for i, (d, n, m) in enumerate(devices)],
                    bit_order='msb-first-bytes-lsb-first-numeric-fields',
                    tick=dict(memory_intervals='all active source and destination intervals pairwise disjoint',
                              completion='tick-end',
                              sys_answer='response-committed-before-tick',
                              transfers_per_device=1, requests_per_sys=1,
                              fstat_seek_close_transfer_conflict='separate-ticks',
                              close_sys_answer='old-response-readable-in-close-tick'))
    result = dict(schema=SCHEMA, status='provisional', protocol_id=identity(contract),
                  contract=contract, space_bits=space_bits, image_bytes=(space_bits+7)//8,
                  processor=dict(start_bits=0, slots=slots, bits=layer_bits,
                                 packet_bytes=(layer_bits+7)//8),
                  instruction=dict(bits=isz, fields=[
                      dict(name=n, offset_bits=o, width_bits=w)
                      for n, o, w in [('n', 0, z), ('dst', z, a), ('src', z+a, a)]]),
                  records=dict(req=fields(req), rsp=fields(rsp)),
                  channels=dict(sys=space_bits, devices=[
                      dict(descriptor=d, name=n, direction=m, position=space_bits+1+i)
                      for i, (d, n, m) in enumerate(devices)]),
                  boot=dict(format='space-stdin-install-v2', min_slots=8,
                            supported=slots >= 8,
                            packet_bytes=(layer_bits+7)//8,
                            payload_max_bytes=((1 << z)-1)//8,
                            framing='processor-packet, payload; repeat; optional embedded tail-bit packet; entry-processor-packet',
                            padding='each packet and payload byte-padded; final packet includes shared data bits',
                            application_input='immediately after final processor packet'),
                  terminal=dict(format='SPT1', record_bytes=80, descriptor=3,
                                snapshot_descriptor=4, debug_descriptor=2,
                                header_format='<4sBBHQQ32s', header_bytes=56,
                                numeric_bit_order='space-fields',
                                fields=dict(exit_code=[56, 32], input_cursor=[60, 64],
                                            output_cursor=[68, 64], guest_status=[76, 32]),
                                snapshot_framing='raw image; length in terminal record',
                                publication='after snapshot; exactly one terminal record'))
    result['terminal']['extensions'] = dict(SPT2=dict(record_bytes=104,
        counters=dict(committed=[80, 64], read_ops=[88, 64], write_ops=[96, 64])))
    result['layout_id'] = identity(result)
    return result


def require_compatible(description, space_bits, slots, *, protocol_path=PROTOCOL):
    """Reject changed fields/devices, framing, version or machine parameters."""
    expected = describe(space_bits, slots, protocol_path=protocol_path)
    if description != expected:
        raise ValueError('incompatible boundary description (schema, protocol or layout changed)')
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-s', type=int, required=True)
    parser.add_argument('-p', type=int, required=True)
    parser.add_argument('--protocol', type=Path, default=PROTOCOL)
    parser.add_argument('--check', type=Path, help='require compatibility with a saved JSON description')
    args = parser.parse_args()
    try:
        desc = describe(args.s, args.p, protocol_path=args.protocol)
        if args.check:
            require_compatible(json.loads(args.check.read_text()), args.s, args.p,
                               protocol_path=args.protocol)
        print(json.dumps(desc, indent=2))
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
