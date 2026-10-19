#!/usr/bin/env python3
"""
In-space driver generator for the channel model.

The host seeds slot 0 with an ordinary load copy (the seed) that reads the
image from the stdin channel. The image built here is an ordinary copy
program:

  --write TEXT   one output per tick from contiguous NOP payload fields.
                 Short text: seed then output, bounded with -t 2.
                 Long text: finite full-image boot, run without -t.
  --echo N       read into a memory buffer on tick 2, write on tick 3.
                 Run with `-t 3`; no same-tick read/write dependency.
  --nop          an all-NOP image (the simplest stub loader). The seed
                 copies it over the processor, so the space stops on the
                 next tick. Placeholder for the real loader (copy-space).

Channels are pre-bound by position (no OPEN): stdin = space+1, stdout =
space+2. Data bytes in the space are MSB-first; numeric instruction
fields are LSB-first. Layout constants match the
emulator: a = bit_length(space_bits), z = a - 1, isz = 2*a + z.
"""
import argparse
import sys

from .schedule import validate


def format_of(space_bits):
    a = space_bits.bit_length()
    if a < 8:
        raise ValueError("space too small for byte data (need address bits >= 8)")
    return a, a - 1, 2 * a + (a - 1)


def encode(prog, a, z):
    bits = []
    for n, dst, src in prog:
        bits += [(n >> k) & 1 for k in range(z)]
        bits += [(dst >> k) & 1 for k in range(a)]
        bits += [(src >> k) & 1 for k in range(a)]
    while len(bits) % 8:
        bits.append(0)
    out = bytearray()
    for i in range(0, len(bits), 8):
        b = 0
        for j in range(8):
            b = (b << 1) | bits[i + j]
        out.append(b)
    return bytes(out)


def build_write(space_bits, proc_n, data):
    a,z,isz=format_of(space_bits)
    if proc_n<2: raise ValueError('write needs at least two slots')
    if len(data)*8>2*a:
        from .boundary import Program,boot_stream
        program=Program(space_bits,proc_n)
        at=program.allocate(data)
        program.step([(len(data)*8,space_bits+2,at)])
        program.halt()
        return boot_stream(program.finish(),space_bits,proc_n),dict(a=a,z=z,isz=isz,boot=True)
    prog=[(0,0,0)]*proc_n
    start=isz+z
    prog[0]=(len(data)*8,space_bits+2,start)
    validate(prog,space_bits)
    image=bytearray(encode(prog,a,z))
    for j in range(len(data)*8):
        if data[j//8] & (128>>(j%8)): image[(start+j)//8] |= 128>>((start+j)%8)
    return bytes(image),dict(a=a,z=z,isz=isz,slots=2)


def build_nop(space_bits, proc_n):
    # an all-zero image is meaningful for any size; unlike --write/--echo it
    # needs no byte data, so it does not go through format_of (a < 8 is fine)
    a = space_bits.bit_length()
    z = a - 1
    isz = 2 * a + z
    nbits = proc_n * isz
    return bytes((nbits + 7) // 8), {"a": a, "z": z, "isz": isz, "bits": nbits}


def build_echo(space_bits, proc_n, nbytes):
    a,z,isz=format_of(space_bits)
    if proc_n<8: raise ValueError('echo needs eight slots')
    buf=(proc_n*isz+7)//8*8
    prog=[(0,0,0)]*proc_n
    prog[:8]=[(nbytes*8,buf,space_bits+1),(3*isz,0,4*isz),
              (z,3*isz,7*isz+z),(0,space_bits+2,buf),
              (0,0,0),(0,0,0),(0,0,0),(0,nbytes*8,0)]
    if nbytes < 0 or nbytes*8 >= 1<<z: raise ValueError("echo count does not fit")
    validate(prog,space_bits)
    return encode(prog,a,z),dict(a=a,z=z,isz=isz,buf=buf,ticks=3)


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
    ap.add_argument("--write", dest="write_text", help="text to write to stdout")
    ap.add_argument("--echo", type=int, metavar="N",
                    help="read N bytes from stdin and write them to stdout")
    ap.add_argument("--nop", action="store_true",
                    help="emit an all-NOP stub loader image")
    args = ap.parse_args()

    if ((args.write_text is None) + (args.echo is None) + (not args.nop)) != 2:
        ap.error("give exactly one of --write, --echo or --nop")

    if args.nop:
        image, info = build_nop(args.space, args.proc)
        emit(image, args.out)
        sys.stderr.write("driver: a=%d z=%d isz=%d nop bits=%d\n"
                         % (info["a"], info["z"], info["isz"], info["bits"]))
    elif args.write_text is not None:
        data = args.write_text.encode()
        image, info = build_write(args.space, args.proc, data)
        emit(image, args.out)
        sys.stderr.write("driver: a=%d z=%d isz=%d write=%r\n"
                         % (info["a"], info["z"], info["isz"], data))
    else:
        image, info = build_echo(args.space, args.proc, args.echo)
        emit(image, args.out)
        sys.stderr.write("driver: a=%d z=%d isz=%d echo=%d\n"
                         % (info["a"], info["z"], info["isz"], args.echo))


if __name__ == "__main__":
    main()
