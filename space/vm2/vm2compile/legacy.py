"""Explicit adapter for unencoded Copy/Field/Layout legacy generators (MIT).

Input blocks and data must be supplied by the owning project. No private
module import, guessing of executable bits, or execution of guest code occurs.
The default preserves a serial control. packing=True delegates independent
operations to copycode.vm1.schedule.plan; dynamic operands/channels are barriers.
"""
from .model import Program,Copy,Memory,Field,Value,Channel

def adapt(blocks,regions,*,address_bits,count_bits,entry,minimum_size=1048560,slots=8,address_literals=(),packing=False):
    """regions: dictionaries name/at/bits/value/align describing old data.

    Code references must be Field objects; block ends use the legacy Copy
    terminator with dst=0 and src=label, or a patched src field for dispatch.
    A (region,bit_offset) address_literals entry declares an address constant.
    """
    if not isinstance(packing,bool):raise ValueError('packing must be boolean')
    if entry not in blocks:raise ValueError('unknown legacy entry')
    p=Program(size=minimum_size,slots=slots);segments=[];objects={};terminators={};first={}
    for name,(ops,term) in blocks.items():
        if term is None or getattr(term,'dst',None)!=0:raise ValueError('unsupported legacy terminator')
        terminators[id(term)]=name
        first[name]='legacy:'+name+(':0' if ops else ':end')
        for index,op in enumerate(ops):
            if id(op) in objects:raise ValueError('one instruction object cannot have two homes')
            objects[id(op)]=('legacy:'+name+':'+str(index),0)
    scheduled={}
    if packing:
        from copycode.vm1.schedule import Span,Copy as SpanCopy,Task,plan
        dynamic={id(v.instruction) for ops,_ in blocks.values() for op in ops for v in (op.dst,)
                 if hasattr(v,'instruction')}
        def span(value,width):
            if isinstance(value,int):return Span('legacy-data',value,value+width)
            if hasattr(value,'instruction'):return Span(('legacy-field',id(value.instruction),value.name),value.offset,value.offset+width)
            raise ValueError('unknown scheduled operand')
        for name,(ops,term) in blocks.items():
            tasks=[];byname={}
            for index,op in enumerate(ops):
                key=str(index);byname[key]=op
                opaque=id(op) in dynamic or any(isinstance(v,Channel) for v in (op.src,op.dst)) or op.n==0
                width=op.n
                if any(hasattr(v,'instruction') and v.offset==0 and
                       ((v.name in ('src','dst') and width==address_bits) or (v.name=='n' and width==count_bits))
                       for v in (op.dst,op.src)):width=64 # conservative native-width relocation
                if opaque:
                    copies=(SpanCopy(span(op.dst,width),Span(('opaque',index),0,width)),) if width and hasattr(op.dst,'instruction') else (SpanCopy(Span(('opaque',index),0,1),Span(('opaque',index),1,2)),)
                else:copies=(SpanCopy(span(op.dst,width),span(op.src,width)),)
                fetch=tuple(Span(('legacy-field',id(op),attr),0,64) for attr in ('n','dst','src'))
                tasks.append(Task(key,copies,fetch,protected=True,barrier=opaque))
            groups=[[byname[t.name] for t in layer] for layer in plan(tasks,slots-1)]
            scheduled[name]=groups
            for layer,group in enumerate(groups):
                for slot,op in enumerate(group):objects[id(op)]=('legacy:'+name+':'+str(layer),slot)
    else:
        scheduled={name:[[op] for op in ops] for name,(ops,_) in blocks.items()}
    p.entry=first[entry]
    for source in regions:
        name,at,bits=source['name'],source['at'],source['bits']
        if not isinstance(at,int) or at<0 or bits<1 or any(at<hi and lo<at+bits for lo,hi,_ in segments):raise ValueError('invalid/overlapping legacy data declarations')
        ref=p.data(name,bits,source.get('value',0),align=source.get('align',8))
        segments.append((at,at+bits,ref))
        for offset,width,value in source.get('relocations',[]):
            if isinstance(value,str):value=Value('entry',first[value])
            p.regions[name].relocations.append((offset,width,value))
    def memory(at,n=0):
        for lo,hi,ref in segments:
            if lo<=at and at+n<=hi:return ref+(at-lo)
        raise ValueError('undeclared raw legacy address '+str(at))
    pointers={}
    for name,(_,term) in blocks.items():
        if not isinstance(term.src,str):pointers[name]=p.pointer('legacy-next:'+name,Value('entry',first[name]))
    def ref(value,n=0):
        if isinstance(value,Channel):return value
        if isinstance(value,int):return memory(value,n)
        if not all(hasattr(value,a) for a in ('instruction','name','offset')):raise ValueError('unsupported legacy address')
        target=value.instruction
        if id(target) in terminators:
            name=terminators[id(target)]
            if value.name!='src' or name not in pointers:raise ValueError('only declared dynamic terminator src can be patched')
            return pointers[name]+value.offset
        if id(target) not in objects:raise ValueError('field target is outside declared blocks')
        layer,slot=objects[id(target)]
        return Field(layer,slot,value.name,value.offset)
    # Replacing an address bit slice is invariant under relocation only if
    # the relocation preserves all lower bits through that slice. Old RV32I
    # memory/LUT builders rely on this alignment, not just data byte alignment.
    for ops,_ in blocks.values():
        for op in ops:
            dst=op.dst
            if not hasattr(dst,'instruction') or dst.name not in ('dst','src') or op.n>=address_bits:continue
            initial=getattr(dst.instruction,dst.name)
            if not isinstance(initial,int):continue
            required=1<<(dst.offset+op.n)
            for lo,hi,target in segments:
                if lo<=initial<hi:
                    if lo%required:raise ValueError('partial address relocation needs an aligned containing region: '+target.name)
                    p.regions[target.name].align=max(p.regions[target.name].align,required)
                    break
    for name,(ops,term) in blocks.items():
        groups=scheduled[name]
        for index,group in enumerate(groups):
            copies=[]
            for op in group:
                count=op.n
                fields=[x for x in (op.dst,op.src) if hasattr(x,'instruction')]
                if any(x.offset==0 and x.name in ('src','dst') and count==address_bits for x in fields):count='address'
                if any(x.offset==0 and x.name=='n' and count==count_bits for x in fields):count='count'
                n=op.n;dst=ref(op.dst,n);src=ref(op.src,n)
                copies.append(Copy(count,dst,src))
            p.layer('legacy:'+name+':'+str(index),copies,next='legacy:'+name+':'+str(index+1) if index+1<len(groups) else 'legacy:'+name+':end')
        following=first[term.src] if isinstance(term.src,str) else pointers[name]
        # A terminator with src=0 and no patch is the legacy halt layer.
        patched=any(any(getattr(x,'instruction',None) is term for x in (op.dst,op.src)) for block_ops,_ in blocks.values() for op in block_ops)
        if not isinstance(term.src,str) and term.src==0 and not patched:following=None
        p.layer('legacy:'+name+':end',next=following)
    for name,offset in address_literals:
        r=p.regions[name];mask=(1<<address_bits)-1;old=(r.value>>offset)&mask
        target=memory(old);r.value &= ~(mask<<offset)
        r.relocations.append((offset,'address',Value('data',target.name,target.offset)))
    return p
