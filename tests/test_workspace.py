"""Workspace-level smoke tests.

Covers properties of the workspace that aren't tied to a single
project: every ``projects/<name>/app.py`` exposes a ``run`` callable;
``workspace.yml`` (machinery) and ``secrets.toml`` (device config)
parse cleanly.

This file is YOUR territory — edit freely.  ``chumicro-workspace
update`` will not touch it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = WORKSPACE_ROOT / "projects"


def _project_directories() -> list[Path]:
    """Return every ``projects/<name>/`` directory that contains an ``app.py``.

    Skips ``_template/`` (the scaffold source) and any directory
    that doesn't define ``app.py`` yet (a partial scaffold).
    """
    if not PROJECTS_DIR.is_dir():
        return []
    return sorted(
        project_dir
        for project_dir in PROJECTS_DIR.iterdir()
        if project_dir.is_dir()
        and not project_dir.name.startswith("_")
        and (project_dir / "app.py").is_file()
    )


def _load_app_module(project_dir: Path):
    """Load ``projects/<name>/app.py`` directly via importlib.

    Avoids needing the on-device ``workspace_runtime`` boot module
    in the test path; we want a host-side smoke test, not a real
    boot.
    """
    spec = importlib.util.spec_from_file_location(
        f"projects.{project_dir.name}.app", project_dir / "app.py",
    )
    if spec is None or spec.loader is None:  # pragma: no cover
        pytest.fail(f"could not load spec for {project_dir / 'app.py'}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "project_dir",
    _project_directories(),
    ids=lambda path: path.name,
)
def test_project_app_exposes_run(project_dir: Path) -> None:
    """Every project's ``app.py`` must expose a ``run`` callable.

    The on-device ``workspace_runtime.boot()`` calls
    ``projects.<name>.app.run()`` after wiring config / wifi / etc.
    A project without ``run`` won't boot, so we catch the regression
    here at host-side test time.
    """
    module = _load_app_module(project_dir)
    assert hasattr(module, "run"), (
        f"{project_dir.name}/app.py must define run(): the on-device "
        f"boot module imports it and calls run()"
    )
    assert callable(module.run), (
        f"{project_dir.name}/app.py: run must be callable"
    )


def test_shared_dir_on_import_path() -> None:
    """The root ``conftest.py`` puts ``shared/`` on ``sys.path``.

    A project imports a ``shared/foo.py`` helper by its bare module name
    (``from foo import bar``); the host test run resolves that only
    because ``shared/`` sits on the import path, matching the device,
    where deploy stages ``shared/`` modules into ``/lib``.  Assert the
    directory is on ``sys.path`` so a regression surfaces here rather
    than as a confusing ImportError while loading a project's ``app.py``.
    """
    shared_dir = WORKSPACE_ROOT / "shared"
    assert str(shared_dir) in sys.path


def test_workspace_yml_parses() -> None:
    """``workspace.yml`` must parse as YAML.

    Catches a yanked-comma or stray-tab regression before deploy
    time, where the same parse failure would surface as a confusing
    "deploy failed" message instead.
    """
    workspace_yml = WORKSPACE_ROOT / "workspace.yml"
    if not workspace_yml.is_file():
        pytest.skip("workspace.yml not present yet")
    # ruamel.yaml is the workspace's shipped YAML dependency (the
    # tooling round-trips workspace.yml with it); PyYAML is not
    # installed, so parse with the library we actually have.
    from ruamel.yaml import YAML

    data = YAML(typ="safe").load(workspace_yml.read_text()) or {}
    assert isinstance(data, dict), "workspace.yml must be a mapping at the root"


def test_secrets_toml_parses() -> None:
    """``secrets.toml`` must parse as TOML.

    Same shape as ``test_workspace_yml_parses`` — surface a malformed
    secrets file at host-side test time rather than as a cryptic
    deploy-time error.
    """
    secrets_toml = WORKSPACE_ROOT / "secrets.toml"
    if not secrets_toml.is_file():
        pytest.skip("secrets.toml not present yet")
    import tomllib

    data = tomllib.loads(secrets_toml.read_text())
    assert isinstance(data, dict), "secrets.toml must be a table at the root"
