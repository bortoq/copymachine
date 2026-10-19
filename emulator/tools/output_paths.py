"""Output locations for the standalone emulator or its enclosing workspace."""
from pathlib import Path


def output_dir(root, kind='build'):
    root = Path(root).resolve()
    workspace = root.parent
    if (workspace/'tools/workspace.mk').is_file():
        return workspace/'build'/'emulator'/kind
    return root/kind
