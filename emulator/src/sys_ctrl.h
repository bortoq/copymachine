/*
 * SYS CHANNEL AND DEVICE CHANNELS (host side)
 *
 * The channel table holds SYS at entry 0 (position space_nbits) and the
 * device channels pre-bound at start after it (stdin at space_nbits+1,
 * stdout at space_nbits+2, debug/stderr at space_nbits+3, optional status
 * fd 3 at space_nbits+4 and snapshot fd 4 at space_nbits+5). All table
 * positions are reserved; absent optional descriptors stay unbound. There
 * is no dynamic opening; inherited streams are duplicated and closed here.
 *
 * A copy that touches a channel is served here (in sys_tick):
 *   - a copy touching SYS carries a control record: dst = SYS is a
 *     request (src holds its address), src = SYS is an answer read
 *     (dst holds its address);
 *   - a copy touching a device channel moves data: dst = channel writes
 *     data out, src = channel reads data in.
 * SYS is an ordinary entry and may be closed like any other channel;
 * after that the space has no control over the host and cannot read any
 * state on subsequent ticks. All channel copies complete by tick end;
 * there is no intermediate readiness guarantee. A SYS read observes the
 * response committed before this tick, even with a concurrent request or
 * CLOSE SYS. A request's new response is readable from the next tick.
 * Supported: one transfer per device, one SYS request, answer reads into
 * disjoint buffers. Transfers must have exactly one device endpoint.
 * FSTAT/SEEK/CLOSE and a transfer on their target require separate ticks;
 * EXEC side effects must be independent of other operations in this tick.
 * All source and destination MEMORY intervals in a tick are pairwise
 * disjoint, including read/read and buffers of different channel operations.
 * Conflicting operations have no defined slot ordering and are the program's
 * responsibility, like overlapping copies. CLOSE takes effect at the tick
 * boundary; CLOSE SYS preserves old-response reads in its submission tick.
 *
 * The long copy (15.2, op LONG) copies to or from a remote space: 0 the
 * old SYS, 1 the clock, 2.. the host files of -r (proto.def).
 *
 * The protocol (op codes, record fields, pre-bound devices) comes from
 * proto.def via proto_gen.h.
 */
#ifndef SYS_CTRL_H_
#define SYS_CTRL_H_

#include "space.h"

void sys_init(void);                 /* compute widths, bind SYS + devices */
void sys_shutdown(void);             /* close duplicate inherited streams */
int  sys_is_channel(size pos);       /* pos names an existing channel */
size sys_device_pos(unsigned id);    /* channel position of a pre-bound device */
void sys_tick(void);                 /* service channel instructions */
size sys_req_bits(void);             /* bits in a request record */
size sys_rsp_bits(void);             /* bits in an answer record */
/* encode/decode a record at a bit address (host side, tests and tools) */
void sys_encode_req(size base, const size *v);  /* v[REQ_NFIELDS] */
void sys_decode_rsp(size base, size *v);        /* v[RSP_NFIELDS] */

#endif /* SYS_CTRL_H_ */
