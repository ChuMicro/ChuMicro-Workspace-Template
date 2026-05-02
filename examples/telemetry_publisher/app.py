"""Telemetry publisher — wifi up, MQTT-publish on a heartbeat.

Pairs wifi with `chumicro-mqtt` to push a JSON payload to a topic
every ``period_ms``.  Uses the socket-factory shape so a wifi drop
self-heals: the next tick after the socket dies builds a new
connection via the factory and re-issues CONNECT automatically
(see `things/example_sensor/` in this repo for the full
network-stack reference).

Scaffold a copy with
``python run.py new <name> --from examples/telemetry_publisher``,
then ``python run.py deploy <name>``.
"""

from chumicro_config import load_runtime_config
from chumicro_mqtt import MQTTClient
from chumicro_mqtt.client import ProtocolState
from chumicro_runner import Runner
from chumicro_sockets import tcp_client_socket, tls_client_socket
from chumicro_timing import ticks_add, ticks_diff, ticks_ms
from chumicro_wifi import WifiConfig, WifiService, WifiState


class _HeartbeatPublisher:
    """Tick-shaped MQTT publisher.

    Skips its work tick when the MQTT client isn't connected;
    otherwise emits one JSON message per ``period_ms`` carrying
    a monotonic sequence number.  Replace the ``payload`` body
    with your own sensor reading once the round-trip works.
    """

    def __init__(self, *, mqtt_client, topic, period_ms):
        self._mqtt = mqtt_client
        self._topic = topic
        self._period_ms = period_ms
        self._next_at = ticks_ms()
        self._sequence = 0

    def check(self, now_ms):
        if self._mqtt.state != ProtocolState.CONNECTED:
            return False
        return ticks_diff(now_ms, self._next_at) >= 0

    def handle(self, now_ms):
        payload = f'{{"n": {self._sequence}}}'
        try:
            self._mqtt.publish(self._topic, payload, qos=1)
            print(f"telemetry_publisher: -> {self._topic} #{self._sequence}")
            self._sequence += 1
            self._next_at = ticks_add(now_ms, self._period_ms)
        except Exception as error:  # noqa: BLE001
            # Backpressure / transient error — back off one period.
            print(f"telemetry_publisher: publish failed: {error!r}")
            self._next_at = ticks_add(now_ms, self._period_ms)


def _radio_for_runtime():
    """CircuitPython exposes `wifi.radio`; MicroPython / CPython don't."""
    try:
        import wifi
        return wifi.radio
    except ImportError:
        return None


def _make_socket_factory(mqtt_section, radio):
    """Closure that builds a fresh TCP / TLS socket on each connect.

    `MQTTClient` calls this every time it (re-)issues CONNECT, which
    is what makes self-heal-on-drop work — the dead socket stays
    dead, the new one walks through DNS + connect from scratch.
    """
    host = mqtt_section["broker"]
    port = mqtt_section["port"]
    use_tls = mqtt_section.get("tls", False)

    def build_socket():
        if use_tls:
            return tls_client_socket(host, port, radio=radio)
        return tcp_client_socket(host, port, radio=radio)

    return build_socket


def run():
    config = load_runtime_config()
    wifi_section = config["wifi"]
    mqtt_section = config["mqtt"]

    wifi = WifiService(WifiConfig.from_dict(wifi_section))
    runner = Runner()
    runner.add(wifi)

    print("telemetry_publisher: connecting to wifi ...")
    while not wifi.connected:
        runner.tick()
        if wifi.state == WifiState.FAILED:
            raise SystemExit(f"wifi failed: {wifi.last_error}")
    print(f"telemetry_publisher: wifi at {wifi.ip}")

    radio = _radio_for_runtime()
    mqtt_client = MQTTClient(
        socket_factory=_make_socket_factory(mqtt_section, radio),
        client_id=mqtt_section["client_id"],
        keep_alive_seconds=mqtt_section.get("keep_alive_seconds", 60),
    )
    mqtt_client.connect()
    runner.add(mqtt_client)
    runner.add(_HeartbeatPublisher(
        mqtt_client=mqtt_client,
        topic=mqtt_section["topic"],
        period_ms=mqtt_section.get("publish_period_ms", 5000),
    ))

    print(f"telemetry_publisher: publishing to {mqtt_section['topic']}")
    try:
        while True:
            runner.tick()
    except KeyboardInterrupt:
        pass
    print("telemetry_publisher: shutdown")
