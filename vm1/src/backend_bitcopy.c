/* Fast software implementation of the same vm1 memory operation. */
#include "space.h"
void backend_init(void) {}
void backend_shutdown(void) {}
void backend_tick(void)
{
  for(size_t i=0;i<proc_n;i++) {
    size *op=processor[i];
    if(op[0] && op[1]<space_nbits && op[2]<space_nbits)
      bitcpy((size_t)op[0],space,(size_t)op[2],space,(size_t)op[1]);
  }
}
