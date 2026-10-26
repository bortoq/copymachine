"""The closure check agrees with the graph of docs/research/definition-graph.json:
the words of the generators (14.3-14.6, src/primitives.fth) are defined, the defining words
among them; after 14.6 no name is external, and the compiler has no branch by the name of a
word (FC-IS? only defined in forthc.fth). 14.7: the digits 0..9 are words (names of literals),
the numbers of the definition use them and the word `literal`, the compiler parses no number."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_closure
import paths

names, nodes = check_closure.external_names()
assert not names, sorted(names)
generated = {name for name, _, _ in check_closure.generators()}
assert len(generated) == 74 and {'+', '*', '/mod', 'cell+', '0=', 'dup', '@', '!', 'i', 'j', 'roll', 'spacec!', 'key',
                               'if', 'then', '?do', 'loop', 'leave', 'exit', 'recurse', "[']", 'catch', 'throw',
                               ':', ';', 'variable', 'constant', 'create', 'allot', '(', '[char]', 's"',
                               'decimal', 'kernel-layout', 'literal', '\\'} <= generated, sorted(generated)
# every registration of the generators and of the digits is seen by the graph (no word is registered unseen)
tokens = [t for t, _, _ in check_closure.defgraph.tokenize('space/language/src/primitives.fth')]
assert tokens.count('fc-generator') == len(check_closure.generators()) == 74, tokens.count('fc-generator')
assert tokens.count('fc-literal-name') == 10, tokens.count('fc-literal-name')
digits = check_closure.literal_names()
assert [(name, value) for name, value, _ in digits] == [(str(d), str(d)) for d in range(10)], digits
numbers = check_closure.number_uses(['space/language/src/' + name for name in paths.KERNEL_FILES])
assert set(numbers) == {str(d) for d in range(10)} | {'literal'}, numbers
compiler = (paths.SRC / 'forthc.fth').read_text()
assert compiler.count('fc-is?') <= 2 and 'fc-primitive' not in compiler, compiler.count('fc-is?')
# 14.8: no word is handled by its name outside the dictionary: the comment word \ is a generator
assert 'fc-word-raw' not in compiler and "[char] \\ =" not in compiler, 'the comment word is handled by name'
syntax = check_closure.syntax_uses(['space/language/src/' + name for name in paths.KERNEL_FILES])
assert syntax['\\'] > 100 and syntax['('] > 100 and syntax['s"'] > 0, syntax
assert 'fc-number' not in compiler and 'fc-number' not in (paths.SRC / 'primitives.fth').read_text()
print(f'PASS closure: 0 external names, {len(generated)} words of generators, {len(digits)} digits'
      f' ({numbers["literal"]} numbers of the definition go through literal), {nodes - 1} definitions')
