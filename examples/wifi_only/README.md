# `wifi_only`

Smallest network-stack example: bring wifi up, log state on a
heartbeat.  Once it's printing `wifi: connected at <ip>`, you've
confirmed every layer between `secrets.toml` and the radio works.

## Why this example exists

Wifi is the layer most likely to surface "config didn't reach the
device" problems — a typo in `secrets.toml`, a missing `password`
field, a `replace-with-your-...` placeholder forgotten on the
user's first deploy.  Running this *before* the higher-level
network examples (HTTP, MQTT) means a failure is unambiguously
about wifi rather than the protocol layer above it.

## Try it

1. Edit your workspace's gitignored `secrets.toml` — set
   `[wifi] password` to your AP's password.
2. Either set `ssid` in `wifi_only/project_config.toml` (lives in
   the project's copy under `projects/<name>/`) or in your
   workspace's `secrets.toml` `[wifi]` block.

```
python run.py new my_first_network --from examples/wifi_only
# edit projects/my_first_network/project_config.toml or secrets.toml
python run.py deploy my_first_network --tail 30
```

Expected output:

```
wifi_only: connecting ...
wifi: connecting
wifi: connecting
wifi: connected at 192.168.0.42
wifi: connected at 192.168.0.42
...
```

The `connecting → connected` transition can take a few seconds.
If you see repeated `wifi: failed` lines instead, the wifi
service's reconnect supervisor is retrying — check the credentials
and the host SSID first.  The lower-level cause shows up in
`WifiService.last_error` (drop into `python run.py repl` and run
`wifi.last_error` to inspect).

## What it uses

| Library | Why |
|---|---|
| `chumicro-config` | reads the merged `/runtime_config.msgpack` deploy lays at the device root |
| `chumicro-runner` | tick-shaped scheduler — `add_periodic` runs the status beacon; `run_until()` parks the CPU between beats |
| `chumicro-wifi` | sole-supervisor wifi service with state machine + auto-reconnect |

## What's next

Once `wifi_only` is solid, the natural follow-on is a project that
uses the network for something — `projects/example_sensor/` in this
template repo is the full reference (wifi → sockets → mqtt →
kvstore → workspace), or wait for the upcoming `examples/`
follow-ons (`periodic_get/`, `telemetry_publisher/`,
`two_projects/`) listed in [`examples/README.md`](../README.md).
