-include ../tools/workspace.mk
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

.PHONY: all emulator FORCE check check-runtime checked runtime-bitcopy clean help
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

check: check-runtime
check-runtime: $(OUT)/emulator $(OUT)/test_runtime $(OUT)/test_sys $(BUILD_DIR)/test_bitcopy
	$(BUILD_DIR)/test_bitcopy
	$(OUT)/test_runtime
	$(OUT)/test_sys
	python3 -B tests/test_runtime_cli.py

checked: $(BUILD_DIR)/checked-emulator

clean:
ifneq ($(WORKSPACE_ROOT),)
	python3 -B "$(WORKSPACE_ROOT)/tools/layout.py" --component "$(CURDIR)" --clean
else
	rm -rf "$(BUILD_DIR)"
	rm -f emulator emulator.tmp
endif

help:
	@echo "Targets: all (emulator), check, checked (audit build), clean"

src/proto_gen.h: src/proto.def tools/proto_gen.py
	python3 -B tools/proto_gen.py src/proto.def src/proto_gen.h
