#define _POSIX_C_SOURCE 200809L
/* Include the implementation only to exercise its private decoders with
 * small exact-size windows, including widths needing impractical full RAM.
 * Oracles below use their own bit codec, never space_get/put or bitcpy. */
#define computation unvalidated_computation
#include "../engine.c"
#undef computation
#include "interval_reference.h"

int computation(void)
{
  if(!intervals_valid(space,space_nbits,proc_n,stderr)) exit(1);
  return unvalidated_computation();
}
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#define REQUIRE(c) do { if(!(c)) { fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#c); exit(1); } } while(0)
static uint64_t rng=UINT64_C(0x915bfd70);
static size_t decoder_cases, tick_cases;

static uint64_t random_value(void)
{
  rng^=rng<<13; rng^=rng>>7; rng^=rng<<17; return rng;
}

static uint64_t mask(unsigned width)
{
  return width==64?UINT64_MAX:((UINT64_C(1)<<width)-1);
}

static void put(unsigned char *b, size_t at, unsigned width, uint64_t value)
{
  unsigned j;
  for(j=0;j<width;++j)
  {
    unsigned m=128u>>((at+j)%8);
    if((value>>j)&1) b[(at+j)/8]|=m; else b[(at+j)/8]&=~m;
  }
}

static uint64_t get(const unsigned char *b,size_t at,unsigned width)
{
  uint64_t value=0;
  unsigned j;
  for(j=0;j<width;++j)
    if(b[(at+j)/8]&(128u>>((at+j)%8))) value|=UINT64_C(1)<<j;
  return value;
}

static void row(unsigned char *b,size_t at,size n,size dst,size src)
{
  put(b,at,nfield_bits,n); put(b,at+nfield_bits,address_bits,dst);
  put(b,at+nfield_bits+address_bits,address_bits,src);
}

static void refcopy(unsigned char *dst,const unsigned char *src,size n,size d,size s0)
{
  size j;
  for(j=0;j<n;++j)
  {
    unsigned m=128u>>((d+j)%8);
    if(src[(s0+j)/8]&(128u>>((s0+j)%8))) dst[(d+j)/8]|=m;
    else dst[(d+j)/8]&=~m;
  }
}

static void decoders(void)
{
  unsigned a,shift,padded,k;
  proc_n=7; processor=calloc(proc_n,sizeof *processor); REQUIRE(processor);
  for(a=5;a<=64;++a) for(shift=0;shift<8;++shift) for(padded=0;padded<2;++padded)
  {
    size_t at=32+shift, bytes=(at+3*a-1+7)/8+(padded?16:0);
    address_bits=a; nfield_bits=a-1; instruction_size=3*a-1;
    o[0]=0; o[1]=a-1; o[2]=2*a-1;
    s[0]=a-1; s[1]=s[2]=a;
    space_nbits=bytes*8; space=malloc(bytes); REQUIRE(space);
    for(k=0;k<40;++k)
    {
      size n=k==0?0:k==1?mask(a-1):random_value()&mask(a-1);
      size dst=k==1?mask(a):random_value()&mask(a);
      size src=k==2?mask(a):random_value()&mask(a);
      memset(space,0xa5,bytes); row(space,at,n,dst,src);
      if(instruction_size<=57) fetch_instruction_rev(3,at);
      else if(instruction_size<=120) fetch_instruction_rev128(3,at);
      else fetch_instruction_at(3,at);
      REQUIRE(processor[3][0]==n);
      if(n) REQUIRE(processor[3][1]==dst && processor[3][2]==src);
      ++decoder_cases;
    }
    free(space);
  }
  free(processor); space=NULL; processor=NULL;
}

static void setup(size_t bits,size_t slots,FILE *in,FILE *out)
{
  char bs[32],ps[32];
  char *argv[]={"space","-s",bs,"-p",ps};
  snprintf(bs,sizeof bs,"%zu",bits); snprintf(ps,sizeof ps,"%zu",slots);
  channel_in=in; channel_out=out;
  parse_config(5,argv); init_space();
}

static void cleanup(FILE *in,FILE *out)
{
  sys_shutdown(); fclose(in); fclose(out); free(space); free(processor);
  space=NULL; processor=NULL; channel_in=NULL; channel_out=NULL;
}

/* Snapshot operands before writes, then compare every memory byte after
 * each tick, including processor and untouched padding/data. */
static int model_tick(unsigned char *expected)
{
  size_t bytes=(space_nbits+7)/8,i;
  unsigned char *before=malloc(bytes);
  int live=0;
  REQUIRE(before); memcpy(before,expected,bytes);
  for(i=0;i<proc_n;++i)
  {
    size at=i*instruction_size,n=get(before,at,nfield_bits);
    size d=get(before,at+nfield_bits,address_bits),s0=get(before,at+nfield_bits+address_bits,address_bits);
    if(n) { live=1; refcopy(expected,before,n,d,s0); }
  }
  free(before); return live;
}

static void programs(void)
{
  static const size_t formats[][2]={{65520,7},{65520,8},{65520,9},{65520,64},
                                  {262128,8},{524272,9},{1048560,8},{2097136,9}};
  size_t f,trial;
  for(f=0;f<sizeof formats/sizeof *formats;++f) for(trial=0;trial<12;++trial)
  {
    FILE *in=tmpfile(),*out=tmpfile(); size_t bytes,i,t,layer,base,data;
    unsigned char *expected;
    REQUIRE(in && out); setup(formats[f][0],formats[f][1],in,out);
    bytes=(space_nbits+7)/8; layer=proc_n*instruction_size;
    base=(layer+7)/8*8+64; data=space_nbits-8192;
    for(i=0;i<bytes;++i) space[i]=random_value()&255;
    /* Eight immutable future layers and an all-NOP last layer. */
    for(t=0;t<9;++t)
    {
      size_t home=t?base+(t-1)*((layer+7)/8*8):0;
      size_t link=random_value()%proc_n;
      memset(space+home/8,0,(layer+7)/8);
      if(t==8) continue;
      for(i=0;i<proc_n;++i)
      {
        if(i==link) row(space,home+i*instruction_size,layer,0,base+t*((layer+7)/8*8));
        else row(space,home+i*instruction_size,1+random_value()%31,
                 data+i*48,space_nbits-4096+i*48+random_value()%16);
      }
    }
    expected=malloc(bytes); REQUIRE(expected); memcpy(expected,space,bytes);
    for(t=0;t<9;++t)
    {
      int live=model_tick(expected);
      REQUIRE(computation()==live);
      REQUIRE(memcmp(expected,space,bytes)==0); ++tick_cases;
    }
    free(expected); cleanup(in,out);
  }
}

static void validator_regressions(void)
{
  FILE *in=tmpfile(),*out=tmpfile(); REQUIRE(in && out); setup(65520,8,in,out);
  memset(space,0,(proc_n*instruction_size+7)/8);
  row(space,0,4,2000,1000); row(space,instruction_size,4,3000,1000);
  REQUIRE(!intervals_valid(space,space_nbits,proc_n,NULL));
  row(space,instruction_size,4,3000,1002);
  REQUIRE(!intervals_valid(space,space_nbits,proc_n,NULL));
  row(space,instruction_size,4,2004,1004);
  REQUIRE(intervals_valid(space,space_nbits,proc_n,NULL));
  row(space,instruction_size,4,1001,3000);
  REQUIRE(!intervals_valid(space,space_nbits,proc_n,NULL));
  row(space,instruction_size,4,2001,3000);
  REQUIRE(!intervals_valid(space,space_nbits,proc_n,NULL));
  row(space,instruction_size,0,0,0); row(space,0,4,1001,1000);
  REQUIRE(!intervals_valid(space,space_nbits,proc_n,NULL));
  row(space,0,0,1000,1000); REQUIRE(intervals_valid(space,space_nbits,proc_n,NULL));
  for(unsigned op=1;op<=3;++op) {
    memset(space,0,(proc_n*instruction_size+7)/8);
    put(space,1001,8,op); put(space,1009,address_bits,space_nbits+1);
    row(space,0,120+address_bits,space_nbits,1001);
    row(space,instruction_size,8,9001,space_nbits+1);
    REQUIRE(!intervals_valid(space,space_nbits,proc_n,NULL));
    put(space,1009,address_bits,space_nbits+2);
    REQUIRE(intervals_valid(space,space_nbits,proc_n,NULL));
  }
  cleanup(in,out);
}

static void self_patch_and_seed(void)
{
  unsigned order;
  for(order=0;order<2;++order)
  {
    FILE *in=tmpfile(),*out=tmpfile(); unsigned char *want,*packet;
    size_t bytes,layer,packet_bytes,data=8000,pointer=9000,patch=order,copy=1-order;
    REQUIRE(in && out); setup(65520,7,in,out);
    bytes=(space_nbits+7)/8; layer=proc_n*instruction_size; packet_bytes=(layer+7)/8;
    want=calloc(bytes,1); packet=calloc(packet_bytes,1); REQUIRE(want && packet);
    row(want,0,layer,0,space_nbits+1);
    REQUIRE(memcmp(want,space,bytes)==0);
    row(packet,patch*instruction_size,address_bits,
        copy*instruction_size+nfield_bits+address_bits,pointer);
    row(packet,copy*instruction_size,8,data,data+64);
    if(layer%8) packet[packet_bytes-1]|=(1u<<(8-layer%8))-1;
    REQUIRE(fwrite(packet,1,packet_bytes,in)==packet_bytes); rewind(in);
    space[data/8+8]=0x6d; space[data/8+16]=0x33;
    put(space,pointer,address_bits,data+128);
    memcpy(want,space,bytes); memcpy(want,packet,packet_bytes);
    REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
    REQUIRE(space[data/8]==0); REQUIRE(ftell(in)==(long)packet_bytes);
    REQUIRE(model_tick(want)==1); REQUIRE(computation()==1);
    REQUIRE(memcmp(want,space,bytes)==0); REQUIRE(space[data/8]==0x6d);
    REQUIRE(processor[copy][2]==data+64);
    REQUIRE(get(space,copy*instruction_size+nfield_bits+address_bits,address_bits)==data+128);
    REQUIRE(model_tick(want)==1); REQUIRE(computation()==1);
    REQUIRE(memcmp(want,space,bytes)==0); REQUIRE(space[data/8]==0x33);
    /* Loading an all-NOP processor is itself a live tick; only the next
     * fetch stops. It must not suppress another already-fetched copy. */
    memset(space,0,packet_bytes);
    row(space,0,layer,0,10000); row(space,instruction_size,8,data,data+64);
    memcpy(want,space,bytes);
    REQUIRE(model_tick(want)==1); REQUIRE(computation()==1);
    REQUIRE(memcmp(want,space,bytes)==0); REQUIRE(space[data/8]==0x6d);
    REQUIRE(computation()==0); REQUIRE(memcmp(want,space,bytes)==0);
    free(want); free(packet); cleanup(in,out);
  }
}

static size_t channel_cases;

static void request(size op,size target)
{
  size base=1001;
  put(space,base,8,op); put(space,base+8,address_bits,target);
  put(space,base+8+address_bits,16,0);
  put(space,base+24+address_bits,32,0); put(space,base+56+address_bits,64,0);
}

static void answer(unsigned char *b,size base,size op,size status,size bytes,size moved,size eof)
{
  put(b,base,8,op); put(b,base+8,8,status); put(b,base+16,16,0);
  put(b,base+32,64,bytes); put(b,base+96,nfield_bits,moved);
  put(b,base+96+nfield_bits,1,eof);
}

/* Independent whole-memory boundary oracle: a read concurrent with a new
 * request always receives the previously committed response. */
static void phases(void)
{
  static const unsigned slots[]={0,3,7};
  unsigned mode,a,b,c;
  for(mode=0;mode<6;++mode) for(a=0;a<3;++a) for(b=0;b<3;++b) for(c=0;c<3;++c)
  {
    FILE *in,*out; unsigned char *want,*before; struct stat st;
    size_t bytes; size data=9001,rsp=2203,second=3001,rb; int error=0;
    const unsigned char text[]={0x58,0x59,0x5a};
    if(a==b || a==c || b==c) continue;
    in=mode==2?fopen(".","r"):tmpfile();
    out=mode==4?fopen("/dev/full","w"):tmpfile(); REQUIRE(in && out);
    if(mode==5) {
      int pipes[2]; REQUIRE(pipe(pipes)==0); close(pipes[0]); fclose(out);
      out=fdopen(pipes[1],"w"); REQUIRE(out);
    }
    if(mode==0) { REQUIRE(fwrite("AB",1,2,in)==2); rewind(in); }
    setup(65520,8,in,out); bytes=(space_nbits+7)/8; rb=97+nfield_bits;
    memset(space,0xa5,bytes); memset(space,0,(proc_n*instruction_size+7)/8);
    refcopy(space,text,24,data,0);
    row(space,slots[a]*instruction_size,24,mode<3?data:space_nbits+2,mode<3?space_nbits+1:data);
    row(space,slots[c]*instruction_size,rb,rsp,space_nbits);
    row(space,instruction_size,19,5003,6007);
    want=malloc(bytes); before=malloc(bytes); REQUIRE(want && before);
    memcpy(want,space,bytes); memcpy(before,space,bytes);
    if(mode==0) refcopy(want,(const unsigned char *)"AB",16,data,0);
    answer(want,rsp,0,0,0,0,0); refcopy(want,before,19,5003,6007);
    REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
    if(mode==2) error=EISDIR;
    if(mode==4) error=ENOSPC;
    if(mode==5) error=EPIPE;
    REQUIRE(fstat(fileno(mode<3?in:out),&st)==0);
    /* Request and read together: still the initial zero response. */
    memset(space,0,(proc_n*instruction_size+7)/8);
    request(3,space_nbits+(mode<3?1:2));
    row(space,slots[b]*instruction_size,120+address_bits,space_nbits,1001);
    row(space,slots[c]*instruction_size,rb,rsp,space_nbits);
    memcpy(want,space,bytes); answer(want,rsp,0,0,0,0,0);
    REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
    memset(space,0,(proc_n*instruction_size+7)/8);
    row(space,slots[c]*instruction_size,rb,second,space_nbits);
    memcpy(want,space,bytes);
    answer(want,second,3,error,(size)st.st_size,mode==0?2:mode==3?3:0,mode<2);
    REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
    /* NONE replacement cannot erase the old answer in its submission tick. */
    memset(space,0,(proc_n*instruction_size+7)/8); request(0,0);
    row(space,slots[b]*instruction_size,120+address_bits,space_nbits,1001);
    row(space,slots[c]*instruction_size,rb,rsp,space_nbits);
    memcpy(want,space,bytes);
    answer(want,rsp,3,error,(size)st.st_size,mode==0?2:mode==3?3:0,mode<2);
    REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
    memset(space,0,(proc_n*instruction_size+7)/8);
    row(space,slots[c]*instruction_size,rb,second,space_nbits);
    memcpy(want,space,bytes); answer(want,second,0,0,0,0,0);
    REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
    free(want); free(before); cleanup(in,out); ++channel_cases;
  }
}

static void boundary_visibility(void)
{
  FILE *in=tmpfile(),*out=tmpfile(); unsigned char *want;
  size bytes,rb; REQUIRE(in && out); setup(65520,8,in,out);
  bytes=(space_nbits+7)/8; rb=97+nfield_bits; want=malloc(bytes); REQUIRE(want);
  memset(space,0,bytes);
  /* Zero answer erases current processor instructions, but the already
   * fetched ordinary copy still executes; the next fetch sees all NOPs. */
  put(space,6000,8,0x5a);
  row(space,0,rb,0,space_nbits);
  row(space,instruction_size,8,7000,6000);
  memcpy(want,space,bytes); answer(want,0,0,0,0,0,0);
  refcopy(want,space,8,7000,6000);
  REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
  REQUIRE(computation()==0);
  /* IOCTL commits ENOTTY; its response is not read until the next tick. */
  request(4,space_nbits+1);
  row(space,0,120+address_bits,space_nbits,1001);
  REQUIRE(computation()==1);
  /* SYS response overwrites processor slot 0 (old NOPs). It must not
   * change an instruction fetched for this tick. Two reads see one value. */
  memset(space,0,(proc_n*instruction_size+7)/8);
  row(space,3*instruction_size,rb,0,space_nbits);
  row(space,7*instruction_size,rb,2203,space_nbits);
  memcpy(want,space,bytes); answer(want,0,4,ENOTTY,0,0,0);
  answer(want,2203,4,ENOTTY,0,0,0);
  REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
  /* The returned record becomes a new instruction on the NEXT fetch.
   * Decode only to demonstrate the processor update, then replace it. */
  REQUIRE(get(space,0,nfield_bits)==(4 | ((size)ENOTTY<<8)));
  /* A later data read changes device metadata, not the stored SYS reply. */
  memset(space,0,(proc_n*instruction_size+7)/8);
  row(space,0,8,9001,space_nbits+1);
  row(space,7*instruction_size,rb,3001,space_nbits);
  memcpy(want,space,bytes); answer(want,3001,4,ENOTTY,0,0,0);
  REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
  /* CLOSE SYS, two old-response reads, unrelated output and ordinary
   * work all finish. Later SYS reads leave their buffers untouched. */
  memset(space,0,(proc_n*instruction_size+7)/8); request(1,space_nbits);
  row(space,0,120+address_bits,space_nbits,1001);
  row(space,instruction_size,rb,2203,space_nbits);
  row(space,2*instruction_size,rb,3001,space_nbits);
  put(space,8000,8,0x58);
  row(space,3*instruction_size,8,space_nbits+2,8000);
  row(space,4*instruction_size,8,7000,6000);
  memcpy(want,space,bytes); answer(want,2203,4,ENOTTY,0,0,0);
  answer(want,3001,4,ENOTTY,0,0,0); refcopy(want,space,8,7000,6000);
  REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
  REQUIRE(!sys_is_channel(space_nbits));
  memset(space,0,(proc_n*instruction_size+7)/8);
  row(space,0,rb,2203,space_nbits);
  memcpy(want,space,bytes); REQUIRE(computation()==1);
  REQUIRE(memcmp(want,space,bytes)==0);
  free(want); cleanup(in,out); ++channel_cases;
}

/* Keep fixture FILEs outside fd 3/4, so optional bindings are intentional. */
static FILE *high_file(void)
{
  FILE *f=tmpfile(),*high; int fd;
  REQUIRE(f); fd=fcntl(fileno(f),F_DUPFD_CLOEXEC,20); REQUIRE(fd>=20);
  fclose(f); high=fdopen(fd,"w+"); REQUIRE(high); return high;
}

static void control(size op,size target)
{
  memset(space,0,(proc_n*instruction_size+7)/8); request(op,target);
  row(space,0,120+address_bits,space_nbits,1001);
  REQUIRE(computation()==1);
  memset(space,0,(proc_n*instruction_size+7)/8);
  row(space,instruction_size,97+nfield_bits,2203,space_nbits);
  REQUIRE(computation()==1);
}

static void ownership(void)
{
  unsigned present;
  for(present=0;present<2;++present)
  {
    int status; pid_t child=fork(); REQUIRE(child>=0);
    if(child==0)
    {
      FILE *in=high_file(),*out=high_file(),*third=high_file();
      unsigned char saved[32]; size rb=112; char got[4]={0};
      close(3); close(4);
      if(present) REQUIRE(dup2(fileno(third),3)==3);
      setup(65520,8,in,out);
      REQUIRE(sys_device_pos(3)==(present?space_nbits+4:0));
      /* Duplicating fd 3 must never manufacture a missing fd 4 channel. */
      REQUIRE(sys_device_pos(4)==0);
      control(3,space_nbits+5);
      REQUIRE(get(space,2203+8,8)==EBADF);
      if(present)
      {
        space[1000]=0x58;
        memset(space,0,(proc_n*instruction_size+7)/8);
        row(space,0,8,space_nbits+4,8000); REQUIRE(computation()==1);
        control(1,space_nbits+4);
        REQUIRE(get(space,2203+8,8)==0 && !sys_is_channel(space_nbits+4));
        REQUIRE(fcntl(3,F_GETFD)>=0 && write(3,"O",1)==1);
        rewind(third); REQUIRE(fread(got,1,4,third)==2 && memcmp(got,"XO",2)==0);
        control(3,space_nbits+4); REQUIRE(get(space,2203+8,8)==EBADF);
      }
      else
      {
        control(3,space_nbits+4); REQUIRE(get(space,2203+8,8)==EBADF);
      }
      /* SYS close still delivers the old answer in its submission tick. */
      memset(saved,0xa5,sizeof saved); refcopy(space,saved,rb,2203,0);
      memset(space,0,(proc_n*instruction_size+7)/8); request(1,space_nbits);
      row(space,0,120+address_bits,space_nbits,1001);
      row(space,instruction_size,rb,2203,space_nbits);
      REQUIRE(computation()==1);
      REQUIRE(get(space,2203,8)==3 && get(space,2211,8)==EBADF);
      refcopy(saved,space,rb,0,2203);
      REQUIRE(!sys_is_channel(space_nbits));
      for(size j=0;j<rb;++j) REQUIRE(get(space,2203+j,1)==get(saved,j,1));
      memset(space,0,(proc_n*instruction_size+7)/8); space[1000]=0x58;
      row(space,0,8,space_nbits+2,8000);
      row(space,instruction_size,rb,2203,space_nbits);
      REQUIRE(computation()==1);
      for(size j=0;j<rb;++j) REQUIRE(get(space,2203+j,1)==get(saved,j,1));
      rewind(out); REQUIRE(fread(got,1,4,out)==1 && got[0]=='X');
      cleanup(in,out); fclose(third); close(3); _exit(0);
    }
    REQUIRE(waitpid(child,&status,0)==child);
    REQUIRE(WIFEXITED(status) && WEXITSTATUS(status)==0); ++channel_cases;
  }
  /* Standard-stream CLOSE disables the binding, preserving its FILE. */
  {
    FILE *in=tmpfile(),*out=tmpfile(); char got[4]={0};
    REQUIRE(in && out); setup(65520,8,in,out);
    memset(space,0,(proc_n*instruction_size+7)/8);
    put(space,2203,64,UINT64_MAX); put(space,2267,48,mask(48));
    row(space,0,112,2203,space_nbits); REQUIRE(computation()==1);
    for(unsigned j=0;j<112;++j) REQUIRE(get(space,2203+j,1)==0);
    control(4,space_nbits+1);
    REQUIRE(get(space,2203,8)==4 && get(space,2203+8,8)==ENOTTY);
    control(255,space_nbits+1);
    REQUIRE(get(space,2203,8)==255 && get(space,2203+8,8)==EINVAL);
    control(1,space_nbits+2);
    REQUIRE(!sys_is_channel(space_nbits+2));
    memset(space,0,(proc_n*instruction_size+7)/8); space[1000]=0x58;
    row(space,0,8,space_nbits+2,8000); REQUIRE(computation()==1);
    REQUIRE(fwrite("Y",1,1,out)==1); rewind(out);
    REQUIRE(fread(got,1,4,out)==1 && got[0]=='Y');
    cleanup(in,out); ++channel_cases;
  }
}

static void stream_edges(void)
{
  FILE *in=tmpfile(),*out=tmpfile();
  size count=40000,actual=count-3,data=9001,bytes,j;
  unsigned char *payload=malloc(count),*want;
  REQUIRE(in && out && payload);
  for(j=0;j<count;++j) payload[j]=(unsigned char)(j*37+j/251);
  REQUIRE(fwrite(payload,1,actual,in)==actual); rewind(in);
  setup(1048560,8,in,out); bytes=(space_nbits+7)/8;
  memset(space,0xa5,bytes); memset(space,0,(proc_n*instruction_size+7)/8);
  request(3,space_nbits+1);
  row(space,0,count*8,data,space_nbits+1);

  want=malloc(bytes); REQUIRE(want); memcpy(want,space,bytes);
  refcopy(want,payload,actual*8,data,0);
  REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
  control(3,space_nbits+1);
  REQUIRE(get(space,2203+96,nfield_bits)==actual && get(space,2203+96+nfield_bits,1)==1);
  memset(space,0,(proc_n*instruction_size+7)/8); request(3,space_nbits+2);
  row(space,0,actual*8,space_nbits+2,data);

  memcpy(want,space,bytes);
  REQUIRE(computation()==1); REQUIRE(memcmp(want,space,bytes)==0);
  control(3,space_nbits+2);
  REQUIRE(get(space,2203+96,nfield_bits)==actual && get(space,2203+96+nfield_bits,1)==0);
  rewind(out);
  for(j=0;j<actual;++j) REQUIRE(fgetc(out)==payload[j]);
  REQUIRE(fgetc(out)==EOF);
  free(want); free(payload); cleanup(in,out); ++channel_cases;

  /* A nonblocking pipe accepts some bytes, then fails. Both the progress
   * and EAGAIN must survive FSTAT; already-read source bytes aren't lost. */
  {
    int pipes[2],flags; long unit; size filled=0,drained=0; ssize_t moved;
    unsigned char *block; FILE *pipe_out;
    REQUIRE(pipe(pipes)==0);
    unit=fpathconf(pipes[1],_PC_PIPE_BUF); REQUIRE(unit>0 && unit<=32768);
    block=malloc((size_t)unit); REQUIRE(block); memset(block,0x42,(size_t)unit);
    flags=fcntl(pipes[1],F_GETFL); REQUIRE(flags>=0);
    REQUIRE(fcntl(pipes[1],F_SETFL,flags|O_NONBLOCK)==0);
    while((moved=write(pipes[1],block,(size_t)unit))>0) filled+=(size)moved;
    REQUIRE(moved==-1 && errno==EAGAIN && filled>=(size)unit);
    REQUIRE(read(pipes[0],block,(size_t)unit)==unit);
    pipe_out=fdopen(pipes[1],"w"); in=tmpfile(); REQUIRE(pipe_out && in);
    setup(2097136,8,in,pipe_out);
    memset(space,0,(proc_n*instruction_size+7)/8);
    memset(space+1000,0x58,(size_t)unit*2);
    request(3,space_nbits+2);
    row(space,0,(size)unit*16,space_nbits+2,8000);
    REQUIRE(computation()==1);
    control(3,space_nbits+2);
    REQUIRE(get(space,2203+8,8)==EAGAIN);
    REQUIRE(get(space,2203+96,nfield_bits)==(size)unit);
    REQUIRE(get(space,2203+96+nfield_bits,1)==0);
    REQUIRE(fcntl(pipes[0],F_SETFL,O_NONBLOCK)==0);
    while((moved=read(pipes[0],block,(size_t)unit))>0)
    {
      for(ssize_t k=0;k<moved;++k)
        REQUIRE(block[k]==(drained+(size)k<filled-(size)unit?0x42:0x58));
      drained+=(size)moved;
    }
    REQUIRE(moved==-1 && errno==EAGAIN && drained==filled);
    free(block); close(pipes[0]); cleanup(in,pipe_out); ++channel_cases;
  }
}

int main(void)
{
  decoders(); validator_regressions(); programs(); self_patch_and_seed(); phases(); boundary_visibility(); ownership(); stream_edges();
  printf("engine: %zu independent decoder cases and %zu whole-space tick comparisons; seed/self-patch passed\n",
         decoder_cases,tick_cases);
  printf("channels: %zu full-tick permutations/ownership cases with independent SYS codec passed\n",channel_cases);
  return 0;
}
