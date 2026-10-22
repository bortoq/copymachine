"""Топ-10 слов по числу зависимых (граф 13.1) и цена связывания (13.2.3).
Порядок как в `## Число зависимых` definition-graph.md: транзитивно по всем
рёбрам (убывание), затем имя. Столбец прямых зависимых сохранён.
Места вызова = сумма count по прямым рёбрам к слову. Слов в теле зависимого =
сумма count по его исходящим рёбрам + числовые литералы тела (счёт по
токенам исходников через defgraph.tokenize). Цена перекомпиляции слова =
тактов на слово исходника (9 мс * 3,8 млн тактов/с, forthc.md) * слов в теле,
сумма по всем транзитивным зависимым. Читает docs/research/definition-graph.json."""
import json,collections,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import defgraph
TICKS_PER_WORD=34200
d=json.loads((Path(__file__).resolve().parents[2]/'docs/research/definition-graph.json').read_text())
dep=d['dependents']
sites=collections.Counter();ind=collections.Counter();body=collections.Counter()
radj=collections.defaultdict(set)
for e in d['edges']:
    body[e['from']]+=e['count']
    radj[e['to']].add(e['from'])
    if e['kind']=='direct':sites[e['to']]+=e['count']
    else:ind[e['to']]+=e['count']
# числовые литералы в телах `:`-слов; имена узлов как в defgraph.Graph.new_node
ver=collections.Counter();lits=collections.Counter()
for aux,paths in ((False,defgraph.K_ORDER),(True,defgraph.AUX_ORDER)):
    for p in paths:
        cur=None;toks=defgraph.tokenize(p);i=0
        while i<len(toks):
            t=toks[i][0]
            if cur is None:
                if t==':' and i+1<len(toks):
                    nm=toks[i+1][0];ver[(aux,nm)]+=1;v=ver[(aux,nm)]
                    cur=('aux:' if aux else '')+(nm if v==1 else '%s~%d'%(nm,v));i+=1
                elif t in('variable','constant','create','value') and i+1<len(toks):
                    ver[(aux,toks[i+1][0])]+=1;i+=1
            elif t==';':cur=None
            elif defgraph.is_number(t):lits[cur]+=1
            i+=1
def dependents(w):
    seen=set();st=[w]
    while st:
        for u in radj[st.pop()]:
            if u in dep and u not in seen and u!=w:seen.add(u);st.append(u)
    return seen
rows=sorted(dep,key=lambda w:(-dep[w]['transitive_all_edges'],w))[:10]
print('| № | Слово | Прямых зависимых | Транзитивно (все рёбра) | Транзитивно (прямые рёбра) | Мест вызова (прямых) | Косвенных ссылок | Слов в телах всех зависимых | Перекомпиляция всех зависимых (тактов) |')
print('|---|---|---:|---:|---:|---:|---:|---:|---:|')
tw=tt=0
for i,w in enumerate(rows,1):
    ds=dependents(w);assert len(ds)==dep[w]['transitive_all_edges'],(w,len(ds))
    words=sum(body[u]+lits[u] for u in ds);tw+=words;tt+=words*TICKS_PER_WORD
    print(f"| {i} | `{w}` | {dep[w]['direct']} | {dep[w]['transitive_all_edges']} | {dep[w]['transitive_direct_edges']} | {sites[w]} | {ind[w]} | {words} | {words*TICKS_PER_WORD} |")
print('всего слов в dependents',len(dep),'; рёбер прямых',sum(1 for e in d['edges'] if e['kind']=='direct'),'; сумма мест',sum(sites.values()),'; слов в телах (топ-10)',tw,'; тактов',tt)
