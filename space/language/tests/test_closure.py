"""The closure check agrees with the graph of docs/research/definition-graph.json:
the names outside the definition of the language are primitives of the compiler (no definer among them)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_closure

names, _ = check_closure.external_names()
assert names and all(uses > 0 for uses in names.values())
assert not {':', ';', 'variable', 'constant', 'create'} & set(names), 'a definer is not a primitive name'
for must in ('@', '!', '+', 'if', 'then', 'dup'):
    assert must in names, must
print(f'PASS closure: {len(names)} external names, most used {max(names, key=names.get)!r}')
