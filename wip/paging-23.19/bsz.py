import sys, re
sys.path.insert(0,'/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower')
import l3ctext
fn=sys.argv[1]
src=open(fn,'rb').read()
l3ctext.LIMIT=10**7; 
c=l3ctext.Compiler(); c.put(l3ctext.prelude()); c.limit=10**7
try: l3ctext.run(c,src); c.finish()
except l3ctext.Stop as e: print('stop',e.why)
out=''.join(c.out)
res,tail=l3ctext.split_pages(out)
pos=0; order=[]
for ln in res.split('\n'):
    t=ln.split()
    if not t: continue
    if t[0].startswith(':'): order.append((t[0][1:],pos))
    elif t[0]=='z': pos+=int(t[1],16)
    elif t[0]=='c': pos+=80
    elif t[0]=='d': pos+=int(t[1],16)
    elif t[0]=='o': pos=0
print('resident end',pos,'tail',len(tail))
sz=[]
for i,(n,p) in enumerate(order):
    q=order[i+1][1] if i+1<len(order) else pos
    if n[0] in 'br': sz.append((n,q-p))
sz2=sorted(sz,key=lambda x:-x[1])
print(sz2[:50])
# source order listing with line numbers of the biggest
lines=open(fn).read().split('\n')
idx={}
for i,l in enumerate(lines,1):
    m=re.match(r':(\w+) (block|word)\b',l)
    if m: idx['b'+m.group(1)]=i
import pickle
pickle.dump((sz,idx),open('bsz.pkl','wb'))
