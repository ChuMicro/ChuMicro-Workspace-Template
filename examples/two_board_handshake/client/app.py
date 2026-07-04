"""Two-board handshake — client side.

Pairs with ``examples/two_board_handshake/server/`` running on a
*different* physical board on the same wifi network.  This side
reads a "sensor" value (a synthetic sine-wave since this example
doesn't assume a real sensor) and POSTs it to the server's
``/api/sensor`` endpoint every ``period_ms`` milliseconds.

Architecture:

* Single-process, runner-shaped: ``HttpClient.check`` /
  ``HttpClient.handle`` advance the in-flight POST one tick at a
  time, so wifi reconnects + LED blinks keep working through the
  request.
* Self-heal on drop: ``HttpClient.from_config`` builds the transport
  from config; a fresh connector is opened per request, so a wifi
  drop doesn't wedge the client.  ``Deadline`` owns the next-post
  arithmetic.

Before deploying, set ``two_board.server_host`` in
``project_config.toml`` to the IP the server printed at startup.

Scaffold a copy with
``python run.py new two_board/client --from examples/two_board_handshake/client``,
then ``python run.py deploy two_board/client``.
"""

import math

from chumicro_config import load_runtime_config
from chumicro_requests import HttpClient
from chumicro_runner import Runner
from chumicro_timing import Deadline, ticks_diff, ticks_ms
from chumicro_wifi import WifiConfig, WifiService, WifiState


class _PeriodicPoster:
    """Tick-shaped poster: build a payload + POST it every ``period_ms``.

    State machine: ``idle`` (next-post ``Deadline`` approaching), ``in
    flight`` (waiting for the request handle's ``done`` flag).  Each
    tick advances whichever phase is current; never blocks.  The first
    post fires immediately, then each completed request re-arms the
    deadline.
    """

    def __init__(self, *, http_client, url, sensor_id, period_ms,
                 timeout_ms=8_000):
        self._client = http_client
        self._url = url
        self._sensor_id = sensor_id
        self._period_ms = period_ms
        self._timeout_ms = timeout_ms
        self._deadline = None
        self._request = None
        self._sequence = 0
        self._start_ms = ticks_ms()

    def check(self, now_ms):
        if self._request is not None:
            return self._request.done
        return self._deadline is None or self._deadline.expired(now_ms)

    def handle(self, now_ms):
        if self._request is None:
            elapsed_seconds = ticks_diff(now_ms, self._start_ms) / 1000.0
            payload = {
                "sensor_id": self._sensor_id,
                "value": _synthetic_reading(elapsed_seconds),
                "uptime_s": round(elapsed_seconds, 1),
                "sequence": self._sequence,
            }
            print(f"client: -> POST {self._url} #{self._sequence}")
            self._request = self._client.post(
                self._url, json=payload, timeout_ms=self._timeout_ms,
            )
            return
        if self._request.error is not None:
            print(f"  -> error: {self._request.error!r}")
        else:
            response = self._request.result
            print(f"  -> status={response.status_code}")
        self._sequence += 1
        self._request = None
        self._deadline = Deadline(self._period_ms, now_ms)


def _synthetic_reading(elapsed_seconds: float) -> float:
    """Synthetic sine-wave reading; replace with your real sensor."""
    return round(20.0 + 5.0 * math.sin(elapsed_seconds / 30.0), 2)


def run() -> None:
    config = load_runtime_config()

    server_host = config.require("two_board.server_host")
    server_port = config.get("two_board.server_port", 8080)
    sensor_id = config.get("two_board.sensor_id", "demo-temp")
    period_ms = config.get("two_board.period_ms", 5_000)
    url = f"http://{server_host}:{server_port}/api/sensor"

    wifi = WifiService(WifiConfig.from_config(config))
    runner = Runner()
    runner.add(wifi)

    print("client: connecting to wifi ...")
    runner.run_until(lambda: wifi.connected or wifi.state == WifiState.FAILED)
    if wifi.state == WifiState.FAILED:
        raise SystemExit(f"wifi failed: {wifi.last_error}")
    print(f"client: wifi at {wifi.ip}")
    print(f"client: posting to {url} every {period_ms} ms")

    http_client = HttpClient.from_config(config, radio=wifi.adapter.radio)
    runner.add(http_client)
    runner.add(_PeriodicPoster(
        http_client=http_client,
        url=url,
        sensor_id=sensor_id,
        period_ms=period_ms,
    ))

    runner.run_until()  # never completes — parks the CPU between posts
