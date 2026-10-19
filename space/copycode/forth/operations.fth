\ SPDX-License-Identifier: MIT
\ Requires integers, bitfields, format, instructions.
\ One summary: 16 cells. count, kind, channel(low/high), two spans(4 cells),
\ row pointer, format pointer, address width, reserved. Kind: 0=memory/NOP,
\ 1=data channel, 2=SYS request, 3=SYS response. Scratch is undefined on THROW.
\ Input row (8 cells), format (3 cells) and summary must be valid/disjoint.
decimal
: cc-op-index ( i op -- low high ) 12 cells + @ swap cc-endpoint@ ;
: cc-op-size ( op -- low high ) 13 cells + @ cc-d@ ;
: cc-op-a ( op -- a ) 14 cells + @ ;
: cc-op-span ( i op -- addr ) swap 4 * 4 + cells + ;
: cc-span! ( lo-low lo-high hi-low hi-high addr -- )
  >r r@ 2 cells + cc-d! r> cc-d! ;
: cc-op-empty? ( i op -- flag )
  >r dup r@ cc-op-index 2 pick 1+ r@ cc-op-index
  4 roll drop cc-du= r> drop ;
: cc-op-channel? ( i op -- flag )
  >r dup r@ cc-op-empty? swap r@ cc-op-index
  r> cc-op-size cc-du< 0= and ;
: cc-op-add-span ( lo-low lo-high hi-low hi-high op -- op )
  >r 2over 2over cc-du< 0= if -9 throw then
  2dup r@ cc-op-size 2swap cc-du< if -9 throw then
  r@ @ 2 < 0= if -8 throw then
  r@ @ r@ cc-op-span cc-span!
  r@ @ 1+ r@ ! r> ;
: cc-op-interval ( i op -- op )
  >r dup r@ cc-op-index 2 pick 1+ r@ cc-op-index
  4 roll drop r> cc-op-add-span ;
: cc-span-width ( addr -- low high )
  dup 2 cells + cc-d@ rot cc-d@ cc-d- ;
: cc-spans-overlap? ( span1 span2 -- flag )
  >r dup cc-d@ r@ 2 cells + cc-d@ cc-du<
  swap 2 cells + cc-d@ r> cc-d@ 2swap cc-du< and ;
: cc-op-memory ( op -- op )
  dup 2 swap cc-op-empty? if exit then
  0 swap cc-op-interval 2 swap cc-op-interval
  dup 4 cells + cc-span-width 2 pick 8 cells + cc-span-width
  cc-du= 0= if -24 throw then
  dup 4 cells + over 8 cells + cc-spans-overlap? if -24 throw then ;
: cc-op-device-span ( memory-index channel-index op -- op )
  >r r@ cc-op-index r@ 2 cells + cc-d!
  dup r@ cc-op-empty? if drop 0 r@ cell+ ! r> exit then
  dup r@ cc-op-index 2 pick 1+ r@ cc-op-index 4 roll drop
  r@ 2 cells + cc-d@ r@ cc-op-size cc-du=
  if
    2over r@ cell+ @ 2 = if 120 else 97 then r@ cc-op-a + 0
    cc-du+? if -9 throw then
    2over 2over cc-du< if 2swap 2drop else 2drop then
  else
    1 r@ cell+ !
    2over 2over 2swap cc-d- drop 7 and if -24 throw then
  then r> cc-op-add-span ;
: cc-op-device ( op -- op )
  dup 0 swap cc-op-channel?
  if 2 over cell+ ! 2 0 rot else 3 over cell+ ! 0 2 rot then
  cc-op-device-span ;
: cc-op-check ( row fmt op -- op )
  2 pick 8 cells 2 pick 16 cells cc-buffers-overlap? if -9 throw then
  over 3 cells 2 pick 16 cells cc-buffers-overlap? if -9 throw then
  over cc-format-check drop
  >r r@ 13 cells + ! r@ 12 cells + !
  0 r@ ! 0 r@ cell+ ! 0 0 r@ 2 cells + cc-d!
  r@ 13 cells + @ cc-format-a r@ 14 cells + ! r>
  4 0 do i over cc-op-index 2 pick cc-op-a cc-fits? 0= if -24 throw then loop
  dup 0 swap cc-op-channel? over 2 swap cc-op-channel?
  2dup and if -24 throw then or
  if cc-op-device else cc-op-memory then ;
: cc-op-devices-conflict? ( op1 op2 -- flag )
  2dup cell+ @ swap cell+ @
  2dup 2 = swap 2 = and if 2drop 2drop -1 exit then
  1 = swap 1 = and
  if over 2 cells + cc-d@ 2 pick 2 cells + cc-d@ cc-du= >r 2drop r>
  else 2drop 0 then ;
: cc-op-spans-conflict? ( op1 op2 -- flag )
  2dup @ swap @ 0 ?do
    dup 0 ?do
      2 pick j swap cc-op-span 2 pick i swap cc-op-span cc-spans-overlap?
      if drop 2drop unloop unloop -1 exit then
    loop
  loop drop 2drop 0 ;
: cc-ops-conflict? ( op1 op2 -- flag )
  2dup cc-op-devices-conflict? if 2drop -1 exit then cc-op-spans-conflict? ;
