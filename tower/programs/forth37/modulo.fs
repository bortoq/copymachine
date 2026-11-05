: b4 ( n -- ) 4 0 do dup 255 and emit 256 / loop drop ;
: main 100 7 mod 48 + emit 17 5 /mod 48 + emit 48 + emit 1000000 999 mod b4 0 5 mod 48 + emit ;
