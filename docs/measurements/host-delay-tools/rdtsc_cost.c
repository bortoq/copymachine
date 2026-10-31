#include <x86intrin.h>
#include <stdio.h>
#include <stdint.h>
#include <time.h>
int main(void){ struct timespec a,b; uint64_t s=0,c0,c1; clock_gettime(CLOCK_MONOTONIC,&a); c0=__rdtsc();
 for(int i=0;i<100000000;i++){ uint64_t x=__rdtsc(); uint64_t y=__rdtsc(); s+=y-x; }
 c1=__rdtsc(); clock_gettime(CLOCK_MONOTONIC,&b);
 double ns=(b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec);
 printf("pair of rdtsc: %.1f ns each pair; avg delta %.1f tsc cycles; tsc %.3f GHz\n",ns/1e8,(double)s/1e8,(double)(c1-c0)/ns); return 0;}
