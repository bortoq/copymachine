\ Primitives as generators (14.3, 14.4): words of the compiler, executed when the
\ source names the word of the language, that write its copycode (as an
\ IMMEDIATE word). Compiled after forthc.fth, before main.fth; the host pForth
\ loads it with the compiler. A generator folds the values known at the top
\ level (FC-FOLD?) or writes code; the code is that of the branches of
\ FC-PRIMITIVE it replaces. The language names are given in FC-GENERATORS:
\ the names here differ (pForth itself uses + - * ...).
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
: gen-space! ( -- ) fc-code 32 fc-space-store ;
: gen-spacec! ( -- ) fc-code 8 fc-space-store ;
: gen-emit ( -- )
  fc-code fc-pop cc-lookups-begin fc-t-rev8 @ 4 8 fc-xr 0 cc-item 8 0 cc-seg cc-lookups
  cc-stdout dup fc-xr dup 8 + fc-rows1 ;
: gen-key ( -- ) fc-code fc-read-key ;
\ Language name, generator, helpers (1 multiplication, 2 division).
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
  s" emit" ['] gen-emit 0 fc-generator  s" key" ['] gen-key 0 fc-generator ;
: fc-install-generators ( -- ) ['] fc-generators fc-gens ! ;
fc-install-generators
