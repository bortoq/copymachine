"""Такты слов, затронутых изоляцией ядра (14.10): space! spacec! space@ spacec@ execute catch и вызов слова.

Схема разности как у call_ticks.py: два размера цикла (9 и 1), (t9 - t1) / 8, минус пустой цикл.
Программа идёт через L0 (ядро само компилирует её в своём пространстве, это программа ядра с проверками
изоляции) на checked-emulator; компиляция в t9 и t1 одинакова, и разность её сокращает.
Столбец host: тот же исходник, поток которого собран определением на хостовом pForth (без проверок).

Использование: isolation_ticks.py NAME L0.boot   (NAME: метка запуска, например before или after)
Результат складывается в docs/research/isolation-ticks.json под NAME (без времени и путей хоста).
Для NAME == after добавляется столбец host."""
import json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / 'space/language/tools')]
import check_programs  # noqa: E402
import host  # noqa: E402
import paths  # noqa: E402

FREE = (1 << 30) + (1 << 28)
UNITS = {
    'пустой цикл': '',
    'вызов слова w': 'w',
    f'7 {FREE} {FREE + 32} space!': f'7 {FREE} {FREE + 32} space!',
    f'7 {FREE} {FREE + 8} spacec!': f'7 {FREE} {FREE + 8} spacec!',
    f'{FREE} {FREE + 32} space@ drop': f'{FREE} {FREE + 32} space@ drop',
    f'{FREE} {FREE + 8} spacec@ drop': f'{FREE} {FREE + 8} spacec@ drop',
    "['] w execute": "['] w execute",
    "['] w catch drop": "['] w catch drop",
}


def source(unit, n):
    return f'variable x\n: w ;\n: main {n} 0 do {unit} loop ;'


def ticks(stream):
    run = subprocess.run([str(paths.CHECKED), '-s', str(paths.SIZE), '-p', '8'], input=stream,
                         capture_output=True, timeout=3600)
    assert run.returncode == 0, run.stderr[-300:]
    assert not run.stdout.startswith(b'error'), run.stdout[:60]
    return int(run.stderr.split(b'VM1_AUDIT_TICKS=')[1].split()[0])


def main():
    name, l0 = sys.argv[1], Path(sys.argv[2]).read_bytes()
    executable, libraries = host.build(), paths.source_bytes(paths.LIBRARY_FILES)
    result = {}
    base = {}
    for label, unit in UNITS.items():
        row = {}
        for column in ('L0', 'host') if name == 'after' else ('L0',):
            def run(n):
                text = source(unit, n)
                if column == 'L0':
                    return ticks(l0 + text.encode('latin-1') + b'\0')
                return ticks(check_programs.compile_on_host(executable, libraries, text))
            try:
                per = (run(9) - run(1)) / 8
            except Exception as error:      # the word does not exist in this L0 (before the fix: space@)
                per = None
                print(label, column, 'ошибка', str(error)[:80], flush=True)
            if label == 'пустой цикл':
                base[column] = per
            row[column] = None if per is None else per - base[column] if label != 'пустой цикл' else per
        result[label] = row
        print(f'{label:40} {row}', flush=True)
    target = REPO / 'docs/research/isolation-ticks.json'
    data = json.loads(target.read_text()) if target.is_file() else {}
    data[name] = result
    target.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
