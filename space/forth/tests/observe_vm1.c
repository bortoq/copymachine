/* Test observer: execute the real emulator runtime and retain sparse raw states. */
#include "space.h"
#include <inttypes.h>
int main(int argc,char **argv) {
 parse_config(argc,argv);init_space();
 const char *reg=getenv("PFORTH_REG_BITS");size at=reg?strtoull(reg,NULL,10):0;
 const char *bad=getenv("PFORTH_INPUT_ERROR");int replaced=0,installed=0;
 uint64_t ticks=0;
 while(!tick_limit||ticks<tick_limit) {
  if(!installed) {
   int boot_input=0;
   for(size_t i=0;i<proc_n;i++) {
    size q=i*4*address_bits;
    if(space_get(q+2*address_bits,address_bits)==space_nbits+1 &&
       space_get(q+3*address_bits,address_bits)==space_nbits+1 &&
       space_get(q,address_bits)<space_get(q+address_bits,address_bits))boot_input=1;
   }
   if(!boot_input)installed=1;
  }
  if(installed && getenv("PFORTH_STOP_AT_READ") && ticks>0 && space_get(at+1024,32)==20)break;
  if(installed && bad && !replaced && space_get(at+1024,32)==20){if(!freopen(bad,"rb",stdin))return 2;replaced=1;}
  if(ticks%1000000==0)fprintf(stderr,"tick=%"PRIu64" pc=%zu status=%zu\n",ticks,space_get(at+1024,32),space_get(at+1056,32));
  if(!computation())break;
  ticks++;
 }
 fprintf(stderr,"stop ticks=%"PRIu64" pc=%zu status=%zu\n",ticks,space_get(at+1024,32),space_get(at+1056,32));
 const char *dump=getenv("PFORTH_DUMP");if(dump){FILE *f=fopen(dump,"wb");if(!f)return 1;fwrite(space,1,(space_nbits+7)/8,f);fclose(f);}
 destroy_space();return 0;
}
