"""wifi_only project — bring wifi up, log status on a heartbeat.

Smallest example that exercises:

* the deploy-time config merge (workspace.yml + secrets.yml +
  this project's `config.toml` flatten into a single
  `/runtime_config.msgpack` that `chumicro-config` reads);
* `chumicro-wifi`'s state machine (cooperative connect, auto-
  reconnect on drop);
* the runner-shaped tick loop pattern (`Runner` calls each
  registered task's `check` / `handle` once per `tick`).

No sockets, no upper-layer protocols — once wifi is up, the loop
just prints status until you stop it.  Great as the second deploy
after `hello_world/` to confirm credentials in `secrets.yml`
flow through to the device.

Scaffold a copy with
``python run.py new <name> --from examples/wifi_only``, edit
the wifi credentials in your workspace's gitignored ``secrets.yml``,
then ``python run.py deploy <name>``.
"""

from chumicro_config import load_runtime_config
from chumicro_runner import Runner
from chumicro_timing import ticks_add, ticks_diff, ticks_ms
from chumicro_wifi import WifiConfig, WifiService, WifiState


class _StatusBeacon:
    """Print one line per period describing wifi state.

    Runner-shaped (``check`` / ``handle``).  Uses ``ticks_ms`` /
    ``ticks_diff`` so the schedule survives the 32-bit wraparound
    that hits MicroPython's monotonic clock every ~50 days.
    """

    def __init__(self, *, wifi_service: WifiService, period_ms: int) -> None:
        self._wifi = wifi_service
        self._period_ms = period_ms
        self._next_at = ticks_ms()

    def check(self, now_ms: int) -> bool:
        return ticks_diff(now_ms, self._next_at) >= 0

    def handle(self, now_ms: int) -> None:
        if self._wifi.state == WifiState.CONNECTED:
            print(f"wifi: connected at {self._wifi.ip}")
        else:
            print(f"wifi: {self._wifi.state}")
        self._next_at = ticks_add(now_ms, self._period_ms)


def run() -> None:
    config = load_runtime_config()
    wifi_section = config["wifi"]
    period_ms = config.get("status", {}).get("period_ms", 5000)

    runner = Runner()
    wifi = WifiService(WifiConfig.from_dict(wifi_section))
    runner.add(wifi)
    runner.add(_StatusBeacon(wifi_service=wifi, period_ms=period_ms))

    print("wifi_only: connecting ...")
    while True:
        try:
            runner.tick()
        except KeyboardInterrupt:
            break
    print("wifi_only: shutdown")
