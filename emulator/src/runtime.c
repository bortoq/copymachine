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
static unsigned char *shadow;
static size_t record_bytes;
static int shadow_valid;
const char **remote_paths; size_t nremote; /* -r path: remote spaces 2.. (15.2) */

/* Bit-reversed byte: stream bytes are MSB-first, numeric fields LSB-first. */
static const unsigned char reverse8[256]={
  0,128,64,192,32,160,96,224,16,144,80,208,48,176,112,240,
  8,136,72,200,40,168,104,232,24,152,88,216,56,184,120,248,
  4,132,68,196,36,164,100,228,20,148,84,212,52,180,116,244,
  12,140,76,204,44,172,108,236,28,156,92,220,60,188,124,252,
  2,130,66,194,34,162,98,226,18,146,82,210,50,178,114,242,
  10,138,74,202,42,170,106,234,26,154,90,218,58,186,122,250,
  6,134,70,198,38,166,102,230,22,150,86,214,54,182,118,246,
  14,142,78,206,46,174,110,238,30,158,94,222,62,190,126,254,
  1,129,65,193,33,161,97,225,17,145,81,209,49,177,113,241,
  9,137,73,201,41,169,105,233,25,153,89,217,57,185,121,249,
  5,133,69,197,37,165,101,229,21,149,85,213,53,181,117,245,
  13,141,77,205,45,173,109,237,29,157,93,221,61,189,125,253,
  3,131,67,195,35,163,99,227,19,147,83,211,51,179,115,243,
  11,139,75,203,43,171,107,235,27,155,91,219,59,187,123,251,
  7,135,71,199,39,167,103,231,23,151,87,215,55,183,119,247,
  15,143,79,207,47,175,111,239,31,159,95,223,63,191,127,255};
size space_get(size at,size n)
{
  /* Reverse each byte once, then extract its little-endian numeric bits.
   * Read only bytes intersecting the field, including fields at space end. */
  static const unsigned char reverse4[16]={0,8,4,12,2,10,6,14,1,9,5,13,3,11,7,15};
  size v=0,done=0;
  if(n%8==0&&n<=64&&at%8==0) { /* whole bytes (32 bits is the common field) */
    const unsigned char *p=space+at/8;
    if(n==32) return (size)reverse8[p[0]]|(size)reverse8[p[1]]<<8|(size)reverse8[p[2]]<<16|(size)reverse8[p[3]]<<24;
    for(;done<n;done+=8) v|=(size)reverse8[*p++]<<done;
    return v;
  }
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
  if(n%8==0&&n<=64&&at%8==0) { /* whole bytes: store the reversed bytes */
    unsigned char *p=space+at/8;
    for(size done=0;done<n;done+=8) *p++=reverse8[(value>>done)&255u];
    return;
  }
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
  free(space); free(instructions); free(processor); free(remote_paths); free(shadow); shadow=NULL; shadow_valid=0;
  remote_paths=NULL; nremote=0;
  space=NULL; instructions=NULL; processor=NULL;
}
/* The records of the processors are decoded only when their bits changed since the last tick: most of the
 * records of a layer (the idle ones) are rewritten with the same bits, and decoding is the dearest part of a
 * tick that does not depend on the work. shadow holds the bits as they were decoded. */
/* A 32-bit field at a byte, as space_get(at,32). */
static inline size get32(const unsigned char *p)
{
  return (size)reverse8[p[0]]|(size)reverse8[p[1]]<<8|(size)reverse8[p[2]]<<16|(size)reverse8[p[3]]<<24;
}
static inline void decode_record(size_t i)
{
  size *q=instructions[i],*op=processor[i];
  if(address_bits==32 && instruction_size%8==0) {
    const unsigned char *p=space+i*record_bytes;
    q[0]=get32(p); q[1]=get32(p+4); q[2]=get32(p+8); q[3]=get32(p+12);
  } else for(size k=0;k<4;k++) q[k]=space_get((i*4+k)*address_bits,address_bits);
  op[0]=0; op[1]=q[0]; op[2]=q[2];
  if(q[0]==q[1] && q[0]>=space_nbits) {
    if(q[2]<q[3] && q[3]<=space_nbits) op[0]=q[3]-q[2];
  } else if(q[2]==q[3] && q[2]>=space_nbits) {
    if(q[0]<q[1] && q[1]<=space_nbits) op[0]=q[1]-q[0];
  } else if(q[2]<q[3]) op[0]=q[3]-q[2];
}
static inline int record_changed(const unsigned char *a,const unsigned char *b)
{
  if(record_bytes==16) {
    uint64_t x[2],y[2];
    memcpy(x,a,16); memcpy(y,b,16);
    return ((x[0]^y[0])|(x[1]^y[1]))!=0;
  }
  return memcmp(a,b,record_bytes)!=0;
}
int computation(void)
{
  int active=0,channel_op=0;
  size_t n=proc_n;
  if(!shadow) {  /* decode every record at the first tick, and when the records are not whole bytes */
    if(instruction_size%8==0) {
      record_bytes=instruction_size/8;
      shadow=malloc(n*record_bytes);
      if(!shadow) { fputs("emulator: out of memory\n",stderr); exit(EXIT_MEMORY); }
    }
    shadow_valid=0;
  }
  for(size_t i=0;i<n;i++) {
    if(shadow) {
      const unsigned char *now=space+i*record_bytes; unsigned char *was=shadow+i*record_bytes;
      if(!shadow_valid || record_changed(now,was)) { decode_record(i); if(record_bytes==16) memcpy(was,now,16); else memcpy(was,now,record_bytes); }
    } else decode_record(i);
    size *op=processor[i];
    if(op[0]) { active=1; if(op[1]>=space_nbits||op[2]>=space_nbits) channel_op=1; }
  }
  shadow_valid=shadow!=NULL;
  if(!active) return 0;
  /* Valid channel buffers and ordinary ranges are disjoint. Neither this
   * host ordering nor sequential bitcpy gives same-tick readiness to guests.
   * Only an operation with a channel position as an end is served by SYS. */
  if(channel_op) sys_tick();
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
