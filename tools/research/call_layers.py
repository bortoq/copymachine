"""Число слоёв (= тактов линейного участка), которые строят call, ret и
call_indirect модели forthc (model.py). Считает вызовы Seq.layer внутри
методов Compiler при компиляции малых программ. Только стандартная
библиотека + модули space/forth/scripts."""
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]/'space/forth/scripts'
sys.path[:0]=[str(R),str(R/'pforth'),str(R.parents[1]/'copycode/src')]
from forthc import model
from copycode.vm1.compute import Seq
cnt={'n':0}
orig=Seq.layer
def layer(self,*a,**k):
    cnt['n']+=1;return orig(self,*a,**k)
Seq.layer=layer
res={}
for name in ('call','ret','call_indirect'):
    f=getattr(model.Compiler,name);acc={'n':0,'calls':0}
    def w(self,*a,_f=f,_acc=acc,**k):
        before=cnt['n'];r=_f(self,*a,**k);_acc['n']+=cnt['n']-before;_acc['calls']+=1;return r
    setattr(model.Compiler,name,w)
    res[name]=acc
def run(src):
    for a in res.values():a['n']=a['calls']=0
    model.compile_forth(src)
    return {k:(v['n'],v['calls']) for k,v in res.items()}
print('empty callee, one call   ',run(': w ; : main w ;'))
print('empty main               ',run(': main ;'))
print('execute site, empty cache',run(': w ; : main [\'] w execute ;'))
