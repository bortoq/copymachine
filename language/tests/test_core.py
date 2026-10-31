"""doc/core.md (14.8) is the core of the language by the graph of the definition.

Checked: the file equals what tools/check_closure.py makes from the graph (a stale file fails);
and, independently of the graph code, by the sources: every row names a word that the source defines
at the stated file:line in the stated kind, the rows follow the order of definition, the foundation
(the words of copying that generate a row and a layer) is marked, every word of the core has a use,
a word listed as unused has none in the text, and the definition is closed (no external names).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_closure
import paths

defgraph = check_closure.defgraph
text = check_closure.render_core()
document = (paths.ROOT / 'doc/core.md').read_text()
assert document == text, 'doc/core.md differs from the graph (run make check-closure)'
print('PASS core.md equals the core made from the graph')

names, nodes = check_closure.external_names()
assert not names, sorted(names)

KIND = {v: k for k, v in check_closure.KINDS.items()}
ROW = re.compile(r'^\| (\d+) \| `(.*?)` \| (.*?) \| (src/\S+\.fth):(\d+) \| (\d+) \| (.*?) \|$', re.M)
rows = ROW.findall(document.split('## Слова ядра')[1].split('## Числа определения')[0])
total = int(re.search(r'Слов в ядре: (\d+)', document).group(1))
assert rows and len(rows) == total, (len(rows), total)
assert [int(row[0]) for row in rows] == list(range(1, total + 1))
order = {name: i for i, name in enumerate(paths.KERNEL_FILES)}

# 1. every row is a definition at its file:line, in the order of definition
position = (-1, 0)
definers = {'определение `:`': ': ', 'переменная': 'variable ', 'данные `create`': 'create ', 'константа': 'constant '}
for _number, name, kind, file, line, uses, note in rows:
    name = name.replace('\\|', '|')
    where = (order[file.split('/')[1]], int(line))
    assert where >= position, ('order of definition', name, file, line)
    position = where
    source = (paths.ROOT / file).read_text().split('\n')[int(line) - 1].lower().split('\\ ')[0]
    if kind in definers or kind == 'основание':
        assert (definers.get(kind, ': ') + name) in source, (name, kind, file, line, source)
    elif kind == 'генератор':
        quoted = 's" ' + name + '"'
        assert quoted in source or (name == 's"' and '[char] s [char] " fc-name2' in source), (name, source)
        assert 'слово компилятора `gen' in note, note
    elif kind == 'цифра (литерал)':
        assert ('s" ' + name + '" ' + name + ' fc-literal-name') in source, (name, source)
    else:
        raise AssertionError(kind)
    assert int(uses) >= 1, ('a word of the core without a use', name)
print(f'PASS {total} words of the core: each is defined at its file:line, in the order of definition, and used')

# 2. the kinds in the header add up
header = re.search(r'Слов в ядре: \d+\*\* \((.*?)\)\.', document).group(1)
counts = {KIND[kind.strip()]: int(count) for kind, count in (part.rsplit(' — ', 1) for part in header.split(', '))}
assert sum(counts.values()) == total and counts['foundation'] == len(check_closure.FOUNDATION), counts
print('PASS kinds:', header)

# 3. the foundation: the words of copying that generate a row and a layer, "the definition of an instruction is it itself"
by_name = {row[1]: row for row in rows if row[2] == 'основание'}
assert set(by_name) == set(check_closure.FOUNDATION) >= {'lay-copy', 'lay-row', 'lay-layer'}, sorted(by_name)
for _name, row in by_name.items():
    assert row[3].endswith('backend.fth') and 'определение инструкции — она сама' in row[6], row
section = document.split('## Основание')[1].split('## Слова ядра')[0]
assert 'Определение инструкции — она сама' in section and all(f'`{name}`' in section for name in by_name)
print('PASS foundation:', ' '.join(by_name))

# 4. unused words: every use of such a word in the text is inside the definition of another unused word
#    (or none), so that no code of the core reaches it; found by the tokens, without the graph
unused_part = document.split('## Определены, но не использованы')[1].split('## Слова, которые при буте')[0]
unused = re.findall(r'^\| `(.*?)`(?: \(вариант \d+\))? \| .*? \| src/\S+\.fth:\d+ \|$', unused_part, re.M)
assert len(unused) == int(re.search(r'Слов: (\d+)', unused_part).group(1))
dead = set(unused)
for name in paths.KERNEL_FILES:
    current = None
    tokens = defgraph.tokenize('language/src/' + name)
    for i, (token, line, _raw) in enumerate(tokens):
        if token == ':' :
            current = tokens[i + 1][0]
        elif token == ';':
            current = None
        elif token in dead and not (i and tokens[i - 1][0] in (':', 'variable', 'create', 'constant')):
            assert current in dead, ('a word listed as unused is used', token, name, line, current)
print(f'PASS {len(unused)} words are defined and not used: no code of the core refers to them')

# 5. the compiler has no word that it handles by its name outside the dictionary: \ is a generator (14.8)
assert any(row[1] == '\\' and row[2] == 'генератор' for row in rows), 'the word \\ is a generator'
assert 'fc-word-raw' not in (paths.SRC / 'forthc.fth').read_text()
print('PASS the comment word \\ is a generator of the language; the definition is closed (external 0)')
