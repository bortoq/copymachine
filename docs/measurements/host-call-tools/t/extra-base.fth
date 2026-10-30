: %w1 ;
: %t-empty 1000 0 do loop ;
: %t-lit 1000 0 do cc-rows 32 cells 0 drop drop drop loop ;
: %t-lit1 1000 0 do cc-new-row drop loop ;
: %t-word 1000 0 do %w1 loop ;
: %t-fill 1000 0 do cc-rows 32 cells 0 fill loop ;
: %t-fill8 1000 0 do cc-rows 8 cells 0 fill loop ;
: %t-fillu 1000 0 do cc-rows 1+ 32 cells 0 fill loop ;
: %t-row 1000 0 do cc-new-row cc-new-row cc-row-clash? drop loop ;
: %t-enc 1000 0 do cc-rows 4 cc-encode loop ;
: %t-enc8 1000 0 do cc-rows 8 cc-encode loop ;
: %w3 ( a b c -- ) drop drop drop ;
: %t-and 1000 0 do cc-rows 3 and drop loop ;
: %t-or 1000 0 do cc-rows cc-new-row or drop loop ;
: %t-zeq 1000 0 do cc-rows 0= drop loop ;
: %t-if 1000 0 do cc-rows if then loop ;
: %t-pick 1000 0 do cc-rows cc-new-row 0 2 pick drop drop drop drop loop ;
: %t-w3 1000 0 do cc-rows 32 cells 0 %w3 loop ;
: %t-add 1000 0 do cc-rows 16 + drop loop ;
: %t-over3 1000 0 do cc-rows 32 cells 0 over 3 and 3 pick 3 and or 0= drop drop drop drop loop ;
: %t-shl 1000 0 do cc-rows 4 lshift drop loop ;

: %tsel key
  dup 97 = if drop %t-empty exit then
  dup 98 = if drop %t-lit exit then
  dup 99 = if drop %t-lit1 exit then
  dup 100 = if drop %t-word exit then
  dup 101 = if drop %t-fill exit then
  dup 102 = if drop %t-fill8 exit then
  dup 103 = if drop %t-fillu exit then
  dup 104 = if drop %t-row exit then
  dup 105 = if drop %t-enc exit then
  dup 106 = if drop %t-enc8 exit then
  dup 107 = if drop %t-and exit then
  dup 108 = if drop %t-or exit then
  dup 109 = if drop %t-zeq exit then
  dup 110 = if drop %t-if exit then
  dup 111 = if drop %t-pick exit then
  dup 112 = if drop %t-w3 exit then
  dup 113 = if drop %t-add exit then
  dup 114 = if drop %t-over3 exit then
  dup 115 = if drop %t-shl exit then
  drop ;
: main ( -- ) fc-sizes kn-order fc-size 8 fc-cellb 4096 cc-machine cc-ebuf @ cc-dest ! %tsel ;
