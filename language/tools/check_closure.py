#!/usr/bin/env python3
"""Closure of the definition of the language (14.0 check-closure).

Builds the graph of definitions of language/src (the model of
language/tests/reference/defgraph.py, order of compilation as in the kernel) and prints
`external N`: the number of names used in the definition but not defined in it,
then the list of the names (with the number of uses). Exit code 0 if N <= MAX_EXTERNAL.

Generators (14.3, src/primitives.fth) are defined words: a registration
`s" NAME" ['] WORD USES fc-generator` defines the word NAME of the language by the
generator WORD (the name in the Forth dictionary differs), so the graph gets a node
NAME of kind `generator` with an edge to WORD (language/doc/generators.md).
A name with a quote (S", 14.6) is registered as `[char] C1 [char] C2 fc-name2 ['] WORD USES
fc-generator`.

Literals, digits, numbers (14.7): a registration `s" D" V fc-literal-name` defines the word D
of the language, the name of the literal V (a digit, node of kind `literal`). A number of the
definition (a token -?[0-9]+, which language/tests/reference/defgraph.py skips) is a word built by the
word `literal` from digits: it uses each of its digits and, unless it is a digit itself,
`literal` (the generator of the words not found in the dictionary). These uses count as
external if the names are not defined (language/doc/literals.md).

The word `\\` (a comment to the end of the line, 14.8) is a generator too: the compiler has no word
that it handles by its name (the comment is skipped by GEN-BACKSLASH).

Core of the language (14.8): the words used in the definition by the graph (reachable from the top-level
code of the files, from the entries of the boot and from the last MAIN, through the direct and indirect
references and the references by name, BY_NAME), in the order of definition, with file:line and kind,
are written to doc/core.md (language/doc/core.md). The foundation is the words of copying that
generate a row and a layer (FOUNDATION): the definition of an instruction is the instruction itself.

Usage: check_closure.py [--max-external N] [--core PATH | --no-core]
       (default MAX_EXTERNAL from the environment, else 0; PATH: doc/core.md)
"""
import argparse
import collections
import os
import pathlib
import re
import sys

import paths

sys.path.insert(0, str(paths.REFERENCE))
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


# The words that the syntax of the text consumes (the graph of defgraph.py does not see them as references).
SYNTAX = {'\\', '(', 's"', '[char]', ':', ';', 'variable', 'create', 'constant', 'allot', 'recurse', "[']"}


def syntax_uses(order):
    """Uses of the words of SYNTAX in the definition: {name: uses}; comments and strings as in defgraph.tokenize."""
    uses = collections.Counter()
    for path in order:
        in_paren = False
        for text in (paths.WORKSPACE / path).read_text().split('\n'):
            words = text.split()
            i = 0
            while i < len(words):
                word = words[i].lower()
                i += 1
                if in_paren:
                    in_paren = word != ')'
                    continue
                if word in SYNTAX:
                    uses[word] += 1
                if word == '\\':
                    break
                if word == '(':
                    in_paren = True
                elif word == 's"':
                    rest = ' '.join(words[i:])
                    words = rest[rest.find('"') + 1:].split() if '"' in rest else []
                    i = 0
                elif word == '[char]':
                    i += 1
    return uses


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


def build_graph():
    """The graph of the definition: (graph, order of files); the generators and the digits are nodes."""
    defgraph.ROOT = str(paths.WORKSPACE)
    order = ['language/src/' + name for name in paths.KERNEL_FILES]
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
        node = graph.new_node(name, 'generator', 'language/src/primitives.fth', line, 'K')
        graph.add_edge(node, graph.lookup(word, 'K'), 'direct', line, sub='generator')
    for name, _value, line in literal_names():   # a digit: the name of a literal
        graph.new_node(name, 'literal', 'language/src/primitives.fth', line, 'K')
    for name, uses in graph.unresolved.items():  # the uses of the generators and the digits (resolved here)
        if name in graph.k and name not in SYNTAX:
            for owner, _, line in uses:
                graph.add_edge(owner, graph.k[name], 'direct', line)
    return graph, order


def external_names():
    """Names used in the definition and not defined in it: {name: uses}."""
    graph, order = build_graph()
    defined = {node['name'] for node in graph.nodes if node['kind'] != 'init'}
    externals = collections.Counter(graph.externals)
    externals.update(number_uses(order))
    return {name: uses for name, uses in externals.items() if name not in defined}, len(graph.nodes)


# --- the core of the language (14.8) -----------------------------------------------------------------

# The foundation: the words of copying that generate a row (a copy: the destination and the source
# interval) and a layer (a cell of rows); their definition is not reduced to other words, the definition of an
# instruction is the instruction itself. name -> what it generates (all are defined by `:` in backend.fth).
FOUNDATION = collections.OrderedDict([
    ('cc-copy', 'строка: копирование n бит из источника в приёмник'),
    ('cc-link-row', 'строка: копирование ссылки на следующий слой'),
    ('cc-row', 'строка: добавляет строку в слой'),
    ('cc-new-record', 'слой: новый слой в ячейке'),
    ('cc-lone', 'слой: отдельный слой в новой ячейке'),
    ('cc-layer', 'слой: следующий слой последовательности'),
])

# References by name: the compiler finds the word by the string in its dictionary (the graph sees no
# tick): (word, the word found, the text of the reference in the file of the word).
BY_NAME = [
    ('fc-not-found', 'literal', 'forthc.fth', 's" literal" fc-lookup'),
    ('fc-compile', 'main', 'forthc.fth', 's" main" fc-tok'),
]

# The entries of the boot: the words that the host driver (tools/boot.py) executes by name.
BOOT_ENTRIES = ['fc|', 'fc-go', 'fc-text-size', 'fc-max-consts', 'fc-max-words', 'fc-names-size', 'fc-nbuckets']

KINDS = {'colon': 'определение `:`', 'variable': 'переменная', 'constant': 'константа', 'value': 'константа',
         'create': 'данные `create`', 'generator': 'генератор', 'literal': 'цифра (литерал)',
         'foundation': 'основание'}


def core_nodes():
    """The core: (graph, rows). A row: dict(node, kind, uses, file, line, why). In the order of definition."""
    graph, order = build_graph()
    src = paths.SRC
    by_id = {node['id']: node for node in graph.nodes}
    for name in FOUNDATION:
        node = by_id.get(name)
        assert node and node['kind'] == 'colon' and node['file'].endswith('backend.fth'), ('foundation', name)
    last = {}                                    # the newest node of the name (what a lookup by name finds)
    for node in graph.nodes:
        last[node['name']] = node['id']
    edges = collections.defaultdict(set)
    uses = collections.Counter()
    for edge in graph.edges.values():
        edges[edge['from']].add(edge['to'])
        if edge['from'] != edge['to']:
            uses[edge['to']] += edge['count']
    for word, target, name, text in BY_NAME:
        assert text in (src / name).read_text(), ('reference by name', text)
        edges[last[word]].add(last[target])
        uses[last[target]] += 1
    boot = (paths.ROOT / 'tools/boot.py').read_text()
    entries = []
    for name in BOOT_ENTRIES:
        assert name in boot, ('entry of the boot', name)
        entries.append(last[name])
        uses[last[name]] += 1
    numbers = number_uses(order)
    digits = [by_id[d]['id'] for d in numbers if d in by_id]        # numbers: digits and `literal`
    syntax = syntax_uses(order)
    for name, count in syntax.items():
        uses[last[name]] += count
    roots = ([node['id'] for node in graph.nodes if node['kind'] == 'init'] + [last['main']] + entries + digits
             + [last[name] for name in syntax])
    seen, stack = set(), list(roots)
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(edges[node])
    files = {'language/src/' + name: i for i, name in enumerate(paths.KERNEL_FILES)}
    rows, unused = [], []
    for node in graph.nodes:
        if node['kind'] == 'init':
            continue
        kind = 'foundation' if node['id'] in FOUNDATION else node['kind']
        row = dict(node=node, kind=kind, uses=uses[node['id']] + (numbers[node['name']] if node['id'] in digits else 0))
        (rows if node['id'] in seen else unused).append(row)
    key = lambda row: (files[row['node']['file']], row['node']['line'])
    rows.sort(key=key)
    unused.sort(key=key)
    return graph, rows, unused, numbers, entries


def host_native():
    """Names that the host pForth executes by its own definition at the boot (14.8): the words that the
    libraries (backend, compute, forthc, primitives) use and that are defined in the definition by a
    generator or in the prelude (the text of which the host does not load)."""
    graph, order = build_graph()
    library = {'language/src/' + name for name in paths.LIBRARY_FILES}
    by_id = {node['id']: node for node in graph.nodes}
    names = collections.Counter()
    for edge in graph.edges.values():
        source, target = by_id[edge['from']], by_id[edge['to']]
        if source['file'] in library and edge['kind'] == 'direct' and target['file'] not in library - {
                'language/src/primitives.fth'}:
            if target['kind'] in ('generator', 'literal') or target['file'].endswith('prelude.fth'):
                names[target['name']] += edge['count']
    return names


REDEFINED = set()      # names defined more than once (filled by render_core)


def cell(text):
    return '`' + text.replace('|', '\\|') + '`'


def render_core():
    """The text of doc/core.md."""
    graph, rows, unused, numbers, entries = core_nodes()
    kinds = collections.Counter(row['kind'] for row in rows)
    REDEFINED.update(node['name'] for node in graph.nodes if node['version'] > 1)
    where = lambda node: node['file'].replace('language/', '') + ':' + str(node['line'])
    out = ['# Ядро языка (14.8)', '',
           'Файл порождается `make -C language check-closure` (`tools/check_closure.py`) и проверяется '
           '`tests/test_core.py`; руками не правится.', '',
           'Ядро языка — слова, использованные в определении языка (`src/*.fth`), по графу определения '
           '(`language/tests/reference/defgraph.py` с генераторами, цифрами и ссылками по имени): слово использовано, '
           'если до него доходят ссылки из кода верхнего уровня файлов, из входов бута и из последнего '
           '`main`. Определение замкнуто: имён, использованных и не определённых в нём, нет '
           '(`external 0`). Слова — в порядке определения.', '',
           f'**Слов в ядре: {len(rows)}** (' + ', '.join(f'{KINDS[kind]} — {count}' for kind, count in
                                                         sorted(kinds.items(), key=lambda item: -item[1])) + ').', '',
           '## Основание', '',
           'Основание — слова-копирования: генераторы строки (копия — приёмник и источник) и слоя '
           '(ячейка строк) из `src/backend.fth`. Определение инструкции — она сама: тело этих слов '
           'не сводится к другим словам языка, а строка и слой — сами инструкции индексного пространства.', '',
           '| Слово | Что порождает | Файл:строка |', '|---|---|---|']
    nodes = {row['node']['id']: row['node'] for row in rows}
    out += [f'| {cell(name)} | {why} | {where(nodes[name])} |' for name, why in FOUNDATION.items()]
    out += ['', '## Слова ядра', '',
            'Вид: генератор (слово словаря, исполняемое при компиляции, `doc/generators.md`; в пояснении слово '
            'компилятора), определение `:`, переменная, константа, данные `create`, цифра (литерал, '
            '`doc/literals.md`), основание. «Исп.» — число ссылок из других слов (цифры — и из чисел '
            'определения). Повторное определение имени — «вариант N» (старое имя остаётся у прежних ссылок).', '',
            '| № | Слово | Вид | Файл:строка | Исп. | Пояснение |', '|---|---|---|---|---|---|']
    for number, row in enumerate(rows, 1):
        node = row['node']
        note = ''
        if row['kind'] == 'foundation':
            note = 'основание: ' + FOUNDATION[node['id']] + '; определение инструкции — она сама'
        elif row['kind'] == 'generator':
            edge = next(e for e in graph.edges.values() if e['from'] == node['id'])
            note = 'слово компилятора ' + cell(by_name_of(graph, edge['to']))
        elif row['kind'] == 'literal':
            note = f'значение {node["name"]}'
        if node['version'] > 1:
            note = (f'вариант {node["version"]}; ' + note).rstrip('; ')
        if node['id'] in entries:
            note = (note + '; ' if note else '') + 'вход бута (хост)'
        out.append(f'| {number} | {cell(node["name"])} | {KINDS[row["kind"]]} | {where(node)} | {row["uses"]} | {note} |')
    out += ['', '## Числа определения', '',
            'Число — слово: его строит генератор `literal` из цифр (`doc/literals.md`); в ядро входят '
            'сами цифры и `literal`. Различных чисел в определении: ' + str(len(count_numbers())) + '.', '',
            '## Определены, но не использованы', '',
            f'Слов: {len(unused)}. Они есть в тексте определения (замкнутость от этого не нарушается), '
            'но по графу до них не доходит ни одна ссылка.', '',
            '| Слово | Вид | Файл:строка |', '|---|---|---|']
    out += [f'| {cell(row["node"]["name"])}{variant(row["node"])} | {KINDS[row["kind"]]} | {where(row["node"])} |'
            for row in unused]
    native = host_native()
    out += ['', '## Слова, которые при буте исполняет хост', '',
            'Первый раз определение исполняет хостовой 32-битный pForth (`doc/boot.md`): библиотеки '
            '`backend`, `compute`, `forthc`, `primitives` он загружает как свой исходник, а '
            'слова, которых в них нет, берёт из своего словаря. Таких имён в библиотеках '
            f'{len(native)}; все они определены в определении языка (генератором в `primitives.fth` '
            'или словом `prelude.fth`, которое хост при буте не загружает), то есть замкнутость '
            'честная: ядро L0 получает их определения из текста, а не от хоста. Числа и цифры библиотек '
            'хост разбирает сам, в определении они — слова (`literal` и цифры). Имена: '
            + ' '.join(cell(name) for name in sorted(native)) + '.', '',
            'Слова, которые хост исполняет иначе, чем ядро: `fc|` (хост кладёт в буфер строку своего входа; '
            'это вход бута — ядро не вызывает `fc|`, его `source` — заглушка из `prelude.fth`, текст ядро '
            'читает каналом `key`), `source` и `>in` — слова только этого пути.']
    return '\n'.join(out) + '\n'


def variant(node):
    return f' (вариант {node["version"]})' if node['version'] > 1 or node['name'] in REDEFINED else ''


def by_name_of(graph, node_id):
    return next(node['name'] for node in graph.nodes if node['id'] == node_id)


def count_numbers():
    numbers = set()
    for name in paths.KERNEL_FILES:
        for token, _, _ in defgraph.tokenize('language/src/' + name):
            if defgraph.is_number(token):
                numbers.add(token)
    return numbers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-external', type=int, default=int(os.environ.get('MAX_EXTERNAL') or 0))
    parser.add_argument('--core', type=pathlib.Path, default=paths.ROOT / 'doc/core.md')
    parser.add_argument('--no-core', action='store_true')
    args = parser.parse_args()
    names, nodes = external_names()
    ordered = sorted(names.items(), key=lambda item: (-item[1], item[0]))
    print(f'definitions {nodes - 1}')
    print(f'external {len(names)}')
    print(' '.join(f'{name}:{uses}' for name, uses in ordered))
    if not args.no_core:
        text = render_core()
        args.core.write_text(text)
        print(f'core {text.split("Слов в ядре: ")[1].split("**")[0]} words -> {args.core}')
    if len(names) > args.max_external:
        print(f'FAIL external {len(names)} > MAX_EXTERNAL {args.max_external}', file=sys.stderr)
        return 1
    print(f'PASS external {len(names)} <= MAX_EXTERNAL {args.max_external}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
