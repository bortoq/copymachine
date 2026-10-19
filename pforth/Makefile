.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.NOTPARALLEL:
PYTHON ?= python3
RV32I_ROOT ?= $(if $(wildcard vendor/rv32i),$(CURDIR)/vendor/rv32i,$(abspath ../rv32i))
VM2_ROOT ?= $(if $(wildcard vendor/vm2),$(CURDIR)/vendor/vm2,$(abspath ../vm2))
VM1_ROOT ?= $(if $(wildcard vendor/vm1),$(CURDIR)/vendor/vm1,$(abspath ../vm1))
COPYCODE_ROOT ?= $(if $(wildcard vendor/copycode),$(CURDIR)/vendor/copycode,$(abspath ../copycode))
VM1 ?= $(VM1_ROOT)/build/bitcopy/vm1
LIMIT_SECONDS ?= 180
LIMIT_MEMORY_MIB ?= 768
TEST_SECONDS ?= 360
BENCH_SECONDS ?= 420
BENCH_LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(BENCH_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
TEST_LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(TEST_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
export PFORTH_TEST_SECONDS=$(TEST_SECONDS)
LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(LIMIT_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
ifeq ($(COPYMACHINE_LIMITED),1)
LIMIT =
TEST_LIMIT =
BENCH_LIMIT =
endif
export RV32I_ROOT VM2_ROOT VM1_ROOT COPYCODE_ROOT VM1
export PYTHONDONTWRITEBYTECODE=1
.PHONY: benchmark all dependencies check prepare-check clean check-release dist distcheck initialize-tests
all: dependencies build/pforth/manifest.json
dependencies:
	$(MAKE) -C "$(VM1_ROOT)" -j1 build/bitcopy/vm1
build/pforth/manifest.json: $(wildcard $(RV32I_ROOT)/modules/*.py $(VM2_ROOT)/vm2compile/*.py $(COPYCODE_ROOT)/src/copycode/vm1/*.py) $(wildcard scripts/pforth/*.py) $(wildcard runtime/pforth/*.c runtime/pforth/*.h) runtime/pforth/pfdicdat.h runtime/pforth/pfdicdat.h.json $(wildcard runtime/pforth/compat/*.h runtime/pforth/compat/sys/*.h third_party/pforth/csrc/*.c third_party/pforth/csrc/*.h third_party/pforth/csrc/paging/*.c third_party/pforth/csrc/paging/*.h)
	rm -rf build/pforth
	$(LIMIT) $(PYTHON) -B pforth build -o build/pforth
check: all build/observe-vm1 initialize-tests
	$(LIMIT) $(PYTHON) -B tests/test_index.py
	$(LIMIT) $(PYTHON) -B tests/test_identity.py
	$(LIMIT) $(PYTHON) -B tests/test_jobs.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case language
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case language-control
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case language-memory
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case index-semantics
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case index-length
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case eof
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case unknown
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case unfinished
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case long-line
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case input-error
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case output-error
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case job

	$(MAKE) -j1 check-native

prepare-check:
	$(LIMIT) $(PYTHON) -B pforth prepare-check
clean:
	rm -rf build dist

check-release: all build/observe-vm1 initialize-tests
	$(LIMIT) $(PYTHON) -B tests/test_index.py
	$(LIMIT) $(PYTHON) -B tests/test_identity.py
	$(LIMIT) $(PYTHON) -B tests/test_jobs.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case job
	$(MAKE) -j1 check-native
dist:
	$(PYTHON) -B tools/release.py create
distcheck: dist
	$(LIMIT) $(PYTHON) -B tools/release.py check

CC ?= cc
build/observe-vm1: tests/observe_vm1.c Makefile FORCE
	@mkdir -p build
	$(CC) -O2 -Wall -DVM1_NO_MAIN -I"$(VM1_ROOT)/src" tests/observe_vm1.c "$(VM1_ROOT)/src/runtime.c" "$(VM1_ROOT)/src/sys_ctrl.c" "$(VM1_ROOT)/src/bitcopy.c" "$(VM1_ROOT)/src/backend_bitcopy.c" -o $@

initialize-tests: build/initialized/manifest.json
build/initialized/manifest.json: build/pforth/manifest.json build/observe-vm1 tools/prepare_test_image.py
	$(LIMIT) $(PYTHON) -B tools/prepare_test_image.py

.PHONY: FORCE
FORCE:

benchmark: all build/observe-vm1
	$(BENCH_LIMIT) $(PYTHON) -B tools/benchmark.py

.PHONY: check-native
check-native: all
	$(MAKE) -C "$(VM2_ROOT)" -j1 build/checked-vm1
	$(LIMIT) $(PYTHON) -B tests/test_native_audit.py
