-include ../../tools/workspace.mk
BUILD_DIR ?= build
DISTDIR ?= dist
TMPDIR ?= $(CURDIR)/tmp
EMULATOR_BUILD_DIR ?= $(if $(and $(WORKSPACE_ROOT),$(filter $(WORKSPACE_ROOT)/emulator,$(EMULATOR_ROOT))),$(WORKSPACE_ROOT)/build/emulator/build,$(EMULATOR_ROOT)/build)
VM2_BUILD_DIR ?= $(if $(and $(WORKSPACE_ROOT),$(filter $(WORKSPACE_ROOT)/space/vm2,$(VM2_ROOT))),$(WORKSPACE_ROOT)/build/space/vm2/build,$(VM2_ROOT)/build)
.DELETE_ON_ERROR:
.DEFAULT_GOAL := all
.NOTPARALLEL:
PYTHON ?= python3
VM2_ROOT ?= $(if $(wildcard vendor/vm2/vm2compile),$(CURDIR)/vendor/vm2,$(abspath ../vm2))
EMULATOR_ROOT ?= $(if $(wildcard vendor/emulator/src/runtime.c),$(CURDIR)/vendor/emulator,$(if $(wildcard ../../emulator/src/runtime.c),$(abspath ../../emulator),$(abspath ../emulator)))
COPYCODE_ROOT ?= $(if $(wildcard vendor/copycode/src/copycode),$(CURDIR)/vendor/copycode,$(abspath ../copycode))
EMULATOR ?= $(EMULATOR_BUILD_DIR)/bitcopy/emulator
CHECKED_EMULATOR ?= $(VM2_BUILD_DIR)/checked-emulator
LIMIT_SECONDS ?= 180
LIMIT_MEMORY_MIB ?= 768
LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(LIMIT_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
ifeq ($(COPYMACHINE_LIMITED),1)
LIMIT =
endif
export VM2_ROOT EMULATOR_ROOT COPYCODE_ROOT EMULATOR CHECKED_EMULATOR
export PYTHONDONTWRITEBYTECODE=1
.PHONY: all check check-machine check-sdk dependencies benchmark dist distcheck clean
all: dependencies
	$(LIMIT) $(PYTHON) -B tools/build_example.py
dependencies:
	@test -d "$(VM2_ROOT)/vm2compile" -a -d "$(COPYCODE_ROOT)/src/copycode" || { echo 'Set VM2_ROOT and COPYCODE_ROOT' >&2; exit 1; }
	$(MAKE) -C "$(EMULATOR_ROOT)" -j1 runtime-bitcopy
	$(MAKE) -C "$(VM2_ROOT)" -j1 checked-emulator
check: check-machine check-sdk
check-machine: dependencies
	$(LIMIT) $(PYTHON) -B tests/test_direct.py
	$(LIMIT) $(PYTHON) -B tests/test_translate.py
check-sdk: dependencies
	$(LIMIT) $(PYTHON) -B tests/test_monitor.py
	$(LIMIT) $(PYTHON) -B tests/test_cli.py
	$(LIMIT) $(PYTHON) -B tests/test_schedule.py
benchmark: dependencies
	$(LIMIT) $(PYTHON) -B tools/benchmark.py
dist:
	$(PYTHON) -B tools/release.py create
distcheck: dist
	$(LIMIT) $(PYTHON) -B tools/release.py check
clean:
ifneq ($(WORKSPACE_ROOT),)
	python3 -B "$(WORKSPACE_ROOT)/tools/layout.py" --component "$(CURDIR)" --clean
else
	$(PYTHON) -B tools/release.py clean
endif
