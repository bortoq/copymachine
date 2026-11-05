: fib ( n -- f ) dup 2 < if exit then dup 1 - recurse swap 2 - recurse + ;
: main 10 fib emit 12 fib 100 - emit ;
