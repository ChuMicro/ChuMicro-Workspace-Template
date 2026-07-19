"""Host-side tests for example_sensor — the shape to copy.

Run with::

    python3 run.py test projects/example_sensor/tests

Demonstrates the two things a per-project test can cover without a
board plugged in:

* the boot contract (``app.py`` defines a ``run`` callable) — cheap
  insurance the on-device boot shim will find its entrypoint;
* pure logic that happens to live in a device app.  ``read_celsius``
  falls back to a synthetic reading when the runtime has no
  ``microcontroller`` module, which is exactly the situation on the
  host — so the fallback path is testable here, no hardware needed.

Device-library wiring (wifi, mqtt, kvstore) lives inside ``run()``
and needs a board; that's what ``functional_tests/`` directories and
`deploy --tail` are for, not host-side unit tests.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_app_module():
    """Load ``app.py`` from the project's directory (sibling of this file)."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("example_sensor_app", app_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_exposes_run() -> None:
    """The on-device boot module imports ``app`` and calls ``run()``."""
    app_module = _load_app_module()
    assert callable(getattr(app_module, "run", None))


def test_read_celsius_returns_float_without_hardware() -> None:
    """``read_celsius`` degrades to a synthetic reading on the host.

    On a board, ``microcontroller.cpu.temperature`` supplies the real
    value; on the host that import fails and the function returns its
    fixed fallback.  Either way the contract is "a float you can put
    in a JSON payload" — assert that, not the exact number, so the
    test also passes in exotic environments that do expose a
    ``microcontroller`` module.
    """
    app_module = _load_app_module()
    value = app_module.read_celsius()
    assert isinstance(value, float)
