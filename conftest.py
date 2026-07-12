"""Pytest bootstrap for the workspace.

Puts the ``shared/`` directory on ``sys.path`` so a project's bare
shared imports resolve under ``python3 run.py test``.  A file
``shared/foo.py`` is imported as ``from foo import bar`` (no ``shared``
package prefix); on the device, deploy stages ``shared/`` modules into
``/lib`` and the runtime finds them by that bare name.  Rooting the test
path at ``shared/`` reproduces that resolution on the host, so the
workspace smoke test can load a project's ``app.py`` the same way the
board would.

This file is YOUR territory; ``chumicro-workspace update`` leaves it
alone.
"""

import sys
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent / "shared"
if _SHARED_DIR.is_dir():
    _shared_path = str(_SHARED_DIR)
    if _shared_path not in sys.path:
        sys.path.insert(0, _shared_path)
