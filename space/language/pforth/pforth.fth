\ pForth on the language (16.1): the kernel of upstream pForth
\ (space/forth/third_party/pforth/csrc) as a program of the user of L0, 32-bit cells, no floating
\ point, as the host pforth32. stdin after the zero byte: system.fth, then the Forth input.
\ The C sources are the specification: names of pfcompil.c, primitives of pf_inner.c with their
\ numbers (the enum of pf_guts.h), the text interpreter and compiler of pfcompil.c, pf_words.c,
\ pf_text.c, the input and output of pf_io.c on the channels KEY and EMIT.
\ Addresses of pForth are addresses of the language: a fault of the language (@ ! C@ C! out of
\ the data, a misaligned cell, / by zero) is an exception of the language with its code; CATCH of
\ pForth catches it, else it ends the session as a fault stops the host pforth32.
\ As the port runtime/pforth/main.c the system is quiet: no "ok", no "redefined".
\ Differences from C, needed by the space: (SAVE-FORTH) keeps the image of the dictionary in memory
\ (system.fth ends with SAVE-FORTH); after BYE or a fault, if input remains, a new session starts
\ from that image (as pforth32 from its prepared dictionary, then AUTO.INIT). The end of input
\ ends QUIT. ALLOCATE takes memory from a pool by a bump pointer (FREE returns only the last block).

\ --- memory -------------------------------------------------------------------------------
create low 8 allot                    \ language addresses 0..7 stay zero (programs probe them)
create mem 270336 allot
mem constant v-context      mem 4 + constant v-state     mem 8 + constant v-base
mem 12 + constant v-byecode mem 16 + constant v-echo     mem 20 + constant v-tlevel
mem 24 + constant v-tstack  mem 28 + constant v-tflags   mem 32 + constant v-retcode
mem 36 + constant v-localxt mem 40 + constant v-hbase    mem 44 + constant v-hptr
mem 48 + constant v-hlimit  mem 52 + constant v-cbase    mem 56 + constant v-dp
mem 60 + constant v-climit  mem 64 + constant v-in       mem 68 + constant v-ntib
mem 72 + constant v-src     mem 76 + constant v-line     mem 80 + constant v-out
mem 84 + constant v-colon   mem 88 + constant v-stream   mem 92 + constant v-incl
mem 96 + constant v-heap    mem 100 + constant v-numq    mem 104 + constant v-accxt
mem 108 + constant v-quitxt
mem 2304 + constant d-base    mem 4416 + constant r-base   \ stacks of 512 cells, growing down
mem 4416 + constant tib       mem 4672 + constant scratch  mem 4968 + constant cntt-end
mem 4992 + constant fake      mem 5008 + constant incl-stack  \ 16 frames of 272 bytes
mem 9472 + constant h-start   mem 42240 + constant c-start
mem 140544 + constant pool    mem 206080 + constant pool-end  \ image of the dictionary after it
mem 206080 + constant img     64256 constant img-size
create prims 824 allot        create ptab 824 allot           \ token -> xt, token -> value
variable sp variable rp variable ip variable cur variable lp
variable rinit variable dinit variable exc variable eof variable saved variable img-h

\ --- helpers ------------------------------------------------------------------------------
: > ( a b -- f ) swap < ;
: u> ( a b -- f ) swap u< ;
: ?dup ( x -- x x | 0 ) dup if dup then ;
: +! ( n a -- ) dup @ rot + swap ! ;
: push ( x -- ) sp @ 4 - dup sp ! ! ;
: pop ( -- x ) sp @ dup 4 + sp ! @ ;
: 2pop ( -- a b ) pop pop swap ;
: t@ ( -- x ) sp @ @ ;
: t! ( x -- ) sp @ ! ;
: s@ ( n -- x ) cells sp @ + @ ;
: rpush ( x -- ) rp @ 4 - dup rp ! ! ;
: rpop ( -- x ) rp @ dup 4 + rp ! @ ;
: lit@ ( -- x ) ip @ dup 4 + ip ! @ ;
: branch ( -- ) ip @ dup @ + ip ! ;
: skip4 ( -- ) 4 ip +! ;
: code, ( x -- ) v-dp @ ! 4 v-dp +! ;
: m-throw ( code -- ) exc ! rinit @ rp ! dinit @ sp ! ;
: cmove ( src dst n -- ) 0 ?do over i + c@ over i + c! loop drop drop ;
: ccopy ( src dst n -- ) 3 + 2 rshift 0 ?do over i cells + @ over i cells + ! loop drop drop ;
: /str ( a n k -- a+k n-k ) swap over - >r + r> ;
: abs ( n -- u ) dup 0 < if 0 swap - then ;
: min ( a b -- m ) over over swap < if swap then drop ;
: lowc ( c -- c ) dup 65 - 26 u< if 32 + then ;
: upc ( c -- c ) dup 97 - 26 u< if 32 - then ;

\ --- output (pf_io.c ioEmit, ioType; pf_text.c) ------------------------------------------
: io-emit ( c -- ) 255 and dup emit 10 = if 0 v-out ! else 1 v-out +! then ;
: msg ( a n -- ) dup 0 > if 0 do dup i + c@ io-emit loop else drop then drop ;
: cr ( -- ) 10 io-emit ;
: unimpl ( a n -- ) msg s" is unimplemented!" msg cr ;
: udivmod ( u b -- r q )
  over 0 < 0= if over over / >r r@ * - r> exit then
  swap over over 1 rshift swap / 1 lshift >r r@ 2 pick * -
  over over swap u< 0= if over - r> 1+ >r then swap drop r> ;
variable nt-b variable nt-neg variable nt-min
: n>text ( n base signed min -- a n ) \ ConvertNumberToText
  nt-min ! swap nt-b ! 0 nt-neg ! if dup 0 < if -1 nt-neg ! 0 swap - then then
  cntt-end swap
  begin dup 0= 0= nt-min @ 0 > or while
    -1 nt-min +! nt-b @ udivmod >r dup 10 < if 48 else 55 then +
    swap 1- dup >r c! r> r>
  repeat drop nt-neg @ if 1- 45 over c! then cntt-end over - ;
: dot ( n -- ) v-base @ -1 1 n>text msg 32 io-emit ;
: dothex ( n -- ) 16 0 1 n>text msg 32 io-emit ;
: dots ( -- ) s" Stack<" msg v-base @ 10 -1 1 n>text msg s" > " msg
  d-base sp @ - dup 0 < if drop s" UNDERFLOW!" msg else
    2 rshift 0 ?do d-base i 1+ cells - @ v-base @ dup 10 = 1 n>text msg 32 io-emit loop
  then cr ;

\ --- input (ioKey, ioAccept on the channel KEY; 0 is the end of input) --------------------
: key-in ( -- c ) key dup 0= if drop -1 -1 eof ! then ;
: accept ( a max -- n )
  0 begin over over > while
    key-in dup 0 < if drop dup 0= if drop drop drop -1 exit then swap drop swap drop exit then
    dup 13 = over 10 = or if drop swap drop swap drop exit then
    dup 8 = over 127 = or if drop dup 0 > if 8 io-emit 32 io-emit 8 io-emit 1- then
    else 3 pick 2 pick + c! 1+ then
  repeat swap drop swap drop ;

\ --- the inner interpreter (pfCatch of pf_inner.c), registers in memory --------------------
: inner ( token -- )
  begin
    begin dup 206 u< 0= while ip @ rpush v-cbase @ + ip ! lit@ repeat
    dup cur ! cells prims + @ execute
    ip @ if lit@ else cur @ then
    rp @ rinit @ < 0=
  until drop ;
: pfcatch ( xt -- code )
  rinit @ >r dinit @ >r exc @ >r ip @ >r lp @ >r
  rp @ rinit ! sp @ dinit ! 0 exc ! 0 ip ! 0 lp !
  inner exc @ r> lp ! r> ip ! r> exc ! r> dinit ! r> rinit ! ;

\ --- parsing (pf_words.c ffSkip, ffScan, Word, ffNumberQ) ----------------------------------
variable sc-c
: blank? ( c -- f ) dup 32 = swap 9 = or ;
: skip ( a n c -- a n ) 255 and sc-c !
  begin dup 0 > if over c@ sc-c @ 32 = if blank? else sc-c @ = then else 0 then
  while 1 /str repeat ;
: scan ( a n c -- a n ) 255 and sc-c !
  begin dup 0 > if over c@ sc-c @ 32 = if dup blank? over 13 = or swap 10 = or
  else sc-c @ = then 0= else 0 then while 1 /str repeat ;
variable wd-n1 variable wd-n2 variable wd-up
: word ( c up -- $a ) \ Word: the result in gScratch, upper case if up
  wd-up ! >r v-src @ v-in @ + v-ntib @ v-in @ - dup wd-n1 !
  r@ skip dup wd-n2 ! over swap r> scan swap drop
  wd-n2 @ over - rot swap
  dup 0 > if dup scratch c! 0 do dup i + c@ wd-up @ if upc then scratch 1+ i + c! loop
  else drop 0 scratch c! then drop
  wd-n1 @ swap - 1+ v-in +! scratch ;
: digit ( c -- n ) dup 48 - dup 10 u< if swap drop exit then drop
  65 - dup 6 u< if 10 + else drop -1 then ;
variable nq-b variable nq-s
: numq ( $a -- n 1 | 0 )
  v-base @ nq-b ! 0 nq-s ! dup 1+ swap c@
  over c@ dup 35 = if drop 10 nq-b ! 1 /str else dup 36 = if drop 16 nq-b ! 1 /str else
  dup 37 = if drop 2 nq-b ! 1 /str else 39 = if dup 3 = if over 2 + c@ 39 = if
  drop 1+ c@ 1 exit then then then then then then
  over c@ 45 = if -1 nq-s ! 1 /str then
  dup 0 < if drop 0 then 0 swap 0 ?do
    over i + c@ digit dup 0 < over nq-b @ < 0= or if drop drop drop 0 unloop exit then
    swap nq-b @ * +
  loop swap drop nq-s @ if 0 swap - then 1 ;

\ --- dictionary (pfcompil.c) ---------------------------------------------------------------
: nfa>prev ( nfa -- nfa | 0 ) 8 - @ dup if v-hbase @ + then ;
: text=ci ( a1 a2 n -- f )
  0 ?do over i + c@ lowc over i + c@ lowc = 0= if drop drop 0 unloop exit then loop drop drop -1 ;
variable fn-w variable fn-len
: find-nfa ( $w -- nfa 1 | nfa -1 | $w 0 ) \ ffFindNFA
  dup fn-w ! c@ 31 and fn-len ! v-context @
  begin
    dup c@ 63 and fn-len @ = if
      dup 1+ fn-w @ 1+ fn-len @ text=ci if dup c@ 64 and if 1 else -1 then exit then
    then nfa>prev dup 0=
  until drop fn-w @ 0 ;
: ffind ( $w -- xt f | $w 0 ) find-nfa dup if swap 4 - @ swap then ;
: dic-entry ( xt $name flags -- ) \ CreateDicEntry
  >r >r v-hptr @ v-context @ dup if v-hbase @ - then over !
  swap over 4 + ! 8 + dup v-context !
  r> over over c@ 1+ dup >r cmove dup r> + swap dup c@ r> or swap c!
  begin dup 3 and while 0 over c! 1+ repeat v-hptr ! ;
: room? ( -- f ) \ ffCheckDicRoom
  v-hlimit @ v-hptr @ - 400 < if s" Error in ffCheckDicRoom - no room left in header space" msg cr -1 exit then
  v-climit @ v-dp @ - 400 < if s" Error in ffCheckDicRoom - no room left in code space" msg cr -1 exit then 0 ;
: sec-header ( $name -- ) \ ffCreateSecondaryHeader
  room? if drop exit then
  v-dp @ 3 + -4 and v-dp ! v-dp @ v-cbase @ - swap 32 dic-entry ;
: finish ( -- ) 0 code, v-context @ dup c@ 223 and swap c! ;
: string-defer ( xt $name -- ) sec-header 45 code, code, finish ;
: colon ( -- ) d-base sp @ - v-colon ! 32 -1 word dup c@ if sec-header 1 v-state ! else drop then ;
: semicolon ( -- code )
  0 v-state ! v-colon @ dup d-base sp @ - = 0= swap -400 = 0= and if -257 else finish 0 then
  -400 v-colon ! ;
: dic-records ( a n -- ) \ pfBuildDictionary: "id name ...", +256 immediate, +512 deferred
  begin 32 skip dup 0 > while
    32 skip over >r 32 scan r> 2 pick over - 0 swap 0 ?do 10 * over i + c@ 48 - + loop
    swap drop >r 32 skip over >r 32 scan r> 2 pick over -
    dup scratch c! scratch 1+ swap cmove
    r> dup 512 and if 511 and scratch string-defer else
    dup 256 and if 255 and scratch 64 dic-entry else scratch 0 dic-entry then then
  repeat drop drop ;
: c>f ( a n -- $a ) dup scratch c! scratch 1+ swap cmove scratch ;
: find-c ( a n -- xt ) c>f ffind drop ;

\ --- text interpreter (pfcompil.c) -------------------------------------------------------
: fcoe ( $w -- code ) \ FindAndCompileOrExecute
  dup ffind ?dup if rot drop -1 = v-state @ and if code, 0 else pfcatch then exit then
  drop dup push v-numq @ pfcatch ?dup if swap drop exit then
  pop dup 1 = if drop drop v-state @ if 89 code, pop code, then 0 exit then
  2 = if drop v-state @ if 5 code, pop pop swap code, code, then 0 exit then
  dup 1+ swap c@ msg s"   ? - unrecognized word!" msg cr -13 ;
: interpret ( -- code ) \ ffInterpret
  begin v-in @ v-ntib @ < while
    32 0 word dup c@ if
      0 v-localxt @ if over push v-localxt @ pfcatch ?dup if >r drop drop r> 0 v-state ! exit then
      drop pop then
      0= if fcoe ?dup if 0 v-state ! exit then else drop then
    else drop then
  repeat 0 ;
: ok? ( -- code ) d-base sp @ - 0 < if -4 else 0 then ;
: refill ( -- n ) \ ffRefill: 1 a line, 0 end of a file, < 0 an error
  0 v-in ! v-stream @ if s" sdInputChar" unimpl 0 0
  else v-src @ push 256 push v-accxt @ pfcatch ?dup if exit then
    pop dup 0 < if exit then 1 then
  swap v-ntib ! 1 v-line +!
  v-echo @ v-ntib @ 0 > and if v-src @ v-ntib @ msg cr then ;
: outer ( -- code ) \ ffOuterInterpreterLoop
  begin refill dup 0 > while drop interpret ?dup if exit then ok? ?dup if exit then repeat ;
: push-stream ( id -- code ) \ ffPushInputStream
  v-incl @ 16 < 0= if drop s" ffPushInputStream: max depth exceeded." msg cr -1 exit then
  v-incl @ 272 * incl-stack + v-stream @ over ! v-in @ over 4 + ! v-line @ over 8 + !
  v-ntib @ over 12 + ! v-ntib @ dup 0 > swap 255 < and if tib over 16 + v-ntib @ 1+ cmove then
  drop 1 v-incl +! v-stream ! 0 v-line ! 0 ;
: pop-stream ( -- id ) \ ffPopInputStream
  v-stream @ v-incl @ if -1 v-incl +! v-incl @ 272 * incl-stack +
    dup @ v-stream ! dup 4 + @ v-in ! dup 8 + @ v-line ! dup 12 + @ v-ntib !
    v-ntib @ dup 0 > swap 255 < and if dup 16 + tib v-ntib @ 1+ cmove then drop then ;
: include-file ( fid -- code ) \ ffIncludeFile
  push-stream ?dup if exit then outer dup if
    s" INCLUDE error on line #" msg v-line @ dot s" , level = " msg v-incl @ dot cr
    v-ntib @ 0 ?do v-src @ i + c@ dup 9 = if drop 32 then io-emit loop cr
    v-in @ 1- dup 0 > if 0 do 94 io-emit loop else drop then cr
  then pop-stream drop s" sdCloseFile" unimpl ;
: report ( code -- ) \ pfReportThrow
  dup -1 = over -2 = or if s" ABORT" else dup -3 = if s" Stack overflow!" else
  dup -4 = if s" Stack underflow!" else dup -14 = if s" Executing a compile-only word!" else
  dup -45 = if s" Float Stack underflow!" else dup -13 = if s" Undefined word!" else
  dup -22 = if s" Conditional control structure mismatch!" else
  dup -256 = over -56 = or if drop exit else
  dup -257 = if s" Stack depth changed between : and ; . Probably unbalanced conditional!" else
  dup -258 = if s" Not a DEFERred word!" else s" Unrecognized throw code!"
  then then then then then then then then then then
  rot s" THROW code = " msg dot cr msg cr ;
: reset-task ( -- ) \ pfResetForthTask
  0 v-stream ! d-base sp ! r-base rp ! v-ntib @ v-in ! 0 v-state ! ;
: quit ( -- ) \ pfQuit; the end of input ends it
  begin
    outer dup 0= if drop ok? then
    ?dup if dup -256 = eof @ or if drop exit then
      dots report begin pop-stream ?dup while drop s" sdCloseFile" unimpl
        v-incl @ 0= if 0 v-stream ! then repeat reset-task
    else eof @ if exit then then
  again ;

\ --- primitives (pf_inner.c), token in CUR ------------------------------------------------
: p-bad s" pfCatch: Unrecognised token = 0x" msg cur @ dothex s"  at 0x" msg ip @ dothex cr
  0 ip ! rinit @ rp ! ;
: p-push cur @ cells ptab + @ push ;
: p-exit rpop ip ! ;
: p-1- t@ 1- t! ;
: p-1+ t@ 1+ t! ;
: p-2dup 1 s@ push 1 s@ push ;
: p-2lit pop pop 5 code, swap code, code, ;
: p-2lit-p lit@ lit@ push push ;
: p-2- t@ 2 - t! ;
: p-2over 3 s@ push 3 s@ push ;
: p-2+ t@ 2 + t! ;
: p-2swap pop pop pop pop >r >r push push r> r> push push ;
: p-2r@ rp @ dup 4 + @ push @ push ;
: p-2r> rpop rpop push push ;
: p-2>r pop pop rpush rpush ;
: p-accept pop pop swap accept push ;
: p-alit pop v-cbase @ - 15 code, code, ;
: p-alit-p lit@ v-cbase @ + push ;
: valid? ( a -- f ) 4 - dup @ swap -1474605719 xor = ;
: alloc-mem ( n -- a | 0 ) \ pfAllocMem, the cell of the size before
  dup 0 > 0= if drop 0 exit then 4 + dup 15 + -16 and
  dup pool-end v-heap @ - u> if drop drop 0 exit then
  v-heap @ dup >r + v-heap ! r@ ! r> 4 + ;
: free-mem ( a -- ) 4 - dup dup @ 15 + -16 and + v-heap @ = if v-heap ! else drop then ;
: p-allocate pop dup 4 u< if drop 4 then 4 + alloc-mem ?dup
  if dup dup -1474605719 xor swap ! 4 + push 0 push else 0 push -1 push then ;
: p-and 2pop and push ;
: p-arshift 2pop over 0 < if swap -1 xor swap rshift -1 xor else rshift then push ;
: p-bail s" Emergency exit." msg cr 1 throw ;
: p-branch branch ;
: p-bye cr -256 m-throw ;
: p-catch pop rinit @ >r dinit @ >r exc @ >r ip @ >r lp @ >r rp @ >r sp @ >r
  ['] pfcatch catch ?dup if dup 1 = if throw then r> sp ! r> rp ! else r> drop r> drop then
  r> lp ! r> ip ! r> exc ! r> dinit ! r> rinit ! push ;
: p-cells t@ cells t! ;
: p-c@ t@ c@ t! ;
: p-cmove pop pop pop rot >r swap r> cmove ;
: p-cmove> pop pop pop rot >r swap r>
  begin dup while 1- >r over r@ + c@ over r@ + c! r> repeat drop drop drop ;
: p-colon colon ;
: p-colon-p pop pop 0 dic-entry ;
: sx ( c -- c ) dup 127 > if 256 - then ;
variable c-a1 variable c-n1 variable c-a2 variable c-n2
: p-compare pop c-n2 ! pop c-a2 ! pop c-n1 ! pop c-a1 !
  c-n1 @ c-n2 @ min dup 0 > if 0 do
    c-a2 @ i + c@ sx c-a1 @ i + c@ sx - ?dup if 0 > if -1 else 1 then push unloop exit then
  loop else drop then
  c-n1 @ c-n2 @ < if -1 else c-n2 @ c-n1 @ < if 1 else 0 then then push ;
: p-= 2pop = push ;
: p-> 2pop > push ;
: p-< 2pop < push ;
: p-<> 2pop = 0= push ;
: p-u> 2pop u> push ;
: p-u< 2pop u< push ;
: p-0= t@ 0= t! ;
: p-0> t@ 0 > t! ;
: p-0< t@ 0 < t! ;
: p-0<> t@ 0= 0= t! ;
: p-cr cr ;
: p-create 32 -1 word dup c@ if sec-header 42 code, 0 code, finish else drop then ;
: p-create-p ip @ 8 + push ;
: p-c! pop pop swap c! ;
: p-d+ pop pop pop pop >r rot + swap r> over + dup push swap u< - push ;
: p-d- pop pop pop pop >r rot - swap r> dup 2 pick - push swap u< + push ;
variable ua variable ub
: um* ( a b -- lo hi ) ub ! ua !
  ua @ 65535 and ub @ 65535 and * ua @ 65535 and ub @ 16 rshift *
  ua @ 16 rshift ub @ 65535 and * ua @ 16 rshift ub @ 16 rshift *
  over 16 rshift + 2 pick 16 rshift + >r
  65535 and swap 65535 and + over 16 rshift +
  dup 16 rshift r> + >r 16 lshift swap 65535 and or r> ;
: p-um* 2pop um* swap push push ;
: p-m* 2pop over over xor 0 < >r abs swap abs um* r>
  if swap -1 xor 1+ swap -1 xor over 0= if 1+ then then swap push push ;
variable dl variable dh variable bl2 variable bh2 variable dq variable xah
: dult ( -- f ) bh2 @ dh @ u< if 0 exit then bh2 @ dh @ = if dl @ bl2 @ u< exit then -1 ;
: p-um/mod pop bh2 ! pop dh ! pop dl ! 0 bl2 ! 0 dq !
  32 0 do dult 0= if dl @ bl2 @ u< dh @ bh2 @ - + dh ! dl @ bl2 @ - dl ! dq @ 1 or dq ! then
    dq @ 1 lshift dq ! bl2 @ 1 rshift bh2 @ 31 lshift or bl2 ! bh2 @ 1 rshift bh2 !
  loop dult 0= if dl @ bl2 @ - dl ! dq @ 1 or dq ! then dl @ push dq @ push ;
: p-mu/mod pop bl2 ! pop dh ! pop dl ! 0 xah ! 0 ua ! 0 dq !
  64 0 do bl2 @ xah @ u> 0= if xah @ bl2 @ - xah ! dq @ 1 or dq ! then
    ua @ 1 lshift dq @ 31 rshift or ua ! dq @ 1 lshift dq !
    xah @ 1 lshift dh @ 31 rshift or xah ! dh @ 1 lshift dl @ 31 rshift or dh ! dl @ 1 lshift dl !
  loop bl2 @ xah @ u> 0= if xah @ bl2 @ - xah ! dq @ 1 or dq ! then
  xah @ push dq @ push ua @ push ;
: p-defer 32 -1 word dup c@ if 131 swap string-defer else drop then ;
: p-noop ;
: p-depth d-base sp @ - 4 / push ;
: p-/ 2pop / push ;
: p-. pop dot ;
: p-.s dots ;
: p-do pop rpush pop rpush ;
: p-drop pop drop ;
: p-dump pop pop swap cr 15 + 16 / dup 0 > if 0 do
    dup 16 0 8 n>text msg s" : " msg
    16 0 do dup i + c@ 16 0 2 n>text msg 32 io-emit loop 32 io-emit
    16 0 do dup i + c@ dup 32 < over 125 > or if drop 46 then io-emit loop
    cr 16 +
  loop else drop then drop ;
: p-dup t@ push ;
: p-emit pop io-emit ;
: p-?error pop pop if m-throw else drop then ;
: p-execute ip @ rpush pop dup 206 u< if fake ! fake ip ! else v-cbase @ + ip ! then ;
: p-@ t@ @ t! ;
: long-name ( -- ) s" Filename too large for name buffer." msg cr ;
: p-fopen pop drop pop pop drop 254 < if s" sdOpenFile" unimpl 0 push -1 push
  else long-name 0 push -2 push then ;
: p-fdelete pop pop drop 254 < if s" sdDeleteFile" unimpl -1 else long-name -2 then push ;
: p-fclose pop drop s" sdCloseFile" unimpl 0 push ;
: p-fread pop drop pop pop drop if s" sdReadFile" unimpl then 0 push 0 push ;
: p-fsize pop drop s" sdTellFile" unimpl s" sdSeekFile" unimpl s" sdTellFile" unimpl
  s" sdSeekFile" unimpl 0 push 0 push 0 push ;
: p-fwrite pop drop pop pop drop dup if s" sdWriteFile" unimpl -3 else 0 then swap drop push ;
: p-frepos pop drop pop pop drop if -3 else s" sdSeekFile" unimpl 0 then push ;
: p-fpos pop drop s" sdTellFile" unimpl 0 push 0 push 0 push ;
: p-fbin t@ 8 or t! ;
: p-fflush pop drop 0 push ;
: p-frename pop pop drop drop s" sdRenameFile" unimpl -1 push ;
: p-fresize pop drop pop pop drop drop s" sdResizeFile" unimpl -74 push ;
: p-fill pop pop pop swap 0 ?do over over i + c! loop drop drop ;
: p-find pop ffind swap push push ;
: p-findnfa pop find-nfa swap push push ;
: p-free pop ?dup 0= if s" FREE passed NULL!" msg cr -2 push exit then
  dup valid? 0= if drop -2 push exit then 4 - -559038737 over ! free-mem 0 push ;
: p-here v-dp @ push ;
: p-numq pop numq dup if swap push then push ;
: p-i rp @ 4 + @ push ;
: p-include pop include-file ?dup if m-throw then ;
: p-j rp @ 12 + @ push ;
: p-key key-in dup push 4 = if -256 m-throw then ;
: p-leave rpop rpop drop drop branch ;
: p-literal pop 89 code, code, ;
: p-lit lit@ push ;
: p-loadsys s" Load system.fth" msg cr s" sdOpenFile" unimpl s" system.fth could not be opened!" msg cr ;
: p-lentry pop lp @ rpush rp @ lp ! rp @ over cells - dup rp ! swap 0 ?do pop over ! 4 + loop drop ;
: p-lexit lp @ rp ! rpop lp ! ;
: p-lfetch t@ cells lp @ swap - @ t! ;
: p-lfetchn lp @ cur @ 94 - cells - @ push ;
: p-lstore pop cells lp @ swap - pop swap ! ;
: p-lstoren pop lp @ cur @ 104 - cells - ! ;
: p-lplus pop cells lp @ swap - pop swap +! ;
: p-loop rpop rpop 1+ over over = if drop drop skip4 else rpush rpush branch then ;
: p-lshift 2pop lshift push ;
: p-max 2pop over over < if swap then drop push ;
: p-min 2pop over over > if swap then drop push ;
: p-- 2pop - push ;
: p-prevname t@ nfa>prev t! ;
: p-name> t@ 4 - @ t! ;
: p-or 2pop or push ;
: p-over 1 s@ push ;
: p-pick pop s@ push ;
: p-+ 2pop + push ;
: p-+loop rpop rpop pop >r over over swap - dup r@ + over xor swap r@ xor and 0 <
  if drop drop r> drop skip4 else r> + rpush rpush branch then ;
: p-+! pop pop swap +! ;
: p-?do pop pop over over = if drop drop branch else swap rpush rpush skip4 then ;
: p-?dup t@ ?dup if push then ;
: p-0push 0 push ;
: p-quit -56 m-throw ;
: p-refill refill 0 > push ;
: p-resize pop pop dup valid? 0= if push drop -3 push exit then
  over 4 + alloc-mem ?dup 0= if push drop -4 push exit then
  >r 4 - dup r@ 3 pick 4 + cmove r@ dup -1474605719 xor swap !
  -559038737 over ! free-mem drop r> 4 + push 0 push ;
: p-line@ v-line @ push ;
: p-roll pop dup s@ >r begin dup while dup 1- s@ over cells sp @ + ! 1- repeat drop r> t! ;
: p-rot pop pop pop >r push push r> push ;
: p-rp@ rp @ push ;
: p-rp! pop rp ! ;
: p-rshift 2pop rshift push ;
: p-rdrop rpop drop ;
: p-r@ rp @ @ push ;
: p-r> rpop push ;
: save-image ( -- err ) \ (SAVE-FORTH): the variables, the names and the code into IMG
  v-hptr @ v-hbase @ - dup img-h ! v-dp @ v-cbase @ - + 260 + img-size > if -1 exit then
  mem img 256 ccopy v-hbase @ img 256 + img-h @ ccopy
  v-cbase @ img 256 + img-h @ + v-dp @ v-cbase @ - ccopy -1 saved ! 0 ;
: restore ( -- ) img mem 256 ccopy img 256 + v-hbase @ img-h @ ccopy
  img 256 + img-h @ + v-cbase @ v-dp @ v-cbase @ - ccopy ;
: p-save pop pop pop pop drop drop drop drop save-image push ;
: p-line! pop v-line ! ;
: p-scan pop pop pop rot rot swap scan swap push push ;
: p-semicolon semicolon ?dup if m-throw then ;
: p-skip pop pop pop rot rot swap skip swap push push ;
: p-source v-src @ push v-ntib @ push ;
: p-source-id v-stream @ push ;
: p-pop-id pop-stream push ;
: p-push-id pop push-stream ?dup if m-throw then ;
: p-set-source pop v-ntib ! pop v-src ! ;
: p-sp@ sp @ push ;
: p-sp! pop sp ! ;
: p-! pop pop swap ! ;
: p-swap pop pop swap push push ;
: p-test1 17 push 34 push 51 push ;
: p-tick 32 -1 word dup ffind ?dup if drop swap drop push else
  drop s" ' could not find " msg dup 1+ swap c@ msg cr -13 m-throw then ;
: p-* 2pop * push ;
: p->r pop rpush ;
: p-type pop pop swap msg ;
: p-word t@ -1 word t! ;
: p-w@ t@ dup c@ swap 1+ c@ 8 lshift or t! ;
: p-w! pop pop swap over over c! swap 8 rshift swap 1+ c! ;
: p-xor 2pop xor push ;
: p-0branch pop if skip4 else branch then ;
: p-throw pop ?dup if m-throw then ;
: p-interpret interpret ?dup if m-throw then ;
: p-sleep -2147483638 t! ;

\ --- tables, start, sessions ---------------------------------------------------------------
: e ( xt id -- ) cells prims + ! ;
: pv ( value id -- ) dup cells ptab + rot swap ! ['] p-push swap e ;
: init-tables ( -- )
  206 0 do ['] p-bad i e loop
  ['] p-exit 0 e ['] p-1- 1 e ['] p-1+ 2 e ['] p-2dup 3 e ['] p-2lit 4 e ['] p-2lit-p 5 e
  ['] p-2- 6 e ['] p-2over 7 e ['] p-2+ 8 e ['] p-2swap 9 e ['] p-2r@ 10 e ['] p-2r> 11 e
  ['] p-2>r 12 e ['] p-accept 13 e ['] p-alit 14 e ['] p-alit-p 15 e ['] p-allocate 16 e
  ['] p-and 17 e ['] p-arshift 18 e ['] p-bail 19 e 12 20 pv ['] p-branch 21 e ['] p-bye 22 e
  ['] p-c@ 24 e ['] p-cmove 25 e ['] p-cmove> 26 e ['] p-colon 27 e ['] p-colon-p 28 e
  ['] p-compare 29 e ['] p-= 30 e ['] p-> 31 e ['] p-< 32 e ['] p-<> 33 e ['] p-u> 34 e
  ['] p-u< 35 e ['] p-0= 36 e ['] p-0> 37 e ['] p-0< 38 e ['] p-0<> 39 e ['] p-cr 40 e
  ['] p-create 41 e ['] p-create-p 42 e ['] p-c! 43 e ['] p-defer 44 e ['] p-noop 45 e
  ['] p-depth 46 e ['] p-/ 47 e ['] p-. 48 e ['] p-.s 49 e ['] p-do 50 e ['] p-drop 51 e
  ['] p-dump 52 e ['] p-dup 53 e ['] p-d- 54 e ['] p-m* 55 e ['] p-mu/mod 56 e ['] p-d+ 57 e
  ['] p-um/mod 58 e ['] p-um* 59 e ['] p-emit 61 e 10 62 pv ['] p-?error 63 e
  ['] p-execute 64 e ['] p-@ 65 e ['] p-fclose 66 e ['] p-fopen 67 e ['] p-fopen 68 e
  ['] p-fpos 69 e ['] p-fread 70 e ['] p-frepos 71 e 0 72 pv 1 73 pv ['] p-fsize 74 e
  ['] p-fwrite 75 e ['] p-fill 76 e ['] p-find 77 e ['] p-findnfa 78 e ['] p-noop 79 e
  ['] p-free 80 e ['] p-here 81 e ['] p-numq 82 e ['] p-i 83 e ['] p-include 84 e ['] p-j 85 e
  ['] p-key 86 e ['] p-leave 87 e ['] p-literal 88 e ['] p-lit 89 e ['] p-loadsys 90 e
  v-localxt 91 pv ['] p-lentry 92 e ['] p-lexit 93 e ['] p-lfetch 94 e
  103 95 do ['] p-lfetchn i e loop ['] p-lplus 103 e ['] p-lstore 104 e
  113 105 do ['] p-lstoren i e loop ['] p-loop 113 e ['] p-lshift 114 e ['] p-max 115 e
  ['] p-min 116 e ['] p-- 117 e ['] p-prevname 118 e ['] p-name> 119 e ['] p-noop 120 e
  ['] p-or 122 e ['] p-over 123 e ['] p-pick 124 e ['] p-+ 125 e ['] p-+loop 126 e
  ['] p-+! 127 e ['] p-?do 128 e ['] p-?dup 129 e ['] p-0push 130 e ['] p-quit 131 e
  ['] p-refill 132 e ['] p-resize 133 e ['] p-line@ 134 e ['] p-roll 135 e ['] p-rot 136 e
  ['] p-rp@ 137 e ['] p-rp! 138 e ['] p-rshift 139 e ['] p-rdrop 140 e ['] p-r@ 141 e
  ['] p-r> 142 e ['] p-save 143 e ['] p-line! 144 e ['] p-scan 145 e ['] p-semicolon 146 e
  ['] p-skip 147 e ['] p-source 148 e ['] p-source-id 149 e ['] p-pop-id 150 e
  ['] p-push-id 151 e ['] p-set-source 152 e ['] p-sp@ 153 e ['] p-sp! 154 e ['] p-! 155 e
  ['] p-swap 156 e ['] p-test1 157 e ['] p-noop 158 e ['] p-tick 160 e ['] p-* 161 e
  ['] p->r 162 e ['] p-type 163 e v-base 165 pv v-cbase 166 pv v-climit 167 pv
  v-context 168 pv v-dp 169 pv v-echo 170 pv v-hbase 171 pv v-hlimit 172 pv v-hptr 173 pv
  v-ntib 174 pv v-out 175 pv v-retcode 176 pv v-state 178 pv v-in 179 pv v-tflags 180 pv
  v-tlevel 181 pv v-tstack 182 pv ['] p-word 184 e ['] p-w@ 185 e ['] p-w! 186 e
  ['] p-xor 187 e ['] p-0branch 188 e ['] p-catch 189 e ['] p-throw 190 e
  ['] p-interpret 191 e 2 192 pv ['] p-fbin 193 e 4 194 pv ['] p-cells 195 e
  ['] p-fdelete 196 e ['] p-fflush 197 e ['] p-frename 198 e ['] p-fresize 199 e
  ['] p-sleep 200 e v-byecode 201 pv 34 202 pv 32 203 pv 31 204 pv r-base 205 pv ;
: cold ( -- ) \ pfInitSystem, pfCreateDictionary, pfBuildDictionary, FindSpecialXTs
  0 v-context ! 0 v-state ! 10 v-base ! 0 v-byecode ! 0 v-echo ! 0 v-tlevel ! 1 v-tstack !
  0 v-tflags ! 0 v-retcode ! 0 v-localxt ! h-start v-hbase ! h-start v-hptr ! c-start v-hlimit !
  c-start v-cbase ! c-start 832 + v-dp ! pool v-climit ! -400 v-colon ! 0 v-incl !
  pool v-heap ! tib v-src ! 0 v-ntib ! 0 v-in ! 0 v-line ! 0 v-out ! 0 fake 4 + !
  s" 0 EXIT 1 1- 2 1+ 10 2R@ 11 2R> 12 2>R 3 2DUP 260 2LITERAL 5 (2LITERAL) 6 2- 8 2+ 7 2OVER 9 2SWAP" dic-records
  s" 13 (ACCEPT) 525 ACCEPT 270 ALITERAL 15 (ALITERAL) 16 ALLOCATE 18 ARSHIFT 17 AND 19 BAIL 21 BRANCH" dic-records
  s" 20 BODY_OFFSET 22 BYE 189 CATCH 194 CELL 195 CELLS 24 C@ 25 CMOVE 26 CMOVE> 27 : 28 (:) 29 COMPARE" dic-records
  s" 30 = 33 <> 31 > 34 U> 32 < 35 U< 36 0= 39 0<> 37 0> 38 0< 40 CR 41 CREATE 42 (CREATE) 57 D+ 54 D-" dic-records
  s" 58 UM/MOD 56 MU/MOD 55 M* 59 UM* 44 DEFER 43 C! 46 DEPTH 47 / 48 . 49 .S 50 (DO) 51 DROP 52 DUMP" dic-records
  s" 53 DUP 61 (EMIT) 573 EMIT 62 EOL 63 (?ERROR) 63 ?ERROR 64 EXECUTE 65 @ 76 FILL 77 FIND" dic-records
  s" 67 CREATE-FILE 196 DELETE-FILE 68 OPEN-FILE 66 CLOSE-FILE 70 READ-FILE 74 FILE-SIZE 75 WRITE-FILE" dic-records
  s" 69 FILE-POSITION 71 REPOSITION-FILE 197 FLUSH-FILE 198 (RENAME-FILE) 199 (RESIZE-FILE) 72 R/O" dic-records
  s" 73 R/W 192 W/O 193 BIN 78 FINDNFA 79 FLUSHEMIT 80 FREE 81 HERE 82 (SNUMBER?) 83 I 191 INTERPRET" dic-records
  s" 85 J 84 INCLUDE-FILE 86 KEY 87 (LEAVE) 344 LITERAL 89 (LITERAL) 90 LOADSYS 91 LOCAL-COMPILER" dic-records
  s" 92 (LOCAL.ENTRY) 93 (LOCAL.EXIT) 94 (LOCAL@) 95 (1_LOCAL@) 96 (2_LOCAL@) 97 (3_LOCAL@) 98 (4_LOCAL@)" dic-records
  s" 99 (5_LOCAL@) 100 (6_LOCAL@) 101 (7_LOCAL@) 102 (8_LOCAL@) 104 (LOCAL!) 105 (1_LOCAL!) 106 (2_LOCAL!)" dic-records
  s" 107 (3_LOCAL!) 108 (4_LOCAL!) 109 (5_LOCAL!) 110 (6_LOCAL!) 111 (7_LOCAL!) 112 (8_LOCAL!)" dic-records
  s" 103 (LOCAL+!) 113 (LOOP) 114 LSHIFT 115 MAX 116 MIN 117 - 119 NAME> 118 PREVNAME 120 NOOP" dic-records
  s" 594 NUMBER? 122 OR 123 OVER 124 PICK 125 + 126 (+LOOP) 127 +! 131 (QUIT) 643 QUIT 128 (?DO) 129 ?DUP" dic-records
  s" 130 ?TERMINAL 130 KEY? 132 REFILL 133 RESIZE 135 ROLL 136 ROT 139 RSHIFT 140 RDROP 141 R@ 142 R>" dic-records
  s" 137 RP@ 138 RP! 205 R0 402 ; 153 SP@ 154 SP! 155 ! 143 (SAVE-FORTH) 145 SCAN 147 SKIP 200 (SLEEP)" dic-records
  s" 148 SOURCE 152 SET-SOURCE 149 SOURCE-ID 151 PUSH-SOURCE-ID 150 POP-SOURCE-ID" dic-records
  s" 134 SOURCE-LINE-NUMBER@ 144 SOURCE-LINE-NUMBER! 156 SWAP 157 TEST1 158 TEST2 160 ' 161 * 190 THROW" dic-records
  s" 162 >R 163 TYPE 165 BASE 201 BYE-CODE 166 CODE-BASE 167 CODE-LIMIT 168 CONTEXT 169 DP 170 ECHO" dic-records
  s" 173 HEADERS-PTR 171 HEADERS-BASE 172 HEADERS-LIMIT 174 #TIB 176 RETURN-CODE 180 TRACE-FLAGS" dic-records
  s" 181 TRACE-LEVEL 182 TRACE-STACK 175 OUT 178 STATE 179 >IN 202 VERSION_CODE 184 WORD 185 W@ 186 W!" dic-records
  s" 187 XOR 188 0BRANCH 203 FLAG_SMUDGE 204 MASK_NAME_SIZE" dic-records
  s" (QUIT)" find-c v-quitxt ! s" NUMBER?" find-c v-numq ! s" ACCEPT" find-c v-accxt ! ;
: exec-if ( a n -- ) c>f ffind if pfcatch drop else drop then ; \ pfExecIfDefined
: warm ( -- ) saved @ if restore else cold then reset-task s" AUTO.INIT" exec-if ;
: session ( -- ) ['] quit catch ?dup if 1 = if -1 eof ! then else s" AUTO.TERM" exec-if then ;
: main ( -- ) init-tables 0 eof ! 0 saved ! cold reset-task begin session eof @ 0= while warm repeat ;
