"""usage: wordmap.py WORDS OUT.json WORK  (WORK: working copy): the cell of the body of every word of the kernel of the variant (boot_call WORDS), for wordprof.py."""
import sys
sys.path.insert(0, sys.argv[3] + '/language/tools')
import boot_call, boot, word_cost, json
words = sys.argv[1].split(',')
text=boot_call.kernel_text(words)
_,rec,info=word_cost.compile_with_records(text,sizes=boot.SIZES)
json.dump({k:v['entry'] for k,v in rec.items()},open(sys.argv[2],'w'))
print(len(rec),list(rec.items())[:2])
