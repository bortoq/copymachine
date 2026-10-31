: %w1 ;
: %w3 ( a b c -- ) drop drop drop ;
create %rec 31 cells allot
: %t-empty 1000 0 do loop ;
: %t-lit 1000 0 do lay-rows 32 cells 0 drop drop drop loop ;
: %t-word 1000 0 do %w1 loop ;
: %t-w3 1000 0 do lay-rows 32 cells 0 %w3 loop ;
: %t-if 1000 0 do lay-rows if then loop ;
: %t-pick 1000 0 do lay-rows lay-new-row 0 2 pick drop drop drop drop loop ;
: %t-add 1000 0 do lay-rows 16 + drop loop ;
: %t-and 1000 0 do lay-rows 3 and drop loop ;
: %t-fill 1000 0 do lay-rows 32 cells 0 fill loop ;
: %t-fill8 1000 0 do lay-rows 8 cells 0 fill loop ;
: %t-fillu 1000 0 do lay-rows 1+ 127 0 fill loop ;
: %t-fill1k 1000 0 do lay-rows 1024 0 fill loop ;
: %t-enc 1000 0 do lay-rows 4 lay-encode loop ;
: %t-enc8 1000 0 do lay-rows 8 lay-encode loop ;
: %t-row 1000 0 do lay-clashes? drop loop ;
: %t-clashes 3 %rec 2 cells + ! %rec lay-cur ! 1000 0 do lay-clashes? drop loop ;
: %t-clashes0 0 %rec 2 cells + ! %rec lay-cur ! 1000 0 do lay-clashes? drop loop ;

: %tsel key
  dup 97 = if drop %t-empty exit then
  dup 98 = if drop %t-lit exit then
  dup 100 = if drop %t-word exit then
  dup 101 = if drop %t-fill exit then
  dup 102 = if drop %t-fill8 exit then
  dup 103 = if drop %t-fillu exit then
  dup 104 = if drop %t-row exit then
  dup 105 = if drop %t-enc exit then
  dup 106 = if drop %t-enc8 exit then
  dup 108 = if drop %t-fill1k exit then
  dup 109 = if drop %t-clashes exit then
  dup 110 = if drop %t-if exit then
  dup 111 = if drop %t-pick exit then
  dup 112 = if drop %t-w3 exit then
  dup 113 = if drop %t-add exit then
  dup 114 = if drop %t-and exit then
  dup 115 = if drop %t-clashes0 exit then
  drop ;
: main ( -- ) fc-sizes kn-order fc-size 8 fc-cellb 4096 lay-machine lay-ebuf @ lay-dest ! %tsel ;
