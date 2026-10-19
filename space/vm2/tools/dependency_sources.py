#!/usr/bin/env python3
"""Unpack explicitly pinned dependency source archives for a clean CI checkout."""
import argparse,hashlib,io,tarfile
from pathlib import Path,PurePosixPath

def install(path,digest,target):
    data=Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('dependency archive SHA256 mismatch')
    if target.exists():raise ValueError('dependency target already exists')
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
        members=archive.getmembers();names=set();payload={};prefix=None
        for item in members:
            p=PurePosixPath(item.name)
            if not item.isfile() or p.is_absolute() or '..' in p.parts or len(p.parts)<2 or str(p)!=item.name or item.name in names:raise ValueError('unsafe dependency source archive')
            if prefix is None:prefix=p.parts[0]
            if p.parts[0]!=prefix:raise ValueError('multiple dependency roots')
            names.add(item.name);payload['/'.join(p.parts[1:])]=(archive.extractfile(item).read(),item.mode&0o777)
        for line in payload['SHA256SUMS'][0].decode().splitlines():
            expected,name=line.split('  ',1)
            if hashlib.sha256(payload[name][0]).hexdigest()!=expected:raise ValueError('dependency member checksum mismatch')
        for name,(content,mode) in payload.items():
            p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content);p.chmod(mode)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path);parser.add_argument('sha256');parser.add_argument('target',type=Path)
    a=parser.parse_args();install(a.archive,a.sha256,a.target)
