\ Primitives as generators (14.3-14.7): words of the compiler, executed when the
\ source names the word of the language, that write its copycode (as an
\ IMMEDIATE word) or define a word. Compiled after forthc.fth, before main.fth;
\ the host pForth loads it with the compiler. A generator folds the values
\ known at the top level (FC-FOLD?) or writes code; the code is that of the
\ branches by the name of the word the compiler had before. The language
\ names are given in FC-GENERATORS: the names here differ (pForth itself uses
\ + - * ...).
: gen+ ( -- ) 2 fc-fold? if fc-ct2 + fc-ct+ exit then 0 fc-binary ;
: gen- ( -- ) 2 fc-fold? if fc-ct2 - fc-ct+ exit then 1 fc-binary ;
: gen-and ( -- ) 2 fc-fold? if fc-ct2 and fc-ct+ exit then 2 fc-binary ;
: gen-or ( -- ) 2 fc-fold? if fc-ct2 or fc-ct+ exit then 3 fc-binary ;
: gen-xor ( -- ) 2 fc-fold? if fc-ct2 xor fc-ct+ exit then 4 fc-binary ;
: gen= ( -- ) fc-code 5 fc-binary ;
: gen< ( -- ) fc-code 6 fc-binary ;
: gen-u< ( -- ) fc-code 7 fc-binary ;
: gen-lshift ( -- )
  2 fc-fold? if fc-ct2 31 and lshift fc-ct+ exit then 0 fc-shift-lit? if exit then 8 fc-binary ;
: gen-rshift ( -- )
  2 fc-fold? if fc-ct2 31 and rshift fc-ct+ exit then -1 fc-shift-lit? if exit then 9 fc-binary ;
: gen-0= ( -- ) fc-code fc-pop fc-reg tuck swap fc-or-zero fc-push ;
: gen-cells ( -- ) 1 fc-fold? if fc-ct- 4 * fc-ct+ exit then 2 fc-shift-copy ;
: gen-2* ( -- ) 1 fc-fold? if fc-ct- 2 * fc-ct+ exit then 1 fc-shift-copy ;
: gen-1+ ( -- ) 1 fc-fold? if fc-ct- 1+ fc-ct+ exit then cc-t-add @ 1 0 fc-inc ;
: gen-1- ( -- ) 1 fc-fold? if fc-ct- 1- fc-ct+ exit then cc-t-sub @ 1 1 fc-inc ;
: gen-cell+ ( -- ) 1 fc-fold? if fc-ct- 4 + fc-ct+ exit then cc-t-add @ 4 0 fc-inc ;
\ * / MOD /MOD call the helpers built before the code (FC-SCAN-USES).
: gen* ( -- )
  2 fc-fold? if fc-ct2 * fc-ct+ exit then fc-mul-lit? if exit then
  fc-mul-entry @ fc-mul-exit @ fc-call-helper fc-mp fc-result1 ;
: gen/ ( -- ) fc-code fc-div-entry @ fc-div-exit @ fc-call-helper fc-mq fc-result1 ;
: gen-mod ( -- ) fc-code fc-div-entry @ fc-div-exit @ fc-call-helper fc-mr fc-result1 ;
: gen/mod ( -- ) fc-code fc-div-entry @ fc-div-exit @ fc-call-helper fc-mr fc-mq fc-result2 ;
\ Stack, memory, channels (14.4). At the top level FC-CODE opens the part of
\ the code first (a definition needs nothing), as the path of the words that
\ were not found did before.
: gen-dup ( -- ) fc-code 1 fc-need fc-n @ 1- fc-c@ fc-push ;
: gen-drop ( -- ) fc-code fc-n @ if fc-pop1 drop else 0 fc-noff ! fc-sp -1 fc-adjust then ;
: gen-swap ( -- ) fc-code 2 fc-need fc-pop1 fc-pop1 swap fc-push fc-push ;
: gen-over ( -- ) fc-code 2 fc-need fc-n @ 2 - fc-c@ fc-push ;
: gen-rot ( -- ) fc-code 3 fc-need fc-pop1 fc-pop1 fc-pop1 >r fc-push fc-push r> fc-push ;
: gen-pick ( -- ) fc-code 0 fc-pick-roll ;
: gen-roll ( -- ) fc-code -1 fc-pick-roll ;
: gen->r ( -- ) fc-code fc-pop fc-src1 fc-rstk fc-rp 32 fc-mem-push ;
: gen-r> ( -- ) fc-code fc-rstk fc-rp 1 32 fc-mem-pop 0 fc-npin ! 0 fc-popped@ fc-push ;
: gen-r@ ( -- ) fc-code -1 fc-r-at ;     \ R@ and I
: gen-j ( -- ) fc-code -3 fc-r-at ;
: gen-@ ( -- )
  fc-code fc-pop dup fc-pin ! 1 fc-npin ! fc-reg fc-cres ! 0 fc-npin ! 0 fc-check fc-cres @ fc-push ;
: gen-! ( -- ) fc-code 2 fc-need fc-pop1 fc-pop1 fc-cv ! 1 fc-check ;
: gen-c@ ( -- )
  fc-code fc-pop dup fc-pin ! 1 fc-npin ! fc-reg fc-cres ! 0 fc-npin ! 2 fc-check fc-cres @ fc-push ;
: gen-c! ( -- ) fc-code 2 fc-need fc-pop1 fc-pop1 fc-cv ! 3 fc-check ;
: gen-emit ( -- )
  fc-code fc-pop cc-lookups-begin fc-t-rev8 @ 4 8 fc-xr 0 cc-item 8 0 cc-seg cc-lookups
  cc-stdout dup fc-xr dup 8 + fc-rows1 ;
: gen-key ( -- ) fc-code fc-read-key ;
\ Control (14.5): the branches of FC-CONTROL-TOKEN and FC-WORD-TOKEN. An open
\ structure is an entry of the control stack (FC-CTL+ FC-CTL-): kind (1 if,
\ 2 else, 3 begin, 4 while, 5 do), its cell and, for a loop, its leave cell.
: gen-if ( -- ) fc-code fc-pop fc-spill fc-branch swap 1 swap fc-ctl+ fc-begin-block drop ;
: gen-else ( -- )
  fc-code fc-ctl- nip fc-spill cc-new-cell dup fc-jump fc-end 2 swap fc-ctl+ fc-begin-block drop ;
: gen-then ( -- )
  fc-code fc-ctl- fc-spill swap 1 = if
    cc-new-cell dup fc-jump cc-flush swap cc-new-record over swap cc-next! fc-end fc-begin-block drop
  else fc-begin-block drop then ;
: gen-begin ( -- ) fc-code fc-by-execution fc-spill 3 -1 fc-begin-block fc-ctl+ ;
: gen-until ( -- )
  fc-code fc-pop fc-spill fc-branch swap cc-new-record fc-ctl- nip swap cc-next! cc-flush fc-begin-block drop ;
: gen-while ( -- ) fc-code fc-pop fc-spill fc-branch swap 4 swap fc-ctl+ fc-begin-block drop ;
: gen-repeat ( -- ) fc-code fc-ctl- nip fc-ctl- nip fc-spill fc-jump fc-end fc-begin-block drop ;
: gen-again ( -- ) fc-code fc-ctl- nip fc-spill fc-jump fc-end -1 fc-begin-block drop ;
\ DO: limit and index to the return stack, the loop starts a block.
: gen-do ( -- )
  fc-code fc-by-execution 2 fc-need fc-pop1 fc-pop1 fc-spill fc-srcs ! fc-srcs cell+ ! 2 fc-nsrc !
  fc-rstk fc-rp 32 fc-mem-push 5 -1 fc-begin-block fc-ctl+ ;
\ ?DO: equal limit and index skip the loop, straight to its leave cell.
variable fc-di variable fc-dl
: gen-?do ( -- )
  fc-code fc-by-execution 2 fc-need fc-pop1 fc-di ! fc-pop1 fc-dl ! fc-spill
  cc-t-xor @ fc-xr fc-di @ fc-dl @ cc-logic fc-xr fc-branch
  cc-new-cell dup >r rot cc-new-record cc-next! cc-flush fc-begin-block drop
  fc-dl @ fc-srcs ! fc-di @ fc-srcs cell+ ! 2 fc-nsrc ! fc-rstk fc-rp 32 fc-mem-push
  5 -1 fc-begin-block fc-ctl+ r> fc-ctl-leave! ;
\ LOOP: index + 1, back to the start unless it equals the limit; then the leave cell.
variable fc-lv
: gen-loop ( -- )
  fc-code fc-ctl- nip fc-ctl-leave fc-lv ! fc-spill fc-rstk fc-rp 2 32 fc-mem-pop 0 fc-npin !
  fc-regs fc-nregs 1- 64 * + >r
  cc-t-add @ fc-tmp 1 fc-popped@ 1 fc-const 0 cc-adder 32 r@ fc-tmp cc-copy fc-rows1
  cc-t-xor @ fc-xr r@ 0 fc-popped@ cc-logic
  fc-xr fc-branch ( start zero more ) cc-seq cc-layer drop
  0 fc-popped@ fc-srcs ! r> fc-srcs cell+ ! 2 fc-nsrc ! fc-rstk fc-rp 32 fc-mem-push
  swap cc-jump fc-end
  fc-lv @ ?dup if swap cc-new-record over swap cc-next! cc-flush then fc-begin-block drop ;
: gen-leave ( -- )
  fc-code fc-do-entry fc-spill 0 fc-noff ! fc-rp -2 fc-adjust
  fc-loop-leave fc-jump fc-end -1 fc-begin-block drop ;
: gen-unloop ( -- ) fc-code 0 fc-noff ! fc-rp -2 fc-adjust ;
\ Calls: EXIT returns, RECURSE calls the word being defined, EXECUTE calls an xt;
\ ['] X compiles the xt of X (the next word of the channel) as a literal.
: gen-exit ( -- ) fc-code fc-ret -1 fc-begin-block drop ;
\ The call of a word goes through its concept cell (FC-XT, 14.11); a loop, RECURSE and a call of an
\ xt make the price of the word one by execution (FC-BY-EXECUTION).
: gen-recurse ( -- ) fc-code fc-by-execution fc-word @ dup fc-callee ! fc-xt fc-call ;
: gen-tick ( -- )
  fc-code fc-next! fc-find dup 0= if -13 throw then dup 2 cells + @ 1 = if fc-xt else 3 cells + @ then
  fc-literal ;
: gen-throw ( -- ) fc-code fc-throw ;
\ Isolation of the kernel (14.10). In the program of the kernel (FC-GUARD, set by the kernel
\ while it compiles a program) the generators of SPACE! SPACEC! SPACE@ SPACEC@ EXECUTE CATCH
\ write a check before their code: -9 THROW unless [lo,hi) is in the half of the program, or the
\ address is the entry of a word of the program. A generator is called as the loop of
\ FC-COMPILE calls it (GEN-CALL: the literal compiled by the previous word is seen); the checks
\ call the generators themselves, not the words of the dictionary, which the program may redefine.
: gen-call ( xt -- ) fc-ll @ fc-plit ! fc-llr @ fc-plr ! fc-llv @ fc-plv ! 0 fc-ll ! execute ;
: gen-lit ( v -- ) fc-code fc-literal ;
\ N PICK as a check needs it: the literal N, then the pick (also at the top level).
: gen-pick-n ( n -- ) gen-lit fc-ll @ fc-plit ! fc-llr @ fc-plr ! fc-llv @ fc-plv ! 0 fc-ll ! 0 fc-pick-roll ;
\ ( lo hi -- lo hi ) for a store or a fetch of n bits: -9 THROW unless hi - lo = n (the interval of the
\ copy is valid), lo and hi - 1 are in the same block of 2^29 bits, and the block is 0 or 2 (bits 29 and
\ 31 of lo are zero). Then [lo, hi) is in the half of the program: [0, 2^29) or [2^30, 2^30 + 2^29).
: gen-check-range ( n -- )
  >r ['] gen-over gen-call ['] gen-over gen-call ['] gen-swap gen-call ['] gen- gen-call
  r> gen-lit ['] gen-xor gen-call 2 gen-pick-n 2 gen-pick-n ['] gen-1- gen-call ['] gen-xor gen-call
  29 gen-lit ['] gen-rshift gen-call ['] gen-or gen-call
  2 gen-pick-n 5 29 lshift gen-lit ['] gen-and gen-call ['] gen-or gen-call
  ['] gen-if gen-call -9 gen-lit ['] gen-throw gen-call ['] gen-then gen-call ;
\ The entry of a word (a colon definition of the program of the kernel) holds, in the first row of
\ its first layer, the copy of 32 zero bits to FC-MARK: the field dl of that row, at the start of
\ the cell, is the mark.
: fc-mark-entry ( -- ) 32 fc-mark fc-zero cc-copy cc-last cc-row drop ;
: gen-space! ( -- ) fc-code fc-guard @ if 32 gen-check-range then 32 fc-space-store ;
: gen-spacec! ( -- ) fc-code fc-guard @ if 8 gen-check-range then 8 fc-space-store ;
: gen-space@ ( -- ) fc-code fc-guard @ if 32 gen-check-range then 32 fc-space-fetch ;
: gen-spacec@ ( -- ) fc-code fc-guard @ if 8 gen-check-range then 8 fc-space-fetch ;
\ ( xt -- xt ) for EXECUTE and CATCH: -9 THROW unless xt is in the code of the program (bits 29 and above
\ are zero) and the 32 bits at the start of its cell are the mark. The read is of the aligned 32 bits
\ of the code ((xt and 2^29 - 32), 32 bits), so it never leaves the code of the program.
: gen-check-entry ( -- )
  0 0 0 cc-field if -24 throw then
  ['] gen-dup gen-call 29 gen-lit ['] gen-rshift gen-call ['] gen-over gen-call
  1 29 lshift 32 - gen-lit ['] gen-and gen-call ['] gen-dup gen-call 32 gen-lit ['] gen+ gen-call
  32 fc-space-fetch fc-mark gen-lit ['] gen-xor gen-call ['] gen-or gen-call
  ['] gen-if gen-call -9 gen-lit ['] gen-throw gen-call ['] gen-then gen-call ;
: gen-execute ( -- )
  fc-code fc-by-execution fc-guard @ if gen-check-entry then fc-pop -1 fc-call-indirect fc-begin-block drop ;
: gen-catch ( -- ) fc-code fc-by-execution fc-guard @ if gen-check-entry then fc-catch ;
\ Defining words and the channel (14.6). : VARIABLE CREATE CONSTANT ALLOT and
\ KERNEL-LAYOUT belong to the top level (FC-TOP-ONLY: else -13); ; to a
\ definition (at the top level -22). ( [CHAR] S" read the channel.
: gen-colon ( -- ) \ : NAME starts the word NAME (visible at once: RECURSE)
  fc-top-only fc-close-init fc-next! 0 cc-group 1 over fc-define fc-nwords @ 1- fc-wt@ fc-word !
  0 fc-live ! 0 fc-n ! fc-begin-block drop fc-guard @ if fc-mark-entry then fc-log-begin ;
: gen-semicolon ( -- ) \ ; returns and ends the definition, its price is counted (14.11)
  fc-defining? 0= if -22 throw then fc-nctl @ if -22 throw then fc-ret fc-word @ fc-price-word 0 fc-word ! ;
: gen-variable ( -- ) fc-top-only fc-next! 4 fc-define-data ;
: gen-create ( -- ) fc-top-only fc-next! 0 fc-define-data ;
: gen-allot ( -- ) fc-top-only fc-ct- fc-here +! fc-check-here ;
: gen-constant ( -- ) fc-top-only fc-ct- fc-next! 0 swap fc-define ;
: gen-decimal ( -- ) ;                  \ numbers are decimal only
\ The layout itself is chosen before the code: FC-SCAN-USES finds the need 4.
: gen-kernel-layout ( -- ) fc-top-only ;
\ The word \ (a comment to the end of the line) has the need 8: it is executed
\ also in FC-SCAN-USES, the words of the comment are not the words of the source.
: gen-backslash ( -- )
  begin fc-more? if fc-ch 10 <> else 0 then while 1 fc-pos +! repeat ;
: gen-paren ( -- ) begin fc-next! s" )" fc-is? until ;   \ ( a comment )
: gen-char ( -- ) fc-code fc-next 0= if -16 throw then fc-raw fc-literal ;
: gen-string ( -- ) fc-code fc-string-token dup >r fc-store-string fc-literal r> fc-literal ;
\ Literals, digits, numbers (14.7). A digit 0..9 is a word of the language, the
\ synonym of a literal (an entry of kind 0, FC-LITERAL-NAME): in a definition
\ it compiles the literal of its value (FC-LITERAL: one copy of a constant), at
\ the top level it is a value known at compile time. A number is a word of
\ digits, after - if negative: the generator LITERAL gets every word not found
\ in the dictionary (FC-WORD-TOKEN) and builds the value from the values of
\ the digits (each looked up in the dictionary as a word) modulo 2^32, then
\ compiles it as a digit is compiled; another word is unknown, -13.
: fc-digit@ ( addr -- d ) \ the value of the digit at addr (a word of one byte)
  1 fc-lookup dup if dup 2 cells + @ 0= if 3 cells + @ exit then then -13 throw ;
: gen-literal ( -- )
  fc-tok fc-tl @ over c@ [char] - = if 1 /string -1 else 1 then >r
  dup 0= if -13 throw then
  0 -rot over + swap do 10 * i fc-digit@ + loop r> *
  fc-defining? if fc-literal else fc-ct+ then ;
\ The mechanisms of a word (14.11, space/language/doc/word.md). COST ( xt -- size bits copies layers
\ known ) and PROVED? ( xt -- f ) need the xt known at compile time: the literal just compiled
\ (['] W), else -13; they compile literals. PRICE ( size bits copies layers -- n ): the sum, the
\ code of three + (at the top level folded, as +).
: fc-known-xt ( -- xt ) fc-lit? 0= if -13 throw then fc-pop1 drop fc-plv @ ;
: gen-cost ( -- )
  fc-known-xt fc-cost >r >r >r >r fc-literal r> fc-literal r> fc-literal r> fc-literal r> fc-literal ;
: gen-proved? ( -- ) fc-known-xt fc-proved? fc-literal ;
: gen-price ( -- ) ['] gen+ gen-call ['] gen+ gen-call ['] gen+ gen-call ;
\ The name of two bytes c1 c2 (S": a quote cannot be written in a string).
: fc-name2 ( c1 c2 -- addr u ) fc-tok 1+ c! fc-tok c! fc-tok 2 ;
\ Language name, generator, needs (1 multiplication, 2 division, 4 the kernel
\ layout); the digits: name and value of the literal.
: fc-generators ( -- )
  s" +" ['] gen+ 0 fc-generator  s" -" ['] gen- 0 fc-generator
  s" *" ['] gen* 1 fc-generator  s" /" ['] gen/ 2 fc-generator
  s" mod" ['] gen-mod 2 fc-generator  s" /mod" ['] gen/mod 2 fc-generator
  s" and" ['] gen-and 0 fc-generator  s" or" ['] gen-or 0 fc-generator
  s" xor" ['] gen-xor 0 fc-generator  s" lshift" ['] gen-lshift 0 fc-generator
  s" rshift" ['] gen-rshift 0 fc-generator  s" =" ['] gen= 0 fc-generator
  s" <" ['] gen< 0 fc-generator  s" u<" ['] gen-u< 0 fc-generator
  s" 0=" ['] gen-0= 0 fc-generator  s" 2*" ['] gen-2* 0 fc-generator
  s" 1+" ['] gen-1+ 0 fc-generator  s" 1-" ['] gen-1- 0 fc-generator
  s" cells" ['] gen-cells 0 fc-generator  s" cell+" ['] gen-cell+ 0 fc-generator
  s" dup" ['] gen-dup 0 fc-generator  s" drop" ['] gen-drop 0 fc-generator
  s" swap" ['] gen-swap 0 fc-generator  s" over" ['] gen-over 0 fc-generator
  s" rot" ['] gen-rot 0 fc-generator  s" pick" ['] gen-pick 0 fc-generator
  s" roll" ['] gen-roll 0 fc-generator  s" >r" ['] gen->r 0 fc-generator
  s" r>" ['] gen-r> 0 fc-generator  s" r@" ['] gen-r@ 0 fc-generator
  s" i" ['] gen-r@ 0 fc-generator  s" j" ['] gen-j 0 fc-generator
  s" @" ['] gen-@ 0 fc-generator  s" !" ['] gen-! 0 fc-generator
  s" c@" ['] gen-c@ 0 fc-generator  s" c!" ['] gen-c! 0 fc-generator
  s" space!" ['] gen-space! 0 fc-generator  s" spacec!" ['] gen-spacec! 0 fc-generator
  s" space@" ['] gen-space@ 0 fc-generator  s" spacec@" ['] gen-spacec@ 0 fc-generator
  s" emit" ['] gen-emit 0 fc-generator  s" key" ['] gen-key 0 fc-generator
  s" if" ['] gen-if 0 fc-generator  s" else" ['] gen-else 0 fc-generator
  s" then" ['] gen-then 0 fc-generator  s" begin" ['] gen-begin 0 fc-generator
  s" until" ['] gen-until 0 fc-generator  s" while" ['] gen-while 0 fc-generator
  s" repeat" ['] gen-repeat 0 fc-generator  s" again" ['] gen-again 0 fc-generator
  s" do" ['] gen-do 0 fc-generator  s" ?do" ['] gen-?do 0 fc-generator
  s" loop" ['] gen-loop 0 fc-generator  s" leave" ['] gen-leave 0 fc-generator
  s" unloop" ['] gen-unloop 0 fc-generator  s" exit" ['] gen-exit 0 fc-generator
  s" recurse" ['] gen-recurse 0 fc-generator  s" execute" ['] gen-execute 0 fc-generator
  s" [']" ['] gen-tick 0 fc-generator  s" catch" ['] gen-catch 0 fc-generator
  s" throw" ['] gen-throw 0 fc-generator
  s" :" ['] gen-colon 0 fc-generator  s" ;" ['] gen-semicolon 0 fc-generator
  s" variable" ['] gen-variable 0 fc-generator  s" create" ['] gen-create 0 fc-generator
  s" allot" ['] gen-allot 0 fc-generator  s" constant" ['] gen-constant 0 fc-generator
  s" decimal" ['] gen-decimal 0 fc-generator  s" kernel-layout" ['] gen-kernel-layout 4 fc-generator
  s" \" ['] gen-backslash 8 fc-generator  s" (" ['] gen-paren 0 fc-generator  s" [char]" ['] gen-char 0 fc-generator
  [char] s [char] " fc-name2 ['] gen-string 0 fc-generator
  s" literal" ['] gen-literal 0 fc-generator
  s" cost" ['] gen-cost 0 fc-generator  s" price" ['] gen-price 0 fc-generator
  s" proved?" ['] gen-proved? 0 fc-generator
  s" 0" 0 fc-literal-name  s" 1" 1 fc-literal-name  s" 2" 2 fc-literal-name  s" 3" 3 fc-literal-name
  s" 4" 4 fc-literal-name  s" 5" 5 fc-literal-name  s" 6" 6 fc-literal-name  s" 7" 7 fc-literal-name
  s" 8" 8 fc-literal-name  s" 9" 9 fc-literal-name ;
: fc-install-generators ( -- ) ['] fc-generators fc-gens ! ;
fc-install-generators
