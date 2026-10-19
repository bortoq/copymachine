"""Generate interpreter boot/manifest, optionally cooperative boundary reports."""
import argparse,json
from pathlib import Path
from .compiler import compile_guest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('-s',type=int,default=65520);p.add_argument('-p',type=int,default=64)
    p.add_argument('-t',type=int,default=0)
    p.add_argument('--snapshot',action='store_true');p.add_argument('--report',action='store_true')
    p.add_argument('--host-size',type=int);p.add_argument('-o',type=Path,required=True)
    args=p.parse_args()
    try:
        _,boot,meta=compile_guest(args.s,args.p,ticks=args.t,snapshot=args.snapshot,report=args.report,host_bits=args.host_size)
        args.o.parent.mkdir(parents=True,exist_ok=True);args.o.write_bytes(boot)
        args.o.with_suffix(args.o.suffix+'.json').write_text(json.dumps(meta,sort_keys=True,indent=2)+'\n')
    except (ValueError,OSError,MemoryError,OverflowError) as error:p.exit(1,str(error)+'\n')
if __name__=='__main__':main()
