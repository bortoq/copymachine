create %buf 80 cells allot
create %buf2 80 cells allot
variable %v
: %t-bmove16 1000 0 do %buf %buf2 16 drop drop drop loop ;
: %t-move16 1000 0 do %buf %buf2 16 cmove loop ;
: %t-move128 1000 0 do %buf %buf2 128 cmove loop ;
: %t-move127u 1000 0 do %buf 1+ %buf2 2 + 127 cmove loop ;
: %t-bnum 1000 0 do 12345 4 %buf drop drop drop loop ;
: %t-num4 1000 0 do 12345 4 %buf lay-numeric loop ;
: %t-num8 1000 0 do 12345 8 %buf 1+ lay-numeric loop ;
: %t-badd 1000 0 do 1 %v drop drop loop ;
: %t-padd 1000 0 do 1 %v +! loop ;
: %tsel key
  dup 104 = if drop %t-bmove16 exit then
  dup 105 = if drop %t-move16 exit then
  dup 106 = if drop %t-move128 exit then
  dup 107 = if drop %t-move127u exit then
  dup 108 = if drop %t-bnum exit then
  dup 109 = if drop %t-num4 exit then
  dup 110 = if drop %t-num8 exit then
  dup 111 = if drop %t-badd exit then
  dup 112 = if drop %t-padd exit then
  drop ;
: main ( -- ) fc-sizes kn-order fc-size 8 fc-cellb 4096 lay-machine lay-ebuf @ lay-dest ! %tsel ;
