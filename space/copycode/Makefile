-include ../../tools/workspace.mk
BUILD_DIR ?= build
DISTDIR ?= dist
TMPDIR ?= $(CURDIR)/tmp
EMULATOR_BUILD_DIR ?= $(if $(and $(WORKSPACE_ROOT),$(filter $(WORKSPACE_ROOT)/emulator,$(EMULATOR_ROOT))),$(WORKSPACE_ROOT)/build/emulator/build,$(EMULATOR_ROOT)/build)
VM2_BUILD_DIR ?= $(if $(and $(WORKSPACE_ROOT),$(filter $(WORKSPACE_ROOT)/space/vm2,$(VM2_ROOT))),$(WORKSPACE_ROOT)/build/space/vm2/build,$(VM2_ROOT)/build)
.DEFAULT_GOAL := check
PYTHON ?= python3
VM2_ROOT ?= $(abspath ../vm2)
EMULATOR_ROOT ?= $(if $(wildcard ../../emulator/src/runtime.c),$(abspath ../../emulator),$(abspath ../emulator))
EMULATOR ?= $(EMULATOR_BUILD_DIR)/bitcopy/emulator
EMULATOR_NETWORK ?= $(EMULATOR_BUILD_DIR)/network/emulator
VM2 ?= $(VM2_BUILD_DIR)/reference-space
EMULATOR_PROTO ?= $(EMULATOR_ROOT)/src/proto.def
export EMULATOR_ROOT EMULATOR_PROTO
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH := $(CURDIR)/src
.PHONY: check check-emulator check-vm2 inventory clean dist distcheck
check: check-emulator check-vm2
check-emulator:
	$(PYTHON) -B tests/test_schedule.py
	EMULATOR="$(abspath $(EMULATOR))" EMULATOR_NETWORK="$(abspath $(EMULATOR_NETWORK))" $(PYTHON) -B tests/test_vm1.py
check-vm2:
	@set -e; for name in machine schedule boundary transport checkpoint dynamic_trace; do \
	  SPACE_EMULATOR="$(abspath $(VM2))" $(PYTHON) -B tests/vm2/test_$$name.py; \
	done
inventory:
	$(PYTHON) -B tools/manifest.py
clean:
ifneq ($(WORKSPACE_ROOT),)
	python3 -B "$(WORKSPACE_ROOT)/tools/layout.py" --component "$(CURDIR)" --clean
else
	rm -rf "$(BUILD_DIR)" "$(DISTDIR)" *.egg-info src/*.egg-info
	find src tests compat -type d -name __pycache__ -prune -exec rm -rf {} +
endif
dist:
	$(PYTHON) -B tools/package.py

distcheck: dist
	$(PYTHON) -B tools/check_dist.py
