"""usage: wordticks.py WORDS-FILE...: the ticks of a word of 1000 repetitions, from the output of t/runt.sh (one file for each variant):
(the test - its loads) / 1000. Letters: see t/README.txt (q, r: the + with its loads)."""
import sys

PAIRS = [('kn-put 8 bytes', 'c', 'b'), ('kn-put 128 bytes', 'e', 'd'), ('kn-put 127 bytes unaligned', 'f', 'b'),
         ('cmove 16 bytes', 'i', 'h'), ('cmove 128 bytes', 'j', 'h'), ('cmove 127 bytes unaligned', 'k', 'h'),
         ('lay-numeric 4 bytes', 'm', 'l'), ('lay-numeric 8 bytes unaligned', 'n', 'l'), ('+!', 'p', 'o'), ('+', 'r', 'q')]


def load(path):
    ticks = {}
    for line in open(path):
        parts = line.split()
        ticks[parts[0]] = int(parts[2])
    return ticks


files = [load(p) for p in sys.argv[1:]]
for name, x, y in PAIRS:
    print(f'{name:30}' + ''.join(f'{(t[x] - t[y]) / 1000:10.3f}' for t in files))
