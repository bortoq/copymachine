/* emulator common four-index runtime. MIT, Dmitri Bortoq, 2024-2026. */
#include "space.h"
#include "sys_ctrl.h"
#include "proto_gen.h"
#include <errno.h>
#include <signal.h>

size_t space_nbits=SPACE_BITS_DFLT, proc_n=PROC_N_DFLT;
uint64_t tick_limit;
size address_bits,nfield_bits,instruction_size;
unsigned char *space;
size (*instructions)[4];
size (*processor)[3];
FILE *channel_in,*channel_out;
const char **remote_paths; size_t nremote; /* -r path: remote spaces 2.. (15.2) */

size space_get(size at,size n)
{
  /* Reverse each byte once, then extract its little-endian numeric bits.
   * Read only bytes intersecting the field, including fields at space end. */
  static const unsigned char reverse4[16]={0,8,4,12,2,10,6,14,1,9,5,13,3,11,7,15};
  size v=0,done=0;
  while(done<n) {
    unsigned offset=(unsigned)(at%8),take=8-offset;
    if((size)take>n-done)take=(unsigned)(n-done);
    unsigned byte=space[at/8];
    unsigned reversed=(unsigned)(reverse4[byte&15]<<4)|reverse4[byte>>4];
    v|=(size)((reversed>>offset)&(255u>>(8-take)))<<done;
    at+=take;done+=take;
  }
  return v;
}
void space_put(size n,size value,size at)
{
  for(size k=0;k<n;k++) {
    unsigned char mask=(unsigned char)(128u>>((at+k)%8));
    if((value>>k)&1u) space[(at+k)/8]|=mask;
    else space[(at+k)/8]&=(unsigned char)~mask;
  }
}
static void usage(void)
{
  fputs("usage: emulator [-s bits] [-p instructions] [-t ticks] [-r path]...\n",stderr);
  exit(EXIT_USAGE);
}
static uint64_t number(const char *s)
{
  char *end;
  unsigned long long v;
  if(*s<'0'||*s>'9') usage();
  errno=0; v=strtoull(s,&end,10);
  if(errno||*end) usage();
  return (uint64_t)v;
}
void parse_config(int argc,char **argv)
{
  for(int i=1;i<argc;i++) {
    const char *arg=argv[i],*v;
    uint64_t n;
    if(arg[0]!='-'||(arg[1]!='s'&&arg[1]!='p'&&arg[1]!='t'&&arg[1]!='r')) usage();
    v=arg+2;
    if(!*v) { if(++i==argc) usage(); v=argv[i]; }
    if(arg[1]=='r') {   /* a host file, the remote space 2+k of the long copy */
      const char **grown=realloc(remote_paths,(nremote+1)*sizeof *remote_paths);
      if(!grown) { fputs("emulator: out of memory\n",stderr); exit(EXIT_MEMORY); }
      remote_paths=grown; remote_paths[nremote++]=v;
      continue;
    }
    n=number(v);
    if(arg[1]=='t') tick_limit=n;
    else {
      if(n>SIZE_MAX) usage();
      if(arg[1]=='s') space_nbits=(size_t)n; else proc_n=(size_t)n;
    }
  }
  if(!space_nbits||!proc_n) usage();
  address_bits=0;
  for(size_t n=space_nbits;n;n>>=1) ++address_bits;
  instruction_size=4*address_bits;
  nfield_bits=address_bits; /* SYS counts cover a full emulator memory range. */
  if(proc_n>space_nbits/instruction_size) usage();
  if((proc_n*instruction_size)/8 + ((proc_n*instruction_size)%8!=0)>space_nbits/8) usage();
  /* Highest reserved channel is S+PROTO_NDEVS; never shift by 64. */
  if(space_nbits>UINT64_MAX-PROTO_NDEVS) usage();
  if(address_bits<64 && space_nbits+PROTO_NDEVS>(((size)1<<address_bits)-1)) usage();
}
void init_space(void)
{
  size_t bytes=space_nbits/8+(space_nbits%8!=0);
#ifdef SIGPIPE
  signal(SIGPIPE,SIG_IGN);
#endif
  if(!channel_in) channel_in=stdin;
  if(!channel_out) channel_out=stdout;
  setvbuf(channel_out,NULL,_IONBF,0);
  if(proc_n>SIZE_MAX/sizeof *instructions || proc_n>SIZE_MAX/sizeof *processor)
    goto memory_error;
  space=calloc(bytes,1);
  instructions=calloc(proc_n,sizeof *instructions);
  processor=calloc(proc_n,sizeof *processor);
  if(!space||!instructions||!processor) goto memory_error;
  sys_init();
  backend_init();
  /* The host seeds exactly one ordinary channel instruction. No image parser. */
  space_put(address_bits,0,0);
  space_put(address_bits,((proc_n*instruction_size+7)/8)*8,address_bits);
  space_put(address_bits,space_nbits+1,2*address_bits);
  space_put(address_bits,space_nbits+1,3*address_bits);
  return;
 memory_error:
  fputs("emulator: out of memory\n",stderr);
  exit(EXIT_MEMORY);
}
void destroy_space(void)
{
  backend_shutdown(); sys_shutdown();
  free(space); free(instructions); free(processor); free(remote_paths);
  remote_paths=NULL; nremote=0;
  space=NULL; instructions=NULL; processor=NULL;
}
int computation(void)
{
  int active=0;
  for(size_t i=0;i<proc_n;i++) {
    size *q=instructions[i],*op=processor[i];
    for(size k=0;k<4;k++) q[k]=space_get((i*4+k)*address_bits,address_bits);
    op[0]=0; op[1]=q[0]; op[2]=q[2];
    if(q[0]==q[1] && q[0]>=space_nbits) {
      if(q[2]<q[3] && q[3]<=space_nbits) op[0]=q[3]-q[2];
    } else if(q[2]==q[3] && q[2]>=space_nbits) {
      if(q[0]<q[1] && q[1]<=space_nbits) op[0]=q[1]-q[0];
    } else if(q[2]<q[3]) op[0]=q[3]-q[2];
    if(op[0]) active=1;
  }
  if(!active) return 0;
  /* Valid channel buffers and ordinary ranges are disjoint. Neither this
   * host ordering nor sequential bitcpy gives same-tick readiness to guests. */
  sys_tick();
  backend_tick();
  return 1;
}
#ifndef VM1_NO_MAIN
int main(int argc,char **argv)
{
  parse_config(argc,argv); init_space();
  for(uint64_t tick=0;!tick_limit||tick<tick_limit;tick++)
    if(!computation()) break;
  fflush(stdout); destroy_space();
  return 0;
}
#endif
