"""AOT lowering: copycode is built once; emulator executes only stored pseudo-instructions."""
from dataclasses import replace
import copy,hashlib,json
from pathlib import Path
from copycode.vm1.machine import Format,NOP,put,field
from copycode.vm1.assembler import Assembler,Reg,Ref,LayoutCapacityError
from copycode.vm1.program import linked_layer
from copycode.vm1.boot import boot_stream
from .model import Program,Copy,Memory,Field,Channel,Replace,Value,LayerBits,SysWidth

from .abi import ABI
FIELDS=('n','dst','src')
CHANNELS=('sys','stdin','stdout','debug','status','snapshot')

class Compiler:
    def __init__(self,program,size):
        self.p=program
        slots=max(8,max((len(l.copies)+1+sum(3*len(program.layers[c.dst].copies) for c in l.copies if isinstance(c,Replace) and c.dst in program.layers)+int(isinstance(l.following,Memory)) for l in program.layers.values()),default=8))
        slots+=slots%2
        self.f=Format(size,slots);f=self.f
        if f.layer_bits%8 or size%8:raise ValueError('direct ABI requires byte-sized space and processor')
        if not isinstance(program.limit,int) or not 0<=program.limit<1<<64:raise ValueError('invalid logical limit')
        self.b=Assembler(f,1<<(f.a-2),1<<(f.a-1),scheduling='optimize',arithmetic='hybrid')
        self.memory={};self.record_fields={};self.state={};self.changes={};self.replaced={};self.checkpoints=[];self.relocs=[]
        self.origins=self.b.alloc(64)
        self.counter=self.b.alloc(64) if program.limit else None
        self.body_labels={name:'body:'+name for name in program.layers}
        self.b.exports.update(self.body_labels.values())
        self.compile_labels={};self.map_ops={};self.selectors={};self.masks={};self.replacement_targets=set()
    def width(self,n):
        if isinstance(n,LayerBits):return self.f.layer_bits
        if isinstance(n,SysWidth):
            if n.kind not in ('req','rsp'):raise ValueError('SYS record kind')
            return (120 if n.kind=='req' else 97)+self.f.a
        if n=='address':return self.f.a
        if n=='count':return self.f.a-1
        if not isinstance(n,int) or isinstance(n,bool) or n<0:raise ValueError('invalid copy width')
        return n
    def key(self,ref):
        if not isinstance(ref,Field) or ref.name not in FIELDS or ref.offset<0:raise ValueError('invalid logical field')
        if ref.layer not in self.p.layers or not 0<=ref.slot<len(self.p.layers[ref.layer].copies):raise ValueError('unknown field target')
        if not isinstance(self.p.layers[ref.layer].copies[ref.slot],Copy):raise ValueError('fields belong to copy instructions')
        return ref.layer,ref.slot
    def address(self,ref,n=0):
        if isinstance(ref,Memory):
            if ref.name not in self.memory:raise ValueError('unknown region '+ref.name)
            r=self.memory[ref.name]
            offset=ref.offset
            if isinstance(offset,str):
                if ref.name not in self.record_fields or offset not in self.record_fields[ref.name]:raise ValueError('unknown record field')
                offset,width=self.record_fields[ref.name][offset]
                if n>width:raise ValueError('record field width exceeded')
            if not isinstance(offset,int) or offset<0 or offset+n>r.width:raise ValueError('data reference outside '+ref.name)
            return r.at+offset
        if isinstance(ref,Channel):
            if ref.name not in CHANNELS:raise ValueError('unknown channel '+ref.name)
            return self.f.size+CHANNELS.index(ref.name)
        if isinstance(ref,Field):
            key=self.key(ref);width=self.f.a-1 if ref.name=='n' else self.f.a
            if ref.offset+n>width:raise ValueError('field slice out of bounds')
            return self.state[key][ref.name].at+ref.offset
        raise ValueError('raw code/data addresses are not the direct ABI; use symbolic references')
    def declarations(self):
        p,f,b=self.p,self.f,self.b
        if not p.layers or p.entry not in p.layers:raise ValueError('missing entry layer')
        if not isinstance(p.slots,int) or p.slots<1:raise ValueError('positive source slot budget required')
        for name,l in p.layers.items():
            if not isinstance(l.checkpoint_stop,bool) or l.checkpoint_stop and not l.checkpoint:raise ValueError('checkpoint_stop requires checkpoint')
            if len(l.copies)>p.slots:raise ValueError('source layer exceeds declared slot budget')
            if not name or not isinstance(name,str):raise ValueError('invalid layer name')
            if l.following is not None and not isinstance(l.following,(str,Memory)):raise ValueError('invalid continuation')
            if isinstance(l.following,str) and l.following not in p.layers:raise ValueError('unknown continuation')
            for op in l.copies:
                if isinstance(op,Copy):
                    n=self.width(op.n)
                    if n>=(1<<(f.a-1)) and not isinstance(op.n,(LayerBits,SysWidth)):
                        raise ValueError('copy count does not fit logical n field')
                    for ref in (op.src,op.dst):
                        if isinstance(ref,Field):self.key(ref);self.state.setdefault((ref.layer,ref.slot),None)
                    if n and isinstance(op.dst,Channel) and isinstance(op.src,Channel):raise ValueError('channel-to-channel copy')
                    if isinstance(op.dst,Field):self.changes.setdefault(name,{}).setdefault(self.key(op.dst),[]).append((op.dst.name,op.dst.offset,n))
                elif isinstance(op,Replace):
                    if op.dst not in p.layers or op.src not in p.layers or op.dst==op.src:raise ValueError('invalid layer replacement')
                    left,right=p.layers[op.dst],p.layers[op.src]
                    if len(left.copies)!=len(right.copies) or not all(isinstance(c,Copy) for c in left.copies+right.copies):raise ValueError('replacement requires equally shaped copy layers')
                    if p.limit or any(layer.checkpoint or isinstance(layer.following,Memory) or
                            any(isinstance(c.dst,Field) and self.width(c.n) for c in layer.copies)
                            for layer in (left,right)):
                        raise ValueError('replacement templates require static continuations and no layer-specific update/checkpoint/limit helpers')
                    self.replaced.setdefault(name,[]).append(op);self.replacement_targets.add(op.dst)
                else:raise ValueError('unknown source operation')
        for changes in self.changes.values():
            for (layer,slot),slices in changes.items():
                operation=p.layers[layer].copies[slot]
                if isinstance(operation.dst,Field) and any(attr in ('n','dst') for attr,_,width in slices if width):
                    raise ValueError('changing the width/destination of a field-update operation requires an explicit new source operation')
        for changes in self.changes.values():
            for key,slices in changes.items():
                masks=self.masks.setdefault(key,{attr:0 for attr in FIELDS})
                for attr,off,width in slices:masks[attr] |= ((1<<width)-1)<<off
        # Replacements must also copy the sparse logical state visible through Field.
        again=True
        while again:
            again=False
            for ops in self.replaced.values():
                for op in ops:
                    for slot in range(len(p.layers[op.dst].copies)):
                        keys=((op.dst,slot),(op.src,slot))
                        if any(k in self.state for k in keys):
                            for k in keys:
                                if k not in self.state:self.state[k]=None;again=True
        for name,r in p.regions.items():
            bits=f.a if r.bits==0 and r.relocations else self.width(r.bits)
            initial=r.value;local_relocs=[]
            if r.record is not None:
                fields={};bits=0
                for attr,width,value in r.record:
                    width=self.width(width)
                    if attr in fields or width<1:raise ValueError('invalid record fields')
                    fields[attr]=(bits,width)
                    if isinstance(value,Value):local_relocs.append((bits,width,value))
                    else:
                        if not isinstance(value,int) or not 0<=value<1<<width:raise ValueError('record value overflow')
                        initial|=value<<bits
                    bits+=width
                self.record_fields[name]=fields
            if not isinstance(bits,int) or bits<1 or not isinstance(r.align,int) or r.align<1:raise ValueError('invalid data allocation')
            if not isinstance(r.value,int) or not 0<=initial<1<<bits:raise ValueError('data initializer overflow')
            if r.at is None:reg=b.alloc(bits,align=r.align,value=initial)
            else:
                if not isinstance(r.at,int) or r.at%r.align or r.at< b.at or r.at+bits>b.data_limit:raise ValueError('absolute data must be in the declared data arena')
                reg=Reg(r.at,bits);b.blocks.append((reg.at,bits,initial));b.at=max(b.at,reg.at+bits)
            if any(reg.at<x.at+x.width and x.at<reg.at+reg.width for x in self.memory.values()):raise ValueError('overlapping data regions')
            self.memory[name]=reg
            for off,width,value in r.relocations+local_relocs:
                width=f.a if width=='address' else width
                if not isinstance(off,int) or not isinstance(width,int) or off<0 or width<1 or off+width>bits:raise ValueError('relocation bounds')
                self.relocs.append((reg.at+off,width,value))
        for key in self.state:self.state[key]={name:b.alloc(f.a) for name in FIELDS}
        # Initial fields are resolved only after every symbol has an address.
        for (name,slot),regs in self.state.items():
            op=p.layers[name].copies[slot]
            values=dict(n=self.width(op.n),dst=self.address(op.dst),src=self.address(op.src))
            for attr,reg in regs.items():b.blocks.append((reg.at,f.a,values[attr]))
        for name,l in p.layers.items():
            # Independent interval validation of the logical effect layer.
            spans=[];devices=set();requests=0
            for op in l.copies:
                if isinstance(op,Replace):
                    # Physical code spans are checked after placement and at execution.
                    # Symbolic whole-layer spans must already obey the logical
                    # src/src and write rules, even without sparse field state.
                    for target in (op.dst,op.src):
                        at=f.size+list(p.layers).index(target)*f.layer_bits
                        spans.append((at,at+f.layer_bits))
                    for slot in range(len(p.layers[op.dst].copies)):
                        if (op.dst,slot) in self.state:
                            for attr in FIELDS:
                                for key in ((op.dst,slot),(op.src,slot)):
                                    r=self.state[key][attr];spans.append((r.at,r.at+f.a))
                    continue
                n=self.width(op.n)
                if not n:continue
                channel=next((r for r in (op.dst,op.src) if isinstance(r,Channel)),None)
                width=n
                if channel:
                    if channel.name=='sys':
                        width=max(n,(120 if isinstance(op.dst,Channel) else 97)+f.a)
                        if isinstance(op.dst,Channel):requests+=1
                    else:
                        if channel.name in devices:raise ValueError('multiple operations on one data channel')
                        devices.add(channel.name);width=(n+7)//8*8
                for ref in (op.dst,op.src):
                    if not isinstance(ref,Channel):
                        at=self.address(ref,width);spans.append((at,at+width))
                        if ref is op.dst and any(isinstance(v,Value) and v.kind=='stdin-origin' and at<where+bits and where<at+width for where,bits,v in self.relocs):raise ValueError('stdin-origin relocation is immutable; compute dynamic offsets from an origin value instead')
            if isinstance(l.following,Memory):
                at=self.address(l.following,f.a);spans.append((at,at+f.a))
                self.selectors[name]=b.alloc(f.a)
            spans.sort()
            if requests>1 or any(hi>lo for (_,hi),(lo,_) in zip(spans,spans[1:])):raise ValueError('overlapping logical operands including sources/SYS')
    def row(self,op):
        if not self.width(op.n):return NOP
        n=self.width(op.n)
        if isinstance(op.dst,Channel) or isinstance(op.src,Channel):
            if not any(isinstance(r,Channel) and r.name=='sys' for r in (op.dst,op.src)):n=(n+7)//8*8
        return self.f.copy(n,self.address(op.dst),self.address(op.src))
    def refresh(self,key,changes):
        """Rebuild only the changed executable description, after source effects."""
        name,slot=key;p,f,b=self.p,self.f,self.b;op=p.layers[name].copies[slot];regs=self.state[key]
        target=self.body_labels[name];A=f.a;changed={attr for attr,_,n in changes if n}
        # Selected address bits can be copied to both endpoints without addition
        # when the fixed low part plus n cannot carry into those selector bits.
        masks=self.masks.get(key,{attr:0 for attr in FIELDS})
        stable=name not in self.replacement_targets
        if stable and not masks['n'] and changed and changed<={'dst','src'} and self.width(op.n)>0:
            possible=True
            for attr in changed:
                ref=getattr(op,attr);slices=[(off,n) for a,off,n in changes if a==attr and n]
                if not isinstance(ref,Memory):possible=False;break
                # Prove carry safety below the lowest bit changed anywhere,
                # not merely below this particular patch. Several separate
                # writes to higher selector bits then share the same proof.
                low=(masks[attr]&-masks[attr]).bit_length()-1;base=self.address(ref);count=self.width(op.n)
                if (base|masks[attr])+count>f.size or (base% (1<<low))+count>=1<<low:possible=False;break
            if possible:
                for attr,off,n in changes:
                    if not n:continue
                    endpoints=(0,1) if attr=='dst' else (2,3)
                    for endpoint in endpoints:b.copy(n,Ref(target,(slot*4+endpoint)*A+off),regs[attr].at+off)
                return 'bit-slices'
        def known_kind(attr):
            if not stable:return None
            ref=getattr(op,attr)
            if isinstance(ref,Channel):return 'channel' if not masks[attr] else None
            if isinstance(ref,(Memory,Field)) and (self.address(ref)|masks[attr])<f.size:return 'memory'
        kinds={attr:known_kind(attr) for attr in ('dst','src')}
        if all(kinds.values()) and list(kinds.values()).count('channel')<2:
            # Partial address patches stay inside a proven memory arena. Avoid
            # device classification, and touch only endpoints actually changed.
            channel=next((getattr(op,attr) for attr in ('dst','src') if kinds[attr]=='channel'),None)
            count=regs['n'] if masks['n'] else self.width(op.n)
            if channel is not None and channel.name!='sys':
                if isinstance(count,int):count=(count+7)//8*8
                else:
                    rounded=b.alloc(A);b.add(count.at,7,rounded.at,A);b.set(Reg(rounded.at,3),0);count=rounded
            for endpoint,attr in ((0,'dst'),(2,'src')):
                initialize='n' in changed and self.width(op.n)==0
                if attr in changed or initialize:b.copy(A,Ref(target,(slot*4+endpoint)*A),regs[attr].at)
                if attr in changed or 'n' in changed:
                    if kinds[attr]=='channel':
                        if attr in changed or initialize:b.copy(A,Ref(target,(slot*4+endpoint+1)*A),regs[attr].at)
                    else:
                        upper=b.alloc(A);b.add(regs[attr].at,count,upper.at,A)
                        b.copy(A,Ref(target,(slot*4+endpoint+1)*A),upper.at)
            return 'memory-bounds'
        dl,dh,sl,sh=[b.alloc(A) for _ in range(4)]
        b.move(dl,regs['dst']);b.move(sl,regs['src'])
        dc,sc=b.alloc(1),b.alloc(1)
        empty=b.name('empty_copy');nonempty=b.name('nonempty_copy');zero=b.alloc(1)
        b.eq(regs['n'].at,0,A,zero);b.branch(zero.at,empty,nonempty)
        b.emit(label=nonempty)
        b.compare(regs['dst'].at,f.size,A,dc);b.compare(regs['src'].at,f.size,A,sc)
        memory=b.name('memory');destination=b.name('destination_channel');source=b.name('source_channel');done=b.name('bounds_ready')
        testsrc=b.name('test_source');b.branch(dc.at,destination,testsrc)
        b.emit(label=testsrc);b.branch(sc.at,source,memory)
        b.emit(label=memory);b.add(regs['dst'].at,regs['n'],dh.at,A);b.add(regs['src'].at,regs['n'],sh.at,A);b.jump(done)
        def channel_bounds(label,buffer,upper,device,other):
            b.emit(label=label);b.move(device,other)
            count=b.alloc(A);b.move(count,regs['n'])
            flag=b.alloc(1);plain=b.name('byte_channel');ready=b.name('channel_count')
            b.eq(other.at,f.size,A,flag);b.branch(flag.at,ready,plain)
            b.emit(label=plain);b.add(regs['n'].at,7,count.at,A);b.set(Reg(count.at,3),0)
            b.emit(label=ready);b.add(buffer.at,count,upper.at,A);b.jump(done)
        channel_bounds(destination,regs['src'],sh,dh,regs['dst'])
        channel_bounds(source,regs['dst'],dh,sh,regs['src'])
        b.emit(label=empty)
        for reg in (dl,dh,sl,sh):b.set(reg,0)
        b.jump(done)
        b.emit(label=done)
        for endpoint,reg in enumerate((dl,dh,sl,sh)):b.copy(A,Ref(target,(slot*4+endpoint)*A),reg.at)
        return 'bounds'
    def compile(self):
        self.declarations();p,f,b=self.p,self.f,self.b
        b.exports.add('halt')
        # A separate initial jump allows the independently audited bootstrap marker.
        b.jump(self.body_labels[p.entry],label='entry')
        methods={};replacement_rows={};checkpoint_maps=[]
        for name,l in p.layers.items():
            rows=[];indices=[]
            for slot,op in enumerate(l.copies):
                indices.append(len(rows))
                if isinstance(op,Copy):rows.append(self.row(op))
                else:
                    dst=Ref(self.body_labels[op.dst],0);src=Ref(self.body_labels[op.src],0)
                    rows.append((dst,dst+f.layer_bits,src,src+f.layer_bits))
                    for index in range(len(p.layers[op.dst].copies)):
                        if (op.dst,index) in self.state:
                            for attr in FIELDS:
                                d=self.state[op.dst,index][attr];r=self.state[op.src,index][attr]
                                rows.append(f.copy(f.a,d.at,r.at))
            if name in self.selectors:rows.append(f.copy(f.a,self.selectors[name].at,self.address(l.following,f.a)))
            if len(rows)>f.slots-1:raise ValueError('replacement state copies exceed native slots; increase source slots')
            self.map_ops[name]=indices
            # Every source copy occupies its declared source slot. Replacements
            # may add sparse-state copies, so patched targets must stay copy-only.
            if any(isinstance(c,Replace) for c in l.copies) and any(key[0]==name for key in self.state):raise ValueError('fields of replacement layers are unsupported')
            affected=self.changes.get(name,{})
            if affected or self.replaced.get(name) or p.limit or l.checkpoint or isinstance(l.following,Memory):
                after='after:'+name;b.emit(rows,label=self.body_labels[name],next=after,fence=True);b.emit(label=after)
                for key,changes in affected.items():methods[name+':'+str(key)]=self.refresh(key,changes)
                follow=l.following
                if p.limit:
                    b.add(self.counter.at,1,self.counter.at,64);flag=b.alloc(1);b.eq(self.counter.at,p.limit,64,flag)
                    more=b.name('continue');b.branch(flag.at,'halt',more);b.emit(label=more)
                if l.checkpoint:
                    if not isinstance(follow,(str,type(None))):raise ValueError('checkpoint needs a static continuation')
                    continuation=b.alloc(f.layer_bits)
                    b.emit([f.copy(f.layer_bits,f.channels['snapshot'],continuation.at)],fence=True)
                    label=b.name('snapshot_rest');b.emit(label=label,next=False,fence=True)
                    finish=b.name('snapshot_finish');b.emit(label=finish,fence=True)
                    self.checkpoints.append((label,continuation.at,follow,finish))
                    checkpoint_maps.append(dict(layer=name,continuation=follow))
                    if l.checkpoint_stop:
                        b.jump('halt')
                        continue
                if isinstance(follow,Memory):
                    source=self.selectors[name].at;end=b.alloc(f.a);b.add(source,f.layer_bits,end.at,f.a)
                    target=b.name('indirect')
                    b.copy(f.a,Ref(target,2*f.a),source);b.copy(f.a,Ref(target,3*f.a),end.at)
                    b.emit(fence=True);placeholder=b.alloc(f.layer_bits)
                    b.emit([(0,f.layer_bits,placeholder.at,placeholder.at+f.layer_bits)],label=target,next=False,fence=True)
                else:b.jump(self.body_labels[follow] if follow is not None else 'halt')
            else:b.emit(rows,label=self.body_labels[name],next=self.body_labels[l.following] if l.following is not None else 'halt',fence=True)
        b.emit(label='halt',next=False,fence=True)
        image,stats=b.assemble()
        labels={name:b.labels[label] for name,label in self.body_labels.items()}
        def relocate(value):
            if not isinstance(value,Value):raise ValueError('typed relocation value required')
            if value.kind=='entry':return labels[value.name]+value.offset
            if value.kind=='data':return self.address(Memory(value.name,value.offset))
            if value.kind=='channel':return self.address(Channel(value.name))+value.offset
            if value.kind=='stdin-origin':return 0
            raise ValueError('unknown relocation kind')
        for at,width,value in self.relocs:put(image,at,width,relocate(value))
        for label,at,following,finish in self.checkpoints:
            following=b.labels['halt'] if following is None else labels[following]
            image[at//8:at//8+f.layer_bytes]=f.layer([f.copy(f.layer_bits,0,following)])
            raw,_=linked_layer(f,[f.copy(f.size-f.layer_bits,f.channels['snapshot'],f.layer_bits)],b.labels[finish])
            home=b.labels[label]//8;image[home:home+f.layer_bytes]=raw
        source=p.source();source_layers={layer['name']:layer for layer in source['layers']}
        mapping=dict(schema='vm2-direct-map-v1',regions={name:dict(at=r.at,bits=r.width,fields=self.record_fields.get(name,{})) for name,r in self.memory.items()},
            layers={name:dict(at=labels[name],slots=self.map_ops[name],next=source_layers[name]['next']) for name in p.layers},
            fields={name+':'+str(slot):{attr:dict(at=r.at,bits=f.a-1 if attr=='n' else f.a) for attr,r in regs.items()} for (name,slot),regs in self.state.items()},
            updates=methods,checkpoints=checkpoint_maps)
        mutable=[(0,f.layer_bits)]
        for _,rows,_ in b.nodes:
            for dl,dh,_,_ in rows:
                if isinstance(dl,Ref):mutable.append((b.records[dl.name]+dl.offset,b.records[dh.name]+dh.offset))
        mutable.sort();merged=[]
        for lo,hi in mutable:
            if merged and lo<=merged[-1][1]:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
            else:merged.append((lo,hi))
        # Native executable pseudo-instructions are the entire processor ABI.
        from .sdk import protocol_path
        import copycode.vm1.optimize,copycode.vm1.assembler,copycode.vm1.schedule,copycode.vm1.machine,copycode.vm1.program
        dependencies={module.__name__:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() for module in (copycode.vm1.optimize,copycode.vm1.assembler,copycode.vm1.schedule,copycode.vm1.machine,copycode.vm1.program)}
        dependencies['emulator/proto.def']=hashlib.sha256(protocol_path().read_bytes()).hexdigest()
        manifest=dict(dependencies=dependencies,schema=ABI,vm1=f.describe(),entry_bits=b.labels['entry'],source_entry=p.entry,
            requested_size=p.size,source_slots=p.slots,code_bits=stats['code_bits'],data_bits=stats['data_bits'],
            logical_limit=p.limit,stdin_origin_bits=self.origins.at,mutable_code_ranges=merged,
            stdin_origin_relocations=[(at,width,v.offset) for at,width,v in self.relocs if isinstance(v,Value) and v.kind=='stdin-origin'],
            source_sha256=hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            boundary='native effect tick, then explicit description updates before the next source layer',
            vm1_tick_limit='physical ticks including bootstrap',external_channels='not part of raw memory snapshots')
        return bytes(image),manifest,mapping

def compile_program(program,*,exact_size=False):
    if not isinstance(program,Program):raise ValueError('Program required')
    if not isinstance(program.size,int) or program.size<128:raise ValueError('invalid minimum space size')
    size=program.size
    while True:
        try:return Compiler(program,size).compile()
        except LayoutCapacityError:
            if exact_size or size.bit_length()>=63:raise
            size=(1<<size.bit_length())*2-16
