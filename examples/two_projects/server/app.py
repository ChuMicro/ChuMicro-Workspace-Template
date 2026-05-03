"""two_projects/server — accept POSTed sensor readings on a LAN.

Listens on a TCP port via `chumicro-http-server`, exposes three
routes:

* ``GET /``           — HTML status page with the latest reading.
* ``GET /api/latest`` — JSON view of the latest reading.
* ``POST /api/sensor`` — accept a JSON ``{"sensor_id": ..., "value": ...}``
  payload and remember it.

Pair with [`two_projects/sensor/`](../sensor/) on a second board.

Scaffold a copy with
``python run.py new <name> --from examples/two_projects/server``,
then ``python run.py deploy <name>``.
"""

from chumicro_config import load_runtime_config
from chumicro_http_server import HttpServer, build_response
from chumicro_runner import Runner
from chumicro_sockets import tcp_listening_socket
from chumicro_timing import ticks_ms
from chumicro_wifi import WifiConfig, WifiService, WifiState


class _LatestState:
    """One-slot store for the most recent sensor reading."""

    def __init__(self) -> None:
        self.sensor_id: str = ""
        self.value: float | None = None
        self.received_at_ms: int = 0


def _radio_for_runtime():
    try:
        import wifi
        return wifi.radio
    except ImportError:
        return None


def run() -> None:
    config = load_runtime_config()
    wifi_section = config["wifi"]
    server_section = config["server"]

    wifi = WifiService(WifiConfig.from_dict(wifi_section))
    runner = Runner()
    runner.add(wifi)

    print("server: connecting to wifi ...")
    while not wifi.connected:
        runner.tick()
        if wifi.state == WifiState.FAILED:
            raise SystemExit(f"wifi failed: {wifi.last_error}")
    print(f"server: wifi at {wifi.ip}")

    radio = _radio_for_runtime()
    listen_port = server_section.get("listen_port", 8080)
    state = _LatestState()
    server = HttpServer(
        listener_factory=lambda: tcp_listening_socket(
            "0.0.0.0", listen_port, radio=radio,
        ),
        max_connections=server_section.get("max_connections", 2),
    )

    @server.route("/")
    def index(_request):  # noqa: ARG001 — request unused
        if state.value is None:
            body = (
                "<html><body><h1>chumicro two-project demo</h1>"
                "<p>No readings yet — waiting for sensor POST.</p>"
                "</body></html>"
            )
        else:
            body = (
                "<html><body><h1>chumicro two-project demo</h1>"
                f"<p>Latest from <b>{state.sensor_id}</b>: "
                f"<b>{state.value}</b></p>"
                f"<p>Received at: {state.received_at_ms} ms</p>"
                "</body></html>"
            )
        return build_response(200, html=body)

    @server.route("/api/latest")
    def latest(_request):  # noqa: ARG001
        return build_response(200, json={
            "sensor_id": state.sensor_id,
            "value": state.value,
            "received_at_ms": state.received_at_ms,
        })

    @server.route("/api/sensor", methods=["POST"])
    def sensor(request):
        payload = request.json()
        state.sensor_id = payload.get("sensor_id", "unknown")
        state.value = payload.get("value")
        state.received_at_ms = ticks_ms()
        print(f"server: <- {state.sensor_id} value={state.value}")
        return build_response(201, json={"ok": True})

    runner.add(server)
    print(f"server: listening on http://{wifi.ip}:{listen_port}/")
    try:
        while True:
            runner.tick()
    except KeyboardInterrupt:
        pass
    print("server: shutdown")
