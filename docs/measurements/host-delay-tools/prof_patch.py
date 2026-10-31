# usage: prof_patch.py DIR : adds rdtsc phase counters to runtime.c (computation) and sys_ctrl.c (host call), printed at exit (HW_PROF)
# works on the 18.13 emulator (computation without the shadow) and on the 18.15 one; the overhead of an interval of two rdtsc is
# measured at exit and subtracted
import sys
d = sys.argv[1]
s = open(d + '/runtime.c').read()
s = s.replace('#include <signal.h>', '#include <signal.h>\n#include <x86intrin.h>\n#include <time.h>\n'
              'uint64_t pr_read,pr_sys,pr_bit,pr_n,pr_act,pr_ops;\n'
              'uint64_t pr_hcall[16],pr_hcyc[16],pr_hin[16],pr_hdef[16],pr_hout[16];\n', 1)
new_style = 'channel_op' in s
if new_style:
    s = s.replace('int computation(void)\n{\n  int active=0,channel_op=0;', 'int computation(void)\n{\n  int active=0,channel_op=0;\n  uint64_t t0=__rdtsc();')
    s = s.replace('  shadow_valid=shadow!=NULL;\n  if(!active) return 0;',
                  '  shadow_valid=shadow!=NULL;\n  uint64_t t1=__rdtsc(); pr_read+=t1-t0; pr_n++;\n  if(!active) return 0;\n'
                  '  pr_act++; for(size_t i=0;i<proc_n;i++) if(processor[i][0]) pr_ops++;')
    old = '  if(channel_op) sys_tick();\n  backend_tick();\n  return 1;'
else:
    s = s.replace('int computation(void)\n{\n  int active=0;', 'int computation(void)\n{\n  int active=0;\n  uint64_t t0=__rdtsc();')
    s = s.replace('  if(!active) return 0;',
                  '  uint64_t t1=__rdtsc(); pr_read+=t1-t0; pr_n++;\n  if(!active) return 0;\n'
                  '  pr_act++; for(size_t i=0;i<proc_n;i++) if(processor[i][0]) pr_ops++;')
    old = '  sys_tick();\n  backend_tick();\n  return 1;'
new = ('  ' + ('if(channel_op) ' if new_style else '') + 'sys_tick();\n  uint64_t t2=__rdtsc();\n  backend_tick();\n  uint64_t t3=__rdtsc();\n'
       '  pr_sys+=t2-t1; pr_bit+=t3-t2;\n  return 1;')
assert old in s
s = s.replace(old, new)
old = '  destroy_space();\n  return 0;'
new = r'''  if(getenv("HW_PROF")) {
    struct timespec a,b; uint64_t c0=__rdtsc(); clock_gettime(CLOCK_MONOTONIC,&a); for(volatile int w=0;w<20000000;w++); uint64_t c1=__rdtsc(); clock_gettime(CLOCK_MONOTONIC,&b);
    double ghz=(double)(c1-c0)/((b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec));
    double n=(double)pr_n; uint64_t os=0; for(int w=0;w<1000000;w++){ uint64_t x=__rdtsc(),y=__rdtsc(); os+=y-x; } double ov=(double)os/1e6;
    pr_read-=(uint64_t)(ov*n); pr_sys-=(uint64_t)(ov*n); pr_bit-=(uint64_t)(ov*n);
    for(int k=0;k<16;k++) if(pr_hcall[k]) { uint64_t o2=(uint64_t)(ov*pr_hcall[k]); pr_hcyc[k]-=o2; pr_hin[k]-=o2; pr_hdef[k]-=o2; pr_hout[k]-=o2; }
    fprintf(stderr,"tsc %.3f GHz (rdtsc interval overhead %.1f cycles subtracted); ticks %llu active %llu ops/active %.2f\n",ghz,ov,(unsigned long long)pr_n,(unsigned long long)pr_act,(double)pr_ops/pr_act);
    fprintf(stderr,"per tick (ns): read %.1f  sys_tick %.1f  bitcpy %.1f  total %.1f\n",pr_read/n/ghz,pr_sys/n/ghz,pr_bit/n/ghz,(pr_read+pr_sys+pr_bit)/n/ghz);
    for(int k=0;k<16;k++) if(pr_hcall[k]) fprintf(stderr,"host def %d: calls %llu, ns/call: total %.0f in %.0f def %.0f out %.0f\n",k,(unsigned long long)pr_hcall[k],pr_hcyc[k]/(double)pr_hcall[k]/ghz,pr_hin[k]/(double)pr_hcall[k]/ghz,pr_hdef[k]/(double)pr_hcall[k]/ghz,pr_hout[k]/(double)pr_hcall[k]/ghz);
  }
  destroy_space();
  return 0;'''
assert old in s
s = s.replace(old, new)
open(d + '/runtime.c', 'w').write(s)

t = open(d + '/sys_ctrl.c').read()
t = t.replace('#include <time.h>', '#include <time.h>\n#include <x86intrin.h>\nextern uint64_t pr_hcall[16],pr_hcyc[16],pr_hin[16],pr_hdef[16],pr_hout[16];', 1)
call_old = 'host_defs[v[3]](in, &out, &ret, &disp)' if 'disp' in t else 'host_defs[v[3]](in, &out, &ret)'
a = t.index('  bitcpy((size_t)in, space, (size_t)(base + req_bits), hv, 0);')
b = t.index('  return 0;', a)
blk = t[a:b]
nb = blk.replace('  bitcpy((size_t)in, space, (size_t)(base + req_bits), hv, 0);',
                 '  uint64_t h0=__rdtsc();\n  bitcpy((size_t)in, space, (size_t)(base + req_bits), hv, 0);\n  uint64_t h1=__rdtsc();')
nb = nb.replace('  if(' + call_old + ') return EINVAL;', '  if(' + call_old + ') return EINVAL;\n  uint64_t h2=__rdtsc();')
nb = nb.replace('  space_put(32, ret, hi);\n', '  space_put(32, ret, hi);\n  uint64_t h3=__rdtsc();\n  pr_hcall[v[3]]++; pr_hin[v[3]]+=h1-h0; pr_hdef[v[3]]+=h2-h1; pr_hout[v[3]]+=h3-h2; pr_hcyc[v[3]]+=h3-h0;\n')
assert 'h3' in nb and 'h2' in nb
t = t[:a] + nb + t[b:]
open(d + '/sys_ctrl.c', 'w').write(t)
