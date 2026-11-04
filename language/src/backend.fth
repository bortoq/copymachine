\ SPDX-License-Identifier: MIT
\ Index-code layers and the emulator boot stream; control: copycode.vm1.backend. Address fields are byte-sized, slots >= 8.
\ A cell is a power-of-two bit range holding one layer (cell 0: the entry); a layer has slots-1 work rows and a link row;
\ a row is dl dh sl sh. Errors are FC-REJECT codes (no exceptions): -24 invalid machine/field/unlinked; -9 overlap or put outside; -8 capacity. Output goes
\ to stdout (TYPE) or to the sink: the xt in lay-sink takes every put ( bit-address src n -- ) and lay-finish keeps the
\ entry in lay-start-cell (a kernel installs code in its own space so; lay-rev is then the identity).
decimal
\ A rejected program (18.21): FC-REJECT prints "error N at WORD" (the last word read) and halts the machine: BYE, on the host
\ the host's, in the compiler a generator that jumps to the halt cell. The program is not run; nothing is compiled further.
create fc-tok 4096 allot variable fc-tl
: fc-.n ( n -- )
  dup 0< if [char] - emit negate then
  dup 10 / ?dup if recurse then 10 mod [char] 0 + emit ;
: fc-reject ( code -- ) s" error " type fc-.n s"  at " type fc-tok fc-tl @ type 10 emit bye ;
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
\ The request block of the long copy of a program of the kernel (18.24): the bits LAY-REQ ... of the upper half of the data block
\ (the positions a program computes reach 2^28 + 31 bits at most): the header of the record LONG (LAY-REC bits; its first LAY-HDR
\ bits are op, chan, flags) and, right after it, LAY-CAP bits of the data. The position in the address space of the host (off) is
\ LAY-POS bits (HOST_POS_BITS of emulator/src/proto.def), LAY-CELLS cells of 32 bits, the least significant first; the record is
\ op 8, chan 32, flags 16, arg 32 (88 bits) and off.
128 constant lay-pos  lay-pos 5 rshift constant lay-cells
88 lay-pos + constant lay-rec  56 constant lay-hdr  65536 constant lay-cap
: lay-req ( -- at ) lay-size @ 1 rshift lay-size @ 3 rshift + 1024 + ;
: lay-bits ( u -- n ) 0 swap begin dup while 1 rshift swap 1+ swap repeat drop ;
: lay-numeric ( value nbytes addr -- )
  swap 0 ?do
    over i 4 < if i 3 lshift rshift 255 and lay-rev + c@ else drop 0 then
    over i + c!
  loop 2drop ;
: lay-numeric4 ( value addr -- )
  over 255 and lay-rev + c@ over c!  over 8 rshift 255 and lay-rev + c@ over 1+ c!
  over 16 rshift 255 and lay-rev + c@ over 2 + c!  swap 24 rshift 255 and lay-rev + c@ swap 3 + c! ;
: lay-field-check ( value -- value )
  lay-a @ 32 < if dup lay-a @ rshift if -24 fc-reject then then ;
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
  rot dup 7 and over lay-cell-bits @ u< or if -9 fc-reject then
  dup 2 pick 3 lshift + lay-size @ u> if -9 fc-reject then
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
\ Layer records: cell, next (-1 unlinked), count, rows. Pending records are a ring: a new record beyond
\ lay-max-layers first writes the oldest one (it must be linked).
128 constant lay-max-layers
: lay-record ( -- n ) lay-slots @ 1- 4 * 3 + cells ;
variable lay-pending variable lay-head variable lay-next-cell
variable lay-seq# variable lay-seq-first variable lay-seq-entry variable lay-seq-last
create lay-foff 32 cells allot
: lay-foff-init ( -- ) 8 0 do 4 0 do j lay-inst * i lay-a @ * + j 2 lshift i + cells lay-foff + ! loop loop ;
\ The buffers are fixed (the only machine is FC-INIT's: 32-bit fields, 8 slots, 1024-bit layers, chunk 4096): the chunk, two layers, the pool.
create lay-chunk-mem 4096 allot create lay-lbuf-mem 128 allot create lay-ebuf-mem 128 allot
create lay-pool-mem 15872 allot
: lay-bufs ( -- ) lay-chunk-mem lay-chunk-buf ! lay-lbuf-mem lay-lbuf ! lay-ebuf-mem lay-ebuf ! lay-pool-mem lay-pool ! ;
: lay-machine ( size slots cell-bits chunk-bytes -- )
  >r >r >r dup lay-bits r> r> r>
  ( size a slots cell chunk )
  lay-chunk ! lay-cell-bits ! lay-slots ! lay-a ! lay-size !
  lay-bufs
  -1 lay-start ! 0 lay-len ! 0 lay-pending ! 0 lay-head ! 2 lay-next-cell ! 0 lay-seq# ! lay-foff-init ;
: lay-field ( cell slot f -- addr ) swap 2 lshift + cells lay-foff + @ + ;
: lay-link-row ( target -- dl dh sl sh ) >r 0 lay-layer-bits r@ dup lay-layer-bits + r> drop ;
: lay-copy ( n dst src -- dl dh sl sh ) rot >r over r@ + swap dup r> + ;
: lay-out ( n src -- dl dh sl sh ) lay-stdout dup 2swap tuck + ;
: lay-builder ( first-cell -- ) lay-next-cell ! 0 lay-pending ! 0 lay-head ! 0 lay-seq# ! ;
: lay-new-cell ( -- addr ) lay-next-cell @ dup 1+ lay-next-cell ! lay-cell-bits @ * ;
\ The link bit selecting a branch target: both endpoints share it, so with a full layer targets are two cells apart.
: lay-branch-bit ( -- n ) lay-cell-bits @ lay-bits 1- lay-layer-bits lay-cell-bits @ < 0= - ;
: lay-branch-step ( -- n ) 1 lay-branch-bit lshift ;
: lay-group ( k -- base )
  1 swap lshift lay-branch-step lay-cell-bits @ / * dup 1- lay-next-cell @ + over / over *
  dup rot + lay-next-cell ! lay-cell-bits @ * ;
: lay-layer-cell ( layer -- cell ) @ ;
: lay-next! ( target layer -- ) cell+ ! ;
: lay-count ( layer -- n ) 2 cells + @ ;
: lay-row-addr ( layer i -- addr ) 2 lshift 3 + cells + ;
: lay-pending@ ( i -- layer ) lay-head @ + lay-max-layers 1- and lay-record * lay-pool @ + ;
: lay-encode-layer ( layer -- )
  dup cell+ @ -1 = if -24 fc-reject then
  lay-clear-rows dup 3 cells + lay-rows 2 pick lay-count 2 lshift cells cmove
  cell+ @ lay-link-row lay-slots @ 1- lay-row!
  lay-ebuf @ lay-dest ! lay-rows lay-slots @ lay-encode ;
\ lay-on-write: an xt ( layer -- ) that sees every written layer (0: none); the price of a word (14.11) is from them.
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
: lay-fits? ( dl dh sl sh layer -- flag )
  lay-row-set lay-full? if 0 exit then lay-clashes? 0= ;
: lay-row ( dl dh sl sh layer -- slot )
  lay-row-set lay-full? if -8 fc-reject then lay-clashes? if -9 fc-reject then
  lay-new-row lay-cur @ dup lay-count lay-row-addr 4 cells cmove
  lay-cur @ lay-count 1 lay-cur @ 2 cells + +! ;
: lay-flush ( -- )
  lay-pending @ 0 ?do i lay-pending@ cell+ @ -1 = if -24 fc-reject then loop
  lay-pending @ 0 ?do i lay-pending@ lay-write loop 0 lay-pending ! 0 lay-head ! 0 lay-seq# ! ;
: lay-finish ( entry -- )
  lay-sink @ if lay-start-cell ! exit then
  lay-stream-flush lay-clear-rows lay-link-row lay-slots @ 1- lay-row!
  lay-lbuf @ lay-dest ! lay-rows lay-slots @ lay-encode lay-lbuf @ lay-lbytes type ;
\ The word of disjointness (3.7.5, language/doc/isolation.md). DJ-PROVE ( first end -- flag ): from the layers of a
\ program as they stand in the space (cells first .. end - 1, read by DJ-READER) true if, in the four blocks of the
\ space (the program: code block 0, data block 2),
\ 1. every row is a no-op, a copy of two intervals of one length each inside one block of the program, or a channel
\    row (stdin into the data, the data into stdout);
\ 2. a copy into the layers (the patch of a field of another row at run time) writes inside one field, reads the field
\    it patches and shows, for any value of the low bits it writes (DJ-REACH), that the position stays in the block of
\    the constant above them (the block 0 or 2; the end of the reach lies in that block, and for a wide start, whose end
\    the program makes of it and the length, with the length of the row). A wide patch (more than DJ-NARROW bits from the start of the field: the program gives the
\    position, not an index of a table, stack or memory) gets from the program only the low bits of the field and stands
\    alone: no other row of its layer has a position in that block (DJ-WIDE). A narrow patch needs no more: its reach is
\    under 2^24 bits and an index only, and the place of rows in a layer is the scheduler's (it would reject programs);
\ 3. the long copy (18.24, 18.26): the request block LAY-REQ (LAY-REC + LAY-CAP bits, in the upper half of the data, where no
\    patch reaches) is written only by (a) the copy of the template from the code, a cell whose first byte is 6 (LONG), into
\    the header (its first LAY-HDR bits: op, chan, flags), (b) the rows of a value of 32 bits from the data below the block
\    into a cell of arg or off, (c) the copy into the window of the data after the record; their destinations are not
\    patched (DJ-DEST-OK?: no patch of a destination meets the block before or after it), nothing else (stdin, the
\    answer of SYS, another row) writes into the block; the only row into SYS copies the whole block and its layer follows,
\    in the cells, the layer of a copy of the template through layers that link to the next cell (DJ-CHAIN?); a row from SYS
\    writes into the data. The header holds zeros or the template whatever path is taken (nothing else writes it).
\ That the rows of a layer do not meet is kept by the scheduler (LAY-ROW, 3.7.2). On failure DJ-BAD-RULE is the number
\ of the rule and DJ-BAD-CELL the cell.
variable dj-reader variable dj-bad-cell variable dj-bad-rule
variable dj-bsh variable dj-csh variable dj-ssh variable dj-fsh
variable dj-first variable dj-end variable dj-pa variable dj-cb
variable dj-vdl variable dj-vdh variable dj-vsl variable dj-vsh
variable dj-tc variable dj-ts variable dj-tf variable dj-tb variable dj-tn variable dj-tk variable dj-vt
variable dj-blk variable dj-hb variable dj-he variable dj-hw variable dj-hz
variable dj-cur variable dj-hc variable dj-wb variable dj-we
create dj-pr 32 cells allot create dj-tr 32 cells allot
24 constant dj-narrow
create dj-seen 64 cells allot variable dj-nseen
: dj-get ( bit-address -- x ) dj-reader @ execute ;
: dj-fail ( rule -- ) dj-bad-rule @ if drop else dj-bad-rule ! then ;
: dj-blk? ( x -- n ) dj-bsh @ rshift ;
: dj-in? ( lo hi -- f )
  2dup u< 0= if 2drop 0 exit then
  1- dj-blk? swap dj-blk? over = >r dup 0= swap 2 = or r> and ;
: dj-meets? ( lo hi -- f ) \ [lo, hi) and the request block (the record and the window) have a bit in common
  dj-hb @ over u< 0= if 2drop 0 exit then drop dj-hz @ u< ;
: dj-row! ( slot -- ) \ the row in DJ-V.. into the array DJ-PA
  2 lshift cells dj-pa @ + >r dj-vdl @ r@ ! dj-vdh @ r@ cell+ ! dj-vsl @ r@ 2 cells + ! dj-vsh @ r> 3 cells + ! ;
: dj-row@ ( slot array -- ) \ the row of the array into DJ-V..
  swap 2 lshift cells + >r r@ @ dj-vdl ! r@ cell+ @ dj-vdh ! r@ 2 cells + @ dj-vsl ! r> 3 cells + @ dj-vsh ! ;
: dj-nop? ( -- f ) dj-vsl @ dj-vsh @ = dj-vsl @ lay-size @ u< and ;
: dj-load ( cb array -- )
  dj-pa ! dj-cb !
  lay-slots @ 0 ?do
    dj-cb @ i 2 lay-field dj-get dj-vsl ! dj-cb @ i 3 lay-field dj-get dj-vsh !
    dj-nop? if 0 dj-vdl ! 0 dj-vdh ! 0 dj-vsl ! 0 dj-vsh !
    else dj-cb @ i 0 lay-field dj-get dj-vdl ! dj-cb @ i 1 lay-field dj-get dj-vdh ! then
    i dj-row!
  loop ;
: dj-sys? ( -- f ) \ the row into SYS: the whole request block, nothing else
  dj-vsl @ dj-hb @ = dj-vsh @ dj-hz @ = and ;
: dj-chain? ( -- f ) \ the layer in DJ-CUR follows the layer of the last copy of the template (DJ-HC) in the cells
  dj-hc @ 0= if 0 exit then
  dj-hc @ dj-cur @ u< 0= if 0 exit then
  -1 dj-cur @ dj-hc @ ?do
    i dj-csh @ lshift lay-slots @ 1- 2 lay-field dj-get i 1+ dj-csh @ lshift = and
  loop ;
: dj-head? ( -- f ) \ the row that writes into the header: the copy of the template, a cell of the code that starts with 6
  dj-vdl @ dj-hb @ = dj-vdh @ dj-he @ = and dj-vsl @ dj-blk? 0= and dj-vsh @ 1- dj-blk? 0= and
  dj-vsh @ dj-vsl @ - lay-hdr = and dup if drop dj-vsl @ dj-get 255 and 6 = then ;
: dj-req-ok? ( -- f ) \ the other row that writes into the request block: a value (a cell of arg or off) or the window
  dj-vsl @ dj-blk? 2 = dj-vsh @ 1- dj-blk? 2 = and 0= if 0 exit then
  dj-vdh @ dj-vdl @ - dj-vsh @ dj-vsl @ - = 0= if 0 exit then
  dj-vdl @ dj-hw @ = dj-vdh @ dj-hz @ = and if -1 exit then
  dj-vdh @ dj-vdl @ - 32 = dj-vdl @ dj-he @ - 31 and 0= and
  dj-vdl @ dj-he @ u< 0= and dj-hw @ dj-vdh @ u< 0= and dj-hb @ dj-vsh @ u< 0= and ;
: dj-row-ok? ( -- f )
  dj-nop? if -1 exit then
  dj-vsl @ dj-vsh @ = if
    dj-vsl @ dup lay-stdin = swap lay-size @ = or dj-vdl @ dj-vdh @ dj-in? and
    dj-vdl @ dj-vdh @ dj-meets? 0= and
    exit
  then
  dj-vdl @ dj-vdh @ = if
    dj-vdl @ lay-size @ = if dj-sys? dj-chain? and 0= if 3 dj-fail then -1 exit then
    dj-vdl @ lay-stdout = dj-vsl @ dj-vsh @ dj-in? and exit
  then
  dj-vdl @ dj-vdh @ dj-meets? if
    dj-vdl @ dj-he @ u< dj-hb @ dj-vdh @ u< and
    if dj-head? if dj-cur @ dj-hc ! else 3 dj-fail then
    else dj-req-ok? 0= if 3 dj-fail then then
    -1 exit
  then
  dj-vdl @ dj-vdh @ dj-in? dj-vsl @ dj-vsh @ dj-in? and dj-vdh @ dj-vdl @ - dj-vsh @ dj-vsl @ - = and ;
: dj-in-blk? ( lo hi -- f )
  2dup u< 0= if 2drop 0 exit then
  over lay-size @ u< 0= if 2drop 0 exit then
  1- dj-blk? dj-blk @ = swap dj-blk? dj-blk @ = or ;
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
: dj-field ( f -- x ) \ field f of the row DJ-TS of the cell DJ-TC
  >r dj-tc @ dj-csh @ lshift dj-ts @ r> lay-field dj-get ;
: dj-dest-ok? ( -- f ) \ the patch of the destination (DJ-TF 0, 1) stays out of the request block: the row before it, and
  \ the reach of its start or, for a narrow patch of its end, of its end (a wide end is the sum of the start and the length)
  dj-tf @ 0= if dj-vt @ 1 dj-field else 0 dj-field dj-vt @ then 2dup dj-meets? if 2drop 0 exit then drop
  dj-tf @ 0= if drop dj-wb @ else dj-tk @ dj-narrow u> if drop -1 exit then then
  dj-we @ dj-meets? 0= ;
: dj-reach ( -- f ) \ the block of the field to patch and the end of the reach of its low DJ-TK bits; failed: rule 2
  dj-tf @ dj-field dj-vt !
  dj-vt @ dj-blk? dup dj-blk ! dup 0= swap 2 = or 0= if 2 dj-fail 0 exit then
  dj-vt @ 1 dj-tk @ lshift 1- invert and dup dj-wb ! 1 dj-tk @ lshift +
  dj-tk @ dj-narrow u> dj-blk @ and dj-tf @ 1 and 0= and if dj-tf @ 1+ dj-field dj-vt @ - + then
  dup dj-we ! dj-blk @ 1+ dj-bsh @ lshift swap u< if 2 dj-fail 0 exit then
  dj-tf @ 2 u< if dj-dest-ok? 0= if 3 dj-fail 0 exit then then
  -1 ;
: dj-wide ( -- )
  dj-seen? if exit then
  dj-reach 0= if exit then
  dj-tc @ dj-csh @ lshift dj-tr dj-load
  lay-slots @ 0 ?do
    i dj-ts @ = 0= if
      i dj-tr dj-row@ dj-nop? 0= if dj-touches? if 2 dj-fail then then
    then
  loop
  dj-seen! ;
: dj-near ( -- ) \ a narrow patch: its window of 2^DJ-NARROW bits at most is aligned, so it stays in the block of the constant above it
  dj-tf @ 2 u< if dj-reach drop exit then
  dj-tc @ dj-csh @ lshift dj-ts @ dj-tf @ lay-field dj-get dj-blk? dup 0= swap 2 = or 0= if 2 dj-fail then ;
: dj-patch ( -- )
  dj-vdl @ dup dj-csh @ rshift dj-tc !
  lay-cell-bits @ 1- and dup dj-ssh @ rshift dj-ts !
  dup lay-inst 1- and dj-fsh @ rshift dj-tf !
  lay-a @ 1- and dj-tb !
  dj-vdh @ dj-vdl @ - dj-tn !
  dj-tb @ dj-tn @ + dup dj-tk ! lay-a @ u> if 2 dj-fail exit then
  dj-tk @ lay-a @ = if 2 dj-fail exit then
  dj-tk @ dj-narrow u> if dj-wide else dj-near then ;
\ The rows of the layer at DJ-CB that are not no-ops, into DJ-PR (DJ-NN of them); the fields of a slot are 128 bits
\ apart, a field has 32 bits (lay-foff).
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
: dj-rows ( -- )
  dj-nn @ 0 ?do
    i dj-pr dj-row@
    dj-row-ok? if
      dj-vdl @ dj-lo @ u< 0= dj-vdl @ dj-hi @ u< and if dj-patch then
    else 1 dj-fail then
  loop ;
: dj-prove ( first end -- flag )
  dj-end ! dj-first ! 0 dj-bad-rule ! 0 dj-nseen ! 0 dj-hc !
  lay-req dj-hb ! lay-req lay-hdr + dj-he ! lay-req lay-rec + dj-hw ! lay-req lay-rec + lay-cap + dj-hz !
  lay-size @ lay-bits 3 - dj-bsh !
  lay-cell-bits @ lay-bits 1- dj-csh ! lay-inst lay-bits 1- dj-ssh ! lay-a @ lay-bits 1- dj-fsh !
  2 dj-csh @ lshift dj-lo ! lay-size @ 2 rshift dj-hi !
  dj-end @ dj-first @ ?do
    i dj-cur ! i dj-csh @ lshift dj-cb ! dj-pr dj-pa ! dj-scan dj-rows
    dj-bad-rule @ if i dj-bad-cell ! unloop 0 exit then
  loop -1 ;
