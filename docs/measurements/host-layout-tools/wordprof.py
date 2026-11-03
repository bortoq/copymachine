"""usage: wordprof.py WORDS.json DIR N: the ticks of the words (self) from the files DIR/*.txt of HW_PROF (prof_patch.py), the N largest; DIR.json is written."""
import sys,json,glob,bisect,collections
m=json.load(open(sys.argv[1])); ents=sorted((v>>10,k) for k,v in m.items()); keys=[e[0] for e in ents]
tot=collections.Counter(); 
for f in glob.glob(sys.argv[2]+'/*.txt'):
    for l in open(f):
        c,n=map(int,l.split())
        if c<524288: w='<program>'
        else:
            i=bisect.bisect_right(keys,c)-1
            w=ents[i][1] if i>=0 else '<prelude>'
        tot[w]+=n
T=sum(tot.values()); print('total',T)
dj=sum(n for w,n in tot.items() if w.startswith('dj-'))
print('dj-* self',dj)
for w,n in tot.most_common(int(sys.argv[3])): print(f'{w:22}{n:12}{100*n/T:6.1f}%')
json.dump(tot,open(sys.argv[2]+'.json','w'))
