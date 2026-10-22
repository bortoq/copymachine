-include ../../tools/workspace.mk
BUILD_DIR ?= build
DISTDIR ?= dist
TMPDIR ?= $(CURDIR)/tmp
EMULATOR_BUILD_DIR ?= $(if $(and $(WORKSPACE_ROOT),$(filter $(WORKSPACE_ROOT)/emulator,$(EMULATOR_ROOT))),$(WORKSPACE_ROOT)/build/emulator/build,$(EMULATOR_ROOT)/build)
VM2_BUILD_DIR ?= $(if $(and $(WORKSPACE_ROOT),$(filter $(WORKSPACE_ROOT)/space/vm2,$(VM2_ROOT))),$(WORKSPACE_ROOT)/build/space/vm2/build,$(VM2_ROOT)/build)
.DELETE_ON_ERROR:
.DEFAULT_GOAL := all
ifeq ($(origin CC),default)
CC := gcc
endif
CFLAGS ?= -std=c11 -Wall -Wextra -O3
CPPFLAGS ?=
LDFLAGS ?=
LDLIBS ?=
COPYCODE_ROOT ?= $(if $(wildcard vendor/copycode/src/copycode),$(CURDIR)/vendor/copycode,$(abspath ../copycode))
EMULATOR_ROOT ?= $(if $(wildcard vendor/emulator/src/runtime.c),$(CURDIR)/vendor/emulator,$(if $(wildcard ../../emulator/src/runtime.c),$(abspath ../../emulator),$(abspath ../emulator)))
EMULATOR ?= $(EMULATOR_BUILD_DIR)/bitcopy/emulator
export COPYCODE_ROOT EMULATOR_ROOT EMULATOR CC CPPFLAGS CFLAGS LDFLAGS LDLIBS SPACE_TEST_ASAN
export PYTHONDONTWRITEBYTECODE=1
export VM2_CACHE=$(BUILD_DIR)/guest-cache
export SPACE_EMULATOR = $(LEGACY_EMULATOR)
export TMPDIR
BIN ?= $(BUILD_DIR)/reference-space
LEGACY_EMULATOR ?= $(BIN)
REFERENCE = tests/reference
COMMON = $(REFERENCE)/globals.c $(REFERENCE)/bitcopy.c
ENGINE = $(REFERENCE)/engine.c $(REFERENCE)/config.c $(REFERENCE)/sys_ctrl.c $(COMMON)
GEN = tools/proto_gen.py
VERSION := $(shell cat VERSION)
prefix ?= /usr/local
bindir ?= $(prefix)/bin
libdir ?= $(prefix)/libexec/vm2
docdir ?= $(prefix)/share/doc/vm2
DISTDIR ?= dist
DIST_ARCHIVE = $(DISTDIR)/vm2-$(VERSION).tar.gz
BENCH_OUTPUT ?= $(BUILD_DIR)/benchmarks/guest
BENCH_REPEATS ?= 5
BENCH_TICKS ?= 32
BENCH_SECONDS ?= 180
BENCH_MEMORY_MIB ?= 768
BENCH_LIMIT = python3 -B tools/limited_run.py --seconds $(BENCH_SECONDS) --memory-mib $(BENCH_MEMORY_MIB)
GUEST_S ?= 65520
GUEST_P ?= 64

.PHONY: all direct check-direct benchmark-direct guest emulator-ready FORCE check check-guest check-legacy check-built check-core legacy install dist check-dist distcheck benchmark clean test-tmp
all: direct

direct: emulator-ready
	python3 -B tools/build_direct_example.py
emulator-ready: | test-tmp
	@test -d "$(COPYCODE_ROOT)/src/copycode" || { echo 'Set COPYCODE_ROOT to the copycode project' >&2; exit 1; }
	@if [ ! -x "$(EMULATOR)" ]; then $(MAKE) -C "$(EMULATOR_ROOT)" runtime-bitcopy; fi
guest: emulator-ready
	python3 -B -m vm2guest.build -s $(GUEST_S) -p $(GUEST_P) -o $(BUILD_DIR)/vm2.boot

$(BUILD_DIR)/checked-config: FORCE | emulator-ready
	@mkdir -p "$(BUILD_DIR)"
	@printf '%s\n' "$$CC" "$$CPPFLAGS" "$$CFLAGS" "$$LDFLAGS" "$$LDLIBS" > "$@.tmp"
	@cmp -s "$@.tmp" "$@" && rm -f "$@.tmp" || mv "$@.tmp" "$@"

$(BUILD_DIR)/checked-emulator: $(BUILD_DIR)/checked-config Makefile tests/checked_vm1.c $(wildcard $(EMULATOR_ROOT)/src/*.c) $(wildcard $(EMULATOR_ROOT)/src/*.h) | emulator-ready
	@mkdir -p "$(BUILD_DIR)"
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -DVM1_NO_MAIN -I "$(EMULATOR_ROOT)/src" tests/checked_vm1.c "$(EMULATOR_ROOT)/src/runtime.c" "$(EMULATOR_ROOT)/src/sys_ctrl.c" "$(EMULATOR_ROOT)/src/bitcopy.c" "$(EMULATOR_ROOT)/src/backend_bitcopy.c" -o $@ $(LDLIBS)
check: check-direct check-guest
check-direct: $(BUILD_DIR)/checked-emulator | test-tmp
	CHECKED_EMULATOR="$(if $(WORKSPACE_ROOT),$(BUILD_DIR),$(CURDIR)/$(BUILD_DIR))/checked-emulator" python3 -B tests/test_direct.py
	python3 -B tests/test_direct_cli.py
	python3 -B tests/test_limited_run.py
	python3 -B tests/test_cost_counters.py
check-guest: $(BUILD_DIR)/checked-emulator | test-tmp
	PYTHONPATH="$(COPYCODE_ROOT)/src" python3 -B "$(COPYCODE_ROOT)/tests/test_schedule.py"
	CHECKED_EMULATOR="$(if $(WORKSPACE_ROOT),$(BUILD_DIR),$(CURDIR)/$(BUILD_DIR))/checked-emulator" python3 -B tests/test_guest_arithmetic.py
	CHECKED_EMULATOR="$(if $(WORKSPACE_ROOT),$(BUILD_DIR),$(CURDIR)/$(BUILD_DIR))/checked-emulator" python3 -B tests/test_guest.py
	python3 -B tests/test_guest_cli.py

# The former C implementation is a migration/control executable, not the product.
reference: $(BIN)
legacy: reference
$(BIN): $(REFERENCE)/space.c $(ENGINE) $(REFERENCE)/space.h $(REFERENCE)/sys_ctrl.h $(REFERENCE)/proto_gen.h Makefile $(BIN).build-config
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o "$@" $(REFERENCE)/space.c $(ENGINE) $(LDLIBS)
$(BIN).build-config: FORCE
	@mkdir -p "$(dir $(BIN))"
	@printf '%s\n' "$$CC" "$$CPPFLAGS" "$$CFLAGS" "$$LDFLAGS" "$$LDLIBS" > "$@.tmp"
	@cmp -s "$@.tmp" "$@" && rm -f "$@.tmp" || mv "$@.tmp" "$@"
FORCE:
$(REFERENCE)/proto_gen.h: $(REFERENCE)/proto.def $(GEN)
	cd "$(REFERENCE)" && python3 -B ../../$(GEN) proto.def proto_gen.h
check-legacy: legacy | test-tmp
	./tests/run_tests.sh "$(SPACE_EMULATOR)"
check-built: | test-tmp
	./tests/run_tests.sh "$(SPACE_EMULATOR)"
check-core: legacy | test-tmp
	./tests/run_core_tests.sh "$(SPACE_EMULATOR)"
install:
	python3 -B tools/release.py install --destdir "$(DESTDIR)" --bindir "$(bindir)" --libdir "$(libdir)" --docdir "$(docdir)"
dist:
	python3 -B tools/release.py create --output "$(DIST_ARCHIVE)"
check-dist distcheck: dist | test-tmp
	python3 -B tools/release.py check --archive "$(DIST_ARCHIVE)"
benchmark: $(BUILD_DIR)/checked-emulator legacy | test-tmp
	VM2_LEGACY="$(abspath $(BIN))" $(BENCH_LIMIT) python3 -B tools/bench_guest.py --output "$(BENCH_OUTPUT)" --repeats $(BENCH_REPEATS) --ticks $(BENCH_TICKS)
benchmark-direct: $(BUILD_DIR)/checked-emulator legacy | test-tmp
	VM2_LEGACY="$(abspath $(BIN))" $(BENCH_LIMIT) python3 -B tools/bench_direct.py --output "$(BENCH_OUTPUT)/direct" --repeats $(BENCH_REPEATS) --layers $(BENCH_TICKS)
test-tmp:
	@mkdir -p "$(TMPDIR)"
clean:
ifneq ($(WORKSPACE_ROOT),)
	python3 -B "$(WORKSPACE_ROOT)/tools/layout.py" --component "$(CURDIR)" --clean
else
	python3 -B tools/clean.py --binary "$(BIN)" --distdir "$(DISTDIR)" --benchmark "$(BENCH_OUTPUT)"
endif

.PHONY: checked-emulator
checked-emulator: $(BUILD_DIR)/checked-emulator
