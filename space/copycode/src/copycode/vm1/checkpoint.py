"""Guest raw snapshot with an explicit continuation; host persists channels."""
from .monitor import emit

def snapshot(program, entry_address, continuation=()):
    f=program.fmt
    if f.size%8:raise ValueError('snapshot requires byte-sized space')
    program.store(entry_address,f.layer(continuation))
    emit(program,entry_address,f.layer_bits,'snapshot')
    # Code/link observation is serialized by linked_layer's processor-only step.
    emit(program,f.layer_bits,f.size-f.layer_bits,'snapshot')
    return f.image_bytes
