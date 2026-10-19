"""Generate the vm2 interpreter in ordinary four-index emulator copycode (MIT).

Only dimensions and generation options are inspected on the host. Instructions,
SYS requests and every virtual tick are decoded/executed inside emulator memory.
"""
from dataclasses import dataclass
import hashlib,json
from copycode.vm1.machine import Format,put
from copycode.vm1.boot import boot_stream
from .assembler import Assembler,Reg,Ref,LayoutCapacityError
from copycode.vm1.machine import NOP

@dataclass(frozen=True)
class Guest:
    size:int=65520
    slots:int=64
    def __post_init__(self):
        if self.size<1 or self.slots<1 or self.a>62 or self.layer_bits>min(self.size,(1<<self.z)-1) or self.size+6>1<<self.a or (self.layer_bits+7)//8*8>self.size:
            raise ValueError('invalid or unrepresentable vm2 configuration')
    @property
    def a(self):return self.size.bit_length()
    @property
    def z(self):return self.a-1
    @property
    def instruction_bits(self):return 3*self.a-1
    @property
    def layer_bits(self):return self.slots*self.instruction_bits

class Compiler:
    def __init__(self,guest=Guest(),*,ticks=0,snapshot=False,report=False,host_bits=None,input_offset=0,
                 scheduling='optimize',translation='parallel',arithmetic='hybrid',host_slots=None):
        if not 0<=ticks<1<<64 or input_offset<0:raise ValueError('invalid tick/input offset')
        self.g=guest;self.ticks=ticks;self.snapshot=snapshot;self.report=report;self.input_offset=input_offset
        width=max(24,guest.a+2)
        host_slots=8 if host_slots is None else host_slots
        self.f=Format((1<<width)-16 if host_bits is None else host_bits,host_slots)
        if host_slots<8:raise ValueError('vm2 interpreter needs at least eight emulator slots')
        if self.f.a<guest.a+2:raise ValueError('emulator address width must provide separate code and guest arenas')
        self.base=1<<(self.f.a-1);self.execbase=self.base+(1<<guest.a)
        if self.execbase+(1<<guest.z)+128+self.f.a>=self.f.size:raise ValueError('emulator space cannot fit the EXEC arena')
        self.asm=Assembler(self.f,1<<(self.f.a-2),self.base,scheduling=scheduling,arithmetic=arithmetic)
        self.translation=translation
        if translation not in ('serial','parallel'):raise ValueError('unknown translation mode')
        self.prefix=self.asm.alloc(64)
        self.negative_prefix=self.asm.alloc(64)
        self.offset=self.asm.alloc(64,value=input_offset)
    def build(self):
        g,f,b=self.g,self.f,self.asm;A=f.a;a=g.a;z=g.z;I=g.instruction_bits
        R=lambda n:b.alloc(n)
        flag=R(1);active=R(1);enabled=R(1);pending_enabled=R(1)
        counter=R(64);remaining=R(64)
        fetch=R(g.layer_bits);current=R(I)
        cursor=R(A);cursor_end=R(A);left=R(max(1,g.slots.bit_length()))
        n=R(A);dst=R(A);src=R(A);nround=R(A)
        dl=R(A);dh=R(A);sl=R(A);sh=R(A)
        temp=R(A);temp2=R(A);channel=R(a);mapped=R(A)
        guest_req=R(120+a);old=R(97+z);pending=R(97+z);host_rsp=R(97+A)
        qchan=Reg(guest_req.at+8,a);qop=Reg(guest_req.at,8)
        qarg=Reg(guest_req.at+24+a,32);qoff=Reg(guest_req.at+56+a,64)
        host_req=self.execbase
        stdin_cursor=R(64);stdin_size=R(64);seekable=R(1);seek_base=R(64);seek_target=R(64)
        def mark(name):b.emit(label=name)
        def eq_branch(at,value,width,yes,no):b.eq(at,value,width,flag);b.branch(flag.at,yes,no)
        def map_channel(register):
            end=b.name('mapped');b.set(mapped,f.size+6)
            for k in range(6):
                yes=b.name('channel');no=b.name('next_channel')
                eq_branch(register.at,g.size+k,a,yes,no)
                mark(yes);b.set(mapped,f.size+k);b.jump(end);mark(no)
            mark(end)
        def physical(register,out):
            b.set(out,self.base);b.copy(a,out.at,register.at)
        def read_fixed(address,width,dest):
            b.add(address.at,width,temp.at,A);b.dynamic(dest,dest+width,address,temp)
        def write_fixed(address,width,source):
            b.add(address.at,width,temp.at,A);b.dynamic(address,temp,source,source+width)
        def translate_memory(rounded=False):
            count=nround if rounded else n
            physical(dst,dl);physical(src,sl)
            b.set(dh,self.base);b.add(dst.at,Reg(count.at,a),dh.at,a)
            b.set(sh,self.base);b.add(src.at,Reg(count.at,a),sh.at,a)
        # One-time guest state. stdin prefix is a stream-transport artifact only.
        b.set(enabled,1);b.set(counter,0);b.set(remaining,self.ticks)
        if self.input_offset:
            # A seekable launch can inherit a nonzero logical stdin position.
            init_req=b.alloc(120+A)
            b.set(Reg(init_req.at,8),2);b.set(Reg(init_req.at+8,A),f.size+1)
            b.add(self.prefix.at,self.input_offset,init_req.at+56+A,64)
            b.emit([f.copy(120+A,f.size,init_req.at)])
        # Virtual stdin coordinates also protect SEEK_CUR/END from entering
        # the hidden bootstrap prefix. The regular launch stream is immutable.
        b.set(stdin_cursor,self.input_offset)
        b.set(Reg(host_req,8),3);b.set(Reg(host_req+8,A),f.size+1);b.set(Reg(host_req+8+A,112),0)
        b.emit([f.copy(120+A,f.size,host_req)])
        b.emit([f.copy(97+A,host_rsp.at,f.size)])
        b.compare(host_rsp.at+32,self.prefix,64,seekable)
        b.branch(seekable.at,'stdin_file_size','stdin_ready')
        mark('stdin_file_size');b.add(host_rsp.at+32,self.negative_prefix,stdin_size.at,64)
        mark('stdin_ready')
        mark('tick')
        b.move(pending,old);b.move(pending_enabled,enabled);b.set(active,0)
        b.copy(g.layer_bits,fetch.at,self.base) # The only guest instruction fetch.
        if self.translation=='parallel':
            # Prepare every ordinary descriptor from the frozen processor.
            # The channel/SYS path keeps the shared serial handler; no host
            # inspection of guest instructions or runtime values is involved.
            prepared=[];channel_flags=[];zero_flags=[];adds=[];initializations=[]
            for slot in range(g.slots):
                at=fetch.at+slot*I
                ends=[R(A) for _ in range(4)];prepared.append(ends)
                for dest,source in ((ends[0],at+z),(ends[2],at+z+a)):
                    initializations.append((dest,source))
                for dest,source in ((ends[1],at+z),(ends[3],at+z+a)):
                    adds.append((source,None,dest.at,a,None))
                zero=R(1);dc=R(1);sc=R(1);io=R(1)
                b.eq(at,0,z,zero);zero_flags.append(zero.at)
                b.compare(at+z,g.size,a,dc);b.compare(at+z+a,g.size,a,sc)
                b.gate([zero.at,dc.at,sc.at],io.at,1,lambda v:(1-v[0])&(v[1]|v[2]))
                channel_flags.append(io.at)
            any_channel=R(1);any_active=R(1)
            b.reduce_or(channel_flags,any_channel.at)
            nonzero=[]
            for zero in zero_flags:
                bit=R(1);b.gate([zero],bit.at,1,lambda v:1-v[0]);nonzero.append(bit.at)
            b.reduce_or(nonzero,any_active.at)
            b.branch(any_channel.at,'serial_slots','prepared_memory')
            mark('prepared_memory');b.move(active,any_active)
            for dest,source in initializations:b.set(dest,self.base);b.copy(a,dest.at,source)
            for ends in prepared:
                for dest in (ends[1],ends[3]):b.set(dest,self.base)
            # Extend the count's z bits without reading the following dst bit.
            counts=[]
            for slot in range(g.slots):
                count=R(a);b.set(count,0);b.copy(z,count.at,fetch.at+slot*I);counts.append(count)
            adds=[(left,counts[index//2],out,width,carry) for index,(left,_,out,width,carry) in enumerate(adds)]
            b.add_many(adds)
            targets=[]
            for start in range(0,g.slots,f.slots-1):
                group=prepared[start:start+f.slots-1];target=b.name('prepared');targets.append((target,len(group)))
                for slot,ends in enumerate(group):
                    for endpoint,value in enumerate(ends):
                        dest=Ref(target,(slot*4+endpoint)*A)
                        b.copy(A,dest,value.at)
            b.emit(fence=True)
            for target,count in targets:b.emit([NOP]*count,label=target,fence=True)
            b.jump('boundary')
            mark('serial_slots')
        b.set(cursor,fetch.at);b.set(left,g.slots)
        mark('slot')
        b.add(cursor.at,I,cursor_end.at,A)
        b.dynamic(current.at,current.at+I,cursor,cursor_end)
        b.move(cursor,cursor_end)
        b.set(n,0);b.copy(z,n.at,current.at)
        eq_branch(n.at,0,z,'next_slot','active_slot')
        mark('active_slot');b.set(active,1)
        b.set(dst,0);b.copy(a,dst.at,current.at+z)
        b.set(src,0);b.copy(a,src.at,current.at+z+a)
        b.compare(dst.at,g.size,a,flag);b.branch(flag.at,'write_channel','test_source')
        mark('test_source');b.compare(src.at,g.size,a,flag);b.branch(flag.at,'read_channel','memory')
        mark('memory');translate_memory();b.dynamic(dl,dh,sl,sh);b.jump('next_slot')
        # Channel direction has a separate buffer; data transfers are rounded to bytes.
        mark('write_channel');b.copy(a,channel.at,dst.at)
        eq_branch(channel.at,g.size,a,'sys_request','write_data')
        mark('write_data');map_channel(channel)
        b.add(n.at,7,nround.at,a);b.set(Reg(nround.at,3),0)
        physical(src,sl);b.set(sh,self.base);b.add(src.at,Reg(nround.at,a),sh.at,a)
        b.dynamic(mapped,mapped,sl,sh);b.jump('next_slot')
        mark('read_channel');b.copy(a,channel.at,src.at)
        eq_branch(channel.at,g.size,a,'sys_answer','read_data')
        mark('read_data');map_channel(channel)
        b.add(n.at,7,nround.at,a);b.set(Reg(nround.at,3),0)
        physical(dst,dl);b.set(dh,self.base);b.add(dst.at,Reg(nround.at,a),dh.at,a)
        b.dynamic(dl,dh,mapped,mapped)
        eq_branch(channel.at,g.size+1,a,'stdin_progress','next_slot')
        mark('stdin_progress')
        b.set(Reg(host_req,8),3);b.set(Reg(host_req+8,A),f.size+1);b.set(Reg(host_req+8+A,112),0)
        b.emit([f.copy(120+A,f.size,host_req)])
        b.emit([f.copy(97+A,host_rsp.at,f.size)])
        moved=R(64);b.set(moved,0);b.copy(A,moved.at,host_rsp.at+96)
        b.add(stdin_cursor.at,moved,stdin_cursor.at,64);b.jump('next_slot')

        mark('sys_answer');b.branch(enabled.at,'answer_enabled','next_slot')
        mark('answer_enabled');physical(dst,dl);write_fixed(dl,97+z,old.at);b.jump('next_slot')
        mark('sys_request');b.branch(enabled.at,'request_enabled','next_slot')
        mark('request_enabled');physical(src,sl);read_fixed(sl,120+a,guest_req.at)
        # Closing virtual SYS must not close the interpreter's private host SYS.
        eq_branch(qop.at,1,8,'test_close_sys','request_translate')
        mark('test_close_sys');eq_branch(qchan.at,g.size,a,'close_sys','request_translate')
        mark('close_sys');b.set(pending_enabled,0);b.jump('next_slot')
        mark('request_translate');map_channel(qchan)
        b.copy(8,host_req,guest_req.at);b.copy(A,host_req+8,mapped.at)
        b.copy(112,host_req+8+A,guest_req.at+8+a)
        eq_branch(qop.at,2,8,'seek','test_exec')
        mark('seek');eq_branch(qchan.at,g.size+1,a,'seek_stdin','send_request')
        mark('seek_stdin');b.branch(seekable.at,'seek_origin','send_request')
        mark('seek_origin');eq_branch(qarg.at,0,32,'seek_start','seek_cur_test')
        mark('seek_start');b.set(seek_base,0);b.jump('seek_compute')
        mark('seek_cur_test');eq_branch(qarg.at,1,32,'seek_current','seek_end_test')
        mark('seek_current');b.move(seek_base,stdin_cursor);b.jump('seek_compute')
        mark('seek_end_test');eq_branch(qarg.at,2,32,'seek_end','send_request')
        mark('seek_end');b.move(seek_base,stdin_size)
        mark('seek_compute');b.add(qoff.at,seek_base,seek_target.at,64)
        b.set(Reg(host_req+24+A,32),0) # Translate to absolute physical SEEK_SET.
        b.branch(seek_target.at+63,'seek_invalid','seek_valid')
        mark('seek_invalid');b.set(Reg(host_req+56+A,64),(1<<64)-1);b.jump('send_request')
        mark('seek_valid');b.add(seek_target.at,self.prefix,host_req+56+A,64);b.jump('send_request')
        mark('test_exec');eq_branch(qop.at,5,8,'exec','send_request')
        mark('exec');b.set(Reg(host_req+8,A),0) # EXEC has no target channel.
        # Invalid advertised EXEC lengths are forwarded without reading a command.
        b.compare(n.at,120+a,a,flag);b.branch(flag.at,'exec_room','send_request')
        mark('exec_room');b.add(n.at,-(120+a),temp.at,A)
        available=R(max(32,A));argument=R(max(32,A))
        b.set(available,0);b.copy(A-3,available.at,temp.at+3)
        b.set(argument,0);b.copy(32,argument.at,qarg.at)
        b.compare(available.at,argument,available.width,flag);b.branch(flag.at,'exec_copy','send_request')
        mark('exec_copy');b.set(temp2,0);b.copy(min(32,A-3),temp2.at+3,qarg.at)
        b.add(sl.at,120+a,dl.at,A);b.add(dl.at,temp2,dh.at,A)
        b.set(sh,host_req+120+A);b.add(sh.at,temp2,temp.at,A)
        b.dynamic(sh,temp,dl,dh)
        mark('send_request')
        # Advertised count adjustment preserves EXEC's short-record check.
        b.add(n.at,A-a,temp.at,A);b.add(temp.at,host_req,temp2.at,A)
        b.dynamic(f.size,f.size,host_req,temp2)
        b.emit([f.copy(97+A,host_rsp.at,f.size)])
        eq_branch(qop.at,3,8,'fstat','response')
        mark('fstat');eq_branch(qchan.at,g.size+1,a,'fstat_stdin','response')
        mark('fstat_stdin')
        # Pipes have size 0; a regular launch file includes the host boot prefix.
        b.compare(host_rsp.at+32,self.prefix,64,flag);b.branch(flag.at,'subtract_prefix','response')
        mark('subtract_prefix')
        b.add(host_rsp.at+32,self.negative_prefix,host_rsp.at+32,64)
        mark('response')
        eq_branch(qop.at,2,8,'seek_reply','copy_response')
        mark('seek_reply');eq_branch(qchan.at,g.size+1,a,'seek_reply_stdin','copy_response')
        mark('seek_reply_stdin');b.branch(seekable.at,'seek_reply_file','copy_response')
        mark('seek_reply_file');eq_branch(host_rsp.at+8,0,8,'seek_success','copy_response')
        mark('seek_success');b.move(stdin_cursor,seek_target)
        mark('copy_response');b.copy(96,pending.at,host_rsp.at)
        b.copy(z,pending.at+96,host_rsp.at+96)
        b.copy(1,pending.at+96+z,host_rsp.at+96+A)
        b.jump('next_slot')
        mark('next_slot');b.add(left.at,-1,left.at,left.width)
        eq_branch(left.at,0,left.width,'boundary','slot')
        mark('boundary');b.branch(active.at,'commit','stop')
        mark('commit');b.move(old,pending);b.move(enabled,pending_enabled)
        b.add(counter.at,1,counter.at,64)
        if self.ticks:
            b.add(remaining.at,-1,remaining.at,64)
            eq_branch(remaining.at,0,64,'stop','tick')
        else:b.jump('tick')
        mark('stop')
        if self.snapshot:b.emit([f.copy((g.size+7)//8*8,f.size+5,self.base)])
        if self.report:
            report=R(96)
            for k,value in enumerate(b'VM2R'):b.blocks.append((report.at+k*8,8,int(f'{value:08b}'[::-1],2)))
            b.copy(64,report.at+32,counter.at)
            b.emit([f.copy(96,f.size+4,report.at)])
        b.emit(label='halt',next=False)
        image,meta=b.assemble()
        meta['entry_bits']=b.labels[b.nodes[0][0]]
        # Initial guest state contains the original packed seed, not widened rows.
        put(image,self.base,z,g.layer_bits);put(image,self.base+z,a,0)
        put(image,self.base+z+a,a,g.size+1)
        meta.update(schema='vm2-on-vm1-v1',guest=dict(space_bits=g.size,slots=g.slots,address_bits=a,instruction_bits=I,processor_bits=g.layer_bits,base_bits=self.base),host=f.describe(),exec_base_bits=self.execbase,prefix_field_bits=self.prefix.at,counter_bits=counter.at,virtual_sys=dict(enabled_bits=enabled.at,response_bits=old.at,response_width=97+z),snapshot=self.snapshot,report=self.report,tick_limit=self.ticks,translation=self.translation,arithmetic=b.arithmetic)
        # Prefix length is part of stdin's virtual SEEK_SET/FSTAT translation.
        prefix=0
        for _ in range(4):
            put(image,self.prefix.at,64,prefix);put(image,self.negative_prefix.at,64,(-prefix)&((1<<64)-1));packet=boot_stream(image,f)
            if len(packet)==prefix:break
            prefix=len(packet)
        else:raise ValueError('bootstrap framing length did not converge')
        meta['bootstrap_bytes']=prefix
        meta['image_sha256']=hashlib.sha256(image).hexdigest()
        meta['boot_sha256']=hashlib.sha256(packet).hexdigest()
        return image,packet,meta

def compile_guest(size=65520,slots=64,**options):
    guest=Guest(size,slots)
    if options.get('host_bits') is not None:return Compiler(guest,**options).build()
    options.pop('host_bits',None)
    # Avoid repeatedly constructing a large parallel circuit merely to learn
    # that its arena is too small. This is only a starting estimate: the exact
    # layout checks below remain authoritative, including explicit host_bits.
    if options.get('arithmetic','hybrid')=='hybrid':estimate=1_500_000+slots*90_000*max(16,guest.a)//16
    else:estimate=3_000_000+slots*120_000*max(16,guest.a)//16
    start=max(24,guest.a+2,(estimate-1).bit_length()+2) if options.get('translation','parallel')=='parallel' else max(24,guest.a+2)
    for width in range(start,65):
        try:return Compiler(guest,host_bits=(1<<width)-16,**options).build()
        except LayoutCapacityError:
            if width==64:raise
    raise ValueError('interpreter exceeds emulator address width')
