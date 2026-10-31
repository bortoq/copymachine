import pickle, sys, glob, collections, bisect
pkl, histdir = sys.argv[1], sys.argv[2]
top = int(sys.argv[3]) if len(sys.argv) > 3 else 40
r, info = pickle.load(open(pkl, 'rb'))
spans = sorted((v['entry'] >> 10, (v['entry'] >> 10) + v['size'], k) for k, v in r.items())
starts = [s[0] for s in spans]
tot = collections.Counter()
for f in glob.glob(histdir + '/*.txt'):
    for l in open(f):
        k, c = map(int, l.split())
        i = bisect.bisect_right(starts, k) - 1
        if i >= 0 and k < spans[i][1]: tot[spans[i][2]] += c
        elif k < spans[0][0] and k >= (536870912 >> 10): tot['(tramp/thrower/helpers)'] += c
        elif k < (536870912 >> 10): tot['(loader/low)'] += c
        else: tot['(other:heap/after)'] += c
total = sum(tot.values())
print('total', total)
for k, c in tot.most_common(top): print(f'{c:>12} {100*c/total:5.1f}%  {k}')
pickle.dump(tot, open(histdir + '.tot.pkl', 'wb'))
