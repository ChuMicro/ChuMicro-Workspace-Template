# `two_projects`

Multi-project LAN demo — a sensor board posts readings to a server
board over HTTP on your local network.  Two boards, two projects,
one workspace.

```
sensor (board A)         server (board B)
   POST /api/sensor   ─►   /api/sensor (accept + remember)
                          /            (status page)
                          /api/latest  (JSON view)
```

Both projects use the same wifi credentials from `secrets.yml`, so
once that's set, you can flip between them with one
`python run.py deploy` per board.

## Why this example exists

Networked projects rarely live alone — they talk to other
networked projects on the LAN.  This example shows the smallest
two-board pattern:

* **server** — opens a TCP listener via `chumicro-http-server`,
  accepts POSTed JSON, exposes a status HTML page + JSON view.
* **sensor** — periodically POSTs a fake-but-real-looking reading
  via `chumicro-requests`.

Both boards run the same boot-shim flow as the single-project
examples — one project per board, deployed independently.
Multi-project-on-one-device staging is not supported: on the
minimum-supported board class (256 KB RAM, 4 MB flash) the
flash budget doesn't accommodate two project payloads side by
side.  If you need two cooperating projects, use two boards.

## Try it

You'll need two boards plugged in and registered:

```
python run.py add-device board-a --address /dev/cu.usbmodem1101
python run.py add-device board-b --address /dev/cu.usbmodem2201
```

Scaffold the projects from the examples:

```
python run.py new garage/server --from examples/two_projects/server
python run.py new garage/sensor --from examples/two_projects/sensor
```

Set the server's IP in the sensor's config (you'll know it after
the server starts — see "Workflow" below).

```
python run.py deploy garage/server --device board-a
python run.py repl board-a --tail 30
# note the IP printed: e.g. "server: listening on http://192.168.0.42:8080/"

# Edit projects/garage/sensor/config.toml — set [target] url to that.
python run.py deploy garage/sensor --device board-b
python run.py repl board-b --tail 30
```

You should see the sensor POSTing every period and the server
acknowledging.  Open `http://<server-ip>:8080/` in a browser to
see the latest reading.

## Workflow

The IP-address dance ("deploy server first, note its IP, then
edit the sensor's config.toml") is the canonical "first-time"
pattern for a workspace example.  In a real deployment you'd
either:

* assign the server a static IP via your router's DHCP
  reservation table; or
* use mDNS so the sensor can resolve `chu-server.local` instead
  of an IP (not yet wired through the workspace template).

## What it uses

Both projects share these:

| Library | Why |
|---|---|
| `chumicro-config` | reads merged `/runtime_config.msgpack` |
| `chumicro-wifi` | sole-supervisor wifi service |
| `chumicro-sockets` | host TCP / listener primitives |
| `chumicro-runner` | tick-shaped scheduler |
| `chumicro-timing` | wraparound-safe ticks |

Plus per-project:

| Project | Library | Why |
|---|---|---|
| server | `chumicro-http-server` | listener + route registration |
| sensor | `chumicro-requests` | non-blocking HTTP/1.1 client |

## What's next

For protocol-level telemetry instead of HTTP, see
[`telemetry_publisher/`](../telemetry_publisher/).  For the full
network-stack reference (wifi → sockets → mqtt → kvstore →
workspace), see `projects/example_sensor/` in this template repo.
