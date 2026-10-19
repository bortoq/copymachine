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
VM1_ROOT ?= $(if $(wildcard vendor/vm1/src/runtime.c),$(CURDIR)/vendor/vm1,$(abspath ../vm1))
VM1 ?= $(VM1_ROOT)/build/bitcopy/vm1
export COPYCODE_ROOT VM1_ROOT VM1 CC CPPFLAGS CFLAGS LDFLAGS LDLIBS SPACE_TEST_ASAN
export PYTHONDONTWRITEBYTECODE=1
export VM2_CACHE=$(CURDIR)/build/guest-cache
export SPACE_EMULATOR = $(EMULATOR)
export TMPDIR=$(CURDIR)/tmp
BIN ?= space
EMULATOR ?= $(BIN)
COMMON = globals.c bitcopy.c
ENGINE = engine.c config.c sys_ctrl.c $(COMMON)
GEN = tools/proto_gen.py
VERSION := $(shell cat VERSION)
prefix ?= /usr/local
bindir ?= $(prefix)/bin
libdir ?= $(prefix)/libexec/vm2
docdir ?= $(prefix)/share/doc/vm2
DISTDIR ?= dist
DIST_ARCHIVE = $(DISTDIR)/vm2-$(VERSION).tar.gz
BENCH_OUTPUT ?= tmp/guest-benchmark
BENCH_REPEATS ?= 5
BENCH_TICKS ?= 32
BENCH_SECONDS ?= 180
BENCH_MEMORY_MIB ?= 768
BENCH_LIMIT = python3 -B tools/limited_run.py --seconds $(BENCH_SECONDS) --memory-mib $(BENCH_MEMORY_MIB)
GUEST_S ?= 65520
GUEST_P ?= 64

.PHONY: all direct check-direct benchmark-direct guest vm1-ready FORCE check check-guest check-legacy check-built check-core legacy install dist check-dist distcheck benchmark clean test-tmp
all: direct

direct: vm1-ready
	python3 -B tools/build_direct_example.py
vm1-ready: | test-tmp
	@test -d "$(COPYCODE_ROOT)/src/copycode" || { echo 'Set COPYCODE_ROOT to the copycode project' >&2; exit 1; }
	@if [ ! -x "$(VM1)" ]; then $(MAKE) -C "$(VM1_ROOT)" build/bitcopy/vm1; fi
guest: vm1-ready
	python3 -B -m vm2guest.build -s $(GUEST_S) -p $(GUEST_P) -o build/vm2.boot

build/checked-config: FORCE | vm1-ready
	@mkdir -p build
	@printf '%s\n' "$$CC" "$$CPPFLAGS" "$$CFLAGS" "$$LDFLAGS" "$$LDLIBS" > "$@.tmp"
	@cmp -s "$@.tmp" "$@" && rm -f "$@.tmp" || mv "$@.tmp" "$@"

build/checked-vm1: build/checked-config Makefile tests/checked_vm1.c $(wildcard $(VM1_ROOT)/src/*.c) $(wildcard $(VM1_ROOT)/src/*.h) | vm1-ready
	@mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -DVM1_NO_MAIN -I "$(VM1_ROOT)/src" tests/checked_vm1.c "$(VM1_ROOT)/src/runtime.c" "$(VM1_ROOT)/src/sys_ctrl.c" "$(VM1_ROOT)/src/bitcopy.c" "$(VM1_ROOT)/src/backend_bitcopy.c" -o $@ $(LDLIBS)
check: check-direct check-guest
check-direct: build/checked-vm1 | test-tmp
	CHECKED_VM1="$(CURDIR)/build/checked-vm1" python3 -B tests/test_direct.py
	python3 -B tests/test_direct_cli.py
	python3 -B tests/test_limited_run.py
check-guest: build/checked-vm1 | test-tmp
	PYTHONPATH="$(COPYCODE_ROOT)/src" python3 -B "$(COPYCODE_ROOT)/tests/test_schedule.py"
	CHECKED_VM1="$(CURDIR)/build/checked-vm1" python3 -B tests/test_guest_arithmetic.py
	CHECKED_VM1="$(CURDIR)/build/checked-vm1" python3 -B tests/test_guest.py
	python3 -B tests/test_guest_cli.py

# The former C implementation is a migration/control executable, not the product.
legacy: $(BIN)
$(BIN): space.c $(ENGINE) space.h sys_ctrl.h proto_gen.h Makefile $(BIN).build-config
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o "$@" space.c $(ENGINE) $(LDLIBS)
$(BIN).build-config: FORCE
	@mkdir -p "$(dir $(BIN))"
	@printf '%s\n' "$$CC" "$$CPPFLAGS" "$$CFLAGS" "$$LDFLAGS" "$$LDLIBS" > "$@.tmp"
	@cmp -s "$@.tmp" "$@" && rm -f "$@.tmp" || mv "$@.tmp" "$@"
FORCE:
proto_gen.h: proto.def $(GEN)
	python3 -B $(GEN) proto.def proto_gen.h
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
benchmark: build/checked-vm1 legacy | test-tmp
	VM2_LEGACY="$(abspath $(BIN))" $(BENCH_LIMIT) python3 -B tools/bench_guest.py --output "$(BENCH_OUTPUT)" --repeats $(BENCH_REPEATS) --ticks $(BENCH_TICKS)
benchmark-direct: build/checked-vm1 legacy | test-tmp
	VM2_LEGACY="$(abspath $(BIN))" $(BENCH_LIMIT) python3 -B tools/bench_direct.py --output "$(BENCH_OUTPUT)/direct" --repeats $(BENCH_REPEATS) --layers $(BENCH_TICKS)
test-tmp:
	@mkdir -p "$(TMPDIR)"
clean:
	python3 -B tools/clean.py --binary "$(BIN)" --distdir "$(DISTDIR)" --benchmark "$(BENCH_OUTPUT)"
