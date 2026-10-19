"""Assembler of emulator pseudo-instructions. Runtime computations remain copies (MIT)."""
from dataclasses import dataclass
from copycode.vm1.machine import Format, NOP, put
from copycode.vm1.schedule import Span, Copy, Task, plan
from copycode.vm1.optimize import optimize

class LayoutCapacityError(ValueError):
    """A larger emulator address arena is required for this generated program."""

@dataclass(frozen=True)
class Ref:
    name: str
    offset: int = 0
    def __add__(self, offset):return Ref(self.name,self.offset+offset)

@dataclass(frozen=True)
class Reg:
    at: int
    width: int
    def __add__(self,n):return Reg(self.at+n,self.width-n)

class Assembler:
    def __init__(self,fmt,data_base,data_limit,*,scheduling='optimize',arithmetic='hybrid'):
        self.f=fmt;self.nodes=[];self.labels={};self.blocks=[];self.tables=[]
        self.at=data_base;self.data_base=data_base;self.data_limit=data_limit;self.serial=0
        if scheduling not in ('none','schedule','optimize'):raise ValueError('unknown scheduling mode')
        if arithmetic not in ('ripple','prefix','hybrid'):raise ValueError('unknown arithmetic mode')
        self.scheduling=scheduling;self.arithmetic=arithmetic;self.fences=set();self.lookup_reads={}
        self.exports=set();self.records={}
    def name(self,prefix='n'):
        self.serial+=1;return f'{prefix}_{self.serial}'
    def alloc(self,bits,align=8,value=0):
        self.at=(self.at+align-1)//align*align
        result=Reg(self.at,bits);self.at+=bits
        if self.at>self.data_limit:raise LayoutCapacityError('microcode data exceeds its reserved arena')
        self.blocks.append((result.at,bits,value));return result
    def constant(self,value,width):return self.alloc(width,value=value&((1<<width)-1))
    def resolve(self,value):
        if isinstance(value,Ref):return self.labels[value.name]+value.offset
        return value
    def emit(self,rows=(),*,label=None,next=None,fence=False):
        label=label or self.name();self.nodes.append((label,list(rows),next))
        if fence:self.fences.add(label)
        return label
    def jump(self,target,*,label=None):return self.emit(label=label,next=target)
    def copy(self,width,dst,src):
        if not width:return
        self.emit([(dst,dst+width,src,src+width)])
    def set(self,dst,value,width=None):
        width=dst.width if width is None else width
        c=self.constant(value,width);self.copy(width,dst.at,c.at)
    def move(self,dst,src,width=None):self.copy(width or min(dst.width,src.width),dst.at,src.at)
    def dynamic(self,dl,dh,sl,sh):
        """Patch a future operation; the separating gap prevents code/link overlap."""
        target=self.name('copy')
        for k,value in enumerate((dl,dh,sl,sh)):
            if not isinstance(value,Reg):value=self.constant(value,self.f.a)
            if value.width<self.f.a:raise ValueError('dynamic endpoint is too narrow')
            self.copy(self.f.a,Ref(target,k*self.f.a),value.at)
        self.emit(fence=True) # Never fetch the layer whose fields this tick is patching.
        self.emit([NOP],label=target,fence=True)
    def gate(self,inputs,out,width,function):
        """Truth-table lookup, at most six input bits and two output bits.

        Deduplicate inputs before issuing patches: even gate fan-out cannot
        read a physical source twice in one layer.
        """
        unique=list(dict.fromkeys(inputs));indices=[unique.index(x) for x in inputs]
        if len(unique)>6 or width not in (1,2):raise ValueError('unsupported truth table')
        stride=1<<width
        table=self.alloc(stride*(1<<len(unique)),align=stride*(1<<len(unique)))
        value=0
        for index in range(1<<len(unique)):
            args=[(index>>j)&1 for j in indices];result=function(args)
            for bit in range(width):value|=((result>>bit)&1)<<(index*stride+bit)
        self.blocks[-1]=(table.at,table.width,value)
        target=self.name('lut')
        for endpoint in (2,3):
            rows=[]
            for k,source in enumerate(unique):
                dst=Ref(target,endpoint*self.f.a+width+k)
                rows.append((dst,dst+1,source,source+1))
            self.emit(rows)
        self.emit()
        self.emit([(out,out+width,table.at,table.at+width)],label=target)
        self.lookup_reads[target]=(table.at,table.at+table.width)
    def eq(self,source,value,width,out):
        self.set(out,1,1)
        for start in range(0,width,5):
            count=min(5,width-start);expected=(value>>start)&((1<<count)-1)
            self.gate([out.at]+[source+start+k for k in range(count)],out.at,1,
                      lambda v,e=expected:v[0] & (sum(x<<i for i,x in enumerate(v[1:]))==e))
    def compare(self,left,right,width,out):
        """Unsigned >=. right is a constant or an address of another field."""
        state=self.alloc(2);self.set(state,0)
        constant=isinstance(right,int)
        for end in range(width,0,-(4 if constant else 2)):
            start=max(0,end-(4 if constant else 2));count=end-start
            inputs=[state.at,state.at+1]+[left+start+k for k in range(count)]
            if not constant:inputs += [right.at+start+k for k in range(count)]
            def truth(v,c=count,s=start):
                old=v[0]+2*v[1]
                if old:return old
                a=sum(x<<i for i,x in enumerate(v[2:2+c]))
                b=(right>>s)&((1<<c)-1) if constant else sum(x<<i for i,x in enumerate(v[2+c:]))
                return 0 if a==b else 1 if a<b else 2
            self.gate(inputs,state.at,2,truth)
        self.gate([state.at],out.at,1,lambda v:1-v[0])
    def add(self,left,right,out,width,carry=None):
        if self.arithmetic in ('prefix','hybrid'):return self.add_many([(left,right,out,width,carry)])
        return self.add_ripple(left,right,out,width,carry)
    def add_ripple(self,left,right,out,width,carry=None):
        """Ripple full-adder, optionally with a constant right operand."""
        pair=self.alloc(2);self.set(pair,0)
        constant=isinstance(right,int)
        for k in range(width):
            inputs=[left+k,pair.at+1]
            if not constant:inputs.append(right.at+k)
            def truth(v,bit=k):
                total=v[0]+v[1]+(((right>>bit)&1) if constant else v[2])
                return (total&1)|((total>>1)<<1)
            self.gate(inputs,pair.at,2,truth)
            self.copy(1,out+k,pair.at)
        if carry is not None:self.copy(1,carry,pair.at+1)
    def add_many(self,operations):
        """Blocked Brent-Kung adders; physical fan-out remains scheduled.

        Two variable bits or four constant-operand bits per block. Prefix
        reduction/distribution uses linear work and logarithmic logic depth.
        """
        if self.arithmetic=='ripple' or (self.arithmetic=='hybrid' and len(operations)>1):
            for args in operations:self.add_ripple(*args)
            return
        for left,right,out,width,carry in operations:
            constant=isinstance(right,int)
            if constant:
                right&=(1<<width)-1
                suffix=width if not right else (right&-right).bit_length()-1
                if suffix and out!=left:self.copy(suffix,out,left)
                if suffix==width:
                    if carry is not None:self.set(Reg(carry,1),0)
                    continue
                left+=suffix;out+=suffix;right>>=suffix;width-=suffix
            saved=self.alloc(width);self.copy(width,saved.at,left);left=saved.at
            if not constant:
                saved=self.alloc(width);self.copy(width,saved.at,right.at);right=saved
            block=4 if constant else 2;original=[];groups=[]
            for start in range(0,width,block):
                count=min(block,width-start);groups.append((start,count))
                pair=self.alloc(2);original.append(pair)
                inputs=[left+start+k for k in range(count)]
                if not constant:inputs += [right.at+start+k for k in range(count)]
                def initial(v,start=start,count=count):
                    a=sum(x<<i for i,x in enumerate(v[:count]))
                    other=(right>>start)&((1<<count)-1) if constant else sum(x<<i for i,x in enumerate(v[count:]))
                    return int((a^other)==(1<<count)-1)|(int(a+other>=1<<count)<<1)
                self.gate(inputs,pair.at,2,initial)
            current=original
            def combine(k,shift):
                pair=self.alloc(2)
                self.gate([current[k].at,current[k].at+1,current[k-shift].at,current[k-shift].at+1],
                          pair.at,2,lambda v:(v[0]&v[2])|((v[1]|(v[0]&v[3]))<<1))
                return pair
            shift=1
            while shift<len(groups):
                following=list(current)
                for k in range(2*shift-1,len(groups),2*shift):following[k]=combine(k,shift)
                current=following;shift*=2
            shift//=4
            while shift:
                following=list(current)
                for k in range(3*shift-1,len(groups),2*shift):following[k]=combine(k,shift)
                current=following;shift//=2
            zero=self.constant(0,1)
            for group,(start,count) in enumerate(groups):
                carry_bit=current[group-1].at+1 if group else zero.at
                for offset in range(0,count,2):
                    bits=min(2,count-offset);needed=offset+bits
                    inputs=[left+start+k for k in range(needed)]
                    if not constant:inputs += [right.at+start+k for k in range(needed)]
                    inputs.append(carry_bit)
                    def summed(v,start=start,needed=needed,offset=offset,bits=bits):
                        a=sum(x<<i for i,x in enumerate(v[:needed]))
                        other=(right>>start)&((1<<needed)-1) if constant else sum(x<<i for i,x in enumerate(v[needed:2*needed]))
                        return ((a+other+v[-1])>>offset)&((1<<bits)-1)
                    self.gate(inputs,out+start+offset,bits,summed)
            if carry is not None:self.copy(1,carry,current[-1].at+1)
    def reduce_or(self,inputs,out):
        inputs=list(inputs)
        if not inputs:self.set(Reg(out,1),0);return
        while len(inputs)>6:
            following=[]
            for start in range(0,len(inputs),6):
                temp=self.alloc(1);self.gate(inputs[start:start+6],temp.at,1,lambda v:int(any(v)))
                following.append(temp.at)
            inputs=following
        self.gate(inputs,out,1,lambda v:int(any(v)))
    def branch(self,bit,yes,no):
        # The two rows have the same low/high selector bit: stride > layer_bits.
        stride=1<<self.f.layer_bits.bit_length();k=stride.bit_length()-1
        table=self.alloc(2*stride,align=2*stride);self.tables.append((table.at,no,yes,stride))
        target=self.name('branch')
        for endpoint in (2,3):
            dst=Ref(target,endpoint*self.f.a+k)
            self.copy(1,dst,bit)
        self.emit(fence=True)
        self.emit([(0,self.f.layer_bits,table.at,table.at+self.f.layer_bits)],label=target,next=False,fence=True)
    def assemble(self):
        if self.scheduling!='none':return self.assemble_scheduled()
        f=self.f
        for i,(name,_,_) in enumerate(self.nodes):
            if name in self.labels:raise ValueError('duplicate label '+name)
            self.labels[name]=(i+1)*f.layer_bits
        self.records=dict(self.labels)
        code_end=(len(self.nodes)+1)*f.layer_bits
        if code_end>self.data_base:raise LayoutCapacityError(f'microcode needs {code_end} code bits, arena has {self.data_base}')
        image=bytearray(f.image_bytes)
        for at,bits,value in self.blocks:put(image,at,bits,value)
        def jump(target):return f.layer([f.copy(f.layer_bits,0,self.labels[target])])
        for at,no,yes,stride in self.tables:
            image[at//8:at//8+f.layer_bytes]=jump(no)
            image[(at+stride)//8:(at+stride)//8+f.layer_bytes]=jump(yes)
        for i,(name,rows,next) in enumerate(self.nodes):
            rows=[tuple(self.resolve(x) for x in row) for row in rows]
            if next is not False:
                following=next if next is not None else (self.nodes[i+1][0] if i+1<len(self.nodes) else None)
                if following:rows+=[NOP]*(f.slots-1-len(rows))+[f.copy(f.layer_bits,0,self.labels[following])]
            at=self.labels[name]//8
            try:image[at:at+f.layer_bytes]=f.layer(rows)
            except ValueError as e:raise ValueError(f'{name} ({i}): {e}; {rows}') from e
        image[:f.layer_bytes]=jump(self.nodes[0][0])
        return image,dict(code_bits=code_end,data_bits=self.at-self.data_base,nodes=len(self.nodes),labels=self.labels)

    def assemble_scheduled(self):
        f=self.f;controls={self.nodes[0][0]}|self.exports
        controls.update(n for _,_,n in self.nodes if isinstance(n,str))
        controls.update(n for _,no,yes,_ in self.tables for n in (no,yes))
        referenced={x.name for _,rows,_ in self.nodes for row in rows for x in row if isinstance(x,Ref)}
        if len({n for n,_,_ in self.nodes})!=len(self.nodes):raise ValueError('duplicate label')
        def span(lo,hi):
            if isinstance(lo,Ref):
                if not isinstance(hi,Ref) or hi.name!=lo.name:raise ValueError('mixed symbolic range')
                return Span(('code',lo.name),lo.offset,hi.offset)
            return Span('memory',lo,hi)
        def task(node):
            name,rows,_=node
            copies=tuple(Copy(span(dl,dh),span(sl,sh)) for dl,dh,sl,sh in rows if (dl,dh,sl,sh)!=NOP)
            extra=tuple(Span('memory',*self.lookup_reads[name]) for _ in [0] if name in self.lookup_reads)
            return Task(name,copies,(Span(('code',name),0,max(1,len(rows))*4*f.a),),extra,
                        name in referenced or name in controls or bool(extra))
        # Each chunk has one entry and no observable control transfer inside.
        # Unknown dynamic copies, channels and branches remain explicit fences.
        chunks=[];current=[]
        for node in self.nodes:
            name,rows,next=node
            channel=any(isinstance(x,int) and x>=f.size for row in rows for x in (row[0],row[2]))
            isolated=name in self.fences or channel or next is not None
            if (name in controls or isolated) and current:chunks.append((current,False));current=[]
            if isolated:chunks.append(([node],True))
            else:current.append(node)
        if current:chunks.append((current,False))
        layers=[];entries={};record={};original_rows=sum(len(r) for _,r,_ in self.nodes)
        for nodes,isolated in chunks:
            if isolated:
                name,rows,next=nodes[0];groups=[[(name,rows)]]
            else:
                tasks=[task(node) for node in nodes]
                planned=(optimize if self.scheduling=='optimize' else plan)(tasks,f.slots-1)
                def endpoint(s,end=False):
                    at=s.hi if end else s.lo
                    return at if s.arena=='memory' else Ref(s.arena[1],at)
                groups=[]
                for group in planned:
                    members=[]
                    for t in group:
                        rows=[(endpoint(c.dst),endpoint(c.dst,True),endpoint(c.src),endpoint(c.src,True)) for c in t.copies]
                        members.append((t.name,rows))
                    groups.append(members)
                if not groups:groups=[[]]
                next=None
            start=len(layers)
            # Entries are layer addresses; Ref points to a particular instruction
            # within that layer. These are deliberately distinct namespaces.
            entries[nodes[0][0]]=start
            for group in groups:
                slot=0
                for name,rows in group:
                    record[name]=(len(layers)+1)*f.layer_bits+slot*4*f.a
                    slot+=len(rows)
                layers.append((group,None))
            layers[-1]=(layers[-1][0],next)
        self.records=record
        self.labels={name:(level+1)*f.layer_bits for name,level in entries.items()}
        code_end=(len(layers)+1)*f.layer_bits
        if code_end>self.data_base:raise LayoutCapacityError(f'microcode needs {code_end} code bits, arena has {self.data_base}')
        def resolve(x):return record[x.name]+x.offset if isinstance(x,Ref) else x
        image=bytearray(f.image_bytes)
        for at,bits,value in self.blocks:put(image,at,bits,value)
        def jump(target):return f.layer([f.copy(f.layer_bits,0,self.labels[target])])
        for at,no,yes,stride in self.tables:
            image[at//8:at//8+f.layer_bytes]=jump(no)
            image[(at+stride)//8:(at+stride)//8+f.layer_bytes]=jump(yes)
        emitted=0
        for i,(group,next) in enumerate(layers):
            rows=[tuple(resolve(x) for x in row) for _,rs in group for row in rs];emitted+=len(rows)
            if next is not False:
                following=self.labels[next] if isinstance(next,str) else ((i+2)*f.layer_bits if i+1<len(layers) else None)
                if following is not None:rows += [NOP]*(f.slots-1-len(rows))+[f.copy(f.layer_bits,0,following)]
            at=(i+1)*f.layer_bits//8
            try:image[at:at+f.layer_bytes]=f.layer(rows)
            except ValueError as e:raise ValueError(f'scheduled layer {i}: {e}; {rows}') from e
        image[:f.layer_bytes]=jump(self.nodes[0][0])
        return image,dict(code_bits=code_end,data_bits=self.at-self.data_base,nodes=len(layers),labels=self.labels,
                          scheduling=self.scheduling,input_nodes=len(self.nodes),input_copies=original_rows,output_copies=emitted)
