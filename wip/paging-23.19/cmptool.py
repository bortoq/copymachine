import sys
sys.path.insert(0,'/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower')
sys.dont_write_bytecode=True
import l3ctext
from common import run
IMG=open('/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/w2318/tool.img','rb').read()
def tool(src, limit=300*10**6):
    r=run(IMG,20,3,checked=False,limit=limit,stdin=src+b'\0')
    return r
for f in sys.argv[1:]:
    src=open(f,'rb').read()
    ref,err=l3ctext.encode(src)
    r=tool(src)
    exp=ref+(b'' if err else b'')
    ok = r.out==ref
    print(f, ok, len(ref), len(r.out), err, r.err[-80:].strip(), r.ticks)
    if not ok:
        for i,(a,b) in enumerate(zip(ref,r.out)):
            if a!=b:
                print('first diff at',i, ref[max(0,i-80):i+60], r.out[max(0,i-80):i+60]); break
