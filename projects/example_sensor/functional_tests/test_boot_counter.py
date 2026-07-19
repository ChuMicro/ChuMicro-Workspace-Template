"""On-device acceptance for example_sensor's persistence contract.

What it covers: the boot-counter pattern in ``app.py`` assumes a
value written through ``KVStore`` survives into a *fresh* store
instance — the same code path a reboot takes.  That's a hardware
property (NVM / flash substrate behavior), so it belongs on a real
board rather than mocked on the host.

Today, ``chumicro-pytest-device`` routes ``functional_tests/``
directories under ``libraries/<name>/`` to a board; routing for
project trees like this one hasn't landed yet, so on a host
interpreter this module skips itself rather than exercising the
host's stand-in backend and calling it hardware coverage.  Once
project routing lands, these tests run on the board unchanged.

The test uses its own key and removes it afterwards, so the real
``boot_count`` of a deployed example_sensor is left alone.
"""

import sys

import pytest
from chumicro_kvstore import KVStore

if sys.implementation.name == "cpython":
    pytest.skip(
        "board-facing acceptance: runs on-device once chumicro-pytest-device "
        "routes project functional_tests trees (it routes library trees "
        "today); on the host these assertions would only exercise the "
        "stand-in backend",
        allow_module_level=True,
    )

_TEST_KEY = "functional_test_probe"


def test_value_survives_a_fresh_store_instance() -> None:
    """Write + commit, then read the value back through a new KVStore.

    A fresh instance re-reads the persisted substrate, which is how
    ``run()`` sees the previous boot's counter after a reset.
    """
    store = KVStore()
    previous = store.get(_TEST_KEY, 0)
    store[_TEST_KEY] = previous + 1
    store.commit()

    reread = KVStore()
    try:
        assert reread.get(_TEST_KEY) == previous + 1
    finally:
        reread.pop(_TEST_KEY, None)
        reread.commit()


def test_boot_counter_starts_at_default_when_absent() -> None:
    """A missing key falls back to the ``get`` default.

    First-boot behavior: ``run()`` reads ``boot_count`` with a
    default of 0 before writing 1 back.
    """
    store = KVStore()
    assert store.get(_TEST_KEY, 0) == 0
