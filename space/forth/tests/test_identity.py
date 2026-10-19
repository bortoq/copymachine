"""Verify upstream and dictionary identities without executing build-time i386."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/pforth'))
from build import dictionary
from common import UPSTREAM,REVISION
metadata=json.loads((UPSTREAM/'UPSTREAM.json').read_text());assert metadata['revision']==REVISION
for name,digest in metadata['files'].items():assert hashlib.sha256((UPSTREAM/name).read_bytes()).hexdigest()==digest,name
m=dictionary();assert m['cell_bytes']==4 and m['little_endian'] and m['names_bytes']==6140 and m['code_bytes']==5328
source=(UPSTREAM/'fth/system.fth').read_bytes().split(b'\\ Auto Initialization')[0]
assert hashlib.sha256(source).hexdigest()==m['system_input_sha256']
print('PASS pinned upstream, dictionary header, source input and 32-bit metadata')

import re,struct
header=(ROOT/'runtime/pforth/pfdicdat.h').read_text();chunks=[]
for name in ('MinDicNames','MinDicCode'):
 body=re.search(name+r'\[.*?= \{(.*?)\};',header,re.S)[1]
 chunks.append(bytes(int(v,16) for v in re.findall(r'0x([0-9a-f]{2})',body)))
raw=b'PFD1'+struct.pack('<4I',m['names_bytes'],m['code_bytes'],m['relative_context'],m['primitives'])+b''.join(chunks)
assert hashlib.sha256(raw).hexdigest()==m['dictionary_sha256']
print('PASS reconstructed raw dictionary SHA256')
