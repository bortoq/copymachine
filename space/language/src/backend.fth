\ SPDX-License-Identifier: MIT
\ Index-code layers and the emulator boot stream; control: copycode.vm1.backend.
\ Address fields are byte-sized (a multiple of 8), slots >= 8. Cells are
\ power-of-two bit ranges holding one layer; cell 0 is the entry layer.
\ A layer has slots-1 work rows and a link row; rows are dl dh sl sh.
\ Pending layers are encoded at cc-flush; a sequence ends at cc-flush.
\ THROW -24: invalid machine/field/unlinked; -9: overlap or put outside;
\ -8: capacity. Output goes to stdout with TYPE as it is produced, or to a
\ sink: an xt ( bit-address src n -- ) in cc-sink takes every put, and
\ cc-finish only keeps the entry in cc-start-cell. A kernel installs code in
\ its own space so; cc-rev (the stream's bit order of a byte) is then the
\ identity, the bytes are numeric.
decimal
variable cc-size variable cc-a variable cc-slots variable cc-cell-bits
variable cc-chunk variable cc-chunk-buf variable cc-lbuf variable cc-pool
variable cc-ebuf variable cc-dest variable cc-sink variable cc-start-cell
0 cc-pool ! 0 cc-sink !
create cc-rev 256 allot
: cc-rev-init 256 0 do
    0 8 0 do 2* j i rshift 1 and or loop cc-rev i + c!
  loop ;
cc-rev-init
: cc-inst ( -- n ) cc-a @ 4 * ;
: cc-layer-bits ( -- n ) cc-slots @ cc-inst * ;
: cc-lbytes ( -- n ) cc-layer-bits 3 rshift ;
: cc-stdin ( -- c ) cc-size @ 1+ ;
: cc-stdout ( -- c ) cc-size @ 2 + ;
: cc-bits ( u -- n ) 0 swap begin dup while 1 rshift swap 1+ swap repeat drop ;
: cc-numeric ( value nbytes addr -- )
  swap 0 ?do
    over i 4 < if i 3 lshift rshift 255 and cc-rev + c@ else drop 0 then
    over i + c!
  loop 2drop ;
\ The same for four bytes, unrolled: the 32-bit address fields of rows.
: cc-numeric4 ( value addr -- )
  over 255 and cc-rev + c@ over c!  over 8 rshift 255 and cc-rev + c@ over 1+ c!
  over 16 rshift 255 and cc-rev + c@ over 2 + c!  swap 24 rshift 255 and cc-rev + c@ swap 3 + c! ;
: cc-field-check ( value -- value )
  cc-a @ 32 < if dup cc-a @ rshift if -24 throw then then ;
\ Encode count rows (4 cells each) padded with zero rows into cc-dest.
: cc-encode ( rows count -- )
  cc-dest @ cc-lbytes 0 fill
  0 ?do
    4 0 do
      dup j 2 lshift i + cells + @ cc-field-check
      cc-a @ 32 = if cc-dest @ j 4 lshift + i 2 lshift + cc-numeric4
      else cc-a @ 3 rshift cc-dest @ j 2 lshift i + cc-a @ 3 rshift * + cc-numeric then
    loop
  loop drop ;
\ Stream state: chunk start byte (-1: none) and length.
variable cc-start variable cc-len
create cc-rows 32 cells allot
: cc-row! ( dl dh sl sh i -- ) 2 lshift cells cc-rows + >r
  r@ 3 cells + ! r@ 2 cells + ! r@ cell+ ! r> ! ;
: cc-clear-rows ( -- ) cc-rows 32 cells 0 fill ;
: cc-loader ( -- )
  cc-clear-rows cc-start @ 3 lshift dup cc-len @ 3 lshift + cc-stdin dup 0 cc-row!
  0 3 cc-inst * 4 cc-inst * 7 cc-inst * 1 cc-row!
  3 cc-inst * cc-a @ + 3 cc-inst * cc-a @ 2 * + 7 cc-inst * dup cc-a @ + 2 cc-row!
  0 0 cc-stdin dup 3 cc-row!
  cc-layer-bits 0 0 0 cc-slots @ 1- cc-row!
  cc-lbuf @ cc-dest ! cc-rows cc-slots @ cc-encode ;
: cc-stream-flush ( -- )
  cc-start @ -1 = if exit then
  cc-loader cc-lbuf @ cc-lbytes type
  cc-chunk-buf @ cc-len @ type -1 cc-start ! ;
: cc-begin-chunk ( byte src n -- )
  dup cc-len ! cc-chunk-buf @ swap cmove cc-start ! ;
: cc-put ( bit-address src n -- )
  cc-sink @ ?dup if execute exit then
  rot dup 7 and over cc-cell-bits @ u< or if -9 throw then
  dup 2 pick 3 lshift + cc-size @ u> if -9 throw then
  3 rshift -rot
  cc-start @ -1 <> if
    2 pick cc-start @ cc-len @ + -               ( byte src n gap )
    dup 0< 0= over 33 < and
    4 pick cc-start @ - 3 pick + cc-chunk @ 1+ < and if
      cc-chunk-buf @ cc-len @ + over 0 fill
      cc-len @ + cc-len !
      cc-chunk-buf @ cc-len @ + swap dup cc-len +! cmove drop exit
    then drop cc-stream-flush
  then
  begin dup cc-chunk @ > while
    2 pick 2 pick cc-chunk @ cc-begin-chunk cc-stream-flush
    rot cc-chunk @ + rot cc-chunk @ + rot cc-chunk @ -
  repeat cc-begin-chunk ;
create cc-scratch 8 allot
: cc-put-numeric ( value nbytes bit-address -- )
  >r dup >r cc-scratch cc-numeric r> r> cc-scratch rot cc-put ;
\ Layer records: cell, next (-1 unlinked), count, rows. Pending records are
\ a ring: a new record beyond cc-max-layers first writes the oldest pending
\ one (it must be linked), as the host Builder with that capacity.
128 constant cc-max-layers
: cc-record ( -- n ) cc-slots @ 1- 4 * 3 + cells ;
variable cc-pending variable cc-head variable cc-next-cell
variable cc-seq# variable cc-seq-first variable cc-seq-entry variable cc-seq-last
\ Offsets of the fields of each slot, computed by cc-machine.
create cc-foff 32 cells allot
: cc-foff-init ( -- ) 8 0 do 4 0 do j cc-inst * i cc-a @ * + j 2 lshift i + cells cc-foff + ! loop loop ;
: cc-machine ( size slots cell-bits chunk-bytes -- )
  >r >r >r dup cc-bits r> r> r>
  ( size a slots cell chunk )
  2 pick 8 < 4 pick 7 and or 5 pick 7 and or if -24 throw then
  over dup 1- and if -24 throw then
  dup 1 < if -24 throw then
  cc-chunk ! cc-cell-bits ! cc-slots ! cc-a ! cc-size !
  cc-size @ 5 + cc-a @ 32 < if cc-a @ rshift if -24 throw then else drop then
  cc-cell-bits @ cc-layer-bits < if -24 throw then
  cc-slots @ 8 > if -24 throw then
  cc-pool @ if
    cc-chunk-buf @ free throw cc-lbuf @ free throw cc-ebuf @ free throw cc-pool @ free throw
  then
  cc-chunk @ allocate throw cc-chunk-buf ! cc-lbytes allocate throw cc-lbuf !
  cc-lbytes allocate throw cc-ebuf !
  cc-record cc-max-layers * allocate throw cc-pool !
  -1 cc-start ! 0 cc-len ! 0 cc-pending ! 0 cc-head ! 2 cc-next-cell ! 0 cc-seq# ! cc-foff-init ;
: cc-field ( cell slot f -- addr ) swap 2 lshift + cells cc-foff + @ + ;
: cc-link-row ( target -- dl dh sl sh ) >r 0 cc-layer-bits r@ dup cc-layer-bits + r> drop ;
: cc-copy ( n dst src -- dl dh sl sh ) rot >r over r@ + swap dup r> + ;
: cc-out ( n src -- dl dh sl sh ) cc-stdout dup 2swap tuck + ;
: cc-builder ( first-cell -- ) cc-next-cell ! 0 cc-pending ! 0 cc-head ! 0 cc-seq# ! ;
: cc-new-cell ( -- addr ) cc-next-cell @ dup 1+ cc-next-cell ! cc-cell-bits @ * ;
\ The link bit selecting a branch target: both endpoints (target, target+layer)
\ share it, so with a layer filling the cell targets are two cells apart.
: cc-branch-bit ( -- n ) cc-cell-bits @ cc-bits 1- cc-layer-bits cc-cell-bits @ < 0= - ;
: cc-branch-step ( -- n ) 1 cc-branch-bit lshift ;
\ 2^k branch targets cc-branch-step apart, aligned to the block.
: cc-group ( k -- base )
  1 swap lshift cc-branch-step cc-cell-bits @ / * dup 1- cc-next-cell @ + over / over *
  dup rot + cc-next-cell ! cc-cell-bits @ * ;
: cc-layer-cell ( layer -- cell ) @ ;
: cc-next! ( target layer -- ) cell+ ! ;
: cc-count ( layer -- n ) 2 cells + @ ;
: cc-row-addr ( layer i -- addr ) 2 lshift 3 + cells + ;
: cc-pending@ ( i -- layer ) cc-head @ + cc-max-layers 1- and cc-record * cc-pool @ + ;
: cc-encode-layer ( layer -- )
  dup cell+ @ -1 = if -24 throw then
  cc-clear-rows dup 3 cells + cc-rows 2 pick cc-count 2 lshift cells cmove
  cell+ @ cc-link-row cc-slots @ 1- cc-row!
  cc-ebuf @ cc-dest ! cc-rows cc-slots @ cc-encode ;
: cc-write ( layer -- ) dup cc-encode-layer cc-layer-cell cc-ebuf @ cc-lbytes cc-put ;
: cc-write-oldest ( -- ) 0 cc-pending@ cc-write cc-head @ 1+ cc-max-layers 1- and cc-head ! -1 cc-pending +! ;
: cc-new-record ( cell -- layer )
  cc-pending @ cc-max-layers = if cc-write-oldest then
  cc-pending @ cc-pending@ tuck !
  -1 over cc-next! 0 over 2 cells + ! 1 cc-pending +! ;
: cc-lone ( -- layer ) cc-new-cell cc-new-record ;
: cc-seq ( first|-1 -- ) cc-seq-first ! 0 cc-seq# ! ;
: cc-last ( -- layer ) cc-seq-last @ ;
: cc-layer ( -- layer )
  cc-seq# @ 0= cc-seq-first @ -1 <> and if cc-seq-first @ else cc-new-cell then
  cc-new-record
  cc-seq# @ if dup cc-layer-cell cc-last cc-next! else dup cc-layer-cell cc-seq-entry ! then
  dup cc-seq-last ! 1 cc-seq# +! ;
: cc-entry ( -- cell ) cc-seq-entry @ ;
: cc-jump ( target -- ) cc-last cc-next! ;
variable cc-l1 variable cc-h1 variable cc-l2 variable cc-h2
variable cc-ra variable cc-rb variable cc-cur
\ Two half-open intervals clash if both are memory, non-empty and overlap.
: cc-clash? ( lo1 hi1 lo2 hi2 -- flag )
  cc-h2 ! cc-l2 ! cc-h1 ! cc-l1 !
  cc-l1 @ cc-h1 @ u< cc-l2 @ cc-h2 @ u< and
  cc-l1 @ cc-h2 @ u< and cc-l2 @ cc-h1 @ u< and
  cc-l1 @ cc-size @ u< and cc-l2 @ cc-size @ u< and ;
: cc-row-clash? ( row1 row2 -- flag )
  cc-rb ! cc-ra ! 0
  2 0 do 2 0 do
    cc-ra @ j 2* cells + 2@ swap cc-rb @ i 2* cells + 2@ swap cc-clash? or
  loop loop ;
create cc-new-row 4 cells allot
: cc-row-set ( dl dh sl sh layer -- )
  cc-cur ! cc-new-row 3 cells + ! cc-new-row 2 cells + ! cc-new-row cell+ ! cc-new-row ! ;
: cc-full? ( -- flag ) cc-cur @ cc-count cc-slots @ 1- < 0= ;
: cc-clashes? ( -- flag )
  0 cc-cur @ cc-count 0 ?do
    cc-new-row cc-cur @ i cc-row-addr cc-row-clash? if drop -1 leave then
  loop ;
\ Would the row fit the layer (a free slot, no overlap)? Nothing is added.
: cc-fits? ( dl dh sl sh layer -- flag )
  cc-row-set cc-full? if 0 exit then cc-clashes? 0= ;
: cc-row ( dl dh sl sh layer -- slot )
  cc-row-set cc-full? if -8 throw then cc-clashes? if -9 throw then
  cc-new-row cc-cur @ dup cc-count cc-row-addr 4 cells cmove
  cc-cur @ cc-count 1 cc-cur @ 2 cells + +! ;
: cc-flush ( -- )
  cc-pending @ 0 ?do i cc-pending@ cell+ @ -1 = if -24 throw then loop
  cc-pending @ 0 ?do i cc-pending@ cc-write loop 0 cc-pending ! 0 cc-head ! 0 cc-seq# ! ;
: cc-finish ( entry -- )
  cc-sink @ if cc-start-cell ! exit then
  cc-stream-flush cc-clear-rows cc-link-row cc-slots @ 1- cc-row!
  cc-lbuf @ cc-dest ! cc-rows cc-slots @ cc-encode cc-lbuf @ cc-lbytes type ;
