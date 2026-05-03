# Examples

Worked-out demos you can read and copy into your own projects.

`python run.py update` rewrites this folder from the canonical
template upstream — they're reading material, not user code.  When
you want to start from one, scaffold a real project under `projects/`:

```
python run.py new garage/heater --from examples/wifi_only
```

That copies the example's tree into `projects/garage/heater/`, leaving
the original here for the next time you reach for it.  Edit the
copy under `projects/`, then `python run.py deploy garage/heater`.

## What's in here

| Example | What it does |
|---|---|
| [`hello_world/`](hello_world/) | Trivial print loop — proves your deploy chain works end-to-end before you bring wifi into the picture. |
| [`wifi_only/`](wifi_only/) | Wifi up + status print on a heartbeat — minimum that exercises `chumicro-wifi` + the merged-config flow. |
| [`periodic_get/`](periodic_get/) | Wifi + non-blocking HTTP GET on a heartbeat — exercises the `chumicro-sockets` + `chumicro-requests` upper-layer stack. |
| [`telemetry_publisher/`](telemetry_publisher/) | Wifi + MQTT publish on a heartbeat — `chumicro-mqtt` over `chumicro-sockets`, with self-heal-on-drop via the socket-factory shape. |
| [`two_projects/`](two_projects/) | Multi-project LAN demo — a sensor board POSTs JSON readings to a server board running `chumicro-http-server`. |

## How they fit together

A natural progression for someone new to a board:

1. **`hello_world/`** — verify the deploy chain works.  No wifi.
2. **`wifi_only/`** — verify your wifi credentials reach the
   device.  No upper-layer protocol.
3. **`periodic_get/`** — verify the network stack moves real
   bytes.  HTTP client, no server.
4. **`telemetry_publisher/`** — same shape, MQTT instead of HTTP.
   Confirms publish-only telemetry flows.
5. **`two_projects/`** — two boards, one network, one workspace.
   The smallest "device A talks to device B" pattern.

For the full network reference (wifi → sockets → mqtt →
kvstore → workspace, with persistent state across resets),
see `projects/example_sensor/` in this template repo.
