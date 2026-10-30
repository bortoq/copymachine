BUILD_DIR ?= build
TMPDIR ?= $(CURDIR)/tmp
.DELETE_ON_ERROR:
.NOTPARALLEL:
.DEFAULT_GOAL := all
export PYTHONDONTWRITEBYTECODE=1
CC      ?= cc
CFLAGS  ?= -Wall -Wextra -pedantic -std=c11 -O2
export CC CPPFLAGS CFLAGS LDFLAGS LDLIBS

# One emulator: four-index runtime, bitcopy, the long copy LONG (-r) and SYS.
SRC_COMMON = src/runtime.c src/sys_ctrl.c src/bitcopy.c src/backend_bitcopy.c
HEADERS = src/space.h src/sys_ctrl.h src/proto_gen.h
OUT = $(BUILD_DIR)/bitcopy
BUILD_CONFIG = $(OUT)/build-config

.PHONY: all emulator pgo FORCE check check-runtime checked runtime-bitcopy coverage clean help
all: emulator
FORCE:

$(BUILD_CONFIG): FORCE
	@mkdir -p "$(@D)"
	@printf '%s\n' "$$CC" "$$CPPFLAGS" "$$CFLAGS" "$$LDFLAGS" "$$LDLIBS" > "$@.tmp"
	@cmp -s "$@.tmp" "$@" && rm -f "$@.tmp" || mv "$@.tmp" "$@"

$(OUT)/emulator: $(SRC_COMMON) $(HEADERS) $(BUILD_CONFIG) Makefile
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) $(SRC_COMMON) -o $@ $(LDLIBS)

$(OUT)/test_runtime: tests/test_runtime.c $(SRC_COMMON) $(HEADERS) $(BUILD_CONFIG) Makefile
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -DVM1_NO_MAIN tests/test_runtime.c src/runtime.c src/sys_ctrl.c src/bitcopy.c src/backend_bitcopy.c -o $@ $(LDLIBS)

$(OUT)/test_sys: tests/test_runtime_sys.c $(SRC_COMMON) $(HEADERS) $(BUILD_CONFIG) Makefile
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -DVM1_NO_MAIN tests/test_runtime_sys.c src/runtime.c src/sys_ctrl.c src/bitcopy.c src/backend_bitcopy.c -o $@ $(LDLIBS)

$(BUILD_DIR)/test_bitcopy: tests/test_runtime_bitcopy.c src/bitcopy.c src/space.h $(BUILD_CONFIG)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/test_runtime_bitcopy.c src/bitcopy.c -o $@ $(LDLIBS)

# The mode of checking disjointness: the same emulator, after each tick an independent audit of the
# processor (no two intervals of the tick overlap). Test-only, never installed.
$(BUILD_DIR)/checked-emulator: tests/checked_vm1.c $(SRC_COMMON) $(HEADERS) $(BUILD_CONFIG) Makefile
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -DVM1_NO_MAIN -I src tests/checked_vm1.c src/runtime.c src/sys_ctrl.c src/bitcopy.c src/backend_bitcopy.c -o $@ $(LDLIBS)

emulator: $(OUT)/emulator FORCE
	ln -sf "$<" emulator.tmp
	mv emulator.tmp emulator

runtime-bitcopy: $(OUT)/emulator

# Optional (18.10): the emulator built with profile-guided optimization (gcc), about 30% faster per tick.
# Training: L0 of language compiles a small program (the first PGO_TICKS ticks); the result is
# $(BUILD_DIR)/pgo/emulator. Neither all, check nor CI depend on it.
PGO = $(BUILD_DIR)/pgo
PGO_L0 ?= $(CURDIR)/../language/build/L0.boot
PGO_TICKS ?= 3000000
PGO_FLAGS = $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) $(addprefix $(CURDIR)/,$(SRC_COMMON)) -o emulator $(LDLIBS)
pgo: $(HEADERS) Makefile
	$(MAKE) -C ../language boot
	rm -rf "$(PGO)"
	mkdir -p "$(PGO)"
	cd "$(PGO)" && $(CC) $(PGO_FLAGS) -fprofile-generate -fprofile-update=single
	{ cat "$(PGO_L0)"; printf ': main 65 emit 3 4 + 60 + emit 100 33 - emit 6 7 and 64 or emit 70 3 xor emit ;\0'; } | \
	  (cd "$(PGO)" && ./emulator -s 2147483648 -p 8 -t $(PGO_TICKS) >/dev/null)
	cd "$(PGO)" && $(CC) $(PGO_FLAGS) -fprofile-use -fprofile-partial-training -Wno-missing-profile

check: check-runtime
check-runtime: $(OUT)/emulator $(OUT)/test_runtime $(OUT)/test_sys $(BUILD_DIR)/test_bitcopy
	$(BUILD_DIR)/test_bitcopy
	$(OUT)/test_runtime
	$(OUT)/test_sys
	python3 -B tests/test_runtime_cli.py

checked: $(BUILD_DIR)/checked-emulator

# Line coverage (17.9): every test binary and the emulator built with gcov, the CLI test on the
# instrumented emulator; the lines of src/*.c executed by any of them are united.
COV = $(BUILD_DIR)/cov
COVFLAGS = -std=c11 -O0 -g --coverage
coverage:
	rm -rf "$(COV)"
	mkdir -p "$(COV)/emulator" "$(COV)/test_runtime" "$(COV)/test_sys" "$(COV)/test_bitcopy"
	cd "$(COV)/emulator" && $(CC) $(COVFLAGS) $(addprefix $(CURDIR)/,$(SRC_COMMON)) -o emulator
	cd "$(COV)/test_runtime" && $(CC) $(COVFLAGS) -DVM1_NO_MAIN $(CURDIR)/tests/test_runtime.c $(addprefix $(CURDIR)/,$(SRC_COMMON)) -o t
	cd "$(COV)/test_sys" && $(CC) $(COVFLAGS) -DVM1_NO_MAIN $(CURDIR)/tests/test_runtime_sys.c $(addprefix $(CURDIR)/,$(SRC_COMMON)) -o t
	cd "$(COV)/test_bitcopy" && $(CC) $(COVFLAGS) $(CURDIR)/tests/test_runtime_bitcopy.c $(CURDIR)/src/bitcopy.c -o t
	cd && $(CC) $(COVFLAGS) -DVM1_NO_MAIN -I $(CURDIR)/src $(CURDIR)/tests/checked_vm1.c $(addprefix $(CURDIR)/,$(SRC_COMMON)) -o t
	for t in test_bitcopy test_runtime test_sys; do (cd "$(COV)/$$t" && ./t >/dev/null); done
	EMULATOR_BIN="$(CURDIR)/$(COV)/emulator/emulator" python3 -B tests/test_runtime_cli.py
	@python3 -B ../tools/gcov_summary.py "$(COV)" $(SRC_COMMON)
clean:
	rm -rf "$(BUILD_DIR)"
	rm -f emulator emulator.tmp

help:
	@echo "Targets: all (emulator), check, checked (audit build), pgo (optional, gcc), clean"

src/proto_gen.h: src/proto.def tools/proto_gen.py
	python3 -B tools/proto_gen.py src/proto.def src/proto_gen.h
