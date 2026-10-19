"""Prepare an index of saved dictionary bytes; never parse user Forth."""
import hashlib,json,re
from pathlib import Path
from common import UPSTREAM,PORT

BUCKETS=4096

def name_hash(name):
    value=0
    for byte in name:
        if 65<=byte<=90:byte+=32
        value=((value<<5)+value)^byte
        value&=0xffffffff
    return value&(BUCKETS-1)

def prepare_index(folder,header=None):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);header=Path(header or PORT/'pfdicdat.h')
    text=header.read_text();m=json.loads(header.with_name(header.name+'.json').read_text())
    if hashlib.sha256(header.read_bytes()).hexdigest()!=m['header_sha256']:raise ValueError('dictionary checksum mismatch')
    body=re.search(r'MinDicNames\[.*?= \{(.*?)\};',text,re.S)[1]
    names=bytes(int(v,16) for v in re.findall(r'0x([0-9a-f]{2})',body))
    if len(names)!=m['names_bytes']:raise ValueError('dictionary name length mismatch')
    entries=[];at=m['relative_context'];seen=set()
    while at:
        if at in seen or at%4 or not 8<=at<len(names):raise ValueError('invalid prepared name chain')
        seen.add(at);size=names[at]&31
        if at+1+size>len(names):raise ValueError('invalid prepared name')
        entries.append((at,names[at+1:at+1+size]))
        previous=int.from_bytes(names[at-8:at-4],'little')
        if previous>=at:raise ValueError('nonmonotonic prepared chain')
        at=previous
    capacity=(m['names_bytes']+m['headers_reserve_bytes']+3)//4
    if capacity>=65535:raise ValueError('dictionary index exceeds 16-bit rank capacity')
    heads=[0]*BUCKETS;links=[0]*capacity;ranks=[0]*capacity
    for at,name in reversed(entries):
        ranks[at//4]=at//4
        bucket=name_hash(name);links[at//4]=heads[bucket];heads[bucket]=at
    output=['/* Generated from verified prepared names, not from user Forth. */',
            '#define PF_INDEX_BUCKETS '+str(BUCKETS),
            '#define PF_INDEX_CAPACITY '+str(capacity),
            '#define PF_INDEX_INITIAL_CONTEXT '+str(m['relative_context']),
            '#define PF_INDEX_INITIAL_LIMIT '+str(m['names_bytes'])]
    for name,values in [('pf_index_heads',heads),('pf_index_next',links),('pf_index_rank',ranks)]:
        output.append('static '+('uint16_t ' if name=='pf_index_rank' else 'uint32_t ')+name+'['+str(len(values))+'] = {')
        output.extend('    '+','.join(map(str,values[i:i+16]))+',' for i in range(0,len(values),16));output.append('};')
    (folder/'name_index.h').write_text('\n'.join(output)+'\n')
    source=(UPSTREAM/'csrc/pfcompil.c').read_text()
    for before,after in [('cell_t ffFindNFA(', 'cell_t pfLinearFindNFA('),('void CreateDicEntry(', 'void pfLinearCreateDicEntry(')]:
        if source.count(before)!=1:raise ValueError('upstream definition changed: '+before)
        source=source.replace(before,after)
    (folder/'compiler.c').write_text(source)
    report=dict(schema='pforth-name-index-v1',entries=len(entries),buckets=BUCKETS,capacity=capacity,
                dictionary_sha256=m['header_sha256'],maximum_bucket=max(sum(name_hash(n)==b for _,n in entries) for b in set(map(lambda e:name_hash(e[1]),entries))))
    (folder/'index.json').write_text(json.dumps(report,indent=2)+'\n');return folder/'compiler.c',report
