"""Reproducible standalone source archive. Dependencies remain explicit."""
from pathlib import Path
import gzip,hashlib,io,tarfile
ROOT=Path(__file__).resolve().parents[1]
names=(ROOT/'dist.manifest').read_text().splitlines()
if names!=sorted(set(names)):raise ValueError('manifest order/duplicates')
files={}
for name in names:
    p=ROOT/name
    if (p.is_symlink()) or not p.is_file() or '..' in Path(name).parts or Path(name).is_absolute():raise ValueError(name)
    if any(parent.is_symlink() for parent in p.parents if parent!=ROOT.parent):raise ValueError('symlink source ancestor')
    files[name]=p.read_bytes()
files['SHA256SUMS']=''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name,data in sorted(files.items())).encode()
import sys
sys.path.insert(0, str(ROOT/"src"))
from copycode.hostpaths import output_dir

out=output_dir(ROOT, 'dist')/'copycode-0.1.0.tar.gz';out.parent.mkdir(parents=True,exist_ok=True)
with out.open('wb') as stream:
    with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0) as gz:
        with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT) as tar:
            for name,data in sorted(files.items()):
                info=tarfile.TarInfo('copycode-0.1.0/'+name);info.size=len(data);info.mode=0o644;info.mtime=0
                tar.addfile(info,io.BytesIO(data))
print(out,hashlib.sha256(out.read_bytes()).hexdigest())
