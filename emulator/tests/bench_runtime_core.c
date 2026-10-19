#define _POSIX_C_SOURCE 200809L
/* Optional benchmark of the actual common four-index cycle. */
#include "../src/space.h"
#include <assert.h>
#include <time.h>
static double cpu(void)
{ struct timespec t; assert(clock_gettime(CLOCK_PROCESS_CPUTIME_ID,&t)==0); return t.tv_sec+t.tv_nsec/1e9; }
static unsigned bit(const unsigned char *m,size_t p)
{ return (m[p/8]>>(7-p%8))&1u; }
static void put(unsigned char *m,size_t p,unsigned v)
{ unsigned char b=(unsigned char)(128u>>(p%8));m[p/8]=(m[p/8]&~b)|(v?b:0); }
int main(void)
{
  char *args[]={"emulator","-s","65520","-p","128"};
  parse_config(5,args); init_space();
  for(unsigned fixture=0;fixture<4;fixture++) {
    unsigned count=fixture==0||fixture==3?1:128;
    unsigned length=fixture==3?8191:(fixture==2?128:7);
    unsigned stride=fixture==2?128:8;
    for(size_t b=0;b<space_nbits/8;b++) space[b]=(unsigned char)(b*197+71);
    memset(space,0,proc_n*(size_t)instruction_size/8);
    for(unsigned i=0;i<count;i++) {
      size q[]={8193+stride*i,8193+stride*i+length,
                32773+stride*(count-1-i),32773+stride*(count-1-i)+length};
      for(unsigned k=0;k<4;k++) space_put(address_bits,q[k],((size_t)i*4+k)*address_bits);
    }
    unsigned char *want=malloc(space_nbits/8); assert(want);
    memcpy(want,space,space_nbits/8);
    for(unsigned i=0;i<count;i++)
      for(unsigned k=0;k<length;k++)
        put(want,8193+stride*i+k,bit(space,32773+stride*(count-1-i)+k));
    for(unsigned i=0;i<2;i++) assert(computation());
    assert(!memcmp(want,space,space_nbits/8));
    for(unsigned round=0;round<5;round++) {
      double start=cpu();
      for(unsigned i=0;i<16;i++) assert(computation());
      double end=cpu();
      assert(!memcmp(want,space,space_nbits/8));
      printf("%u,%u,%.9f\n",fixture,round,(end-start)/16);
    }
    free(want);
  }
  destroy_space(); return 0;
}
