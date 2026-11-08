import sys, os, tempfile
import run as R
from common import run
import l3ctext
src=open(sys.argv[1]).read()
img=R.chain_image(src)
print(len(img))
fn='/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/w2318/img.bin'
open(fn,'wb').write(img)
r=run(img,20,2,checked=True,limit=10**7,files=[fn]); print('chain',r.out,r.rc,r.ticks,r.err[:300])
