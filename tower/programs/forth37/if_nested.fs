: c ( n -- ) dup 0 < if drop 45 else dup 0= if drop 48 else 10 < if 115 else 76 then then then emit ;
: main -5 c 0 c 7 c 70 c ;
