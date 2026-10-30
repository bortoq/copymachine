# Root Makefile. all: the emulator and L0. check-fast: no L0, minutes. check: check-fast + boot + the
# language check. check-full: check + the long goals (hours).
.DEFAULT_GOAL := all
.NOTPARALLEL:
PYTHON ?= python3
RUFF ?= ruff
LIMIT = $(PYTHON) -B tools/limited_run.py --seconds 600 --memory-mib 768
LONG = check-kernel check-self check-isolation check-proof check-replace check-user-programs
.PHONY: all emulator language check-fast check check-full check-layout lint clean
all: emulator language
emulator:
	$(LIMIT) $(MAKE) -C emulator -j1
language:
	$(MAKE) -C language -j1 boot
lint:
	$(RUFF) check .

check-layout:
	$(PYTHON) -B tools/check_layout.py
check-fast:
	$(LIMIT) $(MAKE) -C emulator -j1 check checked
	$(MAKE) -C language -j1 check-programs check-closure check-language-md check-fast-tests
	$(MAKE) check-layout
check: check-fast
	$(MAKE) -C language -j1 boot
	$(MAKE) -C language -j1 check
check-full: check
	$(MAKE) -C language -j1 $(LONG)
clean:
	$(MAKE) -C emulator clean
	$(MAKE) -C language clean
