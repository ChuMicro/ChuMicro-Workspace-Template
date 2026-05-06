# `telemetry_publisher`

Wifi up, MQTT publish on a heartbeat.  Same shape as
[`periodic_get/`](../periodic_get/) but pushes data via MQTT
instead of pulling via HTTP.

## Why this example exists

MQTT is the canonical protocol for "device → service" telemetry
flows.  This example exercises the full publisher path:
TCP (or TLS) socket → MQTT CONNECT → periodic PUBLISH → ACK.
The socket-factory shape means a wifi drop self-heals — the
next tick after the socket dies builds a new connection via the
factory and re-issues CONNECT.

The shipped payload is a trivial JSON sequence counter.  Replace
the `payload` body in `_HeartbeatPublisher.handle` with your
real sensor reading once the round-trip works (the
`projects/example_sensor/` reference in this template repo shows
the full version with on-board temperature + persistent boot
counter).

## Try it

```
python run.py new my_publisher --from examples/telemetry_publisher
# edit projects/my_publisher/project_config.toml — set broker / topic / cadence
python run.py deploy my_publisher
python run.py repl --tail 30
```

In another terminal, subscribe to the topic:

```
mosquitto_sub -h broker.hivemq.com -t 'chumicro/example/telemetry'
```

Expected `repl --tail` output:

```
telemetry_publisher: connecting to wifi ...
telemetry_publisher: wifi at 192.168.0.42
telemetry_publisher: publishing to chumicro/example/telemetry
telemetry_publisher: -> chumicro/example/telemetry #0
telemetry_publisher: -> chumicro/example/telemetry #1
...
```

And `mosquitto_sub` showing one JSON line per tick:

```
{"n": 0}
{"n": 1}
{"n": 2}
```

## TLS

Set `[mqtt] tls = true` and bump `port` to `8883` to exercise the
TLS path.  TLS-on-MicroPython requires a build with
`MBEDTLS_PEM_PARSE_C` enabled (the rp2 default doesn't include
it; the chumicro-sockets adapter handles PEM→DER conversion
automatically when the workspace's runtime config supplies a CA
bundle, but check `projects/example_sensor/` for the recipe).

## What it uses

| Library | Why |
|---|---|
| `chumicro-config` | reads the merged `/runtime_config.msgpack` |
| `chumicro-wifi` | sole-supervisor wifi service |
| `chumicro-sockets` | host TCP / TLS for the MQTT transport |
| `chumicro-mqtt` | non-blocking MQTT 3.1.1 client (QoS 0 + 1) |
| `chumicro-runner` | tick-shaped task scheduler |
| `chumicro-timing` | wraparound-safe `ticks_ms` / `ticks_diff` |

## What's next

For multi-project demos, see
[`two_projects/`](../two_projects/) — a sensor project posts to a
server project via plain HTTP on the same LAN.
