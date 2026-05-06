"""Periodic HTTP GET — wifi up, fetch a URL on a heartbeat.

Demonstrates `chumicro-requests` driven by the `chumicro-runner`
tick scheduler.  The fetcher's `check` / `handle` shape never
block-calls the loop, so wifi reconnects keep working in the gap
between requests.

Scaffold a copy with
``python run.py new <name> --from examples/periodic_get``, then
``python run.py deploy <name>``.
"""

from chumicro_config import load_runtime_config
from chumicro_requests import HttpClient, chumicro_sockets_factory
from chumicro_runner import Runner
from chumicro_timing import ticks_add, ticks_diff, ticks_ms
from chumicro_wifi import WifiConfig, WifiService, WifiState


class _PeriodicFetcher:
    """Tick-shaped poller: GET the URL every ``period_ms``.

    State machine: ``idle`` (next fetch deadline approaching),
    ``in flight`` (waiting for `_request.done`).  Each tick
    advances whichever phase is current; never blocks.
    """

    def __init__(self, *, http_client, url, period_ms, timeout_ms=8_000):
        self._client = http_client
        self._url = url
        self._period_ms = period_ms
        self._timeout_ms = timeout_ms
        self._next_at = ticks_ms()
        self._request = None
        self._count = 0

    def check(self, now_ms):
        if self._request is None:
            return ticks_diff(now_ms, self._next_at) >= 0
        return self._request.done

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
        self._next_at = ticks_add(now_ms, self._period_ms)


def run():
    config = load_runtime_config()

    wifi = WifiService(WifiConfig.from_config(config))
    runner = Runner()
    runner.add(wifi)

    print("periodic_get: connecting ...")
    while not wifi.connected:
        runner.tick()
        if wifi.state == WifiState.FAILED:
            raise SystemExit(f"wifi failed: {wifi.last_error}")
    print(f"periodic_get: connected at {wifi.ip}")

    client = HttpClient(connection_factory=chumicro_sockets_factory())
    runner.add(client)
    runner.add(_PeriodicFetcher(
        http_client=client,
        url=config.require("fetch.url"),
        period_ms=config.get("fetch.period_ms", 30_000),
    ))

    try:
        while True:
            runner.tick()
    except KeyboardInterrupt:
        pass
    print("periodic_get: shutdown")
