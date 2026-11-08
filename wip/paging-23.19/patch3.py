P='/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower/programs/l3c.tw'
s=open(P).read()
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt, (s.count(old), old[:80])
    s=s.replace(old,new)

rep(""":n_act1r block
if &wd[0] &a_push &a_push""", """:n_act1r block
goto &a_push""")

# a_block, a_word
rep(""":a_block block
copy &coded &one1
emit &s_cb
copy &pnm &lbl
call &pname &ab2
:ab2 block
emit &nl8
copy &bopen &one1
ret

:a_word block
copy &coded &one1
copy &q &z20
call &chk &aw1""", """:a_block block
call &pgclose &n_ab0
:n_ab0 block
copy &coded &one1
emit &s_cb
copy &pnm &lbl
call &pname &ab2
:ab2 block
emit &nl8
call &begin &n_ab3
:n_ab3 block
copy &bopen &one1
ret

:a_word block
call &pgclose &n_aw0
:n_aw0 block
copy &coded &one1
copy &q &z20
call &chk &aw1""")
rep(""":aw3 block
emit &nl8
copy &curw &lbl
copy &hasw &one1
copy &bopen &one1
ret""", """:aw3 block
emit &nl8
call &begin &n_aw4
:n_aw4 block
copy &curw &lbl
copy &hasw &one1
copy &bopen &one1
copy &wrk &zero
if &anyrec &n_aw5 &actret
:n_aw5 block
copy &nm &lbl
copy &nm[8] &one1
call &find &n_aw6
:n_aw6 block
copy &wrk &fo
copy &wrs &faddr[0:12]
ret""")

# long in a page
rep(""":lo1 block
copy &wxa &cnmax
copy &wxb &gb[20:40]
call &wlt &xq78""", """:lo1 block
if &pgm &blk &n_lo1b
:n_lo1b block
copy &wxa &cnmax
copy &wxb &gb[20:40]
call &wlt &xq78""")

# a_call
rep(""":a_call block
copy &q &z20
call &chk &acl1
:acl1 block
emit &s_c28r""", """:a_call block
copy &q &z20
call &chk &n_acl0
:n_acl0 block
if &anyrec &n_acl0b &acl1
:n_acl0b block
copy &nm &bn0
copy &nm[8] &one1
call &find &n_acl0c
:n_acl0c block
if &fo &n_acr &acl1
:n_acr block
copy &sfj &faddr[0:12]
copy &skoff &zero12
call &stkload &n_acr2
:n_acr2 block
call &stkptr &n_acr3
:n_acr3 block
store &qa &y0 &ptra
copy &wxa &pos
copy &wxb &c1440
call &wadd &n_acr4
:n_acr4 block
copy &s21 &wxr
store &qa &y1 &s21[0:20]
copy &lmode &one1
call &lutgen &n_acr5
:n_acr5 block
copy &skoff &c2_12
call &stkload &n_acr6
:n_acr6 block
store &qa &y0 &ptra
store &qa &y1 &ptra
copy &lmode &zero
call &lutgen &acl4
:acl1 block
emit &s_c28r""")

# a_ret
rep(""":a_ret block
copy &q &z20
call &chk &ar1
:ar1 block
emit &s_c28""", """:a_ret block
copy &q &z20
call &chk &n_ar0
:n_ar0 block
if &wrk &n_arr &ar1
:n_arr block
copy &sfj &wrs
copy &wxa &pos
copy &wxb &c1560
call &wadd &n_arr1
:n_arr1 block
copy &s21 &wxr
copy &retout &s21[0:20]
copy &skoff &c3_12
call &stkload &n_arr2
:n_arr2 block
call &stkptr &n_arr3
:n_arr3 block
store &qa &y0 &ptra
store &qa &y1 &ptra
copy &lmode &zero
call &lutgen &n_arr4
:n_arr4 block
copy &skoff &zero12
call &stkload &n_arr5
:n_arr5 block
store &qa &y0 &ptra
store &qa &y1 &retout
copy &lmode &zero
call &lutgen &ar4
:ar1 block
emit &s_c28""")

# the new actions, before the arithmetic of 20 bits
rep("""# --- the arithmetic of 20 bits as words""", """# page 0|1: the blocks which follow go to the tail of the image (1) or stay in the space (0); the first time lp, the position of the long copy of the
# loader, is made (128 bits: area 1)
:a_page block
if &packm &actret &n_pg1
:n_pg1 block
call &pgclose &n_pg2
:n_pg2 block
lut &av &k0i &ga
if &ga[0] &n_pg3 &n_pg5
:n_pg3 block
if &lpok &n_pg5 &n_pg4
:n_pg4 block
copy &q &c128
call &chk &n_pg4b
:n_pg4b block
copy &lpa &pos
copy &lpok &one1
emit &s_lp
copy &wxa &pos
copy &wxb &c128
call &wadd &n_pg4c
:n_pg4c block
copy &s21 &wxr
copy &pos &s21[0:20]
goto &n_pg5
:n_pg5 block
lut &av &k0i &ga
copy &pgm &ga[0]
goto &actret

# stack K w: the array is in (tbegin); the pointer (K zero bits), then the tables inc and dec (K bits an entry), named as the stack with the bit
# nm[0] set (a mark no name of a user has); the three symbols follow the array
:a_stack block
lut &av &k0i &ga
copy &skk &ga[0:20]
copy &lbl[0] &one1
copy &q &skk
call &chk &n_as1
:n_as1 block
copy &zc &skk
call &zrun &n_as2
:n_as2 block
copy &sptr &pos
copy &wxa &pos
copy &wxb &skk
call &wadd &n_as3
:n_as3 block
copy &s21 &wxr
copy &pos &s21[0:20]
copy &nm &lbl
copy &ikind &k5
copy &iaddr &sptr
copy &iinfo[0] &lnk
copy &iinfo[1:19] &z20[0:18]
call &insert &n_as4
:n_as4 block
lut &av &k0i &ga
store &av &k1i &ga
copy &wd &wtab
copy &sdir &zero
call &tbegin &n_as5
:n_as5 block
call &tabloop &n_as6
:n_as6 block
if &sdir &actret &n_as8
:n_as8 block
copy &sdir &one1
call &tbegin &n_as5

# rec w s: the word w is recursive, its calls and returns go through the stack s of links (the symbol w marked with nm[8], the address: the stack)
:a_rec block
add &sfj &one12 &fr
lut &sin &fr[0:10] &finfo
if &finfo[0] &n_rc1 &wid
:n_rc1 block
copy &nm &bn0
copy &nm[8] &one1
call &find &n_rc2
:n_rc2 block
if &fo &lab &n_rc3
:n_rc3 block
if &nsym[10] &lab &n_rc4
:n_rc4 block
copy &ikind &k6
copy &iaddr[0:12] &sfj
copy &iaddr[12:20] &z20[0:8]
copy &iinfo &z20[0:19]
copy &anyrec &one1
call &insert &actret

# push s x, pop s x (wd[0]: 1 pop): the store and the inc, or the dec and the lut
:a_push block
copy &sdir &wd[0]
lut &av &k0i &ga
copy &sptr &ga[0:20]
add &sfj &one12 &fr
lut &sin &fr[0:10] &finfo
if &finfo[0] &wid &n_pu1
:n_pu1 block
copy &wxa &ga[20:40]
copy &wxb &tout20
call &weq &n_pu2
:n_pu2 block
if &q5[4] &n_pu3 &wid
:n_pu3 block
copy &q &z20
call &chk &n_pu4
:n_pu4 block
call &stkptr &n_pu5
:n_pu5 block
if &sdir &n_pop &n_push
:n_push block
store &qa &y0 &ptra
store &qa &y1 &sptr
copy &lmode &one1
copy &skoff &zero12
call &stkload &n_pu6
:n_pu6 block
call &lutgen &n_pu7
:n_pu7 block
copy &skoff &c2_12
call &stkload &n_pu8
:n_pu8 block
store &qa &y0 &ptra
store &qa &y1 &ptra
copy &lmode &zero
call &lutgen &actret
:n_pop block
copy &skoff &c3_12
call &stkload &n_pu9
:n_pu9 block
store &qa &y0 &ptra
store &qa &y1 &ptra
copy &lmode &zero
call &lutgen &n_pu10
:n_pu10 block
copy &skoff &zero12
call &stkload &n_pu11
:n_pu11 block
store &qa &y0 &ptra
store &qa &y1 &sptr
copy &lmode &zero
call &lutgen &actret

# --- the arithmetic of 20 bits as words""")

# the end of the text
rep(""":eot3 block
if &bopen &blk &fin1""", """:eot3 block
if &bopen &blk &n_fin0
:n_fin0 block
call &pgclose &n_fin0b
:n_fin0b block
if &lpok &n_fin0c &fin1
:n_fin0c block
call &ldr &fin1""")
rep(""":fin10 block
emit &s_cole
emit &zero8
halt""", """:fin10 block
emit &s_cole
if &lpok &n_fin11 &n_fin12
:n_fin11 block
copy &wxa &c1048416
copy &wxb &pos
call &wsub &n_fin11b
:n_fin11b block
copy &zc &wxr[0:20]
call &zrun &n_fin12
:n_fin12 block
emit &zero8
halt""")
open(P,'w').write(s)
