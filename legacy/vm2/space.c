/*
 * EMULATION OF PARALLEL ADDRESS SPACE (SYS + pre-bound data channels)
 *
 * copyright 2022-12-17, dmitri bortoq, mit license
 *
 * Entry point: flag parsing, seed of the core, engine ticks.
 * Usage: space [-s bits] [-p num] [-t ticks] < user_space > result.
 * The program guarantees half-interval non-overlap,
 * the emulator relies on it (never checks).
 * In one tick ALL source and destination memory intervals are pairwise
 * disjoint, including sources of different instructions (no read fan-out).
 * This is the program's obligation; the production engine does not check it.
 */
#include "space.h"
#include "sys_ctrl.h"

int main(int argc, char **argv)
{
  /* configuration and address space */
  uint64_t time;

  parse_config(argc, argv);
  time = tick_limit;

  init_space();

  /*
   * emulate computation (tick runs to end even with no live instructions;
   * stop: all NOP or tick limit)
   */
  while((tick_limit == 0 || time--))
  {
    if(!computation())
      break;
  }

  fflush(stdout);
  sys_shutdown();
  free(space);
  free(processor);
  return 0;
}
