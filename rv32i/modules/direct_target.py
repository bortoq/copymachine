"""Universal RV32I generator lowered through the public vm2 symbolic ABI."""
import dependencies
import json
from pathlib import Path
from rv32i import Image,Copy,Field,Layout,REGS,PC,STATUS,EXIT_CODE,SCRATCH,DISCARD,RESULT,COND,REDUCE,CARRY,EA,IMM
from vm2compile import Copy as LogicalCopy,Channel,Memory,Value
from vm2compile.legacy import adapt
from vm2compile.sdk import sys_record,request,response
from vm2compile.artifact import build

IO_COUNT=SCRATCH+96*32
IO_ERROR=IO_COUNT+32
MON_REMAIN=SCRATCH+128*32
MON_COMMITS=MON_REMAIN+32
MON_INPUT=MON_COMMITS+32
MON_OUTPUT=MON_INPUT+32

class DirectImage(Image):
    def __init__(self,*,memory_bytes=65536,io=True,checkpoint_every=0):
        super().__init__(io=io,memory_bytes=memory_bytes,layout=Layout(8*1024*1024))
        if not isinstance(checkpoint_every,int) or not 0<=checkpoint_every<1<<32:raise ValueError('checkpoint interval must be uint32')
        self.checkpoint_every=checkpoint_every
        self.table_strides={};self.address_entries=[]

    def table(self,values,stride=5):
        values=list(values)
        actual=max(stride,1) if stride!=1 else 2
        base=super().table(values,actual);self.table_strides[base]=actual
        # This owner-defined table contains physical register addresses. Its
        # values must be relocated; guest integers in other LUTs remain data.
        if values==[DISCARD]+[REGS+32*i for i in range(1,32)]:
            self.address_entries.extend(base+(i<<actual) for i in range(len(values)))
        return base

    def lookup(self,dst,base,indices,width,stride=0):
        return super().lookup(dst,base,indices,width,self.table_strides.get(base,stride))

    def build_io(self):
        a0,a1,a2,a7=(REGS+32*i for i in (10,11,12,17))
        self.start('io_dispatch')
        self.require_zero(list(range(a7+7,a7+32)),'io_enosys')
        self.dispatch(list(range(a7,a7+7)),{63:'io_read',64:'io_write',93:'io_exit'},default='io_enosys')
        for name,descriptor,channel in [('read',0,'stdin'),('write',1,'stdout')]:
            self.start('io_'+name);self.require_value(a0,descriptor,'io_ebadf')
            self.reduce_or(COND,list(range(a2,a2+32)));self.branch(COND,'io_zero','io_'+name+'_range')
            self.start('io_'+name+'_range')
            self.require_zero(list(range(a1+self.memory_bits,a1+32)),'io_efault')
            self.add(EA,a1,a2);self.gate('not',COND,[CARRY]);self.guard(COND,'io_efault')
            self.add(IMM,EA,self.constant(self.memory_bytes+1),subtract=True)
            self.gate('not',COND,[CARRY]);self.guard(COND,'io_efault')
            transfer=Copy(0,self.layout.memory_bit,Channel(channel)) if name=='read' else Copy(0,Channel(channel),self.layout.memory_bit)
            self.emit(self.memory_bits+1,Field(transfer,'n',3),a2)
            self.emit(self.memory_bits,Field(transfer,'dst' if name=='read' else 'src',3),a1)
            self.jump('io_'+name+'_transfer');self.start('io_'+name+'_transfer')
            self.blocks[self.current][0].append(transfer);self.jump('io_'+name+'_status')
            self.start('io_'+name+'_status');self.emit(32,IO_COUNT,self.constant(0));self.emit(8,IO_ERROR,self.constant(0));self.jump('io_'+name+'_answer')
            self.start('io_'+name+'_answer');self.jump('io_'+name+'_collect')
            self.start('io_'+name+'_collect');self.jump('io_'+name+'_result')
            self.start('io_'+name+'_result')
            # A partial successful transfer wins over a later channel error.
            self.reduce_or(REDUCE,list(range(IO_COUNT,IO_COUNT+32)))
            self.branch(REDUCE,'io_'+name+'_error','io_'+name+'_moved')
            self.start('io_'+name+'_error');self.reduce_or(REDUCE,list(range(IO_ERROR,IO_ERROR+8)))
            self.branch(REDUCE,'io_'+name+'_moved','io_eio')
            self.start('io_'+name+'_moved')
            if self.checkpoint_every:self.add(MON_INPUT if name=='read' else MON_OUTPUT,MON_INPUT if name=='read' else MON_OUTPUT,IO_COUNT)
            self.emit(32,RESULT,IO_COUNT);self.jump('io_return')
        self.start('io_zero');self.emit(32,RESULT,self.constant(0));self.jump('io_return')
        for name,value in [('enosys',-38),('ebadf',-9),('efault',-14),('eio',-5)]:
            self.start('io_'+name);self.emit(32,RESULT,self.constant(value&0xffffffff));self.jump('io_return')
        self.start('io_return');self.emit(32,a0,RESULT);self.jump('commit')
        self.start('io_exit');self.emit(32,EXIT_CODE,a0);self.emit(32,STATUS,self.constant(10));self.jump('halt')

    def symbolic(self,program=b'',*,entry=0,registers=None,frames=False,initial_memory=None,packing=True):
        if len(program)>self.memory_bytes or not 0<=entry<1<<32:raise ValueError('guest program/entry out of range')
        registers={2:self.memory_bytes-16} if registers is None else registers
        if any(not 0<=r<32 or not 0<=v<1<<32 for r,v in registers.items()):raise ValueError('invalid register')
        self.build()
        if self.checkpoint_every:
            self.data.append((MON_REMAIN,32,self.checkpoint_every))
            self.blocks['checkpoint'][1].src='monitor_commit'
            self.start('monitor_commit')
            self.add(MON_COMMITS,MON_COMMITS,self.constant(1))
            self.add(MON_REMAIN,MON_REMAIN,self.constant(1),subtract=True)
            self.reduce_or(COND,list(range(MON_REMAIN,MON_REMAIN+32)))
            self.branch(COND,'monitor_report','fetch')
            self.start('monitor_report');self.emit(32,MON_REMAIN,self.constant(self.checkpoint_every));self.jump('fetch')
        for ops,term in self.blocks.values():
            if term.src==0x10000:term.src=0
            for op in ops:
                if op.dst==0:op.dst=DISCARD
        ranges=[('registers',REGS,SCRATCH-REGS,4096),('scratch',SCRATCH,0x24000-SCRATCH,4096),
                ('constants',0x24000,0x30000-0x24000,8),('tables',0x30000,0x40000-0x30000,65536),
                ('guest',self.layout.memory_bit,self.memory_bytes*8,self.memory_bytes*8)]
        regions=[]
        for name,start,bits,align in ranges:
            value=0;relocations=[]
            for at,width,item in self.data:
                if start<=at<start+bits:
                    if isinstance(item,str):relocations.append((at-start,width,item))
                    else:value|=item<<(at-start)
            if name=='registers':
                for r,v in registers.items():
                    if r:value|=v<<(r*32)
                value|=entry<<(PC-start)
            if name=='guest':
                raw=bytearray(self.memory_bytes)
                for at,data in (initial_memory or {}).items():
                    if at<0 or at+len(data)>len(raw):raise ValueError('initial guest memory out of range')
                    raw[at:at+len(data)]=data
                raw[:len(program)]=program
                value=int.from_bytes(bytes(int(f'{b:08b}'[::-1],2) for b in raw),'little')
            regions.append(dict(name=name,at=start,bits=bits,value=value,align=align,relocations=relocations))
        p=adapt(self.blocks,regions,address_bits=self.layout.address_bits,count_bits=self.layout.n_bits,
                entry='fetch',minimum_size=(1<<(27 if self.io else 26))-16,
                address_literals=[('tables',at-0x30000) for at in self.address_entries],packing=packing)
        if self.io:
            for name,device in [('read','stdin'),('write','stdout')]:
                req=sys_record(p,'io-'+name+'-request',op='FSTAT',chan=Channel(device))
                rsp=sys_record(p,'io-'+name+'-reply',kind='rsp')
                p.layers['legacy:io_'+name+'_status:end'].copies.append(request(req))
                p.layers['legacy:io_'+name+'_answer:end'].copies.append(response(rsp))
                p.layers['legacy:io_'+name+'_collect:end'].copies.extend([
                    LogicalCopy('address',Memory('scratch',IO_COUNT-SCRATCH),Memory(rsp.name,'moved')),
                    LogicalCopy(8,Memory('scratch',IO_ERROR-SCRATCH),Memory(rsp.name,'status'))])
        if frames:
            for name in ('checkpoint','halt'):
                p.layers['legacy:'+name+':end'].copies.append(LogicalCopy(1088,Channel('debug'),Memory('registers')))
        p.layers['legacy:halt:end'].checkpoint=True
        if self.checkpoint_every:
            monitor=p.layers['legacy:monitor_report:end'];monitor.checkpoint=True;monitor.checkpoint_stop=True
        return p

def compile_image(program=b'',**options):
    generator=DirectImage(memory_bytes=options.pop('memory_bytes',65536),io=options.pop('io',True),checkpoint_every=options.pop('checkpoint_every',0))
    symbolic=generator.symbolic(program,**options)
    payload,manifest=build(symbolic)
    manifest['rv32i']=dict(schema='rv32i-direct-v1',memory_bytes=generator.memory_bytes,
        registers_region='registers',guest_region='guest',pc_offset=PC-REGS,status_offset=STATUS-REGS,
        exit_offset=EXIT_CODE-REGS,io=generator.io,source_layers=len(symbolic.layers),byte_order='little',
        packing=options.get('packing',True),checkpoint_every=generator.checkpoint_every,monitor_region='scratch',monitor_word_bits=32,
        monitor_offsets=dict(committed=MON_COMMITS-SCRATCH,input_bytes=MON_INPUT-SCRATCH,output_bytes=MON_OUTPUT-SCRATCH))
    return payload,manifest
