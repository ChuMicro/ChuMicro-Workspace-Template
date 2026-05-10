# `two_board_handshake/server`

The HTTP-server side of the two-board handshake demo.  Pairs with
the [`client/`](../client/) project running on a *different* physical
board on the same wifi.

## What it does

* Brings wifi up.
* Opens an HTTP server on `0.0.0.0:8080`.
* Accepts JSON readings at `POST /api/sensor`, stores the latest in
  RAM, exposes `GET /api/latest` (JSON) and `GET /` (HTML status page).
* Prints its own IP at startup so you know what to put in the client's
  config.

## Try it

Both boards must be on the same wifi network.  Register both boards
in `devices.yml` (e.g. `pi-pico-w-cp` for the server, `lolin-s2-cp`
for the client) before deploying.

```
python run.py new two_board/server --from examples/two_board_handshake/server
python run.py deploy two_board/server --device-id pi-pico-w-cp
python run.py repl --tail 30 --device-id pi-pico-w-cp
```

Note the IP the server prints, then deploy the client with that IP
plugged into its `project_config.toml`.  See
[`../client/README.md`](../client/README.md).

Expected server output:

```
server: connecting to wifi ...
server: wifi at 192.168.0.42
server: listening on http://192.168.0.42:8080/
server: configure the client's two_board.server_host = '192.168.0.42'
server: <- sensor=demo-temp value=21.4
server: <- sensor=demo-temp value=21.6
```

You can also hit it from your laptop while the client is running:

```
curl http://192.168.0.42:8080/api/latest
```

## What it uses

| Library | Why |
|---|---|
| `chumicro-config` | reads the merged `/runtime_config.msgpack` |
| `chumicro-wifi` | sole-supervisor wifi service |
| `chumicro-sockets` | host TCP listener |
| `chumicro-http-server` | runner-shaped HTTP/1.1 server |
| `chumicro-runner` | tick-shaped task scheduler |
| `chumicro-timing` | wraparound-safe `ticks_ms` |

## What's next

Once the round-trip is working, swap the synthetic sensor on the
client side for a real one (BME280, DHT22, an ADC pin, etc.) and
extend the server's state machine to log a rolling window or push
each reading to MQTT.
