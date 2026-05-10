"""Two-board handshake — server side.

Pairs with ``examples/two_board_handshake/client/`` running on a
*different* physical board on the same wifi network.  This side
opens an HTTP server and accepts JSON readings from the client at
``POST /api/sensor``, also exposing a tiny status page at ``GET /``
and a JSON view at ``GET /api/latest``.

Architecture:

* Single-process, runner-shaped: ``HttpServer.check`` /
  ``HttpServer.handle`` advance accept / dispatch / response one
  tick at a time, so an LED can keep blinking through inbound
  request handling.
* In-memory state — no persistence (a reset clears the latest
  reading; the client just keeps POSTing).
* Listens on ``0.0.0.0:8080`` by default — adjust
  ``http_server.bind_port`` in ``project_config.toml`` if your
  network conflicts.

Scaffold a copy with
``python run.py new two_board/server --from examples/two_board_handshake/server``,
then ``python run.py deploy two_board/server`` and watch its serial
output for the IP it prints — you'll plug that IP into the client's
``project_config.toml``.
"""

from chumicro_config import load_runtime_config
from chumicro_http_server import HttpServer, build_response
from chumicro_runner import Runner
from chumicro_sockets import tcp_listening_socket
from chumicro_timing import ticks_ms
from chumicro_wifi import WifiConfig, WifiService, WifiState


class _SensorState:
    """Latest sensor reading received from the client board."""

    __slots__ = ("received_at_ms", "sensor_id", "value")

    received_at_ms: int | None
    sensor_id: str | None
    value: float | None

    def __init__(self) -> None:
        self.sensor_id = None
        self.value = None
        self.received_at_ms = None


def _make_listener_factory(host: str, port: int):
    """Closure that builds the listening socket on each accept loop."""

    def build_listener():
        return tcp_listening_socket(host, port)

    return build_listener


def _register_routes(server: HttpServer, state: _SensorState) -> None:
    @server.route("/")
    def index(_request):
        if state.value is None:
            body = (
                "<html><body><h1>two_board_handshake</h1>"
                "<p>No readings yet — waiting for client POST.</p>"
                "</body></html>"
            )
        else:
            body = (
                "<html><body><h1>two_board_handshake</h1>"
                f"<p>Latest from <b>{state.sensor_id}</b>:"
                f" <b>{state.value}</b></p>"
                f"<p>Received at: {state.received_at_ms} ms</p>"
                "</body></html>"
            )
        return build_response(200, html=body)

    @server.route("/api/latest")
    def latest(_request):
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
        print(f"server: <- sensor={state.sensor_id} value={state.value}")
        return build_response(201, json={"ok": True})


def run() -> None:
    config = load_runtime_config()

    bind_host = config.get("http_server.bind_host", "0.0.0.0")
    bind_port = config.get("http_server.bind_port", 8080)

    wifi = WifiService(WifiConfig.from_config(config))
    runner = Runner()
    runner.add(wifi)

    print("server: connecting to wifi ...")
    while not wifi.connected:
        runner.tick()
        if wifi.state == WifiState.FAILED:
            raise SystemExit(f"wifi failed: {wifi.last_error}")
    print(f"server: wifi at {wifi.ip}")
    print(f"server: listening on http://{wifi.ip}:{bind_port}/")
    print(f"server: configure the client's two_board.server_host = {wifi.ip!r}")

    state = _SensorState()
    server = HttpServer(listener_factory=_make_listener_factory(bind_host, bind_port))
    _register_routes(server, state)
    runner.add(server)

    try:
        while True:
            runner.tick()
    except KeyboardInterrupt:
        pass
    print("server: shutdown")
