"""Bounded GCCJOB1 transport and optional real cc1 startup/resume evidence."""
import argparse
import gc
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]/'legacy/copy-space'
EMULATOR = Path(os.environ.get("SPACE_EMULATOR", str(ROOT.parent.parent/"space/vm2/space")))
sys.path.insert(0,str(ROOT/'modules'))
sys.path.insert(0,str(ROOT/'scripts/rv32i'))
sys.path.insert(0,str(ROOT/'scripts/gcc'))
from build import build
from rv32i import Layout
from rv32i_bulk import BulkImage
from checkpoint import execute_segments, digest
from job_format import pack_job, unpack_job

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cc1-image',type=Path)
args=parser.parse_args()
root=Path('tmp/gccjob-checkpoints');root.mkdir(parents=True,exist_ok=True)
out=Path(tempfile.mkdtemp(prefix='run-',dir=root)).resolve()
job=pack_job(['cc1','-E','-P','-quiet','-nostdinc','main.c'],{'main.c':b'int value(void) { return 7; }\n'})
assert unpack_job(job)[1]['main.c'].startswith(b'int value')
inp=out/'job.bin';inp.write_bytes(job)
source=out/'job_reader.c'
source.write_text('''#include "copy_space.h"
int main(void) {
 unsigned char head[16], buf[16], result[4]; unsigned sum=0; int i,n;
 const unsigned char magic[8]={'G','C','C','J','O','B','1',0};
 if(cs_read(head,16)!=16) return 2;
 for(i=0;i<8;i++) if(head[i]!=magic[i]) return 3;
 for(i=0;i<16;i++) sum+=head[i];
 while((n=cs_read(buf,16))>0) for(i=0;i<n;i++) sum+=buf[i];
 for(i=0;i<4;i++) result[i]=(unsigned char)(sum>>(8*i));
 return cs_write(result,4)==4?0:4;
}
''')
image=out/'reader.bin'
manifest=build([source],image,memory_bytes=65536,space_bytes=8*1024*1024,
               new_emulator=True,segment_budget=200)
r=execute_segments(EMULATOR,image,manifest,inp,out/'reader',max_segments=20)
assert r['complete'] and r['terminal']['exit_code']==0 and r['terminal']['input_cursor']==len(job),r
assert (out/'reader/stdout.bin').read_bytes()==sum(job).to_bytes(4,'little')
assert len(r['segments'])>1
print('OK GCCJOB1 reader completed across',len(r['segments']),'segments;',r['terminal'],flush=True)
evidence=dict(reader=r,job_sha256=digest(inp),scope='Complete GCCJOB1 receiver; this receiver does not compile C')
if args.cc1_image:
 old=json.loads((args.cc1_image/'image.json').read_text())
 program=(args.cc1_image/'gcc-space.bin').read_bytes()
 gen=BulkImage(io=True,memory_bytes=old['guest_memory_bytes'],layout=Layout(old['space_bytes']),
               segment_budget=256).build()
 raw,manifest=gen.encode(program,entry=old['entry'],registers={2:old['initial_stack']},
                         image_bytes=old['guest_memory_bit']//8+len(program))
 path=out/'cc1.bin';path.write_bytes(raw)
 del raw,program,gen;gc.collect()
 (out/'cc1.bin.json').write_text(json.dumps(manifest))
 first=execute_segments(EMULATOR,path,manifest,inp,out/'cc1-first',max_segments=1)
 assert not first['complete']
 left=execute_segments(EMULATOR,path,manifest,inp,out/'cc1-left',max_segments=1,
                       checkpoint_from=first['checkpoint'])
 right=execute_segments(EMULATOR,path,manifest,inp,out/'cc1-right',max_segments=1,
                        checkpoint_from=first['checkpoint'])
 assert left['terminal']==right['terminal'] and not left['complete']
 assert digest(Path(left['checkpoint'])/'space.bin')==digest(Path(right['checkpoint'])/'space.bin')
 evidence['cc1']=dict(original_binary_sha256=digest(args.cc1_image/'gcc-space.bin'),
   source_image=str(args.cc1_image),first=first,left=left,right=right,
   scope='Real cc1 startup on valid GCCJOB1 input, 512 committed guest instructions; not a completed compile')
 print('OK real cc1 startup: 256 + 256 committed instructions, byte-identical forked space;',
       'input cursor',left['terminal']['input_cursor'],flush=True)
(out/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('Evidence:',out/'evidence.json',flush=True)
