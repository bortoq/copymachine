# usage: hist_patch.py DIR : after counter/prof patches; per tick histogram of the layer cell (link row source of the last processor), dumped to $HW_HIST
import sys
d=sys.argv[1]
s=open(d+'/runtime.c').read()
s=s.replace('#include <signal.h>','#include <signal.h>\nstatic uint32_t *histo;',1)
old="  shadow_valid=shadow!=NULL;\n"
assert old in s
s=s.replace(old, old+"  if(!histo) histo=calloc(1u<<21,4);\n  histo[(instructions[proc_n-1][2]>>10)&((1u<<21)-1)]++;\n",1)
old="  destroy_space();\n  return 0;"
assert old in s
s=s.replace(old,'  if(getenv("HW_HIST")) { FILE *hf=fopen(getenv("HW_HIST"),"w"); for(size_t k=0;k<(1u<<21);k++) if(histo[k]) fprintf(hf,"%zu %u\\n",k,histo[k]); fclose(hf); }\n'+old,1)
open(d+'/runtime.c','w').write(s)
