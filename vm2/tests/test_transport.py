#!/usr/bin/env python3
# COPYCODE_TEST_COMPAT: independent test source is owned by copycode.
import os
from pathlib import Path
import runpy
_root=Path(os.environ.get('COPYCODE_ROOT',Path(__file__).resolve().parents[2]/'copycode'))
runpy.run_path(str(_root/'tests/vm2/test_transport.py'),run_name='__main__')
