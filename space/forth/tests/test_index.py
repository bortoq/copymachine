"""Compare the actual guest index C with a linear oracle and mutable headers."""
import json,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/pforth'))
from index import prepare_index
from common import PORT
with tempfile.TemporaryDirectory(prefix='pforth index ') as d:
 d=Path(d);_,report=prepare_index(d)
 text=(PORT/'pfdicdat.h').read_text();body=re.search(r'MinDicNames\[.*?= \{(.*?)\};',text,re.S)[1]
 raw=bytes(int(v,16) for v in re.findall(r'0x([0-9a-f]{2})',body))
 (d/'names.h').write_text('static const unsigned char prepared_names[]={'+','.join(map(str,raw))+'};\n')
 (d/'pf_all.h').write_text(r'''
#ifndef INDEX_TEST_PF_ALL
#define INDEX_TEST_PF_ALL
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
typedef uintptr_t vm_address_t;
typedef uint32_t ucell_t;
typedef int32_t cell_t;
typedef int32_t ExecToken;
typedef char ForthString;
typedef struct {vm_address_t dic_HeaderBase,dic_HeaderPtr;} dictionary;
extern dictionary *gCurrentDictionary;
extern vm_address_t gVarContext;
#define NAME_BASE (gCurrentDictionary->dic_HeaderBase)
#define MASK_NAME_SIZE 31
#define FLAG_SMUDGE 32
#define FLAG_IMMEDIATE 64
#define PF_HEADER_OFFSET_NFA 8
#define ABS_TO_NAMEREL(at) ((at)-NAME_BASE)
#define PTR_TO_VMA(at) ((uintptr_t)(at))
static inline uint32_t read32(uintptr_t at){const uint8_t *p=(void *)at;return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
#define READ_CELL_DIC(at) read32(at)
cell_t ffCompareTextCaseN(const char *,const char *,cell_t);
#endif
''')
 (d/'test.c').write_text(r'''
#include "pf_all.h"
#include "names.h"
#include "index.h"
static uint8_t memory[100000];
static dictionary dic;
dictionary *gCurrentDictionary=&dic;
vm_address_t gVarContext;
static unsigned linear_visits,comparisons,queries;
static unsigned lower(unsigned c){return c>='A'&&c<='Z'?c+32:c;}
cell_t ffCompareTextCaseN(const char *a,const char *b,cell_t length)
{comparisons++;for(cell_t i=0;i<length;i++)if(lower((uint8_t)a[i])!=lower((uint8_t)b[i]))return 0;return 1;}
static void write32(uintptr_t at,uint32_t v){for(unsigned i=0;i<4;i++)((uint8_t *)at)[i]=(uint8_t)(v>>(8*i));}
cell_t pfLinearFindNFA(const ForthString *word,vm_address_t *result)
{
 for(uintptr_t n=gVarContext;n;) {
  linear_visits++;unsigned flags=*(uint8_t *)n,len=flags&31;
  if(!(flags&32) && len==((uint8_t)*word&31)) {
   unsigned i=0;while(i<len && lower(((uint8_t *)n)[i+1])==lower((uint8_t)word[i+1]))i++;
   if(i==len){*result=n;return flags&64?1:-1;}
  }
  unsigned next=read32(n-8);n=next?NAME_BASE+next:0;
 }
 *result=(uintptr_t)word;return 0;
}
void pfLinearCreateDicEntry(ExecToken xt,const char *name,ucell_t flags)
{
 uintptr_t p=dic.dic_HeaderPtr;write32(p,gVarContext?(uint32_t)(gVarContext-NAME_BASE):0);write32(p+4,(uint32_t)xt);
 gVarContext=p+8;memcpy((void *)gVarContext,name,(uint8_t)*name+1);*(uint8_t *)gVarContext|=flags;
 dic.dic_HeaderPtr=(gVarContext+(uint8_t)*name+4)&~(uintptr_t)3;
}
extern cell_t ffFindNFA(const ForthString *,vm_address_t *);
extern void CreateDicEntry(ExecToken,const char *,ucell_t);
static void check(const char *text,int expected)
{
 char word[40];unsigned n=(unsigned)strlen(text);assert(n<=31);word[0]=(char)n;memcpy(word+1,text,n);
 uintptr_t a,b;int x=ffFindNFA(word,&a),y=pfLinearFindNFA(word,&b);queries++;
 assert(x==y && a==b);if(expected!=99)assert(x==expected);
}
static void create(const char *name,int xt)
{char word[40];word[0]=(char)strlen(name);strcpy(word+1,name);CreateDicEntry(xt,word,0);}
int main(void)
{
 memcpy(memory,prepared_names,sizeof prepared_names);dic.dic_HeaderBase=(uintptr_t)memory;dic.dic_HeaderPtr=NAME_BASE+sizeof prepared_names;
 gVarContext=NAME_BASE+INITIAL_CONTEXT;
 for(uintptr_t p=gVarContext;p;) {
  unsigned n=*(uint8_t *)p&31;char name[40];memcpy(name,(void *)(p+1),n);name[n]=0;check(name,99);
  for(unsigned i=0;i<n;i++)name[i]=(char)lower((uint8_t)name[i]);
  check(name,99);
  unsigned next=read32(p-8);p=next?NAME_BASE+next:0;
 }
 check("NOT_A_WORD",0);uintptr_t initial_context=gVarContext,initial_end=dic.dic_HeaderPtr;
 for(unsigned i=0;i<1000;i++){char name[31];sprintf(name,"NEW-%u",i);create(name,1000+(int)i);check(name,-1);}
 for(unsigned i=0;i<1000;i++){char name[31];sprintf(name,"new-%u",i);check(name,-1);}
 gVarContext=initial_context;dic.dic_HeaderPtr=initial_end;check("NEW-999",0);check("DUP",-1);
 create("DUP",9001);check("dup",-1);assert(read32(gVarContext-4)==9001);
 create("DUP",9002);check("DUP",-1);assert(read32(gVarContext-4)==9002);
 gVarContext=NAME_BASE+read32(gVarContext-8);check("DUP",-1);assert(read32(gVarContext-4)==9001);
 pfIndexInvalidate(gVarContext,1);*(uint8_t *)gVarContext|=FLAG_SMUDGE;check("DUP",-1); /* older builtin remains visible */
 pfIndexInvalidate(gVarContext,1);*(uint8_t *)gVarContext=3|FLAG_IMMEDIATE;check("DUP",1);
 pfIndexInvalidate(gVarContext+1,1);((uint8_t *)gVarContext)[1]='Z';check("ZUP",1);check("DUP",-1);
 create("LAST",9003);check("LAST",-1);uintptr_t skipped=NAME_BASE+read32(gVarContext-8);
 pfIndexInvalidate(gVarContext-8,4);write32(gVarContext-8,read32(skipped-8));check("ZUP",0);check("LAST",-1);
 create("LENGTH",9004);check("LENGTH",-1);
 pfIndexInvalidate(gVarContext,1);*(uint8_t *)gVarContext=5;check("LENGT",-1);check("LENGTH",0);
 printf("PASS index: %u queries, %u linear visits, %u indexed name comparisons; 1000 new words, collisions, case, redefinition, smudge/immediate, context, rename and links\n",queries,linear_visits,comparisons);
}
'''.replace('INITIAL_CONTEXT',str(json.loads((PORT/'pfdicdat.h.json').read_text())['relative_context'])))
 command=['cc','-O2','-Wall','-Wextra','-Werror','-I'+str(d),'-I'+str(PORT),str(PORT/'index.c'),str(d/'test.c'),'-o',str(d/'test')]
 subprocess.run(command,check=True,timeout=20);subprocess.run([str(d/'test')],check=True,timeout=10)
 print('Prepared builtin names:',report['entries'],'maximum builtin bucket:',report['maximum_bucket'])
