"""Example sensor project — temperature publisher with persistent boot counter.

End-to-end fixture that exercises the full ChuMicro stack:

* `chumicro-wifi`     — connects to the AP from the merged runtime config
* `chumicro-sockets`  — host TCP for the MQTT transport (TLS optional)
* `chumicro-mqtt`     — non-blocking publisher on a heartbeat
* `chumicro-kvstore`  — persistent boot counter survives resets
* `chumicro-runner`   — tick-based scheduling glue (no async, no threads)
* `chumicro-config`   — reads the deploy-time-merged runtime config

Edit ``project_config.toml`` next to this file to change broker /
topic / period; wifi credentials live in the workspace's gitignored
``secrets.toml`` and reach the device via the deploy-time deep-merge.
"""

from chumicro_config import load_runtime_config
from chumicro_kvstore import KVStore
from chumicro_mqtt import MQTTClient
from chumicro_mqtt.client import ProtocolState
from chumicro_runner import Runner
from chumicro_sockets import tcp_client_socket, tls_client_socket
from chumicro_timing import ticks_add, ticks_diff, ticks_ms
from chumicro_wifi import WifiConfig, WifiService, WifiState

_KV_BOOT_COUNT_KEY = "boot_count"
_RECONNECT_BACKOFF_MS = 1000

#: Flag the main loop in ``run()`` polls every tick.  Setting this to
#: ``True`` (from the REPL, a test harness, or a same-process callback)
#: tells the loop to exit cleanly after the current tick finishes.
#: Ctrl-C from the REPL is the convenient interactive path; the flag is
#: the general path for embedded test runs and future supervisor hooks.
_SHUTDOWN_REQUESTED = False


def request_shutdown():
    """Ask ``run()``'s tick loop to exit on the next iteration."""
    global _SHUTDOWN_REQUESTED
    _SHUTDOWN_REQUESTED = True


class _TemperatureProbe:
    """Reads a temperature value.

    Uses the on-board CPU thermistor when one is exposed by the
    runtime; otherwise returns a slow synthetic triangle wave so the
    heartbeat is observable on a sensorless board.
    """

    def read_celsius(self):
        try:
            import microcontroller
            return float(microcontroller.cpu.temperature)
        except (ImportError, AttributeError, RuntimeError):
            pass
        try:
            import esp32
            return float(esp32.mcu_temperature())
        except (ImportError, AttributeError):
            pass
        return 20.0 + (ticks_ms() % 10000) / 1000.0


class HeartbeatPublisher:
    """Tick-shaped MQTT publisher.

    Skips its work tick when the MQTT client is not connected; otherwise
    publishes one JSON message per ``period_ms`` containing the boot
    counter, the temperature reading, and a monotonically-increasing
    sequence number.
    """

    def __init__(self, *, mqtt_client, probe, topic, period_ms, boot_count):
        self._mqtt_client = mqtt_client
        self._probe = probe
        self._topic = topic
        self._period_ms = period_ms
        self._boot_count = boot_count
        self._next_at = ticks_ms()
        self._published = 0

    def check(self, now_ms):
        if self._mqtt_client.state != ProtocolState.CONNECTED:
            return False
        return ticks_diff(now_ms, self._next_at) >= 0

    def handle(self, now_ms):
        celsius = self._probe.read_celsius()
        payload = (
            f'{{"boot": {self._boot_count}, '
            f'"celsius": {celsius:.2f}, '
            f'"n": {self._published}}}'
        )
        try:
            self._mqtt_client.publish(self._topic, payload, qos=1)
            self._published += 1
            self._next_at = ticks_add(now_ms, self._period_ms)
        except Exception as error:
            print(f"sensor: publish failed: {error}")
            self._next_at = ticks_add(now_ms, _RECONNECT_BACKOFF_MS)


def _bump_boot_counter(kv_store):
    next_count = kv_store.get(_KV_BOOT_COUNT_KEY, 0) + 1
    kv_store[_KV_BOOT_COUNT_KEY] = next_count
    kv_store.commit()
    return next_count


def _make_socket_factory(config):
    """Return a closure that builds a fresh connected socket.

    Passed to ``MQTTClient`` so the client can self-heal after a
    wifi-drop: the next tick after the socket dies builds a new one
    via this factory and re-issues CONNECT automatically.
    """
    host = config.require("mqtt.broker")
    port = config.require("mqtt.port")
    use_tls = config.get("mqtt.tls", False)

    def build_socket():
        if use_tls:
            return tls_client_socket(host, port)
        return tcp_client_socket(host, port)

    return build_socket


def run():
    config = load_runtime_config()
    topic = config.require("sensor.topic")

    kv_store = KVStore()
    boot_count = _bump_boot_counter(kv_store)
    print(f"sensor: boot #{boot_count}")

    runner = Runner()

    wifi = WifiService(WifiConfig.from_config(config))
    runner.add(wifi)

    print("sensor: connecting to wifi...")
    while not wifi.connected:
        runner.tick()
        if wifi.state == WifiState.FAILED:
            raise SystemExit(f"wifi failed: {wifi.last_error}")
    print(f"sensor: wifi connected at {wifi.ip}")

    socket_factory = _make_socket_factory(config)
    mqtt_client = MQTTClient(
        socket_factory=socket_factory,
        client_id=config.require("mqtt.client_id"),
        keep_alive_seconds=config.get("mqtt.keep_alive_seconds", 60),
    )
    mqtt_client.connect()
    runner.add(mqtt_client)

    publisher = HeartbeatPublisher(
        mqtt_client=mqtt_client,
        probe=_TemperatureProbe(),
        topic=topic,
        period_ms=config.require("sensor.publish_period_ms"),
        boot_count=boot_count,
    )
    runner.add(publisher)

    print(f"sensor: publishing to {topic}")
    try:
        while not _SHUTDOWN_REQUESTED:
            runner.tick()
    except KeyboardInterrupt:
        pass
    print("sensor: shutdown")
