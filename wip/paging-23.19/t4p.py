import sys, os
sys.path.insert(0,'/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower')
sys.dont_write_bytecode=True
import l3ctext, l5
from common import run
src=open('/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower/programs/l4p.tw').read()
img,P=l5.chain_image(src)
print('l4p image',len(img),P)
open('l4p.img','wb').write(img)
for f in sys.argv[1:]:
    l2,err=l3ctext.encode(open(f,'rb').read())
    assert not err
    ref,e=l3ctext.long_pass(l2)
    tmp='/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/w2318/pages.tmp'
    if os.path.exists(tmp): os.remove(tmp)
    r=run(img,20,P,checked=False,limit=500*10**6,stdin=l2,files=[tmp])
    print(f, r.out==ref, len(ref), len(r.out), r.ticks, r.err[-100:])
    if r.out!=ref:
        for i,(a,b) in enumerate(zip(ref,r.out)):
            if a!=b: print(i, ref[i-50:i+50], r.out[i-50:i+50]); break
