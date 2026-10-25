#!/usr/bin/env python3
"""Closure of the definition of the language (14.0 check-closure).

Builds the graph of definitions of space/language/src (the model of
tools/research/defgraph.py, order of compilation as in the kernel) and prints
`external N`: the number of names used in the definition but not defined in it,
then the list of the names (with the number of uses). Exit code 0 if N <= MAX_EXTERNAL.

Usage: check_closure.py [--max-external N]   (default: the environment MAX_EXTERNAL, else 0)
"""
import argparse, os, sys

import paths

sys.path.insert(0, str(paths.WORKSPACE / 'tools/research'))
import defgraph  # noqa: E402


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
    defined = {node['name'] for node in graph.nodes if node['kind'] != 'init'}
    return {name: uses for name, uses in graph.externals.items() if name not in defined}, len(graph.nodes)


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
