.DEFAULT_GOAL := all
.NOTPARALLEL:
PYTHON ?= python3
JOBS ?= 1
LIMIT = $(PYTHON) -B space/vm2/tools/limited_run.py --seconds 600 --memory-mib 768
.PHONY: all layout emulator forth run-forth check check-layout clean
all: forth
layout:
	$(PYTHON) -B tools/layout.py
emulator: layout
	$(LIMIT) $(MAKE) -C emulator -j1
forth: emulator
	$(LIMIT) $(MAKE) -C space/forth -j1
run-forth:
	./tools/run/forth
check-archive:
	$(PYTHON) -B tools/check_archive.py
check-layout:
	$(PYTHON) -B tools/check_layout.py
check: layout
	$(LIMIT) $(MAKE) -C emulator -j1 check-runtime
	$(LIMIT) $(MAKE) -C space/copycode -j1 check-emulator
	$(LIMIT) $(MAKE) -C space/vm2 -j1 check
	$(PYTHON) -B space/vm2/tools/limited_run.py --seconds 600 --memory-mib 768 --cpus $(JOBS) $(MAKE) -C space/rv32i -j1 check JOBS=$(JOBS)
	$(PYTHON) -B space/vm2/tools/limited_run.py --seconds 3600 --memory-mib 768 --cpus $(JOBS) $(MAKE) -C space/forth -j1 check JOBS=$(JOBS)
	$(MAKE) check-layout
clean:
	$(PYTHON) -B tools/layout.py --clean

.PHONY: check-detached
check-detached:
	$(PYTHON) -B space/vm2/tools/limited_run.py --seconds 1800 --memory-mib 768 --file-mib 512 $(PYTHON) -B tools/test/detached.py $(DETACHED_FLAGS)
