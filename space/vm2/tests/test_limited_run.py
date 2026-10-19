"""Benchmark limits apply to descendants and timeout cleans the whole group."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
runner = [sys.executable, '-B', str(ROOT/'tools/limited_run.py')]
probe = '''import os,resource
assert len(os.sched_getaffinity(0)) == 1
assert os.nice(0) >= 15
assert resource.getrlimit(resource.RLIMIT_AS)[0] <= 96*1024*1024
try:
    bytearray(200*1024*1024)
except MemoryError:
    pass
else:
    raise AssertionError('memory limit missing')
'''
subprocess.run(runner+['--memory-mib', '96', sys.executable, '-c', probe], check=True, timeout=10)
file_probe = """import errno,resource,tempfile
assert resource.getrlimit(resource.RLIMIT_FSIZE)[0] == 1024*1024
with tempfile.TemporaryFile() as stream:
    try:
        stream.truncate(2*1024*1024)
    except OSError as error:
        assert error.errno == errno.EFBIG, error
    else:
        raise AssertionError('file size limit missing')
"""
subprocess.run(runner+['--file-mib','1',sys.executable,'-c',file_probe],check=True,timeout=10)
with tempfile.TemporaryDirectory() as tmp:
    marker = Path(tmp)/'pid'
    script = '''import subprocess,sys,time
from pathlib import Path
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
Path(sys.argv[1]).write_text(str(p.pid))
time.sleep(30)
'''
    result = subprocess.run(runner+['--seconds', '1', sys.executable, '-c', script, str(marker)],
                            capture_output=True, timeout=10)
    assert result.returncode == 124, result
    pid = int(marker.read_text())
    # A killed grandchild may briefly remain a zombie pending reaping by init.
    state = Path('/proc')/str(pid)/'stat'
    if state.exists():
        assert state.read_text().split(') ', 1)[1].split()[0] in ('Z', 'X'), state.read_text()
print('PASS benchmark resource limits and descendant cleanup')
