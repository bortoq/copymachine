# Minimal root Makefile (17.3); the full build and `make check-fast` are 17.4.
.DEFAULT_GOAL := all
.NOTPARALLEL:
PYTHON ?= python3
LIMIT = $(PYTHON) -B tools/limited_run.py --seconds 600 --memory-mib 768
.PHONY: all emulator language check check-layout clean
all: emulator language
emulator:
	$(LIMIT) $(MAKE) -C emulator -j1
language:
	$(LIMIT) $(MAKE) -C language -j1 boot
check-layout:
	$(PYTHON) -B tools/check_layout.py
check:
	$(LIMIT) $(MAKE) -C emulator -j1 check checked
	$(LIMIT) $(MAKE) -C language -j1 check-programs check-closure
	$(MAKE) check-layout
clean:
	$(MAKE) -C emulator clean
	$(MAKE) -C language clean
