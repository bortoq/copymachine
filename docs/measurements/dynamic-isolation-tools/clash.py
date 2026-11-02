import os, subprocess, sys
emu, l0 = sys.argv[1], sys.argv[2]
PRE = r'''
variable lay-size 2147483648 lay-size !
variable lay-l1 variable lay-h1 variable lay-l2 variable lay-h2 variable lay-ra variable lay-rb
: 2@ dup cell+ @ swap @ ;
: lay-clash? ( lo1 hi1 lo2 hi2 -- flag )
  lay-h2 ! lay-l2 ! lay-h1 ! lay-l1 !
  lay-l1 @ lay-h1 @ u< lay-l2 @ lay-h2 @ u< and
  lay-l1 @ lay-h2 @ u< and lay-l2 @ lay-h1 @ u< and
  lay-l1 @ lay-size @ u< and lay-l2 @ lay-size @ u< and ;
: lay-row-clash? ( row1 row2 -- flag )
  lay-rb ! lay-ra ! 0
  2 0 do 2 0 do
    lay-ra @ j 2* cells + 2@ swap lay-rb @ i 2* cells + 2@ swap lay-clash? or
  loop loop ;
create ra 16 allot create rb 16 allot create rc 16 allot create rd 16 allot
: init 1073741824 ra ! 1073741856 ra 4 + ! 1073742000 ra 8 + ! 1073742032 ra 12 + !
       1073745824 rb ! 1073745856 rb 4 + ! 1073746000 rb 8 + ! 1073746032 rb 12 + !
       1073755824 rc ! 1073755856 rc 4 + ! 1073756000 rc 8 + ! 1073756032 rc 12 + !
       1073765824 rd ! 1073765856 rd 4 + ! 1073766000 rd 8 + ! 1073766032 rd 12 + ! ;
: w ;
'''
def ticks(body, n):
    src = f'{PRE}\n: main init {n} 0 do {body} loop ;\n'.encode()
    p = subprocess.run([emu, '-s', '2147483648', '-p', '8'], input=open(l0, 'rb').read() + src + b'\0', capture_output=True, check=False, env=dict(os.environ, HW_TICKS='1'))
    err = p.stderr.decode().split(); assert p.returncode == 0 and err, p.stdout[:100]
    return int(err[1])
def per(b): return (ticks(b, 9) - ticks(b, 1)) / 8
base = per('')
for k, b in {'one row pair (lay-row-clash?)': 'ra rb lay-row-clash? drop',
             'against 3 rows (a dynamic copy in a layer of 4 rows)': 'ra rb lay-row-clash? drop ra rc lay-row-clash? drop ra rd lay-row-clash? drop'}.items():
    print(k, round(per(b) - base, 1))
