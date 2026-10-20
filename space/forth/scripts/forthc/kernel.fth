\ The kernel (9.6): the compiled compiler as the image of the space. It reads
\ a program from stdin up to a zero byte (or the end of input), compiles it
\ into its own space and runs it; the rest of stdin is the program's input.
\ The kernel lives in the upper half of the space (KERNEL-LAYOUT), the
\ program in the lower half at the addresses of its boot stream, so it runs
\ as if loaded from that stream. Compiled after main.fth; this MAIN replaces
\ that one.
kernel-layout
\ The sink of cc-put: numeric bytes written into the space, a cell (32 bits)
\ at a time where the source is aligned. Only the program's half is written:
\ [0, 2^29) and [2^30, 2^30 + 2^29), else THROW -9.
variable kn-at
: kn-put ( bit-address src n -- )
  dup 0= if drop 2drop exit then
  2 pick dup 2 pick 3 lshift + 1- 29 rshift swap 29 rshift tuck <> swap 1 and or
  3 pick 7 and or if -9 throw then
  rot kn-at !
  over 3 and 0= if
    dup 2 rshift 0 ?do over i cells + @ kn-at @ dup 32 + space! 32 kn-at +! loop
    dup -4 and rot + swap 3 and
  then
  0 ?do dup i + c@ kn-at @ dup 8 + spacec! 8 kn-at +! loop drop ;
: kn-order ( -- ) 256 0 do i cc-rev i + c! loop ;
: kn-compile ( -- ) fc-sizes kn-order ['] kn-put cc-sink ! fc-read fc-go ;
: kn-.n ( n -- ) \ decimal
  dup 0< if [char] - emit negate then
  dup 10 / ?dup if recurse then 10 mod [char] 0 + emit ;
\ A compile error prints "error N at WORD" (the last word read) and halts.
: main ( -- )
  ['] kn-compile catch ?dup if
    s" error " type kn-.n s"  at " type fc-tok fc-tl @ type 10 emit exit
  then cc-start-cell @ execute ;
\ The heap starts after the strings above.
create kn-heap-start
kn-heap-start heap-ptr !
