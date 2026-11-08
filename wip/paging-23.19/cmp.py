import sys
import run as R
from common import run
src=open(sys.argv[1]).read()
img=R.chain_image(src)
r=run(img,20,2,checked=True,limit=10**7); print('chain',r.out,r.rc,r.ticks,r.err[:300])
p,errs=R.text.compile_text(src); print(errs)
if p is not None:
    st=p.stats
    r2=run(st['image'],st['A'],st['P'],checked=True,limit=10**7); print('py   ',r2.out,r2.rc,r2.ticks,r2.err[:300])
