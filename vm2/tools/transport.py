#!/usr/bin/env python3
# COPYCODE_COMPAT: source ownership moved to copycode; no ISA conversion.
import os
from pathlib import Path
import sys
_root = Path(os.environ.get('COPYCODE_ROOT', Path(__file__).resolve().parents[2]/'copycode'))
sys.path.insert(0, str(_root/'src'))
from copycode.vm2 import transport as _implementation
if __name__ == '__main__':
    if hasattr(_implementation, 'main'):
        raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
