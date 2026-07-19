"""Telemetry publisher: wifi up, MQTT-publish on a heartbeat.

Pairs wifi with `chumicro-mqtt` to push a JSON payload to a topic
every ``period_ms``.  ``MQTTClient.from_config`` owns the transport,
reconnect backoff, and self-heal-on-drop; a sample produced before
the broker session is up buffers in the client's pre-connect queue
and flushes on CONNACK (``when_disconnected="queue"``, the default),
so the publisher needs no CONNECTED guard.  See
`projects/example_sensor/` for the full network-stack reference.

Scaffold a copy with
``python3 run.py new <name> --from examples/telemetry_publisher``,
then ``python3 run.py deploy <name>``.
"""

import json

from chumicro_config import load_runtime_config
from chumicro_mqtt import MQTTClient
from chumicro_runner import Runner
from chumicro_wifi import WifiConfig, WifiService, WifiState


def run():
    config = load_runtime_config()
    topic = config.require("mqtt.topic")
    period_ms = config.get("mqtt.publish_period_ms", 5000)

    wifi = WifiService(WifiConfig.from_config(config))
    mqtt = MQTTClient.from_config(config, radio=wifi.adapter.radio)

    def on_wifi_state(_old, new):
        if new == WifiState.CONNECTED:
            print(f"telemetry_publisher: wifi at {wifi.ip}")
            mqtt.connect()

    wifi.on_state_change(on_wifi_state)

    seq = 0

    def publish_reading(now_ms):
        nonlocal seq
        # Replace this payload with your own sensor reading once the
        # round-trip works.
        payload = json.dumps({"n": seq})
        mqtt.publish(topic, payload, qos=1)  # queues until CONNECTED, flushes on CONNACK
        print(f"telemetry_publisher: -> {topic} #{seq}")
        seq += 1

    def report_fault(entry, error):
        print("SERVICE_FAULT", entry.service, repr(error))

    runner = Runner(on_handler_error=report_fault)
    runner.add(wifi)
    runner.add(mqtt)
    runner.add_periodic(publish_reading, period_ms=period_ms)

    print(f"telemetry_publisher: publishing to {topic}")
    runner.run_until(lambda: wifi.state == WifiState.FAILED)
    raise SystemExit(f"telemetry_publisher: wifi failed: {wifi.last_error}")
