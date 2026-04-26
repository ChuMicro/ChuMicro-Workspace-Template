"""Self-bootstrapping entry point for a ChuMicro workspace.

Tool-owned: ``chumicro-workspace update`` will rewrite this file.
Don't edit; if you need a custom command, extend ``chumicro-workspace``
upstream and re-run ``update`` to pull it in.

Bootstrap flow on a freshly cloned workspace:

* No ``.venv/`` yet  -> ``python3 run.py setup`` creates the venv,
  enters chumicro-dev mode if ``chumicro-dev.toml`` is present (see
  below), installs ``chumicro-workspace`` (and the workspace's
  pyproject deps), then re-execs into the venv to run the requested
  command.
* ``.venv/`` exists  -> every ``python3 run.py <cmd>`` re-execs into
  the venv and dispatches through ``chumicro_workspace.cli``.

ChuMicro-dev mode: drop a ``chumicro-dev.toml`` next to this file with::

    chumicro_path = "../chumicro"

When present, ``setup`` walks ``<chumicro_path>/libraries/*`` and
``<chumicro_path>/workbench/*`` and pip-installs every package found
there as editable BEFORE the workspace's own install.  Lets you
co-develop chumicro libraries / chumicro-workspace from a sibling
clone of the mono-repo without publishing to PyPI.  Delete the
file (or unset ``chumicro_path``) to revert to the PyPI path.
``chumicro-dev.toml`` is gitignored by default.

Requires Python 3.11+ (system or pyenv) for the initial bootstrap.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
VENV_DIR = WORKSPACE_ROOT / ".venv"
CHUMICRO_DEV_FILE = WORKSPACE_ROOT / "chumicro-dev.toml"
MIN_PYTHON = (3, 11)


def _venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _running_in_venv() -> bool:
    try:
        return Path(sys.prefix).resolve() == VENV_DIR.resolve()
    except OSError:
        return False


def _check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        major, minor = MIN_PYTHON
        raise SystemExit(
            f"error: Python {major}.{minor}+ required; "
            f"got {sys.version.split()[0]}",
        )


def _read_chumicro_dev_path() -> Path | None:
    """Return the resolved chumicro-mono-repo path if dev mode is active.

    Reads ``chumicro-dev.toml`` (TOML, ``chumicro_path = "..."``).
    Relative paths resolve against the workspace root.  Returns
    ``None`` when the file is missing or the path key is unset.
    """
    if not CHUMICRO_DEV_FILE.is_file():
        return None
    data = tomllib.loads(CHUMICRO_DEV_FILE.read_text())
    raw_path = data.get("chumicro_path")
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (WORKSPACE_ROOT / candidate).resolve()
    return candidate


def _discover_chumicro_packages(mono_repo_path: Path) -> list[Path]:
    """Return every package dir under *mono_repo_path*'s ``libraries/``
    and ``workbench/`` trees that has a ``pyproject.toml``.

    Order is alphabetical within each tree, libraries before workbench
    (deploy + workspace need the libraries' build deps to resolve).
    """
    packages: list[Path] = []
    for parent_name in ("libraries", "workbench"):
        parent = mono_repo_path / parent_name
        if not parent.is_dir():
            continue
        for entry in sorted(parent.iterdir()):
            if entry.is_dir() and (entry / "pyproject.toml").is_file():
                packages.append(entry)
    return packages


def _create_venv_and_install() -> None:
    print(f"creating .venv at {VENV_DIR}", flush=True)
    subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        check=True,
    )
    venv_python = _venv_python()
    print("upgrading pip", flush=True)
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--quiet",
            "pip",
        ],
        check=True,
    )
    chumicro_path = _read_chumicro_dev_path()
    if chumicro_path is not None:
        if not chumicro_path.is_dir():
            raise SystemExit(
                f"error: chumicro-dev.toml points at {chumicro_path} "
                "but that path does not exist or is not a directory.",
            )
        packages = _discover_chumicro_packages(chumicro_path)
        if not packages:
            raise SystemExit(
                f"error: no chumicro packages found under {chumicro_path} — "
                "expected libraries/<name>/pyproject.toml or "
                "workbench/<name>/pyproject.toml.  Is this a chumicro mono-repo?",
            )
        print(
            f"chumicro-dev mode: installing {len(packages)} package(s) from "
            f"{chumicro_path}",
            flush=True,
        )
        for package_path in packages:
            print(f"  editable: {package_path.relative_to(chumicro_path)}", flush=True)
            subprocess.run(
                [
                    str(venv_python),
                    "-m",
                    "pip",
                    "install",
                    "--quiet",
                    "--no-deps",
                    "-e",
                    str(package_path),
                ],
                check=True,
            )
    print("installing workspace (editable) + dependencies", flush=True)
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "-e",
            str(WORKSPACE_ROOT),
        ],
        check=True,
    )


def _reexec_in_venv() -> None:
    venv_python = _venv_python()
    if not venv_python.exists():
        raise SystemExit(
            f"error: venv at {VENV_DIR} is broken "
            f"(no python at {venv_python}); "
            f"delete .venv/ and rerun `python3 run.py setup`.",
        )
    os.execv(
        str(venv_python),
        [str(venv_python), __file__, *sys.argv[1:]],
    )


def main() -> int:
    _check_python_version()
    args = sys.argv[1:]
    if not VENV_DIR.exists():
        if args[:1] != ["setup"]:
            raise SystemExit(
                "error: workspace not set up yet. "
                "Run `python3 run.py setup` first.",
            )
        _create_venv_and_install()
        _reexec_in_venv()
    if not _running_in_venv():
        _reexec_in_venv()
    from chumicro_workspace.cli import main as workspace_main

    return workspace_main(args)


if __name__ == "__main__":
    sys.exit(main())
