"""Self-bootstrapping entry point for a ChuMicro workspace.

Tool-owned: ``chumicro-workspace update`` will rewrite this file.
Don't edit; if you need a custom command, extend ``chumicro-workspace``
upstream and re-run ``update`` to pull it in.

Bootstrap flow on a freshly cloned workspace:

* No ``.venv/`` yet  -> ``python3 run.py setup`` creates the venv,
  installs ``chumicro-workspace`` (and the workspace's pyproject
  deps), then re-execs into the venv to run the requested command.
* ``.venv/`` exists  -> every ``python3 run.py <cmd>`` re-execs into
  the venv and dispatches through ``chumicro_workspace.cli``.

Requires Python 3.11+ (system or pyenv) for the initial bootstrap.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
VENV_DIR = WORKSPACE_ROOT / ".venv"
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
