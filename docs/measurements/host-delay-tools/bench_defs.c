/* time of the host definitions of 18.13 outside the emulator loop: the definition alone (input already in hv),
 * and the whole call (copy in, definition, copy out, return value) at a request in the space.
 * build: cc -O2 -DVM1_NO_MAIN -I SRC bench_defs.c SRC/runtime.c SRC/bitcopy.c SRC/backend_bitcopy.c -o bench_defs */
#define _POSIX_C_SOURCE 200809L
#include "sys_ctrl.c"
#include <time.h>
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec*1e9+t.tv_nsec; }
int main(int argc,char **argv)
{
  char *av[]={"x","-s","2147483648","-p","8",NULL};
  (void)argc;(void)argv;
  parse_config(5,av); init_space();
  size rb=sys_req_bits(), base=1u<<20, lo=1u<<24, hi=1u<<25;
  int R=2000000;
  for(int def=0;def<3;def++) for(int variant=0;variant<(def==1?4:2);variant++) {
    size cells=32, payload_bits=0;
    /* build the input image in hv and in the space after the request */
    unsigned char *keep=space;
    size nrow=4;
    space=hv; memset(hv,0,HV_IN_BITS/8);
    if(def==0){ size nr=variant?7:3; space_put(32,1u<<30,0); size rows[4]={1,5,3,9}; for(int j=0;j<4;j++) space_put(32,rows[j],168+64*j);
      space_put(32,nr,424+128); for(size k=0;k<nr;k++) for(int j=0;j<4;j++) space_put(32,(j&1)?100+k:50+k+j,424+64*(3+4*k+j)); payload_bits=2408; }
    if(def==1){ cells=variant==0?32:variant==1?8:4096/4; space_put(32,cells*4,0); space_put(32,65,32); space_put(32,variant==3?1:0,64); payload_bits=96; if(variant==3) space_put(32,127,0); }
    if(def==2){ space_put(32,32,0); space_put(32,variant?8:4,32); space_put(32,variant?8:4,64); nrow=variant?8:4; for(size j=0;j<nrow*4;j++) space_put(32,j*77+3,168+64*j); payload_bits=2216; }
    space=keep;
    unsigned char in[HV_IN_BITS/8]; memcpy(in,hv,sizeof in);
    size out=0,ret=0,disp=0;
    double t0=now();
    for(int r=0;r<R;r++) { host_defs[def](payload_bits,&out,&ret,&disp); __asm__ volatile(""::"r"(out),"r"(ret):"memory"); }
    double t1=now();
    /* whole call */
    unsigned char *k2=space; space=hv; (void)k2; space=k2;
    for(size b=0;b<payload_bits;b++) { /* copy image bit by bit into space after the request */
      int bit=(in[b/8]>>(7-b%8))&1; size at=base+rb+b; unsigned char m=(unsigned char)(128u>>(at%8)); if(bit) space[at/8]|=m; else space[at/8]&=~m; }
    size v[5]={7,0,0,(size)def,lo|(hi<<32)};
    double t2=now();
    for(int r=0;r<R;r++) { int rc=host_call1(base,rb+payload_bits,v); __asm__ volatile(""::"r"(rc):"memory"); }
    double t3=now();
    printf("def %d variant %d (out %llu bits, ret %llu): definition %.0f ns, whole call %.0f ns\n",def,variant,(unsigned long long)out,(unsigned long long)ret,(t1-t0)/R,(t3-t2)/R);
  }
  /* the reference: plain C of the same work on plain arrays */
  {
    static uint32_t a[4096]; double t0=now(); volatile uint32_t sink=0;
    for(int r=0;r<R;r++) { for(int k=0;k<32;k++) a[k]=65u*16843009u; __asm__ volatile(""::"r"(a):"memory"); }
    double t1=now(); sink=a[0];
    printf("plain C fill of 32 cells (loop, vectorised): %.1f ns\n",(t1-t0)/R);
    t0=now(); for(int r=0;r<R;r++) { memset(a,65,128); __asm__ volatile(""::"r"(a):"memory"); } t1=now();
    printf("plain C memset 128 bytes: %.1f ns\n",(t1-t0)/R); (void)sink;
    typedef struct{uint32_t l,h;}iv; iv x[2]={{1,5},{3,9}},y[2]={{2,6},{4,8}}; volatile uint32_t sz=1u<<30; int cl=0;
    t0=now(); for(int r=0;r<R;r++){ x[0].l=(uint32_t)r; cl=0; for(int j=0;j<2;j++)for(int i=0;i<2;i++) if(x[j].l<x[j].h&&y[i].l<y[i].h&&x[j].l<y[i].h&&y[i].l<x[j].h&&x[j].l<sz&&y[i].l<sz) cl=-1; __asm__ volatile(""::"r"(cl):"memory"); } t1=now();
    { uint32_t cells[16], outb[16]; for(int k=0;k<16;k++) cells[k]=k*77+3; double q0=now(); for(int r=0;r<R;r++){ cells[0]=r; for(int k=0;k<16;k++){ uint32_t v=cells[k]; v=((v>>1)&0x55555555u)|((v&0x55555555u)<<1); v=((v>>2)&0x33333333u)|((v&0x33333333u)<<2); v=((v>>4)&0x0f0f0f0fu)|((v&0x0f0f0f0fu)<<4); outb[k]=v; } __asm__ volatile(""::"r"(outb):"memory"); } double q1=now(); printf("plain C encode of 4 rows (16 cells, bit-reversed bytes): %.1f ns\n",(q1-q0)/R); }
    printf("plain C row clash (4 interval pairs): %.1f ns\n",(t1-t0)/R);
  }
  return 0;
}
