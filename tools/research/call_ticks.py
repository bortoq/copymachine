"""Измеренные такты вызова+возврата и `['] w execute` (13.6.2).

Схема разности как у op_cost в space/forth/tools/forthc_costs.py: два размера
цикла (9 и 1), (t9 - t1) / 8, минус пустой цикл. Исполнение идёт через
forthc_costs.compiled (эмулятор checked-emulator, собранный заранее).
Слои модели берутся из tools/research/call_layers.py. Пишет
docs/research/call-ticks.json без времени и путей хоста."""
import contextlib,io,json,sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'space/forth/tools'),str(REPO/'tools/research')]
import forthc_costs
with contextlib.redirect_stdout(io.StringIO()):
    import call_layers

def per_iter(unit,hi=9,lo=1):
    def run(n):
        return forthc_costs.compiled(f'variable x\n: w ;\n: main {n} 0 do {unit} loop ;')
    return (run(hi)-run(lo))/(hi-lo)

def layers(src,key):
    return call_layers.run(src)[key]

if __name__=='__main__':
    base=per_iter('')
    call_return=per_iter('w')-base
    execute=per_iter("['] w execute")-base
    nc,ncalls=layers(': w ; : main w ;','call');nr,nrets=layers(': w ; : main w ;','ret')
    mc,mcalls=layers(': main ;','call');mr,mrets=layers(': main ;','ret')
    ec,_=layers(": w ; : main ['] w execute ;",'call_indirect')
    er,_=layers(": w ; : main ['] w execute ;",'ret')
    model_layers={'call':nc-mc,'ret':nr-mr,'call_return':nc-mc+nr-mr,
                  'call_indirect':ec,'execute':ec+er-mr,
                  'note':'слои Seq.layer, добавленные одним вызовом (разность с пустым main); execute = call_indirect + ret'}
    result={'base':base,'call_return':call_return,'execute':execute,
            'model_layers':model_layers,
            'command':'make -C space/vm2 -j1 checked-emulator && python3 -B tools/research/call_ticks.py'}
    target=REPO/'docs/research/call-ticks.json'
    target.write_text(json.dumps(result,indent=1,ensure_ascii=False)+'\n')
    print(json.dumps(result,indent=1,ensure_ascii=False))
