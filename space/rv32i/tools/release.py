"""Deterministic source release with declared dependency snapshots; no network."""
import argparse,gzip,hashlib,io,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'modules'))
import dependencies

def inventory(root):
    names=(root/'dist.manifest').read_text().splitlines()
    if names!=sorted(set(names)):raise ValueError('invalid manifest order')
    for name in names:
        p=PurePosixPath(name);file=root/name
        if p.is_absolute() or '..' in p.parts or str(p)!=name or not file.is_file() or (file.is_symlink()):raise ValueError('invalid source: '+name)
        if any(parent.is_symlink() for parent in file.parents if parent!=root.parent):raise ValueError('symlink source ancestor')
    return names

from copycode.hostpaths import output_dir

def create():
    files={name:(ROOT/name).read_bytes() for name in inventory(ROOT)};modes={name:(ROOT/name).stat().st_mode&0o777 for name in files}
    vendor={}
    for name,source in [('vm2',dependencies.VM2_ROOT),('emulator',dependencies.EMULATOR_ROOT),('copycode',dependencies.COPYCODE_ROOT)]:
        rows={n:(source/n).read_bytes() for n in inventory(source)}
        vendor[name]={n:hashlib.sha256(data).hexdigest() for n,data in rows.items()}
        for n,data in rows.items():
            key='vendor/'+name+'/'+n;files[key]=data;modes[key]=(source/n).stat().st_mode&0o777
    files['VENDORED.json']=(json.dumps(vendor,sort_keys=True,indent=2)+'\n').encode()
    files['SHA256SUMS']=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(files.items())).encode()
    version=(ROOT/'VERSION').read_text().strip();target=output_dir(ROOT, 'dist')/('rv32i-'+version+'.tar.gz');target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('wb') as stream:
        with gzip.GzipFile(fileobj=stream,filename='',mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT) as tar:
                for name,data in sorted(files.items()):
                    info=tarfile.TarInfo('rv32i-'+version+'/'+name);info.size=len(data);info.mode=modes.get(name,0o644)
                    tar.addfile(info,io.BytesIO(data))
    target.with_suffix(target.suffix+'.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
    print('Archive:',target);return target

def unpack(archive,base):
    with tarfile.open(archive) as tar:
        seen=set();prefix=None
        for member in tar.getmembers():
            path=PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or str(path)!=member.name or len(path.parts)<2 or member.name in seen:raise ValueError('unsafe archive')
            seen.add(member.name)
            if prefix is None:prefix=path.parts[0]
            if path.parts[0]!=prefix:raise ValueError('multiple archive roots')
            target=base/member.name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(tar.extractfile(member).read());target.chmod(member.mode&0o777)
    root=base/prefix;checks=(root/'SHA256SUMS').read_text().splitlines()
    if len(checks)+1!=len(seen):raise ValueError('checksum inventory mismatch')
    for line in checks:
        digest,name=line.split('  ',1)
        if prefix+'/'+name not in seen or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('checksum mismatch')
    return root

def check():
    from rv32i_toolchain import Toolchain
    compiler=Toolchain().compiler
    archive=output_dir(ROOT, 'dist')/('rv32i-'+(ROOT/'VERSION').read_text().strip()+'.tar.gz')
    with tempfile.TemporaryDirectory(prefix='rv32i standalone ') as tmp:
        root=unpack(archive,Path(tmp));env=dict(os.environ,RISCV_CC=compiler)
        for name in ('EMULATOR','EMULATOR_ROOT','VM2_ROOT','COPYCODE_ROOT','CHECKED_EMULATOR','MAKEFLAGS','MFLAGS','MAKELEVEL','PYTHONPATH'):
            env.pop(name,None)
        for name in ('emulator','vm2','copycode'):env[name.upper()+'_ROOT']=str(root/'vendor'/name)
        subprocess.run(['make','-j1','all','check'],cwd=root,env=env,check=True,timeout=165)
        subprocess.run([sys.executable,'-B','tools/release.py','create'],cwd=root,env=env,check=True,timeout=10)
        repeated=output_dir(root, 'dist')/archive.name
        if repeated.read_bytes()!=archive.read_bytes():raise ValueError('non-reproducible archive')
        subprocess.run(['make','clean'],cwd=root,env=env,check=True,timeout=10)
        assert not (output_dir(root, 'build')).exists() and (root/'rv32i').is_file()
    print('RV32I STANDALONE RELEASE PASSED: vendored sources, all checks, C guest, source-free CLI, deterministic repack and clean')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('create','check','clean'));a=p.parse_args()
    if a.action=='create':create()
    elif a.action=='check':check()
    else:
        for name in ('build','dist'):
            path=ROOT/name
            if path.is_symlink():path.unlink()
            elif path.exists():shutil.rmtree(path)
        print('Cleaned owned build/dist; preserved sources and toolchain cache')
if __name__=='__main__':main()
