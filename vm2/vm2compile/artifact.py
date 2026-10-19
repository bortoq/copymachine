"""Deterministic direct artifacts and cooperative native-memory snapshots (MIT)."""
import hashlib,json,os,subprocess,tempfile,threading,stat
from pathlib import Path
from copycode.vm1.machine import Format,put
from copycode.vm1.boot import boot_stream
from .abi import ABI

FILES=('image.bin','boot.bin','map.json')
def digest(data):return hashlib.sha256(data).hexdigest()
def json_bytes(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()

def static_code_digest(image,manifest):
    bits=manifest['code_bits']
    if not isinstance(bits,int) or bits<1 or bits>len(image)*8:raise ValueError('invalid code size')
    data=bytearray(image[:(bits+7)//8])
    for lo,hi in manifest['mutable_code_ranges']:
        if not 0<=lo<hi<=bits:raise ValueError('invalid mutable code range')
        for at in range(lo,hi):data[at//8]&=~(128>>(at%8))
    return digest(data)

def seal(image,manifest,mapping):
    image=bytearray(image);manifest=dict(manifest);f=Format(manifest['vm1']['size'],manifest['vm1']['slots'])
    origin=0
    relocations=manifest.get('stdin_origin_relocations',[])
    for _ in range(8):
        put(image,manifest['stdin_origin_bits'],64,origin)
        for at,width,offset in relocations:put(image,at,width,origin+offset)
        packet=boot_stream(image,f)
        if len(packet)==origin:break
        origin=len(packet)
    else:raise ValueError('bootstrap origin did not converge')
    manifest['stdin_origin_bytes']=origin
    payload={'image.bin':bytes(image),'boot.bin':packet,'map.json':json_bytes(mapping)}
    manifest['static_code_sha256']=static_code_digest(image,manifest)
    manifest['files']={name:dict(bytes=len(data),sha256=digest(data)) for name,data in payload.items()}
    return payload,manifest

def build(program,**options):
    from .compiler import compile_program
    image,manifest,mapping=compile_program(program,**options)
    return seal(image,manifest,mapping)

def save(folder,payload,manifest):
    folder=Path(folder)
    if folder.exists():raise ValueError('artifact output already exists: '+str(folder))
    folder.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=folder.parent,prefix='.vm2-building-') as name:
        temporary=Path(name)
        for file in FILES:(temporary/file).write_bytes(payload[file])
        (temporary/'manifest.json').write_bytes(json_bytes(manifest))
        temporary.rename(folder)

def load(folder):
    folder=Path(folder)
    if not folder.is_dir():raise ValueError('artifact directory required')
    if {p.name for p in folder.iterdir()}!=set(FILES)|{'manifest.json'}:raise ValueError('unexpected artifact files')
    if any((folder/name).is_symlink() or not (folder/name).is_file() for name in (*FILES,'manifest.json')):raise ValueError('artifact requires regular files')
    manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('schema')!=ABI or set(manifest.get('files',{}))!=set(FILES):raise ValueError('unsupported direct artifact ABI')
    f=Format(manifest['vm1']['size'],manifest['vm1']['slots'])
    if manifest['vm1']!=f.describe():raise ValueError('vm1 format mismatch')
    payload={}
    for name in FILES:
        data=(folder/name).read_bytes();identity=manifest['files'][name]
        if len(data)!=identity['bytes'] or digest(data)!=identity['sha256']:raise ValueError('corrupt artifact: '+name)
        payload[name]=data
    if len(payload['image.bin'])!=f.image_bytes:raise ValueError('image size mismatch')
    if static_code_digest(payload['image.bin'],manifest)!=manifest['static_code_sha256']:raise ValueError('static code identity mismatch')
    if manifest['stdin_origin_bits']<f.layer_bits or manifest['stdin_origin_bits']+64>f.size:raise ValueError('invalid stdin origin field')
    mapping=json.loads(payload['map.json'])
    if mapping.get('schema')!='vm2-direct-map-v1':raise ValueError('unsupported source map')
    return payload,manifest

def resume(folder,snapshot):
    payload,manifest=load(folder);data=Path(snapshot).read_bytes()
    f=Format(manifest['vm1']['size'],manifest['vm1']['slots'])
    if len(data)!=f.image_bytes:raise ValueError('snapshot size/ABI mismatch')
    if static_code_digest(data,manifest)!=manifest['static_code_sha256']:raise ValueError('snapshot code/ABI differs from the declared artifact')
    # External file offsets and closed descriptors remain caller-owned state.
    manifest=dict(manifest);manifest['snapshot_sha256']=digest(data)
    return seal(data,manifest,json.loads(payload['map.json']))

def launch(payload,manifest,*,binary='vm1',ticks=0,inherited=()):
    if not isinstance(ticks,int) or not 0<=ticks<1<<64:raise ValueError('physical tick limit must be uint64')
    command=[str(binary),'-s',str(manifest['vm1']['size']),'-p',str(manifest['vm1']['slots']),'-t',str(ticks)]
    packet=payload['boot.bin'];child=None
    try:
        if stat.S_ISREG(os.fstat(0).st_mode):
            # Native stdin begins after the compiled boot. The manifest/SDK
            # explicitly expose this origin for SEEK/FSTAT adapters.
            with tempfile.TemporaryFile() as source:
                source.write(packet)
                while True:
                    data=os.read(0,65536)
                    if not data:break
                    source.write(data)
                source.seek(0);child=subprocess.Popen(command,stdin=source,pass_fds=inherited);code=child.wait()
        else:
            child=subprocess.Popen(command,stdin=subprocess.PIPE,pass_fds=inherited)
            def feed():
                try:
                    child.stdin.write(packet);child.stdin.flush()
                    while True:
                        data=os.read(0,65536)
                        if not data:break
                        child.stdin.write(data);child.stdin.flush()
                except BrokenPipeError:pass
                finally:
                    try:child.stdin.close()
                    except BrokenPipeError:pass
            threading.Thread(target=feed,daemon=True,name='vm2-direct-input').start();code=child.wait()
        return code if code>=0 else 128-code
    finally:
        if child is not None and child.poll() is None:child.terminate();child.wait()
