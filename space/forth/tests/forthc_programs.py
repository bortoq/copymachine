"""Programs of the direct Forth compiler tests (9.5), shared by the model test
(test_forthc.py) and the Forth compiler test (test_forthc_forth.py).

PROGRAMS run on pForth for the reference output. EXPECTED carry their output
where pForth is no reference: its MOD and /MOD are unsigned for negative
operands, it has no address checks and its division by zero is undefined.
"""
import random

PROGRAMS={
'arithmetic':': main 65 emit 3 4 + 60 + emit 100 33 - emit 6 7 and 64 or emit 70 3 xor emit ;',
'stack':': main 65 66 swap emit emit 67 68 over emit emit emit 69 70 71 rot emit emit emit 72 dup emit emit 73 74 drop emit ;',
'compare':': b ( f -- ) if 89 else 78 then emit ;\n'
          ': main 3 3 = b 3 4 = b 3 4 < b 4 3 < b -1 0 < b 0 -1 < b 0 0= b 5 0= b ;',
'if-nested':': c ( n -- ) dup 0 < if drop 45 else dup 0= if drop 48 else 10 < if 115 else 76 then then then emit ;\n'
            ': main -5 c 0 c 7 c 70 c ;',
'begin-until':': main 0 begin dup 48 + emit 1 + dup 5 = until drop ;',
'while-repeat':': main 10 begin dup while dup 64 + emit 2 - repeat drop ;',
'do-loop':': main 5 0 do i 48 + emit loop 3 0 do 2 0 do i j 0 + emit drop loop loop ;',
'variables':'variable x variable y\n: main 5 x ! 7 y ! x @ y @ + 48 + emit x @ 1 + x ! x @ 48 + emit ;',
'return-stack':': main 65 >r 66 >r r@ emit r> emit r> emit ;',
'calls':': sq dup + ; : quad sq sq ; : main 3 quad 48 + emit 10 quad emit ;',
'recursion':': fact ( n -- n! ) dup 1 < if drop 1 else dup 1 - recurse * then ;\n: main 5 fact emit 0 fact 48 + emit 4 fact emit ;',
'fib':': fib ( n -- f ) dup 2 < if exit then dup 1 - recurse swap 2 - recurse + ;\n'
      ': main 10 fib emit 12 fib 100 - emit ;',
'constant':'48 constant zero 7 constant seven\n: main zero seven + emit ;',
'loop-sum':'variable acc\n: main 0 acc ! 101 1 do acc @ i + acc ! loop acc @ 255 and emit acc @ 256 / emit ;',
}
PROGRAMS['execute']=': a 65 emit ; : b 66 emit ; : main [\'] a execute [\'] b execute [\'] a dup execute execute ;'
PROGRAMS['catch']=(': f 3 throw 65 emit ; : g 66 emit ; : h 7 f 8 ; : ok 0 throw 67 emit ;\n'
                   ': main 65 66 [\'] f catch 48 + emit emit emit [\'] g catch 48 + emit'
                   ' [\'] h catch 48 + emit [\'] ok catch 48 + emit 1 [\'] h catch 48 + emit 48 + emit ;')
# J is not in the subset.
PROGRAMS['do-loop']=': main 5 0 do i 48 + emit loop 3 0 do 2 0 do i 48 + emit loop loop ;'
B4=': b4 ( n -- ) 4 0 do dup 255 and emit 256 / loop drop ;\n'
PROGRAMS['multiply']=B4+(': main 6 7 * emit 3 dup * 48 + emit 123456 789 * b4 -3 5 * b4 -7 -9 * b4 65535 65537 * b4'
                         ' 2147483647 2147483647 * b4 -2147483648 -1 * b4 0 99 * b4 ;')
PROGRAMS['divide']=B4+(': main 100 7 / 48 + emit 1000000 3 / b4 -100 7 / b4 100 -7 / b4 -100 -7 / b4'
                       ' 2147483647 1 / b4 -2147483648 2 / b4 7 7 / 48 + emit 6 7 / 48 + emit ;')
PROGRAMS['modulo']=B4+': main 100 7 mod 48 + emit 17 5 /mod 48 + emit 48 + emit 1000000 999 mod b4 0 5 mod 48 + emit ;'

def s32(v):v&=0xffffffff;return v-(1<<32) if v>>31 else v
def tdiv(a,b):q=abs(a)//abs(b);return q if (a<0)==(b<0) else -q
def b4(v):
    out=b''
    for _ in range(4):out+=bytes([v&255]);v=tdiv(v,256)
    return out
rng=random.Random(9)
VALUES=[0,1,-1,2,7,-7,255,256,65535,65536,2**31-1,-2**31,123456789,-987654321]+\
       [rng.randint(-2**31,2**31-1) for _ in range(20)]+[rng.randint(-300,300) for _ in range(10)]
PAIRS=[(rng.choice(VALUES),rng.choice(VALUES)) for _ in range(40)]
DIV=[(a,b) for a,b in PAIRS if b and (a,b)!=(-2**31,-1)]
EXPECTED={
'mul-random':(B4+': main '+' '.join(f'{a} {b} * b4' for a,b in PAIRS)+' ;',b''.join(b4(s32(a*b)) for a,b in PAIRS)),
'divmod-random':(B4+': main '+' '.join(f'{a} {b} /mod b4 b4' for a,b in DIV)+' ;',
                 b''.join(b4(tdiv(a,b))+b4(a-b*tdiv(a,b)) for a,b in DIV)),
'mod-signs':(': main -7 2 mod 48 + emit 7 -2 mod 48 + emit -7 -2 mod 48 + emit -7 2 / 48 + emit 7 -2 /mod 48 + emit 48 + emit ;',
             bytes([47,49,47,45,45,49])),
'faults':(': bad 3 @ ; : far 16384 @ ; : neg -4 @ ; : st 5 2 ! ; : st2 5 20000 ! ; : z 7 0 / ; : zm 7 0 mod ;\n'
          ': ok 16380 @ drop 0 16380 ! ; : c 0 swap - emit ;\n'
          ": main ['] bad catch c ['] far catch c ['] neg catch c ['] st catch c ['] st2 catch c ['] z catch c"
          " ['] zm catch c ['] ok catch 48 + emit 1 2 ['] bad catch c 48 + emit 48 + emit ;",
          bytes([23,9,9,23,9,10,10,48,23,50,49])),
'uncaught-address':(': main 65 emit 1 @ 66 emit ;',b'A'),
'uncaught-zero':(': main 65 emit 0 0 / 66 emit ;',b'A'),
# The ok cell of an address check is entered by BEGIN and THEN with no row.
'empty-run':('variable x\n: main 1 x ! 0 if then x @ drop begin x @ 1 + dup x ! 3 = until x @ 48 + emit'
             ' 1 if x @ drop then 65 emit ;',b'3A'),
}


def wrapped(text,width=200):
    """Lines of at most width characters, broken at spaces (no \\ comments)."""
    out=[]
    for line in text.split('\n'):
        assert '\\' not in line.split()
        while len(line)>width:
            k=line.rindex(' ',0,width);out.append(line[:k]);line=line[k+1:]
        out.append(line)
    return '\n'.join(out)
