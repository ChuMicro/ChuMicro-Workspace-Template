"""two_things/sensor — periodically POST a synthetic reading.

Pair with [`two_things/server/`](../server/) on a second board.
The server's IP + port go into this thing's ``[target]`` config;
deploy the server first, note the URL it prints, then update
the sensor's ``config.toml`` before deploying.

Scaffold a copy with
``python run.py new <name> --from examples/two_things/sensor``,
then ``python run.py deploy <name>``.
"""

from chumicro_config import load_runtime_config
from chumicro_requests import HttpClient, chumicro_sockets_factory
from chumicro_runner import Runner
from chumicro_timing import ticks_add, ticks_diff, ticks_ms
from chumicro_wifi import WifiConfig, WifiService, WifiState


class _PeriodicSensorPoster:
    """Tick-shaped POSTer.

    Every ``period_ms``, builds a JSON sensor-reading payload and
    POSTs it.  Holds at most one in-flight request — the deadline
    advances after each completion (success or error) so a slow /
    failing server doesn't run the loop ahead of itself.
    """

    def __init__(self, *, http_client, url, sensor_id, period_ms):
        self._client = http_client
        self._url = url
        self._sensor_id = sensor_id
        self._period_ms = period_ms
        self._next_at = ticks_ms()
        self._request = None
        self._sequence = 0

    def check(self, now_ms):
        if self._request is None:
            return ticks_diff(now_ms, self._next_at) >= 0
        return self._request.done

    def handle(self, now_ms):
        if self._request is None:
            payload = {
                "sensor_id": self._sensor_id,
                "value": _synthetic_reading(self._sequence),
            }
            print(f"sensor: -> {self._url} #{self._sequence}")
            self._request = self._client.post(self._url, json=payload)
            return
        if self._request.error is not None:
            print(f"  -> error: {self._request.error!r}")
        else:
            response = self._request.result
            print(f"  -> status={response.status_code}")
        self._sequence += 1
        self._request = None
        self._next_at = ticks_add(now_ms, self._period_ms)


def _synthetic_reading(sequence: int) -> float:
    """Slow triangle wave so a board with no real sensor still publishes data."""
    return 20.0 + (sequence % 10) * 0.5


def _radio_for_runtime():
    try:
        import wifi
        return wifi.radio
    except ImportError:
        return None


def run() -> None:
    config = load_runtime_config()
    wifi_section = config["wifi"]
    target_section = config["target"]

    wifi = WifiService(WifiConfig.from_dict(wifi_section))
    runner = Runner()
    runner.add(wifi)

    print("sensor: connecting to wifi ...")
    while not wifi.connected:
        runner.tick()
        if wifi.state == WifiState.FAILED:
            raise SystemExit(f"wifi failed: {wifi.last_error}")
    print(f"sensor: wifi at {wifi.ip}")

    radio = _radio_for_runtime()
    client = HttpClient(
        connection_factory=chumicro_sockets_factory(radio=radio),
    )
    runner.add(client)
    runner.add(_PeriodicSensorPoster(
        http_client=client,
        url=target_section["url"],
        sensor_id=target_section.get("sensor_id", "sensor-1"),
        period_ms=target_section.get("period_ms", 5000),
    ))

    print(f"sensor: posting to {target_section['url']}")
    try:
        while True:
            runner.tick()
    except KeyboardInterrupt:
        pass
    print("sensor: shutdown")
