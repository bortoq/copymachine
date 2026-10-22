"""Топ-10 слов по числу зависимых (граф 13.1) и числу мест вызова.
Места вызова = сумма count по прямым рёбрам к слову; зависимые = различные
источники рёбер. Читает docs/research/definition-graph.json."""
import json,collections
from pathlib import Path
d=json.loads((Path(__file__).resolve().parents[2]/'docs/research/definition-graph.json').read_text())
dep=d['dependents']
sites=collections.Counter();srcs=collections.defaultdict(set);ind=collections.Counter()
for e in d['edges']:
    if e['kind']=='direct':sites[e['to']]+=e['count'];srcs[e['to']].add(e['from'])
    else:ind[e['to']]+=e['count']
rows=sorted(dep,key=lambda w:(-dep[w]['direct'],-dep[w]['transitive_direct_edges'],w))[:10]
print('| № | Слово | Прямых зависимых | Транзитивных (прямые рёбра) | Мест вызова (прямых) | Косвенных ссылок | различных источников в рёбрах |')
print('|---|---|---:|---:|---:|---:|---:|')
for i,w in enumerate(rows,1):
    print(f"| {i} | `{w}` | {dep[w]['direct']} | {dep[w]['transitive_direct_edges']} | {sites[w]} | {ind[w]} | {len(srcs[w])} |")
print('всего слов в dependents',len(dep),'; рёбер прямых',sum(1 for e in d['edges'] if e['kind']=='direct'),'; сумма мест',sum(sites.values()))
