"""Guest Forth backend versus copycode.vm1.backend: identical boot streams.

The guest builds a small program (forward-referenced cell, aligned group,
coalesced/split chunks, entry layer) and writes the stream to stdout. The
stream must match the host model byte for byte and run on checked-emulator.
"""
import subprocess
from guest_support import run_guest
import dependencies
from copycode.hostpaths import output_dir
from copycode.vm1.backend import Machine,Stream,Builder,Seq,copy

SIZE,CELL,CHUNK=65520,512,64
DATA,BUF,BLOCK=32768,40960,48000
MSG=b'copymachine 9.4.5\n'

def host():
    m=Machine(SIZE,8,CELL,CHUNK);stream=Stream(m);b=Builder(stream)
    stream.put(DATA,MSG)
    stream.put(DATA+8*(18+16),b'AB')
    stream.put(DATA+8*(18+16+2+40),b'CD')
    stream.put(BLOCK,bytes(range(200)))
    out=lambda n,src:(m.stdout,m.stdout,src,src+n)
    s=Seq(b);s.rows([copy(8*18,BUF,DATA)]);s.rows([out(8*18,BUF)])
    f=Seq(b);forward=f.layer()
    group=b.group(1)
    s.jump(forward.cell)
    forward.add(out(16,DATA+8*(18+16)));forward.next=group+CELL
    t=Seq(b,group+CELL);t.rows([out(48,DATA)]);t.jump(CELL)
    b.flush()
    return stream.finish(s.entry())

errors=[('bad-machine','1048560 8 512 64 cc-machine'),
        ('layer-full','cc-lone tl ! 8 0 do i 16 * dup 8 + 0 0 tl @ cc-row drop loop'),
        ('overlap','cc-lone tl ! 0 16 100 116 tl @ cc-row drop 8 24 200 216 tl @ cc-row drop'),
        ('field-overflow','cc-lone tl ! 0 1 65536 65537 tl @ cc-row drop 512 tl @ cc-next! cc-flush'),
        ('put-unaligned','32769 pad 1 cc-put'),('put-low','8 pad 1 cc-put'),('put-high','65520 pad 1 cc-put'),
        ('unlinked','cc-lone drop cc-flush')]
codes=[-24,-8,-9,-24,-9,-9,-9,-24]
lines=['create msg 18 allot']+[f'{b} msg {i} + c!' for i,b in enumerate(MSG)]
lines+=['create blob 200 allot',': fill-blob 200 0 do i blob i + c! loop ; fill-blob',
        'create ab 2 allot 65 ab c! 66 ab 1+ c!','create cd 2 allot 67 cd c! 68 cd 1+ c!',
        'variable tl variable entry variable forward variable group']
for i,(name,body) in enumerate(errors):
    lines+=[f'{SIZE} 8 {CELL} {CHUNK} cc-machine',f': bad-{i} {body} ;',f"' bad-{i} catch . cr"]
expected=b''.join(f'{c} \n'.encode() for c in codes)
lines+=[': build',
        f'  {SIZE} 8 {CELL} {CHUNK} cc-machine 2 cc-builder',
        f'  {DATA} msg 18 cc-put {DATA+8*34} ab 2 cc-put {DATA+8*76} cd 2 cc-put {BLOCK} blob 200 cc-put',
        f'  -1 cc-seq cc-layer tl ! 144 {BUF} {DATA} cc-copy tl @ cc-row drop cc-entry entry !',
        f'  cc-layer tl ! 144 {BUF} cc-out tl @ cc-row drop',
        '  cc-lone forward ! 1 cc-group group ! forward @ cc-layer-cell cc-jump',
        f'  16 {DATA+8*34} cc-out forward @ cc-row drop group @ {CELL} + forward @ cc-next!',
        f'  group @ {CELL} + cc-seq cc-layer tl ! 48 {DATA} cc-out tl @ cc-row drop {CELL} cc-jump',
        '  cc-flush entry @ cc-finish ;','build','bye']
stream=host()
run_guest('backend',['backend.fth'],lines,expected+stream+b'\n')
checked=output_dir(dependencies.VM2_ROOT,'build')/'checked-emulator'
result=subprocess.run([str(checked),'-s',str(SIZE),'-p','8'],input=stream,capture_output=True,timeout=120)
assert result.returncode==0 and result.stdout==MSG+b'AB'+MSG[:6],(result.returncode,result.stdout,result.stderr[-500:])
print('PASS guest backend stream:',len(stream),'bytes match the host model and run on checked-emulator',flush=True)
