#!/usr/bin/env python3
"""In-space SYS driver copycode generator.

Builds a copy program (the in-space driver) that exercises the SYS
request/answer path from inside the space:

  * builds a FSTAT request record with ordinary copies (op and chan fields
    are copied from disjoint constant storage);
  * issues the request: a copy with dst = SYS and src = the record address;
  * reads the answer: a copy with dst = the answer buffer and src = SYS;
  * outputs the answer record to the stdout data channel.

Tick rule: a write to a processor position takes effect from the next tick,
so request construction, submission, answer retrieval and output use separate layers.
The finite program emits an initial zero response then three FSTAT responses.

Order rule: every tick performs only copies whose half-intervals are
disjoint, so the result does not depend on the order of copies inside a
tick.

Format matches the emulator: a = bit_length(space_bits), z = a - 1,
isz = 2*a + z. Record fields follow proto.def: REQ op(8) chan(ADDR)
flags(16) arg(32) off(64); RSP op(8) status(8) flags(16) size(64) moved(NF)
eof(1).
"""
import argparse
import sys

from .machine import describe


def format_of(space_bits):
    a = space_bits.bit_length()
    if a < 8:
        raise ValueError("space too small for the SYS driver (need address bits >= 8)")
    return a, a - 1, 2 * a + (a - 1)


def build(space_bits, proc_n):
    a, z, isz = format_of(space_bits)
    if proc_n < 16:
        raise ValueError("proc_n too small for the driver")
    description = describe(space_bits, proc_n)
    sys_pos = description['channels']['sys']
    out_pos = next(d['position'] for d in description['channels']['devices']
                   if d['name'] == 'stdout')
    if out_pos >= (1 << a):
        raise ValueError("no room for the stdout channel")

    # record layouts from proto.def, resolved against the space size
    req_bits = description['records']['req']['bits']
    rsp_bits = description['records']['rsp']['bits']

    from .boundary import Program, boot_stream, record as encode_record
    record=(proc_n*isz+7)//8*8
    answer=record+((req_bits+7)//8)*8
    # Use eight active slots; the rest of the configured processor stays
    # zero. Compact links leave room for separate request/reply ticks.
    program = Program(space_bits,8,code_base=record+512)
    op_const=program.allocate(encode_record(({'v':(0,8)},8),{'v':3}))
    chan_const=program.allocate(encode_record(({'v':(0,a)},a),{'v':out_pos}))
    program.step([(8,record,op_const),(a,record+8,chan_const),(rsp_bits,answer,sys_pos)])
    program.step([(((rsp_bits+7)//8)*8,out_pos,answer)])
    for _ in range(3):
        program.step([(req_bits,sys_pos,record)])
        program.step([(rsp_bits,answer,sys_pos)])
        program.step([(((rsp_bits+7)//8)*8,out_pos,answer)])
    program.halt()
    image=boot_stream(program.finish(),space_bits,proc_n)
    meta=dict(a=a,z=z,isz=isz,req_bits=req_bits,rsp_bits=rsp_bits,record=record,
              answer=answer,sys_pos=sys_pos,out_pos=out_pos,records=4)

    return image, meta


def emit(image, out):
    if out == "-":
        sys.stdout.buffer.write(image)
    else:
        with open(out, "wb") as f:
            f.write(image)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-s", "--space", type=int, required=True)
    ap.add_argument("-p", "--proc", type=int, required=True)
    ap.add_argument("-o", "--out", default="-")
    args = ap.parse_args()

    image, meta = build(args.space, args.proc)
    emit(image, args.out)
    sys.stderr.write("sys_driver: " +
                     " ".join("%s=%s" % kv for kv in meta.items()) + "\n")


if __name__ == "__main__":
    main()
