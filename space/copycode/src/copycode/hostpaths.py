"""Host output locations; workspace outputs are separate from source trees."""
from pathlib import Path


def output_dir(root, kind='build'):
    """Return a component's owned output directory, also in standalone releases."""
    root = Path(root).resolve()
    if kind not in ('build', 'dist', 'tmp'):
        raise ValueError('unknown output kind: '+kind)
    if root.name == 'emulator':
        workspace = root.parent
    elif root.parent.name == 'space':
        workspace = root.parent.parent
    else:
        return root/kind
    if (workspace/'tools/workspace.mk').is_file() and (workspace/'emulator/src/runtime.c').is_file():
        return workspace/'build'/root.relative_to(workspace)/kind
    return root/kind
