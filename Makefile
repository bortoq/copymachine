# Root Makefile. all: the emulator and L0. check-fast: no L0, minutes. check: check-fast + boot + the
# language check. check-full: check + the long goals (hours).
.DEFAULT_GOAL := all
.NOTPARALLEL:
PYTHON ?= python3
RUFF ?= ruff
LIMIT = $(PYTHON) -B tools/limited_run.py --seconds 600 --memory-mib 768
LONG = check-kernel check-self check-isolation check-proof check-replace check-user-programs
.PHONY: all emulator language check-fast check check-full check-layout check-tower lint coverage clean
all: emulator language
emulator:
	$(LIMIT) $(MAKE) -C emulator -j1
language:
	$(MAKE) -C language -j1 boot
lint:
	$(RUFF) check .

# Coverage (17.9): gcov of the emulator under `emulator check` and under the language test of LONG (the
# emulator `make space` builds, instrumented); coverage.py for language/tools if it is installed.
COVLANG = $(CURDIR)/language/build/cov
coverage:
	$(MAKE) -C emulator -j1 coverage
	rm -rf "$(COVLANG)"
	$(MAKE) -C language -j1 space OUT="$(COVLANG)" CFLAGS="-std=c11 -O0 -g --coverage"
	$(MAKE) -C language -j1 boot OUT="$(COVLANG)"
	LANGUAGE_OUT="$(COVLANG)" $(PYTHON) -B language/tests/test_long_copy.py > /dev/null
	@echo "== coverage of emulator/src: emulator check + language test_long_copy =="
	cd emulator && $(PYTHON) -B ../tools/gcov_summary.py "$(CURDIR)/emulator/build/cov:$(COVLANG)" src/runtime.c src/sys_ctrl.c src/bitcopy.c src/backend_bitcopy.c
	@if $(PYTHON) -c 'import coverage' 2>/dev/null; then echo "== coverage.py of language/tools under check-fast =="; $(MAKE) -C language -j1 coverage-python; else echo "coverage.py of language/tools: not installed, skipped (gcov only)"; fi
check-layout:
	$(PYTHON) -B tools/check_layout.py
# The chain of languages 1-4 (tower/): its tests run the emulator in the checked mode; language 4 tests
# long copies into sparse files of 1.5 GiB (positions over 2^32 bits), hence --file-mib 2048.
check-tower:
	$(LIMIT) --file-mib 2048 $(PYTHON) -B -m unittest discover -s tower/tests -p 'test_*.py'
check-fast:
	$(LIMIT) $(MAKE) -C emulator -j1 check checked
	$(MAKE) -C language -j1 check-programs check-closure check-language-md check-fast-tests
	$(MAKE) check-tower
	$(MAKE) check-layout
check: check-fast
	$(MAKE) -C language -j1 boot
	$(MAKE) -C language -j1 check
check-full: check
	$(MAKE) -C language -j1 $(LONG)
clean:
	$(MAKE) -C emulator clean
	$(MAKE) -C language clean
