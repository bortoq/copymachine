-include ../../tools/workspace.mk
BUILD_DIR ?= build
DISTDIR ?= dist
TMPDIR ?= $(CURDIR)/tmp
EMULATOR_BUILD_DIR ?= $(if $(and $(WORKSPACE_ROOT),$(filter $(WORKSPACE_ROOT)/emulator,$(EMULATOR_ROOT))),$(WORKSPACE_ROOT)/build/emulator/build,$(EMULATOR_ROOT)/build)
VM2_BUILD_DIR ?= $(if $(and $(WORKSPACE_ROOT),$(filter $(WORKSPACE_ROOT)/space/vm2,$(VM2_ROOT))),$(WORKSPACE_ROOT)/build/space/vm2/build,$(VM2_ROOT)/build)
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.NOTPARALLEL:
PYTHON ?= python3
RV32I_ROOT ?= $(if $(wildcard vendor/rv32i),$(CURDIR)/vendor/rv32i,$(abspath ../rv32i))
VM2_ROOT ?= $(if $(wildcard vendor/vm2),$(CURDIR)/vendor/vm2,$(abspath ../vm2))
EMULATOR_ROOT ?= $(if $(wildcard vendor/emulator),$(CURDIR)/vendor/emulator,$(if $(wildcard ../../emulator/src/runtime.c),$(abspath ../../emulator),$(abspath ../emulator)))
COPYCODE_ROOT ?= $(if $(wildcard vendor/copycode),$(CURDIR)/vendor/copycode,$(abspath ../copycode))
EMULATOR ?= $(EMULATOR_BUILD_DIR)/bitcopy/emulator
LIMIT_SECONDS ?= 180
LIMIT_MEMORY_MIB ?= 768
TEST_SECONDS ?= 360
BENCH_SECONDS ?= 420
RELEASE_SECONDS ?= 900
BITFIELD_SECONDS ?= 600
INSTRUCTION_SECONDS ?= 600
OPERATION_SECONDS ?= 1500
OPERATION_LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(OPERATION_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
INSTRUCTION_LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(INSTRUCTION_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
BITFIELD_LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(BITFIELD_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
BENCH_LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(BENCH_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
RELEASE_LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(RELEASE_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
TEST_LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(TEST_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
export PFORTH_TEST_SECONDS=$(TEST_SECONDS)
export PFORTH_BITFIELD_SECONDS=$(BITFIELD_SECONDS)
export PFORTH_INSTRUCTION_SECONDS=$(INSTRUCTION_SECONDS)
LIMIT = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(LIMIT_SECONDS) --memory-mib $(LIMIT_MEMORY_MIB)
ifeq ($(COPYMACHINE_LIMITED),1)
LIMIT =
TEST_LIMIT =
BENCH_LIMIT =
RELEASE_LIMIT =
BITFIELD_LIMIT =
INSTRUCTION_LIMIT =
OPERATION_LIMIT =
endif
export RV32I_ROOT VM2_ROOT EMULATOR_ROOT COPYCODE_ROOT EMULATOR
export PYTHONDONTWRITEBYTECODE=1
.PHONY: benchmark all dependencies check check-bitfields check-instructions check-instruction-decode check-integers check-libraries prepare-check clean check-release dist distcheck initialize-tests
all: dependencies $(BUILD_DIR)/pforth/manifest.json
dependencies:
	$(MAKE) -C "$(EMULATOR_ROOT)" -j1 runtime-bitcopy
$(BUILD_DIR)/pforth/manifest.json: $(wildcard $(RV32I_ROOT)/modules/*.py $(VM2_ROOT)/vm2compile/*.py $(COPYCODE_ROOT)/src/copycode/vm1/*.py) $(wildcard scripts/pforth/*.py) $(wildcard runtime/pforth/*.c runtime/pforth/*.h) runtime/pforth/pfdicdat.h runtime/pforth/pfdicdat.h.json $(wildcard runtime/pforth/compat/*.h runtime/pforth/compat/sys/*.h third_party/pforth/csrc/*.c third_party/pforth/csrc/*.h third_party/pforth/csrc/paging/*.c third_party/pforth/csrc/paging/*.h)
	rm -rf $(BUILD_DIR)/pforth
	$(LIMIT) $(PYTHON) -B pforth build -o $(BUILD_DIR)/pforth
check: all $(BUILD_DIR)/observe-emulator initialize-tests
	$(TEST_LIMIT) $(PYTHON) -B tests/test_integers.py
	$(BITFIELD_LIMIT) $(PYTHON) -B tests/test_bitfields.py
	$(INSTRUCTION_LIMIT) $(PYTHON) -B tests/test_instructions.py
	$(INSTRUCTION_LIMIT) $(PYTHON) -B tests/test_instruction_decode.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_arena.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_evaluate.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_format.py
	$(OPERATION_LIMIT) $(PYTHON) -B tests/test_operations.py
	$(OPERATION_LIMIT) $(PYTHON) -B tests/test_backend.py
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
check-bitfields: all $(BUILD_DIR)/observe-emulator initialize-tests
	$(BITFIELD_LIMIT) $(PYTHON) -B tests/test_bitfields.py
check-instructions: all $(BUILD_DIR)/observe-emulator initialize-tests
	$(INSTRUCTION_LIMIT) $(PYTHON) -B tests/test_instructions.py
check-instruction-decode: all $(BUILD_DIR)/observe-emulator initialize-tests
	$(INSTRUCTION_LIMIT) $(PYTHON) -B tests/test_instruction_decode.py
check-libraries: all $(BUILD_DIR)/observe-emulator initialize-tests
	$(TEST_LIMIT) $(PYTHON) -B tests/test_arena.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_evaluate.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_format.py
	$(OPERATION_LIMIT) $(PYTHON) -B tests/test_operations.py
	$(OPERATION_LIMIT) $(PYTHON) -B tests/test_backend.py
check-integers: all $(BUILD_DIR)/observe-emulator initialize-tests
	$(TEST_LIMIT) $(PYTHON) -B tests/test_integers.py
clean:
ifneq ($(WORKSPACE_ROOT),)
	python3 -B "$(WORKSPACE_ROOT)/tools/layout.py" --component "$(CURDIR)" --clean
else
	rm -rf "$(BUILD_DIR)" "$(DISTDIR)"

endif
check-release: all $(BUILD_DIR)/observe-emulator initialize-tests
	$(TEST_LIMIT) $(PYTHON) -B tests/test_integers.py
	$(BITFIELD_LIMIT) $(PYTHON) -B tests/test_bitfields.py
	$(INSTRUCTION_LIMIT) $(PYTHON) -B tests/test_instructions.py
	$(INSTRUCTION_LIMIT) $(PYTHON) -B tests/test_instruction_decode.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_arena.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_evaluate.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_format.py
	$(OPERATION_LIMIT) $(PYTHON) -B tests/test_operations.py
	$(OPERATION_LIMIT) $(PYTHON) -B tests/test_backend.py
	$(LIMIT) $(PYTHON) -B tests/test_index.py
	$(LIMIT) $(PYTHON) -B tests/test_identity.py
	$(LIMIT) $(PYTHON) -B tests/test_jobs.py
	$(TEST_LIMIT) $(PYTHON) -B tests/test_direct.py --case job
	$(MAKE) -j1 check-native
dist:
	$(PYTHON) -B tools/release.py create
distcheck: dist
	$(RELEASE_LIMIT) $(PYTHON) -B tools/release.py check

CC ?= cc
$(BUILD_DIR)/observe-emulator: tests/observe_vm1.c Makefile FORCE
	@mkdir -p "$(BUILD_DIR)"
	$(CC) -O2 -Wall -DVM1_NO_MAIN -I"$(EMULATOR_ROOT)/src" tests/observe_vm1.c "$(EMULATOR_ROOT)/src/runtime.c" "$(EMULATOR_ROOT)/src/sys_ctrl.c" "$(EMULATOR_ROOT)/src/bitcopy.c" "$(EMULATOR_ROOT)/src/backend_bitcopy.c" -o $@

initialize-tests: $(BUILD_DIR)/initialized/manifest.json
$(BUILD_DIR)/initialized/manifest.json: $(BUILD_DIR)/pforth/manifest.json $(BUILD_DIR)/observe-emulator tools/prepare_test_image.py
	$(LIMIT) $(PYTHON) -B tools/prepare_test_image.py

.PHONY: FORCE
FORCE:

benchmark: all $(BUILD_DIR)/observe-emulator
	$(BENCH_LIMIT) $(PYTHON) -B tools/benchmark.py

.PHONY: check-native
check-native: all
	$(MAKE) -C "$(VM2_ROOT)" -j1 checked-emulator
	$(LIMIT) $(PYTHON) -B tests/test_native_audit.py
