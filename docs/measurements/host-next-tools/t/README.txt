extra-next-a.fth (kn-put) and extra-next-b.fth (cmove, lay-numeric, +!): the loop of 1000 repetitions of the word.
Build: python3 -B language/tools/boot_call.py -o L.call --extra t/extra-next-a.fth [--words fill,row,enc  for the words in Forth]
Run:   sh t/runt.sh EMU L.call a b c d e f g   (a: empty loop, b/d: loads of the arguments of put 8/128 bytes, c/e: put 8/128,
       f: put 127 bytes unaligned, g: put 4)    and with extra-next-b.fth: h..p (h: loads of cmove, i/j/k: cmove 16/128/127u, l: loads
       of lay-numeric, m/n: lay-numeric 4/8, o: loads of +!, p: +!)
Ticks of the word = (test - its loads) / 1000. One file would have too many words for the capacity of the kernel build.
