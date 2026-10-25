"""doc/language.md (14.9) is synchronized with the core of the language: tools/language_md.py --check.

On a temporary copy of the component (src, tools, doc and tools/research/defgraph.py; the working
files are not touched): the copy passes --check; a removed record, an extra record, a changed
definition without a change of its record, a shifted definition and a meaning left as the TODO of
--skeleton each give a nonzero exit code; --update rewrites only the lines `код:` and makes a changed
definition pass again; --skeleton restores a removed record with the meaning TODO.
"""
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]                 # space/language
WORKSPACE = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import paths  # noqa: E402

ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', COPYCODE_ROOT=str(paths.COPYCODE_ROOT),
           VM2_ROOT=str(paths.VM2_ROOT), FORTH_ROOT=str(paths.FORTH), EMULATOR_ROOT=str(paths.EMULATOR_ROOT))


def copy_component(to):
    language = to / 'space/language'
    for part in ('src', 'tools', 'doc'):
        shutil.copytree(ROOT / part, language / part, ignore=shutil.ignore_patterns('__pycache__'))
    (to / 'tools/research').mkdir(parents=True)
    shutil.copy(WORKSPACE / 'tools/research/defgraph.py', to / 'tools/research/defgraph.py')
    return language


def run(language, *args):
    result = subprocess.run([sys.executable, '-B', str(language / 'tools/language_md.py'), *args],
                            capture_output=True, text=True, env=ENV)
    return result.returncode, result.stdout + result.stderr


def main():
    with tempfile.TemporaryDirectory(prefix='language-md-') as tmp:
        language = copy_component(Path(tmp))
        doc, src = language / 'doc/language.md', language / 'src'
        original = doc.read_text()
        prelude = (src / 'prelude.fth').read_text()

        code, out = run(language, '--check')
        assert code == 0, out
        print('PASS the copy passes --check:', out.strip().splitlines()[-1])

        # 1. a removed record
        start = original.index('### `tuck`\n')
        end = original.index('\n### ', start + 1) + 1
        doc.write_text(original[:start] + original[end:])
        code, out = run(language, '--check')
        assert code != 0 and 'нет записи' in out and '`tuck`' in out, out
        print('PASS a removed record: --check', code)

        # 2. --skeleton restores it, with the meaning TODO, which --check rejects
        code, out = run(language, '--skeleton')
        assert code == 0 and 'добавлено 1' in out, out
        restored = doc.read_text()
        assert restored.count('### `tuck`\n') == 1 and 'Смысл: TODO' in restored
        code, out = run(language, '--check')
        assert code != 0 and 'смысл не заполнен' in out, out
        meaning = re.search(r'### `tuck`\n\n.*?\n\n(Смысл: .*?)\n', original).group(1)
        assert restored.replace('Смысл: TODO', meaning, 1) == original, 'the skeleton record differs only by the meaning'
        print('PASS --skeleton restores the record with the meaning TODO: --check', code)

        # 3. an extra record (a word that is not in the core)
        extra = original.replace('### `tuck`\n', '### `no-such-word`\n\nВид: определение `:`. Синонимы: нет.\n\n'
                                 'Смысл: слова нет.\n\nкод: src/prelude.fth:7 000000000000\n\nТип адресации: '
                                 'индексное пространство. Доказательство: не доказано. Цена: по исполнению.\n\n'
                                 '### `tuck`\n', 1)
        doc.write_text(extra)
        code, out = run(language, '--check')
        assert code != 0 and 'лишняя запись' in out and 'no-such-word' in out, out
        print('PASS an extra record: --check', code)

        # 4. a changed definition without a change of its record; --update rewrites only `код:`
        doc.write_text(original)
        changed = prelude.replace(': nip ( a b -- b ) swap drop ;', ': nip ( a b -- b ) >r drop r> ;')
        assert changed != prelude
        (src / 'prelude.fth').write_text(changed)
        code, out = run(language, '--check')
        assert code != 0 and '`nip`' in out and 'строка кода' in out, out
        print('PASS a changed definition without a change of the record: --check', code)
        code, out = run(language, '--update')
        assert code == 0 and 'переписано 1' in out, out
        diff = [(a, b) for a, b in zip(original.split('\n'), doc.read_text().split('\n')) if a != b]
        assert len(diff) == 1 and diff[0][0].startswith('код: src/prelude.fth:6 ') and diff[0][1].startswith(
            'код: src/prelude.fth:6 '), diff
        code, out = run(language, '--check')
        assert code == 0, out
        print('PASS --update rewrites only the line `код:`, then --check', code)

        # 5. a shifted definition (the line of every word of the file changes)
        doc.write_text(original)
        (src / 'prelude.fth').write_text('\n' + prelude)
        code, out = run(language, '--check')
        assert code != 0 and 'src/prelude.fth:7 ' in out, out
        print('PASS a shifted definition: --check', code)
        (src / 'prelude.fth').write_text(prelude)

        # 6. a meaning naming a word outside the core
        doc.write_text(original.replace('### `tuck`\n\nВид: определение `:`. Синонимы: нет.\n\nСмысл: ',
                                        '### `tuck`\n\nВид: определение `:`. Синонимы: нет.\n\nСмысл: как `fc-number`; ', 1))
        code, out = run(language, '--check')
        assert code != 0 and 'fc-number' in out, out
        print('PASS a meaning with a name outside the core: --check', code)
    assert (ROOT / 'doc/language.md').read_text() == original and (ROOT / 'src/prelude.fth').read_text() == prelude
    print('PASS the working files are unchanged')


if __name__ == '__main__':
    main()
