\ SPDX-License-Identifier: MIT
\ Numeric 32-bit arena, descriptor = base, limit, cursor (three cells).
\ Units are chosen by the caller (e.g. emulator bits); no host allocation.
\ Unsigned endpoints, exclusive limit. Descriptor must be a valid allocation.
\ -9 invalid bounds/rollback; -24 invalid alignment; -8 capacity exhausted.
decimal
: cc-arena-init ( base limit arena -- )
  >r 2dup u> if -9 throw then
  over r@ ! dup r@ cell+ ! drop r> 2 cells + ! ;
: cc-arena-mark ( arena -- cursor ) 2 cells + @ ;
: cc-arena-used ( arena -- n ) dup cc-arena-mark swap @ - ;
: cc-arena-restore ( mark arena -- )
  >r dup r@ @ u< over r@ cc-arena-mark u> or if -9 throw then
  r> 2 cells + ! ;
: cc-arena-reset ( arena -- ) dup @ swap cc-arena-restore ;
: cc-arena-alloc ( count align arena -- at )
  >r dup 0= over dup 1- and 0<> or if -24 throw then
  1- r@ cc-arena-mark negate and
  r@ cell+ @ r@ cc-arena-mark -
  2dup swap u< if -8 throw then
  over - 2 pick u< if -8 throw then
  r@ cc-arena-mark + swap over + r> 2 cells + ! ;
