# Сборка и проверка vm2

Нужны Python 3.11+, Linux/POSIX, совместимые исходники copycode и бинарник
emulator ABI rev1. В copymachine зависимости находятся рядом. В автономном
архиве make выбирает vendor/emulator и vendor/copycode. В другом размещении
задаются COPYCODE_ROOT, EMULATOR_ROOT и EMULATOR. Произвольный установленный emulator
можно запускать через EMULATOR, но для аудитора tests/checked_vm1.c нужны исходники.

```sh
make                          # прямой пример -> build/direct-example/
make check-direct             # 64 сценария + CLI прямого пути и лимиты ресурсов
make guest GUEST_S=30000 GUEST_P=9
./vm2 -s30000 -p9 < guest-boot
make check                    # независимый vm2-эталон и проверенные такты emulator
make benchmark                # реальные процессы и число физических тактов
make benchmark-direct BENCH_REPEATS=2 BENCH_TICKS=4
make distcheck                # полный автономный выпуск
make clean                    # build/tmp/dist/кэши, без удаления исходника vm2
```

Прямой ABI и команды `vm2c compile/check/run/resume` описаны в
[direct.md](direct.md). Бенчмарки запускаются последовательно на одном CPU,
с nice=15, пределом адресного пространства 768 МиБ для каждого процесса,
ограничением CPU и общим таймаутом 180 секунд. `BENCH_SECONDS` и
`BENCH_MEMORY_MIB` задают бюджет. По таймауту уничтожается вся группа
процессов. Это пределы каждого процесса, а не общий cgroup-лимит памяти.
Для обычной проверки без тяжёлого интерпретатора достаточно `make check-direct`.

make при необходимости собирает build/bitcopy/emulator в объявленной зависимости.
Новый гостевой процессор превышает сетевой профиль emulator ≤65520 бит, поэтому
его проверенный путь — bitcopy. Подмена backend при запуске не производится.

Проверочный C-аудитор собирается теми же CC/CPPFLAGS/CFLAGS/LDFLAGS/LDLIBS.
Для ASan/UBSan можно задать обычные sanitizer flags; локальный LSan под
ptrace не поддерживается. Сами вычисления всё равно выполняются на emulator.
C-версия vm2 доступна только явно: make legacy/check-core/check-legacy.

Сборки/тесты поддерживают каталоги с пробелами. Запускатель использует
VM2_CACHE; при make это build/guest-cache, при самостоятельном запуске —
пользовательский ~/.cache/copymachine/vm2. Новые EMULATOR/COPYCODE версии меняют
идентичность скомпилированного кода. Повреждённый кэш отклоняется.

CI требует четыре repository variables для **опубликованных совместимых**
исходных архивов: EMULATOR_SOURCE_URL, EMULATOR_SOURCE_SHA256, COPYCODE_SOURCE_URL,
COPYCODE_SOURCE_SHA256. tools/dependency_sources.py проверяет SHA256 архива
и файлов перед размещением vendor/. До публикации новых зависимостей эти
значения настроить нельзя; локальная проверка автономного архива не зависит
от GitHub. GitHub CI в этой работе не запускался. Создание новых удалённых
репозиториев и публикация остаются отдельным поручением.
