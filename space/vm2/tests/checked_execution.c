/* Test harness only, built in a temporary directory for fixture validation.
 * No production option, observer or alternative release executable. */
#define computation unvalidated_computation
#include "reference/engine.c"
#undef computation
#include "interval_reference.h"

int computation(void)
{
  if(!intervals_valid(space,space_nbits,proc_n,stderr)) exit(3);
  return unvalidated_computation();
}
