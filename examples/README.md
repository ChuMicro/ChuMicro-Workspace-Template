# Examples

Worked-out demos you can read and copy into your own things.

`python run.py update` rewrites this folder from the canonical
template upstream — they're reading material, not user code.  When
you want to start from one, scaffold a real thing under `things/`:

```
python run.py new garage/heater --from examples/wifi_only
```

That copies the example's tree into `things/garage/heater/`, leaving
the original here for the next time you reach for it.  Edit the
copy under `things/`, then `python run.py deploy garage/heater`.

## What's in here

| Example | What it does |
|---|---|
| [`hello_world/`](hello_world/) | Trivial print loop — proves your deploy chain works end-to-end before you bring wifi into the picture. |
| [`wifi_only/`](wifi_only/) | Wifi up + status print on a heartbeat — minimum that exercises `chumicro-wifi` + the merged-config flow. |

## Planned (not yet shipped)

The Phase 1 plan calls for three more examples that will land in
follow-on commits:

* `periodic_get/` — wifi + `chumicro-requests` heartbeat fetch.
* `telemetry_publisher/` — wifi + `chumicro-mqtt` periodic publish.
* `two_things/{server,sensor}/` — multi-thing LAN demo (HTTP server
  on one board, sensor poster on another).

Until they ship, the `things/example_sensor/` thing in this template
repo serves as the "full network stack" reference — wifi → sockets →
mqtt → kvstore → workspace, end-to-end.
