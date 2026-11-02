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
\ The word of disjointness (3.7.5, language/doc/isolation.md). DJ-PROVE ( first end -- flag ): from the layers
\ of a program as they stand in the space (the cells first .. end - 1, the 32 bits at a bit address read by
\ the word of DJ-READER) true if, in the four blocks of the space (the program: the code block 0 and the data
\ block 2),
\ 1. every row is a no-op, a copy of two intervals of one length, each inside one block of the program, or a
\    channel row (stdin into the data, the data into stdout);
\ 2. a copy into the layers (a row whose destination is a cell of the code block from the cell 2: the patch of a field of another
\    row at run time) writes inside one field, and a wide one (more than DJ-NARROW bits from the start of the
\    field: the position is the program's, not an index of a table, a stack or the memory, which the planner
\    places, 3.7.2) gets, from the program, only the low bits of the field: the bits above are the block of the
\    constant in the row, the end of the reach lies in that block (for the start of an interval in the data,
\    with the length of the interval above it), and no other row of the layer has a position in that block:
\    the row stands alone (the rows of a layer: DJ-SCAN; the layer of a patch: DJ-LOAD).
\ That the rows of a layer do not meet is kept by the scheduler that builds the layers (LAY-ROW, 3.7.2): the word
\ does not prove it. On failure DJ-BAD-RULE is the number of the rule and DJ-BAD-CELL the cell.
variable dj-reader variable dj-bad-cell variable dj-bad-rule
variable dj-bsh variable dj-csh variable dj-ssh variable dj-fsh
variable dj-first variable dj-end variable dj-pa variable dj-cb
variable dj-vdl variable dj-vdh variable dj-vsl variable dj-vsh
variable dj-tc variable dj-ts variable dj-tf variable dj-tb variable dj-tn variable dj-tk variable dj-vt
variable dj-blk
create dj-pr 32 cells allot create dj-tr 32 cells allot
24 constant dj-narrow
\ Wide patches proved already: cell, slot, field, bits.
create dj-seen 64 cells allot variable dj-nseen
: dj-get ( bit-address -- x ) dj-reader @ execute ;
: dj-fail ( rule -- ) dj-bad-rule @ if drop else dj-bad-rule ! then ;
: dj-blk? ( x -- n ) dj-bsh @ rshift ;
\ [lo, hi) is in one block of the program, the code block 0 or the data block 2.
: dj-in? ( lo hi -- f )
  2dup u< 0= if 2drop 0 exit then
  1- dj-blk? swap dj-blk? over = >r dup 0= swap 2 = or r> and ;
: dj-row! ( slot -- ) \ the row in DJ-V.. into the array DJ-PA
  2 lshift cells dj-pa @ + >r dj-vdl @ r@ ! dj-vdh @ r@ cell+ ! dj-vsl @ r@ 2 cells + ! dj-vsh @ r> 3 cells + ! ;
: dj-row@ ( slot array -- ) \ the row of the array into DJ-V..
  swap 2 lshift cells + >r r@ @ dj-vdl ! r@ cell+ @ dj-vdh ! r@ 2 cells + @ dj-vsl ! r> 3 cells + @ dj-vsh ! ;
\ A row with an empty source in the memory is a no-op: only its source is read.
: dj-nop? ( -- f ) dj-vsl @ dj-vsh @ = dj-vsl @ lay-size @ u< and ;
\ The layer at the bit address cb into the array: the four fields of every slot.
: dj-load ( cb array -- )
  dj-pa ! dj-cb !
  lay-slots @ 0 ?do
    dj-cb @ i 2 lay-field dj-get dj-vsl ! dj-cb @ i 3 lay-field dj-get dj-vsh !
    dj-nop? if 0 dj-vdl ! 0 dj-vdh ! 0 dj-vsl ! 0 dj-vsh !
    else dj-cb @ i 0 lay-field dj-get dj-vdl ! dj-cb @ i 1 lay-field dj-get dj-vdh ! then
    i dj-row!
  loop ;
\ Rule 1.
: dj-row-ok? ( -- f )
  dj-nop? if -1 exit then
  dj-vsl @ dj-vsh @ = if dj-vsl @ lay-stdin = dj-vdl @ dj-vdh @ dj-in? and exit then
  dj-vdl @ dj-vdh @ = if dj-vdl @ lay-stdout = dj-vsl @ dj-vsh @ dj-in? and exit then
  dj-vdl @ dj-vdh @ dj-in? dj-vsl @ dj-vsh @ dj-in? and dj-vdh @ dj-vdl @ - dj-vsh @ dj-vsl @ - = and ;
\ The interval [lo, hi) has a position in the block dj-blk (a channel has none).
: dj-in-blk? ( lo hi -- f )
  2dup u< 0= if 2drop 0 exit then
  over lay-size @ u< 0= if 2drop 0 exit then
  1- dj-blk? dj-blk @ = swap dj-blk? dj-blk @ = or ;
\ The row in DJ-V.. has a position in the block DJ-BLK.
: dj-touches? ( -- f ) dj-vdl @ dj-vdh @ dj-in-blk? dj-vsl @ dj-vsh @ dj-in-blk? or ;
: dj-seen? ( -- f ) \ the wide patch (DJ-TC .. DJ-TK) was proved
  0 dj-nseen @ 0 ?do
    i 2 lshift cells dj-seen + >r
    r@ @ dj-tc @ = r@ cell+ @ dj-ts @ = and r@ 2 cells + @ dj-tf @ = and r> 3 cells + @ dj-tk @ = and or
  loop ;
: dj-seen! ( -- )
  dj-nseen @ 16 = if 0 dj-nseen ! then
  dj-nseen @ 2 lshift cells dj-seen + >r dj-tc @ r@ ! dj-ts @ r@ cell+ ! dj-tf @ r@ 2 cells + ! dj-tk @ r> 3 cells + !
  1 dj-nseen +! ;
\ Rule 2 for the wide patch of the field DJ-TF of the row DJ-TS of the cell DJ-TC (DJ-TB, DJ-TN, DJ-TK the
\ start, the width and the end of the patch in the field): the field, then the layer.
: dj-wide ( -- )
  dj-seen? if exit then
  dj-tc @ dj-csh @ lshift dj-ts @ dj-tf @ lay-field dj-get dj-vt !
  dj-tk @ lay-a @ = if 2 dj-fail exit then
  dj-vt @ dj-blk? dup dj-blk ! dup 0= swap 2 = or 0= if 2 dj-fail exit then
  dj-vt @ 1 dj-tk @ lshift 1- invert and 1 dj-tk @ lshift +        ( the end of the reach )
  dj-tc @ dj-csh @ lshift dj-tr dj-load
  dj-ts @ dj-tr dj-row@
  dj-blk @ dj-tf @ 1 and 0= and if dj-vdh @ dj-vdl @ - dj-vsh @ dj-vsl @ - max + then
  dj-blk @ 1+ dj-bsh @ lshift swap u< if 2 dj-fail exit then
  lay-slots @ 0 ?do
    i dj-ts @ = 0= if
      i dj-tr dj-row@ dj-nop? 0= if dj-touches? if 2 dj-fail then then
    then
  loop
  dj-seen! ;
\ A row of the layer that writes into the layers.
: dj-patch ( -- )
  dj-vdl @ dup dj-csh @ rshift dj-tc !
  lay-cell-bits @ 1- and dup dj-ssh @ rshift dj-ts !
  dup lay-inst 1- and dj-fsh @ rshift dj-tf !
  lay-a @ 1- and dj-tb !
  dj-vdh @ dj-vdl @ - dj-tn !
  dj-tb @ dj-tn @ + dup dj-tk ! lay-a @ u> if 2 dj-fail exit then
  dj-tk @ dj-narrow u> if dj-wide then ;
\ The rows of the layer at the bit address DJ-CB that are not no-ops, into DJ-PR (DJ-NN of them). The fields
\ of a slot are at 128 bits from each other, a field has 32 bits (lay-foff, the geometry of the index code); a
\ no-op reads only its source.
variable dj-nn variable dj-lo variable dj-hi
: dj-scan ( -- )
  0 dj-nn !
  lay-slots @ 0 ?do
    dj-cb @ i 7 lshift + 64 + dup dj-get dj-vsl ! 32 + dj-get dj-vsh !
    dj-nop? 0= if
      dj-cb @ i 7 lshift + dup dj-get dj-vdl ! 32 + dj-get dj-vdh !
      dj-nn @ dj-row! 1 dj-nn +!
    then
  loop ;
\ Rules 1 and 2 for the rows of the layer.
: dj-rows ( -- )
  dj-nn @ 0 ?do
    i dj-pr dj-row@
    dj-row-ok? if
      dj-vdl @ dj-lo @ u< 0= dj-vdl @ dj-hi @ u< and if dj-patch then
    else 1 dj-fail then
  loop ;
: dj-prove ( first end -- flag )
  dj-end ! dj-first ! 0 dj-bad-rule ! 0 dj-nseen !
  lay-size @ lay-bits 3 - dj-bsh !
  lay-cell-bits @ lay-bits 1- dj-csh ! lay-inst lay-bits 1- dj-ssh ! lay-a @ lay-bits 1- dj-fsh !
  2 dj-csh @ lshift dj-lo ! lay-size @ 2 rshift dj-hi !
  dj-end @ dj-first @ ?do
    i dj-csh @ lshift dj-cb ! dj-pr dj-pa ! dj-scan dj-rows
    dj-bad-rule @ if i dj-bad-cell ! unloop 0 exit then
  loop -1 ;
