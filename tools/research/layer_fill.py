#!/usr/bin/env python3
"""Замер заполненности слоёв (14.2). Пишет docs/research/layer-fill.md.

Слой = такт (tick) эмулятора. Для каждого исполненного такта считается число непустых
инструкций из 8 (копия с пустым полуинтервалом источника и канальная инструкция с low==high пусты).
Исполняется настоящий эмулятор (-s 2^31 -p 8), код vm2_reference/checked-emulator не меняется:
собирается копия checked_vm1.c в tools/research/layer_fill_trace.c (аудит заменён счётчиком),
рантайм эмулятора линкуется как есть. Python-эталон vm2_reference для миллионов тактов слишком
медленный (копирует память на каждом такте), поэтому не используется.

Случаи: L0 с короткой программой на stdin (ядро компилирует и запускает её внутри пространства,
как check-kernel; в замер входят загрузка ядра и компиляция), и потоки трёх самых длинных программ 14.1
(по размеру потока в build/.../check-programs.json): divmod-random, mul-random, faults.
Запуск: python3 -B tools/research/layer_fill.py   (около минут; L0-случай — основной по тактам)
"""
import json, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'space/language/tools'))
import paths  # noqa: E402
import host  # noqa: E402
import check_programs  # noqa: E402

OUT = ROOT / 'docs/research/layer-fill.md'
SLOTS = 8
L0_PROGRAM = 'arithmetic'
LONGEST = 3


def build_tracer(directory):
    exe = directory / 'layer_fill_trace'
    src = paths.EMULATOR_ROOT / 'src'
    cmd = ['gcc', '-O2', '-DVM1_NO_MAIN', '-I', str(src), str(ROOT / 'tools/research/layer_fill_trace.c'),
           str(src / 'runtime.c'), str(src / 'sys_ctrl.c'), str(src / 'bitcopy.c'), str(src / 'backend_bitcopy.c'),
           '-o', str(exe)]
    subprocess.run(cmd, check=True)
    return exe


def trace(exe, data, timeout=1500):
    with tempfile.TemporaryFile() as i, tempfile.TemporaryFile() as o, tempfile.TemporaryFile() as e:
        i.write(data); i.seek(0)
        start = time.monotonic()
        r = subprocess.run([str(exe), '-s', str(paths.SIZE), '-p', str(SLOTS)], stdin=i, stdout=o, stderr=e, timeout=timeout)
        seconds = time.monotonic() - start
        e.seek(0); err = e.read().decode(); o.seek(0); out = o.read()
    assert r.returncode == 0, (r.returncode, err[-300:])
    info = dict(l.split('=', 1) for l in err.split('\n') if l.startswith('LAYER_FILL_'))
    hist = [int(x) for x in info['LAYER_FILL_HIST'].split(',')]
    assert len(hist) == SLOTS + 1 and sum(hist) >= int(info['LAYER_FILL_TICKS'])
    return dict(ticks=int(info['LAYER_FILL_TICKS']), hist=hist, seconds=round(seconds, 1), output=len(out))


def stats(hist):
    layers = sum(hist)
    copies = sum(k * h for k, h in enumerate(hist))
    d = dict(layers=layers, copies=copies, mean=copies / layers, full=hist[SLOTS] / layers, empty=hist[0] / layers)
    for w in (8, 16, 32):
        ideal = -(-copies // w)          # нижняя граница: число копирований / ширина
        d[f'ideal{w}'] = ideal
        d[f'save{w}'] = 1 - ideal / layers
    return d


def main():
    done = json.loads((paths.BUILD / 'check-programs.json').read_text())
    names = [d['name'] for d in sorted(done, key=lambda d: -d['stream_bytes'])[:LONGEST]]
    cases = paths.programs()
    executable = host.build()
    libraries = paths.source_bytes(paths.LIBRARY_FILES)
    l0 = paths.L0.read_bytes()
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        exe = build_tracer(Path(tmp))
        source = cases[L0_PROGRAM][0]
        runs = [(f'L0 + {L0_PROGRAM} (ядро компилирует и запускает программу)', l0 + source.encode('latin-1') + b'\0')]
        for name in names:
            stream = check_programs.compile_on_host(executable, libraries, cases[name][0])
            runs.append((f'поток {name}', stream))
        for label, data in runs:
            r = trace(exe, data); r['label'] = label; r['bytes'] = len(data); r.update(stats(r['hist']))
            results.append(r)
            print(f"{label}: {r['layers']} слоёв, среднее {r['mean']:.3f}, полных {r['full']:.1%} ({r['seconds']} с)", flush=True)
    total = [sum(r['hist'][k] for r in results) for k in range(SLOTS + 1)]
    write(results, total)


def write(results, total):
    L = ['# Заполненность слоёв (14.2)', '',
         'Слой = такт эмулятора; ширина процессора 8 инструкций (`-p 8`), пространство 2^31 бит. '
         'Непустая инструкция: копия с непустым источником или канальная с `low != high`. '
         'Скрипт: `tools/research/layer_fill.py` (счётчик — `tools/research/layer_fill_trace.c`, копия '
         '`checked_vm1.c` с счётчиком вместо аудита; рантайм эмулятора линкуется без изменений). '
         'Python-эталон `vm2_reference` не использован: на миллионах тактов он копирует память каждый такт.', '',
         '## Замеры', '']
    L += ['| Случай | Байт на stdin | Слоёв | Копирований | Среднее в слое | Полных слоёв | Пустых слоёв |', '|---|---:|---:|---:|---:|---:|---:|']
    for r in results + [dict(label='**Сумма**', bytes='', **stats(total))]:
        L.append(f"| {r['label']} | {r['bytes']} | {r['layers']} | {r['copies']} | {r['mean']:.3f} | {r['full']:.2%} | {r['empty']:.2%} |")
    L += ['', 'Распределение числа непустых инструкций в слое (доля слоёв):', '',
          '| Случай | ' + ' | '.join(str(k) for k in range(SLOTS + 1)) + ' |', '|---|' + '---:|' * (SLOTS + 1)]
    for label, h in [(r['label'], r['hist']) for r in results] + [('**Сумма**', total)]:
        n = sum(h)
        L.append(f'| {label} | ' + ' | '.join(f'{x / n:.2%}' for x in h) + ' |')
    s = stats(total)
    L += ['', '## Оценка', '',
          'Без переделки программ: если бы планировщик заполнял слои полностью, слоёв было бы не меньше '
          '`ceil(копирований / ширина)` (нижняя граница; зависимости по данным между копиями не учитываются, '
          'поэтому реальная экономия меньше).', '',
          '| Ширина | Слоёв сейчас (ширина 8) | Нижняя граница слоёв | Экономия тактов |', '|---:|---:|---:|---:|']
    for w in (8, 16, 32):
        L.append(f"| {w} | {s['layers']} | {s[f'ideal{w}']} | {s[f'save{w}']:.1%} |")
    L += ['', f"Для сумм: среднее {s['mean']:.2f} непустых инструкций из 8, полных слоёв {s['full']:.2%}. "
          'Строка ширины 8 показывает, сколько дал бы идеальный планировщик уже на текущей ширине; '
          'для 16 и 32 нижняя граница достигается только при независимости копий в слое.', '',
          '## Вывод', '',
          f"Слои заполнены в среднем на {s['mean'] / 8:.0%} (суммарно доминирует L0: он даёт почти все такты). "
          f"Идеальное заполнение при ширине 8 сократило бы число тактов на {s['save8']:.0%}, при 16 - на {s['save16']:.0%}, "
          f"при 32 - на {s['save32']:.0%} (нижняя граница числа слоёв; без учёта зависимостей между копиями). "
          'Пока планировщик не заполняет слои, ширина 16 или 32 сама по себе тактов не экономит: '
          'слоёв не меньше, чем при 8. Выигрыш даёт только перепланировка.', '']
    OUT.write_text('\n'.join(L))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
