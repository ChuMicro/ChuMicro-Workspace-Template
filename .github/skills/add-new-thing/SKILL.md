---
name: add-new-thing
description: Scaffold a new thing in this ChuMicro workspace, wire its config + secrets, and verify the first deploy.  Use when the user says "make a new thing", "add an X app", or asks to start a new program from scratch.
---

# Add a new thing

A "thing" is one deployable program — a directory under `things/`
with an `app.py` defining `def run(): ...` and a `config.toml` for
its knobs.  This skill walks through scaffolding one and getting
to the first successful deploy.

## 1. Pick a name

Thing directory names must be valid Python identifiers — letters,
digits, underscores; **no hyphens**, no dots, no leading digit.
The runtime imports `things.<name>.app`, so anything Python can't
import breaks deploy.

If the user typed `back-porch`, suggest `back_porch`.  If they
typed `1sensor`, suggest `sensor_one` or similar.

`python run.py new <name>` rejects invalid names up-front with a
clear message — that's a fast way to validate.

## 2. Scaffold

```bash
python run.py new my_thing
```

Copies `things/_template/` into `things/my_thing/`.  The template
typically ships:

- `app.py` — minimal `def run(): print("hello")` placeholder.
- `config.toml` — empty config sections matching the libraries
  the template imports.

Open both and edit:

- `app.py` — write the actual logic.  Most networked things
  follow the pattern in `things/example_sensor/app.py`: build
  services, register them with a `Runner`, drive `runner.tick()`
  in a `while not _SHUTDOWN_REQUESTED:` loop.
- `config.toml` — fill in board-specific values that aren't
  sensitive (SSID, broker host, sample period).  Keep credentials
  out of git: set them in `workspace.local.yml` instead.

## 3. Wire credentials

If the thing uses wifi, MQTT auth, or any other secret, add it to
`workspace.local.yml` (gitignored credential / per-developer
overlay; materialized from the chumicro-workspace package's
canonical starter during `setup`).  Use the same section-namespaced
shape as `workspace.yml`:

```yaml
defaults:
  wifi:
    password: your-actual-passphrase
  mqtt:
    password: your-broker-password
```

`config.toml` carries the public values for the same sections:

```toml
[wifi]
ssid = "YourNetwork"

[mqtt]
broker = "broker.example.com"
username = "device-user"
```

The deploy-time deep-merge layers `workspace.yml` →
`workspace.local.yml` → `config.toml`, with each later layer
winning at any key.  The resulting dict ships to the device as
`/runtime_config.msgpack`.  `workspace.local.yml` itself never
lands on the device.

## 4. First deploy

```bash
python run.py deploy my_thing
```

If a default device is set in `devices.yml` (`defaults.micropython`
or `defaults.circuitpython`), the deploy fires against that
board.  Otherwise add `--device-id <id>`.

Watch the output.  On success you'll see:

```
deploy: staged N files
deploy: executing entrypoint
<your thing's stdout here>
```

If the deploy fails, **load the `deploy-and-debug` skill** —
don't guess at fixes.

## 5. Follow REPL output

After deploy, the entrypoint runs forever (most things have
`while True: runner.tick()` style loops).  To watch what it's
printing:

```bash
python run.py repl              # interactive — Ctrl-X to exit
python run.py repl --tail 30    # stream for 30 seconds, then exit
```

`--tail` is convenient for "did the heartbeat fire?" sanity
checks; interactive REPL is for poking at variables.

## Rules

- **One name move only** — `python run.py new` doesn't rename or
  copy from non-template sources.  If the user wants to fork an
  existing thing, copy the directory by hand and rename
  carefully.
- **Don't edit `things/_template/`** — it's tool-owned and
  `update` will rewrite it.  If the user wants a different
  template starter, that's an upstream change.
- **Run `python run.py test`** if the user has tests under
  `things/<name>/tests/` before reporting the work done.
- **Surface the deploy output** to the user — don't summarize
  the success message unless they ask.  The full deploy log
  contains diagnostics future agents (or human re-runs) might
  need.
