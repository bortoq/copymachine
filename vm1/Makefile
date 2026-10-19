.DELETE_ON_ERROR:
.DEFAULT_GOAL := all
BACKEND ?= bitcopy
ifneq ($(words $(BACKEND)),1)
$(error BACKEND must be one of bitcopy or network)
endif
ifeq ($(filter $(BACKEND),bitcopy network),)
$(error BACKEND must be bitcopy or network)
endif
export PYTHONDONTWRITEBYTECODE=1
CC      ?= cc
CFLAGS  ?= -Wall -Wextra -pedantic -std=c11 -O2
SPACE_SIZE ?= 65520
export CC CPPFLAGS CFLAGS LDFLAGS LDLIBS

SRC_DIR   = src
VM1_SRC   = $(SRC_DIR)/machine.c
SORT_SRC = $(SRC_DIR)/network.c
MKLDR1_SRC = tools/loader.c
C3_SRC    = tools/compile.c
TEST_SORT_SRC = tests/test_network.c
TEST_COMPAT_SRC = tests/test_channel.c
TEST_MACHINE_SRC = tests/test_machine.c
TEST_NETUNIT_SRC = tests/test_network_unit.c
TEST_LOADER_SRC = tests/test_loader.c
TEST_COMPILE_SRC = tests/test_compile.c

VM1_BIN   = build/legacy/vm1
SORT_BIN = sort
MKLDR1_BIN = tools/loader
C3_BIN    = tools/compile
TEST_SORT_BIN = tests/test_network
TEST_COMPAT_BIN = tests/test_channel
TEST_MACHINE_BIN = tests/test_machine
TEST_NETUNIT_BIN = tests/test_network_unit
TEST_LOADER_BIN = tests/test_loader
TEST_COMPILE_BIN = tests/test_compile
TEST_ADDRESS_BIN = tests/test_addressing
TEST_ADDRESS_SMALL_BIN = tests/test_addressing_small
TEST_ADDRESS_IRREGULAR_BIN = tests/test_addressing_irregular
PARALLEL_BINS = tests/test_parallel tests/test_parallel_small tests/test_parallel_irregular
IRREGULAR_SORTER = tests/sorter-irregular.txt
SMALL_SORTER = tests/sorter-small.txt
SORTER    = sorter.txt

.PHONY: all clean sorter check test help tools tests

all: vm1

tools: $(MKLDR1_BIN) $(C3_BIN)

tests: $(TEST_SORT_BIN) $(TEST_COMPAT_BIN) $(TEST_MACHINE_BIN) $(TEST_NETUNIT_BIN) $(TEST_LOADER_BIN) $(TEST_COMPILE_BIN) $(TEST_ADDRESS_BIN) $(TEST_ADDRESS_SMALL_BIN) $(TEST_ADDRESS_IRREGULAR_BIN) $(PARALLEL_BINS)

$(VM1_BIN): $(VM1_SRC) $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
	@mkdir -p "$(@D)"
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) $(VM1_SRC) -o $@ $(LDLIBS)

$(SORT_BIN): $(SORT_SRC)
	$(CC) $(CFLAGS) $(SORT_SRC) -o $@

$(MKLDR1_BIN): $(MKLDR1_SRC)
	$(CC) $(CFLAGS) $(MKLDR1_SRC) -o $@

$(C3_BIN): $(C3_SRC)
	$(CC) $(CFLAGS) $(C3_SRC) -o $@

$(TEST_SORT_BIN): $(TEST_SORT_SRC)
	$(CC) $(CFLAGS) $(TEST_SORT_SRC) -o $@

$(TEST_COMPAT_BIN): $(TEST_COMPAT_SRC)
	$(CC) $(CFLAGS) $(TEST_COMPAT_SRC) -o $@

$(TEST_MACHINE_BIN): $(TEST_MACHINE_SRC) $(SRC_DIR)/machine.c $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
	$(CC) $(CFLAGS) -DUNIT_TEST $(TEST_MACHINE_SRC) -o $@

$(TEST_NETUNIT_BIN): $(TEST_NETUNIT_SRC) $(SRC_DIR)/network.c
	$(CC) $(CFLAGS) -DUNIT_TEST $(TEST_NETUNIT_SRC) -o $@

$(TEST_LOADER_BIN): $(TEST_LOADER_SRC) tools/loader.c
	$(CC) $(CFLAGS) -DUNIT_TEST $(TEST_LOADER_SRC) -o $@

$(TEST_COMPILE_BIN): $(TEST_COMPILE_SRC) tools/compile.c
	$(CC) $(CFLAGS) -DUNIT_TEST $(TEST_COMPILE_SRC) -o $@

$(TEST_ADDRESS_BIN): tests/test_addressing.c $(VM1_SRC) $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
	$(CC) $(CFLAGS) tests/test_addressing.c -o $@

$(TEST_ADDRESS_SMALL_BIN): tests/test_addressing.c $(VM1_SRC) $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
	$(CC) $(CFLAGS) -DSPACE_SIZE=256 -DPROCESSOR_N=2 tests/test_addressing.c -o $@

$(TEST_ADDRESS_IRREGULAR_BIN): tests/test_addressing.c $(VM1_SRC) $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
	$(CC) $(CFLAGS) -DSPACE_SIZE=240 -DPROCESSOR_N=2 $< -o $@

tests/test_parallel: tests/test_parallel.c $(VM1_SRC) $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
	$(CC) $(CFLAGS) $< -o $@

tests/test_parallel_small: tests/test_parallel.c $(VM1_SRC) $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
	$(CC) $(CFLAGS) -DSPACE_SIZE=256 -DPROCESSOR_N=2 $< -o $@

tests/test_parallel_irregular: tests/test_parallel.c $(VM1_SRC) $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
	$(CC) $(CFLAGS) -DSPACE_SIZE=240 -DPROCESSOR_N=2 $< -o $@

$(IRREGULAR_SORTER): $(SORT_BIN)
	./$(SORT_BIN) 240 > $@

.PHONY: check-parallel
check-parallel: $(PARALLEL_BINS) $(SORTER) $(SMALL_SORTER) $(IRREGULAR_SORTER)
	./tests/test_parallel_small $(SMALL_SORTER)
	./tests/test_parallel_irregular $(IRREGULAR_SORTER)
	./tests/test_parallel $(SORTER)
	$(MAKE) check-parallel-shapes

$(SMALL_SORTER): $(SORT_BIN)
	./$(SORT_BIN) 256 > $@

.PHONY: check-addressing
check-addressing: $(TEST_ADDRESS_BIN) $(TEST_ADDRESS_SMALL_BIN) $(TEST_ADDRESS_IRREGULAR_BIN) $(SORTER) $(SMALL_SORTER) $(IRREGULAR_SORTER)
	@status=0; ./$(TEST_ADDRESS_SMALL_BIN) $(SMALL_SORTER) || status=1; \
	./$(TEST_ADDRESS_IRREGULAR_BIN) $(IRREGULAR_SORTER) || status=1; \
	./$(TEST_ADDRESS_BIN) $(SORTER) || status=1; exit $$status

# Generate default sorting network
sorter: $(SORTER)

$(SORTER): $(SORT_BIN)
	./$(SORT_BIN) $(SPACE_SIZE) > $@

# Run all runtime and historical mechanism tests
check: all tools $(VM1_BIN) $(SORTER) $(SMALL_SORTER) tests check-runtime
	@echo "== machine unit (per-function) =="
	./$(TEST_MACHINE_BIN)
	@echo "== network unit (per-function) =="
	./$(TEST_NETUNIT_BIN)
	@echo "== loader unit (per-function) =="
	./$(TEST_LOADER_BIN)
	@echo "== compile unit (per-function) =="
	./$(TEST_COMPILE_BIN)
	@echo "== sort: 256-pair sanity =="
	./$(TEST_SORT_BIN)
	@echo "== vm1 channel compat (exact echo, 2-phase) =="
	VM1_LEGACY_BIN=./$(VM1_BIN) ./$(TEST_COMPAT_BIN)
	@echo "== independent simultaneous-copy oracle =="
	$(MAKE) check-addressing
	$(MAKE) check-parallel

test: check

clean:
	rm -rf build dist
	rm -f vm1 vm1.tmp
	rm -f $(VM1_BIN) $(SORT_BIN) $(SORTER) $(MKLDR1_BIN) $(C3_BIN) $(TEST_SORT_BIN) $(TEST_COMPAT_BIN) $(TEST_MACHINE_BIN) $(TEST_NETUNIT_BIN) $(TEST_LOADER_BIN) $(TEST_COMPILE_BIN) $(TEST_ADDRESS_BIN) $(TEST_ADDRESS_SMALL_BIN) $(TEST_ADDRESS_IRREGULAR_BIN)
	rm -f $(PARALLEL_BINS) $(IRREGULAR_SORTER) tests/test_parallel_shape tests/sorter-shape.txt
	rm -f tests/bench_ordering tests/bench_ordering_stats tests/test_ordering_probe
	rm -f $(SMALL_SORTER)
	rm -f tmp_* tmp-*

help:
	@echo "Targets:"
	@echo "  all     - build vm1 (BACKEND=bitcopy by default; network for two-phase)"
	@echo "  tools   - build loader and compile"
	@echo "  tests   - build C test binaries"
	@echo "  sorter  - generate sorter.txt for SPACE_SIZE=$(SPACE_SIZE)"
	@echo "  check   - run runtime and mechanism tests"
	@echo "  install - install vm1 and contract (prefix, DESTDIR supported)"
	@echo "  dist / distcheck - package / verify a standalone source release"
	@echo "  clean   - remove build artifacts"
	@echo "  help    - this message"

# Cover a large padding gap, a top-level local ghost pair and a partial tail.
.PHONY: check-parallel-shapes
check-parallel-shapes: $(SORT_BIN)
	@set -e; for n in 1040 32784 60000; do \
	  $(CC) $(CFLAGS) -DSPACE_SIZE=$$n -DPROCESSOR_N=128 tests/test_parallel.c -o tests/test_parallel_shape; \
	  ./$(SORT_BIN) $$n > tests/sorter-shape.txt; \
	  ./tests/test_parallel_shape tests/sorter-shape.txt; \
	done

# Optional research controls; none changes the vm1 CLI or the default kernel.
ORDERING_DEPS = tests/bench_ordering.c tests/ordering_variants.h $(VM1_SRC) $(SRC_DIR)/machine.h $(SRC_DIR)/loader.h
.PHONY: bench-ordering bench-ordering-stats check-ordering

tests/bench_ordering: $(ORDERING_DEPS)
	$(CC) $(CFLAGS) $< -o $@

tests/bench_ordering_stats: $(ORDERING_DEPS)
	$(CC) $(CFLAGS) -DVM1_ORDERING_STATS $< -o $@

bench-ordering: tests/bench_ordering $(SORTER)
	./tests/bench_ordering $(SORTER)

bench-ordering-stats: tests/bench_ordering_stats $(SORTER)
	./tests/bench_ordering_stats $(SORTER)

check-ordering: $(SORTER) $(SMALL_SORTER) $(IRREGULAR_SORTER)
	@set -e; for variant in 0 1 2; do \
	  echo "ordering control $$variant"; \
	  for n in 240 256 65520; do \
	    case $$n in 240) net=$(IRREGULAR_SORTER); proc=2;; 256) net=$(SMALL_SORTER); proc=2;; *) net=$(SORTER); proc=128;; esac; \
	    $(CC) $(CFLAGS) -DSPACE_SIZE=$$n -DPROCESSOR_N=$$proc -DORDERING_VARIANT=$$variant -DVM1_MACHINE_SOURCE='"ordering_probe.h"' tests/test_addressing.c -o tests/test_ordering_probe; \
	    ./tests/test_ordering_probe $$net; \
	  done; \
	done

# Production four-index runtime; old native-word/LDR1 code is a test control.
RUNTIME_COMMON = src/runtime.c src/sys_ctrl.c src/bitcopy.c
RUNTIME_HEADERS = src/space.h src/sys_ctrl.h src/proto_gen.h
.PHONY: vm1 FORCE check-runtime
FORCE:
vm1: build/$(BACKEND)/vm1 FORCE
	cp "$<" vm1.tmp
	mv vm1.tmp vm1

define RUNTIME_template
build/$(1)/build-config: FORCE
	@mkdir -p "$$(@D)"
	@printf '%s\n' "$$$$CC" "$$$$CPPFLAGS" "$$$$CFLAGS" "$$$$LDFLAGS" "$$$$LDLIBS" > "$$@.tmp"
	@cmp -s "$$@.tmp" "$$@" && rm -f "$$@.tmp" || mv "$$@.tmp" "$$@"

build/$(1)/vm1: $$(RUNTIME_COMMON) $$(RUNTIME_HEADERS) src/backend_$(1).c $(if $(filter network,$(1)),src/machine.c src/machine.h src/network.c) build/$(1)/build-config Makefile
	$$(CC) $$(CPPFLAGS) $$(CFLAGS) $$(LDFLAGS) $$(RUNTIME_COMMON) src/backend_$(1).c -o $$@ $$(LDLIBS)

build/$(1)/test_runtime: tests/test_runtime.c $$(RUNTIME_COMMON) $$(RUNTIME_HEADERS) src/backend_$(1).c $(if $(filter network,$(1)),src/machine.c src/machine.h src/network.c) build/$(1)/build-config Makefile
	$$(CC) $$(CPPFLAGS) $$(CFLAGS) $$(LDFLAGS) -DVM1_NO_MAIN $(if $(filter network,$(1)),-DVM1_TEST_NETWORK) tests/test_runtime.c $$(RUNTIME_COMMON) src/backend_$(1).c -o $$@ $$(LDLIBS)

build/$(1)/test_sys: tests/test_runtime_sys.c $$(RUNTIME_COMMON) $$(RUNTIME_HEADERS) src/backend_$(1).c $(if $(filter network,$(1)),src/machine.c src/machine.h src/network.c) build/$(1)/build-config Makefile
	$$(CC) $$(CPPFLAGS) $$(CFLAGS) $$(LDFLAGS) -DVM1_NO_MAIN tests/test_runtime_sys.c $$(RUNTIME_COMMON) src/backend_$(1).c -o $$@ $$(LDLIBS)
endef
$(foreach variant,bitcopy network,$(eval $(call RUNTIME_template,$(variant))))

build/test_bitcopy: tests/test_runtime_bitcopy.c src/bitcopy.c src/space.h build/bitcopy/build-config
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/test_runtime_bitcopy.c src/bitcopy.c -o $@ $(LDLIBS)

check-runtime: build/bitcopy/vm1 build/network/vm1 build/bitcopy/test_runtime build/network/test_runtime build/bitcopy/test_sys build/network/test_sys build/test_bitcopy
	./build/test_bitcopy
	./build/bitcopy/test_runtime
	./build/network/test_runtime
	./build/bitcopy/test_sys
	./build/network/test_sys
	python3 -B tests/test_runtime_cli.py
	python3 -B tests/test_runtime_build.py

build/bitcopy/bench_core: tests/bench_runtime_core.c $(RUNTIME_COMMON) $(RUNTIME_HEADERS) src/backend_bitcopy.c build/bitcopy/build-config
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -DVM1_NO_MAIN $< $(RUNTIME_COMMON) src/backend_bitcopy.c -o $@ $(LDLIBS)
build/network/bench_core: tests/bench_runtime_core.c $(RUNTIME_COMMON) $(RUNTIME_HEADERS) src/backend_network.c src/machine.c src/machine.h src/network.c build/network/build-config
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -DVM1_NO_MAIN $< $(RUNTIME_COMMON) src/backend_network.c -o $@ $(LDLIBS)
.PHONY: benchmark
benchmark: build/bitcopy/vm1 build/network/vm1 build/bitcopy/bench_core build/network/bench_core
	python3 -B tests/bench_runtime.py

src/proto_gen.h: src/proto.def tools/proto_gen.py
	python3 -B tools/proto_gen.py src/proto.def src/proto_gen.h

# Standalone source release; paths with spaces are supported.
prefix ?= /usr/local
bindir ?= $(prefix)/bin
docdir ?= $(prefix)/share/doc/vm1
VERSION := $(shell cat VERSION)
DIST_ARCHIVE = dist/vm1-$(VERSION).tar.gz
.PHONY: install dist distcheck
install: vm1
	python3 -B tools/release.py install --binary vm1 --destdir "$(DESTDIR)" --bindir "$(bindir)" --docdir "$(docdir)"
dist:
	python3 -B tools/release.py create --output "$(DIST_ARCHIVE)"
distcheck: dist
	python3 -B tools/release.py check --archive "$(DIST_ARCHIVE)"
