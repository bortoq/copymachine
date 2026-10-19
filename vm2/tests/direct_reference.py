"""Independent symbolic-copy oracle. No compiler, native codec or runtime imports."""
import copy,errno,subprocess
from vm2_reference import get,put,bits_copy,payload,store_bytes

def run(source,manifest,mapping,stream=b'',*,regular=False,bound=(1,2,3,4,5),stdout_error=0,boot=b''):
    S=manifest['vm1']['size'];A=S.bit_length();memory=bytearray((S+7)//8)
    regions=mapping['regions'];fields=mapping['fields'];layers={l['name']:copy.deepcopy(l) for l in source['layers']}
    def width(n):
        if n=='address':return A
        if n=='count':return A-1
        if isinstance(n,dict):
            if n['type']=='SysWidth':return (120 if n['kind']=='req' else 97)+A
            if n['type']=='LayerBits':return manifest['vm1']['slots']*4*A
        return n
    def addr(ref,n=0):
        if ref['type']=='Memory':
            r=regions[ref['name']];off=ref.get('offset',0)
            if isinstance(off,str):off,available=r['fields'][off];assert n<=available
            assert 0<=off and off+n<=r['bits']
            return r['at']+off
        if ref['type']=='Field':
            r=fields[ref['layer']+':'+str(ref['slot'])][ref['name']];off=ref.get('offset',0)
            assert off+n<=r['bits'];return r['at']+off
        if ref['type']=='Channel':return S+['sys','stdin','stdout','debug','status','snapshot'].index(ref['name'])
        raise AssertionError(ref)
    def value(v):
        if isinstance(v,int):return v
        assert v['type']=='Value'
        if v['kind']=='data':return regions[v['name']]['at']+v.get('offset',0)
        if v['kind']=='entry':return mapping['layers'][v['name']]['at']+v.get('offset',0)
        if v['kind']=='channel':return S+['sys','stdin','stdout','debug','status','snapshot'].index(v['name'])+v.get('offset',0)
        if v['kind']=='stdin-origin':return len(boot)+v.get('offset',0)
        raise AssertionError(v)
    for r in source['data']:
        at=regions[r['name']]['at'];put(memory,at,regions[r['name']]['bits'],int(r['value'],0))
        if r.get('record') is not None:
            offset=0
            for _,count,v in r['record']:
                count=width(count);put(memory,at+offset,count,value(v));offset+=count
        for off,count,v in r['relocations']:put(memory,at+off,width(count),value(v))
    for key,items in fields.items():
        name,slot=key.rsplit(':',1);op=layers[name]['copies'][int(slot)]
        for attr,r in items.items():put(memory,r['at'],r['bits'],width(op['n']) if attr=='n' else addr(op[attr]))
    channels={k:dict(used=k in bound,cursor=len(boot) if k==1 else 0,data=bytearray(boot+stream if k==1 else b''),status=0,moved=0,eof=0) for k in range(1,6)}
    response=bytearray((97+A+7)//8);enabled=True;states=[];current=source['entry'];ticks=0
    def encode_rsp(op=0,status=0,flags=0,size=0,moved=0,eof=0):
        result=bytearray(len(response));at=0
        for item,count in ((op,8),(status,8),(flags,16),(size,64),(moved,A),(eof,1)):
            put(result,at,count,item);at+=count
        return result
    while current is not None:
        layer=copy.deepcopy(layers[current]);before=bytes(memory);old=bytes(response);old_enabled=enabled;copies=[];replacements=[]
        spans=[];devices=set();request=None
        for slot,op in enumerate(layer['copies']):
            if op['type']=='Replace':replacements.append(op);continue
            key=current+':'+str(slot)
            if key in fields:
                n,d,s=(get(before,fields[key][attr]['at'],fields[key][attr]['bits']) for attr in ('n','dst','src'))
            else:n=width(op['n']);d=addr(op['dst']);s=addr(op['src'])
            copies.append((n,d,s))
            if not n:continue
            assert not(d>=S and s>=S)
            count=n
            if max(d,s)>=S:
                device=max(d,s)
                if device==S:
                    count=max(n,120+A) if d==S else 97+A
                    if d==S:assert request is None;request=s
                else:
                    assert device not in devices;devices.add(device);count=(n+7)//8*8
            for at in (d,s):
                if at<S:assert 0<=at<at+count<=S;spans.append((at,at+count))
        assert all(not(x<q and p<y) for i,(x,y) in enumerate(spans) for p,q in spans[i+1:]),current
        following=layer['next']
        if isinstance(following,dict):
            pointer=get(before,addr(following,A),A)
            following=next((name for name,l in mapping['layers'].items() if l['at']==pointer),None)
            assert following is not None,'invalid dynamic target'
        if request is not None and old_enabled:
            op=get(before,request,8);target=get(before,request+8,A);arg=get(before,request+24+A,32);off=get(before,request+56+A,64)
            if op in (1,2,3):assert target not in devices
            channel=channels.get(target-S);reply=dict(op=op)
            if op==0:pass
            elif op==1:
                if target==S:enabled=False
                elif channel is None or not channel['used']:reply['status']=errno.EBADF
                else:channel['used']=False
            elif op==2:
                if channel is None or not channel['used']:reply['status']=errno.EBADF
                elif target in (S+2,S+3) or target==S+1 and not regular:reply['status']=errno.ESPIPE
                else:
                    signed=off-(1<<64) if off>>63 else off
                    origin=arg-(1<<32) if arg>>31 else arg
                    start=0 if origin==0 else channel['cursor'] if origin==1 else len(channel['data']) if origin==2 else None
                    if start is None or start+signed<0:reply['status']=errno.EINVAL
                    else:channel['cursor']=start+signed
            elif op==3:
                if channel is None or not channel['used']:reply['status']=errno.EBADF
                else:reply.update(status=channel['status'],size=len(channel['data']) if target==S+1 and regular or target>=S+4 else 0,moved=channel['moved'],eof=channel['eof'])
            elif op==4:reply['status']=errno.ENOTTY
            elif op==5:
                n=next(n for n,d,s in copies if d==S)
                if n<120+A+arg*8:reply['status']=errno.EINVAL
                else:
                    command=payload(before,request+120+A,arg).decode();r=subprocess.run(command,shell=True,capture_output=True,check=False)
                    reply.update(status=r.returncode if r.returncode>=0 else 128-r.returncode,size=r.returncode<<8 if r.returncode>=0 else -r.returncode)
                    for k,data in ((2,r.stdout),(3,r.stderr)):channels[k]['data'].extend(data);channels[k]['cursor']+=len(data)
            else:reply['status']=errno.EINVAL
            response=encode_rsp(**reply)
        for n,d,s in copies:
            if not n:continue
            if s==S:
                if old_enabled:bits_copy(memory,d,old,0,97+A)
            elif max(d,s)>S:
                c=channels.get(max(d,s)-S)
                if c is None or not c['used']:continue
                count=(n+7)//8
                if s>S:
                    assert s==S+1
                    chunk=c['data'][c['cursor']:c['cursor']+count];c['cursor']+=len(chunk)
                    c.update(status=0,moved=len(chunk),eof=int(len(chunk)<count));store_bytes(memory,d,chunk)
                else:
                    if d==S+2 and stdout_error:c.update(status=stdout_error,moved=0);continue
                    chunk=payload(before,s,count);end=c['cursor']+count
                    if end>len(c['data']):c['data'].extend(bytes(end-len(c['data'])))
                    c['data'][c['cursor']:end]=chunk;c['cursor']=end;c.update(status=0,moved=count)
            elif d<S:bits_copy(memory,d,before,s,n)
        for op in replacements:
            layers[op['dst']]=copy.deepcopy(layers[op['src']]);layers[op['dst']]['name']=op['dst']
            for slot in range(len(layers[op['dst']]['copies'])):
                left=fields.get(op['dst']+':'+str(slot));right=fields.get(op['src']+':'+str(slot))
                if left:
                    for attr in left:bits_copy(memory,left[attr]['at'],before,right[attr]['at'],left[attr]['bits'])
        ticks+=1;states.append(bytes(memory));current=following
        if source['limit'] and ticks>=source['limit']:break
        if ticks>1000:raise AssertionError('reference step bound')
    return dict(memory=bytes(memory),channels=channels,ticks=ticks,states=states,response=bytes(response),enabled=enabled)
