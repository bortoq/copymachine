\ SPDX-License-Identifier: MIT
\ Computation by copies; control: copycode.vm1.compute. Requires backend.fth.
\ A lookup reads a table entry whose index bits are copied into both source
\ endpoints of the read row: lower-endpoint patches, upper-endpoint patches,
\ one gap layer, then the reads. Entry stride exceeds width, so both
\ endpoints share the index bits. Layers and rows are created in the same
\ order as the host model, so the streams are identical. Words keep their
\ state in variables and are not reentrant. THROW -8: capacity.
decimal
variable lay-t1 variable lay-t2 variable lay-t3 variable lay-t4 variable lay-t5
variable lay-lo variable lay-hi
variable lay-l0 variable lay-l1 variable lay-l2 variable lay-l3 variable lay-l4 variable lay-l5
: lay-work ( -- n ) lay-slots @ 1- ;
: lay-cell-bit ( -- n ) lay-cell-bits @ lay-bits 1- ;
: lay-link-slot ( -- n ) lay-slots @ 1- ;
\ Lookup items: table s width out preset nseg, then 4 segments (src n off).
18 constant lay-item-cells 16 constant lay-max-items
create lay-items lay-max-items lay-item-cells * cells allot
variable lay-nitems
: lay-item@ ( i -- addr ) dup 4 lshift swap 2* + cells lay-items + ;   \ 18 cells each
: lay-lookups-begin ( -- ) 0 lay-nitems ! ;
: lay-item ( table s width out preset -- )
  lay-nitems @ lay-max-items < 0= if -8 throw then
  lay-nitems @ lay-item@ lay-t1 !
  lay-t1 @ 4 cells + ! lay-t1 @ 3 cells + ! lay-t1 @ 2 cells + ! lay-t1 @ cell+ ! lay-t1 @ !
  0 lay-t1 @ 5 cells + ! 1 lay-nitems +! ;
: lay-seg ( src n off -- )
  lay-nitems @ 1- lay-item@ lay-t1 !
  lay-t1 @ 5 cells + @ 4 < 0= if -8 throw then
  lay-t1 @ 5 cells + @ dup 2* + 6 + cells lay-t1 @ + lay-t2 !
  lay-t2 @ 2 cells + ! lay-t2 @ cell+ ! lay-t2 @ !
  1 lay-t1 @ 5 cells + +! ;
create lay-sl 16 cells allot create lay-sh 16 cells allot
create lay-read-layer 16 cells allot create lay-read-slot 16 cells allot
create lay-used 8 cells allot variable lay-nused variable lay-rl variable lay-pk variable lay-pkl
: lay-npatches ( -- n ) 0 lay-nitems @ 0 ?do i lay-item@ 5 cells + @ + loop ;
: lay-used? ( table -- flag )
  0 lay-nused @ 0 ?do over lay-used i cells + @ = or loop nip ;
: lay-place-reads ( -- )
  0 lay-rl ! 0 lay-nused !
  lay-nitems @ 0 ?do
    i lay-item@ lay-t1 !
    lay-rl @ 0= if -1 else lay-rl @ lay-count lay-work = lay-t1 @ @ lay-used? or then
    if lay-layer lay-rl ! 0 lay-nused ! then
    lay-t1 @ @ lay-used lay-nused @ cells + ! 1 lay-nused +!
    lay-t1 @ @ lay-t1 @ 4 cells + @ lay-t1 @ cell+ @ lshift + lay-t2 !
    lay-t1 @ 3 cells + @ dup lay-t1 @ 2 cells + @ +
    lay-t2 @ dup lay-t1 @ 2 cells + @ +
    lay-rl @ lay-row i cells lay-read-slot + ! lay-rl @ i cells lay-read-layer + !
  loop ;
: lay-patch ( item seg -- )
  lay-t4 ! lay-t3 !
  lay-t3 @ lay-item@ lay-t1 ! lay-t1 @ lay-t4 @ dup 2* + 6 + cells + lay-t2 !
  lay-t3 @ cells lay-read-layer + @ lay-layer-cell lay-t3 @ cells lay-read-slot + @
  2dup 2 lay-field lay-t1 @ cell+ @ + lay-t2 @ 2 cells + @ + lay-lo !
  3 lay-field lay-t1 @ cell+ @ + lay-t2 @ 2 cells + @ + lay-hi !
  lay-t2 @ cell+ @ lay-lo @ lay-t2 @ @ lay-copy lay-pkl @ cells lay-sl + @ lay-row drop
  lay-t2 @ cell+ @ lay-hi @ lay-t2 @ @ lay-copy lay-pkl @ cells lay-sh + @ lay-row drop
  1 lay-pk +! lay-pk @ lay-work = if 0 lay-pk ! 1 lay-pkl +! then ;
: lay-lookups ( -- )
  0 lay-npatches begin dup 0> while lay-work - swap 1+ swap repeat drop lay-t5 !
  lay-t5 @ 0 ?do lay-layer i cells lay-sl + ! loop
  lay-t5 @ 0 ?do lay-layer i cells lay-sh + ! loop
  lay-layer drop lay-place-reads 0 lay-pk ! 0 lay-pkl !
  lay-nitems @ 0 ?do i lay-item@ 5 cells + @ 0 ?do j i lay-patch loop loop ;
\ Nibble adder: x = a + b, or a + ~b + 1 with the sub table and carry 1.
create lay-al 25 cells allot create lay-ar 8 cells allot
variable lay-ax variable lay-aa variable lay-ab variable lay-atab variable lay-acarry
: lay-al@ ( i -- layer ) cells lay-al + @ ;
: lay-rd ( i -- cell slot ) dup dup 2* + 3 + lay-al@ lay-layer-cell swap cells lay-ar + @ ;
: lay-adder-patch ( i f layer -- )
  lay-t3 ! lay-t4 !
  dup lay-rd lay-t4 @ lay-field lay-lo !
  4 lay-lo @ 3 + 2 pick 2 lshift lay-aa @ + lay-copy lay-t3 @ lay-row drop
  4 lay-lo @ 7 + rot 2 lshift lay-ab @ + lay-copy lay-t3 @ lay-row drop ;
: lay-adder ( table x a b carry -- )
  lay-acarry ! lay-ab ! lay-aa ! lay-ax ! lay-atab !
  25 0 do lay-layer i cells lay-al + ! loop
  8 0 do
    lay-atab @ i 0= if lay-acarry @ 11 lshift + then
    lay-ax @ i 4 * + dup 6 + rot dup 6 +
    i dup 2* + 3 + lay-al@ lay-row i cells lay-ar + !
  loop
  8 0 do
    i 3 < if i 2 0 lay-al@ lay-adder-patch i 3 1 lay-al@ lay-adder-patch
    else i 2 i dup 2* + 1- lay-al@ lay-adder-patch i 3 i dup 2* + lay-al@ lay-adder-patch then
    i if
      1 i lay-rd 2 lay-field 11 + lay-ax @ i 4 * + lay-copy i dup 2* + 1+ lay-al@ lay-row drop
      1 i lay-rd 3 lay-field 11 + lay-ax @ i 4 * + 1+ lay-copy i dup 2* + 1+ lay-al@ lay-row drop
    then
  loop ;
\ Continue at group target value(src[0:k]); src[k:2k] holds a copy.
variable lay-dsrc variable lay-dk variable lay-dg variable lay-dp variable lay-dx
: lay-decide ( src k -- group )
  lay-dk ! lay-dsrc ! lay-dk @ lay-group lay-dg !
  lay-layer lay-dp ! lay-layer drop lay-layer lay-dx !
  lay-dg @ lay-dx @ lay-next!
  lay-dk @ lay-dx @ lay-layer-cell lay-link-slot 2 lay-field lay-branch-bit + lay-dsrc @ lay-copy lay-dp @ lay-row drop
  lay-dk @ lay-dx @ lay-layer-cell lay-link-slot 3 lay-field lay-branch-bit + lay-dsrc @ lay-dk @ + lay-copy
  lay-dp @ lay-row drop lay-dg @ ;
\ Tables are placed in [at, limit), each aligned to its size.
variable lay-table-at variable lay-table-limit variable lay-tbuf
variable lay-tx variable lay-tbits variable lay-ts variable lay-tsize variable lay-tbase variable lay-tper
: lay-tables ( at limit -- ) lay-table-limit ! lay-table-at ! ;
: lay-table-area ( bits s -- buf )
  lay-ts ! lay-tbits !
  1 lay-ts @ lay-tbits @ + lshift lay-tsize !
  lay-table-at @ lay-tsize @ 1- + lay-tsize @ negate and lay-tbase !
  lay-tbase @ lay-tsize @ + lay-table-at !
  lay-table-at @ lay-table-limit @ u> if -8 throw then
  lay-tsize @ 3 rshift allocate throw lay-tbuf ! lay-tbuf @ lay-tsize @ 3 rshift 0 fill
  1 lay-ts @ lshift 3 rshift lay-tper ! lay-tbuf @ ;
: lay-table-done ( -- base )
  lay-tbase @ lay-tbuf @ lay-tsize @ 3 rshift lay-put lay-tbuf @ free throw lay-tbase @ ;
\ Or fill the buffer of lay-table-area directly (entry i at i * 2^s / 8 bytes).
: lay-table ( xt bits s -- base )
  rot lay-tx ! lay-table-area drop
  lay-ts @ 3 < 0= if
    1 lay-tbits @ lshift 0 ?do
      i lay-tx @ execute lay-tper @ lay-tbuf @ i lay-tper @ * + lay-numeric
    loop
  else
    1 lay-tbits @ lshift 0 ?do
      i lay-tx @ execute
      1 lay-ts @ lshift 0 ?do
        dup i rshift 1 and if
          j lay-ts @ lshift i + lay-t5 !
          lay-t5 @ 3 rshift lay-tbuf @ + dup c@ 1 lay-t5 @ 7 and lshift lay-rev + c@ or swap c!
        then
      loop drop
    loop
  then lay-table-done ;
\ Entries of two cells, low 32 bits first: xt ( i -- lo hi ), s >= 6.
: lay-table2 ( xt bits s -- base )
  dup 6 < if -24 throw then
  rot lay-tx ! lay-table-area drop
  1 lay-tbits @ lshift 0 ?do
    i lay-tx @ execute lay-tbuf @ i lay-tper @ * + >r
    4 r@ 4 + lay-numeric 4 r> lay-numeric
  loop lay-table-done ;
: lay-add-entry ( i -- v ) dup 15 and over 4 rshift 15 and + swap 8 rshift +
  dup 4 rshift 5 lshift or ;
: lay-sub-entry ( i -- v ) dup 15 and over 4 rshift invert 15 and + swap 8 rshift +
  dup 4 rshift 5 lshift or ;
: lay-xor-entry ( i -- v ) dup 15 and swap 4 rshift xor ;
: lay-or-entry ( i -- v ) dup 15 and swap 4 rshift or ;
: lay-and-entry ( i -- v ) dup 15 and swap 4 rshift and ;
: lay-or8-entry ( i -- v ) 0<> 1 and ;
variable lay-fz variable lay-fu variable lay-fs
: lay-pair ( flag shift -- v ) swap if 3 swap lshift else drop 0 then ;
: lay-flags-entry ( i -- v )
  dup 15 and 0= lay-fz ! dup 4 rshift 1 and 0= lay-fu !
  dup 5 rshift 1 and swap 6 rshift 1 and
  2dup <> if drop 0<> else 2drop lay-fu @ then lay-fs !
  lay-fz @ 0 lay-pair lay-fz @ 0= 2 lay-pair or
  lay-fs @ 4 lay-pair or lay-fs @ 0= 6 lay-pair or
  lay-fu @ 8 lay-pair or lay-fu @ 0= 10 lay-pair or ;
: lay-not5-entry ( i -- v ) 31 swap - dup 5 lshift or ;
: lay-sign-entry ( i -- v ) if -1 else 0 then ;
: lay-fill24-entry ( i -- v ) if 16777215 else 0 then ;
: lay-fill16-entry ( i -- v ) if 65535 else 0 then ;
: lay-inc1-entry ( i -- v ) 1+ ;
: lay-inc2-entry ( i -- v ) 2 + ;
variable lay-t-add variable lay-t-sub variable lay-t-xor variable lay-t-or variable lay-t-and
variable lay-t-or8 variable lay-t-flags variable lay-t-not5 variable lay-t-sign32
variable lay-t-fill24 variable lay-t-fill16 variable lay-t-inc1 variable lay-t-inc2
: lay-standard-tables ( -- )
  ['] lay-add-entry 9 3 lay-table lay-t-add ! ['] lay-sub-entry 9 3 lay-table lay-t-sub !
  ['] lay-xor-entry 8 3 lay-table lay-t-xor ! ['] lay-or-entry 8 3 lay-table lay-t-or !
  ['] lay-and-entry 8 3 lay-table lay-t-and ! ['] lay-or8-entry 8 1 lay-table lay-t-or8 !
  ['] lay-flags-entry 7 4 lay-table lay-t-flags ! ['] lay-not5-entry 5 4 lay-table lay-t-not5 !
  ['] lay-sign-entry 1 6 lay-table lay-t-sign32 ! ['] lay-fill24-entry 1 5 lay-table lay-t-fill24 !
  ['] lay-fill16-entry 1 5 lay-table lay-t-fill16 ! ['] lay-inc1-entry 2 2 lay-table lay-t-inc1 !
  ['] lay-inc2-entry 2 2 lay-table lay-t-inc2 ! ;
\ Building blocks over registers given as bit addresses.
variable lay-oo variable lay-os variable lay-ol variable lay-oh
: lay-or-chunks ( out src lo hi -- )
  lay-oh ! lay-ol ! lay-os ! lay-oo !
  lay-oh @ lay-ol @ - 7 + 3 rshift 0 ?do
    lay-t-or8 @ 1 1 lay-oo @ i + 0 lay-item
    lay-os @ lay-ol @ + i 3 lshift + lay-oh @ lay-ol @ - i 3 lshift - 8 min 0 lay-seg
  loop ;
variable lay-cr variable lay-ca variable lay-cb variable lay-cz variable lay-cf
: lay-compare ( res a b z flags -- )
  lay-cf ! lay-cz ! lay-cb ! lay-ca ! lay-cr !
  lay-lookups-begin lay-cz @ lay-cr @ 0 32 lay-or-chunks lay-lookups
  lay-lookups-begin lay-t-flags @ 4 12 lay-cf @ 0 lay-item
  lay-cz @ 4 0 lay-seg lay-cr @ 32 + 1 4 lay-seg lay-ca @ 31 + 1 5 lay-seg lay-cb @ 31 + 1 6 lay-seg
  lay-lookups ;
: lay-logic ( table res a b -- )
  lay-cb ! lay-ca ! lay-cr ! lay-t5 ! lay-lookups-begin
  8 0 do
    lay-t5 @ 3 4 lay-cr @ i 2 lshift + 0 lay-item
    lay-ca @ i 2 lshift + 4 0 lay-seg lay-cb @ i 2 lshift + 4 4 lay-seg
  loop lay-lookups ;
variable lay-sres variable lay-sa variable lay-samt variable lay-sw variable lay-szero
variable lay-sarg variable lay-sign
: lay-shift-row ( layer -- ) >r lay-sres @ dup 32 + lay-sw @ dup 32 + r> lay-row drop ;
: lay-shift-patch ( n src shift-layer f off dst-layer -- )
  >r >r >r lay-layer-cell 0 r> lay-field r> + swap lay-copy r> lay-row drop ;
: lay-shift-right ( res a amount w zero arithmetic -- )
  lay-sarg ! lay-szero ! lay-sw ! lay-samt ! lay-sa ! lay-sres !
  lay-sarg @ 0= if
    lay-layer lay-l0 ! 32 lay-sw @ lay-sa @ lay-copy lay-l0 @ lay-row drop
    32 lay-sw @ 32 + lay-szero @ lay-copy lay-l0 @ lay-row drop
    lay-layer lay-l1 ! lay-layer drop lay-layer dup lay-l3 ! lay-shift-row
    5 lay-samt @ lay-l3 @ 2 0 lay-l0 @ lay-shift-patch
    5 lay-samt @ lay-l3 @ 3 0 lay-l1 @ lay-shift-patch exit
  then
  lay-layer lay-l0 ! 32 lay-sw @ lay-sa @ lay-copy lay-l0 @ lay-row drop
  lay-layer lay-l1 ! lay-layer lay-l2 ! lay-layer drop
  lay-layer lay-l4 ! lay-layer dup lay-l5 ! lay-shift-row
  lay-sw @ 32 + dup 32 + lay-t-sign32 @ dup 32 + lay-l4 @ lay-row lay-sign !
  5 lay-samt @ lay-l5 @ 2 0 lay-l0 @ lay-shift-patch
  5 lay-samt @ lay-l5 @ 3 0 lay-l1 @ lay-shift-patch
  1 lay-l4 @ lay-layer-cell lay-sign @ 2 lay-field 6 + lay-sa @ 31 + lay-copy lay-l1 @ lay-row drop
  1 lay-l4 @ lay-layer-cell lay-sign @ 3 lay-field 6 + lay-sa @ 31 + lay-copy lay-l2 @ lay-row drop ;
: lay-shift-left ( res a amount w zero u -- )
  lay-sarg ! lay-szero ! lay-sw ! lay-samt ! lay-sa ! lay-sres !
  lay-layer lay-l0 ! 31 lay-sw @ lay-szero @ lay-copy lay-l0 @ lay-row drop
  32 lay-sw @ 31 + lay-sa @ lay-copy lay-l0 @ lay-row drop
  lay-layer lay-l1 ! lay-layer drop
  lay-layer lay-l3 ! lay-sarg @ dup 10 + lay-t-not5 @ dup 10 + lay-l3 @ lay-row lay-sign !
  5 lay-l3 @ lay-layer-cell lay-sign @ 2 lay-field 4 + lay-samt @ lay-copy lay-l0 @ lay-row drop
  5 lay-l3 @ lay-layer-cell lay-sign @ 3 lay-field 4 + lay-samt @ lay-copy lay-l1 @ lay-row drop
  lay-layer lay-l4 ! lay-layer drop lay-layer dup lay-l5 ! lay-shift-row
  5 lay-sarg @ lay-l5 @ 2 0 lay-l4 @ lay-shift-patch
  5 lay-sarg @ 5 + lay-l5 @ 3 0 lay-l4 @ lay-shift-patch ;
\ Exit select: flag pair (source patched by the caller) becomes the cell bit
\ of the exit link, so a call returns to ret or ret + lay-branch-step.
variable lay-fc variable lay-ff
: lay-flag-exit ( c2 flags -- row exit )
  lay-ff ! lay-fc !
  lay-layer lay-l0 ! 2 lay-fc @ lay-ff @ lay-copy lay-l0 @ lay-row drop
  lay-layer lay-l1 ! lay-layer drop
  lay-lone lay-l2 ! lay-cell-bits @ lay-l2 @ lay-next! lay-l2 @ lay-layer-cell lay-jump
  1 lay-l2 @ lay-layer-cell lay-link-slot 2 lay-field lay-branch-bit + lay-fc @ lay-copy lay-l1 @ lay-row drop
  1 lay-l2 @ lay-layer-cell lay-link-slot 3 lay-field lay-branch-bit + lay-fc @ 1+ lay-copy lay-l1 @ lay-row drop
  lay-l0 @ lay-layer-cell 0 0 lay-field lay-l2 @ lay-layer-cell ;
\ Shared returns: write res to a patched destination, or plain return.
: lay-exit-layers ( res discard width -- xw x )
  lay-lone lay-l0 ! swap rot lay-copy lay-l0 @ lay-row drop lay-cell-bits @ lay-l0 @ lay-next!
  lay-lone lay-l1 ! lay-cell-bits @ lay-l1 @ lay-next!
  lay-l0 @ lay-layer-cell lay-l1 @ lay-layer-cell ;
\ Call site rows: patch the exit link with ret and ret+layer stored at lo/hi.
variable lay-ce variable lay-cl variable lay-ch
: lay-call-rows ( exit lo-src hi-src layer -- )
  lay-l0 ! lay-ch ! lay-cl ! lay-ce !
  lay-a @ lay-ce @ lay-link-slot 2 lay-field lay-cl @ lay-copy lay-l0 @ lay-row drop
  lay-a @ lay-ce @ lay-link-slot 3 lay-field lay-ch @ lay-copy lay-l0 @ lay-row drop ;
\ Halt: one stdout region per layer, then the zero cell 1.
: lay-halt-begin ( -- ) -1 lay-seq ;
: lay-halt-region ( n src -- ) lay-layer >r lay-out r> lay-row drop ;
: lay-halt-end ( -- cell ) lay-cell-bits @ lay-jump lay-entry ;
: lay-stub-on ( status constant halt layer -- ) dup >r lay-next! 32 -rot lay-copy r> lay-row drop ;
: lay-stub ( status constant halt -- ) lay-layer lay-stub-on ;
