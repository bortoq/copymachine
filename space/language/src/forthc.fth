\ Direct Forth compiler (9.5): Forth source to emulator index code, in Forth.
\ Requires backend.fth and compute.fth. Control: scripts/forthc/model.py; for
\ the same source both write the same boot stream byte for byte, so every
\ layer, row, table, constant and cell is created in the model's order.
\ Usage: FC| <line> appends a source line, FC-GO compiles the text (word
\ MAIN is the entry) and types the stream, FC-RESET clears the text.
\ Cells may be 32 bits: values of 34 and 64 bits are kept as two cells.
\ Words keep their state in variables and are not reentrant. THROW -8:
\ capacity, -13: unknown word, -22: control structure, -16: missing word.
decimal
1 31 lshift constant fc-size  1024 constant fc-cellb  1024 constant fc-l  32 constant fc-a
\ The data region at fc-d and the first code cell: a program at 2^30 and 2,
\ a kernel (a source with KERNEL-LAYOUT) in the upper half of both, so the
\ programs it installs in its own space keep their layout (model: layout).
variable fc-d variable fc-first variable fc-kernel
: fc-layout ( kernel? -- )
  if 3 29 lshift 1 19 lshift else 1 30 lshift 2 then fc-first ! fc-d ! ;
: fc-d+ ( offset -- addr ) fc-d @ + ;
: fc-sp 0 fc-d+ ;  : fc-rp 64 fc-d+ ;  : fc-handler 128 fc-d+ ;  : fc-code 192 fc-d+ ;
: fc-regs 1024 fc-d+ ;  48 constant fc-nregs
: fc-tmp 4096 fc-d+ ;  : fc-xr 4160 fc-d+ ;  : fc-z 4224 fc-d+ ;  : fc-idx 4288 fc-d+ ;
: fc-flt 4672 fc-d+ ;
: fc-ma 4800 fc-d+ ;  : fc-mb 4864 fc-d+ ;  : fc-mp 4928 fc-d+ ;  : fc-mq 4992 fc-d+ ;  : fc-mr 5056 fc-d+ ;
: fc-zero 5120 fc-d+ ;  : fc-consts 8192 fc-d+ ;
: fc-sw 5376 fc-d+ ;  : fc-su 5440 fc-d+ ;  : fc-key 5504 fc-d+ ;  : fc-bp 5568 fc-d+ ;
: fc-tab 1 19 lshift fc-d+ ;  : fc-stk 1 21 lshift fc-d+ ;
: fc-rstk 1 21 lshift 1 15 lshift + fc-d+ ;  : fc-scr0 1 21 lshift 1 16 lshift + fc-d+ ;
: fc-links 1 22 lshift fc-d+ ;  1 15 lshift constant fc-max-links  512 constant fc-link-chunk
: fc-mem 1 23 lshift fc-d+ ;  17 constant fc-mw  : fc-htab 1 24 lshift fc-d+ ;
256 constant fc-data-start

\ --- tables ----------------------------------------------------------------
create fc-off 17 cells allot variable fc-oc
variable fc-t-rev8 variable fc-t-zero32 variable fc-t-nz2 variable fc-t-lt32
variable fc-t-or8b variable fc-t-fault variable fc-t-xr2 variable fc-t-ult32 variable fc-t-bytepos
: fc-off@ ( c -- table ) 8 + cells fc-off + @ ;
\ Entry i: (i+c) & 255 in each of 8 bytes, then 8 zero bytes.
: fc-off-table ( c -- base )
  fc-oc ! 8 7 cc-table-area
  256 0 do dup i 16 * + 8 i fc-oc @ + 255 and cc-rev + c@ fill loop drop cc-table-done ;
: fc-rev-entry ( i -- v ) 0 8 0 do 2* over i rshift 1 and or loop nip ;
: fc-zero-entry ( i -- v ) 0= ;
: fc-nz-entry ( i -- v ) 0<> 3 and ;
: fc-lt-entry ( i -- v )
  >r r@ 1 rshift 1 and r@ 2 rshift 1 and <> if r@ 1 rshift 1 and else r@ 1 and 0= then
  r> drop 0<> ;
: fc-fault-entry ( i -- lo hi )
  dup 3 and if drop -9 else 12 and if -23 else 0 then then
  dup if dup 2 lshift 3 or swap 30 rshift else 0 then ;
: fc-xr2-entry ( i -- v ) dup 1 rshift xor 1 and 3 * ;
: fc-ult-entry ( i -- v ) 0= ;
\ Bit offsets of byte i in its cell: 8i for the lower endpoint, 8i+8 above.
: fc-bytepos-entry ( i -- v ) 8 * dup 8 + 6 lshift or ;
: fc-tables ( -- )
  fc-tab fc-stk cc-tables cc-standard-tables
  17 0 do i 8 - fc-off-table i cells fc-off + ! loop
  ['] fc-rev-entry 8 4 cc-table fc-t-rev8 !
  ['] fc-zero-entry 4 6 cc-table fc-t-zero32 !
  ['] fc-nz-entry 4 2 cc-table fc-t-nz2 !
  ['] fc-lt-entry 3 6 cc-table fc-t-lt32 !
  ['] cc-or8-entry 8 1 cc-table fc-t-or8b !
  ['] fc-fault-entry 4 6 cc-table2 fc-t-fault !
  ['] fc-xr2-entry 2 2 cc-table fc-t-xr2 !
  ['] fc-ult-entry 1 6 cc-table fc-t-ult32 !
  ['] fc-bytepos-entry 2 4 cc-table fc-t-bytepos !
  fc-htab fc-size cc-tables ;
: fc-mul4-entry ( i -- v )
  dup 15 and over 4 rshift 15 and * swap 8 rshift +
  dup 15 and over 4 rshift 4 lshift or swap 4 rshift 8 lshift or ;
: fc-qsel-entry ( i -- v ) dup 1 and if 2 rshift else 1 rshift then 1 and 3 * ;

\ --- constants: value low, high, bits; at fc-consts + 64 * index -----------
\ Tables live in the heap, allocated once at the sizes in these variables;
\ words and constants are found through hash chains (index+1, 0 ends).
variable fc-max-consts 384 fc-max-consts ! variable fc-ck variable fc-nconsts
variable fc-nbuckets 256 fc-nbuckets ! variable fc-cbk
: fc-ck@ ( i -- addr ) 4 * cells fc-ck @ + ;   \ value low, high, bits, next
: fc-chash ( lo hi bits -- addr ) + + dup 16 rshift xor fc-nbuckets @ 1- and cells fc-cbk @ + ;
variable fc-cb
: fc-const2 ( lo hi bits -- addr )
  2 pick 2 pick 2 pick fc-chash dup fc-cb ! @
  begin ?dup while
    1- dup fc-ck@ >r 3 pick r@ @ = 3 pick r@ cell+ @ = and 2 pick r@ 2 cells + @ = and
    if r> drop >r drop 2drop r> 64 * fc-consts + exit then
    drop r> 3 cells + @
  repeat
  fc-nconsts @ fc-max-consts @ = if -8 throw then
  fc-nconsts @ fc-ck@ >r r@ 2 cells + ! r@ cell+ ! r@ ! fc-cb @ @ r> 3 cells + !
  fc-nconsts @ 1+ fc-cb @ ! fc-nconsts @ 64 * fc-consts + 1 fc-nconsts +! ;
: fc-const ( value -- addr ) 0 32 fc-const2 ;
\ Link pool: the link fields (cell, cell+layer) of each continuation, one
\ entry per call site, written to the stream fc-link-chunk at a time.
variable fc-nlinks variable fc-link-buf variable fc-nbuf
: fc-put-links ( -- )
  fc-nbuf @ if
    fc-nlinks @ fc-nbuf @ - 64 * fc-links + fc-link-buf @ fc-nbuf @ 8 * cc-put 0 fc-nbuf !
  then ;
: fc-link-const ( cell -- addr )
  fc-nlinks @ fc-max-links = if -8 throw then
  fc-link-buf @ fc-nbuf @ 8 * + >r dup 4 r@ cc-numeric fc-l + 4 r> 4 + cc-numeric
  fc-nlinks @ 64 * fc-links + 1 fc-nlinks +! 1 fc-nbuf +!
  fc-nbuf @ fc-link-chunk = if fc-put-links then ;
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
variable fc-rl variable fc-f0 variable fc-f1 variable fc-psh
: fc-row+ ( dl dh sl sh -- )
  fc-nrow @ 4 * cells fc-prow + >r r@ 3 cells + ! r@ 2 cells + ! r@ cell+ ! r> ! 1 fc-nrow +! ;
: fc-4@ ( addr -- a b c d ) >r r@ @ r@ cell+ @ r@ 2 cells + @ r> 3 cells + @ ;
\ Rows whose endpoint fields f0, f1 get IDX+16k (and its copy) at bit shift.
: fc-patched ( f0 f1 shift -- )
  fc-psh ! fc-f1 ! fc-f0 !
  \ ceil(2n/7) patch layers for n <= 7 rows
  fc-nrow @ dup 0> 1 and swap 3 > 1 and + 0 ?do cc-layer i cells fc-pl + ! loop cc-layer drop
  cc-layer fc-rl !
  fc-nrow @ 0 ?do i 4 * cells fc-prow + fc-4@ fc-rl @ cc-row i cells fc-pslot + ! loop
  fc-nrow @ 0 ?do
    2 0 do
      8 fc-rl @ cc-layer-cell j cells fc-pslot + @ i if fc-f1 else fc-f0 then @ cc-field fc-psh @ +
      fc-idx j 16 * + i 8 * + cc-copy j 2* i + 6 > 1 and cells fc-pl + @ cc-row drop
    loop
  loop ;
create fc-popped 8 cells allot create fc-srcs 8 cells allot variable fc-nsrc
variable fc-mbase variable fc-mptr variable fc-mn variable fc-mw2
: fc-popped@ ( i -- r ) cells fc-popped + @ ;
: fc-shift ( base -- shift ) fc-rstk = if 7 else 6 then ;
: fc-mem-pop ( base pointer n width -- )
  fc-mw2 ! fc-mn ! fc-mptr ! fc-mbase !
  fc-mn @ 0 ?do fc-reg-for-pop i cells fc-popped + ! loop
  fc-mn @ 0 ?do i fc-mn @ - i cells fc-offs + ! loop fc-mn @ fc-noff !
  fc-mptr @ fc-mn @ negate fc-adjust
  0 fc-nrow ! fc-mn @ 0 ?do
    i fc-popped@ dup fc-mw2 @ + fc-mbase @ i fc-mbase @ fc-shift lshift + dup fc-mw2 @ + fc-row+
  loop 2 3 fc-mbase @ fc-shift fc-patched ;
: fc-push-group ( -- )
  fc-nsrc @ 0 ?do i i cells fc-offs + ! loop fc-nsrc @ fc-noff !
  fc-mptr @ fc-nsrc @ fc-adjust
  0 fc-nrow ! fc-nsrc @ 0 ?do
    fc-mbase @ i fc-mbase @ fc-shift lshift + dup fc-mw2 @ + i cells fc-srcs + @ dup fc-mw2 @ + fc-row+
  loop 0 1 fc-mbase @ fc-shift fc-patched ;
\ The first source that repeats an earlier one (DUP shares a register; one
\ layer may not read it twice), else the count.
: fc-dup-at ( -- k )
  fc-nsrc @ 1 ?do i cells fc-srcs + @ fc-srcs i fc-in? if i unloop exit then loop fc-nsrc @ ;
create fc-rest 8 cells allot variable fc-nrest
: fc-mem-push ( base pointer width -- )
  fc-mw2 ! fc-mptr ! fc-mbase !
  begin fc-dup-at dup fc-nsrc @ < while
    fc-srcs over cells + fc-rest fc-nsrc @ 3 pick - cells cmove fc-nsrc @ over - fc-nrest ! fc-nsrc !
    fc-push-group fc-rest fc-srcs fc-nrest @ cells cmove fc-nrest @ fc-nsrc !
  repeat drop fc-push-group ;
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
: fc-branch ( flag -- zero yes ) fc-nonzero 1 cc-decide fc-end dup cc-branch-step + ;
: fc-call ( entry -- )
  fc-spill cc-new-cell >r r@ fc-link-const fc-src1 fc-rstk fc-rp 64 fc-mem-push
  cc-jump fc-end r> fc-begin-block drop ;
variable fc-v0 variable fc-v1
: fc-call-indirect ( xt cont|-1 -- cont )
  fc-spill dup -1 = if drop cc-new-cell then >r
  r@ fc-link-const fc-src1 fc-rstk fc-rp 64 fc-mem-push
  cc-layer fc-v0 ! cc-layer fc-v1 ! cc-layer drop
  fc-a cc-branch-bit - fc-ex @ 7 2 cc-field cc-branch-bit + 2 pick cc-branch-bit + cc-copy fc-v0 @ cc-row drop
  fc-a cc-branch-bit - fc-ex @ 7 3 cc-field cc-branch-bit + rot cc-branch-bit + cc-copy fc-v1 @ cc-row drop
  fc-ex @ cc-jump fc-end r> ;
: fc-push-frame ( thrown -- )
  fc-link-const fc-sp fc-srcs ! fc-handler fc-srcs cell+ ! fc-srcs 2 cells + ! 3 fc-nsrc !
  fc-rstk fc-rp 64 fc-mem-push 64 fc-handler fc-rp cc-copy fc-rows1 ;
: fc-restore ( dst src -- ) \ pointer from the first copy, by the identity table
  >r >r 0 fc-off@ 7 64 r> 0 cc-item r> 8 0 cc-seg ;
: fc-build-thrower ( -- entry )
  0 fc-n ! -1 cc-seq 64 fc-rp fc-handler cc-copy fc-rows1 cc-entry
  fc-rstk fc-rp 3 64 fc-mem-pop 0 fc-npin !
  cc-lookups-begin fc-sp 0 fc-popped@ fc-restore fc-handler 1 fc-popped@ fc-restore cc-lookups
  64 fc-tramp @ 7 2 cc-field 2 fc-popped@ cc-copy fc-rows1
  cc-layer drop fc-tramp @ cc-jump fc-end ;
: fc-throw ( -- )
  fc-pop fc-spill 32 fc-code 2 pick cc-copy fc-rows1
  fc-branch cc-new-record fc-thrower @ swap cc-next! cc-flush fc-begin-block drop ;
: fc-catch ( -- )
  fc-pop >r fc-spill cc-new-cell cc-new-cell over fc-push-frame
  r> -1 fc-call-indirect fc-begin-block drop
  fc-rstk fc-rp 3 64 fc-mem-pop 0 fc-npin !
  cc-lookups-begin fc-handler 1 fc-popped@ fc-restore cc-lookups
  0 fc-n ! 0 fc-reg dup fc-push 32 swap rot fc-const cc-copy fc-rows1 fc-spill
  dup cc-jump fc-end
  swap fc-begin-block drop fc-reg dup >r 32 swap fc-code cc-copy fc-rows1 0 fc-n ! r> fc-push fc-spill
  dup cc-jump fc-end fc-begin-block drop ;
variable fc-ret-p variable fc-ret-l
: fc-ret ( -- )
  fc-spill -1 fc-offs ! 1 fc-noff ! fc-rp -1 fc-adjust
  cc-layer fc-ret-p ! cc-layer drop cc-layer fc-ret-l !
  fc-tramp @ 7 2 cc-field dup 64 + fc-rstk dup 64 + fc-ret-l @ cc-row >r
  8 fc-ret-l @ cc-layer-cell r@ 2 cc-field 7 + fc-idx cc-copy fc-ret-p @ cc-row drop
  8 fc-ret-l @ cc-layer-cell r> 3 cc-field 7 + fc-idx 8 + cc-copy fc-ret-p @ cc-row drop
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
\ The access row (in layer, slot) gets the cell index a[2:] at bit 6 of its
\ endpoint fields f, f+1 (patches in l0, l1); a byte access also the bit
\ offsets of the byte from BP in the low six bits.
variable fc-cmode variable fc-ar variable fc-as variable fc-af variable fc-al0 variable fc-al1
variable fc-apl variable fc-afld
: fc-access-patch ( k -- ) \ endpoint field f+k, patch layer l0 or l1
  dup if fc-al1 else fc-al0 then @ fc-apl !
  fc-ar @ cc-layer-cell fc-as @ fc-af @ 3 pick + cc-field fc-afld !
  fc-cmode @ 2 and if 6 fc-afld @ fc-bp 3 pick 6 * + cc-copy fc-apl @ cc-row drop then
  drop fc-mw fc-afld @ 6 + fc-ca @ 2 + cc-copy fc-apl @ cc-row drop ;
: fc-access ( layer slot f l0 l1 -- )
  fc-al1 ! fc-al0 ! fc-af ! fc-as ! fc-ar ! 0 fc-access-patch 1 fc-access-patch ;
: fc-width ( -- n ) fc-cmode @ 2 and if 8 else 32 then ;
variable fc-r1l0 variable fc-r1l1 variable fc-r1r
\ mode 0: load a cell into fc-cres, 1: store fc-cv, 2 and 3: the same for a
\ byte. Loads run before the decision, stores in the ok cell after it.
: fc-check ( a mode -- )
  fc-cmode ! fc-ca !
  cc-layer fc-cl0 ! cc-layer fc-cl1 ! cc-layer drop cc-layer fc-cr !
  cc-t-or8 @ 1 1 fc-z fc-chk-read fc-ca @ fc-mw 2 + + 8 0 fc-chk-seg
  fc-t-or8b @ 1 1 fc-z 1+ fc-chk-read fc-ca @ fc-mw 10 + + fc-a fc-mw 10 + - 0 fc-chk-seg
  fc-cmode @ 2 and if fc-t-bytepos @ 4 12 fc-bp fc-chk-read fc-ca @ 2 0 fc-chk-seg then
  fc-cl0 @ fc-r1l0 ! fc-cl1 @ fc-r1l1 ! fc-cr @ fc-r1r !
  cc-layer fc-cl0 ! cc-layer fc-cl1 ! cc-layer drop cc-layer fc-cr !
  fc-t-fault @ 6 34 fc-flt fc-chk-read fc-z 2 0 fc-chk-seg
  fc-cmode @ 2 and 0= if fc-ca @ 2 2 fc-chk-seg then
  1 cc-group fc-cg ! cc-layer >r cc-layer drop cc-layer fc-cx ! fc-cg @ fc-cx @ cc-next!
  1 fc-cx @ cc-layer-cell 7 2 cc-field cc-branch-bit + fc-flt cc-copy r@ cc-row drop
  1 fc-cx @ cc-layer-cell 7 3 cc-field cc-branch-bit + fc-flt 1+ cc-copy r> cc-row drop
  fc-cg @ cc-seq
  fc-cmode @ 1 and if
    cc-layer dup fc-ar ! fc-mem dup fc-width + fc-cv @ dup fc-width + fc-ar @ cc-row 0
  else
    fc-cmode @ 2 and if fc-cr @ else fc-r1r @ then dup fc-ar !
    fc-cres @ dup fc-width + fc-mem dup fc-width + fc-ar @ cc-row 2
    fc-cmode @ 2 and if 24 fc-cres @ 8 + fc-zero cc-copy fc-ar @ cc-row drop then
  then
  fc-cmode @ 2 and if fc-cl0 @ fc-cl1 @ else fc-r1l0 @ fc-r1l1 @ then fc-access
  fc-cg @ cc-branch-step + cc-new-record >r 32 fc-code fc-flt 2 + cc-copy r@ cc-row drop
  fc-thrower @ r> cc-next! -1 fc-live ! ;

\ --- straight-line scheduler (model: Sched) ---------------------------------
64 constant fc-ring 48 constant fc-window
create fc-sl fc-ring cells allot variable fc-stabs
variable fc-slen variable fc-slow
: fc-sinit ( first|-1 -- ) cc-seq 0 fc-slen ! 0 fc-slow ! ;
: fc-sbegin ( -- ) fc-slen @ fc-window - 0 max fc-slow ! ;
: fc-tabs ( t -- addr ) fc-ring 1- and 8 * cells fc-stabs @ + ;
: fc-at ( t -- layer )
  dup fc-slow @ - fc-ring < 0= if -8 throw then
  begin dup fc-slen @ < 0= while
    cc-layer fc-slen @ fc-ring 1- and cells fc-sl + ! 0 fc-slen @ fc-tabs ! 1 fc-slen +!
  repeat fc-ring 1- and cells fc-sl + @ ;
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
  fc-nseg @ dup 2 lshift + cells fc-segs + >r r@ 4 cells + ! r@ 3 cells + ! r@ 2 cells + ! r@ cell+ ! r> !
  1 fc-nseg +! ;
: fc-pp+ ( t slot f x n off -- ) fc-npp @ dup 2* + 2* cells fc-pp + 6 0 do tuck 5 i - cells + ! loop drop 1 fc-npp +! ;
: fc-slookup ( table s width dst preset -- t )
  >r fc-ldst ! fc-lw ! fc-ls ! fc-ltab ! fc-sbegin -2 fc-latest ! 0 fc-npp !
  fc-nseg @ 0 ?do
    i dup 2 lshift + cells fc-segs + fc-sga !
    2 0 do
      0 0 fc-sga @ i cells + @ dup fc-sga @ 2 cells + @ + fc-sga @ 4 cells + @ 0 fc-place
      over fc-latest @ max fc-latest !
      i 2 + fc-sga @ i cells + @ fc-sga @ 2 cells + @ fc-sga @ 3 cells + @ fc-pp+
    loop
  loop
  fc-ltab @ r> fc-ls @ lshift + fc-ldst @ dup fc-lw @ + rot dup fc-lw @ +
  fc-latest @ 2 + fc-ltab @ fc-place ( t slot )
  fc-npp @ 0 ?do
    i dup 2* + 2* cells fc-pp + fc-sga !
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
  -1 fc-sinit ['] fc-mul4-entry 12 4 cc-table fc-m4 !
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
variable fc-w variable fc-lo variable fc-tlo variable fc-t0 variable fc-t1 variable fc-qr variable fc-tqk
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
  256 256 fc-scratch fc-w ! 32 64 fc-scratch fc-lo ! 0 fc-tlo ! 0 fc-t0 ! 0 fc-t1 !
  4 0 do
    0 fc-sub@ fc-lo @ i 4 * + i i if fc-lo @ i 4 * + else 0 then fc-tlo @ i 0= 1 and fc-step fc-tlo !
    1 fc-sub@ fc-w @ 80 + i 4 * + i 4 + i if fc-w @ 80 + i 4 * + else 0 then fc-t0 @ 0 fc-step fc-t0 !
    2 fc-sub@ fc-w @ 208 + i 4 * + i 4 + i if fc-w @ 208 + i 4 * + else 0 then fc-t1 @ i 0= 1 and fc-step fc-t1 !
  loop
  2 64 fc-scratch fc-qr !
  fc-lo @ 16 + dup 1+ 1 0 fc-tlo @ fc-seg+ fc-w @ 96 + dup 1+ 1 1 fc-t0 @ fc-seg+
  fc-w @ 224 + dup 1+ 1 2 fc-t1 @ fc-seg+ fc-qsel @ 2 2 fc-qr @ 0 fc-slookup fc-tqk !
  16 fc-w @ 64 + fc-lo @ fc-tlo @ fc-scopy 16 fc-w @ 192 + fc-lo @ fc-tlo @ fc-scopy max
  31 fc-w @ 1+ fc-rem @ fc-tr @ fc-scopy max 1 fc-w @ fc-absa @ fc-k @ + fc-ta @ fc-scopy max
  31 fc-w @ 129 + fc-rem @ fc-tr @ fc-scopy max 1 fc-w @ 128 + fc-absa @ fc-k @ + fc-ta @ fc-scopy max
  32 64 fc-scratch >r
  fc-qr @ dup 1+ 1 6 fc-tqk @ fc-seg+ fc-lo @ 16 + dup 1+ 1 7 4 roll fc-tlo @ max fc-seg+
  fc-w @ 0 32 r@ 0 fc-slookup fc-tr ! r> fc-rem !
  1 fc-q @ fc-k @ + fc-qr @ fc-tqk @ fc-scopy fc-tq @ max fc-tq ! ;
: fc-build-div ( -- entry exit )
  -1 cc-seq cc-layer drop cc-entry fc-mb fc-nonzero 1 cc-decide fc-end
  dup cc-new-record >r 32 fc-code -10 fc-const cc-copy r@ cc-row drop fc-thrower @ r> cc-next!
  cc-branch-step + fc-sinit
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
  64 swap 7 2 cc-field fc-hcont @ fc-link-const cc-copy cc-layer dup fc-hl ! cc-row drop
  ( b a entry ) >r 32 fc-ma rot cc-copy fc-row-or-new 32 fc-mb rot cc-copy fc-row-or-new
  r> cc-jump cc-flush fc-hcont @ cc-seq ;
: fc-result1 ( src -- ) fc-reg dup fc-push 32 swap rot cc-copy fc-rows1 ;
variable fc-s1 variable fc-s2 variable fc-r1
: fc-result2 ( src1 src2 -- )
  fc-s2 ! fc-s1 ! fc-reg dup fc-push fc-r1 ! fc-reg dup fc-push
  32 fc-r1 @ fc-s1 @ cc-copy cc-layer dup >r cc-row drop 32 swap fc-s2 @ cc-copy r> cc-row drop ;

\ --- primitives ---------------------------------------------------------------
\ The literal compiled by the previous word (for N PICK, N ROLL).
variable fc-ll variable fc-llr variable fc-llv variable fc-plit variable fc-plr variable fc-plv
: fc-literal ( value -- )
  dup fc-llv ! fc-reg dup fc-llr ! -1 fc-ll ! dup fc-push 32 swap rot fc-const cc-copy fc-rows1 ;
: fc-or-zero ( out r -- ) \ out = (r == 0) as 32 bits
  cc-lookups-begin fc-z swap 0 32 cc-or-chunks cc-lookups
  >r cc-lookups-begin fc-t-zero32 @ 6 32 r> 0 cc-item fc-z 4 0 cc-seg cc-lookups ;
variable fc-ba variable fc-bb variable fc-br
\ op: 0 + 1 - 2 and 3 or 4 xor 5 = 6 < 7 u< 8 lshift 9 rshift
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
  else dup 5 = if drop
    cc-t-xor @ fc-xr fc-ba @ fc-bb @ cc-logic fc-br @ fc-xr fc-or-zero
  else dup 6 = if drop
    cc-t-sub @ fc-tmp fc-ba @ fc-bb @ 1 cc-adder
    cc-lookups-begin fc-t-lt32 @ 6 32 fc-br @ 0 cc-item
    fc-tmp 32 + 1 0 cc-seg fc-ba @ 31 + 1 1 cc-seg fc-bb @ 31 + 1 2 cc-seg cc-lookups
  else dup 7 = if drop
    cc-t-sub @ fc-tmp fc-ba @ fc-bb @ 1 cc-adder
    cc-lookups-begin fc-t-ult32 @ 6 32 fc-br @ 0 cc-item fc-tmp 32 + 1 0 cc-seg cc-lookups
  else 8 = if fc-br @ fc-ba @ fc-bb @ fc-sw fc-zero fc-su cc-shift-left
  else fc-br @ fc-ba @ fc-bb @ fc-sw fc-zero 0 cc-shift-right
  then then then then then then fc-br @ fc-push ;
: fc-r-at ( offset -- ) \ R@ and I: -1, J: -3
  fc-reg >r fc-offs ! 1 fc-noff ! fc-rp 0 fc-adjust
  0 fc-nrow ! r@ dup 32 + fc-rstk dup 32 + fc-row+ 2 3 7 fc-patched r> fc-push ;
: fc-pop-pinned ( -- a r ) fc-pop dup fc-pin ! 1 fc-npin ! fc-reg 0 fc-npin ! ;
\ CELLS and 2*: a shift by copying, one layer.
variable fc-sk
: fc-shift-copy ( k -- )
  fc-sk ! fc-pop-pinned cc-layer >r
  32 fc-sk @ - over fc-sk @ + 3 pick cc-copy r@ cc-row drop
  fc-sk @ over fc-zero cc-copy r> cc-row drop fc-push drop ;
\ 1+ 1- CELL+: the adder with a constant.
: fc-inc ( table k carry -- )
  >r >r >r fc-pop-pinned swap r> fc-tmp rot r> fc-const r> cc-adder
  dup 32 swap fc-tmp cc-copy fc-rows1 fc-push ;
: fc-read-key ( -- ) \ a cleared byte, then stdin: at the end of input it stays 0
  fc-reg 8 fc-key fc-zero cc-copy fc-rows1 fc-key dup 8 + cc-stdin dup fc-rows1 cc-layer drop
  cc-lookups-begin fc-t-rev8 @ 4 8 3 pick 0 cc-item fc-key 8 0 cc-seg cc-lookups
  24 over 8 + fc-zero cc-copy fc-rows1 fc-push ;

\ --- source text and words ------------------------------------------------
variable fc-text variable fc-tlen variable fc-pos variable fc-text-size 8192 fc-text-size !
create fc-tok 256 allot variable fc-tl
: fc-reset ( -- ) fc-text @ 0= if fc-text-size @ allocate throw fc-text ! then 0 fc-tlen ! ;
: fc-append ( addr u -- )
  fc-text @ 0= if fc-reset then
  dup 1+ fc-tlen @ + fc-text-size @ > if -8 throw then
  tuck fc-text @ fc-tlen @ + swap cmove fc-tlen +! 10 fc-text @ fc-tlen @ + c! 1 fc-tlen +! ;
: fc| ( "line" -- ) source >in @ /string fc-append source nip >in ! ;
: fc-ch ( -- c ) fc-text @ fc-pos @ + c@ ;
: fc-more? ( -- f ) fc-pos @ fc-tlen @ < ;
\ Next word into fc-tok, ASCII letters folded to lower case; a word \ ends
\ the line. Words are runs of bytes above 32. False at the end of the text.
: fc-word-raw ( -- f ) \ the next word, without comment handling ([CHAR] \)
  begin fc-more? if fc-ch 33 < else 0 then while 1 fc-pos +! repeat
  fc-more? 0= if 0 exit then
  0 fc-tl !
  begin fc-more? if fc-ch 32 > else 0 then while
    fc-tl @ 255 = if -8 throw then
    fc-ch dup [char] A [char] Z 1+ over - >r - r> u< if 32 + then fc-tok fc-tl @ + c! 1 fc-tl +! 1 fc-pos +!
  repeat -1 ;
: fc-next ( -- f )
  begin fc-word-raw while
    fc-tl @ 1 = fc-tok c@ [char] \ = and 0= if -1 exit then
    begin fc-more? if fc-ch 10 <> else 0 then while 1 fc-pos +! repeat
  repeat 0 ;
: fc-next! ( -- ) fc-next 0= if -16 throw then ;
: fc-is? ( addr u -- f ) \ length and first byte first: most words differ there
  dup fc-tl @ <> if 2drop 0 exit then over c@ fc-tok c@ <> if 2drop 0 exit then
  fc-tok fc-tl @ compare 0= ;
: fc-squote? ( -- f ) \ the word S"
  fc-tl @ 2 = fc-tok c@ [char] s = and fc-tok 1+ c@ [char] " = and ;
\ The first byte of the word as written (not folded).
: fc-raw ( -- c ) fc-text @ fc-pos @ fc-tl @ - + c@ ;
\ S" text": one delimiter, then the bytes up to the closing quote.
: fc-string-token ( -- addr u )
  fc-pos @ 1+ fc-tlen @ min fc-pos ! fc-pos @
  begin fc-more? if fc-ch [char] " <> else 0 then while 1 fc-pos +! repeat
  fc-more? 0= if -16 throw then
  fc-text @ over + fc-pos @ rot - 1 fc-pos +! ;
\ A decimal literal, optionally negative, modulo 2^32.
: fc-number ( -- n true | false )
  fc-tok fc-tl @ over c@ [char] - = if 1 /string -1 else 1 then >r
  dup 0= if 2drop r> drop 0 exit then
  0 -rot over + swap do
    i c@ [char] 0 - dup 10 u< 0= if 2drop unloop r> drop 0 exit then swap 10 * +
  loop r> * -1 ;
variable fc-names-size 4096 fc-names-size ! variable fc-max-words 256 fc-max-words !
variable fc-names variable fc-names-used
variable fc-wt variable fc-nwords variable fc-wbk   \ entries: offset len kind value next
: fc-wt@ ( i -- addr ) dup 2 lshift + cells fc-wt @ + ;
: fc-whash ( -- addr )
  0 fc-tl @ 0 ?do dup 5 lshift swap - fc-tok i + c@ + loop fc-nbuckets @ 1- and cells fc-wbk @ + ;
: fc-define ( kind value -- ) \ the newest definition heads its chain
  fc-nwords @ fc-max-words @ = fc-names-used @ fc-tl @ + fc-names-size @ > or if -8 throw then
  fc-nwords @ fc-wt@ >r r@ 3 cells + ! r@ 2 cells + !
  fc-names-used @ r@ ! fc-tl @ r@ cell+ ! fc-whash dup @ r> 4 cells + ! fc-nwords @ 1+ swap !
  fc-tok fc-names @ fc-names-used @ + fc-tl @ cmove fc-tl @ fc-names-used +! 1 fc-nwords +! ;
: fc-find ( -- entry|0 )
  fc-whash @ begin ?dup while
    1- fc-wt@ dup @ fc-names @ + over cell+ @ fc-tok fc-tl @ compare 0= if exit then 4 cells + @
  repeat 0 ;

\ --- compiler -------------------------------------------------------------
variable fc-here variable fc-word variable fc-uses
\ Control entries: kind (1 if, 2 else, 3 begin, 4 while, 5 do), cell, and for
\ a loop its leave cell (0: none yet).
create fc-ctl 96 cells allot variable fc-nctl variable fc-cleave
: fc-ctl@ ( i -- addr ) dup 2* + cells fc-ctl + ;
: fc-ctl+ ( kind cell -- )
  fc-nctl @ 32 = if -8 throw then fc-nctl @ fc-ctl@ >r r@ cell+ ! r@ ! 0 r> 2 cells + ! 1 fc-nctl +! ;
: fc-ctl- ( -- kind cell )
  fc-nctl @ 0= if -22 throw then -1 fc-nctl +! fc-nctl @ fc-ctl@ >r r@ @ r@ cell+ @ r> 2 cells + @ fc-cleave ! ;
: fc-do-entry ( -- addr ) \ the innermost loop
  fc-nctl @ 0 ?do fc-nctl @ 1- i - fc-ctl@ dup @ 5 = if unloop exit then drop loop -22 throw ;
\ The leave cell (14.5): of the entry FC-CTL- took (0: none), of the top
\ entry, of the loop entry (a new cell if it has none yet).
: fc-ctl-leave ( -- cell ) fc-cleave @ ;
: fc-ctl-leave! ( cell -- ) fc-nctl @ 1- fc-ctl@ 2 cells + ! ;
: fc-loop-leave ( entry -- cell ) dup 2 cells + @ 0= if cc-new-cell over 2 cells + ! then 2 cells + @ ;
\ Data memory: HERE is cell aligned for each definition and string.
: fc-align ( -- ) fc-here @ 3 + -4 and fc-here ! ;
: fc-check-here ( -- ) fc-here @ 4 fc-mw lshift > if -8 throw then ;
: fc-define-data ( size -- ) fc-align 0 fc-here @ fc-define fc-here +! fc-check-here ;
variable fc-sat
: fc-store-string ( addr u -- at )
  fc-align fc-here @ fc-sat ! dup fc-here +! 0 ?do
    dup i + c@ cc-rev + c@ fc-eight c!
    fc-sat @ i + dup 2 rshift 64 * swap 3 and 8 * + fc-mem + fc-eight 1 cc-put
  loop drop fc-check-here fc-sat @ ;
\ Values known at compile time at the top level.
create fc-ct 64 cells allot variable fc-nct
: fc-ct+ ( v -- ) fc-nct @ 64 = if -8 throw then fc-ct fc-nct @ cells + ! 1 fc-nct +! ;
: fc-ct- ( -- v ) fc-nct @ 0= if -22 throw then -1 fc-nct +! fc-ct fc-nct @ cells + @ ;
: fc-ct2 ( -- a b ) fc-ct- fc-ct- swap ;
\ Other top-level code runs before MAIN: parts, each a word of its own.
create fc-inits 64 cells allot variable fc-ninit variable fc-init-open
: fc-init ( -- )
  fc-size 8 fc-cellb 4096 cc-machine fc-first @ cc-builder fc-tables
  fc-ck @ 0= if
    fc-max-consts @ 4 * cells allocate throw fc-ck ! fc-ring 8 * cells allocate throw fc-stabs !
    fc-nbuckets @ cells allocate throw fc-cbk !
  then
  fc-cbk @ fc-nbuckets @ cells 0 fill
  0 fc-nconsts ! 0 fc-n ! 0 fc-npin ! 0 fc-live ! 0 fc-nseg !
  0 fc-nctl ! fc-data-start fc-here ! 0 fc-word !
  0 fc-nct ! 0 fc-ninit ! 0 fc-init-open ! 0 fc-ll ! 0 fc-plit !
  cc-lone fc-cellb over cc-next! cc-layer-cell fc-tramp ! cc-flush
  cc-lone 0 over cc-next! cc-layer-cell fc-ex ! cc-flush
  0 fc-nlinks ! 0 fc-nbuf ! fc-link-buf @ 0= if fc-link-chunk 8 * allocate throw fc-link-buf ! then
  fc-scr0 fc-scr ! fc-build-thrower fc-thrower ! ;
: fc-scan-uses ( -- ) \ helpers the generators need (1: *  2: / MOD /MOD); and KERNEL-LAYOUT
  0 fc-uses ! 0 fc-kernel ! 0 fc-pos ! begin fc-next while
    s" kernel-layout" fc-is? if -1 fc-kernel ! then
    fc-find ?dup if 2 cells + @ 2 rshift fc-uses @ or fc-uses ! then
  repeat 0 fc-pos ! ;
: fc-primitive ( -- ) \ the words that are not generators yet
  s" decimal" fc-is? if exit then
  -13 throw ;
\ N PICK and N ROLL: N is the literal just compiled, on top of the cache.
: fc-const-shift ( right? k -- )
  dup 0= if 2drop fc-pop fc-push exit then
  fc-sk ! fc-pop-pinned cc-layer >r rot if
    32 fc-sk @ - over 3 pick fc-sk @ + cc-copy r@ cc-row drop
    fc-sk @ over 32 + fc-sk @ - fc-zero cc-copy r> cc-row drop
  else
    32 fc-sk @ - over fc-sk @ + 3 pick cc-copy r@ cc-row drop
    fc-sk @ over fc-zero cc-copy r> cc-row drop
  then fc-push drop ;
\ A literal power of two before * (the generator of *), or a literal shift
\ below 32 (of LSHIFT, RSHIFT): a shift by copying, one layer.
: fc-lit? ( -- f ) \ the top of the cache is the literal just compiled
  fc-plit @ 0= fc-n @ 0= or if 0 exit then fc-n @ 1- fc-c@ fc-plr @ = ;
: fc-mul-lit? ( -- f )
  fc-lit? 0= if 0 exit then fc-plv @
  dup 0= over dup 1- and or if drop 0 exit then
  0 swap begin dup 1 u> while 1 rshift swap 1+ swap repeat drop
  fc-pop1 drop 0 swap fc-const-shift -1 ;
: fc-shift-lit? ( right? -- f )
  fc-lit? 0= if drop 0 exit then fc-plv @ dup 32 u< 0= if 2drop 0 exit then
  fc-pop1 drop fc-const-shift -1 ;
: fc-pick-roll ( roll? -- )
  fc-plit @ 0= fc-n @ 0= or if -13 throw then fc-n @ 1- fc-c@ fc-plr @ <> if -13 throw then
  fc-pop1 drop fc-plv @ dup 1+ fc-need fc-n @ 1- swap - ( index )
  swap if
    dup fc-c@ >r fc-cache over cells + dup cell+ swap fc-n @ 3 pick - 1- cells cmove drop -1 fc-n +! r> fc-push
  else fc-c@ fc-push then ;
\ SPACE! and SPACEC! ( x lo hi -- ): bits [lo,hi) of the space get the low
\ 32 (8) bits of x; the destination of the copy is patched two layers ahead.
variable fc-stx variable fc-stlo variable fc-sthi variable fc-stp variable fc-strow
: fc-space-store ( n -- )
  3 fc-need fc-pop1 fc-sthi ! fc-pop1 fc-stlo ! fc-pop1 fc-stx !
  fc-sthi @ fc-stlo @ = if
    fc-stx @ fc-pin ! fc-stlo @ fc-pin cell+ ! 2 fc-npin ! fc-reg fc-sthi ! 0 fc-npin !
    32 fc-sthi @ fc-stlo @ cc-copy fc-rows1
  then
  cc-layer fc-stp ! cc-layer drop cc-layer fc-strow !
  >r 0 0 fc-stx @ dup r> + fc-strow @ cc-row
  32 fc-strow @ cc-layer-cell 2 pick 0 cc-field fc-stlo @ cc-copy fc-stp @ cc-row drop
  32 fc-strow @ cc-layer-cell rot 1 cc-field fc-sthi @ cc-copy fc-stp @ cc-row drop ;
: fc-control-token ( -- ) \ inside a definition: words (a generator is executed), literals
  fc-find ?dup if
    dup 3 cells + @ swap 2 cells + @ dup 2 and if drop execute exit then if fc-call else fc-literal then exit
  then fc-number if fc-literal exit then
  fc-primitive ;
: fc-word-token ( -- ) \ inside a definition
  s" ;" fc-is? if fc-nctl @ if -22 throw then fc-ret 0 fc-word ! exit then
  s" [char]" fc-is? if fc-word-raw 0= if -16 throw then fc-raw fc-literal exit then
  fc-squote? if fc-string-token dup >r fc-store-string fc-literal r> fc-literal exit then
  fc-control-token ;
: fc-close-init ( -- )
  fc-nct @ if -22 throw then
  fc-init-open @ if fc-ret 0 fc-init-open ! 0 fc-word ! then ;
: fc-open-init ( -- ) \ start a part if needed, then the known values as literals
  fc-init-open @ 0= if
    fc-ninit @ 64 = if -8 throw then 0 cc-group dup fc-inits fc-ninit @ cells + ! 1 fc-ninit +!
    -1 fc-init-open ! -1 fc-word ! 0 fc-live ! 0 fc-n ! fc-begin-block drop
  then
  fc-nct @ 0 ?do fc-ct i cells + @ fc-literal loop 0 fc-nct ! ;

\ --- generators (14.3) ----------------------------------------------------
\ A generator is a dictionary entry of kind 2 (+ 4 * the helpers it needs:
\ 1 multiplication, 2 division) whose value is the xt of a word of the
\ compiler: found in the source, it is executed and writes the copycode.
\ Generators are registered by the word in FC-GENS (primitives.fth) when
\ the dictionary is cleared, before the source is read; the source may
\ redefine their names. The words below are the state of the compiler a
\ generator uses (space/language/doc/generators.md).
variable fc-gens
: fc-generator ( addr u xt uses -- ) \ the entry: name addr u, xt, helpers
  2 lshift 2 or swap 2swap dup fc-tl ! fc-tok swap cmove fc-define ;
: fc-words ( -- ) \ the dictionary: cleared, then the generators
  fc-wt @ 0= if
    fc-max-words @ 5 * cells allocate throw fc-wt ! fc-names-size @ allocate throw fc-names !
    fc-nbuckets @ cells allocate throw fc-wbk !
  then
  fc-wbk @ fc-nbuckets @ cells 0 fill 0 fc-nwords ! 0 fc-names-used !
  fc-gens @ ?dup if execute then ;
: fc-depth ( -- n ) fc-n @ ;           \ items in the stack cache
: fc-ctl-depth ( -- n ) fc-nctl @ ;    \ entries of the control stack
: fc-known ( -- n ) fc-nct @ ;         \ values known at compile time
\ Code at the top level runs before MAIN: open its part (the known values
\ become literals); inside a definition nothing is needed.
: fc-code ( -- ) fc-word @ fc-init-open @ 0= and 0= if fc-open-init 0 fc-plit ! then ;
\ True: n values are known (the generator folds them with FC-CT- FC-CT+);
\ else FC-CODE and false (the generator writes code).
: fc-fold? ( n -- f ) fc-known > if fc-code 0 else -1 then ;

\ Definitions; constant expressions are evaluated here, other code runs before
\ MAIN as parts of the top-level code, in order.
: fc-top-token ( -- )
  s" :" fc-is? if
    fc-close-init fc-next! 0 cc-group 1 over fc-define fc-nwords @ 1- fc-wt@ fc-word !
    0 fc-live ! 0 fc-n ! fc-begin-block drop exit then
  s" variable" fc-is? if fc-next! 4 fc-define-data exit then
  s" create" fc-is? if fc-next! 0 fc-define-data exit then
  s" decimal" fc-is? s" kernel-layout" fc-is? or if exit then
  s" allot" fc-is? if fc-ct- fc-here +! fc-check-here exit then
  s" constant" fc-is? if fc-ct- fc-next! 0 swap fc-define exit then
  fc-number if fc-ct+ exit then
  fc-find ?dup if
    dup 3 cells + @ swap 2 cells + @ dup 0= if drop fc-ct+ exit then 2 and if execute exit then drop
  then
  fc-open-init 0 fc-plit ! fc-word-token fc-word @ 0= if -22 throw then ;
: fc-compile ( -- )
  fc-words fc-scan-uses fc-kernel @ fc-layout fc-init
  fc-uses @ 1 and if fc-build-mul fc-mul-exit ! fc-mul-entry ! then
  fc-uses @ 2 and if fc-build-div fc-div-exit ! fc-div-entry ! then
  begin fc-next while
    fc-ll @ fc-plit ! fc-llr @ fc-plr ! fc-llv @ fc-plv ! 0 fc-ll !
    s" (" fc-is? if begin fc-next! s" )" fc-is? until
    else fc-word @ fc-init-open @ 0= and if fc-word-token else fc-top-token then then
  repeat
  fc-word @ fc-init-open @ 0= and if -22 throw then fc-close-init
  s" main" fc-tok swap dup fc-tl ! cmove fc-find dup 0= if -16 throw then >r
  0 fc-live ! 0 fc-n ! 0 cc-group fc-begin-block cc-new-cell
  dup fc-push-frame fc-ninit @ 0 ?do fc-inits i cells + @ fc-call loop
  r> 3 cells + @ fc-call fc-cellb fc-jump cc-flush
  cc-new-record fc-cellb swap cc-next! cc-flush
  fc-sp fc-zeros 8 cc-put fc-rp fc-zeros 8 cc-put fc-handler fc-zeros 8 cc-put
  fc-zero fc-zeros 16 cc-put fc-put-consts fc-put-links cc-finish ;
: fc-go ( -- ) fc-text @ 0= if fc-reset then fc-compile ;
