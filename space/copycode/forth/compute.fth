\ SPDX-License-Identifier: MIT
\ Computation by copies; control: copycode.vm1.compute. Requires backend.fth.
\ A lookup reads a table entry whose index bits are copied into both source
\ endpoints of the read row: lower-endpoint patches, upper-endpoint patches,
\ one gap layer, then the reads. Entry stride exceeds width, so both
\ endpoints share the index bits. Layers and rows are created in the same
\ order as the host model, so the streams are identical. Words keep their
\ state in variables and are not reentrant. THROW -8: capacity.
decimal
variable cc-t1 variable cc-t2 variable cc-t3 variable cc-t4 variable cc-t5
variable cc-lo variable cc-hi
variable cc-l0 variable cc-l1 variable cc-l2 variable cc-l3 variable cc-l4 variable cc-l5
: cc-work ( -- n ) cc-slots @ 1- ;
: cc-cell-bit ( -- n ) cc-cell-bits @ cc-bits 1- ;
: cc-link-slot ( -- n ) cc-slots @ 1- ;
\ Lookup items: table s width out preset nseg, then 4 segments (src n off).
18 constant cc-item-cells 16 constant cc-max-items
create cc-items cc-max-items cc-item-cells * cells allot
variable cc-nitems
: cc-item@ ( i -- addr ) dup 4 lshift swap 2* + cells cc-items + ;   \ 18 cells each
: cc-lookups-begin ( -- ) 0 cc-nitems ! ;
: cc-item ( table s width out preset -- )
  cc-nitems @ cc-max-items < 0= if -8 throw then
  cc-nitems @ cc-item@ cc-t1 !
  cc-t1 @ 4 cells + ! cc-t1 @ 3 cells + ! cc-t1 @ 2 cells + ! cc-t1 @ cell+ ! cc-t1 @ !
  0 cc-t1 @ 5 cells + ! 1 cc-nitems +! ;
: cc-seg ( src n off -- )
  cc-nitems @ 1- cc-item@ cc-t1 !
  cc-t1 @ 5 cells + @ 4 < 0= if -8 throw then
  cc-t1 @ 5 cells + @ dup 2* + 6 + cells cc-t1 @ + cc-t2 !
  cc-t2 @ 2 cells + ! cc-t2 @ cell+ ! cc-t2 @ !
  1 cc-t1 @ 5 cells + +! ;
create cc-sl 16 cells allot create cc-sh 16 cells allot
create cc-read-layer 16 cells allot create cc-read-slot 16 cells allot
create cc-used 8 cells allot variable cc-nused variable cc-rl variable cc-pk variable cc-pkl
: cc-npatches ( -- n ) 0 cc-nitems @ 0 ?do i cc-item@ 5 cells + @ + loop ;
: cc-used? ( table -- flag )
  0 cc-nused @ 0 ?do over cc-used i cells + @ = or loop nip ;
: cc-place-reads ( -- )
  0 cc-rl ! 0 cc-nused !
  cc-nitems @ 0 ?do
    i cc-item@ cc-t1 !
    cc-rl @ 0= if -1 else cc-rl @ cc-count cc-work = cc-t1 @ @ cc-used? or then
    if cc-layer cc-rl ! 0 cc-nused ! then
    cc-t1 @ @ cc-used cc-nused @ cells + ! 1 cc-nused +!
    cc-t1 @ @ cc-t1 @ 4 cells + @ cc-t1 @ cell+ @ lshift + cc-t2 !
    cc-t1 @ 3 cells + @ dup cc-t1 @ 2 cells + @ +
    cc-t2 @ dup cc-t1 @ 2 cells + @ +
    cc-rl @ cc-row i cells cc-read-slot + ! cc-rl @ i cells cc-read-layer + !
  loop ;
: cc-patch ( item seg -- )
  cc-t4 ! cc-t3 !
  cc-t3 @ cc-item@ cc-t1 ! cc-t1 @ cc-t4 @ dup 2* + 6 + cells + cc-t2 !
  cc-t3 @ cells cc-read-layer + @ cc-layer-cell cc-t3 @ cells cc-read-slot + @
  2dup 2 cc-field cc-t1 @ cell+ @ + cc-t2 @ 2 cells + @ + cc-lo !
  3 cc-field cc-t1 @ cell+ @ + cc-t2 @ 2 cells + @ + cc-hi !
  cc-t2 @ cell+ @ cc-lo @ cc-t2 @ @ cc-copy cc-pkl @ cells cc-sl + @ cc-row drop
  cc-t2 @ cell+ @ cc-hi @ cc-t2 @ @ cc-copy cc-pkl @ cells cc-sh + @ cc-row drop
  1 cc-pk +! cc-pk @ cc-work = if 0 cc-pk ! 1 cc-pkl +! then ;
: cc-lookups ( -- )
  0 cc-npatches begin dup 0> while cc-work - swap 1+ swap repeat drop cc-t5 !
  cc-t5 @ 0 ?do cc-layer i cells cc-sl + ! loop
  cc-t5 @ 0 ?do cc-layer i cells cc-sh + ! loop
  cc-layer drop cc-place-reads 0 cc-pk ! 0 cc-pkl !
  cc-nitems @ 0 ?do i cc-item@ 5 cells + @ 0 ?do j i cc-patch loop loop ;
\ Nibble adder: x = a + b, or a + ~b + 1 with the sub table and carry 1.
create cc-al 25 cells allot create cc-ar 8 cells allot
variable cc-ax variable cc-aa variable cc-ab variable cc-atab variable cc-acarry
: cc-al@ ( i -- layer ) cells cc-al + @ ;
: cc-rd ( i -- cell slot ) dup dup 2* + 3 + cc-al@ cc-layer-cell swap cells cc-ar + @ ;
: cc-adder-patch ( i f layer -- )
  cc-t3 ! cc-t4 !
  dup cc-rd cc-t4 @ cc-field cc-lo !
  4 cc-lo @ 3 + 2 pick 2 lshift cc-aa @ + cc-copy cc-t3 @ cc-row drop
  4 cc-lo @ 7 + rot 2 lshift cc-ab @ + cc-copy cc-t3 @ cc-row drop ;
: cc-adder ( table x a b carry -- )
  cc-acarry ! cc-ab ! cc-aa ! cc-ax ! cc-atab !
  25 0 do cc-layer i cells cc-al + ! loop
  8 0 do
    cc-atab @ i 0= if cc-acarry @ 11 lshift + then
    cc-ax @ i 4 * + dup 6 + rot dup 6 +
    i dup 2* + 3 + cc-al@ cc-row i cells cc-ar + !
  loop
  8 0 do
    i 3 < if i 2 0 cc-al@ cc-adder-patch i 3 1 cc-al@ cc-adder-patch
    else i 2 i dup 2* + 1- cc-al@ cc-adder-patch i 3 i dup 2* + cc-al@ cc-adder-patch then
    i if
      1 i cc-rd 2 cc-field 11 + cc-ax @ i 4 * + cc-copy i dup 2* + 1+ cc-al@ cc-row drop
      1 i cc-rd 3 cc-field 11 + cc-ax @ i 4 * + 1+ cc-copy i dup 2* + 1+ cc-al@ cc-row drop
    then
  loop ;
\ Continue at group target value(src[0:k]); src[k:2k] holds a copy.
variable cc-dsrc variable cc-dk variable cc-dg variable cc-dp variable cc-dx
: cc-decide ( src k -- group )
  cc-dk ! cc-dsrc ! cc-dk @ cc-group cc-dg !
  cc-layer cc-dp ! cc-layer drop cc-layer cc-dx !
  cc-dg @ cc-dx @ cc-next!
  cc-dk @ cc-dx @ cc-layer-cell cc-link-slot 2 cc-field cc-branch-bit + cc-dsrc @ cc-copy cc-dp @ cc-row drop
  cc-dk @ cc-dx @ cc-layer-cell cc-link-slot 3 cc-field cc-branch-bit + cc-dsrc @ cc-dk @ + cc-copy
  cc-dp @ cc-row drop cc-dg @ ;
\ Tables are placed in [at, limit), each aligned to its size.
variable cc-table-at variable cc-table-limit variable cc-tbuf
variable cc-tx variable cc-tbits variable cc-ts variable cc-tsize variable cc-tbase variable cc-tper
: cc-tables ( at limit -- ) cc-table-limit ! cc-table-at ! ;
: cc-table-area ( bits s -- buf )
  cc-ts ! cc-tbits !
  1 cc-ts @ cc-tbits @ + lshift cc-tsize !
  cc-table-at @ cc-tsize @ 1- + cc-tsize @ negate and cc-tbase !
  cc-tbase @ cc-tsize @ + cc-table-at !
  cc-table-at @ cc-table-limit @ u> if -8 throw then
  cc-tsize @ 3 rshift allocate throw cc-tbuf ! cc-tbuf @ cc-tsize @ 3 rshift 0 fill
  1 cc-ts @ lshift 3 rshift cc-tper ! cc-tbuf @ ;
: cc-table-done ( -- base )
  cc-tbase @ cc-tbuf @ cc-tsize @ 3 rshift cc-put cc-tbuf @ free throw cc-tbase @ ;
\ Or fill the buffer of cc-table-area directly (entry i at i * 2^s / 8 bytes).
: cc-table ( xt bits s -- base )
  rot cc-tx ! cc-table-area drop
  cc-ts @ 3 < 0= if
    1 cc-tbits @ lshift 0 ?do
      i cc-tx @ execute cc-tper @ cc-tbuf @ i cc-tper @ * + cc-numeric
    loop
  else
    1 cc-tbits @ lshift 0 ?do
      i cc-tx @ execute
      1 cc-ts @ lshift 0 ?do
        dup i rshift 1 and if
          j cc-ts @ lshift i + cc-t5 !
          cc-t5 @ 3 rshift cc-tbuf @ + dup c@ 128 cc-t5 @ 7 and rshift or swap c!
        then
      loop drop
    loop
  then cc-table-done ;
\ Entries of two cells, low 32 bits first: xt ( i -- lo hi ), s >= 6.
: cc-table2 ( xt bits s -- base )
  dup 6 < if -24 throw then
  rot cc-tx ! cc-table-area drop
  1 cc-tbits @ lshift 0 ?do
    i cc-tx @ execute cc-tbuf @ i cc-tper @ * + >r
    4 r@ 4 + cc-numeric 4 r> cc-numeric
  loop cc-table-done ;
: cc-add-entry ( i -- v ) dup 15 and over 4 rshift 15 and + swap 8 rshift +
  dup 4 rshift 5 lshift or ;
: cc-sub-entry ( i -- v ) dup 15 and over 4 rshift invert 15 and + swap 8 rshift +
  dup 4 rshift 5 lshift or ;
: cc-xor-entry ( i -- v ) dup 15 and swap 4 rshift xor ;
: cc-or-entry ( i -- v ) dup 15 and swap 4 rshift or ;
: cc-and-entry ( i -- v ) dup 15 and swap 4 rshift and ;
: cc-or8-entry ( i -- v ) 0<> 1 and ;
variable cc-fz variable cc-fu variable cc-fs
: cc-pair ( flag shift -- v ) swap if 3 swap lshift else drop 0 then ;
: cc-flags-entry ( i -- v )
  dup 15 and 0= cc-fz ! dup 4 rshift 1 and 0= cc-fu !
  dup 5 rshift 1 and swap 6 rshift 1 and
  2dup <> if drop 0<> else 2drop cc-fu @ then cc-fs !
  cc-fz @ 0 cc-pair cc-fz @ 0= 2 cc-pair or
  cc-fs @ 4 cc-pair or cc-fs @ 0= 6 cc-pair or
  cc-fu @ 8 cc-pair or cc-fu @ 0= 10 cc-pair or ;
: cc-not5-entry ( i -- v ) 31 swap - dup 5 lshift or ;
: cc-sign-entry ( i -- v ) if -1 else 0 then ;
: cc-fill24-entry ( i -- v ) if 16777215 else 0 then ;
: cc-fill16-entry ( i -- v ) if 65535 else 0 then ;
: cc-inc1-entry ( i -- v ) 1+ ;
: cc-inc2-entry ( i -- v ) 2 + ;
variable cc-t-add variable cc-t-sub variable cc-t-xor variable cc-t-or variable cc-t-and
variable cc-t-or8 variable cc-t-flags variable cc-t-not5 variable cc-t-sign32
variable cc-t-fill24 variable cc-t-fill16 variable cc-t-inc1 variable cc-t-inc2
: cc-standard-tables ( -- )
  ['] cc-add-entry 9 3 cc-table cc-t-add ! ['] cc-sub-entry 9 3 cc-table cc-t-sub !
  ['] cc-xor-entry 8 3 cc-table cc-t-xor ! ['] cc-or-entry 8 3 cc-table cc-t-or !
  ['] cc-and-entry 8 3 cc-table cc-t-and ! ['] cc-or8-entry 8 1 cc-table cc-t-or8 !
  ['] cc-flags-entry 7 4 cc-table cc-t-flags ! ['] cc-not5-entry 5 4 cc-table cc-t-not5 !
  ['] cc-sign-entry 1 6 cc-table cc-t-sign32 ! ['] cc-fill24-entry 1 5 cc-table cc-t-fill24 !
  ['] cc-fill16-entry 1 5 cc-table cc-t-fill16 ! ['] cc-inc1-entry 2 2 cc-table cc-t-inc1 !
  ['] cc-inc2-entry 2 2 cc-table cc-t-inc2 ! ;
\ Building blocks over registers given as bit addresses.
variable cc-oo variable cc-os variable cc-ol variable cc-oh
: cc-or-chunks ( out src lo hi -- )
  cc-oh ! cc-ol ! cc-os ! cc-oo !
  cc-oh @ cc-ol @ - 7 + 3 rshift 0 ?do
    cc-t-or8 @ 1 1 cc-oo @ i + 0 cc-item
    cc-os @ cc-ol @ + i 3 lshift + cc-oh @ cc-ol @ - i 3 lshift - 8 min 0 cc-seg
  loop ;
variable cc-cr variable cc-ca variable cc-cb variable cc-cz variable cc-cf
: cc-compare ( res a b z flags -- )
  cc-cf ! cc-cz ! cc-cb ! cc-ca ! cc-cr !
  cc-lookups-begin cc-cz @ cc-cr @ 0 32 cc-or-chunks cc-lookups
  cc-lookups-begin cc-t-flags @ 4 12 cc-cf @ 0 cc-item
  cc-cz @ 4 0 cc-seg cc-cr @ 32 + 1 4 cc-seg cc-ca @ 31 + 1 5 cc-seg cc-cb @ 31 + 1 6 cc-seg
  cc-lookups ;
: cc-logic ( table res a b -- )
  cc-cb ! cc-ca ! cc-cr ! cc-t5 ! cc-lookups-begin
  8 0 do
    cc-t5 @ 3 4 cc-cr @ i 2 lshift + 0 cc-item
    cc-ca @ i 2 lshift + 4 0 cc-seg cc-cb @ i 2 lshift + 4 4 cc-seg
  loop cc-lookups ;
variable cc-sres variable cc-sa variable cc-samt variable cc-sw variable cc-szero
variable cc-sarg variable cc-sign
: cc-shift-row ( layer -- ) >r cc-sres @ dup 32 + cc-sw @ dup 32 + r> cc-row drop ;
: cc-shift-patch ( n src shift-layer f off dst-layer -- )
  >r >r >r cc-layer-cell 0 r> cc-field r> + swap cc-copy r> cc-row drop ;
: cc-shift-right ( res a amount w zero arithmetic -- )
  cc-sarg ! cc-szero ! cc-sw ! cc-samt ! cc-sa ! cc-sres !
  cc-sarg @ 0= if
    cc-layer cc-l0 ! 32 cc-sw @ cc-sa @ cc-copy cc-l0 @ cc-row drop
    32 cc-sw @ 32 + cc-szero @ cc-copy cc-l0 @ cc-row drop
    cc-layer cc-l1 ! cc-layer drop cc-layer dup cc-l3 ! cc-shift-row
    5 cc-samt @ cc-l3 @ 2 0 cc-l0 @ cc-shift-patch
    5 cc-samt @ cc-l3 @ 3 0 cc-l1 @ cc-shift-patch exit
  then
  cc-layer cc-l0 ! 32 cc-sw @ cc-sa @ cc-copy cc-l0 @ cc-row drop
  cc-layer cc-l1 ! cc-layer cc-l2 ! cc-layer drop
  cc-layer cc-l4 ! cc-layer dup cc-l5 ! cc-shift-row
  cc-sw @ 32 + dup 32 + cc-t-sign32 @ dup 32 + cc-l4 @ cc-row cc-sign !
  5 cc-samt @ cc-l5 @ 2 0 cc-l0 @ cc-shift-patch
  5 cc-samt @ cc-l5 @ 3 0 cc-l1 @ cc-shift-patch
  1 cc-l4 @ cc-layer-cell cc-sign @ 2 cc-field 6 + cc-sa @ 31 + cc-copy cc-l1 @ cc-row drop
  1 cc-l4 @ cc-layer-cell cc-sign @ 3 cc-field 6 + cc-sa @ 31 + cc-copy cc-l2 @ cc-row drop ;
: cc-shift-left ( res a amount w zero u -- )
  cc-sarg ! cc-szero ! cc-sw ! cc-samt ! cc-sa ! cc-sres !
  cc-layer cc-l0 ! 31 cc-sw @ cc-szero @ cc-copy cc-l0 @ cc-row drop
  32 cc-sw @ 31 + cc-sa @ cc-copy cc-l0 @ cc-row drop
  cc-layer cc-l1 ! cc-layer drop
  cc-layer cc-l3 ! cc-sarg @ dup 10 + cc-t-not5 @ dup 10 + cc-l3 @ cc-row cc-sign !
  5 cc-l3 @ cc-layer-cell cc-sign @ 2 cc-field 4 + cc-samt @ cc-copy cc-l0 @ cc-row drop
  5 cc-l3 @ cc-layer-cell cc-sign @ 3 cc-field 4 + cc-samt @ cc-copy cc-l1 @ cc-row drop
  cc-layer cc-l4 ! cc-layer drop cc-layer dup cc-l5 ! cc-shift-row
  5 cc-sarg @ cc-l5 @ 2 0 cc-l4 @ cc-shift-patch
  5 cc-sarg @ 5 + cc-l5 @ 3 0 cc-l4 @ cc-shift-patch ;
\ Exit select: flag pair (source patched by the caller) becomes the cell bit
\ of the exit link, so a call returns to ret or ret + cc-branch-step.
variable cc-fc variable cc-ff
: cc-flag-exit ( c2 flags -- row exit )
  cc-ff ! cc-fc !
  cc-layer cc-l0 ! 2 cc-fc @ cc-ff @ cc-copy cc-l0 @ cc-row drop
  cc-layer cc-l1 ! cc-layer drop
  cc-lone cc-l2 ! cc-cell-bits @ cc-l2 @ cc-next! cc-l2 @ cc-layer-cell cc-jump
  1 cc-l2 @ cc-layer-cell cc-link-slot 2 cc-field cc-branch-bit + cc-fc @ cc-copy cc-l1 @ cc-row drop
  1 cc-l2 @ cc-layer-cell cc-link-slot 3 cc-field cc-branch-bit + cc-fc @ 1+ cc-copy cc-l1 @ cc-row drop
  cc-l0 @ cc-layer-cell 0 0 cc-field cc-l2 @ cc-layer-cell ;
\ Shared returns: write res to a patched destination, or plain return.
: cc-exit-layers ( res discard width -- xw x )
  cc-lone cc-l0 ! swap rot cc-copy cc-l0 @ cc-row drop cc-cell-bits @ cc-l0 @ cc-next!
  cc-lone cc-l1 ! cc-cell-bits @ cc-l1 @ cc-next!
  cc-l0 @ cc-layer-cell cc-l1 @ cc-layer-cell ;
\ Call site rows: patch the exit link with ret and ret+layer stored at lo/hi.
variable cc-ce variable cc-cl variable cc-ch
: cc-call-rows ( exit lo-src hi-src layer -- )
  cc-l0 ! cc-ch ! cc-cl ! cc-ce !
  cc-a @ cc-ce @ cc-link-slot 2 cc-field cc-cl @ cc-copy cc-l0 @ cc-row drop
  cc-a @ cc-ce @ cc-link-slot 3 cc-field cc-ch @ cc-copy cc-l0 @ cc-row drop ;
\ Halt: one stdout region per layer, then the zero cell 1.
: cc-halt-begin ( -- ) -1 cc-seq ;
: cc-halt-region ( n src -- ) cc-layer >r cc-out r> cc-row drop ;
: cc-halt-end ( -- cell ) cc-cell-bits @ cc-jump cc-entry ;
: cc-stub-on ( status constant halt layer -- ) dup >r cc-next! 32 -rot cc-copy r> cc-row drop ;
: cc-stub ( status constant halt -- ) cc-layer cc-stub-on ;
