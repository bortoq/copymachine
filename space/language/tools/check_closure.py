#!/usr/bin/env python3
"""Closure of the definition of the language (14.0 check-closure).

Builds the graph of definitions of space/language/src (the model of
tools/research/defgraph.py, order of compilation as in the kernel) and prints
`external N`: the number of names used in the definition but not defined in it,
then the list of the names (with the number of uses). Exit code 0 if N <= MAX_EXTERNAL.

Generators (14.3, src/primitives.fth) are defined words: a registration
`s" NAME" ['] WORD USES fc-generator` defines the word NAME of the language by the
generator WORD (the name in the Forth dictionary differs), so the graph gets a node
NAME of kind `generator` with an edge to WORD (space/language/doc/generators.md).
A name with a quote (S", 14.6) is registered as `[char] C1 [char] C2 fc-name2 ['] WORD USES
fc-generator`.

Literals, digits, numbers (14.7): a registration `s" D" V fc-literal-name` defines the word D
of the language, the name of the literal V (a digit, node of kind `literal`). A number of the
definition (a token -?[0-9]+, which tools/research/defgraph.py skips) is a word built by the
word `literal` from digits: it uses each of its digits and, unless it is a digit itself,
`literal` (the generator of the words not found in the dictionary). These uses count as
external if the names are not defined (space/language/doc/literals.md).

Usage: check_closure.py [--max-external N]   (default: the environment MAX_EXTERNAL, else 0)
"""
import argparse, collections, os, re, sys

import paths

sys.path.insert(0, str(paths.WORKSPACE / 'tools/research'))
import defgraph  # noqa: E402


GENERATOR = re.compile(r'(?i)s" (\S+)" \[\'\] (\S+) \S+ fc-generator(?!\S)')
LITERAL = re.compile(r'(?i)s" (\S+)" (\S+) fc-literal-name(?!\S)')
NAME2 = re.compile(r'(?i)\[char\] (\S) \[char\] (\S) fc-name2 \[\'\] (\S+) \S+ fc-generator(?!\S)')


def generators():
    """Registrations of src/primitives.fth: [(language name, generator word, line)]."""
    found = []
    for line, text in enumerate((paths.SRC / 'primitives.fth').read_text().split('\n'), 1):
        code = text.split('\\ ')[0]
        found += [(name.lower(), word.lower(), line) for name, word in GENERATOR.findall(code)]
        found += [((c1 + c2).lower(), word.lower(), line) for c1, c2, word in NAME2.findall(code)]
    return found


def literal_names():
    """Names of literals of src/primitives.fth (the digits): [(name, value, line)]."""
    found = []
    for line, text in enumerate((paths.SRC / 'primitives.fth').read_text().split('\n'), 1):
        code = text.split('\\ ')[0]
        found += [(name.lower(), value, line) for name, value in LITERAL.findall(code)]
    return found


def number_uses(order):
    """The words that the numbers of the definition use: {name: uses}."""
    uses = collections.Counter()
    for path in order:
        for token, _, _ in defgraph.tokenize(path):
            if defgraph.is_number(token):
                uses.update(token.lstrip('-'))
                if len(token) > 1:
                    uses['literal'] += 1
    return uses


def external_names():
    """Names used in the definition and not defined in it: {name: uses}."""
    defgraph.ROOT = str(paths.WORKSPACE)
    order = ['space/language/src/' + name for name in paths.KERNEL_FILES]
    defgraph.VECTOR_NAMES.clear()
    for path in order:
        tokens = defgraph.tokenize(path)
        for i, token in enumerate(tokens):
            if token[0] == 'execute':
                vector = defgraph.find_exec_vector(tokens, i)
                if vector:
                    defgraph.VECTOR_NAMES.add(vector)
    graph = defgraph.Graph()
    for path in order:
        defgraph.process(graph, path, 'K')
    for name, word, line in generators():       # the word of the language -> its generator
        node = graph.new_node(name, 'generator', 'space/language/src/primitives.fth', line, 'K')
        graph.add_edge(node, graph.lookup(word, 'K'), 'direct', line, sub='generator')
    for name, value, line in literal_names():   # a digit: the name of a literal
        graph.new_node(name, 'literal', 'space/language/src/primitives.fth', line, 'K')
    defined = {node['name'] for node in graph.nodes if node['kind'] != 'init'}
    externals = collections.Counter(graph.externals)
    externals.update(number_uses(order))
    return {name: uses for name, uses in externals.items() if name not in defined}, len(graph.nodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-external', type=int, default=int(os.environ.get('MAX_EXTERNAL') or 0))
    args = parser.parse_args()
    names, nodes = external_names()
    ordered = sorted(names.items(), key=lambda item: (-item[1], item[0]))
    print(f'definitions {nodes - 1}')
    print(f'external {len(names)}')
    print(' '.join(f'{name}:{uses}' for name, uses in ordered))
    if len(names) > args.max_external:
        print(f'FAIL external {len(names)} > MAX_EXTERNAL {args.max_external}', file=sys.stderr)
        return 1
    print(f'PASS external {len(names)} <= MAX_EXTERNAL {args.max_external}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
