# Positional address space (definition)

It is a half-open interval of uniformly typed values. Each half-open
interval of the space is addressed either by the positions bounding the
interval (vm1 addressing; the bounds are strictly greater and strictly
less), or by the lower position of the half-open interval and the interval
size (vm2 addressing; the lower bound belongs to the half-open interval,
and the upper bound is strictly greater than the half-open interval).
Half-open intervals of the same size can be copied (violating the
isolation* of some values by others), i.e. assigning the value of one
half-open interval to another.

space-emulator is a mechanism of vm2 addressing of bit values.

Copying can be performed between address spaces.

Channels are also positionally addressable values, but they differ from
the other values of the space in that they have a different type. From
this single position one can read not a bit but a much larger quantity.

For simultaneous copying in one tick, all source and destination
half-intervals specified by active instructions are pairwise disjoint.
This includes the source intervals of different copies: a position cannot
serve as the source of two copies in that tick. Distinct half-intervals may
share a boundary, which is not an overlap.
