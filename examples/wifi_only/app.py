"""wifi_only project — bring wifi up, log status on a heartbeat.

Smallest example that exercises:

* the deploy-time config merge (secrets.toml + this project's
  ``project_config.toml`` flatten into a single
  ``/runtime_config.msgpack`` that ``chumicro-config`` reads);
* ``chumicro-wifi``'s state machine (cooperative connect, auto-
  reconnect on drop);
* the runner pattern: ``add_periodic`` schedules the status print,
  and ``run_until()`` drives ``tick`` + ``wait`` so the CPU parks
  between beats instead of busy-spinning.

No sockets, no upper-layer protocols — once wifi is up, the loop
just prints status.  Great as the second deploy after
``hello_world/`` to confirm credentials in ``secrets.toml`` flow
through to the device.

Scaffold a copy with
``python run.py new <name> --from examples/wifi_only``, edit the
wifi credentials in your workspace's gitignored ``secrets.toml``
under ``[wifi]``, then ``python run.py deploy <name>``.
"""

from chumicro_config import load_runtime_config
from chumicro_runner import Runner
from chumicro_wifi import WifiConfig, WifiService, WifiState


def run() -> None:
    config = load_runtime_config()
    period_ms = config.get("status.period_ms", 5000)

    wifi = WifiService(WifiConfig.from_config(config))

    def report_status(now_ms: int) -> None:
        if wifi.state == WifiState.CONNECTED:
            print(f"wifi: connected at {wifi.ip}")
        else:
            print(f"wifi: {wifi.state}")

    def report_fault(entry, error):
        print("SERVICE_FAULT", entry.service, repr(error))

    runner = Runner(on_handler_error=report_fault)
    runner.add(wifi)
    runner.add_periodic(report_status, period_ms=period_ms)

    print("wifi_only: connecting ...")
    runner.run_until()  # never completes — parks the CPU between beats
