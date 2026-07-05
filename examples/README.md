# Examples

Worked-out demos you can read and copy into your own projects.

`python3 run.py update` rewrites this folder from the template
upstream, so treat it as reading material, not user code.  When you
want to start from one, scaffold a real project under `projects/`:

```
python3 run.py new garage/heater --from examples/wifi_only
```

That copies the example's tree into `projects/garage/heater/`, leaving
the original here for the next time you reach for it.  Edit the
copy under `projects/`, then `python3 run.py deploy garage/heater`.

## What's in here

| Example | What it does |
|---|---|
| [`hello_world/`](hello_world/) | Trivial print loop.  Proves your deploy chain works end to end before you bring wifi into the picture. |
| [`wifi_only/`](wifi_only/) | Wifi up plus a status print on a heartbeat.  The minimum that exercises `chumicro-wifi` and the merged-config flow. |
| [`periodic_get/`](periodic_get/) | Wifi plus a non-blocking HTTP GET on a heartbeat, exercising `chumicro-sockets` and `chumicro-requests`. |
| [`telemetry_publisher/`](telemetry_publisher/) | Wifi plus MQTT publish on a heartbeat: `chumicro-mqtt` over `chumicro-sockets`, self-healing on a wifi drop. |
| [`two_board_handshake/`](two_board_handshake/) | Two physical boards on the same wifi.  One runs `chumicro-http-server`; the other POSTs JSON readings to it on a heartbeat. |

## How they fit together

A natural progression for someone new to a board:

1. **`hello_world/`**: verify the deploy chain works.  No wifi.
2. **`wifi_only/`**: verify your wifi credentials reach the device.
   No upper-layer protocol.
3. **`periodic_get/`**: verify the network stack moves real bytes.
   HTTP client, no server.
4. **`telemetry_publisher/`**: same shape, MQTT instead of HTTP.
   Confirms publish-only telemetry flows.
5. **`two_board_handshake/`**: two physical boards on one network,
   talking to each other over HTTP.  The smallest "device A talks
   to device B" pattern; needs two registered boards in `devices.yml`.

For the full network reference (wifi, sockets, MQTT, and persistent
state across resets in one program), see `projects/example_sensor/`
in this template repo.
