\ SPDX-License-Identifier: MIT
\ Image bit codec. Bytes are MSB first; field significance is LSB first.
\ Public API: cc-field@ ( addr bytes bit width -- low high )
\             cc-field! ( low high addr bytes bit width -- )
\ 32-bit cells; unsigned double values, low cell first. Width is 0..64.
\ bytes is 0..268435455. The caller owns the declared buffer.
\ THROW -9: bounds; THROW -24: width/value overflow. No partial writes.
\ Internal words are unchecked. No global scratch state is used.
decimal
: cc-bit@ ( addr bit -- u )
  dup 3 rshift rot + c@ swap 7 and 7 swap - rshift 1 and ;
: cc-bit! ( u addr bit -- )
  dup 3 rshift rot + >r 7 and 128 swap rshift
  swap if r@ c@ or else invert r@ c@ and then r> c! ;
: cc-range ( bytes bit width -- bytes bit width )
  dup 0< over 64 > or if -24 throw then
  2 pick dup 0< swap 268435455 > or if -9 throw then
  over 0< if -9 throw then
  2 pick 8 * 2 pick 2dup u< if -9 throw then
  - over u< if -9 throw then ;
: cc-read-step ( addr bit value shift -- addr bit value' )
  >r 2 pick 2 pick r@ + cc-bit@ r> lshift or ;
: cc-read32 ( addr bit width -- u )
  >r 0 r> 0 ?do i cc-read-step loop >r 2drop r> ;
: cc-read64 ( addr bit width -- low high )
  dup 32 > if
    32 - >r 2dup 32 cc-read32 -rot 32 + r> cc-read32
  else cc-read32 0 then ;
: cc-field@ ( addr bytes bit width -- low high )
  cc-range >r swap drop r> cc-read64 ;
: cc-fits? ( low high width -- flag )
  dup 64 = if drop 2drop -1 exit then
  dup 32 < if
    >r swap r> rshift 0= swap 0= and
  else 32 - rshift 0= swap drop then ;
: cc-write-step ( addr bit value shift -- addr bit value )
  >r dup r@ rshift 1 and 3 pick 3 pick r> + cc-bit! ;
: cc-write32 ( addr bit value width -- )
  0 ?do i cc-write-step loop drop 2drop ;
: cc-write64 ( low high addr bit width -- )
  >r 2dup 5 pick r@ 32 min cc-write32
  32 + rot r> 32 - 0 max cc-write32 drop ;
: cc-field! ( low high addr bytes bit width -- )
  cc-range 5 pick 5 pick 2 pick cc-fits? 0= if -24 throw then
  >r swap drop r> cc-write64 ;
