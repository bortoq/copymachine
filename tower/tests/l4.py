"""Language 4: the long copy (a copy to or from the address space of the host). Two words, over
language 3 and no new primitive: long_put (`long!`: a part of the data of the program to the host at a
position) and long_get (`long@`: from the host at a position into a part of the data). The position is
a 128-bit value in the data of the program (a constant or computed, for example by `add`): the area
in its top 32 bits (0 the clock, 1.. the files `-r`), the bit in the area in the low 96 bits. A request
of the SYS channel is built from copies only: the constants op, chan, flags, arg (one copy), the position
(a copy of the field off), the data after the record; then one row writes the record to SYS, and for
`long@` the next tick reads the answer. The request buffer is private to this module and the only row to
SYS lives here, so a request can be written in no other way (by construction, no checks). There are no
errors: outside a file the host gives zeros and loses writes."""
import l1
from l2 import Ref, norm

SYS = object()                    # pseudo region: one SYS request or answer read per tick, order preserved
CHAN = object()                   # pseudo region: every access to a channel (S..S+5) writes it, so the accesses of a block keep the order of the text
OP_LONG, POS_BITS, AREA_BITS = 6, 128, 96     # emulator/src/proto.def (a test compares them)
ARG_BITS = 32


def host_pos(area, bit):
    """The position (128-bit number) of the bit `bit` of the area `area` of the host."""
    assert 0 <= area < 1 << POS_BITS - AREA_BITS and 0 <= bit < 1 << AREA_BITS
    return area << AREA_BITS | bit


class Long:
    """Mixin of l3.Program: record fields op:8 chan:A flags:16 arg:32 off:128, low bit first."""

    def _lreq(self, n):
        """The request buffer: the record, then room for n bits of data (one for the whole program)."""
        if getattr(self, '_lq', None) is None:
            self._lq, self._lh = self.var('longreq', 0), {}
        self._lq.bits = max(self._lq.bits, 184 + self.A + n)
        return self._lq

    def _lhead(self, out, n):
        """The constants op, chan, flags (bit 0 = the direction), arg = n: 56 + A bits."""
        if (out, n) not in self._lh:
            A = self.A

            def init(mem, addr):
                mem.put(addr, OP_LONG, 8)
                mem.put(addr + 8 + A, out, 16)
                mem.put(addr + 24 + A, n, ARG_BITS)
            self._lh[out, n] = self.var('longhead%d_%d' % (out, n), 56 + A, init)
        return self._lh[out, n].ref()

    def _lrecord(self, pos, out, n):
        pos = norm(pos)
        assert pos.n == POS_BITS and 0 < n < 1 << ARG_BITS, 'the position has 128 bits, the length is 1..2**32-1'
        q, A = self._lreq(n), self.A
        self.copy(q[0:56 + A], self._lhead(out, n))
        self.copy(q[56 + A:184 + A], pos)
        return q

    def _lsys(self, q, n):
        """The only row to SYS: the whole record (and the data after it)."""
        S, s = self.S, Ref(q, 0, n).addr
        self._op(l1.row(S, S, s, lambda: s() + n), [(q, 0, n)], [(SYS, 0, 1), (CHAN, 0, 1)])

    def long_put(self, pos, data):
        """`long!`: write the bits of `data` to the host at `pos`."""
        data = norm(data)
        q = self._lrecord(pos, 0, data.n)
        a = 184 + self.A
        self.copy(q[a:a + data.n], data)
        self._lsys(q, a + data.n)

    def long_get(self, pos, data):
        """`long@`: read len(data) bits from the host at `pos` into `data` (zeros where the host has nothing).
        A read of the answer of SYS needs room for a whole answer record (97 + A bits, contract of the
        emulator): a shorter `data` is read through a private buffer and copied, one layer more."""
        data = norm(data)
        q = self._lrecord(pos, 1, data.n)
        self._lsys(q, 184 + self.A)
        rsp = 97 + self.A
        if data.n >= rsp:
            dst = data
        else:
            if getattr(self, '_la', None) is None:
                self._la = self.var('longans', 0)
            self._la.bits = max(self._la.bits, rsp)
            dst = Ref(self._la, 0, rsp)
        d, n = dst.addr, dst.n
        self._op(l1.row(d, lambda: d() + n, self.S, self.S), [(SYS, 0, 1)], [(dst.region, dst.off, dst.off + n), (CHAN, 0, 1)])
        if dst is not data:
            self.copy(data, dst[0:data.n])
