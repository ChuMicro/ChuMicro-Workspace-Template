"""Starter test for this project.  Edit freely.

Scaffolded by ``python3 run.py new <project>``.  Lives alongside
``app.py`` so test code can import the project's helpers directly.

Run with::

    python3 run.py test projects/<project-name>/tests

The workspace-level ``tests/`` directory at the repo root is for
cross-project smoke tests; per-project tests like this one cover the
project's own internals.

The starter test below is intentionally trivial.  Replace it with
real assertions about your project's behaviour as you build it out.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_app_module():
    """Load ``app.py`` from the project's directory (sibling of this file)."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app", app_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_exposes_run() -> None:
    """The project's ``app.py`` must define a ``run`` callable.

    The on-device ``workspace_runtime.boot()`` imports
    ``projects.<name>.app`` and calls ``run()``.  A project without
    ``run`` won't boot.
    """
    app_module = _load_app_module()
    assert hasattr(app_module, "run")
    assert callable(app_module.run)
