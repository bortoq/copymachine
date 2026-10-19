"""Independent bitwise vm2 oracle. No generator, emulator or codec imports."""
import errno,subprocess

def get(data,at,width):
    return sum(((data[(at+j)//8]>>(7-(at+j)%8))&1)<<j for j in range(width))
def put(data,at,width,value):
    for j in range(width):
        mask=128>>((at+j)%8)
        data[(at+j)//8]=(data[(at+j)//8]&~mask)|(mask if value>>j&1 else 0)
def bits_copy(memory,dst,before,src,width):
    for j in range(width):put(memory,dst+j,1,get(before,src+j,1))
def payload(data,at,nbytes):
    return bytes(sum(get(data,at+i*8+j,1)<<(7-j) for j in range(8)) for i in range(nbytes))
def store_bytes(data,at,values):
    for i,value in enumerate(values):
        for j in range(8):put(data,at+i*8+j,1,(value>>(7-j))&1)

def run(stream,size=65520,slots=8,limit=0,*,regular=False,bound=(1,2,3,4,5),stdout_error=0):
    a=size.bit_length();z=a-1;I=3*a-1;L=I*slots
    memory=bytearray((size+7)//8);put(memory,0,z,L);put(memory,z+a,a,size+1)
    # Channels use logical stream coordinates, never the emulator bootstrap prefix.
    channels={k:dict(used=k in bound,cursor=0,data=bytearray(stream if k==1 else b''),status=0,moved=0,eof=0) for k in range(1,6)}
    response=bytearray((97+z+7)//8);enabled=True;ticks=0;states=[]
    def encode_rsp(op=0,status=0,flags=0,size=0,moved=0,eof=0):
        result=bytearray(len(response));offset=0
        for value,width in [(op,8),(status,8),(flags,16),(size,64),(moved,z),(eof,1)]:
            put(result,offset,width,value);offset+=width
        return result
    while not limit or ticks<limit:
        rows=[(get(memory,i*I,z),get(memory,i*I+z,a),get(memory,i*I+z+a,a)) for i in range(slots)]
        if not any(n for n,_,_ in rows):break
        # Full independent operand-set audit, including rounded IO and SYS widths.
        spans=[];devices=set();request=None
        for n,d,s in rows:
            if not n:continue
            channel=max(d,s)>=size
            if channel:
                assert min(d,s)<size,'channel/channel'
                pos=max(d,s)
                if pos>size:
                    assert pos not in devices,'duplicate device operation';devices.add(pos)
                elif d==size:assert request is None;request=s
            for p in (d,s):
                if p>=size:continue
                width=n
                if channel:
                    width=max(n,120+a) if d==size else 97+z if s==size else (n+7)//8*8
                assert 0<=p<p+width<=size,(n,d,s,width)
                spans.append((p,p+width))
        assert all(not(x<q and p<y) for i,(x,y) in enumerate(spans) for p,q in spans[i+1:]),rows
        if request is not None:
            op=get(memory,request,8);target=get(memory,request+8,a)
            if op in (1,2,3):assert target not in devices
        before=bytes(memory);old_response=bytes(response)
        # SYS answer is old for every slot, independent of slot ordering.
        if enabled:
            for n,d,s in rows:
                if n and s==size:bits_copy(memory,d,old_response,0,97+z)
        for n,d,s in rows:
            if not n or d!=size or not enabled:continue
            op=get(before,s,8);target=get(before,s+8,a);arg=get(before,s+24+a,32);off=get(before,s+56+a,64)
            c=channels.get(target-size);reply=dict(op=op)
            if op==0:pass
            elif op==1:
                if target==size:enabled=False
                elif c is None or not c['used']:reply['status']=errno.EBADF
                else:c['used']=False
            elif op==2:
                if c is None or not c['used']:reply['status']=errno.EBADF
                elif target in (size+2,size+3) or (target==size+1 and not regular):reply['status']=errno.ESPIPE
                else:
                    signed=off-(1<<64) if off>>63 else off
                    origin=arg-(1<<32) if arg>>31 else arg
                    start=0 if origin==0 else c['cursor'] if origin==1 else len(c['data']) if origin==2 else None
                    if start is None or start+signed<0:reply['status']=errno.EINVAL
                    else:c['cursor']=start+signed
            elif op==3:
                if c is None or not c['used']:reply['status']=errno.EBADF
                else:
                    byte_size=len(c['data']) if (target==size+1 and regular or target>=size+4) else 0
                    reply.update(status=c['status'],size=byte_size,moved=c['moved'],eof=c['eof'])
            elif op==4:reply['status']=errno.ENOTTY
            elif op==5:
                if n<120+a+arg*8:reply['status']=errno.EINVAL
                else:
                    command=payload(before,s+120+a,arg).decode()
                    result=subprocess.run(command,shell=True,capture_output=True,check=False)
                    code=result.returncode if result.returncode>=0 else 128-result.returncode
                    reply.update(status=code,size=result.returncode<<8 if result.returncode>=0 else -result.returncode)
                    channels[2]['data'].extend(result.stdout);channels[3]['data'].extend(result.stderr)
                    channels[2]['cursor']+=len(result.stdout);channels[3]['cursor']+=len(result.stderr)
            else:reply['status']=errno.EINVAL
            response=encode_rsp(**reply)
        for n,d,s in rows:
            if not n:continue
            if d<size and s<size:bits_copy(memory,d,before,s,n)
            elif max(d,s)>size:
                c=channels.get(max(d,s)-size)
                if c is None or not c['used']:continue
                count=(n+7)//8
                if s>=size:
                    assert s==size+1
                    chunk=c['data'][c['cursor']:c['cursor']+count];c['cursor']+=len(chunk)
                    c.update(status=0,moved=len(chunk),eof=int(len(chunk)<count))
                    store_bytes(memory,d,chunk)
                else:
                    if d==size+2 and stdout_error:c.update(status=stdout_error,moved=0);continue
                    chunk=payload(before,s,count);end=c['cursor']+count
                    if end>len(c['data']):c['data'].extend(bytes(end-len(c['data'])))
                    c['data'][c['cursor']:end]=chunk;c['cursor']=end;c.update(status=0,moved=count)
        ticks+=1;states.append(bytes(memory))
        if ticks>1000:raise AssertionError('reference exceeded test tick bound')
    return dict(memory=bytes(memory),ticks=ticks,channels=channels,response=bytes(response),enabled=enabled,states=states)
