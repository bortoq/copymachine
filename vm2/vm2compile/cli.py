"""Compile/check/run direct artifacts. Compatibility vm2 is a separate command."""
import argparse,json,os,shutil,sys
from pathlib import Path
from .model import Program
from .artifact import build,save,load,resume,launch

def unsigned(value):
    if not value or any(c not in '0123456789' for c in value) or int(value)>=1<<64:raise argparse.ArgumentTypeError('expected decimal uint64')
    return int(value)

def main(argv=None):
    inherited=[]
    for descriptor in (3,4):
        try:os.fstat(descriptor);inherited.append(descriptor)
        except OSError:pass
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('compile');c.add_argument('source',type=Path);c.add_argument('-o',type=Path,required=True);c.add_argument('--exact-size',action='store_true')
    c=sub.add_parser('check');c.add_argument('artifact',type=Path)
    c=sub.add_parser('run');c.add_argument('artifact',type=Path);c.add_argument('--physical-ticks',type=unsigned,default=0)
    c=sub.add_parser('resume');c.add_argument('artifact',type=Path);c.add_argument('snapshot',type=Path);c.add_argument('-o',type=Path,required=True)
    args=p.parse_args(argv)
    try:
        if args.command=='compile':
            source=Program.load(json.loads(args.source.read_text()));payload,manifest=build(source,exact_size=args.exact_size);save(args.o,payload,manifest)
        elif args.command=='resume':
            payload,manifest=resume(args.artifact,args.snapshot);save(args.o,payload,manifest)
        else:
            payload,manifest=load(args.artifact)
            if args.command=='check':print(manifest['schema'],manifest['files']['image.bin']['sha256'])
            else:
                root=Path(__file__).resolve().parents[1]
                candidate=root.parent/'vm1/vm1'
                binary=os.environ.get('VM1',str(candidate) if candidate.is_file() else (shutil.which('vm1') or 'vm1'))
                return launch(payload,manifest,binary=binary,ticks=args.physical_ticks,inherited=inherited)
        return 0
    except (ValueError,KeyError,TypeError,OSError,OverflowError) as error:print('vm2c:',error,file=sys.stderr);return 2
    except MemoryError:print('vm2c: out of memory',file=sys.stderr);return 1
