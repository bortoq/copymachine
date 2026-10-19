#!/usr/bin/env python3
"""Reproducible vm2 source release, declared dependency snapshots, staged install."""
import argparse,gzip,hashlib,io,json,os,re,shutil,subprocess,tarfile,tempfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]

def version(root):
    value=(root/'VERSION').read_text().strip()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?',value):raise ValueError('invalid version')
    return value

def file_list(root):
    names=(root/'dist.manifest').read_text().splitlines()
    if names!=sorted(set(names)):raise ValueError('invalid source manifest order')
    for name in names:
        p=PurePosixPath(name);source=root/name
        archived=source.resolve()==root.parent/'legacy'/root.name/name
        if not name or p.is_absolute() or '..' in p.parts or str(p)!=name or (source.is_symlink() and not archived) or not source.is_file():raise ValueError('invalid source path: '+name)
        if not archived and any(parent.is_symlink() for parent in source.parents if parent!=root.parent):raise ValueError('symlink source ancestor')
    return names

def dependencies(root):
    for name,variable in [('copycode','COPYCODE_ROOT'),('vm1','VM1_ROOT')]:
        bundled=root/'vendor'/name
        yield name,bundled if bundled.is_dir() else Path(os.environ.get(variable,root.parent/name)).resolve()

def create(root,output):
    payload={n:(root/n).read_bytes() for n in file_list(root)}
    modes={n:(0o755 if (root/n).stat().st_mode&0o111 else 0o644) for n in payload}
    vendors={}
    for name,source in dependencies(root):
        files={n:(source/n).read_bytes() for n in file_list(source)}
        identities={n:hashlib.sha256(data).hexdigest() for n,data in sorted(files.items())}
        vendors[name]=dict(schema='source-snapshot-v1',tree_sha256=hashlib.sha256(json.dumps(identities,sort_keys=True,separators=(',',':')).encode()).hexdigest(),files=identities)
        for n,data in files.items():
            key='vendor/'+name+'/'+n;payload[key]=data;modes[key]=0o755 if (source/n).stat().st_mode&0o111 else 0o644
    payload['VENDORED.json']=(json.dumps(vendors,sort_keys=True,indent=2)+'\n').encode()
    payload['SHA256SUMS']=''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name,data in sorted(payload.items())).encode()
    epoch=int(os.environ.get('SOURCE_DATE_EPOCH','0'))
    if not 0<=epoch<=0xffffffff:raise ValueError('invalid SOURCE_DATE_EPOCH')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent,delete=False) as raw:
        temporary=Path(raw.name)
        try:
            with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=epoch) as gz:
                with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT) as tar:
                    for name,data in sorted(payload.items()):
                        info=tarfile.TarInfo('vm2-'+version(root)+'/'+name);info.size=len(data);info.mtime=epoch;info.mode=modes.get(name,0o644)
                        tar.addfile(info,io.BytesIO(data))
            raw.flush();temporary.replace(output)
        finally:temporary.unlink(missing_ok=True)
    digest=hashlib.sha256(output.read_bytes()).hexdigest();output.with_name(output.name+'.sha256').write_text(f'{digest}  {output.name}\n')
    return output

def unpack(path,folder):
    with tarfile.open(path) as tar:
        names=set();prefix=None
        for member in tar.getmembers():
            p=PurePosixPath(member.name)
            if not member.isfile() or p.is_absolute() or '..' in p.parts or str(p)!=member.name or len(p.parts)<2 or member.name in names:raise ValueError('unsafe archive')
            names.add(member.name)
            if prefix is None:prefix=p.parts[0]
            if p.parts[0]!=prefix:raise ValueError('multiple archive roots')
        for member in tar.getmembers():
            target=folder/member.name;target.parent.mkdir(parents=True,exist_ok=True)
            with tar.extractfile(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
            target.chmod(member.mode&0o777)
    root=folder/prefix
    if prefix!='vm2-'+version(root):raise ValueError('archive version mismatch')
    sums=(root/'SHA256SUMS').read_text().splitlines()
    if len(sums)+1!=len(names):raise ValueError('checksum inventory mismatch')
    for line in sums:
        digest,name=line.split('  ',1)
        if prefix+'/'+name not in names or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('checksum mismatch: '+name)
    vendors=json.loads((root/'VENDORED.json').read_text())
    expected=set(file_list(root))|{'VENDORED.json','SHA256SUMS'}
    for name,source in dependencies(root):
        listed=file_list(source)
        actual={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in listed}
        if actual!=vendors[name]['files']:raise ValueError('dependency snapshot mismatch')
        expected.update('vendor/'+name+'/'+n for n in listed)
    if {prefix+'/'+n for n in expected}!=names:raise ValueError('unexpected archive files')
    return root

def staged(destdir,path):
    p=Path(path)
    if not p.is_absolute() or '..' in p.parts:raise ValueError('installation paths must be absolute without ..')
    return Path(destdir)/str(p).lstrip('/') if destdir else p

def install(root,destdir,bindir,libdir,docdir):
    binary=staged(destdir,bindir)/'vm2';libraries=staged(destdir,libdir);docs=staged(destdir,docdir)
    binary.parent.mkdir(parents=True,exist_ok=True)
    relative=os.path.relpath(libdir,bindir)
    binary.write_text('#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\nsys.path.insert(0,str((Path(__file__).resolve().parent/'+repr(relative)+').resolve()))\nfrom vm2guest.cli import main\nraise SystemExit(main())\n');binary.chmod(0o755)
    def copy(source,target):target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);target.chmod(0o644)
    for package in ('vm2guest','vm2compile'):
        for p in (root/package).glob('*.py'):copy(p,libraries/package/p.name)
    native=binary.with_name('vm2c')
    native.write_text(binary.read_text().replace('from vm2guest.cli import main','from vm2compile.cli import main'));native.chmod(0o755)
    deps=dict(dependencies(root));source=deps['copycode']
    copy(deps['vm1']/'src/proto.def',libraries/'vm2compile/vm1-proto.def')
    for name in file_list(source):
        if name.startswith('src/copycode/'):copy(source/name,libraries/Path(name).relative_to('src'))
        elif name=='LICENSE' or name.startswith('LICENSES/'):copy(source/name,docs/'dependencies/copycode'/name)
    for name in file_list(root):
        if name.startswith(('doc/','examples/direct/','sdk/')) or name in ('README.md','VERSION','LICENSE','CHANGELOG.md','proto.def'):copy(root/name,docs/name)
    print('Installed',binary,'and guest packages',libraries)

def check(path):
    with tempfile.TemporaryDirectory(prefix='vm2 source release ') as tmp:
        base=Path(tmp);root=unpack(path,base)
        env=dict(os.environ)
        for n in ('MAKEFLAGS','MFLAGS','MAKELEVEL','VM1','VM1_ROOT','COPYCODE_ROOT','SPACE_EMULATOR','CHECKED_VM1'):env.pop(n,None)
        env.update(VM1_ROOT=str(root/'vendor/vm1'),COPYCODE_ROOT=str(root/'vendor/copycode'),VM1=str(root/'vendor/vm1/build/bitcopy/vm1'))
        def make(*args):subprocess.run(['make',*args],cwd=root,env=env,check=True)
        make('check');make('check-core')
        stage=base/'staged';make('install','DESTDIR='+str(stage),'prefix=/usr')
        import sys
        sys.path.insert(0,str(root/'vendor/copycode/src'))
        from copycode.vm2.driver_gen import build_write
        packet,_=build_write(65520,8,b'A')
        result=subprocess.run([str(stage/'usr/bin/vm2'),'-p8','-t2'],input=packet,capture_output=True,env=dict(env,VM2_CACHE=str(base/'installed-cache')),timeout=20)
        if result.returncode or result.stdout!=b'A' or result.stderr:raise ValueError('installed vm2 failed: '+repr(result))
        native=stage/'usr/bin/vm2c';artifact=base/'installed-direct'
        installed_env=dict(env);installed_env.pop('VM1_ROOT',None);installed_env.pop('COPYCODE_ROOT',None)
        subprocess.run([str(native),'compile',str(root/'examples/direct/hello.json'),'-o',str(artifact)],cwd=base,env=installed_env,check=True)
        result=subprocess.run([str(native),'run',str(artifact)],input=b'',cwd=base,capture_output=True,env=installed_env,timeout=20)
        if result.returncode or result.stdout!=b'copymachine\n' or result.stderr:raise ValueError('installed vm2c failed: '+repr(result))
        # Installed SYS adapter must find the native protocol, independently of checkout.
        subprocess.run([sys.executable,'-c',
            'import sys;sys.path.insert(0,sys.argv[1]);from vm2compile import Program;from vm2compile.sdk import sys_record;sys_record(Program(),\"q\",op=\"FSTAT\")',
            str(stage/'usr/libexec/vm2')],cwd=base,env=installed_env,check=True)
        repacked=create(root,base/'repacked.tar.gz')
        if repacked.read_bytes()!=path.read_bytes():raise ValueError('source archive is not reproducible')
        make('clean')
        if (root/'build').exists() or not (root/'vm2').is_file():raise ValueError('clean failed to preserve sources/remove build')
        print('VM2 SOURCE RELEASE CHECK PASSED: standalone dependencies, real guest suite, staged install, deterministic repack and clean')

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    c=sub.add_parser('create');c.add_argument('--output',type=Path,required=True)
    c=sub.add_parser('check');c.add_argument('--archive',type=Path,required=True)
    c=sub.add_parser('install');c.add_argument('--destdir',default='');c.add_argument('--bindir',required=True);c.add_argument('--libdir',required=True);c.add_argument('--docdir',required=True)
    a=p.parse_args()
    try:
        if a.action=='create':print('Source archive:',create(ROOT,a.output))
        elif a.action=='check':check(a.archive.resolve())
        else:install(ROOT,a.destdir,a.bindir,a.libdir,a.docdir)
    except (ValueError,OSError,MemoryError,subprocess.CalledProcessError,tarfile.TarError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
