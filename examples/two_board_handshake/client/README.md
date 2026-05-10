# `two_board_handshake/client`

The HTTP-client side of the two-board handshake demo.  Pairs with
the [`server/`](../server/) project running on a *different* physical
board on the same wifi.

## What it does

* Brings wifi up.
* POSTs a JSON payload (`sensor_id` + `value` + `uptime_s` + `sequence`)
  to the server's `/api/sensor` endpoint every `period_ms`
  milliseconds.
* Uses a synthetic sine-wave for the value — replace with a real
  sensor read when you have one wired up.
* Self-heals on wifi drops via `chumicro_sockets_factory`'s rebuild-on-
  connect contract.

## Try it

Deploy the server first, note the IP it prints, then update this
project's `project_config.toml` with that IP under
`[two_board] server_host`:

```
python run.py new two_board/client --from examples/two_board_handshake/client
# edit projects/two_board/client/project_config.toml — set two_board.server_host
python run.py deploy two_board/client --device-id lolin-s2-cp
python run.py repl --tail 30 --device-id lolin-s2-cp
```

Expected client output:

```
client: connecting to wifi ...
client: wifi at 192.168.0.43
client: posting to http://192.168.0.42:8080/api/sensor every 5000 ms
client: -> POST http://192.168.0.42:8080/api/sensor #0
  -> status=201
client: -> POST http://192.168.0.42:8080/api/sensor #1
  -> status=201
```

If the server's IP is wrong or unreachable, you'll see:

```
  -> error: TimeoutError(...)
```

The loop keeps going.

## What it uses

| Library | Why |
|---|---|
| `chumicro-config` | reads the merged `/runtime_config.msgpack` |
| `chumicro-wifi` | sole-supervisor wifi service |
| `chumicro-sockets` | host TCP for the HTTP client |
| `chumicro-requests` | non-blocking HTTP/1.1 client |
| `chumicro-runner` | tick-shaped task scheduler |
| `chumicro-timing` | wraparound-safe `ticks_ms` / `ticks_diff` |

## What's next

Same shape as `periodic_get/`, but talking to your own board on the
LAN instead of a public URL.  Once round-trip is confirmed:

* Swap the synthetic value for a real sensor read (BME280, DHT22, an
  ADC pin, etc.).
* Bump the cadence up to interactive rates (e.g. 100 ms) if your
  network can handle it.
* Add a second client board posting under a different `sensor_id` —
  the server's `/api/latest` shows whichever posted most recently.
