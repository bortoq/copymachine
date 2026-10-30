\ Words of pForth used by the compiler libraries, defined for the direct
\ compiler (forthc), which builds in only the primitives of its subset.
\ Compiled before backend.fth, compute.fth and forthc.fth; pForth itself
\ has all of them. ALLOCATE takes from a heap that main.fth starts after the
\ static data; FREE gives back only the last allocation.
: nip ( a b -- b ) swap drop ;
: tuck ( a b -- b a b ) swap over ;
: -rot ( a b c -- c a b ) rot rot ;
: 2dup ( a b -- a b a b ) over over ;
: 2drop ( a b -- ) drop drop ;
: 2swap ( a b c d -- c d a b ) 3 roll 3 roll ;
: 2over ( a b c d -- a b c d a b ) 3 pick 3 pick ;
: ?dup ( x -- x x | 0 ) dup if dup then ;
: negate ( n -- -n ) 0 swap - ;
: invert ( x -- ~x ) -1 xor ;
: > ( a b -- f ) swap < ;
: u> ( a b -- f ) swap u< ;
: <> ( a b -- f ) = 0= ;
: 0< ( n -- f ) 0 < ;
: 0> ( n -- f ) 0 swap < ;
: 0<> ( x -- f ) 0= 0= ;
: max ( a b -- m ) 2dup < if swap then drop ;
: min ( a b -- m ) 2dup swap < if swap then drop ;
: +! ( n addr -- ) dup >r @ + r> ! ;
: 2@ ( addr -- x1 x2 ) dup cell+ @ swap @ ;
: 2! ( x1 x2 addr -- ) swap over ! cell+ ! ;
\ FILL and CMOVE go by cells when addresses and length are cell aligned.
variable fill-cell
: fill ( addr u c -- )
  over 3 and 3 pick 3 and or 0= if
    255 and 16843009 * fill-cell ! 2 rshift 0 ?do fill-cell @ over i cells + ! loop drop exit
  then swap 0 ?do 2dup swap i + c! loop 2drop ;
: cmove ( src dst u -- )
  dup 3 and 2 pick 3 and or 3 pick 3 and or 0= if
    2 rshift 0 ?do over i cells + @ over i cells + ! loop 2drop exit
  then 0 ?do over i + c@ over i + c! loop 2drop ;
: cmove> ( src dst u -- ) begin dup while 1- >r over r@ + c@ over r@ + c! r> repeat drop 2drop ;
: /string ( addr u n -- addr+n u-n ) tuck - >r + r> ;
: type ( addr u -- ) 0 ?do dup i + c@ emit loop drop ;
: compare ( a1 u1 a2 u2 -- n )
  rot 2dup swap - >r min 0 ?do
    over i + c@ over i + c@ - ?dup if 0< 2* 1+ nip nip unloop r> drop exit then
  loop 2drop r> dup if 0< 2* 1+ then ;
variable heap-ptr variable heap-last 524288 constant heap-end
: allocate ( u -- addr ior )
  3 + -4 and heap-ptr @ dup heap-last ! tuck + dup heap-end u> if 2drop 0 -59 exit then
  heap-ptr ! 0 ;
: free ( addr -- ior ) dup heap-last @ = if heap-ptr ! else drop then 0 ;
\ Never called here: FC| reads pForth's input line.
: source ( -- addr u ) 0 0 ;
variable >in
