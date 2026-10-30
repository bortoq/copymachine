/* Independent audit of the actual emulator execution; test-only, never installed. */
#include "space.h"
#include <inttypes.h>
#include <assert.h>
typedef struct {uint64_t lo,hi;} span;
static uint64_t field(uint64_t at,unsigned width) {
  uint64_t value=0;
  for(unsigned k=0;k<width;k++) value|=(uint64_t)((space[(at+k)/8]>>(7-(at+k)%8))&1)<<k;
  return value;
}
static void audit(void) {
  span *all=malloc(2*proc_n*sizeof *all);size_t count=0;
  uint64_t *devices=malloc(proc_n*sizeof *devices);size_t used=0,requests=0;
  assert(all && devices);
  for(size_t i=0;i<proc_n;i++) {
    uint64_t p=i*4*address_bits;
    uint64_t dl=field(p,address_bits),dh=field(p+address_bits,address_bits);
    uint64_t sl=field(p+2*address_bits,address_bits),sh=field(p+3*address_bits,address_bits);
    int dc=dl==dh && dl>=space_nbits,sc=sl==sh && sl>=space_nbits;
    assert(!(dc&&sc));
    if(dc||sc) {
      uint64_t device=dc?dl:sl,lo=dc?sl:dl,hi=dc?sh:dh;
      if(lo==hi) continue;
      assert(lo<hi && hi<=space_nbits);
      if(device==space_nbits) {
        uint64_t width=dc?120+address_bits:97+address_bits;
        if(hi<lo+width)hi=lo+width;
        if(dc) assert(++requests==1);
      } else {
        assert((hi-lo)%8==0);
        for(size_t k=0;k<used;k++)assert(devices[k]!=device);
        devices[used++]=device;
      }
      assert(hi<=space_nbits);all[count++]=(span){lo,hi};
    } else if(sl!=sh) {
      assert(sl<sh && dl<dh && sh-sl==dh-dl && sh<=space_nbits && dh<=space_nbits);
      all[count++]=(span){sl,sh};all[count++]=(span){dl,dh};
    }
  }
  for(size_t i=0;i<count;i++)for(size_t j=i+1;j<count;j++)
    if(all[i].lo<all[j].hi && all[j].lo<all[i].hi) {
      fprintf(stderr,"AUDIT overlap: %"PRIu64"..%"PRIu64" / %"PRIu64"..%"PRIu64"\n",all[i].lo,all[i].hi,all[j].lo,all[j].hi);abort();
    }
  free(all);free(devices);
}
int main(int argc,char **argv) {
  uint64_t ticks=0;parse_config(argc,argv);init_space();
  const char *entry_option=getenv("VM1_AUDIT_ENTRY");
  uint64_t entry=entry_option?strtoull(entry_option,NULL,10):0;
  int boot_reported=0;
  while(!tick_limit||ticks<tick_limit) {
    if(entry && !boot_reported && field(0,address_bits)==0 &&
       field(address_bits,address_bits)==proc_n*4*address_bits &&
       field(2*address_bits,address_bits)==entry &&
       field(3*address_bits,address_bits)==entry+proc_n*4*address_bits) {
      fprintf(stderr,"VM1_AUDIT_BOOT_TICKS=%"PRIu64"\n",ticks);boot_reported=1;
    }
    audit();if(!computation())break;ticks++;
  }
  fprintf(stderr,"VM1_AUDIT_TICKS=%"PRIu64"\n",ticks);
  destroy_space();return 0;
}
