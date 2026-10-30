/* emulator host runtime. MIT, Dmitri Bortoq, 2024-2026.
 * Wire instruction: four A-bit fields [dst_low,dst_high,src_low,src_high].
 * Stream bytes are MSB-first; numeric fields are least-significant-bit first.
 * All memory src/dst ranges of a tick are pairwise disjoint, including src/src.
 */
#ifndef VM1_SPACE_H
#define VM1_SPACE_H
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint64_t size;
enum { SPACE_BITS_DFLT=65520, PROC_N_DFLT=128,
       EXIT_MEMORY=1, EXIT_USAGE=2, ERR_IO=1 };
extern size_t space_nbits, proc_n;
extern uint64_t tick_limit;
extern size address_bits, nfield_bits, instruction_size;
extern unsigned char *space;
/* Decoded four-field processor snapshot; never fetched again during a tick. */
extern size (*instructions)[4];
/* Internal IO/bitcopy view [length,destination,source], not a wire instruction. */
extern size (*processor)[3];
extern FILE *channel_in, *channel_out;
/* Host files of the long copy (15.2): -r path, in order, are the remote spaces 2, 3, ... */
extern const char **remote_paths;
extern size_t nremote;
size space_get(size at, size n);
void space_put(size n, size value, size at);
void bitcpy(size_t n,const void *src,size_t s,void *dst,size_t d);
void parse_config(int argc,char **argv);
void init_space(void);
void destroy_space(void);
int computation(void);
void backend_init(void);
void backend_tick(void);
void backend_shutdown(void);
#endif
