#!/usr/bin/env python3
"""Build a traced four-byte echo and a resumable terminal checkpoint."""
import argparse
from pathlib import Path

from boundary import Program, boot_stream


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', choices=('full', 'channels'), default='full')
    parser.add_argument('-o', type=Path, required=True, help='output stdin boot stream')
    args = parser.parse_args()
    program = Program(trace=args.trace, code_base=8192)
    buffer, zero = 1024, 2048
    program.step([(32, buffer, 65521)])
    program.step([(32, 65522, buffer)])
    program.checkpoint([(32, 65522, buffer), (program.fmt.layer_bits, 0, zero)], reason='limit')
    args.o.write_bytes(boot_stream(program.finish(), 65520, 8))


if __name__ == '__main__':
    main()
