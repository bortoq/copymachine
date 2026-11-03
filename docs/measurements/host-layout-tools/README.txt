Tools of 18.19 (host-layout.md). From the root of a working copy (WORK), in a scratch directory:
  python3 -B host-layout-tools/progs.py WORK progs                 the 37 programs (one file each, zero byte at the end)
  sh host-layout-tools/buildemu.sh WORK/emulator/src EMU           the emulator with the tick counter (HW_TICKS=1)
  (cd WORK/language && python3 -B tools/boot_call.py -o L0.call)  L0 of the variant (words: --words fill,row,enc,put,cmove,numeric,pstore)
  PROGS=progs python3 host-layout-tools/all37p.py EMU L0.call TAG 0,1,2,3,4,5     ticks and md5 of the output of the 37 programs: all37-TAG.txt
  WORK=WORK CPU=9 python3 host-layout-tools/selfcall.py EMU L0.call fill,row,enc,put,cmove,numeric,pstore L1.call    the self-compilation: L1 = L0?
  t/ (README.txt), wordticks.py                                    the ticks of a word
  python3 -B WORK/language/tools/host_layout.py [-o FILE]          the table of the layout (host_layout.h) from src/hostlayout.fth
Tables: all37-1816.txt, all37-1819.txt (name, ticks, hash of the program, md5 of the output, seconds, code), words-1816.txt, words-1819.txt.
18.23: prof_patch.py (after counter_patch.py: HW_PROF=FILE, the ticks of each cell), wordmap.py WORDS OUT.json WORK (the cell of every word), wordprof.py MAP.json DIR N (the ticks of the words);
  noproof.py WORDS OUT.call WORK (L0 without dj-prove: the ticks of the proof by difference). Tables: words-1823.txt, all37-1823*.txt.
