# The language experiment (stage 14): the definition of the language is src/*.fth, a copy of the
# sources of kernel K; the host pForth executes it (boot) and writes L0.
BUILD_DIR ?= build
TMPDIR ?= $(CURDIR)/tmp
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.NOTPARALLEL:
PYTHON ?= python3
EMULATOR_ROOT ?= $(abspath ../emulator)
LIMITED_RUN ?= $(abspath ../tools/limited_run.py)
# The executor of check-programs, check-kernel and check-self (15.1): EMULATOR=path of an emulator binary, for
# example the one `make space` builds from the definition of the word "space" (space/). Empty: the
# working one (`make -C emulator checked` for check-programs, emulator/ for check-kernel).
EMULATOR ?=
export EMULATOR_ROOT EMULATOR
export PYTHONDONTWRITEBYTECODE=1
# L0 is written to the output directory of the component (language/build), the rest to BUILD_DIR.
OUT ?= $(BUILD_DIR)
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
SELF_SECONDS ?= 14000
TEST_SECONDS ?= 1800
CC ?= cc
CFLAGS ?= -Wall -Wextra -pedantic -std=c11 -O2
# The word "space": the text of its definition is emulator/src; `make space` builds from it the
# emulator $(SPACE_BIN).
SPACE_DIR = $(OUT)/space
SPACE_BIN = $(SPACE_DIR)/emulator
SPACE_SRC = $(EMULATOR_ROOT)/src
SPACE_SOURCES = $(wildcard $(SPACE_SRC)/*.c $(SPACE_SRC)/*.h) $(SPACE_SRC)/proto.def
limit = $(PYTHON) -B "$(LIMITED_RUN)" --seconds $(1) --memory-mib $(or $(2),768) --file-mib 64
ifeq ($(COPYMACHINE_LIMITED),1)
limit =
endif
SOURCES = $(wildcard src/*.fth)
TOOLS = $(wildcard tools/*.py)
.PHONY: all boot space check check-programs check-space-replace check-closure check-kernel check-self check-tests check-fast-tests check-language-md check-isolation check-proof check-replace check-user-programs clean
all: boot
boot: $(L0)
space: $(SPACE_BIN)
$(SPACE_BIN): $(SPACE_SOURCES) Makefile
	@mkdir -p "$(@D)"
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) $(addprefix $(SPACE_SRC)/,runtime.c sys_ctrl.c bitcopy.c backend_bitcopy.c) -o $@ $(LDLIBS)
$(L0): $(SOURCES) $(TOOLS)
	$(call limit,$(BOOT_SECONDS)) $(PYTHON) -B tools/boot.py -o "$(L0)"
check-programs:
	$(if $(EMULATOR),,$(call limit,600) $(MAKE) -C "$(EMULATOR_ROOT)" -j1 checked)
	$(call limit,$(PROGRAMS_SECONDS)) $(PYTHON) -B tools/check_programs.py $(if $(filter equal,$(STREAMS)),--streams-equal)
# Replacing the word "space" (15.4, 3.5.1 on the small value): the guest builds the emulator from the text of the
# definition (emulator/src) through EXEC and runs the programs of check-programs on it.
check-space-replace: $(SPACE_BIN)
	$(call limit,$(PROGRAMS_SECONDS)) $(PYTHON) -B tools/check_space_replace.py
check-closure:
	MAX_EXTERNAL=$(MAX_EXTERNAL) $(PYTHON) -B tools/check_closure.py
# doc/language.md (14.9): one record per word of the core, file:line and hash of the definition;
# 14.11: the prices of its colon definitions are those of the compiler (tests/test_word.py).
check-language-md:
	$(PYTHON) -B tools/language_md.py --check
check-kernel: $(L0)
	$(if $(EMULATOR),,$(call limit,600) $(MAKE) -C "$(EMULATOR_ROOT)" -j1 runtime-bitcopy)
	$(call limit,$(KERNEL_SECONDS)) $(PYTHON) -B tools/check_kernel.py --l0 "$(L0)"
# Self-compilation (14.15): L0 on the emulator compiles the definition of the language, L1 = L0
# (hours; run with --file-mib 64, L0 is larger than 16 MiB).
check-self: $(L0)
	$(if $(EMULATOR),,$(call limit,600) $(MAKE) -C "$(EMULATOR_ROOT)" -j1 runtime-bitcopy)
	$(call limit,$(SELF_SECONDS)) $(PYTHON) -B tools/check_self.py --l0 "$(L0)"
# The tests that need neither L0 nor the long runs (part of the root check-fast).
check-fast-tests:
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_provenance.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_closure.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_core.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_language_md.py
	$(call limit,$(TEST_SECONDS),1536) $(PYTHON) -B tests/test_long_copy.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_platform.py
check-tests: $(L0)
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_provenance.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_closure.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_core.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_boot.py
	$(call limit,600) $(MAKE) -C "$(EMULATOR_ROOT)" -j1 runtime-bitcopy
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_comments.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_literals.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_language_md.py
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_word.py
# Isolation of the kernel (14.10): probes of L0 (about 20 minutes), not part of check.
check-isolation: $(L0)
	$(call limit,$(KERNEL_SECONDS)) $(PYTHON) -B tests/test_isolation.py --l0 "$(L0)"
# Check and proof (14.12): CHECK-TABLE, ACCURACY, PROVED? on the checked emulator and on L0 (about 3 minutes).
check-proof: $(L0)
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_proof.py
# Replacement and synonyms (14.13): REPLACE, synonyms, the price from the concept cell on the counters
# and L0 (about 5 minutes).
check-replace: $(L0)
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_replace.py
# User programs do not get dearer (14.14): tools/user_programs.py recompiles the programs of the user
# with a recompiled language and keeps the previous code if the new one is dearer (about 1 minute).
check-user-programs:
	$(call limit,$(TEST_SECONDS)) $(PYTHON) -B tests/test_user_programs.py
check: check-programs check-closure check-tests check-language-md
clean:
	rm -rf "$(BUILD_DIR)"
