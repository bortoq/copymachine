"""Optional local copycode transformations, separate from scheduling (MIT)."""
from dataclasses import replace
from .schedule import Span, Copy, Task, plan

class _Ranges:
    def __init__(self):self.items={}
    def covered(self, span):
        return [(max(lo,span.lo),min(hi,span.hi)) for lo,hi in self.items.get(span.arena,())
                if lo<span.hi and span.lo<hi]
    def add(self, span):
        pairs=self.items.setdefault(span.arena,[]);pairs.append((span.lo,span.hi));pairs.sort()
        merged=[]
        for lo,hi in pairs:
            if merged and lo<=merged[-1][1]:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
            else:merged.append((lo,hi))
        self.items[span.arena]=merged
    def subtract(self, span):
        result=[]
        for lo,hi in self.items.get(span.arena,()):
            if hi<=span.lo or lo>=span.hi:result.append((lo,hi))
            else:
                if lo<span.lo:result.append((lo,span.lo))
                if span.hi<hi:result.append((span.hi,hi))
        self.items[span.arena]=result

def eliminate_dead_writes(tasks, *, live_out=None):
    """Trim overwritten writes, or writes outside explicitly declared live_out.

    Protected tasks retain their shape (e.g. instruction records referenced by
    patches). Fetches and declared dynamic reads participate in liveness.
    """
    tasks=list(tasks);killed=_Ranges();result=[]
    if live_out is not None:
        for task in tasks:
            for span in task.writes:killed.add(span)
        for span in live_out:killed.subtract(span)
    for task in reversed(tasks):
        if task.barrier:
            killed=_Ranges();result.append(task);continue
        copies=[]
        for copy in task.copies:
            if task.protected:copies.append(copy);continue
            start=copy.dst.lo
            for lo,hi in killed.covered(copy.dst):
                if start<lo:copies.append(copy.part(start-copy.dst.lo,lo-copy.dst.lo))
                start=hi
            if start<copy.dst.hi:copies.append(copy.part(start-copy.dst.lo,copy.width))
        kept=replace(task,copies=tuple(copies))
        if copies or task.protected or task.extra_reads:
            result.append(kept)
            for span in kept.writes:killed.add(span)
            for span in kept.reads+kept.fetch:killed.subtract(span)
    return list(reversed(result))

def merge_adjacent(copies):
    """Merge only neighbouring source/destination spans with the same mapping."""
    result=[]
    for copy in copies:
        for i,old in enumerate(result):
            if old.dst.arena!=copy.dst.arena or old.src.arena!=copy.src.arena:continue
            if old.dst.hi==copy.dst.lo and old.src.hi==copy.src.lo:
                result[i]=Copy(Span(old.dst.arena,old.dst.lo,copy.dst.hi),Span(old.src.arena,old.src.lo,copy.src.hi));break
            if copy.dst.hi==old.dst.lo and copy.src.hi==old.src.lo:
                result[i]=Copy(Span(old.dst.arena,copy.dst.lo,old.dst.hi),Span(old.src.arena,copy.src.lo,old.src.hi));break
        else:result.append(copy)
    return result

def optimize(tasks, slots, *, live_out=None):
    """Dead-write fixed point, earliest placement and adjacent-copy merging.

    Preserve protected instruction records and control entries. All memory
    is observable at region exit; callers split regions at external effects.
    This is a local deterministic optimizer, not global optimal scheduling.
    """
    if slots<1:raise ValueError('positive slot budget required')
    tasks=list(tasks)
    if live_out is not None:live_out=tuple(live_out)
    while True:
        reduced=eliminate_dead_writes(tasks,live_out=live_out)
        if reduced==tasks:break
        tasks=reduced
    expanded=[]
    for task in tasks:
        if task.slots<=slots or task.protected:expanded.append(task)
        else:
            for start in range(0,task.slots,slots):
                expanded.append(replace(task,name=task.name+"/part"+str(start),copies=task.copies[start:start+slots]))
    layers=plan(expanded,slots);result=[]
    for layer in layers:
        merged=[];pending=[]
        def flush():
            if not pending:return
            copies=[c for t in pending for c in t.copies]
            while True:
                following=merge_adjacent(copies)
                if following==copies:break
                copies=following
            merged.append(Task(pending[0].name,tuple(copies),tuple(s for t in pending for s in t.fetch)))
            pending.clear()
        for task in layer:
            if task.protected or task.barrier or task.extra_reads:flush();merged.append(task)
            else:pending.append(task)
        flush();result.append(merged)
    return result
