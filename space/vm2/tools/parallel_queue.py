#!/usr/bin/env python3
"""Queue independent check commands and run them in parallel.

  parallel_queue.py add FILE -- command...   append a command
  parallel_queue.py run FILE -j N            run all queued commands, N at once

Each command's output is printed as one block when it finishes, followed by
its wall time; the exit status is non-zero if any command failed. The queue
file is removed after the run. Commands keep their own limits (limited_run).
"""
import argparse,json,os,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor

def main():
    if len(sys.argv)>3 and sys.argv[1]=='add' and sys.argv[3]=='--':
        with open(sys.argv[2],'a') as queue:queue.write(json.dumps(sys.argv[4:])+'\n')
        return 0
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['run']);p.add_argument('file')
    p.add_argument('-j',type=int,default=os.cpu_count());a=p.parse_args()
    if not os.path.exists(a.file):return 0
    commands=[json.loads(line) for line in open(a.file) if line.strip()];os.remove(a.file)
    def run(command):
        start=time.monotonic()
        r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        return command,r.returncode,r.stdout,time.monotonic()-start
    failed=0;start=time.monotonic()
    with ThreadPoolExecutor(max(1,a.j)) as pool:
        for command,code,output,seconds in pool.map(run,commands):
            sys.stdout.buffer.write(b'$ '+' '.join(command).encode()+b'\n'+output)
            print(f'QUEUE {"PASS" if code==0 else "FAIL"} {seconds:.1f} s exit {code}',flush=True)
            failed+=code!=0
    print(f'QUEUE {len(commands)-failed}/{len(commands)} passed in {time.monotonic()-start:.1f} s with -j {a.j}',flush=True)
    return 1 if failed else 0

if __name__=='__main__':raise SystemExit(main())
