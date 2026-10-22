#!/usr/bin/env python3
"""Образы копимашины vm2 для сравнения (пункт 13.5.2).

Готовых генераторов арифметики для vm2 нет: `copycode.vm2.arithmetic`
написан для построителя со своими сигналами (не vm2-образ), поэтому здесь
образ собирается напрямую из слоёв по формату `copycode.vm2.boundary.Format`.
Только стандартная библиотека; код в space/ не меняется.

Устройство. Слой = инструкции [n,dst,src] + последняя инструкция-связка,
копирующая следующий слой в процессор (адреса 0..layer_bits). Таблица
лежит в памяти, адрес её записи = base + stride*индекс. Индекс собирается
копированием читаемых бит в поле src инструкции чтения таблицы (в хранимой
копии слоя, не в процессоре): патч слоя должен идти минимум на два слоя
раньше его исполнения (связка читает следующий слой до патча).

Программы (все параметризуются шириной w):
  A  build_lookup_add(w)   сложение w-битных a+b одной таблицей 2^(2w) строк
  B  build_ripple_add(w)   поразрядно, таблица полного сумматора (a,b,c)->(s,c')
  C  build_less(w)         a<b без знака, цепочка по таблице (a,b,lt)->lt'
  D  build_lookup_add(w, corrupt=(a,b))  как A, но в одной строке испорчен бит
Слагаемые и результат — слова, младший бит по младшему адресу.
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'space/vm2/tests'))
sys.path.insert(0, str(ROOT / 'space/copycode/src'))
from vm2_reference import run, get, put
from copycode.vm2.boundary import Format, boot_stream


@dataclass
class Prog:
    name: str
    size: int                 # бит в пространстве
    slots: int
    image: bytes
    reads: list               # [(имя, позиция, ширина)] читаемые слова (бит i по адресу pos+i)
    outs: list                # адреса выдаваемых бит, младший первым
    expected: object          # функция(*значения) -> ожидаемое число
    layers: int = 0           # число рабочих слоёв (тактов программы)
    info: dict = field(default_factory=dict)

    def input_ranges(self):
        return [1 << w for _, _, w in self.reads]


class _Image:
    def __init__(self, slots, min_size=4096):
        self.slots = slots
        self.min_size = min_size

    def build(self, plan):
        """plan(img) заполняет образ; размер подбирается степенью двойки."""
        size = self.min_size
        while True:
            try:
                return plan(_Space(size, self.slots)), size
            except MemoryError:
                size *= 2


class _Space:
    def __init__(self, size, slots):
        self.size, self.slots = size, slots
        self.fmt = Format(size, slots)
        self.z, self.a, self.isz = self.fmt.z, self.fmt.a, self.fmt.isz
        self.lb = self.fmt.layer_bits
        self.used = [(0, self.lb)]
        self.mem = bytearray(self.fmt.space_bytes)
        self.layers = []          # (addr, rows)

    def alloc(self, n, align=1):
        pos = 0
        for s, e in sorted(self.used):
            at = -(-pos // align) * align
            if at + n <= s:
                break
            pos = max(pos, e)
        else:
            at = -(-pos // align) * align
        if at + n > self.size:
            raise MemoryError
        self.used.append((at, at + n))
        return at

    def new_layer(self):
        addr = self.alloc(self.lb, 8)
        self.layers.append([addr, []])
        return len(self.layers) - 1

    def addr(self, k):
        return self.layers[k][0]

    def src_field(self, k, slot):
        return self.addr(k) + slot * self.isz + self.z + self.a


def _pow2_ceil(n):
    return 1 << (n - 1).bit_length() if n > 1 else 1


def _finish(sp, name, reads, outs, expected, info):
    # слой 0 живёт по адресу 0 (процессор), остальные хранятся, последняя связка -> нулевой слой
    zero = sp.alloc(sp.lb, 8)           # нулевой слой: процессор обнулится, останов
    sp.layers.append([zero, []])
    # у слоя-останова связки нет; у предпоследнего связка на него
    n_work = len(sp.layers) - 1
    for k, (addr, rows) in enumerate(sp.layers):
        if k == len(sp.layers) - 1:
            continue
        nxt = sp.addr(k + 1)
        data = sp.fmt.layer(list(rows) + [(sp.lb, 0, nxt)])
        sp.mem[addr // 8:addr // 8 + sp.lb // 8] = data
    assert sp.addr(0) == 0
    return Prog(name, sp.size, sp.slots, bytes(sp.mem), reads, outs, expected,
                layers=n_work, info=info)


def _new_layer0(sp):
    # слой 0 по адресу 0: зарезервированная область процессора
    sp.layers.append([0, []])
    return 0


def build_lookup_add(w=4, *, corrupt=None, name=None, slots=8):
    """A (и D при corrupt=(a,b)): сумма w-битных a,b по таблице 2^(2w) строк.

    Строка = w+1 бит (сумма и перенос), шаг stride = степень двойки >= w+1.
    Слой 0 копирует a и b в разряды индекса поля src слоя 2; слой 2 читает строку.
    """
    stride = _pow2_ceil(w + 1)
    sh = stride.bit_length() - 1
    tsize = (1 << (2 * w)) * stride

    def plan(sp):
        base = sp.alloc(tsize, _pow2_ceil(tsize))
        for idx in range(1 << (2 * w)):
            a, b = idx & ((1 << w) - 1), idx >> w
            v = a + b
            if corrupt is not None and corrupt == (a, b):
                v ^= 1
            put(sp.mem, base + idx * stride, w + 1, v)
        ain = sp.alloc(2 * w)
        out = sp.alloc(w + 1)
        _new_layer0(sp)
        l1, l2 = sp.new_layer(), sp.new_layer()
        fld = sp.src_field(l2, 0)
        sp.layers[0][1] = [(w, fld + sh, ain), (w, fld + sh + w, ain + w)]
        sp.layers[l2][1] = [(w + 1, out, base)]
        return _finish(sp, name or ('D' if corrupt else 'A'),
                       [('a', ain, w), ('b', ain + w, w)], list(range(out, out + w + 1)),
                       lambda a, b: a + b,
                       dict(table_bits=tsize, stride=stride, corrupt=corrupt))
    prog, _ = _Image(slots).build(plan)
    return prog


def build_ripple_add(w=4, *, name='B', slots=8):
    """B: поразрядное сложение, таблица (a,b,c) -> (сумма, перенос), 8 строк по 2 бита.

    Шаг i = три слоя: PA_i (патч поля src: a_i, b_i, перенос), заполнитель,
    LK_i (чтение 2 бит строки -> out+i, перенос попадает в out+i+1 и
    перезаписывается следующим шагом после того, как PA_{i+1} его прочёл).
    Перенос из последнего разряда остаётся в out+w (бит w суммы).
    """
    def plan(sp):
        base = sp.alloc(16, 16)
        for idx in range(8):
            a, b, c = idx & 1, idx >> 1 & 1, idx >> 2
            put(sp.mem, base + idx * 2, 2, a + b + c)       # бит0 сумма, бит1 перенос
        ain = sp.alloc(2 * w)
        out = sp.alloc(w + 1)
        _new_layer0(sp)
        pa, lk = [0], []
        for i in range(w):
            if i:
                pa.append(sp.new_layer())
            sp.new_layer()                                    # заполнитель
            lk.append(sp.new_layer())
        for i in range(w):
            f = sp.src_field(lk[i], 0)
            rows = [(1, f + 1, ain + i), (1, f + 2, ain + w + i)]
            if i:
                rows.append((1, f + 3, out + i))
            sp.layers[pa[i]][1] = rows
            sp.layers[lk[i]][1] = [(2, out + i, base)]
        return _finish(sp, name, [('a', ain, w), ('b', ain + w, w)],
                       list(range(out, out + w + 1)), lambda a, b: a + b,
                       dict(table_bits=16, stride=2))
    prog, _ = _Image(slots).build(plan)
    return prog


def build_less(w=8, *, digit=None, name='C', slots=8):
    """C: a < b без знака (флаг 1 бит). Идём от младшей цифры к старшей:
    lt' = (a<b) | (a==b & lt) по цифрам из digit бит; таблица (a,b,lt)->lt',
    2^(2*digit+1) строк по 1 биту. По умолчанию digit = 4 (или w, если меньше);
    digit=1 даёт поразрядную цепочку. w должно делиться на digit."""
    d = digit or min(w, 4)
    if w % d:
        raise ValueError('w must be divisible by digit')
    steps = w // d
    rows_n = 1 << (2 * d + 1)

    def plan(sp):
        base = sp.alloc(rows_n, _pow2_ceil(rows_n))
        m = (1 << d) - 1
        for idx in range(rows_n):
            a, b, lt = idx & m, idx >> d & m, idx >> 2 * d
            put(sp.mem, base + idx, 1, int(a < b or (a == b and lt)))
        ain = sp.alloc(2 * w)
        ch = sp.alloc(steps)
        _new_layer0(sp)
        pa, lk = [0], []
        for i in range(steps):
            if i:
                pa.append(sp.new_layer())
            sp.new_layer()
            lk.append(sp.new_layer())
        for i in range(steps):
            f = sp.src_field(lk[i], 0)
            rows = [(d, f, ain + i * d), (d, f + d, ain + w + i * d)]
            if i:
                rows.append((1, f + 2 * d, ch + i - 1))
            sp.layers[pa[i]][1] = rows
            sp.layers[lk[i]][1] = [(1, ch + i, base)]
        return _finish(sp, name, [('a', ain, w), ('b', ain + w, w)],
                       [ch + steps - 1], lambda a, b: int(a < b),
                       dict(table_bits=rows_n, stride=1, digit=d))
    prog, _ = _Image(slots).build(plan)
    return prog


def execute(prog, *values, counters=False):
    """Исполнить образ на эталоне: вернуть число выдаваемых бит (и счётчики)."""
    img = bytearray(prog.image)
    for (_, pos, width), v in zip(prog.reads, values):
        assert 0 <= v < 1 << width
        put(img, pos, width, v)
    r = run(boot_stream(bytes(img), prog.size, prog.slots), prog.size, prog.slots, counters=counters)
    out = sum(get(r['memory'], p, 1) << j for j, p in enumerate(prog.outs))
    return (out, r['cost']) if counters else out


def default_programs():
    return {'A': build_lookup_add(4), 'B': build_ripple_add(4), 'C': build_less(8),
            'D': build_lookup_add(4, corrupt=(3, 5), name='D')}


def table_path(tables, name):
    """Путь к таблице name: `.tsv`, если есть, иначе `.tsv.gz`."""
    for ext in ('.tsv', '.tsv.gz'):
        f = Path(tables) / (name + ext)
        if f.exists():
            return f
    raise FileNotFoundError(f'нет таблицы {name} (.tsv или .tsv.gz) в {tables}')


def read_table_text(tables, name):
    """Текст таблицы name из `.tsv` или `.tsv.gz`."""
    f = table_path(tables, name)
    if f.suffix == '.gz':
        import gzip
        return gzip.decompress(f.read_bytes()).decode('utf-8')
    return f.read_text(encoding='utf-8')


def write_table_gz(path, text):
    """Записать `.tsv.gz` детерминированно (без времени и имени в заголовке)."""
    import gzip
    import io
    buf = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=buf, mtime=0, compresslevel=9) as g:
        g.write(text.encode('utf-8'))
    Path(path).write_bytes(buf.getvalue())
