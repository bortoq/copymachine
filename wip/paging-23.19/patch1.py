P='/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower/programs/l3c.tw'
s=open(P).read()
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt, (s.count(old), old[:80])
    s=s.replace(old,new)

# --- data
rep(":cnw data 8 26\n", ":cnw data 8 31\n")
rep(":s_long data 40 \"long\\n\"\n", """:s_long data 40 "long\\n"
:s_tp data 24 "&tp"
:s_ctp data 32 ":tp\\n"
:s_d14one data 56 "d 14 1\\n"
:s_lp data 144 "d 60 0\\nd 1 1\\nz 1f\\n"
:mk_a data 8 128
:mk_b data 8 64
""")
rep(":hv data 20 0\n:s13 data 13 0\n", """:hv data 20 0
:s13 data 13 0
:isptr table 3 1  0 0 0 0 0 1 0 0
:pgm data 1 0
:inpg data 1 0
:lpok data 1 0
:lnk data 1 0
:anyrec data 1 0
:wrk data 1 0
:sdir data 1 0
:wrs data 12 0
:sfj data 12 0
:skoff data 12 0
:c2_12 data 12 2
:c3_12 data 12 3
:rpos data 20 0
:tp data 20 0
:lpa data 20 0
:sptr data 20 0
:ptra data 20 0
:skk data 20 0
:sci data 20 0
:retout data 20 0
:cpw data 20 1024000
:cplim data 20 1035566
:climit data 20 1024000
:cnmax19 data 20 535854
:c1440 data 20 1440
:c1560 data 20 1560
:c1048416 data 20 1048416
:k5 data 3 5
:k6 data 3 6
:wtab data 8 1
""")

# --- kn3: a stack with w = 0 is a stack of links (2A = 40 bits); lnk tells
rep(""":kn3 block
copy &ga[0:20] &num
""", """:kn3 block
lut &isstk &wd[0:5] &q1
copy &q2[0] &q1
copy &q2[1] &na[0]
lut &and2 &q2 &q1
if &q1 &n_kn3a &n_kn3b
:n_kn3a block
copy &wxa &num
copy &wxb &z20
call &weq &n_kn3c
:n_kn3c block
copy &lnk &q5[4]
if &q5[4] &n_kn3d &n_kn3b
:n_kn3d block
copy &num &c40
goto &n_kn3b
:n_kn3b block
copy &ga[0:20] &num
""")
rep(""":kn6 block
copy &fd &one1
copy &fact &zero
goto &argfin""", """:kn6 block
copy &fd &one1
lut &isstk &wd[0:5] &fact
goto &argfin""")

# --- kt: the stack of push, pop, rec
rep(""":kt5 block
lut &isstore &wd[0:5] &q1
if &q1 &kt6 &kt7""", """:kt5 block
lut &isstkw &wd[0:5] &q1
if &q1 &n_kts &n_kt5b
:n_kts block
lut &isarr &fkind &q1
if &q1 &n_kts2 &lab
:n_kts2 block
add &fj &one12 &fr
lut &ski &fr[0:10] &ikind
lut &isptr &ikind &q1
if &q1 &n_kts3 &lab
:n_kts3 block
copy &sfj &fj
goto &kt7
:n_kt5b block
lut &isstore &wd[0:5] &q1
if &q1 &kt6 &kt7""")

# --- wstart
rep(""":ws2c1 block
copy &nm &lbl
call &find &ws2d
:ws2d block
if &fo &lab &ws2e
:ws2e block
if &nsym[10] &lab &ws5
:ws3 block
if &bopen &ws3b &blk""", """:ws2c1 block
if &pgm &blk &n_ws2c2
:n_ws2c2 block
copy &nm &lbl
call &find &ws2d
:ws2d block
if &fo &lab &ws2e
:ws2e block
lut &isstk &wd[0:5] &q1
if &q1 &n_ws2f &n_ws2g
:n_ws2f block
copy &wxa[0:12] &nsym
copy &wxa[12:20] &z20[0:8]
copy &wxb &c3a
call &wadd &n_ws2h
:n_ws2h block
if &wxr[10] &lab &ws5
:n_ws2g block
if &nsym[10] &lab &ws5
:ws3 block
lut &outb &wd[0:5] &q1
if &q1 &n_ws3o &n_ws3p
:n_ws3o block
if &bopen &blk &ws5
:n_ws3p block
if &bopen &ws3b &blk""")

open(P,'w').write(s)
