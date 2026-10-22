#!/usr/bin/env python3
"""Символьный исполнитель копимашины vm2 (пункт 13.5.3).

Повторяет семантику `vm2_reference.run` (инструкция [n,dst,src], такт =
выборка всех слотов из состояния «до», затем копии), но каждый бит памяти —
узел BDD из bdd.py (0 и 1 — константы). Копирование переносит узлы.

Поле инструкции (n, dst или src) читается из памяти процессора, поэтому его
биты тоже узлы. Если они все константы, инструкция исполняется как обычно.
Иначе перебираются все значения переменных, от которых зависят биты полей
этой инструкции, сгруппированные по получаемой тройке (n,dst,src): для
каждой тройки — условие (BDD набора значений, её дающих), и новый бит по
адресу p получается цепочкой ite(условие, исходный бит, прежний бит).
Перебор сделан разложением по переменной (по узлам BDD полей, с памятью),
а не по 2^k наборам: так поле, зависящее от 16 переменных (цепочка сравнения C
с w=8 на последнем шаге), но принимающее мало значений, обрабатывается за
число этих значений. Предел 2^12 относится к числу различных троек (вариантов);
больше — исключение TooLarge («слишком велико»).

Не поддерживается (исключение Unsupported): канал и SYS — копия с концом
>= size при n > 0 (и в любом варианте поля), а также останов, зависящий от
переменных (часть значений дала бы все n=0, часть нет). Как и в эталоне,
конец исполнения — такт, где все n равны 0; лимит 1000 тактов.

Начальное состояние. Образы 13.5.2 ставятся в память загрузкой через канал
(boot_stream), а канал здесь не поддерживается. Проверено на эталоне: после
первых трёх тактов загрузки состояние памяти равно образу (prog.image) бит
в бит, процессор содержит слой 0. Поэтому исполнитель берёт prog.image
напрямую как уже загруженное состояние (ни запуск эталона, ни канал не нужны);
первый такт исполнителя = первый рабочий такт программы. Читаемые биты
(prog.reads) заменяются переменными BDD, остальная память — константы образа.

Нумерация переменных: читаемые слова называются по имени ('a','b',...),
переменная = (номер бита)*(число слов)+(номер слова в reads), т.е. разряды
слов чередуются a0,b0,a1,b1,... У программ с одинаковыми именами и ширинами
слов (A,B,C,D) одни и те же номера, поэтому их узлы лежат в общей BDD и
сравниваются как целые числа (равенство узла = равенство функций).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bdd import BDD, TERMINAL_VAR

MAX_VARIANTS = 1 << 12
MAX_TICKS = 1000


class TooLarge(Exception):
    """Слишком велико: поле инструкции зависит от >12 переменных."""


class Unsupported(Exception):
    """Канал, SYS или останов, зависящий от переменных."""


def var_index(prog, name, bit):
    """Номер переменной BDD для бита `bit` читаемого слова `name`."""
    names = [r[0] for r in prog.reads]
    return bit * len(names) + names.index(name)


def initial_memory(bdd, prog):
    """Список узлов по битам: константы образа, читаемые биты — переменные."""
    img = prog.image
    mem = [(img[i // 8] >> (7 - i % 8)) & 1 for i in range(prog.size)]
    for name, pos, width in prog.reads:
        for j in range(width):
            mem[pos + j] = bdd.var(var_index(prog, name, j))
    return mem


class SymExec:
    """Символьная копимашина: mem — список узлов BDD длиной size."""

    def __init__(self, bdd, mem, size, slots):
        self.bdd, self.mem, self.size, self.slots = bdd, list(mem), size, slots
        a = size.bit_length()
        self.a, self.z = a, a - 1
        self.isz = 3 * a - 1
        self.cost = dict(layers=0, copies=0, bits=0, variants=0)

    @classmethod
    def from_prog(cls, prog, bdd=None):
        bdd = bdd or BDD()
        return cls(bdd, initial_memory(bdd, prog), prog.size, prog.slots)

    def _rows(self):
        z, a, i, m = self.z, self.a, self.isz, self.mem
        return [(m[k * i:k * i + z], m[k * i + z:k * i + z + a], m[k * i + z + a:k * i + z + 2 * a])
                for k in range(self.slots)]

    def _any_active(self, rows):
        """Узел «хотя бы одно n != 0» (BDD)."""
        b, r = self.bdd, 0
        for n, _, _ in rows:
            for bit in n:
                r = b.or_(r, bit)
        return r

    def _variants(self, n_bits, d_bits, s_bits):
        """Все значения тройки (n,dst,src) -> условие (BDD) на переменные.

        Это перебор значений переменных, от которых зависят биты полей,
        сгруппированный по получаемому значению: разложение по старшей
        переменной с памятью по кортежу узлов. Число перебираемых наборов
        из-за этого не 2^(число переменных), а не больше числа различных
        значений поля (и размера BDD). Больше 2^12 различных троек —
        TooLarge.
        """
        b, memo = self.bdd, {}
        kn, kd = len(n_bits), len(d_bits)

        def val(bits):
            return sum(x << k for k, x in enumerate(bits))

        def rec(t):
            r = memo.get(t)
            if r is not None:
                return r
            top = min(b.nodes[x][0] for x in t)
            if top >= TERMINAL_VAR:
                r = {(val(t[:kn]), val(t[kn:kn + kd]), val(t[kn + kd:])): 1}
            else:
                lo = tuple(b.nodes[x][1] if b.nodes[x][0] == top else x for x in t)
                hi = tuple(b.nodes[x][2] if b.nodes[x][0] == top else x for x in t)
                r0, r1 = rec(lo), rec(hi)
                v = b.var(top)
                r = {k: b.ite(v, r1.get(k, 0), r0.get(k, 0)) for k in {**r0, **r1}}
            if len(r) > MAX_VARIANTS:
                raise TooLarge(f'слишком велико: {len(r)} вариантов поля > 2^12')
            memo[t] = r
            return r
        return rec(tuple(n_bits) + tuple(d_bits) + tuple(s_bits))

    def step(self):
        """Один такт. Возвращает False при останове (все n = 0)."""
        b = self.bdd
        rows = self._rows()
        act = self._any_active(rows)
        if act == 0:
            return False
        if act != 1:
            raise Unsupported('останов зависит от переменных')
        before = self.mem
        new = list(before)
        for n_bits, d_bits, s_bits in rows:
            fields = n_bits + d_bits + s_bits
            if all(f < 2 for f in fields):
                n, d, s = (sum(f << k for k, f in enumerate(x)) for x in (n_bits, d_bits, s_bits))
                self._copy_const(new, before, n, d, s)
                continue
            groups = self._variants(n_bits, d_bits, s_bits)
            self.cost['variants'] += len(groups)
            self.cost['copies'] += 1
            self.cost['bits'] += max(t[0] for t in groups)
            for (n, d, s), cond in groups.items():
                self._check(n, d, s)
                for j in range(n):
                    new[d + j] = b.ite(cond, before[s + j], new[d + j])
        self.mem = new
        self.cost['layers'] += 1
        return True

    def _check(self, n, d, s):
        if n and max(d, s) >= self.size:
            raise Unsupported('канал или SYS не поддерживаются')
        if n and not (0 <= d and d + n <= self.size and 0 <= s and s + n <= self.size):
            raise Unsupported('копия выходит за память')

    def _copy_const(self, new, before, n, d, s):
        if not n:
            return
        self._check(n, d, s)
        self.cost['copies'] += 1
        self.cost['bits'] += n
        new[d:d + n] = before[s:s + n]

    def run(self):
        ticks = 0
        while self.step():
            ticks += 1
            if ticks > MAX_TICKS:
                raise AssertionError('превышен предел тактов')
        return ticks

    def word(self, positions):
        """Узлы по адресам (младший первым)."""
        return [self.mem[p] for p in positions]


def execute_symbolic(prog, bdd=None):
    """Исполнить образ символьно. Возвращает (SymExec, узлы выходных бит)."""
    m = SymExec.from_prog(prog, bdd)
    m.run()
    return m, m.word(prog.outs)
