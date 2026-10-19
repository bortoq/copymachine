/* Independent bit-at-a-time oracle; all tested intervals are nonoverlapping. */
#include "../src/space.h"

static uint64_t rng = UINT64_C(0x42d2c971);
static unsigned long cases;

static unsigned random_byte(void)
{
  rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
  return (unsigned)(rng & 255);
}

static void reference(size_t n, const unsigned char *src, size_t s,
                      unsigned char *dst, size_t d)
{
  size_t i;
  for(i = 0; i < n; ++i)
  {
    unsigned mask = 128u >> ((d+i) % 8);
    if(src[(s+i)/8] & (128u >> ((s+i) % 8))) dst[(d+i)/8] |= mask;
    else dst[(d+i)/8] &= ~mask;
  }
}

static void separate(size_t n, size_t s, size_t d)
{
  /* Exact allocation at the last touched byte enables sanitizer boundary
   * checks; compare entire arrays, including untouched edge bits. */
  size_t ns = (s+n+7)/8+1, nd = (d+n+7)/8+1, i;
  unsigned char *src = malloc(ns), *saved = malloc(ns);
  unsigned char *dst = malloc(nd), *want = malloc(nd);
  if(!src || !saved || !dst || !want) abort();
  for(i = 0; i < ns; ++i) src[i] = random_byte();
  for(i = 0; i < nd; ++i) dst[i] = random_byte();
  memcpy(saved, src, ns); memcpy(want, dst, nd);
  reference(n, saved, s, want, d);
  bitcpy(n, src, s, dst, d);
  if(memcmp(dst, want, nd) || memcmp(src, saved, ns))
  {
    fprintf(stderr, "bitcopy mismatch: separate n=%zu s=%zu d=%zu\n", n,s,d);
    exit(1);
  }
  /* Also exercise no trailing allocation, so read/write lookahead is caught
   * in sanitizer builds, rather than hidden by a canary byte. */
  free(src); free(dst);
  src = malloc(ns-1 ? ns-1 : 1); dst = malloc(nd-1 ? nd-1 : 1);
  if(!src || !dst) abort();
  memcpy(src,saved,ns-1); memcpy(dst,want,nd-1);
  bitcpy(n,src,s,dst,d);
  if(memcmp(dst,want,nd-1)) abort();
  free(src); free(saved); free(dst); free(want); ++cases;
}

static void shared(size_t n, size_t s, size_t d)
{
  size_t bytes = ((s>d?s:d)+n+7)/8+3, i;
  unsigned char *actual = malloc(bytes), *before = malloc(bytes), *want = malloc(bytes);
  if(!actual || !before || !want) abort();
  for(i = 0; i < bytes; ++i) actual[i] = random_byte();
  memcpy(before,actual,bytes); memcpy(want,actual,bytes);
  reference(n,before,s,want,d);
  bitcpy(n,actual,s,actual,d);
  if(memcmp(actual,want,bytes))
  {
    fprintf(stderr,"bitcopy mismatch: shared n=%zu s=%zu d=%zu\n",n,s,d);
    exit(1);
  }
  free(actual); free(before); free(want); ++cases;
}

int main(void)
{
  static const size_t lengths[] = {255,256,257,511,512,513,1023,4095,32768,65536};
  size_t n,s,d,k;
  for(s=0;s<8;++s) for(d=0;d<8;++d)
  {
    for(n=0;n<=192;++n) separate(n,s,d);
    for(k=0;k<sizeof lengths/sizeof *lengths;++k) separate(lengths[k],s,d);
    for(n=0;n<=192;++n)
    {
      size_t other=s+n+d;
      shared(n,s,other); shared(n,other,s);
    }
  }
  for(k=0;k<2048;++k)
  {
    n=(random_byte()*257u+random_byte())%8193;
    s=random_byte(); d=random_byte();
    separate(n,s,d);
    shared(n,s,s+n+d); shared(n,s+n+d,s);
  }
  printf("bitcopy: %lu oracle cases, all alignments, edges and unchanged bits passed\n",cases);
  return 0;
}
