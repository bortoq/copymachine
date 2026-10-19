from pathlib import Path
import hashlib,os,subprocess,tarfile,tempfile
root=Path(__file__).resolve().parents[1]
from copycode.hostpaths import output_dir

archive=output_dir(root, 'dist')/'copycode-0.1.0.tar.gz';before=archive.read_bytes()
with tempfile.TemporaryDirectory(prefix='copycode standalone ') as tmp:
    folder=Path(tmp)
    with tarfile.open(archive) as tar:
        for m in tar.getmembers():
            assert m.isfile() and m.name.startswith('copycode-0.1.0/') and '..' not in Path(m.name).parts
            target=folder/m.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(tar.extractfile(m).read())
    extracted=folder/'copycode-0.1.0'
    for line in (extracted/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1);assert hashlib.sha256((extracted/name).read_bytes()).hexdigest()==digest
    env=dict(os.environ,EMULATOR_PROTO=os.environ.get('EMULATOR_PROTO', str((root.parent.parent if root.parent.name == 'space' else root.parent)/'emulator/src/proto.def')))
    subprocess.run(['make','check', 'EMULATOR='+str(Path(os.environ.get('EMULATOR', output_dir((root.parent.parent if root.parent.name == 'space' else root.parent)/'emulator')/'bitcopy/emulator')).resolve()), 'EMULATOR_NETWORK='+str(Path(os.environ.get('EMULATOR_NETWORK', output_dir((root.parent.parent if root.parent.name == 'space' else root.parent)/'emulator')/'network/emulator')).resolve()), 'VM2='+str(Path(os.environ.get('VM2', output_dir(root.parent/'vm2')/'reference-space')).resolve())],cwd=extracted,env=env,check=True)
    saved=[(extracted/'doc'/name).read_bytes() for name in ['contracts.json','generated.json']]
    subprocess.run(['make','inventory'],cwd=extracted,check=True)
    assert saved==[(extracted/'doc'/name).read_bytes() for name in ['contracts.json','generated.json']]
    subprocess.run(['make','dist'],cwd=extracted,check=True)
    assert (output_dir(extracted, 'dist')/'copycode-0.1.0.tar.gz').read_bytes()==before
    subprocess.run(['make','clean'],cwd=extracted,check=True)
    assert not (output_dir(extracted, 'dist')).exists() and not (output_dir(extracted, 'build')).exists()
print('PASS standalone archive, complete suite, deterministic manifests/repack, clean')
