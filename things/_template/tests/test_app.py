"""Starter test for this thing — edit freely.

Scaffolded by ``python run.py new <thing>``.  Lives alongside
``app.py`` so test code can import the thing's helpers directly.

Run with::

    python run.py test things/<thing-name>/tests

The workspace-level ``tests/`` directory at the repo root is for
cross-thing smoke tests; per-thing tests like this one cover the
thing's own internals.

The starter test below is intentionally trivial — replace it with
real assertions about your thing's behaviour as you build it out.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_app_module():
    """Load ``app.py`` from the thing's directory (sibling of this file)."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app", app_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_exposes_run() -> None:
    """The thing's ``app.py`` must define a ``run`` callable.

    The on-device ``workspace_runtime.boot()`` imports
    ``things.<name>.app`` and calls ``run()``.  A thing without
    ``run`` won't boot.
    """
    app_module = _load_app_module()
    assert hasattr(app_module, "run")
    assert callable(app_module.run)
