#!/usr/bin/env python3
"""Minimal finite emulator stdin program, not an image parser or application SDK."""
import argparse
import sys
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('-s',type=int,default=65520)
parser.add_argument('-p',type=int,default=128)
parser.add_argument('--write',default='A')
args=parser.parse_args()
a=args.s.bit_length(); inst=4*a
payload=args.write.encode()
if len(payload)!=1 or a<8 or args.p<6 or args.p*inst>args.s or args.s+5>=1<<a:
    parser.error('need one byte, >=6 slots and a fitting processor/channel table')
image=bytearray((args.p*inst+7)//8)
def field(at,value):
    for k in range(a):
        if value>>k&1: image[(at+k)//8]|=128>>((at+k)%8)
def instruction(slot,fields):
    for k,value in enumerate(fields): field((slot*4+k)*a,value)
instruction(0,(args.s+2,args.s+2,3*inst,3*inst+8))
instruction(1,(0,2*inst,4*inst,6*inst))
# NOP fields carry data; slots 4/5 supply disjoint zero words for the halt.
field(3*inst,int(f'{payload[0]:08b}'[::-1],2))
sys.stdout.buffer.write(image)
