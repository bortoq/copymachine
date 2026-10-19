"""Refresh only the owned build/direct-example artifact, atomically per file."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vm2compile import Program
from vm2compile.artifact import build,json_bytes
p=Program.load(json.loads((ROOT/'examples/direct/hello.json').read_text()))
payload,manifest=build(p);target=ROOT/'build/direct-example';target.mkdir(parents=True,exist_ok=True)
for name,data in dict(payload,**{'manifest.json':json_bytes(manifest)}).items():
    path=target/name
    if path.is_file() and path.read_bytes()==data:continue
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_bytes(data);temporary.replace(path)
print('Native artifact:',target)
