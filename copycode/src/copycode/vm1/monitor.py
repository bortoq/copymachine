"""Cooperative live reports emitted by guest copies, not emulator observation."""
import struct

def emit(program, address, bits, device='debug'):
    if bits%8:raise ValueError('report length must be whole bytes')
    program.layer([program.fmt.copy(bits,program.fmt.channels[device],address)])

def status(program, address, code=0):
    """VMS1 + little-endian static exit code; emitted through inherited fd3."""
    program.store(address,b'VMS1'+struct.pack('<I',code))
    emit(program,address,64,'status')
