\ SPDX-License-Identifier: MIT
\ Unsigned cell/double-cell utilities for the 32-bit guest.
\ Double values use (low high); addition/subtraction are modulo 2^64.
decimal
: cc-within ( u low high -- flag ) over - >r - r> u< ;
: within cc-within ;
: cc-du< ( lo1 hi1 lo2 hi2 -- flag )
  rot 2dup = if 2drop u< else u> >r 2drop r> then ;
: cc-du= ( lo1 hi1 lo2 hi2 -- flag )
  rot = >r = r> and ;
: cc-du+? ( lo1 hi1 lo2 hi2 -- lo hi overflow )
  2over >r >r d+ 2dup r> r> cc-du< ;
: cc-d- ( lo1 hi1 lo2 hi2 -- lo hi )
  invert swap invert swap 1 0 d+ d+ ;
: cc-udigit ( u -- ) dup 9 > if 7 + then 48 + emit ;
: cc-udigits ( u -- )
  0 base @ um/mod dup if recurse else drop then cc-udigit ;
: u. ( u -- )
  base @ 2 37 cc-within 0= if -24 throw then cc-udigits space ;
