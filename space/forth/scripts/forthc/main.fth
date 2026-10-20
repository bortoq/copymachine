\ The compiled compiler: the source on stdin, the boot stream on stdout.
\ Compiled last, after prelude.fth, backend.fth, compute.fth and forthc.fth:
\ the heap starts after all static data.
create heap-start
heap-start heap-ptr !
\ Input ends at the end of stdin or at a zero byte.
: fc-read ( -- )
  fc-reset begin key ?dup while
    fc-tlen @ fc-text-size @ = if -8 throw then fc-text @ fc-tlen @ + c! 1 fc-tlen +!
  repeat ;
\ Room for the compiler's own source (pForth keeps the smaller defaults).
: main ( -- )
  131072 fc-text-size ! 4096 fc-max-consts ! 2048 fc-max-words ! 32768 fc-names-size !
  1024 fc-nbuckets ! fc-read fc-go ;
