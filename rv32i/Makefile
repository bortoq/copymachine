.DELETE_ON_ERROR:
.DEFAULT_GOAL := all
.NOTPARALLEL:
PYTHON ?= python3
VM2_ROOT ?= $(if $(wildcard vendor/vm2/vm2compile),$(CURDIR)/vendor/vm2,$(abspath ../vm2))
VM1_ROOT ?= $(if $(wildcard vendor/vm1/src/runtime.c),$(CURDIR)/vendor/vm1,$(abspath ../vm1))
COPYCODE_ROOT ?= $(if $(wildcard vendor/copycode/src/copycode),$(CURDIR)/vendor/copycode,$(abspath ../copycode))
VM1 ?= $(VM1_ROOT)/build/bitcopy/vm1
CHECKED_VM1 ?= $(VM2_ROOT)/build/checked-vm1
LIMIT_SECONDS ?= 180
LIMIT_MEMORY_MIB ?= 768
LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(LIMIT_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
ifeq ($(COPYMACHINE_LIMITED),1)
LIMIT =
endif
export VM2_ROOT VM1_ROOT COPYCODE_ROOT VM1 CHECKED_VM1
export PYTHONDONTWRITEBYTECODE=1
.PHONY: all check check-machine check-sdk dependencies benchmark dist distcheck clean
all: dependencies
	$(LIMIT) $(PYTHON) -B tools/build_example.py
dependencies:
	@test -d "$(VM2_ROOT)/vm2compile" -a -d "$(COPYCODE_ROOT)/src/copycode" || { echo 'Set VM2_ROOT and COPYCODE_ROOT' >&2; exit 1; }
	$(MAKE) -C "$(VM1_ROOT)" -j1 build/bitcopy/vm1
	$(MAKE) -C "$(VM2_ROOT)" -j1 build/checked-vm1
check: check-machine check-sdk
check-machine: dependencies
	$(LIMIT) $(PYTHON) -B tests/test_direct.py
check-sdk: dependencies
	$(LIMIT) $(PYTHON) -B tests/test_monitor.py
	$(LIMIT) $(PYTHON) -B tests/test_cli.py
	$(LIMIT) $(PYTHON) -B tests/test_schedule.py
	$(LIMIT) $(PYTHON) -B tests/test_rv32i_bulk_schedule.py
benchmark: dependencies
	$(LIMIT) $(PYTHON) -B tools/benchmark.py
dist:
	$(PYTHON) -B tools/release.py create
distcheck: dist
	$(LIMIT) $(PYTHON) -B tools/release.py check
clean:
	$(PYTHON) -B tools/release.py clean
