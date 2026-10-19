\ SPDX-License-Identifier: MIT
\ Requires bitfields.fth. Raw four-index instruction encoder, 32-bit cells.
\ cc-instruction! ( row buffer bytes bit address-bits -- )
\ row: eight cells, low/high pairs for dl, dh, sl, sh. Width is 1..64.
\ Row and declared output buffer must be disjoint, valid owned allocations.
\ THROW -9: bounds/alias; -24: width/endpoint overflow. No partial writes.
\ Copy/channel semantics and conflicts between instructions are not checked.
decimal
: cc-instruction-range ( bytes bit a -- bytes bit a )
  dup 1 < over 64 > or if -24 throw then
  >r 0 cc-range drop
  2dup swap 8 * swap - r@ 4 * u< if -9 throw then r> ;
: cc-buffers-overlap? ( addr1 bytes1 addr2 bytes2 -- flag )
  3 pick 3 pick + 2 pick u> >r
  + rot u> swap drop r> and ;
: cc-endpoint@ ( row index -- low high )
  2 * cells + dup @ swap cell+ @ ;
: cc-instruction! ( row buffer bytes bit a -- )
  cc-instruction-range
  4 pick 8 cells 5 pick 5 pick cc-buffers-overlap?
  if -9 throw then
  4 0 do
    4 pick i cc-endpoint@ 2 pick cc-fits? 0= if -24 throw then
  loop
  4 0 do
    4 pick i cc-endpoint@
    5 pick 5 pick 5 pick 5 pick i * + 5 pick cc-field!
  loop
  drop 2drop 2drop ;
