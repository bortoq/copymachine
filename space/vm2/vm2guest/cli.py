"""Launch guest copycode. The host never fetches or executes a vm2 instruction."""
import argparse,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,threading
from pathlib import Path
from .compiler import compile_guest

ROOT=Path(__file__).resolve().parents[1]

def unsigned(value):
    if not value or any(c not in '0123456789' for c in value) or int(value)>=1<<64:
        raise argparse.ArgumentTypeError('expected unsigned decimal uint64')
    return int(value)

def cached(size,slots,ticks,offset):
    import copycode.vm1.optimize,copycode.vm1.machine,copycode.vm1.boot,copycode.vm1.schedule
    files=sorted(Path(__file__).parent.glob('*.py'))+[Path(module.__file__) for module in
        (copycode.vm1.optimize,copycode.vm1.machine,copycode.vm1.boot,copycode.vm1.schedule)]
    identity=hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()
    key=hashlib.sha256(json.dumps([identity,size,slots,ticks,offset]).encode()).hexdigest()
    cache=Path(os.environ.get('VM2_CACHE',Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'copymachine/vm2'))
    cache.mkdir(parents=True,exist_ok=True)
    folder=cache/key
    if folder.is_dir():
        meta=json.loads((folder/'manifest.json').read_text());packet=(folder/'boot.bin').read_bytes()
        if meta['boot_sha256']==hashlib.sha256(packet).hexdigest():return packet,meta
        raise ValueError('corrupt vm2 guest cache: '+str(folder))
    _,packet,meta=compile_guest(size,slots,ticks=ticks,input_offset=offset)
    with tempfile.TemporaryDirectory(dir=cache,prefix='.building-') as name:
        temporary=Path(name);(temporary/'boot.bin').write_bytes(packet)
        (temporary/'manifest.json').write_text(json.dumps(meta,sort_keys=True,indent=2)+'\n')
        try:temporary.rename(folder)
        except FileExistsError:pass
    return packet,meta

from copycode.hostpaths import output_dir

def main(argv=None):
    parser=argparse.ArgumentParser(description='vm2 [-s bits] [-p instructions] [-t ticks], implemented by copycode on emulator',allow_abbrev=False)
    parser.add_argument('-s',type=unsigned,default=65520)
    parser.add_argument('-p',type=unsigned,default=64)
    parser.add_argument('-t',type=unsigned,default=0)
    args=parser.parse_args(argv)
    # Capture actual inherited descriptors before cache/tempfiles use free numbers.
    inherited=[]
    for descriptor in (3,4):
        try:os.fstat(descriptor);inherited.append(descriptor)
        except OSError:pass
    candidate=output_dir((ROOT.parent.parent if ROOT.parent.name == 'space' else ROOT.parent)/'emulator')/'bitcopy/emulator'
    binary=os.environ.get('EMULATOR',str(candidate) if candidate.is_file() else (shutil.which('emulator') or 'emulator'))
    child=None
    try:
        regular=stat.S_ISREG(os.fstat(0).st_mode)
        offset=os.lseek(0,0,os.SEEK_CUR) if regular else 0
        packet,meta=cached(args.s,args.p,args.t,offset)
        command=[binary,'-s',str(meta['host']['size']),'-p',str(meta['host']['slots'])]
        if regular:
            # Seekable concatenation gives guest SEEK/FSTAT the original stream
            # coordinates through the copycode's explicit prefix translation.
            with tempfile.TemporaryFile() as source:
                source.write(packet);at=0
                while True:
                    data=os.pread(0,65536,at)
                    if not data:break
                    source.write(data);at+=len(data)
                source.seek(0)
                child=subprocess.Popen(command,stdin=source,pass_fds=inherited)
                code=child.wait()
        else:
            child=subprocess.Popen(command,stdin=subprocess.PIPE,pass_fds=inherited)
            def feed():
                try:
                    child.stdin.write(packet);child.stdin.flush()
                    while True:
                        # Raw read avoids a daemon holding Python's stdin-buffer lock at exit.
                        data=os.read(0,65536)
                        if not data:break
                        child.stdin.write(data);child.stdin.flush()
                except BrokenPipeError:pass # A virtual halt need not consume the rest of stdin.
                finally:
                    try:child.stdin.close()
                    except BrokenPipeError:pass
            threading.Thread(target=feed,daemon=True,name='vm2-stdin').start()
            code=child.wait()
        return code if code>=0 else 128-code
    except ValueError as error:
        print('vm2:',error,file=sys.stderr);return 2
    except MemoryError:
        print('vm2: out of memory',file=sys.stderr);return 1
    except (OSError,OverflowError) as error:
        print('vm2:',error,file=sys.stderr);return 1
    finally:
        if child is not None and child.poll() is None:child.terminate();child.wait()
