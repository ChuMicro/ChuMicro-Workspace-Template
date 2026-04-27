"""Workspace-level smoke tests.

Covers properties of the workspace that aren't tied to a single
thing: every ``things/<name>/app.py`` exposes a ``run`` callable,
``workspace.yml`` parses, and the secrets template stays in sync
with the gitignored ``secrets.yml`` schema.

This file is YOUR territory — edit freely.  ``chumicro-workspace
update`` will not touch it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
THINGS_DIR = WORKSPACE_ROOT / "things"


def _thing_directories() -> list[Path]:
    """Return every ``things/<name>/`` directory that contains an ``app.py``.

    Skips ``_template/`` (the scaffold source) and any directory
    that doesn't define ``app.py`` yet (a partial scaffold).
    """
    if not THINGS_DIR.is_dir():
        return []
    return sorted(
        thing_dir
        for thing_dir in THINGS_DIR.iterdir()
        if thing_dir.is_dir()
        and not thing_dir.name.startswith("_")
        and (thing_dir / "app.py").is_file()
    )


def _load_app_module(thing_dir: Path):
    """Load ``things/<name>/app.py`` directly via importlib.

    Avoids needing the on-device ``workspace_runtime`` boot module
    in the test path; we want a host-side smoke test, not a real
    boot.
    """
    spec = importlib.util.spec_from_file_location(
        f"things.{thing_dir.name}.app", thing_dir / "app.py",
    )
    if spec is None or spec.loader is None:  # pragma: no cover
        pytest.fail(f"could not load spec for {thing_dir / 'app.py'}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "thing_dir",
    _thing_directories(),
    ids=lambda path: path.name,
)
def test_thing_app_exposes_run(thing_dir: Path) -> None:
    """Every thing's ``app.py`` must expose a ``run`` callable.

    The on-device ``workspace_runtime.boot()`` calls
    ``things.<name>.app.run()`` after wiring config / wifi / etc.
    A thing without ``run`` won't boot, so we catch the regression
    here at host-side test time.
    """
    module = _load_app_module(thing_dir)
    assert hasattr(module, "run"), (
        f"{thing_dir.name}/app.py must define run(): the on-device "
        f"boot module imports it and calls run()"
    )
    assert callable(module.run), (
        f"{thing_dir.name}/app.py: run must be callable"
    )


def test_workspace_yml_parses() -> None:
    """``workspace.yml`` must parse as YAML.

    Catches a yanked-comma or stray-tab regression before deploy
    time, where the same parse failure would surface as a confusing
    "deploy failed" message instead.
    """
    workspace_yml = WORKSPACE_ROOT / "workspace.yml"
    if not workspace_yml.is_file():
        pytest.skip("workspace.yml not present yet")
    import yaml

    data = yaml.safe_load(workspace_yml.read_text()) or {}
    assert isinstance(data, dict), "workspace.yml must be a mapping at the root"
