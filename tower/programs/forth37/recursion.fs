: fact ( n -- n! ) dup 1 < if drop 1 else dup 1 - recurse * then ;
: main 5 fact emit 0 fact 48 + emit 4 fact emit ;
