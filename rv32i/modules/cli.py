"""Build and launch persisted RV32I artifacts; instruction execution is in vm1."""
import dependencies
import argparse,json,os,subprocess,tempfile,sys
from pathlib import Path
from direct_target import compile_image
from vm2compile.artifact import save,load,launch,resume
from copycode.vm1.machine import field
from rv32i_toolchain import Toolchain

def compile_c(sources,folder,compiler=None):
    tools=Toolchain(compiler);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    runtime=dependencies.ROOT/'runtime/rv32i';elf=folder/'program.elf';binary=folder/'program.bin'
    command=tools.command('-O2')+['-I',str(runtime),'-T',str(runtime/'link.ld'),
        '-Wl,--defsym=CS_STACK_TOP=65520',str(runtime/'start.S'),str(runtime/'runtime.c')]+list(map(str,sources))+['-lgcc','-o',str(elf)]
    (folder/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    result=subprocess.run(command,capture_output=True,timeout=30)
    (folder/'compiler.stderr').write_bytes(result.stderr)
    if result.returncode:raise ValueError(result.stderr.decode(errors='replace'))
    subprocess.run([tools.objcopy,'-O','binary',str(elf),str(binary)],check=True,timeout=15)
    return binary.read_bytes()

def run(folder,*,snapshot=None,ticks=0):
    payload,m=load(folder)
    if m.get('rv32i',{}).get('schema')!='rv32i-direct-v1':raise ValueError('RV32I artifact required')
    with (Path(snapshot).open('w+b') if snapshot else tempfile.TemporaryFile()) as saved:
        try:old=os.dup(4)
        except OSError:old=None
        try:
            os.dup2(saved.fileno(),4,inheritable=True)
            code=launch(payload,m,binary=os.environ.get('VM1',str(dependencies.VM1_ROOT/'build/bitcopy/vm1')),ticks=ticks,inherited=(4,))
        finally:
            if old is not None:os.dup2(old,4);os.close(old)
            elif saved.fileno()!=4:os.close(4)
        if code:return code
        saved.seek(0);raw=saved.read()
    if len(raw)!=len(payload['image.bin']):return 125
    mapping=json.loads(payload['map.json']);at=mapping['regions']['registers']['at']
    status=field(raw,at+m['rv32i']['status_offset'],32)
    if status==0 and m['rv32i'].get('checkpoint_every'):return 75
    if status!=10:
        print('RV32I stopped with status '+str(status),file=sys.stderr);return 125
    return field(raw,at+m['rv32i']['exit_offset'],32)&255

def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    c=commands.add_parser('build');c.add_argument('program',type=Path);c.add_argument('-o',required=True,type=Path);c.add_argument('--no-io',action='store_true');c.add_argument('--frames',action='store_true');c.add_argument('--checkpoint-every',type=int,default=0)
    c=commands.add_parser('build-c');c.add_argument('sources',nargs='+',type=Path);c.add_argument('-o',required=True,type=Path);c.add_argument('--compiler')
    c=commands.add_parser('run');c.add_argument('artifact',type=Path);c.add_argument('--snapshot',type=Path);c.add_argument('--physical-ticks',type=int,default=0)
    c=commands.add_parser('resume');c.add_argument('artifact',type=Path);c.add_argument('snapshot',type=Path);c.add_argument('-o',type=Path,required=True)
    a=parser.parse_args()
    try:
        if a.command in ('build','build-c'):
            if a.command=='build-c':
                with tempfile.TemporaryDirectory() as d:program=compile_c(a.sources,d,a.compiler)
                options={}
            else:program=a.program.read_bytes();options=dict(io=not a.no_io,frames=a.frames,checkpoint_every=a.checkpoint_every)
            payload,m=compile_image(program,**options);save(a.o,payload,m)
        elif a.command=='resume':
            payload,m=resume(a.artifact,a.snapshot);save(a.o,payload,m)
        else:return run(a.artifact,snapshot=a.snapshot,ticks=a.physical_ticks)
        return 0
    except (OSError,ValueError,KeyError,subprocess.SubprocessError,MemoryError) as e:
        print('rv32i:',e,file=sys.stderr);return 2
