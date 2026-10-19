/* Preserve upstream; observe Forth stores into indexed dictionary headers. */
#include "pf_all.h"
#include "index.h"
static void index_store8(vm_address_t at,uint8_t value)
{
 if(at!=gVarContext || ((*(uint8_t *)(uintptr_t)at ^ value)&MASK_NAME_SIZE))pfIndexInvalidate(at,1);
 *((uint8_t *)(uintptr_t)at)=value;
}
static void index_store16(vm_address_t at,uint16_t value)
{ pfIndexInvalidate(at,2);*((uint16_t *)(uintptr_t)at)=value; }
static void index_store_cell(vm_address_t at,cell_t value)
{ pfIndexInvalidate(at,sizeof value);*((cell_t *)(uintptr_t)at)=value; }
static vm_address_t index_set(vm_address_t at,cell_t value,uint32_t bytes)
{ pfIndexInvalidate(at,bytes);return pfSetVirtualMemory(at,value,bytes); }
static vm_address_t index_copy(vm_address_t at,const void *source,uint32_t bytes)
{ pfIndexInvalidate(at,bytes);return pfCopyToVirtualMemory(at,source,bytes); }
static uint8_t *index_lock(vm_address_t at,uint32_t bytes)
{ pfIndexInvalidate(at,bytes);return pfLockMemoryReadWrite(at,bytes); }
#undef DP_STORE_U8
#undef DP_STORE_U16
#undef DP_STORE_CELL
#define DP_STORE_U8(at,value) index_store8((vm_address_t)(at),(uint8_t)(value))
#define DP_STORE_U16(at,value) index_store16((vm_address_t)(at),(uint16_t)(value))
#define DP_STORE_CELL(at,value) index_store_cell((vm_address_t)(at),(cell_t)(value))
#define pfSetVirtualMemory index_set
#define pfCopyToVirtualMemory index_copy
#define pfLockMemoryReadWrite index_lock
#include "../../third_party/pforth/csrc/pf_inner.c"
