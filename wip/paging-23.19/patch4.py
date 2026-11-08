P='/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower/programs/l4p.tw'
s=open(P).read()
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt, (s.count(old), old[:80])
    s=s.replace(old,new)

rep(""":qdd data 20 0
""", """:qdd data 20 0

# --- the pages (23.19): the text between the bytes 1 and 2 is kept on the host (area 1, the file of -r), in pieces of 1024 bytes, and comes out at the end
:pb data 8192 0
:pb2 data 8192 0
:pcn data 20 0
:nch data 20 0
:wpos data 128 0
:one1 data 1 1
:mka data 8 128
:mkb data 8 64
:c1 data 20 1
:c1024 data 20 1024
""")
rep(""":main block
goto &ls
""", """:main block
copy &wpos[96:97] &one1
goto &ls
""")
rep(""":ls block
key &ch
eq &ch &zero8 &q2
if &q2[1] &eot &ls1
:ls1 block""", """:ls block
key &ch
eq &ch &zero8 &q2
if &q2[1] &eot &n_ls0
:n_ls0 block
eq &ch &mka &q2
if &q2[1] &n_pg &ls1
:ls1 block""")
rep(""":eot2 block
emit &zero8
halt
""", """:eot2 block
call &pdone &eot3
:eot3 block
emit &zero8
halt

# a page: the characters go into the buffer up to the byte 2
:n_pg block
key &ch
eq &ch &zero8 &q2
if &q2[1] &eot &n_pg1
:n_pg1 block
eq &ch &mkb &q2
if &q2[1] &ls &n_pg2
:n_pg2 block
call &pput &n_pg

# a character of a page into the buffer (it comes in at the top and moves down); a full buffer goes to the host
:pput word
shr &pb &pb2 8
copy &pb &pb2
copy &pb[8184:8192] &ch
copy &wxa &pcn
copy &wxb &c1
call &wadd &n_pp1
:n_pp1 block
copy &pcn &wxr[0:20]
copy &wxa &pcn
copy &wxb &c1024
call &weq &n_pp2
:n_pp2 block
if &q5[4] &n_pp3 &n_ppx
:n_pp3 block
long! &wpos &pb
copy &pcn &z20
copy &wxa &wpos[13:33]
copy &wxb &c1
call &wadd &n_pp4
:n_pp4 block
copy &wpos[13:33] &wxr[0:20]
goto &n_ppx
:n_ppx block
ret

# the end: the buffer is filled up with line breaks and written, then the pieces come back from the host and out
:pdone word
goto &n_pd1
:n_pd1 block
copy &wxa &pcn
copy &wxb &z20
call &weq &n_pd2
:n_pd2 block
if &q5[4] &n_pd4 &n_pd3
:n_pd3 block
copy &ch &nl8
call &pput &n_pd1
:n_pd4 block
copy &nch &wpos[13:33]
copy &wpos[13:33] &z20
goto &n_pd5
:n_pd5 block
copy &wxa &wpos[13:33]
copy &wxb &nch
call &weq &n_pd6
:n_pd6 block
if &q5[4] &n_pd9 &n_pd7
:n_pd7 block
long@ &wpos &pb
emit &pb
copy &wxa &wpos[13:33]
copy &wxb &c1
call &wadd &n_pd8
:n_pd8 block
copy &wpos[13:33] &wxr[0:20]
goto &n_pd5
:n_pd9 block
ret
""")
rep(""":wlt word
lt &wxa &wxb &ltc
ret""", """:wlt word
lt &wxa &wxb &ltc
ret
:weq word
eq &wxa &wxb &q5
ret""")
open(P,'w').write(s)
