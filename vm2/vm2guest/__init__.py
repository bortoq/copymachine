"""vm2 implemented by four-index copycode, running on vm1 (MIT)."""
# The dependency can be an installed Python package, a declared checkout, or
# the explicit vendored dependency in a standalone source release.
import os,sys
from pathlib import Path
try:
    import copycode.vm1.machine
except ModuleNotFoundError as error:
    if error.name not in ('copycode','copycode.vm1','copycode.vm1.machine'):raise
    root=Path(__file__).resolve().parents[1]
    default=root/'vendor/copycode' if (root/'vendor/copycode').is_dir() else root.parent/'copycode'
    sys.path.insert(0,str(Path(os.environ.get('COPYCODE_ROOT',default))/'src'))
    if 'copycode' in sys.modules and getattr(sys.modules['copycode'],'__file__',None) is None:
        del sys.modules['copycode']
    import copycode.vm1.machine
