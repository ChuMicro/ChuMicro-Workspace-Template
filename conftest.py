"""Pytest bootstrap for the workspace.

Mirrors the deploy tooling's import search path on the host so a
project's imports resolve under ``python3 run.py test`` the same way
they do on the device:

* ``shared/``: a file ``shared/foo.py`` is imported as ``from foo
  import bar`` (no ``shared`` package prefix); on the device, deploy
  stages ``shared/`` modules into ``/lib`` and the runtime finds them
  by that bare name.
* ``libraries/<name>/src/``: chumicro libraries acquired with
  ``python3 run.py library add`` (and any library you scaffold with
  ``new --library``) live here as source; the deploy ships them to
  ``/lib`` from these trees.
* ``packages/``: third-party source trees you dropped in by hand.

Directories that don't exist are skipped, so a fresh workspace pays
nothing.  (In chumicro-dev mode the libraries are pip-installed
editable instead, and resolve without any of this.)

This file is YOUR territory; ``chumicro-workspace update`` leaves it
alone.
"""

import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parent


def _prepend_path(directory: Path) -> None:
    if directory.is_dir():
        path_str = str(directory)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_prepend_path(_WORKSPACE_ROOT / "packages")
_libraries_dir = _WORKSPACE_ROOT / "libraries"
if _libraries_dir.is_dir():
    for _library_dir in sorted(_libraries_dir.iterdir(), reverse=True):
        _prepend_path(_library_dir / "src")
_prepend_path(_WORKSPACE_ROOT / "shared")
