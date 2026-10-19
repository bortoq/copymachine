/* Guest-resident index; original ISC linear search remains the fallback. */
#include "pf_all.h"
#include "index.h"
#include "name_index.h"
#ifdef PF_SUPPORT_LONG_NAMES
#error "Index preparation currently requires the pinned 31-byte name layout"
#endif

extern cell_t pfLinearFindNFA(const ForthString *, vm_address_t *);
extern void pfLinearCreateDicEntry(ExecToken, const char *, ucell_t);
static vm_address_t indexed_base;
static uint32_t indexed_context=PF_INDEX_INITIAL_CONTEXT;
static uint32_t indexed_limit=PF_INDEX_INITIAL_LIMIT;
static int dirty, unusable;
static uint32_t pending,pending_bucket,pending_length;
static uint32_t last_rank=PF_INDEX_INITIAL_CONTEXT/4;

static uint32_t hash_name(const uint8_t *name, unsigned length)
{
    uint32_t hash=0;
    while(length--) {
        unsigned byte=*name++;
        if(byte>='A' && byte<='Z')byte+='a'-'A';
        hash=((hash<<5)+hash)^byte;
    }
    return hash&(PF_INDEX_BUCKETS-1);
}
static int valid(uint32_t relative)
{
    return relative>=PF_HEADER_OFFSET_NFA && !(relative&3) && relative/4<PF_INDEX_CAPACITY;
}
static uint32_t previous(uint32_t relative)
{
    return (uint32_t)READ_CELL_DIC(NAME_BASE+relative-PF_HEADER_OFFSET_NFA);
}
static void insert(uint32_t relative)
{
    const uint8_t *name=(const uint8_t *)(uintptr_t)(NAME_BASE+relative);
    pf_index_rank[relative/4]=(uint16_t)++last_rank;
    unsigned length=*name&MASK_NAME_SIZE;
    unsigned bucket=hash_name(name+1,length);
    if(relative+length+1>indexed_limit)indexed_limit=relative+length+1;
    pf_index_next[relative/4]=pf_index_heads[bucket];pf_index_heads[bucket]=relative;
}
static void remove_entry(uint32_t relative,unsigned bucket)
{
    uint32_t *link=&pf_index_heads[bucket];
    while(*link && *link!=relative)link=&pf_index_next[*link/4];
    if(*link)*link=pf_index_next[relative/4];
}
void pfIndexInvalidate(vm_address_t address, uint32_t bytes)
{
    if(!indexed_base || !bytes || dirty || unusable || address>=indexed_base+indexed_limit ||
       (address<indexed_base && bytes<=indexed_base-address))return;
    if(address>=indexed_base && address-indexed_base<PF_INDEX_CAPACITY*4) {
        uint32_t relative=(uint32_t)(address-indexed_base),candidate=relative&~3u;
        for(unsigned slots=0;slots<10 && candidate>=8;slots++,candidate-=4) {
            if(!pf_index_rank[candidate/4])continue;
            const uint8_t *name=(const uint8_t *)(uintptr_t)(indexed_base+candidate);
            unsigned length=*name&MASK_NAME_SIZE;
            uint32_t end=(candidate+length+4)&~3u;
            if(relative>=candidate && relative<end && bytes<=end-relative) {
                if(pending && pending!=candidate){dirty=1;return;}
                if(!pending){pending=candidate;pending_bucket=hash_name(name+1,length);pending_length=length;}
                return;
            }
        }
    }
    dirty=1;
}
static void repair(void)
{
    const uint8_t *name=(const uint8_t *)(uintptr_t)(NAME_BASE+pending);
    unsigned length=*name&MASK_NAME_SIZE;
    /* Arbitrary length changes can make headers overlap; preserve semantics
     * through the original search instead of retaining an ambiguous cache. */
    if(length!=pending_length){unusable=1;return;}
    remove_entry(pending,pending_bucket);
    unsigned bucket=hash_name(name+1,length);
    uint32_t *link=&pf_index_heads[bucket];
    while(*link && pf_index_rank[*link/4]>pf_index_rank[pending/4])link=&pf_index_next[*link/4];
    pf_index_next[pending/4]=*link;*link=pending;pending=0;
}
static void synchronize(void)
{
    uint32_t head=gVarContext?(uint32_t)ABS_TO_NAMEREL(gVarContext):0;
    if(indexed_base!=NAME_BASE) {
        if(indexed_base)dirty=1;
        indexed_base=NAME_BASE;
    }
    if(pending && !dirty) {
        if(head!=indexed_context)dirty=1;
        else repair();
    }
    if(unusable || (!dirty && head==indexed_context))return;
    if(last_rank+PF_INDEX_CAPACITY>=65535)dirty=1;
    uint32_t cursor=head,steps=0;
    if(!dirty && head<indexed_context) {
        cursor=indexed_context;
        while(cursor!=head && valid(cursor) && steps++<PF_INDEX_CAPACITY)cursor=previous(cursor);
        if(cursor==head) {
            cursor=indexed_context;
            while(cursor!=head) {
                const uint8_t *name=(const uint8_t *)(uintptr_t)(NAME_BASE+cursor);
                remove_entry(cursor,hash_name(name+1,*name&MASK_NAME_SIZE));
                pf_index_rank[cursor/4]=0;cursor=previous(cursor);
            }
            indexed_context=head;return;
        }
    }
    if(!dirty && head>indexed_context) {
        /* Verify a monotonic append before changing any bucket. */
        while(cursor!=indexed_context && valid(cursor) && cursor>indexed_context && steps++<PF_INDEX_CAPACITY)
            cursor=previous(cursor);
        if(cursor==indexed_context) {
            uint32_t reversed=0;cursor=head;
            while(cursor!=indexed_context) {
                uint32_t next=previous(cursor);
                pf_index_next[cursor/4]=reversed;reversed=cursor;cursor=next;
            }
            while(reversed) {
                uint32_t next=pf_index_next[reversed/4];insert(reversed);reversed=next;
            }
            indexed_context=head;if(gCurrentDictionary->dic_HeaderPtr-NAME_BASE>indexed_limit)indexed_limit=(uint32_t)(gCurrentDictionary->dic_HeaderPtr-NAME_BASE);return;
        }
    }
    for(unsigned i=0;i<PF_INDEX_BUCKETS;i++)pf_index_heads[i]=0;
    for(unsigned i=0;i<PF_INDEX_CAPACITY;i++)pf_index_rank[i]=0;
    last_rank=0;pending=0;
    /* Reverse the active chain using scratch links, then insert oldest first. */
    uint32_t reversed=0;cursor=head;steps=0;
    while(cursor) {
        if(!valid(cursor) || steps++>=PF_INDEX_CAPACITY){unusable=1;return;}
        uint32_t next=previous(cursor);pf_index_next[cursor/4]=reversed;reversed=cursor;cursor=next;
    }
    while(reversed) {
        uint32_t next=pf_index_next[reversed/4];insert(reversed);reversed=next;
    }
    indexed_context=head;if(gCurrentDictionary->dic_HeaderPtr-NAME_BASE>indexed_limit)indexed_limit=(uint32_t)(gCurrentDictionary->dic_HeaderPtr-NAME_BASE);dirty=0;
}
void CreateDicEntry(ExecToken xt,const char *name,ucell_t flags)
{
    /* Reusing a forgotten header can leave the same context address. */
    pfIndexInvalidate(gCurrentDictionary->dic_HeaderPtr,(uint32_t)(PF_HEADER_OFFSET_NFA+((uint8_t)*name)+1));
    pfLinearCreateDicEntry(xt,name,flags);
}
cell_t ffFindNFA(const ForthString *word,vm_address_t *result)
{
    synchronize();
    if(unusable)return pfLinearFindNFA(word,result);
    unsigned length=(uint8_t)*word&MASK_NAME_SIZE;
    uint32_t relative=pf_index_heads[hash_name((const uint8_t *)word+1,length)];
    while(relative) {
        vm_address_t nfa=NAME_BASE+relative;
        const uint8_t *name=(const uint8_t *)(uintptr_t)nfa;
        unsigned flags=*name;
        if(!(flags&FLAG_SMUDGE) && (flags&MASK_NAME_SIZE)==length &&
           ffCompareTextCaseN((const char *)name+1,word+1,length)) {
            *result=nfa;return (flags&FLAG_IMMEDIATE)?1:-1;
        }
        relative=pf_index_next[relative/4];
    }
    *result=PTR_TO_VMA(word);return 0;
}
