/* Independent snapshot oracle for the real four-index runtime, either backend.
 * Neither expected data nor descriptor decoding uses production helpers.
 */
#include "../src/space.h"
#include <assert.h>
static uint64_t rng=UINT64_C(0x891735cc);
static unsigned cases;
static unsigned random_value(void)
{ rng^=rng<<13; rng^=rng>>7; rng^=rng<<17; return (unsigned)rng; }
static unsigned get(const unsigned char *m,size_t p)
{ return (m[p/8]>>(7-p%8))&1u; }
static void put(unsigned char *m,size_t p,unsigned v)
{ unsigned char mask=(unsigned char)(128u>>(p%8)); m[p/8]=(m[p/8]&~mask)|(v?mask:0); }
static void field(unsigned char *m,size_t p,unsigned a,size v)
{ for(unsigned k=0;k<a;k++) put(m,p+k,(unsigned)((v>>k)&1u)); }
static size read_field(const unsigned char *m,size_t p,unsigned a)
{ size v=0; for(unsigned k=0;k<a;k++) v|=(size)get(m,p+k)<<k; return v; }
static void instruction(unsigned i,size dl,size dh,size sl,size sh)
{
  size q[]={dl,dh,sl,sh};
  for(unsigned k=0;k<4;k++) field(space,((size_t)i*4+k)*address_bits,(unsigned)address_bits,q[k]);
}
static void check(void)
{
  size_t bytes=space_nbits/8+(space_nbits%8!=0);
  unsigned char *before=malloc(bytes),*want=malloc(bytes),*used=calloc(space_nbits,1);
  int active=0;
  assert(before&&want&&used);
  memcpy(before,space,bytes); memcpy(want,before,bytes);
  for(size_t i=0;i<proc_n;i++) {
    size q[4];
    for(unsigned k=0;k<4;k++) q[k]=read_field(before,(i*4+k)*address_bits,(unsigned)address_bits);
    if(q[2]==q[3]) continue;
    active=1;
    assert(q[0]<q[1]&&q[2]<q[3]&&q[1]<=space_nbits&&q[3]<=space_nbits);
    assert(q[1]-q[0]==q[3]-q[2]);
    for(size k=0;k<q[1]-q[0];k++) {
      assert(!used[q[0]+k]); used[q[0]+k]=1;
      assert(!used[q[2]+k]); used[q[2]+k]=1;
      put(want,(size_t)(q[0]+k),get(before,(size_t)(q[2]+k)));
    }
  }
  assert(computation()==active);
  if(memcmp(want,space,bytes)) {
    fprintf(stderr,"whole-memory mismatch N=%zu P=%zu case=%u\n",space_nbits,proc_n,cases);
    exit(1);
  }
  cases++; free(before);free(want);free(used);
}
static void profile(const char *n,const char *p,unsigned rounds)
{
  char *args[]={"emulator","-s",(char *)n,"-p",(char *)p};
  parse_config(5,args); init_space();
  size_t bytes=space_nbits/8+(space_nbits%8!=0), home=proc_n*(size_t)instruction_size;
  size_t stride=(space_nbits-home)/(2*proc_n);
  assert(stride>=2);
  for(unsigned r=0;r<rounds;r++) {
    for(size_t b=0;b<bytes;b++) space[b]=(unsigned char)random_value();
    for(size_t b=0;b<home;b++) put(space,b,0);
    for(unsigned i=0;i<proc_n;i++) {
      if((random_value()&3)==0) continue;
      size_t len=1+random_value()%(stride-1);
      size_t dst=home+stride*i,src=home+stride*(2*proc_n-1-i)+1;
      if(random_value()&1) { size_t tmp=src;src=dst;dst=tmp; }
      instruction(i,dst,dst+len,src,src+len);
    }
    check(); check(); /* Repeat a layer and preserve all untouched data. */
  }
  /* Erase the entire live processor with one copy; next tick must be idle. */
  memset(space,0,bytes);
  size_t source=space_nbits-home;
  assert(source>=home);
  instruction(0,0,home,source,source+home);
  check(); check();
  destroy_space();
}
static void test_field_reads(void)
{
  unsigned char data[10];unsigned char *saved=space;space=data;
  for(unsigned trial=0;trial<256;trial++) {
    for(size_t k=0;k<sizeof data;k++)data[k]=(unsigned char)random_value();
    for(unsigned n=0;n<=64;n++)for(unsigned at=0;at+n<=80;at++)
      assert(space_get(at,n)==read_field(data,at,n));
  }
  space=saved;
}
int main(void)
{
  test_field_reads();
  /* Exact-size codec windows cover widths that do not require enormous RAM. */
  for(unsigned width=1;width<=64;width++)
    for(unsigned offset=0;offset<8;offset++) {
      size_t bytes=(width+offset+7)/8;
      space=calloc(bytes,1); assert(space);
      size value=width==64?UINT64_MAX:(((size)1<<width)-1);
      for(unsigned k=0;k<width;k++) put(space,offset+k,(unsigned)((value>>k)&1));
      assert(space_get(offset,width)==value);
      memset(space,0,bytes); space_put(width,value,offset);
      assert(read_field(space,offset,width)==value);
      free(space); space=NULL;
    }
  channel_in=tmpfile();channel_out=tmpfile();assert(channel_in&&channel_out);
  profile("240","2",120); profile("256","2",120);
  profile("1040","8",80); profile("65520","128",30);
#ifndef VM1_TEST_NETWORK
  {
    char *args[]={"emulator","-s","536870896","-p","256"};
    parse_config(5,args); init_space();
    size_t bytes=(space_nbits+7)/8;
    unsigned char *want=calloc(bytes,1); assert(want);
    memset(space,0,proc_n*(size_t)instruction_size/8);
    for(unsigned k=0;k<31;k++) put(space,space_nbits-64+k,(k%3)==0);
    instruction(0,65537,65568,space_nbits-64,space_nbits-33);
    memcpy(want,space,bytes);
    for(unsigned k=0;k<31;k++) put(want,65537+k,(k%3)==0);
    assert(computation()==1); assert(!memcmp(space,want,bytes));
    cases++; free(want); destroy_space();
  }
#endif
  fclose(channel_in);fclose(channel_out);
  printf("runtime whole-memory snapshot oracle: %u cases passed\n",cases);
  return 0;
}
