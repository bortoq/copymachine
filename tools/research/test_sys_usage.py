#!/usr/bin/env python3
"""Тест режима --check sys_usage.py: целая таблица проходит, испорченная строка не проходит."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sys_usage


def bump(row):
    """Увеличивает первый номер строки в ссылке файл:строка на 10000."""
    loc = re.sub(r':(\d+)', lambda m: ':%d' % (int(m.group(1)) + 10000), row[1], count=1)
    assert loc != row[1], 'в строке нет номера строки'
    return (row[0], loc) + tuple(row[2:])


def main():
    assert sys_usage.check_rows(sys_usage.rows) == [], 'целая таблица должна проходить'
    idx = next(i for i, r in enumerate(sys_usage.rows) if re.search(r':\d+', r[1]))
    bad = list(sys_usage.rows)
    bad[idx] = bump(bad[idx])
    errs = sys_usage.check_rows(bad)
    assert len(errs) >= 1 and errs[0].startswith('строка %d:' % (idx + 1)), errs
    print('ok')


main()
