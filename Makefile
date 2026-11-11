# Root Makefile. all: the emulator. check-fast: minutes. check: check-fast. check-full: check + the long goals of the
# chain (hours).
.DEFAULT_GOAL := all
.NOTPARALLEL:
PYTHON ?= python3
RUFF ?= ruff
LIMIT = $(PYTHON) -B tools/limited_run.py --seconds 600 --memory-mib 768
LIMIT_LONG = $(PYTHON) -B tools/limited_run.py --seconds 1800 --memory-mib 768
.PHONY: all emulator check-fast check check-full check-layout check-tower check-tower-long check-level-proof lint coverage clean
all: emulator
emulator:
	$(LIMIT) $(MAKE) -C emulator -j1
lint:
	$(RUFF) check .

# Coverage (17.9): gcov of the emulator under `emulator check`.
coverage:
	$(MAKE) -C emulator -j1 coverage
	@echo "== coverage of emulator/src: emulator check =="
	cd emulator && $(PYTHON) -B ../tools/gcov_summary.py "$(CURDIR)/emulator/build/cov" src/runtime.c src/sys_ctrl.c src/bitcopy.c src/backend_bitcopy.c
check-layout:
	$(PYTHON) -B tools/check_layout.py
# The chain of languages 1-5 (tower/): its tests run the emulator in the checked mode; language 4 tests
# long copies into sparse files of 1.5 GiB (positions over 2^32 bits), hence --file-mib 2048.
check-tower:
	$(LIMIT) --file-mib 2048 $(PYTHON) -B -m unittest discover -s tower/tests -p 'test_*.py'
# The long runs of the chain (not in check-fast; in check-full): the tools compiled by l3c (23.9, part 2) and working, 300 spoiled texts,
# the fixed points of l3c: serial (23.9) and with the planner l3p (23.10), the 37 programs by hand (23.11) and as Forth texts (23.15).
check-tower-long:
	$(LIMIT_LONG) $(PYTHON) -B -m unittest discover -s tower/tests -p 'long_*.py'
# Proof of a level (23.21), not in check-tower-long or the nightly run: ~12 min on 4 CPUs (722 s measured), ~27 min on one; 4 CPUs, 4 GiB, 3600 s.
# MALLOC_ARENA_MAX: glibc reserves 64 MiB of address space per arena (8 per CPU), which the memory limit counts.
check-level-proof:
	MALLOC_ARENA_MAX=2 $(PYTHON) -B tools/limited_run.py --seconds 3600 --memory-mib 4096 --cpus 4 $(PYTHON) -B tower/tests/exp_level_proof.py
check-fast:
	$(LIMIT) $(MAKE) -C emulator -j1 check checked
	$(MAKE) check-tower
	$(MAKE) check-layout
	sh tools/ci/contract.sh
check: check-fast
check-full: check
	$(MAKE) check-tower-long
clean:
	$(MAKE) -C emulator clean
