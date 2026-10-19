"""PCS2 copycode wrappers for dynamic layered programs and streaming audit.

Original instruction homes remain writable. Wrappers capture them AFTER
prior application copies commit, then execute that captured layer once.
"""
import argparse
import gzip
import json
from pathlib import Path
import struct

from .boundary import Format, protocol, record
from .terminal import numeric
from .schedule import validate

FRAME = struct.Struct('<4sBBI')
META = struct.Struct('<QIBBHH')
PREFIX = FRAME.size+META.size+32+8
END_SIZE = FRAME.size+2+32+8+4
WIDTH = 8
LAYER_TICKS = 20
REVERSE = bytes(int(f'{i:08b}'[::-1],2) for i in range(256))


def field(data, at, width):
    start,shift=divmod(at,8)
    return (int.from_bytes(data[start:(at+width+7)//8].translate(REVERSE),'little')>>shift)&((1<<width)-1)


def instruction(data, at, f):
    word=field(data,at,f.isz)
    mask=(1<<f.a)-1
    return word&((1<<f.z)-1),(word>>f.z)&mask,(word>>(f.z+f.a))&mask


def put_field(data, at, width, value):
    if not 0 <= value < 1 << width:
        raise ValueError('trace relocation overflow')
    for k in range(width):
        mask = 1 << (7-(at+k)%8)
        data[(at+k)//8] = (data[(at+k)//8] & ~mask) | (((value >> k) & 1) << (7-(at+k)%8))


def instrument(image, manifest, layers, label_relocations, *, mode, initial_label):
    """Instrument generated layers; retain their original operand/patch homes.

    layers = [(home, phase)] (0 application, 1 monitor, 2 control).
    Label relocations describe generator-owned address constants only.
    """
    if mode not in ('full', 'channels'):
        raise ValueError('trace must be full or channels')
    f = Format(manifest['boundary']['space_bits'], manifest['processor_n'])
    if f.slots < WIDTH or f.layer_bits % 8:
        raise ValueError('PCS2 needs a byte-aligned processor with at least 8 slots')
    ops, req, rsp = protocol(f.space_bits)
    mon = manifest['monitor']
    size, row_bytes = WIDTH*f.isz, (f.isz+7)//8
    full = mode == 'full'
    body_size = f.layer_bytes if full else 2*row_bytes
    req_bytes, rsp_bytes = (req[1]+7)//8, (rsp[1]+7)//8
    started = len(image)*8

    def alloc(data):
        at = len(image)*8
        image.extend(data)
        if len(image)*8 > f.space_bits:
            raise ValueError('trace code exceeds space; choose a larger layout')
        return at
    def full_layer(rows=(), following=None):
        rows = list(rows)
        if following is not None:
            rows += [(0,0,0)]*(f.slots-1-len(rows)) + [(f.layer_bits,0,following)]
        return alloc(f.layer(rows))
    def small(rows):
        if len(rows) > WIDTH:
            raise ValueError('trace gateway exceeds reserved width')
        return alloc(f.layer(rows)[:size//8])
    def patch_layer(at, rows, following=None):
        rows = list(rows)
        if following is not None:
            rows += [(0,0,0)]*(f.slots-1-len(rows)) + [(f.layer_bits,0,following)]
        image[at//8:at//8+f.layer_bytes] = f.layer(rows)

    shadow = alloc(bytes(f.layer_bytes))
    returning = alloc(bytes(f.layer_bytes))  # executable control in slot 0
    original_link = alloc(bytes(row_bytes))
    candidates = alloc(bytes(2*row_bytes))
    meta = alloc(bytes(PREFIX+req_bytes))
    answer = alloc(bytes(rsp_bytes))
    zeros = alloc(bytes(row_bytes))
    nvalue = alloc(numeric(size,64))
    poll_req = alloc(numeric(req[1],64));poll_rsp = alloc(numeric(rsp[1],64));poll_off=alloc(bytes(8))
    phase_boot, phase_compute = alloc(b'PHT1B'), alloc(b'PHT1C')
    # All common stages are full processor layers. Only gateway loads are short.
    common = [full_layer() for _ in range(11)]
    pre1,pre1b,pre2,pre3,post1,post_answer,post2,post3,post4,post5,post6 = common
    next_link = alloc(f.layer([(f.layer_bits,0,post1)])[:row_bytes])
    debug = f.devices['debug']
    patch_layer(pre1, [(f.isz,returning,shadow+(f.slots-1)*f.isz)],pre1b)
    patch_layer(pre1b, [(f.isz,original_link,shadow+(f.slots-1)*f.isz)],pre2)
    patch_layer(pre2, [(f.isz,shadow+(f.slots-1)*f.isz,next_link),
                      (f.z,returning,nvalue)],pre3)
    patch_layer(pre3, [(f.layer_bits,0,shadow)])
    patch_layer(post1, [(req[1],f.space_bits,meta+PREFIX*8)],post_answer)
    patch_layer(post_answer, [(rsp[1],answer,f.space_bits)],post2)
    patch_layer(post2, [(PREFIX*8,debug,meta)],post3)
    patch_layer(post3, [(body_size*8,debug,shadow if full else candidates)],post4)
    patch_layer(post4, [(row_bytes*8,debug,original_link)],post5)
    patch_layer(post5, [(rsp_bytes*8,debug,answer)],post6)
    patch_layer(post6, [(f.layer_bits,0,returning)])

    gateways, terminal_costs = {}, {}
    for name,kind,reason in [('checkpoint',2,1),('final',1,0)]:
        terminal = mon[name+'_entry']
        prefix = FRAME.pack(b'PCS2',2,int(not full),END_SIZE-FRAME.size)
        end = alloc(prefix+bytes([kind,reason])+bytes.fromhex(f.description['layout_id'])+bytes(12))
        stage3 = small([(END_SIZE*8,debug,end),(f.layer_bits,0,terminal)])
        stage2 = small([(40,debug,phase_compute),(size,0,stage3)])
        stage1 = small([(64,end+(FRAME.size+2+32)*8,mon['counters_bit']['committed']),
                        (32,end+(FRAME.size+2+32+8)*8,manifest['status_bit']),
                        (size,0,stage2)])
        gateways[terminal] = stage1
        terminal_costs[name] = mon[name+'_report_ticks']
    wrappers = {home: small([]) for home,_ in layers}
    targets = dict(wrappers)
    targets.update(gateways)
    old_labels = dict(manifest['labels'])
    for at,width,target in label_relocations:
        if target not in targets:
            raise ValueError('unknown generator label target')
        put_field(image,at,width,targets[target])
    # Reject invalid producer schedules before rewriting anything executable.
    for home,_ in layers:
        validate([instruction(image,home+i*f.isz,f) for i in range(f.slots)],f.space_bits)
    # Direct and patched control transfers now name compact gateways.
    for home,_ in layers:
        at = home+(f.slots-1)*f.isz
        n,dst,src = instruction(image,at,f)
        if n and dst == 0 and src in targets:
            put_field(image,at+f.z+f.a,f.a,targets[src])
    phase_names, metadata = {0:'application',1:'monitor',2:'control'}, {}
    for home,phase in layers:
        selected, ordinary, data_devices = [], 0, []
        for slot in range(f.slots-1):
            n,dst,src = instruction(image,home+slot*f.isz,f)
            if max(dst,src) >= f.space_bits:
                selected.append(slot)
                device = dst if dst > f.space_bits else src if src > f.space_bits else None
                if device is not None:
                    data_devices.append(device)
            elif n:
                ordinary += 1
        if len(selected)>2 or len(data_devices)>1:
            raise ValueError('PCS2 supports two SYS rows or one device row per layer')
        payload = META.size+32+8+body_size+row_bytes+rsp_bytes
        slots = selected+[65535]*(2-len(selected))
        template = FRAME.pack(b'PCS2',1,int(not full),payload)
        template += META.pack(home,ordinary,phase,len(selected),*slots)
        template += bytes.fromhex(f.description['layout_id'])+bytes(8)
        template += record(req, {'op':ops['FSTAT'], 'chan':data_devices[0]}) if data_devices else record(req, {})
        source = alloc(template)
        rows = [(f.layer_bits,shadow,home),((PREFIX+req_bytes)*8,meta,source),
                (64,meta+(PREFIX-8)*8,mon['counters_bit']['committed'])]
        for index in range(2):
            rows.append((f.isz if index<len(selected) else row_bytes*8,
                         candidates+index*row_bytes*8,
                         home+selected[index]*f.isz if index<len(selected) else zeros))
        # Preserve an application's pending SYS response between its request
        # and answer layers. Only data layers need a tracer FSTAT.
        rows.extend([(f.z,post1,poll_req if data_devices else poll_off),
                     (f.z,post_answer,poll_rsp if data_devices else poll_off)])
        # Each service copy gets a separate compact gateway. This preserves
        # template-before-counter updates and prevents source fan-out from
        # the captured home/zero constants. Seven gateways for every layer.
        at = wrappers[home]
        stages = [at]+[small([]) for _ in range(6)]
        for current, following, work in zip(stages,stages[1:]+[pre1],rows):
            encoded = f.layer([work,(f.layer_bits if following==pre1 else size,0,following)])[:size//8]
            image[current//8:current//8+size//8] = encoded
        metadata[str(home)] = dict(phase=phase_names[phase],ordinary=ordinary,
                                  slots=selected,wrapper=at)
    continuation = [(32,mon['remaining_bit'],mon['reload_bit']),
                    (size,0,wrappers[old_labels['fetch']]),(40,debug,phase_boot)]
    at = mon['checkpoint_snapshot_entry']
    image[at//8:at//8+f.layer_bytes] = f.layer(continuation)
    mon['continuation_hex'] = f.layer(continuation).hex()
    initial = f.layer([(40,debug,phase_boot),(size,0,wrappers[old_labels[initial_label]])])
    image[:f.layer_bytes] = initial
    manifest['labels'] = {name:wrappers[at] for name,at in old_labels.items()}
    manifest['trace'] = dict(format='PCS2',mode=mode,layer_ticks=LAYER_TICKS,
        body_tick_offset=11,start_ticks=1,end_gateway_ticks=3,
        original_labels=old_labels,layers=metadata,terminal_ticks=terminal_costs,
        terminal_gateways={('checkpoint' if terminal==mon['checkpoint_entry'] else 'terminal'):at
                           for terminal,at in gateways.items()},
        terminal_snapshots=dict(checkpoint=True,terminal=mon['final_snapshot']),
        completion_marker='PHT1F',
        code_bytes=(len(image)*8-started)//8,wrapper_bits=size,
        phase_markers='PHT1: B boot complete, C compute complete, S snapshot begins')
    return image


def frames(stream, manifest):
    """Yield bounded decoded records; callers need not retain any trace."""
    f = Format(manifest['boundary']['space_bits'],manifest['processor_n'])
    _,_,rsp = protocol(f.space_bits)
    row_bytes = (f.isz+7)//8
    def take(n):
        data=bytearray()
        while len(data)<n:
            part=stream.read(n-len(data))
            if not part: raise ValueError('truncated PCS2 record')
            data.extend(part)
        return bytes(data)
    while True:
        first=stream.read(1)
        if not first:return
        magic=first+take(3)
        if magic==b'PHT1':
            phase=take(1)
            if phase not in (b'B',b'C',b'S',b'F'):raise ValueError('unknown phase marker')
            yield dict(type='phase',phase=phase.decode());continue
        header=magic+take(FRAME.size-4)
        magic,kind,mode,length=FRAME.unpack(header)
        if magic!=b'PCS2' or mode not in (0,1) or bool(mode)!=(manifest['trace']['mode']=='channels'):
            raise ValueError('incompatible PCS2 header/mode')
        body_size=f.layer_bytes if mode==0 else 2*row_bytes
        expected = META.size+32+8+body_size+row_bytes+(rsp[1]+7)//8 if kind==1 else END_SIZE-FRAME.size
        if kind not in (1,2) or length!=expected:raise ValueError('invalid PCS2 record length')
        data=take(length)
        if kind==2:
            end_kind,reason=data[:2]
            if data[2:34].hex()!=f.description['layout_id'] or end_kind not in (1,2) or reason not in (0,1):
                raise ValueError('invalid PCS2 stop record')
            status=field(data,42*8,32)
            yield dict(type='end',kind='checkpoint' if end_kind==2 else 'terminal',
                       reason='limit' if reason else 'idle',committed=field(data,34*8,64),
                       guest_status=status,outcome='limit' if end_kind==2 else 'idle' if status==10 else 'error');continue
        home,ncopy,phase,nsel,s0,s1=META.unpack_from(data)
        if data[META.size:META.size+32].hex()!=f.description['layout_id'] or phase>2 or nsel>2:
            raise ValueError('invalid PCS2 layer metadata')
        committed=field(data,(META.size+32)*8,64)
        at=META.size+32+8
        body=data[at:at+body_size];at+=body_size
        control=instruction(data,at*8,f);at+=row_bytes
        values={name:field(data,at*8+offset,width) for name,(offset,width) in rsp[0].items()}
        selected=[s0,s1][:nsel]
        rows = [(i,instruction(body,i*f.isz,f)) for i in range(f.slots-1)] if not mode else [
            (slot,instruction(body,i*row_bytes*8,f)) for i,slot in enumerate(selected)]
        yield dict(type='layer',home=home,copies=ncopy,phase=phase,committed=committed,
                   selected=selected,rows=rows,control=control,status=values)


def audit(stream, manifest, *, terminal=None, on_event=None):
    """Validate executed operands/framing and summarize exact application counts."""
    trace=manifest['trace']
    if trace.get('layer_ticks') != LAYER_TICKS: raise ValueError('obsolete nonconforming PCS2 schedule')
    f=Format(manifest['boundary']['space_bits'],manifest['processor_n'])
    summary=dict(layers=0,application_layers=0,monitor_layers=0,control_layers=0,
                 copies=0,monitor_copies=0,data_ops=0,sys_ops=0,input_bytes=0,output_bytes=0)
    started=ended=False;end=None;last_commit=None;compute_end=False;snapshot_start=False;finished=False;next_target=None
    phase_names=['application','monitor','control']
    for event in frames(stream,manifest):
        if event['type']=='phase':
            if event['phase']=='B':
                if started or ended:raise ValueError('duplicate/out-of-order boot marker')
                started=True
            elif event['phase']=='C':
                if not started or compute_end or ended:raise ValueError('out-of-order compute marker')
                compute_end=True
            elif event['phase']=='S':
                if not ended or snapshot_start or finished:raise ValueError('out-of-order snapshot marker')
                snapshot_start=True
            elif event['phase']=='F':
                if not ended or finished:raise ValueError('out-of-order completion marker')
                if trace['terminal_snapshots'][end['kind']] and not snapshot_start:
                    raise ValueError('completion before snapshot start')
                finished=True
            continue
        if not started or ended:raise ValueError('trace events outside cooperative interval')
        if event['type']=='end':
            if not compute_end or next_target!=trace['terminal_gateways'][event['kind']]:
                raise ValueError('stop disagrees with executed control transfer')
            ended=True;end=event
            if last_commit is not None and event['committed']<last_commit:raise ValueError('regressed stop counter')
            continue
        meta=trace['layers'].get(str(event['home']))
        if compute_end:raise ValueError('layer after compute end')
        if meta is None or event['copies']!=meta['ordinary'] or event['selected']!=meta['slots'] or phase_names[event['phase']]!=meta['phase']:
            raise ValueError('layer metadata disagrees with generator manifest')
        if next_target is not None and next_target!=meta['wrapper']:raise ValueError('executed control-flow discontinuity')
        n,dst,src=event['control']
        if n!=f.layer_bits or dst!=0:raise ValueError('invalid original layer control')
        next_target=src
        if event['phase']!=1:
            if last_commit is not None and event['committed']<last_commit:raise ValueError('regressed guest counter')
            last_commit=event['committed']
        summary['layers']+=1
        summary[meta['phase']+'_layers']+=1
        summary['monitor_copies' if event['phase']==1 else 'copies']+=event['copies']
        if trace['mode']=='full':
            actual=sum(n>0 and max(dst,src)<f.space_bits for _,(n,dst,src) in event['rows'])
            if actual!=event['copies']:raise ValueError('actual ordinary-copy count mismatch')
        if trace['mode']=='full':
            validate([row for _,row in event['rows']]+[event['control']],f.space_bits)
        for slot,(n,dst,src) in event['rows']:
            if not n:continue
            if slot>=f.slots-1:raise ValueError('invalid executed slot')
            for pos in (src,dst):
                if pos<f.space_bits and pos+n>f.space_bits:raise ValueError('executed copy out of space')
            if dst<f.space_bits:
                if dst<f.layer_bits:raise ValueError('application copy writes processor')
            if max(dst,src)>=f.space_bits:
                if dst==f.space_bits or src==f.space_bits:
                    summary['sys_ops']+=1
                    kind='sys'
                else:
                    if min(dst,src)>=f.space_bits:raise ValueError('device-to-device copy')
                    values=event['status'];device=max(dst,src)
                    if values['moved']>(n+7)//8 or values['eof']>1:raise ValueError('invalid transferred byte count')
                    summary['data_ops']+=1
                    direction='input' if src==device else 'output'
                    summary[direction+'_bytes']+=values['moved']
                    kind='channel'
                if on_event:on_event(dict(type=kind,step=summary['layers'],physical_tick=(summary['layers']-1)*LAYER_TICKS+12,
                    application_step=summary['application_layers']+summary['control_layers'],
                    committed=event['committed'],home=event['home'],slot=slot,n=n,dst=dst,src=src,
                    status=event['status'] if kind=='channel' else None))
            elif on_event and event['phase']==0:
                on_event(dict(type='copy',step=summary['layers'],home=event['home'],slot=slot,n=n,dst=dst,src=src))
    if not started or not ended or snapshot_start!=trace['terminal_snapshots'][end['kind']]:
        raise ValueError('trace has no cooperative stop (host limit/interruption)')
    if trace.get('completion_marker') and not finished:
        raise ValueError('trace/report incomplete (missing completion marker)')
    if not trace.get('completion_marker') and terminal is None:
        raise ValueError('older PCS2 needs a complete terminal receipt')
    if terminal and (terminal['kind']!=end['kind'] or terminal['reason']!=end['reason'] or
                     terminal['counts']['committed']!=end['committed'] or terminal['guest_status']!=end['guest_status']):
        raise ValueError('trace stop disagrees with terminal status')
    report_key='checkpoint' if end['kind']=='checkpoint' else 'final'
    summary.update(stop=end,physical_ticks=1+summary['layers']*LAYER_TICKS+3+trace['terminal_ticks'][report_key])
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path);parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--events',action='store_true',help='stream application copy/channel/SYS events as JSON lines')
    parser.add_argument('--status',type=Path,help='optional SPT terminal receipt to cross-check the trace')
    args=parser.parse_args()
    try:
        with (gzip.open(args.trace,'rb') if args.trace.suffix=='.gz' else args.trace.open('rb')) as stream:
            manifest=json.loads(args.manifest.read_text())
            from .terminal import decode_terminal
            terminal=decode_terminal(args.status.read_bytes(),manifest['boundary']) if args.status else None
            callback=(lambda event: print(json.dumps(event))) if args.events else None
            print(json.dumps(audit(stream,manifest,on_event=callback,terminal=terminal),indent=2))
    except (OSError,ValueError,KeyError) as error:parser.error(str(error))

if __name__=='__main__':main()
