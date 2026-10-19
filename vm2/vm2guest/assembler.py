"""Compatibility imports; the common vm1 pseudo-instruction assembler owns code."""
from copycode.vm1.assembler import Assembler,Reg,Ref,LayoutCapacityError

__all__=['Assembler','Reg','Ref','LayoutCapacityError']
