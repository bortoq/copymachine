\ The kernel (9.6): the compiled compiler as the image of the space. It reads a program from stdin up to a zero byte
\ (or the end), compiles it into its own space and runs it; the rest of stdin is its input. The kernel is in the upper half
\ of the space (KERNEL-LAYOUT), the program in the lower half at the addresses of its boot stream. This MAIN replaces main.fth's.
kernel-layout
\ The sink of lay-put: numeric bytes written into the space, a cell at a time where the source is aligned; the
\ positions are the compiler's, nothing is checked.
variable kn-at
: kn-put ( bit-address src n -- )
  dup 0= if drop 2drop exit then
  rot kn-at !
  over 3 and 0= if
    dup 2 rshift 0 ?do over i cells + @ kn-at @ space! 32 kn-at +! loop
    dup -4 and rot + swap 3 and
  then
  0 ?do dup i + c@ kn-at @ spacec! 8 kn-at +! loop drop ;
: kn-order ( -- ) 256 0 do i lay-rev i + c! loop ;
\ Before the program runs, its layers, the table of entries and the table of returns are proved by DJ-PROVE (backend.fth), else -9.
: kn-get ( bit-address -- x ) space@ ;
: kn-compile ( -- )
  fc-sizes kn-order 1 fc-guard ! ['] kn-put lay-sink ! ['] kn-get dj-reader ! fc-read fc-go
  fc-first @ lay-next-cell @ dj-prove 0= if -9 throw then
  fc-etab lay-cell-bit rshift dup fc-nwords @ 2* + dj-prove 0= if -9 throw then
  fc-rtab lay-cell-bit rshift dup fc-nret @ 2* + dj-prove 0= if -9 throw then ;
: kn-.n ( n -- )
  dup 0< if [char] - emit negate then
  dup 10 / ?dup if recurse then 10 mod [char] 0 + emit ;
\ A compile error prints "error N at WORD" (the last word read) and halts.
: main ( -- )
  ['] kn-compile catch ?dup if
    s" error " type kn-.n s"  at " type fc-tok fc-tl @ type 10 emit exit
  then lay-start-cell @ execute ;
create kn-heap-start
kn-heap-start heap-ptr !
