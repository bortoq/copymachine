/* Fast software implementation of the same emulator memory operation. */
#include "space.h"
void backend_init(void) {}
void backend_shutdown(void) {}
/* The part of the copy beyond the end of the space (rare): reads as zeros, a write there is lost. */
static void copy_edge(size n,size s,size d)
{
  size nr=s<space_nbits?space_nbits-s:0,nw=space_nbits-d; /* readable and writable bits */
  if(n>nw) n=nw;
  if(nr>n) nr=n;
  if(nr) bitcpy((size_t)nr,space,(size_t)s,space,(size_t)d);
  for(size k=nr;k<n;k++) space[(d+k)/8]&=(unsigned char)~(128u>>((d+k)%8));
}
void backend_tick(void)
{
  for(size_t i=0;i<proc_n;i++) {
    size *op=processor[i];
    if(op[0] && op[1]<space_nbits && op[2]<space_nbits) {
      if(op[0]<=space_nbits-op[1] && op[0]<=space_nbits-op[2])
        bitcpy((size_t)op[0],space,(size_t)op[2],space,(size_t)op[1]);
      else copy_edge(op[0],op[2],op[1]);
    }
  }
}
