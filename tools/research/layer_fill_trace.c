/* Trace copy of space/vm2/tests/checked_vm1.c for 14.2 (tools/research/layer_fill.py):
 * instead of the audit it counts, per executed tick (layer), the instructions that are not empty.
 * Empty: a copy with src_low==src_high, a channel instruction with low==high. Nothing in
 * emulator/ or space/vm2/ is changed; the runtime files are linked as they are.
 * Output on stderr: LAYER_FILL_TICKS=N and LAYER_FILL_HIST=h0,h1,...,h<proc_n> */
#include "space.h"
#include <inttypes.h>
static uint64_t field(uint64_t at,unsigned width) {
  uint64_t value=0;
  for(unsigned k=0;k<width;k++) value|=(uint64_t)((space[(at+k)/8]>>(7-(at+k)%8))&1)<<k;
  return value;
}
static unsigned nonempty(void) {
  unsigned count=0;
  for(size_t i=0;i<proc_n;i++) {
    uint64_t p=i*4*address_bits;
    uint64_t dl=field(p,address_bits),dh=field(p+address_bits,address_bits);
    uint64_t sl=field(p+2*address_bits,address_bits),sh=field(p+3*address_bits,address_bits);
    int dc=dl==dh && dl>=space_nbits,sc=sl==sh && sl>=space_nbits;
    if(dc||sc) { uint64_t lo=dc?sl:dl,hi=dc?sh:dh; if(lo!=hi) count++; }
    else if(sl!=sh) count++;
  }
  return count;
}
int main(int argc,char **argv) {
  uint64_t ticks=0,*hist;
  parse_config(argc,argv);init_space();
  hist=calloc(proc_n+1,sizeof *hist);
  while(!tick_limit||ticks<tick_limit) {
    hist[nonempty()]++;
    if(!computation())break;ticks++;
  }
  fprintf(stderr,"LAYER_FILL_TICKS=%"PRIu64"\nLAYER_FILL_HIST=",ticks);
  for(size_t k=0;k<=proc_n;k++) fprintf(stderr,"%s%"PRIu64,k?",":"",hist[k]);
  fputc('\n',stderr);
  destroy_space();return 0;
}
