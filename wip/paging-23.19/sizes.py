import sys, re
sys.path.insert(0,'/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower')
sys.dont_write_bytecode=True
import l3ctext
P='/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower/programs/l3c.tw'
src=open(P,'rb').read()
c=l3ctext.Compiler(); c.put(l3ctext.prelude())
try:
    l3ctext.run(c,src)
except l3ctext.Stop as e:
    print('stop',e.why, c.pos)
out=''.join(c.out)
pos=0; lab={}
order=[]
for ln in out.split('\n'):
    t=ln.split()
    if not t: continue
    if t[0].startswith(':'):
        order.append((t[0][1:],pos))
    elif t[0]=='z': pos+=int(t[1],16)
    elif t[0]=='c': pos+=80
    elif t[0]=='d': pos+=int(t[1],16)
    elif t[0]=='o': pos=0
print('end',pos, c.pos)
# sizes
sz={}
for i,(n,p) in enumerate(order):
    q=order[i+1][1] if i+1<len(order) else pos
    sz[n]=q-p
# walk source lines with line numbers, sections
lines=src.decode().split('\n')
sec=None; secs=[]; cur=None
for i,l in enumerate(lines,1):
    m=re.match(r'# --- (.*)',l)
    if m:
        cur=[i,m.group(1)[:60],0,0]; secs.append(cur)
    m=re.match(r':(\w+) (block|word)\b',l)
    if m and cur is not None:
        n=m.group(1)
        key=('b'+n)
        if m.group(2)=='word': cur[2]+=sz.get('r'+n,0)
        cur[2]+=sz.get(key,0); cur[3]+=1
for s in secs: print(s)
