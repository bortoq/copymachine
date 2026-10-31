create %buf 80 cells allot
variable %ba
: %t-empty 1000 0 do loop ;
: %t-bput8 1000 0 do %ba @ %buf 8 drop drop drop loop ;
: %t-put8 1000 0 do %ba @ %buf 8 kn-put loop ;
: %t-bput128 1000 0 do %ba @ %buf 128 drop drop drop loop ;
: %t-put128 1000 0 do %ba @ %buf 128 kn-put loop ;
: %t-put127u 1000 0 do %ba @ %buf 1+ 127 kn-put loop ;
: %t-put4 1000 0 do %ba @ %buf 4 kn-put loop ;
: %tsel key
  dup 97 = if drop %t-empty exit then
  dup 98 = if drop %t-bput8 exit then
  dup 99 = if drop %t-put8 exit then
  dup 100 = if drop %t-bput128 exit then
  dup 101 = if drop %t-put128 exit then
  dup 102 = if drop %t-put127u exit then
  dup 103 = if drop %t-put4 exit then
  drop ;
: main ( -- ) fc-sizes kn-order fc-size 8 fc-cellb 4096 lay-machine lay-ebuf @ lay-dest ! 1 30 lshift 1 28 lshift + %ba ! %tsel ;
