"""Public launcher: pipes, live input, regular files, descriptors, cache, errors."""
import json,os,select,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vm2guest.compiler import compile_guest
from copycode.vm2.boundary import Format,Program,boot_stream,record,protocol
from vm2_reference import run as reference
from copycode.hostpaths import output_dir

EMULATOR=Path(os.environ.get('EMULATOR',output_dir((ROOT.parent.parent if ROOT.parent.name == 'space' else ROOT.parent)/'emulator')/'bitcopy/emulator')).resolve()
launcher=ROOT/'vm2'
with tempfile.TemporaryDirectory() as folder:
    cache=Path(folder)/'cache';env=dict(os.environ,EMULATOR=str(EMULATOR),VM2_CACHE=str(cache),PYTHONDONTWRITEBYTECODE='1')
    p=Program(code_base=8192);at=p.allocate(b'go?');p.step([(24,65522,at)])
    p.step([(16,1024,65521)]);p.step([(16,65522,1024)])
    packet=boot_stream(p.finish(),65520,8)
    child=subprocess.Popen([str(launcher),'-p8'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    child.stdin.write(packet);child.stdin.flush()
    assert select.select([child.stdout],[],[],15)[0],'no live prompt'
    assert os.read(child.stdout.fileno(),3)==b'go?'
    child.stdin.write(b'ABtail');child.stdin.flush()
    assert child.wait(timeout=15)==0
    assert child.stdout.read()==b'AB' and child.stderr.read()==b''
    child.stdin.close()
    print('PASS live prompt, binary input, early guest halt with parent input still open')
    first_folder=next(cache.iterdir())
    first={p.name:p.read_bytes() for p in first_folder.iterdir()}
    r=subprocess.run([str(launcher),'-p8'],input=packet+b'CD',capture_output=True,env=env,timeout=15)
    assert r.returncode==0 and r.stdout==b'go?CD' and r.stderr==b''
    assert first=={p.name:p.read_bytes() for p in first_folder.iterdir()}
    print('PASS deterministic cache reuse')
    # For seekable stdin both size and offset zero refer to the guest stream.
    ops,q,rsp=protocol(65520);f=Format(65520,8)
    p=Program(code_base=8192)
    stat=p.allocate(record(q,dict(op=3,chan=65521)));seek=p.allocate(record(q,dict(op=2,chan=65521,arg=0,off=0)))
    p.layer([(q[1],65520,stat)]);p.layer([(rsp[1],1024,65520)])
    p.layer([(rsp[1],65522,1024)]);p.layer([(q[1],65520,seek)])
    p.layer([(8,1200,65521)]);p.layer([(8,65522,1200)])
    packet=boot_stream(p.finish(),65520,8)
    expected=reference(packet)
    source=Path(folder)/'input';source.write_bytes(packet)
    with source.open('rb') as data:
        result=subprocess.run([str(launcher),'-p8'],stdin=data,capture_output=True,env=env,timeout=15)
    file_reference=reference(packet,regular=True)
    assert result.returncode==0 and result.stdout==bytes(file_reference['channels'][2]['data']) and not result.stderr,(result.returncode,result.stdout.hex(),bytes(file_reference['channels'][2]['data']).hex(),result.stderr)
    # The inherited regular-file cursor is supported, not only offset zero.
    source.write_bytes(b'junk'+packet)
    with source.open('rb') as data:
        data.seek(4)
        result=subprocess.run([str(launcher),'-p8','-t1'],stdin=data,capture_output=True,env=env,timeout=15)
    assert result.returncode==0 and result.stdout==b'' and result.stderr==b''
    p=Program(code_base=8192);at=p.allocate(b'offset-ok');p.step([(72,65522,at)])
    source.write_bytes(b'junk'+boot_stream(p.finish(),65520,8))
    with source.open('rb') as data:
        data.seek(4)
        result=subprocess.run([str(launcher),'-p8'],stdin=data,capture_output=True,env=env,timeout=15)
    assert result.returncode==0 and result.stdout==b'offset-ok' and result.stderr==b'',result
    print('PASS regular stdin FSTAT/SEEK and nonzero inherited cursor')
    for args in [('-s0',),('-p0',),('-s-1',),('-t-1',),('-s+123',),('-t18446744073709551616',),('--core','x'),('--backend','network')]:
        result=subprocess.run([str(launcher),*args],input=b'',capture_output=True,env=env,timeout=10)
        assert result.returncode==2,(args,result)
    print('PASS invalid CLI/configuration returns 2')
    # ABI cache entries are integrity checked before execution.
    key=first_folder;(key/'boot.bin').write_bytes(b'corrupt')
    result=subprocess.run([str(launcher),'-p8'],input=b'',capture_output=True,env=env,timeout=10)
    assert result.returncode==2 and b'corrupt vm2 guest cache' in result.stderr
    print('PASS corrupt cache rejected')
print('ALL public launcher checks passed')
