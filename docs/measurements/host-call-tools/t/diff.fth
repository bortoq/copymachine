\ differential test (18.13): the definitions on the host against the originals, random inputs
variable %seed
: %rnd ( -- n ) %seed @ 69069 * 1+ dup %seed ! 8 rshift ;
: %rndw ( -- n ) %rnd 12 lshift %rnd xor ;
variable o-fc
: o-fill ( addr u c -- )
  over 3 and 3 pick 3 and or 0= if
    255 and 16843009 * o-fc ! 2 rshift 0 ?do o-fc @ over i cells + ! loop drop exit
  then swap 0 ?do 2dup swap i + c! loop 2drop ;
: o-row-clash? ( row1 row2 -- flag )
  cc-rb ! cc-ra ! 0
  2 0 do 2 0 do
    cc-ra @ j 2* cells + 2@ swap cc-rb @ i 2* cells + 2@ swap cc-clash? or
  loop loop ;
: o-encode ( rows count -- )
  cc-dest @ cc-lbytes 0 fill
  0 ?do
    4 0 do
      dup j 2 lshift i + cells + @ cc-field-check
      cc-a @ 32 = if cc-dest @ j 4 lshift + i 2 lshift + cc-numeric4
      else cc-a @ 3 rshift cc-dest @ j 2 lshift i + cc-a @ 3 rshift * + cc-numeric then
    loop
  loop drop ;
create %ta 600 allot create %tb 600 allot create %tr2 4 cells allot
variable %bad variable %off variable %len variable %byt
: %same? ( n -- f ) -1 swap 0 ?do %ta i + c@ %tb i + c@ = and loop ;
: %check ( f -- ) 0= if 1 %bad +! then ;
: %fill1 ( -- )
  256 0 do %rnd 255 and dup %ta i + c! %tb i + c! loop
  %rnd 7 and %off !
  %rnd 1 and if %rnd 31 and 2 lshift else %rnd 127 and then %len !
  %rnd 255 and %byt !
  %ta %off @ + %len @ %byt @ fill
  %tb %off @ + %len @ %byt @ o-fill
  256 %same? %check ;
: %val ( -- v ) %rnd 3 and dup 0= if drop -1 exit then dup 1 = if drop 2147483648 %rnd 15 and + exit then drop %rnd 31 and ;
: %row! ( addr -- ) 4 0 do %val over i cells + ! loop drop ;
: %sz ( -- n ) %rnd 3 and dup 0= if drop 32 exit then 1 = if 2147483648 exit then 20 ;
variable %clashes
: %row1 ( -- )
  %sz cc-size ! cc-new-row %row! %tr2 %row!
  cc-new-row %tr2 cc-row-clash? cc-new-row %tr2 o-row-clash? over over = %check
  if 1 %clashes +! then drop ;
: %enc1 ( -- )
  128 0 do 85 %ta i + c! 170 %tb i + c! loop
  32 0 do %rndw cc-rows i cells + ! loop
  %rnd 7 and 1+ >r
  %ta cc-dest ! cc-rows r@ cc-encode %tb cc-dest ! cc-rows r> o-encode
  128 %same? %check ;
variable %e1 variable %e2 variable %cnt
: %e-host ( -- ) %ta cc-dest ! cc-rows %cnt @ cc-encode ;
: %e-orig ( -- ) %tb cc-dest ! cc-rows %cnt @ o-encode ;
: %w24 ( -- ) 32 0 do %rnd 8 lshift 16777215 and cc-rows i cells + ! loop %rnd 7 and 1+ %cnt ! %e-host %e-orig 96 %same? %check ;
: %wthrow ( -- ) 32 0 do 2147483648 cc-rows i cells + ! loop
  %rnd 7 and 1+ %cnt ! ['] %e-host catch %e1 ! ['] %e-orig catch %e2 ! %e1 @ %e2 @ = %check %e1 @ -24 = if 1 %clashes +! then ;
: %wlast ( -- ) 32 0 do 5 cc-rows i cells + ! loop 2147483648 cc-rows 7 cells + !
  2 %cnt ! ['] %e-host catch %e1 ! ['] %e-orig catch %e2 ! %e1 @ %e2 @ = %check %e1 @ -24 = if 1 %clashes +! then ;
: %rep ( xt n -- ) 0 ?do dup execute loop drop ;
: %report ( -- ) %bad @ kn-.n 32 emit 0 %bad ! ;
: main ( -- )
  fc-sizes kn-order 2147483648 8 1024 4096 cc-machine 12345 %seed !
  ['] %fill1 200 %rep %report
  ['] %row1 1000 %rep %report %clashes @ kn-.n 32 emit 0 %clashes !
  ['] %enc1 100 %rep %report
  24 cc-a !
  ['] %w24 100 %rep %report
  ['] %wthrow 20 %rep %wlast %report %clashes @ kn-.n 10 emit ;
