/* Test-only oracle over all operand intervals; no generator dependencies. */
#ifndef INTERVAL_REFERENCE_H
#define INTERVAL_REFERENCE_H
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

typedef struct { uint64_t lo,hi; size_t slot; const char *side; } operand_interval;
static uint64_t operand_field(const unsigned char *mem,size_t at,unsigned width)
{
  uint64_t value=0;
  for(unsigned k=0;k<width;++k)
    if(mem[(at+k)/8]&(128u>>((at+k)%8))) value|=UINT64_C(1)<<k;
  return value;
}
static int operand_compare(const void *a,const void *b)
{
  const operand_interval *x=a,*y=b;
  return x->lo<y->lo?-1:x->lo>y->lo?1:x->hi<y->hi?-1:x->hi>y->hi;
}
static int intervals_valid(const unsigned char *mem,uint64_t bits,size_t slots,FILE *diagnostic)
{
  unsigned a=0; uint64_t v=bits; size_t used=0;
  operand_interval *all=malloc(2*slots*sizeof *all);
  uint64_t *devices=malloc(slots*sizeof *devices); size_t ndevices=0,requests=0;
  uint64_t request_at=0;
  if(!all || !devices) abort();
  while(v) { ++a; v>>=1; }
  for(size_t i=0;i<slots;++i)
  {
    size_t at=i*(3*a-1);
    uint64_t n=operand_field(mem,at,a-1),d=operand_field(mem,at+a-1,a),s=operand_field(mem,at+2*a-1,a);
    if(!n) continue;
    uint64_t pos[2]={s,d}; const char *side[2]={"src","dst"};
    if(s>=bits && d>=bits) goto invalid;
    if(s>=bits || d>=bits)
    {
      uint64_t device=s>=bits?s:d;
      if(device>bits)
      {
        for(size_t k=0;k<ndevices;++k) if(devices[k]==device) goto invalid;
        devices[ndevices++]=device;
      }
      else if(d==bits) { request_at=s; if(++requests>1) goto invalid; }
    }
    for(unsigned j=0;j<2;++j) if(pos[j]<bits)
    {
      uint64_t width=n;
      if(s>=bits || d>=bits)
      {
        uint64_t device=s>=bits?s:d;
        if(device==bits) width=d==bits?(n>120+a?n:120+a):96+a;
        else width=(n+7)/8*8;
      }
      if(width>bits-pos[j]) goto invalid;
      all[used++]=(operand_interval){pos[j],pos[j]+width,i,side[j]};
    }
  }
  /* Decode control independently from the pre-tick memory image. Even
   * disjoint buffers cannot make control and target transfer independent. */
  if(requests) {
    uint64_t op=operand_field(mem,request_at,8);
    uint64_t target=operand_field(mem,request_at+8,a);
    if(op==1 || op==2 || op==3)
      for(size_t k=0;k<ndevices;++k) if(devices[k]==target) goto invalid;
  }
  qsort(all,used,sizeof *all,operand_compare);
  for(size_t j=1;j<used;++j) if(all[j].lo<all[j-1].hi)
  {
    if(diagnostic) fprintf(diagnostic,"overlapping tick operands: slot %zu %s [%llu,%llu) and slot %zu %s [%llu,%llu)\n",
      all[j-1].slot,all[j-1].side,(unsigned long long)all[j-1].lo,(unsigned long long)all[j-1].hi,
      all[j].slot,all[j].side,(unsigned long long)all[j].lo,(unsigned long long)all[j].hi);
    free(devices); free(all); return 0;
  }
  free(devices); free(all); return 1;
invalid:
  if(diagnostic) fprintf(diagnostic,"invalid tick operand range or channel conflict\n");
  free(devices); free(all); return 0;
}
#endif
