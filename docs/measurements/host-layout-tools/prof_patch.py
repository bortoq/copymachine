"""usage: prof_patch.py runtime.c  (after counter_patch.py): the histogram of the cells that the ticks execute (18.23). HW_PROF=FILE writes
"cell count" lines at the end (the cell of a tick is the target of the link row of the tick before: the cell = bit address >> 10)."""
import sys
p = sys.argv[1]; s = open(p).read()
s = s.replace("int computation(void)\n{", "static uint32_t *prof_h; static size prof_prev;\nint computation(void)\n{", 1)
s = s.replace("  if(channel_op) sys_tick();", "  if(!prof_h) prof_h=calloc(1u<<22,4);\n  { size *l=instructions[n-1]; if(l[0]==0) { prof_h[(prof_prev>>10)&((1u<<22)-1)]++; prof_prev=l[2]; } }\n  if(channel_op) sys_tick();", 1)
s = s.replace("  if(getenv(\"HW_TICKS\")) {", "  if(getenv(\"HW_PROF\")) { FILE*f=fopen(getenv(\"HW_PROF\"),\"w\"); for(size_t i=0;i<(1u<<22);i++) if(prof_h[i]) fprintf(f,\"%zu %u\\n\",i,prof_h[i]); fclose(f); }\n  if(getenv(\"HW_TICKS\")) {", 1)
open(p, 'w').write(s)
