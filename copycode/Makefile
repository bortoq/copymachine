.DEFAULT_GOAL := check
PYTHON ?= python3
VM1 ?= ../vm1/vm1
VM1_NETWORK ?= ../vm1/build/network/vm1
VM2 ?= ../vm2/space
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH := $(CURDIR)/src
.PHONY: check check-vm1 check-vm2 inventory clean dist distcheck
check: check-vm1 check-vm2
check-vm1:
	$(PYTHON) -B tests/test_schedule.py
	VM1="$(abspath $(VM1))" VM1_NETWORK="$(abspath $(VM1_NETWORK))" $(PYTHON) -B tests/test_vm1.py
check-vm2:
	@set -e; for name in machine schedule boundary transport checkpoint dynamic_trace; do \
	  SPACE_EMULATOR="$(abspath $(VM2))" $(PYTHON) -B tests/vm2/test_$$name.py; \
	done
inventory:
	$(PYTHON) -B tools/manifest.py
clean:
	rm -rf build dist *.egg-info src/*.egg-info
	find src tests compat -type d -name __pycache__ -prune -exec rm -rf {} +
dist:
	$(PYTHON) -B tools/package.py

distcheck: dist
	$(PYTHON) -B tools/check_dist.py
