"""Boot (14.1): L0 made by the host pForth equals K0 made by the model, byte for byte
(before any change of the definition), and the boot is repeatable."""
import hashlib, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import boot, k0_path, paths

stream, seconds = boot.boot()
assert stream == paths.L0.read_bytes(), 'the second boot differs from build L0.boot (run make boot)'
print(f'PASS boot is repeatable: {len(stream)} bytes ({seconds:.1f} s)')
reference = k0_path.k0().read_bytes()
assert stream == reference, ('L0 differs from K0', len(stream), len(reference))
print('PASS L0 equals K0 of the model:', hashlib.sha256(stream).hexdigest()[:16])
