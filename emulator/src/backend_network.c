/* Adapt the verified two-phase mechanism to the common runtime boundary.
 * Arithmetic here belongs to the host model/network construction, not the
 * hardware's per-position addressing primitive. State words stay 16-bit.
 */
#include "space.h"
#define VM1_RUNTIME_NETWORK
#define EMULATOR_NETWORK_LIBRARY
#define UNIT_TEST
#include "machine.c"
#include "network.c"

size_t vm1_network_size,vm1_network_slots;
static machine *model;
void backend_shutdown(void)
{
  if(model) {
    network_free(&model->fabric);
    free(model->subspace); free(model); model=NULL;
  }
}
void backend_init(void)
{
  backend_shutdown();
  if(space_nbits<16 || space_nbits>65520 || space_nbits%16 || proc_n>128) {
    fputs("emulator: network requires -s divisible by 16, 16..65520, and -p 1..128\n",stderr);
    exit(EXIT_USAGE);
  }
  vm1_network_size=space_nbits; vm1_network_slots=proc_n;
  model=calloc(1,sizeof *model);
  if(!model) { fputs("emulator: out of memory\n",stderr); exit(EXIT_MEMORY); }
  model->space=space;
  model->subspace=calloc(space_nbits,sizeof *model->subspace);
  if(!model->subspace) { fputs("emulator: out of memory\n",stderr); exit(EXIT_MEMORY); }
  for(size_t i=0;i<space_nbits;i++) model->subspace[i].key.origin=(idx)i;
  uint32_t padded=next_pow2((uint32_t)space_nbits);
  net_t big=gen_pairwise_pow2(padded), packed={0};
  seq_t seq={0};
  for(size_t l=0;l<big.layers;l++)
    for(size_t p=0;p<big.layer[l].count;p++) {
      pair_t edge=big.layer[l].pair[p];
      if(edge.left<space_nbits && edge.right<space_nbits)
        seq_add(&seq,edge.left,edge.right);
    }
  net_free(&big);
  packed=seq_pack(&seq,(uint32_t)space_nbits); seq_free(&seq);
  for(size_t l=0;l<packed.layers;l++) {
    network_add_layer(&model->fabric);
    for(size_t p=0;p<packed.layer[l].count;p++) {
      pair_t edge=packed.layer[l].pair[p];
      network_push_pair(&model->fabric,(idx)edge.left,(idx)edge.right);
    }
  }
  net_free(&packed);
}
void backend_tick(void)
{
  run_cycle(model);
  /* Commit once at THIS tick boundary, including the final limited tick. */
  sync_space_and_subspace(model);
}
