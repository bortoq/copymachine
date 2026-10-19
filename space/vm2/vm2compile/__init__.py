"""Compile copycode [n,dst,src] to stored emulator pseudo-instructions (MIT)."""
# Reuse dependency discovery; no application or guest interpreter is executed.
import vm2guest
from .model import Program,Copy,Memory,Field,Channel,Replace,Value,LayerBits,SysWidth
