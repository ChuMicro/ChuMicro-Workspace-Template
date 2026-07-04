"""Periodic HTTP GET — wifi up, fetch a URL on a heartbeat.

Demonstrates `chumicro-requests` driven by the `chumicro-runner`
tick scheduler.  The fetcher's `check` / `handle` shape never
block-calls the loop, so wifi reconnects keep working in the gap
between requests.  ``Deadline`` owns the next-fetch arithmetic — no
raw ticks math to get the 32-bit wrap wrong.

Scaffold a copy with
``python run.py new <name> --from examples/periodic_get``, then
``python run.py deploy <name>``.
"""

from chumicro_config import load_runtime_config
from chumicro_requests import HttpClient
from chumicro_runner import Runner
from chumicro_timing import Deadline
from chumicro_wifi import WifiConfig, WifiService, WifiState


class _PeriodicFetcher:
    """Tick-shaped poller: GET the URL every ``period_ms``.

    State machine: ``idle`` (next-fetch ``Deadline`` approaching),
    ``in flight`` (waiting for `_request.done`).  Each tick advances
    whichever phase is current; never blocks.  The first fetch fires
    immediately, then each completed request re-arms the deadline.
    """

    def __init__(self, *, http_client, url, period_ms, timeout_ms=8_000):
        self._client = http_client
        self._url = url
        self._period_ms = period_ms
        self._timeout_ms = timeout_ms
        self._deadline = None
        self._request = None
        self._count = 0

    def check(self, now_ms):
        if self._request is not None:
            return self._request.done
        return self._deadline is None or self._deadline.expired(now_ms)

    def handle(self, now_ms):
        if self._request is None:
            print(f"periodic_get: GET {self._url}")
            self._request = self._client.get(
                self._url, timeout_ms=self._timeout_ms,
            )
            return
        if self._request.error is not None:
            print(f"  -> error: {self._request.error!r}")
        else:
            response = self._request.result
            print(
                f"  -> status={response.status_code} "
                f"bytes={len(response.body)}",
            )
        self._count += 1
        self._request = None
        self._deadline = Deadline(self._period_ms, now_ms)


def run():
    config = load_runtime_config()

    wifi = WifiService(WifiConfig.from_config(config))

    def report_fault(entry, error):
        print("SERVICE_FAULT", entry.service, repr(error))

    runner = Runner(on_handler_error=report_fault)
    runner.add(wifi)

    print("periodic_get: connecting ...")
    runner.run_until(lambda: wifi.connected or wifi.state == WifiState.FAILED)
    if wifi.state == WifiState.FAILED:
        raise SystemExit(f"wifi failed: {wifi.last_error}")
    print(f"periodic_get: connected at {wifi.ip}")

    client = HttpClient.from_config(config, radio=wifi.adapter.radio)
    runner.add(client)
    runner.add(_PeriodicFetcher(
        http_client=client,
        url=config.require("fetch.url"),
        period_ms=config.get("fetch.period_ms", 30_000),
    ))

    runner.run_until()  # never completes — parks the CPU between fetches
