-include ../../tools/workspace.mk
# The language experiment (stage 14): the definition of the language is src/*.fth, a copy of the
# sources of kernel K; the host pForth executes it (boot) and writes L0.
BUILD_DIR ?= build
TMPDIR ?= $(CURDIR)/tmp
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.NOTPARALLEL:
PYTHON ?= python3
VM2_ROOT ?= $(abspath ../vm2)
EMULATOR_ROOT ?= $(abspath ../../emulator)
COPYCODE_ROOT ?= $(abspath ../copycode)
FORTH_ROOT ?= $(abspath ../forth)
export VM2_ROOT EMULATOR_ROOT COPYCODE_ROOT FORTH_ROOT
export PYTHONDONTWRITEBYTECODE=1
# L0 is written to the output directory of the component (build/space/language), the rest to BUILD_DIR.
OUT ?= $(if $(WORKSPACE_ROOT),$(WORKSPACE_ROOT)/build/$(WORKSPACE_COMPONENT),$(BUILD_DIR))
L0 ?= $(OUT)/L0.boot
# The number of names used in the definition and not defined in it (14.1: 58 in the sources of K
# without the auxiliary libraries of copycode/forth; 68 with them, docs/research/definition-graph.md;
# 14.3: 39, the 19 words of the generators of src/primitives.fth are defined; 14.4: 19, 20 more;
# 14.5: 2, the control words are generators: DECIMAL and KERNEL-LAYOUT remain; 14.6: 0, the
# defining words, ( [CHAR] S" DECIMAL KERNEL-LAYOUT are generators too; 14.7: 0, the digits and
# LITERAL, used by the numbers of the definition, are defined too; 14.8: 0, the comment word \ is a
# generator too, check-closure writes doc/core.md, the core of the language).
MAX_EXTERNAL ?= 0
STREAMS ?=
BOOT_SECONDS ?= 600
PROGRAMS_SECONDS ?= 1800
KERNEL_SECONDS ?= 12000
TEST_SECONDS ?= 1800
limit = $(PYTHON) -B "$(VM2_ROOT)/tools/limited_run.py" --seconds $(1) --memory-mib 768
ifeq ($(COPYMACHINE_LIMITED),1)
limit =
endif
SOURCES = $(wildcard src/*.fth)
TOOLS = $(wildcard tools/*.py)
.PHONY: all boot check check-programs check-closure check-kernel check-tests check-language-md check-isolation clean
all: boot
boot: $(L0)
$(L0): $(SOURCES) $(TOOLS)
	$(call limit,$(BOOT_SECONDS)) $(PYTHON) -B tools/boot.py -o "$(L0)"
check-programs:
	$(call limit,600) $(MAKE) -C "$(VM2_ROOT)" -j1 checked-emulator
	$(call limit,$(PROGRAMS_SECONDS)) $(PYTHON) -B tools/check_programs.py $(if $(filter equal,$(STREAMS)),--streams-equal)
check-closure:
	MAX_EXTERNAL=$(MAX_EXTERNAL) $(PYTHON) -B tools/check_closure.py
# doc/language.md (14.9): one record per word of the core, file:line and hash of the definition.
check-language-md:
	$(PYTHON) -B tools/language_md.py --check
check-kernel: $(L0)
	$(call limit,600) $(MAKE) -C "$(EMULATOR_ROOT)" -j1 runtime-bitcopy
	$(call limit,$(KERNEL_SECONDS)) $(PYTHON) -B tools/check_kernel.py --l0 "$(L0)"
check-tests: $(L0)
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_provenance.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_closure.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_core.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_boot.py
	$(call limit,600) $(MAKE) -C "$(EMULATOR_ROOT)" -j1 runtime-bitcopy
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_comments.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_literals.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_language_md.py
# Isolation of the kernel (14.10): probes of L0 (about 20 minutes), not part of check.
check-isolation: $(L0)
	$(call limit,$(KERNEL_SECONDS)) $(PYTHON) -B tests/test_isolation.py --l0 "$(L0)"
check: check-programs check-closure check-tests check-language-md
clean:
ifneq ($(WORKSPACE_ROOT),)
	rm -rf "$(BUILD_DIR)" "$(L0)"
else
	rm -rf "$(BUILD_DIR)"
endif
