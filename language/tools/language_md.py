#!/usr/bin/env python3
"""doc/language.md, the definition of the language in Russian (14.9), and the core of the language.

The document has one record per word of the core (tools/check_closure.py core_nodes, the list of
doc/core.md), in the order of definition:

    ### `NAME`                     (a redefinition: ### `NAME` (вариант N))

    Вид: KIND. Синонимы: ...

    Смысл: what the word does, in words (written by hand, never generated).

    код: src/FILE.fth:LINE HASH     (HASH: the first 12 hex digits of SHA-256 of the text of the definition)

    Тип адресации: ... Доказательство: ... Цена: ...

The text of the definition: `: NAME ... ;` for a colon definition, `variable NAME`, the value
on the same line and `constant NAME`, `create NAME` up to its `allot` (the body as the graph of
language/tests/reference/defgraph.py sees it), the registration `s" NAME" ['] WORD USES fc-generator` of a
generator and `s" D" V fc-literal-name` of a digit (src/primitives.fth), exactly as written.

Usage: language_md.py --check     compare the records with the core: the set and the order of the
                                  records, file:line and hash, kind; meaning filled (no TODO)
       language_md.py --update    rewrite only the lines `код:` of the existing records
       language_md.py --skeleton  add the missing records (heading, kind, synonyms, `код:`, the
                                  meaning TODO, which --check rejects); create the file if missing
       language_md.py --prices    rewrite the price of the colon definitions (14.11) from the
                                  records the compiler makes when the host compiles the definition
                                  (tools/word_cost.py; tests/test_word.py checks them)
       [--doc PATH]               default doc/language.md
Exit code of --check: 0 if the document agrees with the core, else 1.
"""
import argparse
import collections
import hashlib
import re
import sys

import check_closure
import paths

DOC = paths.ROOT / 'doc/language.md'
TODO = 'TODO'
WORDS = '## Слова ядра'
ADDRESSING = 'индексное пространство'
FOUNDATION_NOTE = 'определение инструкции — она сама'
HEADING = re.compile(r'^### `(.+)`(?: \(вариант (\d+)\))?$')
KIND_LINE = re.compile(r'^Вид: (.+?)\. Синонимы: (.+)$')
CODE_LINE = re.compile(r'^код: (\S+):(\d+) ([0-9a-f]{12})$')
PROPS_LINE = re.compile(r'^Тип адресации: (.+?)\. Доказательство: (.+?)\. Цена: (.+)$')
FILE_TITLES = {
    'prelude.fth': 'слова стека, сравнения, памяти и кучи',
    'backend.fth': 'копикод: строки, слои, поток',
    'compute.fth': 'вычисления на копированиях: таблицы, сложение, вызовы',
    'forthc.fth': 'компилятор: словарь, канал, литералы, кэш стека, построители',
    'primitives.fth': 'генераторы и цифры',
    'main.fth': 'компилятор как программа',
    'kernel.fth': 'ядро: компилирует и исполняет программу',
}


# --- the texts of the definitions --------------------------------------------------------------------

def lex(text):
    """Tokens of a source as language/tests/reference/defgraph.py tokenize, with offsets: [(token, line, start, end)].
    Comments are removed; `s" ..."` and `[char] c` are one token each."""
    out, in_paren, offset = [], False, 0
    for ln, line in enumerate(text.split('\n'), 1):
        pos, n = 0, len(line)
        while pos < n:
            while pos < n and line[pos] <= ' ':
                pos += 1
            if pos >= n:
                break
            st = pos
            while pos < n and line[pos] > ' ':
                pos += 1
            tok = line[st:pos].lower()
            if in_paren:
                in_paren = tok != ')'
                continue
            if tok == '\\':
                break
            if tok == '(':
                in_paren = True
                continue
            if tok in ('s"', '."'):
                e = line.find('"', pos + 1)
                pos = n if e < 0 else e + 1
                out.append(('"str"', ln, offset + st, offset + pos))
                continue
            if tok == '[char]':
                while pos < n and line[pos] <= ' ':
                    pos += 1
                while pos < n and line[pos] > ' ':
                    pos += 1
                out.append(('[char]', ln, offset + st, offset + pos))
                continue
            out.append((tok, ln, offset + st, offset + pos))
        offset += len(line) + 1
    return out


def definitions(name):
    """The definitions of src/NAME by the walk of defgraph.process: {(line, word, kind): [text]}."""
    text = (paths.SRC / name).read_text()
    toks = lex(text)
    found = collections.defaultdict(list)
    add = lambda word, kind, line, start, end: found[(line, word, kind)].append(text[start:end])
    i, n, cur, boundary = 0, len(toks), None, 0
    while i < n:
        tok, ln, start, end = toks[i]
        if cur is None:
            if tok in (':', 'variable', 'create', 'constant', 'value') and i + 1 < n:
                word, wline, _, wend = toks[i + 1]
                if tok == ':':
                    cur = (word, wline, start)
                    i += 2
                    continue
                if tok in ('constant', 'value'):      # the value: the tokens of the same line before
                    j = i
                    while j > boundary and toks[j - 1][1] == ln:
                        j -= 1
                    add(word, 'constant', wline, toks[j][2], wend)
                    i += 2
                elif tok == 'variable':
                    add(word, 'variable', wline, start, wend)
                    i += 2
                else:                                 # create: up to the first allot, else the line
                    j, last = i + 2, wend
                    while j < n:
                        t2, l2, _, e2 = toks[j]
                        if t2 in check_closure.defgraph.DEFINERS and t2 != 'value':
                            break
                        if l2 != wline and t2 != 'allot':
                            break
                        last = e2
                        j += 1
                        if t2 == 'allot':
                            break
                    add(word, 'create', wline, start, last)
                    i = j
                boundary = i
                continue
            i += 2 if tok in ("'", "[']") else 1
            continue
        if tok == ';':
            add(cur[0], 'colon', cur[1], cur[2], end)
            cur, boundary = None, i + 1
            i += 1
            continue
        i += 2 if tok in ("'", "[']") else 1
    if name == 'primitives.fth':                       # the registrations of generators and digits
        for ln, line in enumerate(text.split('\n'), 1):
            code = line.split('\\ ')[0]
            for match in check_closure.GENERATOR.finditer(code):
                found[(ln, match.group(1).lower(), 'generator')].append(match.group(0))
            for match in check_closure.NAME2.finditer(code):
                found[(ln, (match.group(1) + match.group(2)).lower(), 'generator')].append(match.group(0))
            for match in check_closure.LITERAL.finditer(code):
                found[(ln, match.group(1).lower(), 'literal')].append(match.group(0))
    return found


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


def core():
    """The words of the core in the order of definition: [dict(key, name, version, kind, file, line, hash, synonyms)]."""
    graph, rows, _, _, _ = check_closure.core_nodes()
    words = collections.defaultdict(list)                          # a generator word -> its names
    for name, word, _ in check_closure.generators():
        words[word].append(name)
    word_of = {name: word for name, word, _ in check_closure.generators()}
    texts = {name: definitions(name) for name in paths.KERNEL_FILES}
    out = []
    for row in rows:
        node = row['node']
        file = node['file'].split('/')[-1]
        kind = 'colon' if row['kind'] == 'foundation' else row['kind']
        found = texts[file].get((node['line'], node['name'], kind), [])
        assert len(found) == 1, ('the text of the definition', node['name'], file, node['line'], len(found))
        if row['kind'] == 'generator':
            others = [name for name in words[word_of[node['name']]] if name != node['name']]
            synonyms = ', '.join(f'`{name}`' for name in others) + ' (тот же генератор)' if others else 'нет'
        elif row['kind'] == 'literal':
            synonyms = f'литерал значения {node["name"]}'
        else:
            synonyms = 'нет'
        out.append(dict(key=(node['name'], node['version']), name=node['name'], version=node['version'],
                        kind=row['kind'], file='src/' + file, line=node['line'], hash=digest(found[0]),
                        synonyms=synonyms))
    return out


# --- the document ------------------------------------------------------------------------------------

def heading(word):
    return f'### `{word["name"]}`' + (f' (вариант {word["version"]})' if word['version'] > 1 else '')


def code_line(word):
    return f'код: {word["file"]}:{word["line"]} {word["hash"]}'


def skeleton_record(word):
    price = 'по исполнению'
    if word['kind'] == 'literal':
        price = 'в определении — одна копия 32 бит константы; на верхнем уровне — известное значение, без кода'
    props = f'Тип адресации: {ADDRESSING}. Доказательство: не доказано. Цена: {price}.'
    if word['kind'] == 'foundation':
        props += ' Основание: ' + FOUNDATION_NOTE + '.'
    return [heading(word), '', f'Вид: {check_closure.KINDS[word["kind"]]}. Синонимы: {word["synonyms"]}.', '',
            f'Смысл: {TODO}', '', code_line(word), '', props, '']


def parse(lines):
    """Records of the document: [dict(key, start, end, lines)] (end: the next line starting with #)."""
    records, current, fence = [], None, False
    for i, line in enumerate(lines):
        if line.startswith('```'):          # an example in a fenced block is not a record
            fence = not fence
        if line.startswith('#') and not fence:
            if current:
                current['end'] = i
                current = None
            match = HEADING.match(line)
            if match:
                current = dict(key=(match.group(1), int(match.group(2) or 1)), start=i, end=len(lines))
                records.append(current)
    for record in records:
        record['lines'] = lines[record['start'] + 1:record['end']]
    return records


def show(key):
    return f'`{key[0]}`' + (f' (вариант {key[1]})' if key[1] > 1 else '')


def check(lines):
    """Errors of the document against the core: [text]."""
    words = core()
    expected = {word['key']: word for word in words}
    names = {word['name'] for word in words}
    records = parse(lines)
    errors = []
    keys = [record['key'] for record in records]
    for key, count in collections.Counter(keys).items():
        if count > 1:
            errors.append(f'{show(key)}: записей {count}')
    for key in keys:
        if key not in expected:
            errors.append(f'{show(key)}: лишняя запись (слова нет в ядре языка)')
    for word in words:
        if word['key'] not in keys:
            errors.append(f'{show(word["key"])}: нет записи ({word["file"]}:{word["line"]})')
    present = [key for key in keys if key in expected]
    order = [word['key'] for word in words if word['key'] in set(present)]
    if not errors and present != order:
        wrong = next(a for a, b in zip(present, order, strict=False) if a != b)
        errors.append(f'{show(wrong)}: записи не в порядке определения')
    for record in records:
        word = expected.get(record['key'])
        if not word:
            continue
        body, where = record['lines'], show(record['key'])
        codes = [line for line in body if line.startswith('код:')]
        if codes != [code_line(word)]:
            errors.append(f'{where}: строка кода {codes} не равна «{code_line(word)}» (--update)')
        kinds = [KIND_LINE.match(line) for line in body if line.startswith('Вид:')]
        if len(kinds) != 1 or not kinds[0] or kinds[0].group(1) != check_closure.KINDS[word['kind']]:
            errors.append(f'{where}: строка «Вид: {check_closure.KINDS[word["kind"]]}. Синонимы: ...» нужна одна')
        meanings = [line for line in body if line.startswith('Смысл:')]
        if len(meanings) != 1 or not meanings[0][len('Смысл:'):].strip() or TODO in meanings[0]:
            errors.append(f'{where}: смысл не заполнен')
        else:
            unknown = [name for name in re.findall(r'`([^`]+)`', meanings[0]) if name not in names]
            if unknown:
                errors.append(f'{where}: в смысле не слова ядра: {", ".join(unknown)}')
        props = [PROPS_LINE.match(line) for line in body if line.startswith('Тип адресации:')]
        if len(props) != 1 or not props[0]:
            errors.append(f'{where}: строка «Тип адресации: ... Доказательство: ... Цена: ...» нужна одна')
        elif TODO in props[0].group(0):
            errors.append(f'{where}: тип адресации, доказательство или цена не заполнены')
        if word['kind'] == 'foundation' and not any(FOUNDATION_NOTE in line for line in body):
            errors.append(f'{where}: у основания нет «{FOUNDATION_NOTE}»')
    return errors, len(records), len(words)


def update(lines):
    """Rewrite the lines `код:` of the records of the core: (lines, changed)."""
    expected = {word['key']: word for word in core()}
    changed = 0
    for record in parse(lines):
        word = expected.get(record['key'])
        if word:
            for i in range(record['start'] + 1, record['end']):
                if lines[i].startswith('код:') and lines[i] != code_line(word):
                    lines[i] = code_line(word)
                    changed += 1
    return lines, changed


# --- the prices of the words (14.11) ---------------------------------------------------------------

PRICE_KNOWN = 'размер {size} яч., биты {bits}, копирования {copies}, слои {layers} (при компиляции)'
PRICE_RUN = 'размер {size} яч.; биты, копирования, слои — по исполнению'


def price_text(record):
    """The price of a record of the compiler (word_cost.FIELDS) as the record of the document writes it."""
    return (PRICE_KNOWN if record['known'] else PRICE_RUN).format(**record)


def prices(lines, versions):
    """The lines with the price of the colon definitions of the core from the records the compiler made when
    it compiled the definition (versions: word_cost.definition()[2]['versions']): (lines, changed, errors)."""
    records = {record['key']: record for record in parse(lines)}
    count, changed, errors = collections.Counter(), 0, []
    for word in core():
        if word['kind'] not in ('colon', 'foundation'):
            continue
        count[word['name']] += 1
        compiled = versions.get((word['name'], count[word['name']]))
        record = records.get(word['key'])
        if not compiled or not record:
            errors.append(f'{show(word["key"])}: нет записи компилятора или документа')
            continue
        for i in range(record['start'] + 1, record['end']):
            match = PROPS_LINE.match(lines[i])
            if match:
                suffix = ' Основание: ' + FOUNDATION_NOTE + '.' if word['kind'] == 'foundation' else ''
                line = (f'Тип адресации: {match.group(1)}. Доказательство: {match.group(2)}. '
                        f'Цена: {price_text(compiled)}.{suffix}')
                if lines[i] != line:
                    lines[i] = line
                    changed += 1
    return lines, changed, errors


def skeleton(lines):
    """Add the missing records: (lines, added). A new record goes after the previous present record of its
    file, else before the next one, else after the heading `## `src/FILE`` and its paragraphs, else at the end."""
    words = core()
    if not lines:
        lines = ['# Язык', '', TODO, '', WORDS, '']
        for name in paths.KERNEL_FILES:
            lines += [f'## `src/{name}` — {FILE_TITLES[name]}', '']
    added = 0
    for index, word in enumerate(words):
        records = {record['key']: record for record in parse(lines)}
        if word['key'] in records:
            continue
        same = lambda w, word=word, records=records: w['file'] == word['file'] and w['key'] in records
        before = next((records[w['key']] for w in reversed(words[:index]) if same(w)), None)
        after = next((records[w['key']] for w in words[index + 1:] if same(w)), None)
        section = [i for i, line in enumerate(lines) if line.startswith('## ') and f'`{word["file"]}`' in line]
        if before:
            at = before['end']
        elif after:
            at = after['start']
        elif section:          # after the heading of the file and its paragraphs
            at = next((i for i in range(section[0] + 1, len(lines)) if lines[i].startswith('#')), len(lines))
        else:
            at = len(lines)
        lines[at:at] = skeleton_record(word)
        added += 1
    return lines, added


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--update', action='store_true')
    mode.add_argument('--skeleton', action='store_true')
    mode.add_argument('--prices', action='store_true')
    parser.add_argument('--doc', default=str(DOC))
    args = parser.parse_args()
    doc = paths.Path(args.doc)
    lines = doc.read_text().split('\n') if doc.is_file() else []
    if args.check:
        if not lines:
            print(f'FAIL {doc}: нет файла', file=sys.stderr)
            return 1
        errors, records, words = check(lines)
        for error in errors[:50]:
            print('FAIL', error, file=sys.stderr)
        if errors:
            print(f'FAIL language.md: ошибок {len(errors)}; записей {records}, слов ядра {words}', file=sys.stderr)
            return 1
        print(f'PASS language.md: {records} записей = {words} слов ядра, в порядке определения; '
              'файл, строка и хеш совпадают с определением; смысл заполнен')
        return 0
    if args.update:
        lines, changed = update(lines)
        doc.write_text('\n'.join(lines))
        print(f'update: строк кода переписано {changed}')
        return 0
    if args.prices:
        import word_cost
        lines, changed, errors = prices(lines, word_cost.definition()[2]['versions'])
        for error in errors:
            print('FAIL', error, file=sys.stderr)
        doc.write_text('\n'.join(lines))
        print(f'prices: строк цены переписано {changed}')
        return 1 if errors else 0
    lines, added = skeleton(lines)
    doc.write_text('\n'.join(lines) + ('' if lines[-1] == '' else '\n'))
    print(f'skeleton: записей добавлено {added}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
