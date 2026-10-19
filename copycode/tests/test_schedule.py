"""Independent bit oracle for vm1 planning and dead-write elimination (MIT)."""
import random
import sys
from copycode.vm1.schedule import Span,Copy,Task,plan
assert 'copycode.vm1.optimize' not in sys.modules, 'scheduler imports optimizer'
from copycode.vm1.optimize import eliminate_dead_writes,merge_adjacent,optimize

def span(at,n=1,arena='m'):return Span(arena,at,at+n)
def copy(dst,src,n=1):return Copy(span(dst,n),span(src,n))
def task(name,dst,src,n=1):return Task(str(name),(copy(dst,src,n),))
def execute(layers,initial):
    memory=list(initial)
    for group in layers:
        before=memory[:];positions=[]
        for t in group:
            for c in t.copies:
                assert c.dst.arena==c.src.arena=='m'
                for s in (c.dst,c.src):
                    bits=set(range(s.lo,s.hi))
                    assert not any(bits&other for other in positions),(group,s)
                    positions.append(bits)
                memory[c.dst.lo:c.dst.hi]=before[c.src.lo:c.src.hi]
    return memory

def level_of(layers,name):return next(i for i,g in enumerate(layers) if any(t.name==name for t in g))
# RAW, WAR, WAW, and read/read sharing must all be respected.
for tasks in ([task('a',16,0,4),task('b',32,16,4)],
              [task('a',16,0,4),task('b',0,32,4)],
              [task('a',16,0,4),task('b',16,32,4)],
              [task('a',16,0,4),task('b',32,0,4)]):
    layers=plan(tasks,7);assert level_of(layers,'a')<level_of(layers,'b')
assert len(plan([task(i,32+i,2*i) for i in range(8)],7))==2
# Patch fields can be parallel; fetch must wait at least two physical ticks.
patches=[Task('p0',(Copy(span(0,4,'code'),span(0,4)),)),
         Task('p1',(Copy(span(4,4,'code'),span(4,4)),)),
         Task('execute',(copy(20,16,4),),(span(0,8,'code'),))]
layers=plan(patches,7)
assert level_of(layers,'p0')==level_of(layers,'p1')==0
assert level_of(layers,'execute')==2
# Barriers retain order even for otherwise independent addresses.
layers=plan([task('before',32,0),Task('io',barrier=True,protected=True),task('after',33,1)],7)
assert [level_of(layers,n) for n in ('before','io','after')]==[0,1,2]
# Split a partially dead write; preserve observable sources of surviving bits.
tasks=[task('wide',32,0,16),task('middle',36,20,4)]
optimized=eliminate_dead_writes(tasks)
assert len(optimized[0].copies)==2
live=eliminate_dead_writes([task('needed',32,0,8),task('unused',48,16,8)],live_out=[span(32,8)])
assert [t.name for t in live]==['needed']
assert len(optimize([task('unused',48,16,8)],7,live_out=[]))==0
assert [(c.dst.lo,c.dst.hi) for c in optimized[0].copies]==[(32,36),(40,48)]
assert len(merge_adjacent([copy(32,0,4),copy(36,4,4)]))==1
assert sum(t.slots for layer in optimize([task('a',32,0,4),task('b',36,4,4)],7) for t in layer)==1
# Planning preserves even redundant writes and adjacent copies verbatim.
unchanged=[task('first',32,0,4),task('overwrite',32,8,4),task('adjacent',36,12,4)]
planned=plan(unchanged,7)
assert {id(t) for layer in planned for t in layer}=={id(t) for t in unchanged}
assert sum(t.slots for layer in planned for t in layer)==3
# A protected or observed write cannot be removed.
assert len(eliminate_dead_writes([Task('kept',(copy(32,0),),protected=True),task('overwrite',32,1)]))==2
assert len(eliminate_dead_writes([task('write',32,0),task('read',48,32),task('overwrite',32,1)]))==3
assert len(eliminate_dead_writes([task('write',32,0),Task('io',barrier=True),task('overwrite',32,1)]))==3
# Wrong schedules are rejected, not silently repaired.
for tasks,slots in [([Task('shared',(copy(16,0),copy(32,0)))],7),
                    ([task('a',16,0),task('a',32,1)],7),([Task('wide',(copy(16,0),copy(32,1)))],1)]:
    try:plan(tasks,slots)
    except ValueError:pass
    else:raise AssertionError('invalid task accepted')
# Wide spans stay interval based; no expansion into billions of positions.
assert len(plan([task('wide',1<<40,0,1<<30)],7))==1
rng=random.Random(5019)
for trial in range(2000):
    tasks=[]
    for i in range(rng.randrange(1,70)):
        n=rng.randrange(1,13)
        while True:
            src,dst=rng.randrange(96-n),rng.randrange(96-n)
            if dst+n<=src or src+n<=dst:break
        tasks.append(task(i,dst,src,n))
    initial=[rng.randrange(2) for _ in range(96)]
    expected=execute([[t] for t in tasks],initial)
    for pruning in (False,True):
        selected=eliminate_dead_writes(tasks) if pruning else tasks
        # Splitting may exceed a task's atomic slot budget; generic callers may
        # split independent fragments into individual tasks before scheduling.
        selected=[Task(t.name+'-'+str(k),(c,)) for t in selected for k,c in enumerate(t.copies)]
        layers=plan(selected,rng.randrange(1,9))
        assert execute(layers,initial)==expected,(trial,pruning)
        if trial%100==0:assert plan(selected,7)==plan(selected,7)
    optimized=optimize(tasks,rng.randrange(1,9))
    assert execute(optimized,initial)==expected,(trial,"full optimizer")
print('PASS vm1 scheduler/optimizer: 2000 randomized whole-memory oracles, hazards, fan-out, fetch, barriers, partial writes, wide intervals')
