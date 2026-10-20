\ SPDX-License-Identifier: MIT
\ Index-code layers and the emulator boot stream; control: copycode.vm1.backend.
\ Address fields are byte-sized (a multiple of 8), slots >= 8. Cells are
\ power-of-two bit ranges holding one layer; cell 0 is the entry layer.
\ A layer has slots-1 work rows and a link row; rows are dl dh sl sh.
\ Pending layers are encoded at cc-flush; a sequence ends at cc-flush.
\ THROW -24: invalid machine/field/unlinked; -9: overlap or put outside;
\ -8: capacity. Output goes to stdout with TYPE as it is produced.
decimal
variable cc-size variable cc-a variable cc-slots variable cc-cell-bits
variable cc-chunk variable cc-chunk-buf variable cc-lbuf variable cc-pool
variable cc-ebuf variable cc-dest
0 cc-pool !
create cc-rev 256 allot
: cc-rev-init 256 0 do
    0 8 0 do 2* j i rshift 1 and or loop cc-rev i + c!
  loop ;
cc-rev-init
: cc-inst ( -- n ) cc-a @ 4 * ;
: cc-layer-bits ( -- n ) cc-slots @ cc-inst * ;
: cc-lbytes ( -- n ) cc-layer-bits 8 / ;
: cc-stdin ( -- c ) cc-size @ 1+ ;
: cc-stdout ( -- c ) cc-size @ 2 + ;
: cc-bits ( u -- n ) 0 swap begin dup while 1 rshift swap 1+ swap repeat drop ;
: cc-numeric ( value nbytes addr -- )
  swap 0 ?do
    over i 4 < if i 8 * rshift 255 and cc-rev + c@ else drop 0 then
    over i + c!
  loop 2drop ;
: cc-field-check ( value -- value )
  cc-a @ 32 < if dup cc-a @ rshift if -24 throw then then ;
\ Encode count rows (4 cells each) padded with zero rows into cc-dest.
: cc-encode ( rows count -- )
  cc-dest @ cc-lbytes 0 fill
  0 ?do
    4 0 do
      dup j 4 * i + cells + @ cc-field-check
      cc-a @ 8 / cc-dest @ j 4 * i + cc-a @ 8 / * + cc-numeric
    loop
  loop drop ;
\ Stream state: chunk start byte (-1: none) and length.
variable cc-start variable cc-len
create cc-rows 32 cells allot
: cc-row! ( dl dh sl sh i -- ) 4 * cells cc-rows + >r
  r@ 3 cells + ! r@ 2 cells + ! r@ cell+ ! r> ! ;
: cc-clear-rows ( -- ) cc-rows 32 cells 0 fill ;
: cc-loader ( -- )
  cc-clear-rows cc-start @ 8 * dup cc-len @ 8 * + cc-stdin dup 0 cc-row!
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
  rot dup 7 and over cc-cell-bits @ u< or if -9 throw then
  dup 2 pick 8 * + cc-size @ u> if -9 throw then
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
\ Layer records: cell, next (-1 unlinked), count, rows.
96 constant cc-max-layers
: cc-record ( -- n ) cc-slots @ 1- 4 * 3 + cells ;
variable cc-pending variable cc-next-cell
create cc-seq-list 96 cells allot variable cc-seq# variable cc-seq-first
: cc-machine ( size slots cell-bits chunk-bytes -- )
  >r >r >r dup cc-bits r> r> r>
  ( size a slots cell chunk )
  2 pick 8 < 4 pick 8 mod or 5 pick 8 mod or if -24 throw then
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
  -1 cc-start ! 0 cc-len ! 0 cc-pending ! 2 cc-next-cell ! 0 cc-seq# ! ;
: cc-field ( cell slot f -- addr ) cc-a @ * swap cc-inst * + + ;
: cc-link-row ( target -- dl dh sl sh ) >r 0 cc-layer-bits r@ dup cc-layer-bits + r> drop ;
: cc-copy ( n dst src -- dl dh sl sh ) rot >r over r@ + swap dup r> + ;
: cc-out ( n src -- dl dh sl sh ) cc-stdout dup 2swap tuck + ;
: cc-builder ( first-cell -- ) cc-next-cell ! 0 cc-pending ! 0 cc-seq# ! ;
: cc-new-cell ( -- addr ) cc-next-cell @ dup 1+ cc-next-cell ! cc-cell-bits @ * ;
: cc-group ( k -- base )
  1 swap lshift dup 1- cc-next-cell @ + over negate and
  dup rot + cc-next-cell ! cc-cell-bits @ * ;
: cc-layer-cell ( layer -- cell ) @ ;
: cc-next! ( target layer -- ) cell+ ! ;
: cc-count ( layer -- n ) 2 cells + @ ;
: cc-row-addr ( layer i -- addr ) 4 * 3 + cells + ;
: cc-new-record ( cell -- layer )
  cc-pending @ cc-max-layers < 0= if -8 throw then
  cc-pool @ cc-pending @ cc-record * + tuck !
  -1 over cc-next! 0 over 2 cells + ! 1 cc-pending +! ;
: cc-lone ( -- layer ) cc-new-cell cc-new-record ;
: cc-seq ( first|-1 -- ) cc-seq-first ! 0 cc-seq# ! ;
: cc-seq@ ( i -- layer ) cells cc-seq-list + @ ;
: cc-last ( -- layer ) cc-seq# @ 1- cc-seq@ ;
: cc-layer ( -- layer )
  cc-seq# @ 0= cc-seq-first @ -1 <> and if cc-seq-first @ else cc-new-cell then
  cc-new-record
  cc-seq# @ if dup cc-layer-cell cc-last cc-next! then
  cc-seq# @ 96 < 0= if -8 throw then
  dup cc-seq# @ cells cc-seq-list + ! 1 cc-seq# +! ;
: cc-entry ( -- cell ) 0 cc-seq@ cc-layer-cell ;
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
: cc-row ( dl dh sl sh layer -- slot )
  cc-cur ! cc-new-row 3 cells + ! cc-new-row 2 cells + ! cc-new-row cell+ ! cc-new-row !
  cc-cur @ cc-count cc-slots @ 1- < 0= if -8 throw then
  cc-cur @ cc-count 0 ?do
    cc-new-row cc-cur @ i cc-row-addr cc-row-clash? if unloop -9 throw then
  loop
  cc-new-row cc-cur @ dup cc-count cc-row-addr 4 cells cmove
  cc-cur @ cc-count 1 cc-cur @ 2 cells + +! ;
: cc-encode-layer ( layer -- )
  dup cell+ @ -1 = if -24 throw then
  cc-clear-rows dup 3 cells + cc-rows 2 pick cc-count 4 * cells cmove
  cell+ @ cc-link-row cc-slots @ 1- cc-row!
  cc-ebuf @ cc-dest ! cc-rows cc-slots @ cc-encode ;
: cc-flush ( -- )
  cc-pending @ 0 ?do cc-pool @ i cc-record * + cell+ @ -1 = if -24 throw then loop
  cc-pending @ 0 ?do
    cc-pool @ i cc-record * + dup cc-encode-layer
    cc-layer-cell cc-ebuf @ cc-lbytes cc-put
  loop 0 cc-pending ! 0 cc-seq# ! ;
: cc-finish ( entry -- )
  cc-stream-flush cc-clear-rows cc-link-row cc-slots @ 1- cc-row!
  cc-lbuf @ cc-dest ! cc-rows cc-slots @ cc-encode cc-lbuf @ cc-lbytes type ;
