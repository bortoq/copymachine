: b4 ( n -- ) 4 0 do dup 255 and emit 256 / loop drop ;
: main 100 7 / 48 + emit 1000000 3 / b4 -100 7 / b4 100 -7 / b4 -100 -7 / b4 2147483647 1 / b4 -2147483648 2 / b4 7 7 / 48 + emit 6 7 / 48 + emit ;
