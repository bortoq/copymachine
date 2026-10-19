# copycode

Общий копикод copymachine и инструменты его сборки/запуска. Гостевые программы
состоят из копирований; арифметика, вывод и снимки выполняются в пространстве.
Python генерирует код, подаёт потоки и проверяет результат.

Копикод — логические инструкции `[n,dst,src]`. Четыре границы vm1 —
псевдоинструкции: описания каналов переноса битового сигнала между
полуинтервалами, отдельно от устройств stdin/stdout/SYS. Исторические имена
модулей и API vm1 сохранены. Прямой backend и целевой ABI принадлежат
[vm2/vm2compile](../vm2/doc/direct.md); здесь находятся общие примитивы
сборки, размещения, арифметики и планирования.
`copycode.vm2.arithmetic.add32` содержит общий переносный 32-битный
сумматор для символических генераторов; адреса scratch передаёт вызывающий
проект. Этот файл выделен из copy-space и сохраняет Apache-2.0.

- `copycode.vm1`: четыре индекса, ABI rev1; boot, bit packing, add8, SYS,
  кооперативные сообщения и снимки с явным продолжением;
  [общий планировщик и оптимизатор расписаний](doc/scheduling.md).
  Планировщик находится в `copycode.vm1.schedule`, необязательные
  преобразования — в отдельном `copycode.vm1.optimize`.
- `copycode.vm2`: сохранённый формат троек; boot/SYS/PCS1/PCS2/SPT1/SPT2,
  checkpoint и потоковый transport. Исполняется в том числе копикодом vm2 на vm1.
- `legacy/copy-space`: неподдерживаемый старый формат, сохранённый для миграции.

```sh
make -C ../vm1
make -C ../vm1 BACKEND=network
make -C ../vm2 legacy         # explicit native control for legacy SDK suites
make check
```

Исполняемые файлы задаются независимо от импорта:
`make check VM1=/path/bitcopy VM1_NETWORK=/path/network VM2=/path/space`.
Для схемы SYS можно задать `VM1_PROTO=/path/to/vm1/src/proto.def`.
Для импорта достаточно `PYTHONPATH=/path/copycode/src` либо установки Python
пакета. Никакие тестовые модули соседнего проекта не импортируются.

```python
from copycode.vm1.machine import Format
from copycode.vm1.program import Program
from copycode.vm1.lib import add8
f = Format()
p = Program(f)
layout = add8(p)
p.store(layout['left'], bytes([23, 47]))
p.layer([f.copy(8, f.channels['stdout'], layout['result'])])
# subprocess.run(['/path/vm1', '-p', '8'], input=p.boot()) -> b'F'
```

`make inventory` пересобирает манифесты API/получаемых образов; `make dist`
создаёт воспроизводимый исходный архив; `make distcheck` проверяет его отдельно; `make clean` удаляет результаты сборки.
[Контракты, происхождение и границы модулей](doc/README.md).
Компонент входит в общий исходный репозиторий copymachine; собственный remote
не создаётся. Публикация требует отдельного поручения.
Лицензии MIT/Apache-2.0 сохранены вместе с происхождением файлов.

Новый `../vm2/vm2` исполняет тройки копикодом vm1. Базовые boot/trace/
snapshot-проверки прошли и на нём. Полная матрица SDK с 256 МиБ образами
пока по умолчанию использует явный C-контроль `space`; для вложенной машины
нужно учитывать дополнительную память и время. Путь задаётся VM2.
