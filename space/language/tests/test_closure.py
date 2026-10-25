"""The closure check agrees with the graph of docs/research/definition-graph.json:
the names outside the definition of the language are primitives of the compiler (no definer among them);
the words of the generators (14.3-14.5, src/primitives.fth) are defined; after 14.5 only
DECIMAL and KERNEL-LAYOUT are external."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_closure

names, _ = check_closure.external_names()
assert names and all(uses > 0 for uses in names.values())
assert not {':', ';', 'variable', 'constant', 'create'} & set(names), 'a definer is not a primitive name'
assert set(names) <= {'decimal', 'kernel-layout'} and 'decimal' in names, sorted(names)
generated = {name for name, _, _ in check_closure.generators()}
assert len(generated) == 59 and {'+', '*', '/mod', 'cell+', '0=', 'dup', '@', '!', 'i', 'j', 'roll', 'spacec!', 'key',
                               'if', 'then', '?do', 'loop', 'leave', 'exit', 'recurse', "[']", 'catch', 'throw'} <= generated, sorted(generated)
assert not generated & set(names), sorted(generated & set(names))
print(f'PASS closure: {len(names)} external names, most used {max(names, key=names.get)!r}')
