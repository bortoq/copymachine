"""Finite layered copycode. This generator does not execute guest arithmetic."""
from .machine import Format
from .boot import boot_stream

class Program:
    def __init__(self, fmt=Format()):
        if fmt.layer_bits%8 or fmt.size%8:raise ValueError('byte-sized layout required')
        self.fmt=fmt;self.layers=[];self.data=[]
    def layer(self,rows=()):
        if len(rows)>=self.fmt.slots:raise ValueError('last slot reserved for link')
        self.layers.append(list(rows));return (len(self.layers)-1)*self.fmt.layer_bits
    def store(self,at,data):
        if at%8 or at<0 or at+len(data)*8>self.fmt.size:raise ValueError('data bounds/alignment')
        self.data.append((at,bytes(data)))
    def image(self):
        f=self.fmt;image=bytearray(f.image_bytes)
        code_end=(len(self.layers)+1)*f.layer_bits
        for at,data in self.data:
            if at<code_end:raise ValueError('data overlaps program')
            image[at//8:at//8+len(data)]=data
        for i,rows in enumerate(self.layers):
            at=i*f.layer_bits//8
            image[at:at+f.layer_bytes]=linked_layer(f,rows,(i+1)*f.layer_bits)[0]
        return bytes(image)
    def boot(self):return boot_stream(self.image(),self.fmt)

def linked_layer(fmt, rows, following):
    """Serialize an observing operation when its source includes the link layer."""
    rows=list(rows)
    direct=rows+[fmt.copy(fmt.layer_bits,0,following)]
    try:return fmt.layer(direct),1
    except ValueError:
        active=[r for r in rows if r[2]!=r[3] or (r[2]>=fmt.size and r[0]!=r[1])]
        if len(active)!=1 or fmt.slots<8:raise ValueError('cannot serialize conflicting control link')
        inst=fmt.instruction_bits
        result=[active[0],fmt.copy(3*inst,0,4*inst),
                fmt.copy(fmt.a,3*inst+3*fmt.a,7*inst),
                (0,fmt.layer_bits,following,following),
                (0,0,0,0),(0,0,0,0),(0,0,0,0),
                (following+fmt.layer_bits,0,0,0)]
        return fmt.layer(result),2
