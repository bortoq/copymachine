\ SPDX-License-Identifier: MIT
\ Requires integers.fth and bitfields.fth. Format = size(low/high), slots.
\ Numeric ABI geometry; layer bit count must fit a positive 32-bit cell.
\ Caller owns the three-cell descriptor. -24: invalid format. Atomic init.
decimal
: cc-d@ ( addr -- low high ) dup @ swap cell+ @ ;
: cc-d! ( low high addr -- ) >r swap r@ ! r> cell+ ! ;
: cc-ubits ( u -- n )
  0 swap begin dup while 1 rshift swap 1+ swap repeat drop ;
: cc-dbits ( low high -- n )
  dup if swap drop cc-ubits 32 + else drop cc-ubits then ;
: cc-format-values ( low high slots -- low high slots a )
  >r 2dup cc-dbits dup 0= if -24 throw then >r
  2dup 5 0 cc-du+? if -24 throw then
  r@ cc-fits? 0= if -24 throw then
  r> r> swap
  over 1 < if -24 throw then
  2147483647 over 4 * / 2 pick u< if -24 throw then
  2dup * 4 * 0 5 pick 5 pick 2swap cc-du< if -24 throw then ;
: cc-format-init ( low high slots fmt -- )
  >r cc-format-values drop r@ 2 cells + ! r> cc-d! ;
: cc-format-check ( fmt -- fmt )
  dup cc-d@ 2 pick 2 cells + @ cc-format-values 2drop 2drop ;
: cc-format-a ( fmt -- a ) cc-d@ cc-dbits ;
: cc-layer-bits ( fmt -- bits ) dup cc-format-a swap 2 cells + @ * 4 * ;
