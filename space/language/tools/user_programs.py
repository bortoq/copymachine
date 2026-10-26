#!/usr/bin/env python3
"""User programs do not get dearer (14.14, space/language/doc/user_programs.md).

When the language is recompiled, the programs of the user are recompiled with it; the new code is
accepted if its price is not higher (and it gives the same artifacts), otherwise the previous code stays.
The mechanism is a tool outside the kernel: the definition of the language needs none of it.

    Language   the definition of the language: the texts of src/ (a copy of the sources, or another
               directory with the same files); `replaced` puts another definition of a word in its place.
    Store      the programs of the user: the source, the current code (the stream of the boot), its
               price, the reference artifact (the output on checked-emulator), the stack of the previous
               codes and the history of the recompilations.

The price of a program. The compiler gives every word its price (size, bits, copies, layers; 14.11);
PRICE (the same sum as the generator gen-price) makes one number of it. The price of a program is the
price of each of its words (those it defines with `:`) and their sum. The words priced by execution
(a loop, recursion, a call of an xt) have their size only: they are compared only in the sum (their
size can grow by the alignment of the cells when a word they call becomes smaller). With MEASURE the
price of the run is also compared (the counters of 13.4 on the execution of the whole program: size of
its words, bits, copies, layers).

The rule. RULE 'words' (default): the new code is accepted if no word of the program with a price known at compile
time is dearer and the program is not dearer; 'total': if the sum is not higher. The program is compiled as a whole (calls
are bound while compiling), so a word is not taken from the old code and the others from the new one:
either all the new code or all the old one. Besides the price the new code has to give the same
artifact as the old one (the same output), else it is refused (reason 'artifacts'); a language that
cannot compile the program is refused (reason 'error').

Usage: user_programs.py add STORE NAME FILE [--language DIR]
       user_programs.py recompile STORE [--language DIR] [--rule words|total] [--measure] [--boot L0]
       user_programs.py show STORE
"""
import argparse, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

import boot
import counters
import paths
import word_cost

COUNTERS = ('size', 'bits', 'copies', 'layers')


def price(size, bits, copies, layers):
    """The formula of the language word PRICE (generator gen-price): the sum."""
    return size + bits + copies + layers


class CompileError(Exception):
    """The language could not compile the program."""


# ---------------------------------------------------------------- the language

def definition_span(text, name):
    """(start, end) of the lines of the colon definition `: name ...` in text; None if not there."""
    lines = text.splitlines(keepends=True)
    at = next((i for i, line in enumerate(lines) if re.match(r': %s(\s|$)' % re.escape(name), line)), None)
    if at is None:
        return None
    for end in range(at, len(lines)):
        code = re.split(r'(?:^|\s)\\(?:\s|$)', lines[end], maxsplit=1)[0]     # without the comment to the end of the line
        if code.rstrip().endswith(' ;') or code.rstrip() == ';':
            return sum(map(len, lines[:at])), sum(map(len, lines[:end + 1]))
    raise ValueError('definition of %s does not end' % name)


class Language:
    """The definition of the language: {file name: text} of src/ (latin-1, as the host reads it)."""

    def __init__(self, files):
        self.files = dict(files)

    @classmethod
    def load(cls, directory=paths.SRC):
        directory = Path(directory)
        return cls({name: (directory / name).read_bytes().decode('latin-1') for name in paths.KERNEL_FILES})

    def libraries(self):
        """What the host pForth loads as native words (the compiler and the generators)."""
        return ''.join(self.files[n] for n in paths.LIBRARY_FILES).encode('latin-1')

    def text(self):
        return ''.join(self.files[n] for n in paths.KERNEL_FILES)

    def digest(self):
        return hashlib.sha256(self.text().encode('latin-1')).hexdigest()

    def replaced(self, name, definition):
        """A language in which the colon definition of NAME is DEFINITION (text of its lines)."""
        found = [(f, definition_span(t, name)) for f, t in self.files.items()]
        found = [(f, span) for f, span in found if span]
        if len(found) != 1:
            raise ValueError('%s is defined %d times' % (name, len(found)))
        (file, (start, end)), files = found[0], dict(self.files)
        files[file] = self.files[file][:start] + definition.rstrip('\n') + '\n' + self.files[file][end:]
        return Language(files)

    def boot(self, timeout=3000):
        """Recompile the language: the host pForth executes the definition (tools/boot.py); the stream L0."""
        import host
        lines = [boot.SIZES] + ['fc| ' + line for line in self.text().split('\n')] + ['fc-go', 'bye']
        data = self.libraries() + ('\n'.join(lines) + '\n').encode('latin-1')
        result = subprocess.run([str(host.build())], input=data, capture_output=True, timeout=timeout)
        if result.returncode or result.stderr or not result.stdout.endswith(b'\n'):
            raise CompileError('boot failed: code %d, %r' % (result.returncode, result.stdout[-300:]))
        return result.stdout[:-1]


# ---------------------------------------------------------------- compiling and running a program

def program_words(source):
    """The names a program defines with `:` (in order, without repeats)."""
    names = []
    for name in re.findall(r'(?:^|\s):\s+(\S+)', source):
        if name not in names:
            names.append(name)
    return names


def run_checked(stream, timeout=600):
    """The output of the stream on checked-emulator (the artifact of a program)."""
    run = subprocess.run([str(paths.CHECKED), '-s', str(paths.SIZE), '-p', '8'], input=stream,
                         capture_output=True, timeout=timeout)
    if run.returncode or b'AUDIT' in run.stderr.replace(b'VM1_AUDIT_TICKS', b''):
        raise CompileError('the code does not run: %d %r' % (run.returncode, run.stderr[-200:]))
    return run.stdout


def compile_program(language, source, measure=False, limit=2_000_000):
    """dict(stream, words {name: counters and price}, total, output, run) of the program compiled by
    LANGUAGE on the host. run (with MEASURE): the price of the execution on the counters of 13.4."""
    try:
        stream, records, _ = word_cost.compile_with_records(source, libraries=language.libraries())
    except (AssertionError, ValueError) as error:
        raise CompileError('the language does not compile the program: %s' % str(error)[:300])
    words = {}
    for name in program_words(source):
        if name not in records:
            raise CompileError('no record of %s' % name)
        record = records[name]
        words[name] = {k: record[k] for k in COUNTERS + ('known',)}
        words[name]['price'] = price(*(record[k] for k in COUNTERS))
    result = dict(stream=stream, words=words, total=sum(w['price'] for w in words.values()),
                  output=run_checked(stream), run=None)
    if measure:
        trace = counters.run(stream, limit=limit)['trace']
        got = counters.counters(trace, 0, len(trace) - 1)
        size = sum(w['size'] for w in words.values())
        result['run'] = dict(ticks=len(trace), bits=got['bits'], copies=got['rows'], layers=got['layers'],
                             price=price(size, got['bits'], got['rows'], got['layers']))
    return result


def judge(old, new, rule='words'):
    """(accepted, reason, detail): is the code NEW (a compile_program result or its record) accepted
    in place of OLD. The reasons: 'price' (a word dearer, or the sum), 'artifacts' (another output)."""
    if new['output'] != old['output']:
        return False, 'artifacts', 'the output differs'
    if rule == 'words':
        # a word priced by execution has its size only: it is not compared alone (its size goes into the sum)
        dearer = [n for n, w in new['words'].items() if n in old['words'] and w['known'] and old['words'][n]['known']
                  and w['price'] > old['words'][n]['price']]
        if dearer:
            return False, 'price', 'dearer words: ' + ', '.join(
                '%s %d -> %d' % (n, old['words'][n]['price'], new['words'][n]['price']) for n in dearer)
    elif rule != 'total':
        raise ValueError(rule)
    if new['total'] > old['total']:
        return False, 'price', 'the program: %d -> %d' % (old['total'], new['total'])
    if new.get('run') and old.get('run') and new['run']['price'] > old['run']['price']:
        return False, 'price', 'the run: %d -> %d' % (old['run']['price'], new['run']['price'])
    return True, '', ''


# ---------------------------------------------------------------- the programs of the user

class Store:
    """A directory with one subdirectory per program: source.fth, code.stream, output.bin,
    record.json (language, price of the words, total, run, history) and stack/NNN.stream (previous codes)."""

    def __init__(self, directory):
        self.dir = Path(directory)

    def names(self):
        return sorted(p.name for p in self.dir.iterdir() if (p / 'record.json').is_file()) if self.dir.is_dir() else []

    def record(self, name):
        return json.loads((self.dir / name / 'record.json').read_text())

    def source(self, name):
        return (self.dir / name / 'source.fth').read_text()

    def code(self, name):
        return (self.dir / name / 'code.stream').read_bytes()

    def output(self, name):
        return (self.dir / name / 'output.bin').read_bytes()

    def stack(self, name):
        return [p.read_bytes() for p in sorted((self.dir / name / 'stack').glob('*.stream'))]

    def _save(self, name, result, language, history, measure):
        directory = self.dir / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'code.stream').write_bytes(result['stream'])
        (directory / 'output.bin').write_bytes(result['output'])
        record = dict(language=language.digest(), words=result['words'], total=result['total'], run=result['run'],
                      measure=measure, stream_sha256=hashlib.sha256(result['stream']).hexdigest(), history=history)
        (directory / 'record.json').write_text(json.dumps(record, indent=1) + '\n')

    def add(self, name, source, language, measure=False):
        """Compile the program by the language; its code is the first one."""
        result = compile_program(language, source, measure)
        directory = self.dir / name
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
        (directory / 'source.fth').write_text(source)
        self._save(name, result, language, [dict(language=language.digest(), status='new', total=result['total'])], measure)
        return result

    def recompile(self, language, rule='words', measure=False):
        """Recompile every program by the language. Returns [(name, status, reason, detail)], status:
        'same' (the same code), 'accepted' (other code, not dearer, to the stack goes the previous one),
        'refused' (the previous code stays; reason price, artifacts or error)."""
        report = []
        for name in self.names():
            old, source = self.record(name), self.source(name)
            old = dict(old, output=self.output(name))
            try:
                new = compile_program(language, source, measure or bool(old.get('run')))
                accepted, reason, detail = judge(old, new, rule)
            except CompileError as error:
                new, accepted, reason, detail = None, False, 'error', str(error)
            history = old['history']
            if not accepted:
                history.append(dict(language=language.digest(), status='refused', reason=reason, detail=detail,
                                    total=new['total'] if new else None))
                record = dict(old, history=history)
                record.pop('output')
                (self.dir / name / 'record.json').write_text(json.dumps(record, indent=1) + '\n')
                report.append((name, 'refused', reason, detail))
                continue
            if new['stream'] == self.code(name):
                history.append(dict(language=language.digest(), status='same', total=new['total']))
                self._save(name, new, language, history, bool(new['run']))
                report.append((name, 'same', '', 'total %d' % new['total']))
                continue
            stack = self.dir / name / 'stack'
            stack.mkdir(exist_ok=True)
            (stack / ('%03d.stream' % len(list(stack.glob('*.stream'))))).write_bytes(self.code(name))
            history.append(dict(language=language.digest(), status='accepted', total=new['total'],
                                before=old['total']))
            self._save(name, new, language, history, bool(new['run']))
            report.append((name, 'accepted', '', 'total %d -> %d' % (old['total'], new['total'])))
        return report


# ---------------------------------------------------------------- command line

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('add')
    add.add_argument('store'), add.add_argument('name'), add.add_argument('file')
    add.add_argument('--language', default=str(paths.SRC))
    add.add_argument('--measure', action='store_true')
    again = sub.add_parser('recompile')
    again.add_argument('store')
    again.add_argument('--language', default=str(paths.SRC))
    again.add_argument('--rule', choices=('words', 'total'), default='words')
    again.add_argument('--measure', action='store_true')
    again.add_argument('--boot', help='also recompile the language itself (boot) and write its L0 here')
    show = sub.add_parser('show')
    show.add_argument('store')
    args = parser.parse_args()
    store = Store(args.store)
    if args.command == 'add':
        result = store.add(args.name, open(args.file).read(), Language.load(args.language), args.measure)
        print(f'{args.name}: {len(result["stream"])} bytes, price {result["total"]}')
    elif args.command == 'recompile':
        language = Language.load(args.language)
        if args.boot:
            stream = language.boot()
            Path(args.boot).write_bytes(stream)
            print(f'boot: L0 {len(stream)} bytes -> {args.boot}')
        for name, status, reason, detail in store.recompile(language, args.rule, args.measure):
            print(f'{name}: {status}{" (" + reason + ")" if reason else ""} {detail}')
    else:
        for name in store.names():
            record = store.record(name)
            print(f'{name}: price {record["total"]}, stack {len(store.stack(name))}, history '
                  + ' '.join(h['status'] for h in record['history']))


if __name__ == '__main__':
    sys.exit(main())
