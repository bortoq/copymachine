import sys
p=sys.argv[1]; s=open(p).read()
old="""  for(uint64_t tick=0;!tick_limit||tick<tick_limit;tick++)
    if(!computation()) break;
  fflush(stdout); destroy_space();"""
new="""  uint64_t tick=0;
  for(;!tick_limit||tick<tick_limit;tick++)
    if(!computation()) break;
  fflush(stdout);
  if(getenv("HW_TICKS")) {
    /* FNV-1a of the two halves of the program: bits [0,2^29) and [2^30,2^30+2^29) */
    uint64_t h=1469598103934665603ull; size_t a;
    for(a=0;a<(1u<<26);a++) h=(h^space[a])*1099511628211ull;
    for(a=(1u<<27);a<(1u<<27)+(1u<<26);a++) h=(h^space[a])*1099511628211ull;
    fprintf(stderr,"ticks %llu prog-hash %016llx\\n",(unsigned long long)tick,(unsigned long long)h);
  }
  destroy_space();"""
assert old in s
open(p,'w').write(s.replace(old,new))
