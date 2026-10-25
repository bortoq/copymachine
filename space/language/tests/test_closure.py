"""The closure check agrees with the graph of docs/research/definition-graph.json:
the words of the generators (14.3-14.6, src/primitives.fth) are defined, the defining words
among them; after 14.6 no name is external, and the compiler has no branch by the name of a
word (FC-IS? only defined in forthc.fth)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_closure
import paths

names, nodes = check_closure.external_names()
assert not names, sorted(names)
generated = {name for name, _, _ in check_closure.generators()}
assert len(generated) == 70 and {'+', '*', '/mod', 'cell+', '0=', 'dup', '@', '!', 'i', 'j', 'roll', 'spacec!', 'key',
                               'if', 'then', '?do', 'loop', 'leave', 'exit', 'recurse', "[']", 'catch', 'throw',
                               ':', ';', 'variable', 'constant', 'create', 'allot', '(', '[char]', 's"',
                               'decimal', 'kernel-layout'} <= generated, sorted(generated)
compiler = (paths.SRC / 'forthc.fth').read_text()
assert compiler.count('fc-is?') <= 2 and 'fc-primitive' not in compiler, compiler.count('fc-is?')
print(f'PASS closure: 0 external names, {len(generated)} words of generators, {nodes - 1} definitions')
