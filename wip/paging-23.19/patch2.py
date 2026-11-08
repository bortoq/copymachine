P='/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower/programs/l3c.tw'
s=open(P).read()
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt, (s.count(old), old[:80])
    s=s.replace(old,new)

# --- lastx: jtv 0 is the jump to the loader
rep(""":lx2 block
emit &s_ae
goto &lxe""", """:lx2 block
if &jtv[1] &n_lx2e &n_lx2p
:n_lx2e block
emit &s_ae
goto &lxe
:n_lx2p block
emit &s_tp
goto &lxe""")

# --- new words, before the bytes of the string
rep("""# the bytes of the string in hand: d 8 <byte>
:ebytes word""", """# --- pages (23.19). The end of a block of a page: the mark, the bits of the tail grow by the block, the position goes back to the space
:pgclose word
if &inpg &n_pgc1 &n_pgcx
:n_pgcx block
ret
:n_pgc1 block
emit &mk_b
copy &wxa &pos
copy &wxb &cpw
call &wsub &n_pgc2
:n_pgc2 block
copy &s21 &wxr
copy &wxa &tp
copy &wxb &s21[0:20]
call &wadd &n_pgc3
:n_pgc3 block
copy &s21 &wxr
copy &tp &s21[0:20]
copy &pos &rpos
copy &limit &climit
copy &inpg &zero
ret

# the start of a block or a word (its label is out): in a page a stub in the space (a copy of 40 bits of the place in the tail into lp, a layer
# with a jump to the loader, the 40 bits) and the position goes to the window (the block follows between the marks)
:begin word
if &pgm &n_bg1 &n_bgx
:n_bgx block
ret
:n_bg1 block
copy &q &z20
call &chk &n_bg2
:n_bg2 block
copy &p1 &c40
copy &p2 &lpa
copy &wxa &pos
copy &wxb &c320
call &wadd &n_bg3
:n_bg3 block
copy &s21 &wxr
copy &p3 &s21[0:20]
call &lc &n_bg4
:n_bg4 block
copy &jtv &y0
call &lastx &n_bg5
:n_bg5 block
emit &s_d14
copy &h &tp
call &puthex &n_bg6
:n_bg6 block
emit &nl8
emit &s_d14one
copy &wxa &pos
copy &wxb &c40
call &wadd &n_bg7
:n_bg7 block
copy &s21 &wxr
copy &rpos &s21[0:20]
copy &pos &cpw
copy &limit &cplim
copy &inpg &one1
emit &mk_a
ret

# the loader (at the end, once): the long copy of NMAX bits from lp into the window, a layer with a jump to the window
:ldr word
emit &s_ctp
emit &s_long
store &bua &k0i &one1
copy &qd1 &cnmax19
copy &qd2 &lpa
copy &qd3 &cpw
copy &qd4 &pos
call &lq &n_ldr2
:n_ldr2 block
copy &wxa &pos
copy &wxb &c1600
call &wadd &n_ldr3
:n_ldr3 block
copy &s21 &wxr
copy &pos &s21[0:20]
emit &s_gap
emit &s_jmp
copy &h &cpw
call &puthex &n_ldr4
:n_ldr4 block
emit &nl8
copy &wxa &pos
copy &wxb &c160
call &wadd &n_ldr5
:n_ldr5 block
copy &s21 &wxr
copy &pos &s21[0:20]
ret

# a part of the stack in sfj (+ skoff: 0 the array, 2 inc, 3 dec): the table in hand; the pointer of the stack (+1) goes to ptra
:stkload word
add &sfj &skoff &fr
lut &sad &fr[0:10] &tadr
lut &sin &fr[0:10] &tinfo
copy &tbl &zero
call &loadinfo &n_skl2
:n_skl2 block
ret

:stkptr word
add &sfj &one12 &fr
lut &sad &fr[0:10] &ptra
ret

# one entry of a table of a stack: d <m> <num>, the zeros up to the stride
:tabent word
emit &s_d
copy &h &tstm
call &puthex &n_te2
:n_te2 block
emit &sp
copy &h &num
call &puthex &n_te3
:n_te3 block
emit &nl8
copy &wxa &tstr20
copy &wxb &tstm
call &wsub &n_te4
:n_te4 block
copy &s21 &wxr
copy &zc &s21[0:20]
call &zrun &n_te5
:n_te5 block
ret

# the entries of the table in hand (2^K): (i + 1) or (i - 1) by sdir, modulo 2^K
:tabloop word
copy &sci &z20
goto &n_tlp
:n_tlp block
copy &wxa &sci
copy &wxb &c1
if &sdir &n_tdec &n_tinc
:n_tinc block
call &wadd &n_tl2
:n_tdec block
call &wsub &n_tl2
:n_tl2 block
copy &s21 &wxr
lut &mask &skk[0:5] &mk
band &s21[0:20] &mk &num
call &tabent &n_tl3
:n_tl3 block
copy &wxa &sci
copy &wxb &c1
call &wadd &n_tl4
:n_tl4 block
copy &s21 &wxr
copy &sci &s21[0:20]
copy &wxa &sci
copy &wxb &tcnt
call &weq &n_tl5
:n_tl5 block
if &q5[4] &n_tl6 &n_tlp
:n_tl6 block
ret

# the bytes of the string in hand: d 8 <byte>
:ebytes word""")

# --- the tree of the words
rep(""":act1x block
lut &or2 &wd[1:3] &q1
if &q1 &a_lib &act1y
:act1y block
if &wd[3] &a_long &act1z
:act1z block
if &wd[0] &a_key &a_warn""", """:act1x block
if &wd[3] &n_act1w &n_act1v
:n_act1v block
lut &or2 &wd[1:3] &q1
if &q1 &a_lib &act1z
:act1z block
if &wd[0] &a_key &a_warn
:n_act1w block
if &wd[2] &n_act1u &n_act1t
:n_act1t block
if &wd[1] &n_act1s &a_long
:n_act1s block
if &wd[0] &a_stack &a_page
:n_act1u block
if &wd[1] &a_rec &n_act1r
:n_act1r block
if &wd[0] &a_push &a_push""")
open(P,'w').write(s)
