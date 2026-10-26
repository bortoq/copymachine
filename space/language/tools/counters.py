"""The counters of 13.4 (space/vm2/tests/vm2_reference.py) on the execution of a stream of the language.

vm2_reference.run executes the three-field images of vm2 ([n, dst, src] rows of 3A-1 bits, at most
1000 ticks, a full copy of the memory each tick): it cannot execute the four-index stream of the
language (emulator contract: rows [dst_low, dst_high, src_low, src_high] of 4A bits, S = 2^31). This
module is the same machine for the four-index rows: the bit functions of vm2_reference (get, put,
payload, store_bytes) on a sparse memory, all sources read before any write, and per tick the
counters with the definitions of 13.4 (as vm2_reference.run counts them):

    layers        executed ticks;
    copies        instructions with n > 0 that changed memory or moved at least one byte through a
                  channel (a memory copy that writes the bits already there is not counted);
    bits          n of every memory-to-memory copy;
    channel_bits  8 * bytes moved through the channels.

and also `rows`: the instructions with n > 0 executed (changed or not), which the compiler counts as
the copies of a word (space/language/doc/word.md). The cell of a tick is the target of the link row
(slot P-1, [0, P*4A, cell, cell + P*4A]) of the tick before.
"""
import sys

import paths

sys.path.insert(0, str(paths.VM2_ROOT / 'tests'))
from vm2_reference import get, put, payload, store_bytes  # noqa: E402


class Memory:
    """Sparse bytes of the space (pages of 4 KiB, absent pages are zero), indexed as a bytearray."""
    def __init__(self):
        self.pages = {}

    def __getitem__(self, i):
        page = self.pages.get(i >> 12)
        return page[i & 4095] if page is not None else 0

    def __setitem__(self, i, value):
        page = self.pages.get(i >> 12)
        if page is None:
            if not value:
                return
            page = self.pages[i >> 12] = bytearray(4096)
        page[i & 4095] = value


def run(stream, size=paths.SIZE, slots=8, limit=2_000_000):
    """Execute stream (stdin) from the seed; return dict(out, ticks, trace). trace[t] =
    (cell, rows, copies, bits, channel_bits) of tick t; cell is None for a tick not entered by a link row."""
    a = size.bit_length()
    stdin, stdout = size + 1, size + 2
    layer = slots * 4 * a
    memory = Memory()
    for value, at in ((0, 0), (layer, a), (stdin, 2 * a), (stdin, 3 * a)):      # the seed of slot 0
        put(memory, at, a, value)
    cursor, out, trace, cell = 0, bytearray(), [], None
    for _ in range(limit):
        rows = [tuple(get(memory, (i * 4 + k) * a, a) for k in range(4)) for i in range(slots)]
        reads, writes, count, copies, bits, channel = [], [], 0, 0, 0, 0
        for dl, dh, sl, sh in rows:
            if dl == dh and dl >= size:                      # output channel
                if sl < sh:
                    assert dl == stdout, ('channel', dl - size)
                    reads.append(('out', payload(memory, sl, (sh - sl + 7) // 8)))
            elif sl == sh and sl >= size:                    # input channel
                if dl < dh:
                    assert sl == stdin, ('channel', sl - size)
                    reads.append(('in', dl, (dh - dl + 7) // 8))
            elif sl < sh:                                    # ordinary copy (an empty source is NOP)
                assert dh - dl == sh - sl, (dl, dh, sl, sh)
                reads.append(('copy', dl, sh - sl, get(memory, sl, sh - sl), get(memory, dl, dh - dl)))
        if not reads:
            break
        for item in reads:                                   # all sources were read: now the writes
            count += 1
            if item[0] == 'copy':
                _, dl, n, value, old = item
                bits += n
                copies += value != old
                put(memory, dl, n, value)
            elif item[0] == 'out':
                out += item[1]
                copies += 1
                channel += 8 * len(item[1])
            else:
                _, dl, nbytes = item
                chunk = stream[cursor:cursor + nbytes]
                cursor += len(chunk)
                store_bytes(memory, dl, chunk)
                copies += bool(chunk)
                channel += 8 * len(chunk)
        trace.append((cell, count, copies, bits, channel))
        dl, dh, sl, sh = rows[slots - 1]
        cell = sl if (dl, dh) == (0, layer) and sh == sl + layer else None
    else:
        raise AssertionError('tick limit')
    return dict(out=bytes(out), ticks=len(trace), trace=trace)


def window(trace, entry, entries, tramp, start=0):
    """The ticks of one execution of the word at entry (from its first tick at or after start):
    (first, last), last the tick of the trampoline of its return; the calls inside (ticks at the entry
    of a word, entries) and their returns (ticks at the trampoline) are nested."""
    first = next(t for t in range(start, len(trace)) if trace[t][0] == entry)
    depth = 0
    for t in range(first + 1, len(trace)):
        if trace[t][0] in entries:
            depth += 1
        elif trace[t][0] == tramp:
            if depth == 0:
                return first, t
            depth -= 1
    raise AssertionError('no return')


def counters(trace, first, last):
    """The counters of the ticks [first, last]: dict(layers, rows, copies, bits, channel_bits)."""
    ticks = trace[first:last + 1]
    return dict(layers=len(ticks), rows=sum(t[1] for t in ticks), copies=sum(t[2] for t in ticks),
                bits=sum(t[3] for t in ticks), channel_bits=sum(t[4] for t in ticks))
