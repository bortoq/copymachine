\ Direct Forth compiler (9.5): Forth source to emulator index code, in Forth.
\ Requires backend.fth and compute.fth. Control: scripts/forthc/model.py; for
\ the same source both write the same boot stream byte for byte, so every
\ layer, row, table, constant and cell is created in the model's order.
\ Usage: FC| <line> appends a source line, FC-GO compiles the text (word
\ MAIN is the entry) and types the stream, FC-RESET clears the text.
\ Cells may be 32 bits: values of 34 and 48 bits are kept as two cells.
\ Words keep their state in variables and are not reentrant. THROW -8:
\ capacity, -13: unknown word, -22: control structure, -16: missing word.
decimal
16777200 constant fc-size  1024 constant fc-cellb  768 constant fc-l
12582912 constant fc-d
fc-d constant fc-sp  fc-d 64 + constant fc-rp
fc-d 128 + constant fc-handler  fc-d 192 + constant fc-code
fc-d 1024 + constant fc-regs  48 constant fc-nregs
fc-d 4096 + constant fc-tmp  fc-d 4160 + constant fc-xr
fc-d 4224 + constant fc-z  fc-d 4288 + constant fc-idx
fc-d 4672 + constant fc-flt
fc-d 4800 + constant fc-ma  fc-d 4864 + constant fc-mb  fc-d 4928 + constant fc-mp
fc-d 4992 + constant fc-mq  fc-d 5056 + constant fc-mr
fc-d 5120 + constant fc-zero  fc-d 8192 + constant fc-consts
fc-d 131072 + constant fc-tab  fc-d 1048576 + constant fc-stk
fc-stk 16384 + constant fc-rstk  fc-d 2097152 + constant fc-mem  12 constant fc-mw
fc-stk 65536 + constant fc-scr0  fc-mem 262144 + constant fc-htab
256 constant fc-data-start

\ --- tables ----------------------------------------------------------------
create fc-off 17 cells allot variable fc-oc
variable fc-t-rev8 variable fc-t-zero32 variable fc-t-nz2 variable fc-t-lt32
variable fc-t-or8b variable fc-t-chk variable fc-t-fault variable fc-t-xr2
: fc-off@ ( c -- table ) 8 + cells fc-off + @ ;
\ Entry i: (i+c) & 255 in each of 8 bytes, then 8 zero bytes.
: fc-off-table ( c -- base )
  fc-oc ! 8 7 cc-table-area
  256 0 do dup i 16 * + 8 i fc-oc @ + 255 and cc-rev + c@ fill loop drop cc-table-done ;
: fc-rev-entry ( i -- v ) cc-rev + c@ ;
: fc-zero-entry ( i -- v ) 0= ;
: fc-nz-entry ( i -- v ) 0<> 3 and ;
: fc-lt-entry ( i -- v )
  >r r@ 1 rshift 1 and r@ 2 rshift 1 and <> if r@ 1 rshift 1 and else r@ 1 and 0= then
  r> drop 0<> ;
: fc-chk-entry ( i -- v ) dup 3 and 0<> 1 and swap 2 rshift 0<> 2 and or ;
: fc-fault-entry ( i -- lo hi )
  dup 7 and if drop -9 else 8 and if -23 else 0 then then
  dup if dup 2 lshift 3 or swap 30 rshift else 0 then ;
: fc-xr2-entry ( i -- v ) dup 1 rshift xor 1 and 3 * ;
: fc-tables ( -- )
  fc-tab fc-stk cc-tables cc-standard-tables
  17 0 do i 8 - fc-off-table i cells fc-off + ! loop
  ['] fc-rev-entry 8 4 cc-table fc-t-rev8 !
  ['] fc-zero-entry 4 6 cc-table fc-t-zero32 !
  ['] fc-nz-entry 4 2 cc-table fc-t-nz2 !
  ['] fc-lt-entry 3 6 cc-table fc-t-lt32 !
  ['] cc-or8-entry 8 1 cc-table fc-t-or8b !
  ['] fc-chk-entry 4 2 cc-table fc-t-chk !
  ['] fc-fault-entry 4 6 cc-table2 fc-t-fault !
  ['] fc-xr2-entry 2 2 cc-table fc-t-xr2 !
  fc-htab fc-size cc-tables ;
: fc-mul-entry ( i -- v )
  dup 15 and over 4 rshift 15 and * swap 8 rshift +
  dup 15 and over 4 rshift 4 lshift or swap 4 rshift 8 lshift or ;
: fc-qsel-entry ( i -- v ) dup 1 and if 2 rshift else 1 rshift then 1 and 3 * ;

\ --- constants: value low, high, bits; at fc-consts + 64 * index -----------
512 constant fc-max-consts
create fc-ck fc-max-consts 3 * cells allot variable fc-nconsts
: fc-ck@ ( i -- addr ) 3 * cells fc-ck + ;
: fc-const2 ( lo hi bits -- addr )
  fc-nconsts @ 0 ?do
    i fc-ck@ >r dup r@ 2 cells + @ = 2 pick r@ cell+ @ = and 3 pick r@ @ = and r> drop
    if drop 2drop i 64 * fc-consts + unloop exit then
  loop
  fc-nconsts @ fc-max-consts = if -8 throw then
  fc-nconsts @ fc-ck@ >r r@ 2 cells + ! r@ cell+ ! r> !
  fc-nconsts @ 64 * fc-consts + 1 fc-nconsts +! ;
: fc-const ( value -- addr ) 0 32 fc-const2 ;
\ Link fields of a continuation: cell and cell+layer, 24 bits each.
: fc-link-const ( cell -- addr )
  dup fc-l + dup 255 and 24 lshift rot or swap 8 rshift 64 fc-const2 ;
create fc-eight 8 allot create fc-zeros 16 allot fc-zeros 16 0 fill
: fc-put-consts ( -- )
  fc-nconsts @ 0 ?do
    i 64 * fc-consts + i fc-ck@ >r r@ 2 cells + @ 32 = if r@ @ 4 rot cc-put-numeric
    else r@ @ 4 fc-eight cc-numeric r@ cell+ @ 4 fc-eight 4 + cc-numeric
      fc-eight 8 cc-put then r> drop
  loop ;

\ --- stack cache and registers ----------------------------------------------
create fc-cache 64 cells allot variable fc-n
create fc-pin 16 cells allot variable fc-npin
: fc-c@ ( i -- r ) cells fc-cache + @ ;
: fc-push ( r -- ) fc-n @ 64 = if -8 throw then fc-n @ cells fc-cache + ! 1 fc-n +! ;
: fc-pop1 ( -- r ) -1 fc-n +! fc-n @ fc-c@ ;
: fc-in? ( r arr n -- f ) 0 swap 0 ?do 2 pick 2 pick i cells + @ = or loop nip nip ;
: fc-reg ( -- r )
  fc-nregs 0 do
    fc-regs i 64 * + dup fc-cache fc-n @ fc-in? over fc-pin fc-npin @ fc-in? or
    0= if unloop exit then drop
  loop -8 throw ;
: fc-reg-for-pop ( -- r ) fc-reg dup fc-npin @ cells fc-pin + ! 1 fc-npin +! ;
variable fc-scr
: fc-scratch ( bits align -- at )
  fc-scr @ over 1- + swap negate and dup rot + dup fc-mem u> if -8 throw then fc-scr ! ;

\ --- memory stacks ------------------------------------------------------------
create fc-offs 8 cells allot variable fc-noff variable fc-ptr
\ IDX+16k = pointer + offsets[k] (value, copy); pointer += delta.
: fc-adjust ( pointer delta -- )
  swap fc-ptr ! cc-lookups-begin
  fc-noff @ 0 ?do
    i cells fc-offs + @ fc-off@ 7 16 fc-idx i 16 * + 0 cc-item fc-ptr @ i 8 * + 8 0 cc-seg
  loop
  fc-off@ 7 64 fc-ptr @ 0 cc-item fc-ptr @ fc-noff @ 8 * + 8 0 cc-seg cc-lookups ;
create fc-prow 28 cells allot variable fc-nrow
create fc-pl 2 cells allot create fc-pslot 7 cells allot
variable fc-rl variable fc-f0 variable fc-f1
: fc-row+ ( dl dh sl sh -- )
  fc-nrow @ 4 * cells fc-prow + >r r@ 3 cells + ! r@ 2 cells + ! r@ cell+ ! r> ! 1 fc-nrow +! ;
: fc-4@ ( addr -- a b c d ) >r r@ @ r@ cell+ @ r@ 2 cells + @ r> 3 cells + @ ;
\ Rows whose endpoint fields f0, f1 get IDX+16k (and its copy) at bit 6.
: fc-patched ( f0 f1 -- )
  fc-f1 ! fc-f0 !
  fc-nrow @ 2* 6 + 7 / 0 ?do cc-layer i cells fc-pl + ! loop cc-layer drop
  cc-layer fc-rl !
  fc-nrow @ 0 ?do i 4 * cells fc-prow + fc-4@ fc-rl @ cc-row i cells fc-pslot + ! loop
  fc-nrow @ 0 ?do
    2 0 do
      8 fc-rl @ cc-layer-cell j cells fc-pslot + @ i if fc-f1 else fc-f0 then @ cc-field 6 +
      fc-idx j 16 * + i 8 * + cc-copy j 2* i + 7 / cells fc-pl + @ cc-row drop
    loop
  loop ;
create fc-popped 8 cells allot create fc-srcs 8 cells allot variable fc-nsrc
variable fc-mbase variable fc-mptr variable fc-mn variable fc-mw2
: fc-popped@ ( i -- r ) cells fc-popped + @ ;
: fc-mem-pop ( base pointer n width -- )
  fc-mw2 ! fc-mn ! fc-mptr ! fc-mbase !
  fc-mn @ 0 ?do fc-reg-for-pop i cells fc-popped + ! loop
  fc-mn @ 0 ?do i fc-mn @ - i cells fc-offs + ! loop fc-mn @ fc-noff !
  fc-mptr @ fc-mn @ negate fc-adjust
  0 fc-nrow ! fc-mn @ 0 ?do
    i fc-popped@ dup fc-mw2 @ + fc-mbase @ i 64 * + dup fc-mw2 @ + fc-row+
  loop 2 3 fc-patched ;
: fc-mem-push ( base pointer width -- )
  fc-mw2 ! fc-mptr ! fc-mbase !
  fc-nsrc @ 0 ?do i i cells fc-offs + ! loop fc-nsrc @ fc-noff !
  fc-mptr @ fc-nsrc @ fc-adjust
  0 fc-nrow ! fc-nsrc @ 0 ?do
    fc-mbase @ i 64 * + dup fc-mw2 @ + i cells fc-srcs + @ dup fc-mw2 @ + fc-row+
  loop 0 1 fc-patched ;
: fc-src1 ( r -- ) fc-srcs ! 1 fc-nsrc ! ;
\ Ensure n cached items, popping the missing ones from memory.
: fc-need ( n -- )
  fc-n @ - begin dup 0> while
    dup 7 min >r fc-stk fc-sp r@ 32 fc-mem-pop 0 fc-npin !
    fc-cache dup r@ cells + fc-n @ cells cmove>
    r@ 0 ?do i fc-popped@ i cells fc-cache + ! loop r@ fc-n +! r> -
  repeat drop ;
\ Write the cache to the data stack in memory, seven items per step.
: fc-spill ( -- )
  begin fc-n @ while
    fc-n @ 7 min fc-nsrc ! fc-nsrc @ 0 ?do i fc-c@ i cells fc-srcs + ! loop
    fc-cache fc-nsrc @ cells + fc-cache fc-n @ fc-nsrc @ - cells cmove
    fc-nsrc @ negate fc-n +! fc-stk fc-sp 32 fc-mem-push
  repeat ;
: fc-pop ( -- r ) 1 fc-need fc-pop1 ;

\ --- control --------------------------------------------------------------
variable fc-live variable fc-tramp variable fc-ex variable fc-thrower
: fc-jump ( target -- ) cc-seq# @ 0= if cc-layer drop then cc-jump ;
: fc-end ( -- ) cc-flush 0 fc-live ! ;
\ Start a new layer run at cell (-1: a new cell); the previous one continues.
: fc-begin-block ( cell|-1 -- cell )
  dup -1 = if drop cc-new-cell then
  fc-live @ if dup fc-jump then
  cc-flush dup cc-seq cc-layer drop -1 fc-live ! ;
: fc-rows1 ( dl dh sl sh -- ) cc-layer cc-row drop ;
: fc-nonzero ( r -- e )
  cc-lookups-begin fc-z swap 0 32 cc-or-chunks cc-lookups
  cc-lookups-begin fc-t-nz2 @ 2 2 fc-xr 0 cc-item fc-z 4 0 cc-seg cc-lookups fc-xr ;
: fc-branch ( flag -- zero yes ) fc-nonzero 1 cc-decide fc-end dup fc-cellb + ;
: fc-call ( entry -- )
  fc-spill cc-new-cell >r r@ fc-link-const fc-src1 fc-rstk fc-rp 48 fc-mem-push
  cc-jump fc-end r> fc-begin-block drop ;
variable fc-v0 variable fc-v1
: fc-call-indirect ( xt cont|-1 -- cont )
  fc-spill dup -1 = if drop cc-new-cell then >r
  r@ fc-link-const fc-src1 fc-rstk fc-rp 48 fc-mem-push
  cc-layer fc-v0 ! cc-layer fc-v1 ! cc-layer drop
  14 fc-ex @ 7 2 cc-field 10 + 2 pick 10 + cc-copy fc-v0 @ cc-row drop
  14 fc-ex @ 7 3 cc-field 10 + rot 10 + cc-copy fc-v1 @ cc-row drop
  fc-ex @ cc-jump fc-end r> ;
: fc-push-frame ( thrown -- )
  fc-link-const fc-sp fc-srcs ! fc-handler fc-srcs cell+ ! fc-srcs 2 cells + ! 3 fc-nsrc !
  fc-rstk fc-rp 48 fc-mem-push 64 fc-handler fc-rp cc-copy fc-rows1 ;
: fc-restore ( dst src -- ) \ pointer from the first copy, by the identity table
  >r >r 0 fc-off@ 7 64 r> 0 cc-item r> 8 0 cc-seg ;
: fc-build-thrower ( -- entry )
  0 fc-n ! -1 cc-seq 64 fc-rp fc-handler cc-copy fc-rows1 cc-entry
  fc-rstk fc-rp 3 48 fc-mem-pop 0 fc-npin !
  cc-lookups-begin fc-sp 0 fc-popped@ fc-restore fc-handler 1 fc-popped@ fc-restore cc-lookups
  48 fc-tramp @ 7 2 cc-field 2 fc-popped@ cc-copy fc-rows1
  cc-layer drop fc-tramp @ cc-jump fc-end ;
: fc-throw ( -- )
  fc-pop fc-spill 32 fc-code 2 pick cc-copy fc-rows1
  fc-branch cc-new-record fc-thrower @ swap cc-next! cc-flush fc-begin-block drop ;
: fc-catch ( -- )
  fc-pop >r fc-spill cc-new-cell cc-new-cell over fc-push-frame
  r> -1 fc-call-indirect fc-begin-block drop
  fc-rstk fc-rp 3 48 fc-mem-pop 0 fc-npin !
  cc-lookups-begin fc-handler 1 fc-popped@ fc-restore cc-lookups
  0 fc-n ! 0 fc-reg dup fc-push 32 swap rot fc-const cc-copy fc-rows1 fc-spill
  dup cc-jump fc-end
  swap fc-begin-block drop fc-reg dup >r 32 swap fc-code cc-copy fc-rows1 0 fc-n ! r> fc-push fc-spill
  dup cc-jump fc-end fc-begin-block drop ;
variable fc-ret-p variable fc-ret-l
: fc-ret ( -- )
  fc-spill -1 fc-offs ! 1 fc-noff ! fc-rp -1 fc-adjust
  cc-layer fc-ret-p ! cc-layer drop cc-layer fc-ret-l !
  fc-tramp @ 7 2 cc-field dup 48 + fc-rstk dup 48 + fc-ret-l @ cc-row >r
  8 fc-ret-l @ cc-layer-cell r@ 2 cc-field 6 + fc-idx cc-copy fc-ret-p @ cc-row drop
  8 fc-ret-l @ cc-layer-cell r> 3 cc-field 6 + fc-idx 8 + cc-copy fc-ret-p @ cc-row drop
  cc-layer drop fc-tramp @ cc-jump fc-end ;
\ Address check of register a; continues in the ok cell, a fault throws.
variable fc-ca variable fc-cl0 variable fc-cl1 variable fc-cr variable fc-cg variable fc-cx
variable fc-cv variable fc-cres variable fc-cslot variable fc-csh
\ Read row (dst, dst+w, table, table+w) in the read layer.
: fc-chk-read ( table sh w dst -- )
  >r swap fc-csh ! r@ over r> + 2swap over + fc-cr @ cc-row fc-cslot ! ;
\ Its index segment: patches in l0 (lower endpoint) and l1 (upper).
: fc-chk-seg ( src n off -- )
  fc-csh @ + >r 2dup fc-cr @ cc-layer-cell fc-cslot @ 2 cc-field r@ + rot cc-copy fc-cl0 @ cc-row drop
  fc-cr @ cc-layer-cell fc-cslot @ 3 cc-field r> + rot cc-copy fc-cl1 @ cc-row drop ;
\ store? 0: load into fc-cres before the decision; else store fc-cv after it.
: fc-check ( a store? -- )
  swap fc-ca !
  cc-layer fc-cl0 ! cc-layer fc-cl1 ! cc-layer drop cc-layer fc-cr !
  cc-t-or8 @ 1 1 fc-z fc-chk-read fc-ca @ 14 + 8 0 fc-chk-seg
  fc-t-or8b @ 1 1 fc-z 1+ fc-chk-read fc-ca @ 22 + 8 0 fc-chk-seg
  fc-t-chk @ 2 2 fc-z 2 + fc-chk-read fc-ca @ 30 + 2 0 fc-chk-seg fc-ca @ 2 2 fc-chk-seg
  cc-lookups-begin fc-t-fault @ 6 34 fc-flt 0 cc-item fc-z 4 0 cc-seg cc-lookups
  1 cc-group fc-cg ! cc-layer >r cc-layer drop cc-layer fc-cx ! fc-cg @ fc-cx @ cc-next!
  1 fc-cx @ cc-layer-cell 7 2 cc-field cc-cell-bit + fc-flt cc-copy r@ cc-row drop
  1 fc-cx @ cc-layer-cell 7 3 cc-field cc-cell-bit + fc-flt 1+ cc-copy r> cc-row drop
  fc-cg @ cc-seq
  if
    cc-layer >r fc-mem dup 32 + fc-cv @ dup 32 + r@ cc-row
    fc-mw r@ cc-layer-cell 2 pick 0 cc-field 6 + fc-ca @ 2 + cc-copy fc-cl0 @ cc-row drop
    fc-mw r> cc-layer-cell rot 1 cc-field 6 + fc-ca @ 2 + cc-copy fc-cl1 @ cc-row drop
  else
    fc-cres @ dup 32 + fc-mem dup 32 + fc-cr @ cc-row
    fc-mw fc-cr @ cc-layer-cell 2 pick 2 cc-field 6 + fc-ca @ 2 + cc-copy fc-cl0 @ cc-row drop
    fc-mw fc-cr @ cc-layer-cell rot 3 cc-field 6 + fc-ca @ 2 + cc-copy fc-cl1 @ cc-row drop
  then
  fc-cg @ fc-cellb + cc-new-record >r 32 fc-code fc-flt 2 + cc-copy r@ cc-row drop
  fc-thrower @ r> cc-next! -1 fc-live ! ;

\ --- straight-line scheduler (model: Sched) ---------------------------------
64 constant fc-ring 48 constant fc-window
create fc-sl fc-ring cells allot create fc-stabs fc-ring 8 * cells allot
variable fc-slen variable fc-slow
: fc-sinit ( first|-1 -- ) cc-seq 0 fc-slen ! 0 fc-slow ! ;
: fc-sbegin ( -- ) fc-slen @ fc-window - 0 max fc-slow ! ;
: fc-tabs ( t -- addr ) fc-ring mod 8 * cells fc-stabs + ;
: fc-at ( t -- layer )
  dup fc-slow @ - fc-ring < 0= if -8 throw then
  begin dup fc-slen @ < 0= while
    cc-layer fc-slen @ fc-ring mod cells fc-sl + ! 0 fc-slen @ fc-tabs ! 1 fc-slen +!
  repeat fc-ring mod cells fc-sl + @ ;
: fc-has? ( t table -- f ) swap fc-tabs 0 over @ 0 ?do over i 1+ cells + @ 3 pick = or loop nip nip ;
: fc-tab+ ( t table -- ) swap fc-tabs dup @ 1+ over ! dup @ cells + ! ;
create fc-prw 4 cells allot variable fc-ptab
: fc-place ( dl dh sl sh t table -- t slot )
  fc-ptab ! >r fc-prw 3 cells + ! fc-prw 2 cells + ! fc-prw cell+ ! fc-prw ! r> fc-slow @ max
  begin
    dup fc-at >r
    fc-ptab @ if dup fc-ptab @ fc-has? else 0 then 0= if
      fc-prw fc-4@ r@ cc-fits? if
        fc-prw fc-4@ r> cc-row fc-ptab @ if over fc-ptab @ fc-tab+ then exit
      then
    then r> drop 1+
  again ;
: fc-scopy ( n dst src ready -- t ) >r cc-copy fc-sbegin r> 0 fc-place drop 1+ ;
\ Segments: src, src for the upper endpoint, n, index offset, ready.
create fc-segs 20 cells allot variable fc-nseg
create fc-pp 48 cells allot variable fc-npp variable fc-latest variable fc-sga
variable fc-ltab variable fc-ls variable fc-lw variable fc-ldst
: fc-seg+ ( src src2 n off ready -- )
  fc-nseg @ 5 * cells fc-segs + >r r@ 4 cells + ! r@ 3 cells + ! r@ 2 cells + ! r@ cell+ ! r> !
  1 fc-nseg +! ;
: fc-pp+ ( t slot f x n off -- ) fc-npp @ 6 * cells fc-pp + 6 0 do tuck 5 i - cells + ! loop drop 1 fc-npp +! ;
: fc-slookup ( table s width dst preset -- t )
  >r fc-ldst ! fc-lw ! fc-ls ! fc-ltab ! fc-sbegin -2 fc-latest ! 0 fc-npp !
  fc-nseg @ 0 ?do
    i 5 * cells fc-segs + fc-sga !
    2 0 do
      0 0 fc-sga @ i cells + @ dup fc-sga @ 2 cells + @ + fc-sga @ 4 cells + @ 0 fc-place
      over fc-latest @ max fc-latest !
      i 2 + fc-sga @ i cells + @ fc-sga @ 2 cells + @ fc-sga @ 3 cells + @ fc-pp+
    loop
  loop
  fc-ltab @ r> fc-ls @ lshift + fc-ldst @ dup fc-lw @ + rot dup fc-lw @ +
  fc-latest @ 2 + fc-ltab @ fc-place ( t slot )
  fc-npp @ 0 ?do
    i 6 * cells fc-pp + fc-sga !
    fc-sga @ 4 cells + @ 2 pick fc-at cc-layer-cell 2 pick fc-sga @ 2 cells + @ cc-field
    fc-ls @ + fc-sga @ 5 cells + @ + fc-sga @ 3 cells + @ cc-copy
    fc-sga @ @ fc-at fc-sga @ cell+ @ cc-row-addr >r r@ 3 cells + ! r@ 2 cells + ! r@ cell+ ! r> !
  loop drop 1+ 0 fc-nseg ! ;
\ x = 0 + ~value + 1 by nibbles (the negation), step i writing x[4i, 4i+6).
variable fc-nx variable fc-nv variable fc-nt
: fc-negate-chain ( table x value ready -- t )
  fc-nt ! fc-nv ! fc-nx ! fc-nt @ 8 0 do
    fc-nv @ i 4 * + dup 4 4 fc-nt @ fc-seg+
    i if fc-nx @ i 4 * + dup 1+ 1 8 4 pick fc-seg+ then
    over 3 6 fc-nx @ i 4 * + i 0= if 256 else 0 then fc-slookup nip
  loop nip ;
\ dst = sign ? -value : value, from a window (value, negation).
variable fc-gw variable fc-gs variable fc-gs2 variable fc-gts variable fc-gdst
: fc-negate-select ( value t sign sign2 ts dst table -- t )
  >r fc-gdst ! fc-gts ! fc-gs2 ! fc-gs ! 128 128 fc-scratch fc-gw !
  2dup 32 fc-gw @ 2swap fc-scopy fc-gts @ max fc-gts !
  r> fc-gw @ 64 + 2swap fc-negate-chain fc-gts @ max fc-gts !
  fc-gs @ fc-gs2 @ 1 6 fc-gts @ fc-seg+ fc-gw @ 0 32 fc-gdst @ 0 fc-slookup ;
: fc-sfinish ( -- exit ) fc-slen @ 1- fc-at dup fc-cellb swap cc-next! cc-layer-cell ;

\ --- multiplication and division ------------------------------------------
create fc-pr 128 cells allot create fc-xs 128 cells allot   \ (reg, ready) pairs
variable fc-m4 variable fc-mj variable fc-mk
: fc-p@ ( i j -- reg t ) 8 * + 2* cells fc-pr + 2@ swap ;
: fc-p! ( reg t i j -- ) 8 * + 2* cells fc-pr + >r swap r> 2! ;
: fc-x@ ( j k -- reg t ) swap 8 * + 2* cells fc-xs + 2@ swap ;
: fc-x! ( reg t j k -- ) swap 8 * + 2* cells fc-xs + >r swap r> 2! ;
: fc-build-mul ( -- entry exit )
  -1 fc-sinit ['] fc-mul-entry 12 4 cc-table fc-m4 !
  8 0 do i fc-mj ! 8 i - 0 do
    16 64 fc-scratch
    fc-ma i 4 * + dup 4 0 0 fc-seg+ fc-mb fc-mj @ 4 * + dup 4 4 0 fc-seg+
    i if i 1- fc-mj @ fc-p@ >r dup 4 + swap 8 + 4 8 r> fc-seg+ then
    dup >r fc-m4 @ 4 12 r> 0 fc-slookup i fc-mj @ fc-p!
  loop loop
  8 0 do i 0 fc-p@ 0 i fc-x! loop
  8 1 do i fc-mj ! 8 i do i fc-mk !
    8 64 fc-scratch
    fc-mj @ 1- fc-mk @ fc-x@ >r dup 4 0 r> fc-seg+
    fc-mk @ fc-mj @ - fc-mj @ fc-p@ >r dup 4 4 r> fc-seg+
    fc-mk @ fc-mj @ > if fc-mj @ fc-mk @ 1- fc-x@ >r dup 4 + swap 5 + 1 8 r> fc-seg+ then
    dup >r cc-t-add @ 3 6 r> 0 fc-slookup fc-mj @ fc-mk @ fc-x!
  loop loop
  8 0 do 4 fc-mp i 4 * + i i fc-x@ fc-scopy drop loop
  cc-entry fc-sfinish ;
create fc-sub 3 cells allot variable fc-qsel
variable fc-absa variable fc-absb variable fc-ta variable fc-tb
variable fc-rem variable fc-tr variable fc-q variable fc-tq variable fc-k
variable fc-w variable fc-lo variable fc-tl variable fc-t0 variable fc-t1 variable fc-qr variable fc-tqk
: fc-sub@ ( i -- table ) cells fc-sub + @ ;
\ One step of a sub chain at nibble i of t - d; carry 0: none.
: fc-step ( table dst i carry t preset -- t )
  >r >r >r
  dup 0= if fc-absa @ fc-k @ + dup 1 0 fc-ta @ fc-seg+ fc-rem @ dup 3 1 fc-tr @ fc-seg+
  else fc-rem @ over 4 * + 1- dup 4 0 fc-tr @ fc-seg+ then
  fc-absb @ swap 4 * + dup 4 4 fc-tb @ fc-seg+
  r> r> swap ?dup if dup 1+ 1 8 4 pick fc-seg+ then drop
  3 6 rot r> 8 lshift fc-slookup ;
: fc-div-step ( -- )
  256 256 fc-scratch fc-w ! 32 64 fc-scratch fc-lo ! 0 fc-tl ! 0 fc-t0 ! 0 fc-t1 !
  4 0 do
    0 fc-sub@ fc-lo @ i 4 * + i i if fc-lo @ i 4 * + else 0 then fc-tl @ i 0= 1 and fc-step fc-tl !
    1 fc-sub@ fc-w @ 80 + i 4 * + i 4 + i if fc-w @ 80 + i 4 * + else 0 then fc-t0 @ 0 fc-step fc-t0 !
    2 fc-sub@ fc-w @ 208 + i 4 * + i 4 + i if fc-w @ 208 + i 4 * + else 0 then fc-t1 @ i 0= 1 and fc-step fc-t1 !
  loop
  2 64 fc-scratch fc-qr !
  fc-lo @ 16 + dup 1+ 1 0 fc-tl @ fc-seg+ fc-w @ 96 + dup 1+ 1 1 fc-t0 @ fc-seg+
  fc-w @ 224 + dup 1+ 1 2 fc-t1 @ fc-seg+ fc-qsel @ 2 2 fc-qr @ 0 fc-slookup fc-tqk !
  16 fc-w @ 64 + fc-lo @ fc-tl @ fc-scopy 16 fc-w @ 192 + fc-lo @ fc-tl @ fc-scopy max
  31 fc-w @ 1+ fc-rem @ fc-tr @ fc-scopy max 1 fc-w @ fc-absa @ fc-k @ + fc-ta @ fc-scopy max
  31 fc-w @ 129 + fc-rem @ fc-tr @ fc-scopy max 1 fc-w @ 128 + fc-absa @ fc-k @ + fc-ta @ fc-scopy max
  32 64 fc-scratch >r
  fc-qr @ dup 1+ 1 6 fc-tqk @ fc-seg+ fc-lo @ 16 + dup 1+ 1 7 4 roll fc-tl @ max fc-seg+
  fc-w @ 0 32 r@ 0 fc-slookup fc-tr ! r> fc-rem !
  1 fc-q @ fc-k @ + fc-qr @ fc-tqk @ fc-scopy fc-tq @ max fc-tq ! ;
: fc-build-div ( -- entry exit )
  -1 cc-seq cc-layer drop cc-entry fc-mb fc-nonzero 1 cc-decide fc-end
  dup cc-new-record >r 32 fc-code -10 fc-const cc-copy r@ cc-row drop fc-thrower @ r> cc-next!
  fc-cellb + fc-sinit
  3 0 do ['] cc-sub-entry 9 3 cc-table i cells fc-sub + ! loop
  ['] fc-qsel-entry 3 2 cc-table fc-qsel !
  32 64 fc-scratch fc-absa ! 32 64 fc-scratch fc-absb !
  fc-ma 0 fc-ma 31 + dup 0 fc-absa @ 0 fc-sub@ fc-negate-select fc-ta !
  fc-mb 0 fc-mb 31 + dup 0 fc-absb @ 1 fc-sub@ fc-negate-select fc-tb !
  fc-zero fc-rem ! 0 fc-tr ! 32 64 fc-scratch fc-q ! 0 fc-tq !
  32 0 do 31 i - fc-k ! fc-div-step loop
  2 64 fc-scratch >r fc-ma 31 + dup 1 0 0 fc-seg+ fc-mb 31 + dup 1 1 0 fc-seg+
  fc-t-xr2 @ 2 2 r@ 0 fc-slookup
  fc-q @ fc-tq @ r@ r> 1+ 4 roll fc-mq 0 fc-sub@ fc-negate-select drop
  fc-rem @ fc-tr @ fc-ma 31 + dup 0 fc-mr 1 fc-sub@ fc-negate-select drop
  fc-sfinish ;
variable fc-mul-entry variable fc-mul-exit variable fc-div-entry variable fc-div-exit
variable fc-hl variable fc-hcont
: fc-row-or-new ( dl dh sl sh -- )
  2over 2over fc-hl @ cc-fits? if fc-hl @ cc-row drop else cc-layer dup fc-hl ! cc-row drop then ;
\ Operands to MA/MB and the exit link patched with the continuation, one layer.
: fc-call-helper ( entry exit -- )
  2 fc-need fc-pop1 fc-pop1 2swap cc-new-cell fc-hcont !
  48 swap 7 2 cc-field fc-hcont @ fc-link-const cc-copy cc-layer dup fc-hl ! cc-row drop
  ( b a entry ) >r 32 fc-ma rot cc-copy fc-row-or-new 32 fc-mb rot cc-copy fc-row-or-new
  r> cc-jump cc-flush fc-hcont @ cc-seq ;
: fc-result1 ( src -- ) fc-reg dup fc-push 32 swap rot cc-copy fc-rows1 ;
variable fc-s1 variable fc-s2 variable fc-r1
: fc-result2 ( src1 src2 -- )
  fc-s2 ! fc-s1 ! fc-reg dup fc-push fc-r1 ! fc-reg dup fc-push
  32 fc-r1 @ fc-s1 @ cc-copy cc-layer dup >r cc-row drop 32 swap fc-s2 @ cc-copy r> cc-row drop ;

\ --- primitives ---------------------------------------------------------------
: fc-literal ( value -- ) fc-reg dup fc-push 32 swap rot fc-const cc-copy fc-rows1 ;
: fc-or-zero ( out r -- ) \ out = (r == 0) as 32 bits
  cc-lookups-begin fc-z swap 0 32 cc-or-chunks cc-lookups
  >r cc-lookups-begin fc-t-zero32 @ 6 32 r> 0 cc-item fc-z 4 0 cc-seg cc-lookups ;
variable fc-ba variable fc-bb variable fc-br
\ op: 0 + 1 - 2 and 3 or 4 xor 5 = 6 <
: fc-binary ( op -- )
  2 fc-need fc-pop1 fc-bb ! fc-pop1 fc-ba !
  fc-ba @ fc-bb @ = if
    fc-ba @ fc-push fc-reg fc-bb ! fc-pop1 drop 32 fc-bb @ fc-ba @ cc-copy fc-rows1
  then
  fc-ba @ fc-push fc-bb @ fc-push fc-reg fc-br ! fc-pop1 fc-pop1 2drop
  dup 2 < if
    dup if cc-t-sub @ else cc-t-add @ then fc-tmp fc-ba @ fc-bb @ 4 roll cc-adder
    32 fc-br @ fc-tmp cc-copy fc-rows1
  else dup 5 < if
    dup 2 = if cc-t-and @ else dup 3 = if cc-t-or @ else cc-t-xor @ then then
    fc-br @ fc-ba @ fc-bb @ cc-logic drop
  else 5 = if
    cc-t-xor @ fc-xr fc-ba @ fc-bb @ cc-logic fc-br @ fc-xr fc-or-zero
  else
    cc-t-sub @ fc-tmp fc-ba @ fc-bb @ 1 cc-adder
    cc-lookups-begin fc-t-lt32 @ 6 32 fc-br @ 0 cc-item
    fc-tmp 32 + 1 0 cc-seg fc-ba @ 31 + 1 1 cc-seg fc-bb @ 31 + 1 2 cc-seg cc-lookups
  then then then fc-br @ fc-push ;
: fc-r-at ( -- ) \ R@ and I
  fc-reg >r -1 fc-offs ! 1 fc-noff ! fc-rp 0 fc-adjust
  0 fc-nrow ! r@ dup 32 + fc-rstk dup 32 + fc-row+ 2 3 fc-patched r> fc-push ;

\ --- source text and words ------------------------------------------------
variable fc-text variable fc-tlen variable fc-pos 16384 constant fc-text-size
create fc-tok 256 allot variable fc-tl
: fc-reset ( -- ) fc-text @ 0= if fc-text-size allocate throw fc-text ! then 0 fc-tlen ! ;
: fc-append ( addr u -- )
  fc-text @ 0= if fc-reset then
  dup 1+ fc-tlen @ + fc-text-size > if -8 throw then
  tuck fc-text @ fc-tlen @ + swap cmove fc-tlen +! 10 fc-text @ fc-tlen @ + c! 1 fc-tlen +! ;
: fc| ( "line" -- ) source >in @ /string fc-append source nip >in ! ;
: fc-ch ( -- c ) fc-text @ fc-pos @ + c@ ;
: fc-more? ( -- f ) fc-pos @ fc-tlen @ < ;
\ Next word into fc-tok, ASCII letters folded to lower case; a word \ ends
\ the line. Words are runs of bytes above 32. False at the end of the text.
: fc-next ( -- f )
  begin
    begin fc-more? if fc-ch 33 < else 0 then while 1 fc-pos +! repeat
    fc-more? 0= if 0 exit then
    0 fc-tl !
    begin fc-more? if fc-ch 32 > else 0 then while
      fc-tl @ 255 = if -8 throw then
      fc-ch dup [char] A [char] Z 1+ over - >r - r> u< if 32 + then fc-tok fc-tl @ + c! 1 fc-tl +! 1 fc-pos +!
    repeat
    fc-tl @ 1 = fc-tok c@ [char] \ = and
  while begin fc-more? if fc-ch 10 <> else 0 then while 1 fc-pos +! repeat
  repeat -1 ;
: fc-next! ( -- ) fc-next 0= if -16 throw then ;
: fc-is? ( addr u -- f ) fc-tok fc-tl @ compare 0= ;
\ A decimal literal, optionally negative, modulo 2^32.
: fc-number ( -- n true | false )
  fc-tok fc-tl @ over c@ [char] - = if 1 /string -1 else 1 then >r
  dup 0= if 2drop r> drop 0 exit then
  0 -rot over + swap do
    i c@ [char] 0 - dup 10 u< 0= if 2drop unloop r> drop 0 exit then swap 10 * +
  loop r> * -1 ;
4096 constant fc-names-size 256 constant fc-max-words
create fc-names fc-names-size allot variable fc-names-used
create fc-wt fc-max-words 4 * cells allot variable fc-nwords   \ offset len kind value
: fc-define ( kind value -- )
  fc-nwords @ fc-max-words = fc-names-used @ fc-tl @ + fc-names-size > or if -8 throw then
  fc-nwords @ 4 * cells fc-wt + >r r@ 3 cells + ! r@ 2 cells + !
  fc-names-used @ r@ ! fc-tl @ r> cell+ !
  fc-tok fc-names fc-names-used @ + fc-tl @ cmove fc-tl @ fc-names-used +! 1 fc-nwords +! ;
: fc-find ( -- entry|0 )
  0 fc-nwords @ 0 ?do
    fc-nwords @ 1- i - 4 * cells fc-wt + >r
    r@ @ fc-names + r@ cell+ @ fc-tok fc-tl @ compare 0= if drop r> leave then r> drop
  loop ;

\ --- compiler -------------------------------------------------------------
variable fc-here variable fc-word variable fc-uses
create fc-ctl 64 cells allot variable fc-nctl
: fc-ctl+ ( kind cell -- ) fc-nctl @ 31 > if -8 throw then fc-ctl fc-nctl @ 2* cells + 2! 1 fc-nctl +! ;
: fc-ctl- ( -- kind cell ) fc-nctl @ 0= if -22 throw then -1 fc-nctl +! fc-ctl fc-nctl @ 2* cells + 2@ ;
: fc-init ( -- )
  fc-size 8 fc-cellb 4096 cc-machine 2 cc-builder fc-tables
  0 fc-nconsts ! 0 fc-n ! 0 fc-npin ! 0 fc-live ! 0 fc-nseg ! 0 fc-nwords ! 0 fc-names-used !
  0 fc-nctl ! fc-data-start fc-here ! 0 fc-word ! 0 fc-uses !
  cc-lone fc-cellb over cc-next! cc-layer-cell fc-tramp ! cc-flush
  cc-lone fc-cellb over cc-next! cc-layer-cell fc-ex ! cc-flush
  fc-scr0 fc-scr ! fc-build-thrower fc-thrower ! ;
: fc-scan-uses ( -- ) \ 1: *  2: / MOD /MOD
  0 fc-pos ! begin fc-next while
    s" *" fc-is? if fc-uses @ 1 or fc-uses ! then
    s" /" fc-is? s" mod" fc-is? or s" /mod" fc-is? or if fc-uses @ 2 or fc-uses ! then
  repeat 0 fc-pos ! ;
: fc-primitive ( -- )
  s" +" fc-is? if 0 fc-binary exit then  s" -" fc-is? if 1 fc-binary exit then
  s" and" fc-is? if 2 fc-binary exit then  s" or" fc-is? if 3 fc-binary exit then
  s" xor" fc-is? if 4 fc-binary exit then  s" =" fc-is? if 5 fc-binary exit then
  s" <" fc-is? if 6 fc-binary exit then
  s" *" fc-is? if fc-mul-entry @ fc-mul-exit @ fc-call-helper fc-mp fc-result1 exit then
  s" /" fc-is? if fc-div-entry @ fc-div-exit @ fc-call-helper fc-mq fc-result1 exit then
  s" mod" fc-is? if fc-div-entry @ fc-div-exit @ fc-call-helper fc-mr fc-result1 exit then
  s" /mod" fc-is? if fc-div-entry @ fc-div-exit @ fc-call-helper fc-mr fc-mq fc-result2 exit then
  s" 0=" fc-is? if fc-pop fc-reg tuck swap fc-or-zero fc-push exit then
  s" dup" fc-is? if 1 fc-need fc-n @ 1- fc-c@ fc-push exit then
  s" drop" fc-is? if
    fc-n @ if fc-pop1 drop else 0 fc-noff ! fc-sp -1 fc-adjust then exit then
  s" swap" fc-is? if 2 fc-need fc-pop1 fc-pop1 swap fc-push fc-push exit then
  s" over" fc-is? if 2 fc-need fc-n @ 2 - fc-c@ fc-push exit then
  s" rot" fc-is? if 3 fc-need fc-pop1 fc-pop1 fc-pop1 >r fc-push fc-push r> fc-push exit then
  s" >r" fc-is? if fc-pop fc-src1 fc-rstk fc-rp 32 fc-mem-push exit then
  s" r>" fc-is? if fc-rstk fc-rp 1 32 fc-mem-pop 0 fc-npin ! 0 fc-popped@ fc-push exit then
  s" r@" fc-is? s" i" fc-is? or if fc-r-at exit then
  s" @" fc-is? if
    fc-pop dup fc-pin ! 1 fc-npin ! fc-reg fc-cres ! 0 fc-npin ! 0 fc-check fc-cres @ fc-push exit then
  s" !" fc-is? if 2 fc-need fc-pop1 fc-pop1 fc-cv ! -1 fc-check exit then
  s" emit" fc-is? if
    fc-pop cc-lookups-begin fc-t-rev8 @ 4 8 fc-xr 0 cc-item 8 0 cc-seg cc-lookups
    cc-stdout dup fc-xr dup 8 + fc-rows1 exit then
  -13 throw ;
: fc-loop ( -- )
  fc-ctl- nip fc-spill fc-rstk fc-rp 2 32 fc-mem-pop 0 fc-npin !
  fc-regs fc-nregs 1- 64 * + >r
  cc-t-add @ fc-tmp 1 fc-popped@ 1 fc-const 0 cc-adder 32 r@ fc-tmp cc-copy fc-rows1
  cc-t-xor @ fc-xr r@ 0 fc-popped@ cc-logic
  fc-xr fc-branch ( start zero more ) cc-seq cc-layer drop
  0 fc-popped@ fc-srcs ! r> fc-srcs cell+ ! 2 fc-nsrc ! fc-rstk fc-rp 32 fc-mem-push
  swap cc-jump fc-end fc-begin-block drop ;
: fc-word-token ( -- ) \ inside a definition
  s" ;" fc-is? if fc-nctl @ if -22 throw then fc-ret 0 fc-word ! exit then
  s" exit" fc-is? if fc-ret -1 fc-begin-block drop exit then
  s" recurse" fc-is? if fc-word @ 3 cells + @ fc-call exit then
  s" [']" fc-is? if fc-next! fc-find dup 0= if -13 throw then 3 cells + @ fc-literal exit then
  s" execute" fc-is? if fc-pop -1 fc-call-indirect fc-begin-block drop exit then
  s" catch" fc-is? if fc-catch exit then
  s" throw" fc-is? if fc-throw exit then
  s" if" fc-is? if fc-pop fc-spill fc-branch swap 1 swap fc-ctl+ fc-begin-block drop exit then
  s" else" fc-is? if
    fc-ctl- nip fc-spill cc-new-cell dup fc-jump fc-end 2 swap fc-ctl+ fc-begin-block drop exit then
  s" then" fc-is? if
    fc-ctl- fc-spill swap 1 = if
      cc-new-cell dup fc-jump cc-flush swap cc-new-record over swap cc-next! fc-end fc-begin-block drop
    else fc-begin-block drop then exit then
  s" begin" fc-is? if fc-spill 3 -1 fc-begin-block fc-ctl+ exit then
  s" until" fc-is? if
    fc-pop fc-spill fc-branch swap cc-new-record fc-ctl- nip swap cc-next! cc-flush fc-begin-block drop exit then
  s" while" fc-is? if fc-pop fc-spill fc-branch swap 4 swap fc-ctl+ fc-begin-block drop exit then
  s" repeat" fc-is? if
    fc-ctl- nip fc-ctl- nip fc-spill fc-jump fc-end fc-begin-block drop exit then
  s" again" fc-is? if fc-ctl- nip fc-spill fc-jump fc-end -1 fc-begin-block drop exit then
  s" do" fc-is? if
    2 fc-need fc-pop1 fc-pop1 fc-spill fc-srcs ! fc-srcs cell+ ! 2 fc-nsrc ! fc-rstk fc-rp 32 fc-mem-push
    5 -1 fc-begin-block fc-ctl+ exit then
  s" loop" fc-is? if fc-loop exit then
  fc-find ?dup if dup 2 cells + @ if 3 cells + @ fc-call else 3 cells + @ fc-literal then exit then
  fc-number if fc-literal exit then
  fc-primitive ;
: fc-top-token ( -- )
  s" :" fc-is? if
    fc-next! cc-new-cell 1 over fc-define fc-nwords @ 1- 4 * cells fc-wt + fc-word !
    0 fc-live ! 0 fc-n ! fc-begin-block drop exit then
  s" variable" fc-is? if fc-next! 0 fc-here @ fc-define 4 fc-here +! exit then
  fc-number 0= if -13 throw then
  fc-next! s" constant" fc-is? 0= if -13 throw then fc-next! 0 swap fc-define ;
: fc-compile ( -- )
  fc-init fc-scan-uses
  fc-uses @ 1 and if fc-build-mul fc-mul-exit ! fc-mul-entry ! then
  fc-uses @ 2 and if fc-build-div fc-div-exit ! fc-div-entry ! then
  begin fc-next while
    s" (" fc-is? if begin fc-next! s" )" fc-is? until
    else fc-word @ if fc-word-token else fc-top-token then then
  repeat
  fc-word @ if -22 throw then
  s" main" fc-tok swap dup fc-tl ! cmove fc-find dup 0= if -16 throw then >r
  0 fc-live ! 0 fc-n ! -1 fc-begin-block cc-new-cell
  dup fc-push-frame r> 3 cells + @ fc-call fc-cellb fc-jump cc-flush
  cc-new-record fc-cellb swap cc-next! cc-flush
  fc-sp fc-zeros 8 cc-put fc-rp fc-zeros 8 cc-put fc-handler fc-zeros 8 cc-put
  fc-zero fc-zeros 16 cc-put fc-put-consts cc-finish ;
: fc-go ( -- ) fc-text @ 0= if fc-reset then fc-compile ;
