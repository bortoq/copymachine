\ Primitives as generators (14.3-14.7): words of the compiler, executed when the source names the word of the language,
\ that write its copycode or define a word. Compiled after forthc.fth, before main.fth. A generator folds the values
\ known at the top level (FC-FOLD?) or writes code. The names of the language are in FC-GENERATORS.
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
: gen-1+ ( -- ) 1 fc-fold? if fc-ct- 1+ fc-ct+ exit then lay-t-add @ 1 0 fc-inc ;
: gen-1- ( -- ) 1 fc-fold? if fc-ct- 1- fc-ct+ exit then lay-t-sub @ 1 1 fc-inc ;
: gen-cell+ ( -- ) 1 fc-fold? if fc-ct- 4 + fc-ct+ exit then lay-t-add @ 4 0 fc-inc ;
: gen* ( -- )
  2 fc-fold? if fc-ct2 * fc-ct+ exit then fc-mul-lit? if exit then
  fc-mul-entry @ fc-mul-exit @ fc-call-helper fc-mp fc-result1 ;
: gen/ ( -- ) fc-code fc-div-entry @ fc-div-exit @ fc-call-helper fc-mq fc-result1 ;
: gen-mod ( -- ) fc-code fc-div-entry @ fc-div-exit @ fc-call-helper fc-mr fc-result1 ;
: gen/mod ( -- ) fc-code fc-div-entry @ fc-div-exit @ fc-call-helper fc-mr fc-mq fc-result2 ;
: gen-dup ( -- ) fc-code 1 fc-need fc-n @ 1- fc-c@ fc-push ;
: gen-drop ( -- ) fc-code fc-n @ if fc-pop1 drop else 0 fc-noff ! fc-sp -1 fc-adjust then ;
: gen-swap ( -- ) fc-code 2 fc-need fc-pop1 fc-pop1 swap fc-push fc-push ;
: gen-over ( -- ) fc-code 2 fc-need fc-n @ 2 - fc-c@ fc-push ;
: gen-rot ( -- ) fc-code 3 fc-need fc-pop1 fc-pop1 fc-pop1 >r fc-push fc-push r> fc-push ;
: gen-pick ( -- ) fc-code 0 fc-pick-roll ;
: gen-roll ( -- ) fc-code -1 fc-pick-roll ;
: gen->r ( -- ) fc-code fc-pop fc-src1 fc-rstk fc-rp 32 fc-mem-push ;
: gen-r> ( -- ) fc-code fc-rstk fc-rp 1 32 fc-mem-pop 0 fc-npin ! 0 fc-popped@ fc-push ;
: gen-r@ ( -- ) fc-code -1 fc-r-at ;
: gen-j ( -- ) fc-code -3 fc-r-at ;
: gen-@ ( -- )
  fc-code fc-pop dup fc-pin ! 1 fc-npin ! fc-reg fc-cres ! 0 fc-npin ! 0 fc-check fc-cres @ fc-push ;
: gen-! ( -- ) fc-code 2 fc-need fc-pop1 fc-pop1 fc-cv ! 1 fc-check ;
: gen-c@ ( -- )
  fc-code fc-pop dup fc-pin ! 1 fc-npin ! fc-reg fc-cres ! 0 fc-npin ! 2 fc-check fc-cres @ fc-push ;
: gen-c! ( -- ) fc-code 2 fc-need fc-pop1 fc-pop1 fc-cv ! 3 fc-check ;
: gen-emit ( -- )
  fc-code fc-pop lay-lookups-begin fc-t-rev8 @ 4 8 fc-xr 0 lay-item 8 0 lay-seg lay-lookups
  lay-stdout dup fc-xr dup 8 + fc-rows1 ;
: gen-key ( -- ) fc-code fc-read-key ;
\ Control (14.5): FC-CONTROL-TOKEN, FC-WORD-TOKEN. An open structure is an entry of the control stack (FC-CTL+ FC-CTL-).
: gen-if ( -- ) fc-code fc-pop fc-spill fc-branch swap 1 swap fc-ctl+ fc-begin-block drop ;
: gen-else ( -- )
  fc-code fc-ctl- nip fc-spill lay-new-cell dup fc-jump fc-end 2 swap fc-ctl+ fc-begin-block drop ;
: gen-then ( -- )
  fc-code fc-ctl- fc-spill swap 1 = if
    lay-new-cell dup fc-jump lay-flush swap lay-new-record over swap lay-next! fc-end fc-begin-block drop
  else fc-begin-block drop then ;
: gen-begin ( -- ) fc-code fc-by-execution fc-spill 3 -1 fc-begin-block fc-ctl+ ;
: gen-until ( -- )
  fc-code fc-pop fc-spill fc-branch swap lay-new-record fc-ctl- nip swap lay-next! lay-flush fc-begin-block drop ;
: gen-while ( -- ) fc-code fc-pop fc-spill fc-branch swap 4 swap fc-ctl+ fc-begin-block drop ;
: gen-repeat ( -- ) fc-code fc-ctl- nip fc-ctl- nip fc-spill fc-jump fc-end fc-begin-block drop ;
: gen-again ( -- ) fc-code fc-ctl- nip fc-spill fc-jump fc-end -1 fc-begin-block drop ;
: gen-do ( -- )
  fc-code fc-by-execution 2 fc-need fc-pop1 fc-pop1 fc-spill fc-srcs ! fc-srcs cell+ ! 2 fc-nsrc !
  fc-rstk fc-rp 32 fc-mem-push 5 -1 fc-begin-block fc-ctl+ ;
variable fc-di variable fc-dl
: gen-?do ( -- )
  fc-code fc-by-execution 2 fc-need fc-pop1 fc-di ! fc-pop1 fc-dl ! fc-spill
  lay-t-xor @ fc-xr fc-di @ fc-dl @ lay-logic fc-xr fc-branch
  lay-new-cell dup >r rot lay-new-record lay-next! lay-flush fc-begin-block drop
  fc-dl @ fc-srcs ! fc-di @ fc-srcs cell+ ! 2 fc-nsrc ! fc-rstk fc-rp 32 fc-mem-push
  5 -1 fc-begin-block fc-ctl+ r> fc-ctl-leave! ;
variable fc-lv
: gen-loop ( -- )
  fc-code fc-ctl- nip fc-ctl-leave fc-lv ! fc-spill fc-rstk fc-rp 2 32 fc-mem-pop 0 fc-npin !
  fc-regs fc-nregs 1- 64 * + >r
  lay-t-add @ fc-tmp 1 fc-popped@ 1 fc-const 0 lay-adder 32 r@ fc-tmp lay-copy fc-rows1
  lay-t-xor @ fc-xr r@ 0 fc-popped@ lay-logic
  fc-xr fc-branch ( start zero more ) lay-seq lay-layer drop
  0 fc-popped@ fc-srcs ! r> fc-srcs cell+ ! 2 fc-nsrc ! fc-rstk fc-rp 32 fc-mem-push
  swap lay-jump fc-end
  fc-lv @ ?dup if swap lay-new-record over swap lay-next! lay-flush then fc-begin-block drop ;
: gen-leave ( -- )
  fc-code fc-do-entry fc-spill 0 fc-noff ! fc-rp -2 fc-adjust
  fc-loop-leave fc-jump fc-end -1 fc-begin-block drop ;
: gen-unloop ( -- ) fc-code 0 fc-noff ! fc-rp -2 fc-adjust ;
: gen-exit ( -- ) fc-code fc-ret -1 fc-begin-block drop ;
\ BYE (the halt of a rejected program, FC-REJECT): a jump to the halt cell, where the end of MAIN goes too. Not a word of the
\ programs of the kernel too: a static jump to the cell the end of MAIN reaches.
: gen-bye ( -- ) fc-code fc-spill fc-cellb fc-jump fc-end -1 fc-begin-block drop ;
\ A call goes through the concept cell (FC-XT, 14.11); a loop, RECURSE and a call of an xt make the price by execution.
: gen-recurse ( -- ) fc-code fc-by-execution fc-word @ dup fc-callee ! fc-xt fc-call ;
: gen-tick ( -- )
  fc-code fc-next! fc-find dup 0= if -13 fc-reject then dup 2 cells + @ 1 = if fc-xtn else 3 cells + @ then
  fc-literal ;
: gen-throw ( -- ) fc-code fc-throw ;
\ Copies whose position is computed at run time (SPACE! SPACEC! SPACE@ SPACEC@, EXECUTE, CATCH, return, throw) write
\ into their row only the low bits of the position in the kernel (FC-GUARD, language/doc/isolation.md).
\ A generator is called as the loop of FC-COMPILE calls it (the previous literal is seen).
: gen-call ( xt -- ) fc-ll @ fc-plit ! fc-llr @ fc-plr ! fc-llv @ fc-plv ! 0 fc-ll ! execute ;
: gen-space! ( -- ) fc-code 32 fc-space-store ;
: gen-spacec! ( -- ) fc-code 8 fc-space-store ;
: gen-space@ ( -- ) fc-code 32 fc-space-fetch ;
: gen-spacec@ ( -- ) fc-code 8 fc-space-fetch ;
: gen-execute ( -- ) fc-code fc-by-execution fc-pop -1 fc-call-indirect fc-begin-block drop ;
: gen-catch ( -- ) fc-code fc-by-execution fc-catch ;
\ Defining words and the channel (14.6). : VARIABLE CREATE CONSTANT ALLOT KERNEL-LAYOUT belong to the top level
\ (FC-TOP-ONLY: else -13); ; to a definition (else -22). ( [CHAR] S" read the channel.
\ The replacement (14.13, language/doc/replace.md): in a program that names it each word has a concept cell in the code,
\ a layer that jumps to its entry, written like the call of EXECUTE (FC-CALL-INDIRECT) from the record in the memory of the
\ program (word 4: REPLACE changes it).
: fc-entry-cell ( cell -- ) \ a layer of the table of entries: jumps to the entry of the word being defined
  lay-seq lay-layer drop fc-word @ 6 cells + @ lay-jump lay-flush ;
: fc-concept ( cell -- )
  fc-log-begin dup fc-word @ 3 cells + ! lay-seq lay-layer fc-v0 ! lay-layer fc-v1 ! lay-layer drop lay-layer
  fc-jw over lay-layer-cell 7 2 lay-field lay-branch-bit + fc-rta @ 4 + 2 rshift 64 * fc-mem + lay-branch-bit + lay-copy
  fc-v0 @ lay-row drop
  fc-jw swap lay-layer-cell 7 3 lay-field lay-branch-bit + fc-rta @ 4 + 2 rshift 64 * fc-mem + lay-branch-bit + lay-copy
  fc-v1 @ lay-row drop
  fc-word @ 6 cells + @ lay-jump lay-flush ;
: gen-colon ( -- )
  fc-top-only fc-close-init fc-next! fc-synonym? ?dup if fc-synonym-of exit then
  fc-guard @ if fc-nwords @ 1 fc-ebits lshift u< 0= if -8 fc-reject then fc-nwords @ fc-etab-at
  else fc-rt @ if 0 lay-group else 0 then then 0 lay-group 1 over fc-define fc-nwords @ 1- fc-wt@ fc-word !
  swap ?dup if fc-rt @ if fc-concept else fc-entry-cell then then
  0 fc-live ! 0 fc-n ! fc-begin-block drop fc-rt @ 0= if fc-log-begin then ;
: gen-semicolon ( -- )
  fc-defining? 0= if -22 fc-reject then fc-nctl @ if -22 fc-reject then fc-ret fc-word @ fc-price-word
  fc-rt @ if fc-word @ fc-concept-record then 0 fc-word ! ;
: gen-variable ( -- ) fc-top-only fc-next! 4 fc-define-data ;
: gen-create ( -- ) fc-top-only fc-next! 0 fc-define-data ;
: gen-allot ( -- ) fc-top-only fc-ct- fc-here +! fc-check-here ;
: gen-constant ( -- ) fc-top-only fc-ct- fc-next! 0 swap fc-define ;
: gen-decimal ( -- ) ;
: gen-kernel-layout ( -- ) fc-top-only ;
: gen-backslash ( -- )
  begin fc-more? if fc-ch 10 <> else 0 then while 1 fc-pos +! repeat ;
: gen-paren ( -- ) begin fc-next! s" )" fc-is? until ;
: gen-char ( -- ) fc-code fc-next 0= if -16 fc-reject then fc-raw fc-literal ;
: gen-string ( -- ) fc-code fc-string-token dup >r fc-store-string fc-literal r> fc-literal ;
\ Literals, digits, numbers (14.7). A digit 0..9 is a word of the language, a synonym of a literal (kind 0, FC-LITERAL-NAME).
\ A number: LITERAL gets every word not found in the dictionary and builds the value from its digits modulo 2^32, else -13.
: fc-digit@ ( addr -- d )
  1 fc-lookup dup if dup 2 cells + @ 0= if 3 cells + @ exit then then -13 fc-reject ;
: gen-literal ( -- )
  fc-tok fc-tl @ over c@ [char] - = if 1 /string -1 else 1 then >r
  dup 0= if -13 fc-reject then
  0 -rot over + swap do 10 * i fc-digit@ + loop r> *
  fc-defining? if fc-literal else fc-ct+ then ;
\ The mechanisms of a word (14.11, language/doc/word.md). COST ( xt -- size bits copies layers known ) and PROVED?
\ ( xt -- f ) need the xt known at compile time (['] W just compiled), else -13. PRICE ( size bits copies layers -- n ): the sum.
: fc-known-xt ( -- xt ) fc-lit? 0= if -13 fc-reject then fc-pop1 drop fc-plv @ ;
: gen-cost ( -- )
  fc-known-xt fc-cost >r >r >r >r fc-literal r> fc-literal r> fc-literal r> fc-literal r> fc-literal ;
: gen-proved? ( -- ) fc-known-xt fc-proved? fc-literal ;
: gen-library ( -- ) -13 fc-reject ;   \ never called: FC-LIBRARY (FC-LONG, FC-PLATFORM) defines these names
: gen-price ( -- ) ['] gen+ gen-call ['] gen+ gen-call ['] gen+ gen-call ;
\ Platform 1, the host (15.3, language/doc/platform.md): HOST NAME in a definition makes it the definition of NAME on the
\ host: its text (the first : NAME of the source, words inline to the depth 16) becomes a C program (generators + - * and
\ or xor lshift rshift dup drop swap over, numbers, digits, else -13) in the stream at HB + 32, its length in bits at
\ HB = 2^30 + 2^29 + 2^22 K (K at most 16); K+1 goes to the cell 8 of the record.
variable fc-cpos variable fc-hn variable fc-cdepth create fc-hname 4096 allot
: fc-hb ( -- at ) fc-nhost @ 22 lshift 1610612736 + ;
: fc-c, ( addr u -- ) >r >r fc-cpos @ r> r@ lay-put r> 8 * fc-cpos +! ;
: fc-c1 ( c -- ) fc-eight c! fc-eight 1 fc-c, ;
: fc-c-gen ( record -- )
  dup 3 cells + @ ['] gen-paren = if drop gen-paren exit then
  fc-wt @ - 6 rshift dup 24 u< if 1 over lshift 15730631 and else 0 then 0= if -13 fc-reject then
  s" X(1" fc-c, dup 10 / 48 + fc-c1 10 mod 48 + fc-c1 s" );" fc-c, ;
: fc-c-body ( -- )
  fc-cdepth @ 64 = if -8 fc-reject then 1 fc-cdepth +!
  fc-tok fc-hname fc-tl @ cmove fc-tl @ fc-hn ! fc-pos @ >r 0 fc-pos !
  begin fc-next! s" :" fc-is? if fc-next! fc-hname fc-hn @ fc-is? else 0 then until
  begin fc-next! s" ;" fc-is? 0= while
    fc-find dup if dup 2 cells + @ dup 1 = if 2drop recurse 0 else 2 and if fc-c-gen 0 else drop
      fc-tok c@ 48 - 10 u< 0= if -13 fc-reject then -1 then then else drop -1 then
    if s" s[++p]=" fc-c, fc-tok fc-tl @ fc-c, 59 fc-c1 then
  repeat r> fc-pos ! -1 fc-cdepth +! ;
: gen-host ( -- )
  fc-guard @ fc-defining? 0= or if -13 fc-reject then fc-nhost @ 16 = if -8 fc-reject then
  fc-next! fc-hb 32 + fc-cpos ! 0 fc-cdepth !
  s" #include <stdio.h>" fc-c, 10 fc-c1 s" #define S(x) #x" fc-c, 10 fc-c1
  s" static unsigned s[300],t;static int p=8;static unsigned r8(unsigned b){unsigned r=0;int i;" fc-c,
  s" for(i=0;i<8;i++)r|=(b>>i&1)<<(7-i);return r;}static void X(int i){switch(i){" fc-c,
  s" case 100:s[p-1]+=s[p];break;case 101:s[p-1]-=s[p];break;case 102:s[p-1]*=s[p];break;" fc-c,
  s" case 106:s[p-1]&=s[p];break;case 107:s[p-1]|=s[p];break;case 108:s[p-1]^=s[p];break;" fc-c,
  s" case 109:s[p-1]=s[p]>31?0:s[p-1]<<s[p];break;case 110:s[p-1]=s[p]>31?0:s[p-1]>>s[p];break;" fc-c,
  s" case 120:s[p+1]=s[p];p+=2;break;case 122:t=s[p];s[p]=s[p-1];s[p-1]=t;p++;break;" fc-c,
  s" case 123:s[p+1]=s[p-1];p+=2;}p--;}int main(void){unsigned char b[4];FILE*f=fopen(S(host.io)," fc-c,
  s" S(r+b));if(!f||fread(b,1,4,f)!=4)return 1;s[8]=r8(b[0])|r8(b[1])<<8|r8(b[2])<<16|r8(b[3])<<24;" fc-c,
  10 fc-c1 fc-c-body 10 fc-c1 s" t=s[p];for(p=0;p<4;p++)b[p]=r8(t>>8*p&255);fseek(f,4,SEEK_SET);" fc-c,
  s" fwrite(b,1,4,f);fclose(f);return 0;}" fc-c, 10 fc-c1
  fc-cpos @ fc-hb - 32 - dup 4194272 u> if -8 fc-reject then 4 fc-hb lay-put-numeric
  fc-nhost @ dup 1+ fc-word @ 8 cells + ! fc-literal
  s" %host" dup fc-tl ! fc-tok swap cmove fc-word-token 1 fc-nhost +! ;
: fc-name2 ( c1 c2 -- addr u ) fc-tok 1+ c! fc-tok c! fc-tok 2 ;
\ Language name, generator, needs (1 multiplication, 2 division, 4 kernel layout, 8 comment, 16 proof words and FC-LIBRARY,
\ 32 the replacement, 64 the long copy, 128 the platforms); the digits: name, value.
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
  s" bye" ['] gen-bye 0 fc-generator
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
  s" check-table" ['] gen-library 19 fc-generator  s" accuracy" ['] gen-library 19 fc-generator
  s" replace" ['] gen-library 51 fc-generator
  s" long!" ['] gen-library 64 fc-generator  s" long@" ['] gen-library 64 fc-generator
  s" host" ['] gen-host 243 fc-generator  s" time" ['] gen-library 243 fc-generator
  s" platform" ['] gen-library 243 fc-generator  s" platform-of" ['] gen-library 243 fc-generator
  s" 0" 0 fc-literal-name  s" 1" 1 fc-literal-name  s" 2" 2 fc-literal-name  s" 3" 3 fc-literal-name
  s" 4" 4 fc-literal-name  s" 5" 5 fc-literal-name  s" 6" 6 fc-literal-name  s" 7" 7 fc-literal-name
  s" 8" 8 fc-literal-name  s" 9" 9 fc-literal-name ;
: fc-install-generators ( -- ) ['] fc-generators fc-gens ! ;
fc-install-generators
