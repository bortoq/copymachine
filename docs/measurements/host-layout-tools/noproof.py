"""usage: noproof.py WORDS OUT.call WORK: L0 of the variant without the three calls of dj-prove in kn-compile (the ticks of the proof = the ticks with it - without it)."""
import sys,subprocess
sys.path.insert(0,sys.argv[3]+'/language/tools')
import boot,boot_call,host,paths
words=sys.argv[1].split(',')
text=boot_call.kernel_text(words)
a="  fc-first @ lay-next-cell @ dj-prove 0= if -9 throw then\n  fc-etab lay-cell-bit rshift dup fc-nwords @ 2* + dj-prove 0= if -9 throw then\n  fc-rtab lay-cell-bit rshift dup fc-nret @ 2* + dj-prove 0= if -9 throw then ;"
assert a in text
text=text.replace(a," ;")
lines=[boot.SIZES]+['fc| '+l for l in text.split('\n')]+['fc-go','bye']
data=paths.source_bytes(paths.LIBRARY_FILES)+('\n'.join(lines)+'\n').encode('latin-1')
r=subprocess.run([str(host.build())],input=data,capture_output=True,check=False)
assert r.returncode==0 and not r.stderr, r.stdout[-200:]
open(sys.argv[2],'wb').write(r.stdout[:-1]); print(len(r.stdout))
