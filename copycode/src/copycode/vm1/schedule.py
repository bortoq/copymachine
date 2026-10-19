"""Deterministic interval scheduler for ordinary vm1 copycode (MIT).

Symbols identify disjoint address arenas, including individual code records.
RAW/WAR/WAW constrain order; every physical operand, including two sources,
conflicts within a layer. Fetch dependencies require two layers after a patch.
Channels/unknown dynamic operands must be separated by caller-owned barriers;
this module never guesses their effects or inserts implicit fan-out.
"""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass

@dataclass(frozen=True)
class Span:
    arena: object
    lo: int
    hi: int
    def __post_init__(self):
        if self.lo < 0 or self.hi <= self.lo:raise ValueError('invalid half-open span')
    def overlaps(self, other):
        return self.arena == other.arena and self.lo < other.hi and other.lo < self.hi
    def part(self, lo, hi):return Span(self.arena,self.lo+lo,self.lo+hi)

@dataclass(frozen=True)
class Copy:
    dst: Span
    src: Span
    def __post_init__(self):
        if self.dst.hi-self.dst.lo != self.src.hi-self.src.lo:raise ValueError('unequal copy widths')
        if self.dst.overlaps(self.src):raise ValueError('intersecting copy operands')
    @property
    def width(self):return self.dst.hi-self.dst.lo
    def part(self, lo, hi):return Copy(self.dst.part(lo,hi),self.src.part(lo,hi))

@dataclass(frozen=True)
class Task:
    name: str
    copies: tuple = ()
    fetch: tuple = ()
    extra_reads: tuple = ()
    protected: bool = False
    barrier: bool = False
    @property
    def reads(self):return tuple(c.src for c in self.copies)+self.extra_reads
    @property
    def writes(self):return tuple(c.dst for c in self.copies)
    @property
    def operands(self):
        sources=tuple(c.src for c in self.copies if not any(
            r.arena==c.src.arena and r.lo<=c.src.lo and r.hi>=c.src.hi for r in self.extra_reads))
        return sources+self.extra_reads+self.writes
    @property
    def slots(self):return len(self.copies)

class _History:
    """Piecewise-constant last writer and readers; never expand spans to bits."""
    def __init__(self):self.bounds=[0];self.states=[(None,frozenset())]
    def split(self, at):
        i=bisect_left(self.bounds,at)
        if i==len(self.bounds) or self.bounds[i]!=at:
            self.bounds.insert(i,at);self.states.insert(i,self.states[i-1])
        return i
    def access(self, span, task, writing, delay, predecessors):
        begin=self.split(span.lo);end=self.split(span.hi)
        for i in range(begin,end):
            writer,readers=self.states[i]
            if writer is not None and writer!=task:
                predecessors[writer]=max(predecessors.get(writer,0),delay)
            if writing:
                for reader in readers:
                    if reader!=task:predecessors[reader]=max(predecessors.get(reader,0),1)
                self.states[i]=(task,frozenset())
            else:self.states[i]=(writer,readers|{task})

def plan(tasks, slots):
    """Return layers of Tasks, including required empty fetch-delay layers.

    Stable greedy earliest placement; optimal schedules are not promised.
    A Task is an indivisible group: all its physical operands must be disjoint.
    """
    if slots<1:raise ValueError('positive slot budget required')
    tasks=list(tasks)
    if len({t.name for t in tasks})!=len(tasks):raise ValueError('duplicate task name')
    histories={};layers=[];occupied=[];usage=[];levels=[];floor=0
    for number,task in enumerate(tasks):
        if task.slots>slots:raise ValueError('task exceeds slot budget')
        spans=task.operands
        if any(x.overlaps(y) for i,x in enumerate(spans) for y in spans[i+1:]):
            raise ValueError('overlapping operands including sources in '+task.name)
        predecessors={}
        for reading,delay in ((task.reads,1),(task.fetch,2)):
            for span in reading:
                histories.setdefault(span.arena,_History()).access(span,number,False,delay,predecessors)
        for span in task.writes:
            histories.setdefault(span.arena,_History()).access(span,number,True,1,predecessors)
        level=max(floor,max((levels[i]+delay for i,delay in predecessors.items()),default=0))
        if task.barrier:level=max(level,max(levels,default=-1)+1)
        while level<len(layers):
            if usage[level]+task.slots<=slots and not any(x.overlaps(y) for x in spans for y in occupied[level]):break
            level+=1
        while len(layers)<=level:layers.append([]);occupied.append([]);usage.append(0)
        layers[level].append(task);occupied[level].extend(spans);usage[level]+=task.slots;levels.append(level)
        if task.barrier:floor=level+1
    return layers

