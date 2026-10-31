\ SPDX-License-Identifier: MIT
\ Index-code layers and the emulator boot stream; control: copycode.vm1.backend.
\ Address fields are byte-sized (a multiple of 8), slots >= 8. Cells are
\ power-of-two bit ranges holding one layer; cell 0 is the entry layer.
\ A layer has slots-1 work rows and a link row; rows are dl dh sl sh.
\ Pending layers are encoded at lay-flush; a sequence ends at lay-flush.
\ THROW -24: invalid machine/field/unlinked; -9: overlap or put outside;
\ -8: capacity. Output goes to stdout with TYPE as it is produced, or to a
\ sink: an xt ( bit-address src n -- ) in lay-sink takes every put, and
\ lay-finish only keeps the entry in lay-start-cell. A kernel installs code in
\ its own space so; lay-rev (the stream's bit order of a byte) is then the
\ identity, the bytes are numeric.
decimal
variable lay-size variable lay-a variable lay-slots variable lay-cell-bits
variable lay-chunk variable lay-chunk-buf variable lay-lbuf variable lay-pool
variable lay-ebuf variable lay-dest variable lay-sink variable lay-start-cell
0 lay-pool ! 0 lay-sink !
create lay-rev 256 allot
: lay-rev-init 256 0 do
    0 8 0 do 2* j i rshift 1 and or loop lay-rev i + c!
  loop ;
lay-rev-init
: lay-inst ( -- n ) lay-a @ 4 * ;
: lay-layer-bits ( -- n ) lay-slots @ lay-inst * ;
: lay-lbytes ( -- n ) lay-layer-bits 3 rshift ;
: lay-stdin ( -- c ) lay-size @ 1+ ;
: lay-stdout ( -- c ) lay-size @ 2 + ;
: lay-bits ( u -- n ) 0 swap begin dup while 1 rshift swap 1+ swap repeat drop ;
: lay-numeric ( value nbytes addr -- )
  swap 0 ?do
    over i 4 < if i 3 lshift rshift 255 and lay-rev + c@ else drop 0 then
    over i + c!
  loop 2drop ;
\ The same for four bytes, unrolled: the 32-bit address fields of rows.
: lay-numeric4 ( value addr -- )
  over 255 and lay-rev + c@ over c!  over 8 rshift 255 and lay-rev + c@ over 1+ c!
  over 16 rshift 255 and lay-rev + c@ over 2 + c!  swap 24 rshift 255 and lay-rev + c@ swap 3 + c! ;
: lay-field-check ( value -- value )
  lay-a @ 32 < if dup lay-a @ rshift if -24 throw then then ;
\ Encode count rows (4 cells each) padded with zero rows into lay-dest.
: lay-encode ( rows count -- )
  lay-dest @ lay-lbytes 0 fill
  0 ?do
    4 0 do
      dup j 2 lshift i + cells + @ lay-field-check
      lay-a @ 32 = if lay-dest @ j 4 lshift + i 2 lshift + lay-numeric4
      else lay-a @ 3 rshift lay-dest @ j 2 lshift i + lay-a @ 3 rshift * + lay-numeric then
    loop
  loop drop ;
\ Stream state: chunk start byte (-1: none) and length.
variable lay-start variable lay-len
create lay-rows 32 cells allot
: lay-row! ( dl dh sl sh i -- ) 2 lshift cells lay-rows + >r
  r@ 3 cells + ! r@ 2 cells + ! r@ cell+ ! r> ! ;
: lay-clear-rows ( -- ) lay-rows 32 cells 0 fill ;
: lay-loader ( -- )
  lay-clear-rows lay-start @ 3 lshift dup lay-len @ 3 lshift + lay-stdin dup 0 lay-row!
  0 3 lay-inst * 4 lay-inst * 7 lay-inst * 1 lay-row!
  3 lay-inst * lay-a @ + 3 lay-inst * lay-a @ 2 * + 7 lay-inst * dup lay-a @ + 2 lay-row!
  0 0 lay-stdin dup 3 lay-row!
  lay-layer-bits 0 0 0 lay-slots @ 1- lay-row!
  lay-lbuf @ lay-dest ! lay-rows lay-slots @ lay-encode ;
: lay-stream-flush ( -- )
  lay-start @ -1 = if exit then
  lay-loader lay-lbuf @ lay-lbytes type
  lay-chunk-buf @ lay-len @ type -1 lay-start ! ;
: lay-begin-chunk ( byte src n -- )
  dup lay-len ! lay-chunk-buf @ swap cmove lay-start ! ;
: lay-put ( bit-address src n -- )
  lay-sink @ ?dup if execute exit then
  rot dup 7 and over lay-cell-bits @ u< or if -9 throw then
  dup 2 pick 3 lshift + lay-size @ u> if -9 throw then
  3 rshift -rot
  lay-start @ -1 <> if
    2 pick lay-start @ lay-len @ + -               ( byte src n gap )
    dup 0< 0= over 33 < and
    4 pick lay-start @ - 3 pick + lay-chunk @ 1+ < and if
      lay-chunk-buf @ lay-len @ + over 0 fill
      lay-len @ + lay-len !
      lay-chunk-buf @ lay-len @ + swap dup lay-len +! cmove drop exit
    then drop lay-stream-flush
  then
  begin dup lay-chunk @ > while
    2 pick 2 pick lay-chunk @ lay-begin-chunk lay-stream-flush
    rot lay-chunk @ + rot lay-chunk @ + rot lay-chunk @ -
  repeat lay-begin-chunk ;
create lay-scratch 8 allot
: lay-put-numeric ( value nbytes bit-address -- )
  >r dup >r lay-scratch lay-numeric r> r> lay-scratch rot lay-put ;
\ Layer records: cell, next (-1 unlinked), count, rows. Pending records are
\ a ring: a new record beyond lay-max-layers first writes the oldest pending
\ one (it must be linked), as the host Builder with that capacity.
128 constant lay-max-layers
: lay-record ( -- n ) lay-slots @ 1- 4 * 3 + cells ;
variable lay-pending variable lay-head variable lay-next-cell
variable lay-seq# variable lay-seq-first variable lay-seq-entry variable lay-seq-last
\ Offsets of the fields of each slot, computed by lay-machine.
create lay-foff 32 cells allot
: lay-foff-init ( -- ) 8 0 do 4 0 do j lay-inst * i lay-a @ * + j 2 lshift i + cells lay-foff + ! loop loop ;
: lay-machine ( size slots cell-bits chunk-bytes -- )
  >r >r >r dup lay-bits r> r> r>
  ( size a slots cell chunk )
  2 pick 8 < 4 pick 7 and or 5 pick 7 and or if -24 throw then
  over dup 1- and if -24 throw then
  dup 1 < if -24 throw then
  lay-chunk ! lay-cell-bits ! lay-slots ! lay-a ! lay-size !
  lay-size @ 5 + lay-a @ 32 < if lay-a @ rshift if -24 throw then else drop then
  lay-cell-bits @ lay-layer-bits < if -24 throw then
  lay-slots @ 8 > if -24 throw then
  lay-pool @ if
    lay-chunk-buf @ free throw lay-lbuf @ free throw lay-ebuf @ free throw lay-pool @ free throw
  then
  lay-chunk @ allocate throw lay-chunk-buf ! lay-lbytes allocate throw lay-lbuf !
  lay-lbytes allocate throw lay-ebuf !
  lay-record lay-max-layers * allocate throw lay-pool !
  -1 lay-start ! 0 lay-len ! 0 lay-pending ! 0 lay-head ! 2 lay-next-cell ! 0 lay-seq# ! lay-foff-init ;
: lay-field ( cell slot f -- addr ) swap 2 lshift + cells lay-foff + @ + ;
: lay-link-row ( target -- dl dh sl sh ) >r 0 lay-layer-bits r@ dup lay-layer-bits + r> drop ;
: lay-copy ( n dst src -- dl dh sl sh ) rot >r over r@ + swap dup r> + ;
: lay-out ( n src -- dl dh sl sh ) lay-stdout dup 2swap tuck + ;
: lay-builder ( first-cell -- ) lay-next-cell ! 0 lay-pending ! 0 lay-head ! 0 lay-seq# ! ;
: lay-new-cell ( -- addr ) lay-next-cell @ dup 1+ lay-next-cell ! lay-cell-bits @ * ;
\ The link bit selecting a branch target: both endpoints (target, target+layer)
\ share it, so with a layer filling the cell targets are two cells apart.
: lay-branch-bit ( -- n ) lay-cell-bits @ lay-bits 1- lay-layer-bits lay-cell-bits @ < 0= - ;
: lay-branch-step ( -- n ) 1 lay-branch-bit lshift ;
\ 2^k branch targets lay-branch-step apart, aligned to the block.
: lay-group ( k -- base )
  1 swap lshift lay-branch-step lay-cell-bits @ / * dup 1- lay-next-cell @ + over / over *
  dup rot + lay-next-cell ! lay-cell-bits @ * ;
: lay-layer-cell ( layer -- cell ) @ ;
: lay-next! ( target layer -- ) cell+ ! ;
: lay-count ( layer -- n ) 2 cells + @ ;
: lay-row-addr ( layer i -- addr ) 2 lshift 3 + cells + ;
: lay-pending@ ( i -- layer ) lay-head @ + lay-max-layers 1- and lay-record * lay-pool @ + ;
: lay-encode-layer ( layer -- )
  dup cell+ @ -1 = if -24 throw then
  lay-clear-rows dup 3 cells + lay-rows 2 pick lay-count 2 lshift cells cmove
  cell+ @ lay-link-row lay-slots @ 1- lay-row!
  lay-ebuf @ lay-dest ! lay-rows lay-slots @ lay-encode ;
\ An xt ( layer -- ) in lay-on-write sees every layer as it is written (0: none); the price of
\ a word (14.11) is counted from them. The stream does not change.
variable lay-on-write 0 lay-on-write !
: lay-write ( layer -- )
  lay-on-write @ ?dup if over swap execute then
  dup lay-encode-layer lay-layer-cell lay-ebuf @ lay-lbytes lay-put ;
: lay-write-oldest ( -- ) 0 lay-pending@ lay-write lay-head @ 1+ lay-max-layers 1- and lay-head ! -1 lay-pending +! ;
: lay-new-record ( cell -- layer )
  lay-pending @ lay-max-layers = if lay-write-oldest then
  lay-pending @ lay-pending@ tuck !
  -1 over lay-next! 0 over 2 cells + ! 1 lay-pending +! ;
: lay-lone ( -- layer ) lay-new-cell lay-new-record ;
: lay-seq ( first|-1 -- ) lay-seq-first ! 0 lay-seq# ! ;
: lay-last ( -- layer ) lay-seq-last @ ;
: lay-layer ( -- layer )
  lay-seq# @ 0= lay-seq-first @ -1 <> and if lay-seq-first @ else lay-new-cell then
  lay-new-record
  lay-seq# @ if dup lay-layer-cell lay-last lay-next! else dup lay-layer-cell lay-seq-entry ! then
  dup lay-seq-last ! 1 lay-seq# +! ;
: lay-entry ( -- cell ) lay-seq-entry @ ;
: lay-jump ( target -- ) lay-last lay-next! ;
variable lay-l1 variable lay-h1 variable lay-l2 variable lay-h2
variable lay-ra variable lay-rb variable lay-cur
\ Two half-open intervals clash if both are memory, non-empty and overlap.
: lay-clash? ( lo1 hi1 lo2 hi2 -- flag )
  lay-h2 ! lay-l2 ! lay-h1 ! lay-l1 !
  lay-l1 @ lay-h1 @ u< lay-l2 @ lay-h2 @ u< and
  lay-l1 @ lay-h2 @ u< and lay-l2 @ lay-h1 @ u< and
  lay-l1 @ lay-size @ u< and lay-l2 @ lay-size @ u< and ;
: lay-row-clash? ( row1 row2 -- flag )
  lay-rb ! lay-ra ! 0
  2 0 do 2 0 do
    lay-ra @ j 2* cells + 2@ swap lay-rb @ i 2* cells + 2@ swap lay-clash? or
  loop loop ;
create lay-new-row 4 cells allot
: lay-row-set ( dl dh sl sh layer -- )
  lay-cur ! lay-new-row 3 cells + ! lay-new-row 2 cells + ! lay-new-row cell+ ! lay-new-row ! ;
: lay-full? ( -- flag ) lay-cur @ lay-count lay-slots @ 1- < 0= ;
: lay-clashes? ( -- flag )
  0 lay-cur @ lay-count 0 ?do
    lay-new-row lay-cur @ i lay-row-addr lay-row-clash? if drop -1 leave then
  loop ;
\ Would the row fit the layer (a free slot, no overlap)? Nothing is added.
: lay-fits? ( dl dh sl sh layer -- flag )
  lay-row-set lay-full? if 0 exit then lay-clashes? 0= ;
: lay-row ( dl dh sl sh layer -- slot )
  lay-row-set lay-full? if -8 throw then lay-clashes? if -9 throw then
  lay-new-row lay-cur @ dup lay-count lay-row-addr 4 cells cmove
  lay-cur @ lay-count 1 lay-cur @ 2 cells + +! ;
: lay-flush ( -- )
  lay-pending @ 0 ?do i lay-pending@ cell+ @ -1 = if -24 throw then loop
  lay-pending @ 0 ?do i lay-pending@ lay-write loop 0 lay-pending ! 0 lay-head ! 0 lay-seq# ! ;
: lay-finish ( entry -- )
  lay-sink @ if lay-start-cell ! exit then
  lay-stream-flush lay-clear-rows lay-link-row lay-slots @ 1- lay-row!
  lay-lbuf @ lay-dest ! lay-rows lay-slots @ lay-encode lay-lbuf @ lay-lbytes type ;
