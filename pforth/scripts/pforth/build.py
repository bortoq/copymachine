"""Build the pinned pForth C port as a persisted direct RV32I artifact."""
import argparse,hashlib,json,subprocess,os
from pathlib import Path
from common import ROOT,PORT,RV32I_ROOT,REVISION,sources,flags
from rv32i_toolchain import Toolchain
from direct_target import compile_image
from vm2compile.artifact import save,load

MEMORY_BYTES=524288

def dictionary():
    header=PORT/'pfdicdat.h';metadata=json.loads(header.with_name(header.name+'.json').read_text())
    if metadata['upstream_revision']!=REVISION or hashlib.sha256(header.read_bytes()).hexdigest()!=metadata['header_sha256']:
        raise ValueError('dictionary revision/checksum mismatch')
    return metadata

def build(output,compiler=None,*,indexed=True,packing=True):
    output=Path(output).resolve()
    if output.exists():raise ValueError('output already exists: '+str(output))
    prepared=dictionary();tools=Toolchain(compiler);artifacts=output.with_name(output.name+'.build');artifacts.mkdir(parents=True,exist_ok=True)
    selected=sources();port_flags=flags();index_report=None
    if indexed:
        from index import prepare_index
        generated,index_report=prepare_index(artifacts/'index')
        selected=[generated if p.name=='pfcompil.c' else PORT/'inner.c' if p.name=='pf_inner.c' else p for p in selected]+[PORT/'index.c']
        port_flags+=['-I'+str(generated.parent)]
    runtime=RV32I_ROOT/'runtime/rv32i';elf=artifacts/'program.elf';binary=artifacts/'program.bin'
    command=tools.command('-O2')+['-I',str(runtime),'-T',str(runtime/'link.ld'),'-Wl,--defsym=CS_STACK_TOP='+str(MEMORY_BYTES-16),'-Wl,-Map='+str(artifacts/'program.map'),str(runtime/'start.S'),str(runtime/'runtime.c')]+port_flags+list(map(str,selected))+['-lgcc','-o',str(elf)]
    (artifacts/'compile.json').write_text(json.dumps(command,indent=2)+'\n')
    env=dict(os.environ);env.setdefault("SOURCE_DATE_EPOCH","0")
    (artifacts/"compile-env.json").write_text(json.dumps({"SOURCE_DATE_EPOCH":env["SOURCE_DATE_EPOCH"]},indent=2)+"\n")
    result=subprocess.run(command,capture_output=True,timeout=45,env=env);(artifacts/'compile.stderr').write_bytes(result.stderr)
    if result.returncode:raise ValueError(result.stderr.decode(errors='replace'))
    subprocess.run([tools.objcopy,'-O','binary',str(elf),str(binary)],check=True,timeout=10)
    with (artifacts/'disassembly.txt').open('wb') as out:subprocess.run([tools.objdump,'-d',str(elf)],stdout=out,check=True,timeout=10)
    payload,manifest=compile_image(binary.read_bytes(),memory_bytes=MEMORY_BYTES,packing=packing)
    manifest['pforth']=dict(schema='pforth-direct-v1',revision=REVISION,source_date_epoch=env['SOURCE_DATE_EPOCH'],dictionary=prepared,index=index_report,program_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    save(output,payload,manifest);return manifest

def job(artifact,task,output):
    artifact=Path(artifact).resolve();task=Path(task).resolve();output=Path(output).resolve()
    payload,manifest=load(artifact)
    if manifest.get('pforth',{}).get('schema')!='pforth-direct-v1':raise ValueError('pForth artifact required')
    source=task.read_bytes()
    if output.exists():raise ValueError('job already exists')
    output.mkdir(parents=True)
    save(output/'image',payload,manifest);(output/'task.fth').write_bytes(source)
    identity=hashlib.sha256((output/'image/manifest.json').read_bytes()).hexdigest()
    (output/'job.json').write_text(json.dumps(dict(schema='pforth-job-v1',task_sha256=hashlib.sha256(source).hexdigest(),manifest_sha256=identity),indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('-o',type=Path,required=True);p.add_argument('--compiler');a=p.parse_args()
    build(a.o,a.compiler)
if __name__=='__main__':main()
