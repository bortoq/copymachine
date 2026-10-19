"""Conformance oracle rejects source fan-out, not just write conflicts."""
import itertools
from pathlib import Path
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'compat/vm2'))
from schedule import validate, decode_layer
from boundary import Format,Program

bits=65520
rows=[(4,2000,1000),(4,3000,1000)]
for bad in (rows,[(4,2000,1000),(4,3000,1002)],[(4,1002,1000)],
            [(4,2000,1000),(4,1001,3000)],[(4,2000,1000),(4,2002,3000)],
            [(9,2000,bits+1),(1,3000,2009)]):
    try: validate(bad,bits)
    except ValueError: pass
    else: raise AssertionError(('accepted overlap',bad))
    if bad!=[(9,2000,bits+1),(1,3000,2009)]:
        try: Program().step(bad)
        except ValueError: pass
        else: raise AssertionError(('Program accepted overlap',bad))
for good in ([(4,2000,1000),(4,2004,1004)],[(4,1004,1000)],
             [(0,1000,1000)],[(8,2000,bits+1),(4,3000,2008)],
             [(136,bits,1000),(112,2000,bits)]):
    validate(good,bits)

# Compare the sorted validator against an independent all-pairs oracle,
# including identical starts, containment, partial overlap and adjacency.
rng=random.Random(4815);cases=0
for _ in range(6000):
    rows=[(rng.randrange(9),rng.randrange(48),rng.randrange(48)) for _ in range(rng.randrange(1,7))]
    spans=[set(range(at,at+n)) for n,d,s in rows if n for at in (d,s)]
    expected=not any(a & b for a,b in itertools.combinations(spans,2))
    try: validate(rows,bits)
    except ValueError: actual=False
    else: actual=True
    assert actual==expected,rows
    cases+=1
# The codec decodes the actual packed layer, not a generator's annotations.
f=Format(bits,8);data=f.layer([(4,2000,1000),(4,2004,1004)])
assert decode_layer(data,bits,8)[:2]==[(4,2000,1000),(4,2004,1004)]
print('schedule: source/source, source/destination, destination/destination and',cases,'all-pairs oracle cases passed')
