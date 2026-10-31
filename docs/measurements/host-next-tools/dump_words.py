"""usage: dump_words.py OUT [words]: compiles the kernel variant on the host like boot_call.py and writes OUT.pkl (records of the words:
entry, size, ...) and OUT.stream (equal to L0). Run with LANGUAGE_TOOLS=<dir of language/tools>."""
import os, sys, pickle
sys.path.insert(0, os.environ['LANGUAGE_TOOLS'])
import paths, boot, boot_call, word_cost
out = sys.argv[1]
words = sys.argv[2].split(',') if len(sys.argv) > 2 else ['fill', 'row', 'enc']
stream, records, info = word_cost.compile_with_records(boot_call.kernel_text(words), sizes=boot.SIZES)
pickle.dump((records, info), open(out + '.pkl', 'wb'))
open(out + '.stream', 'wb').write(stream)
print(len(stream), len(records))
