# my-workspace

A ChuMicro project workspace.

## Quickstart

```bash
# Option A: clone this template
git clone --depth 1 https://github.com/ChuMicro/ChuMicro-Workspace-Template my-workspace
cd my-workspace
rm -rf .git && git init

# Option B: GitHub UI -> "Use this template" -> clone the resulting repo

# Then, with the workspace cloned:
python3 run.py setup           # creates .venv, installs chumicro-workspace, materializes secrets.yml
python run.py add-device my-board --address /dev/cu.usbmodem1101 --runtime micropython
python run.py new my-thing     # scaffolds things/my-thing/
# Edit things/my-thing/{config.toml, app.py} and secrets.yml as needed
python run.py deploy my-thing
```

`python3 run.py setup` is self-bootstrapping: it creates a virtualenv at
`.venv/`, installs `chumicro-workspace` and the workspace's
dependencies, materializes any files declared under `_templates/` (e.g.
`secrets.yml`), and then re-execs into the venv for any subsequent
command.  No prerequisite `pip install` is required — system Python
3.11+ is enough.

See [chumicro-workspace's guide](https://github.com/ChuMicro/ChuMicro/blob/main/workbench/workspace/docs/guide.md)
for the full workflow walkthrough.

## Layout

- `things/<name>/` — your apps.  `def run()` in `app.py`.
  - `things/_template/` — the "blank thing" copied by `python run.py new`.
  - `things/example-sensor/` — a worked example (wifi → mqtt heartbeat
    with persistent boot counter).  See the walkthrough below.
- `devices.yml` — gitignored, materialized from `_templates/devices.yml`.
  Mutated in place by `add-device` / `rename` / `probe`.
- `workspace.yml` — defaults every thing inherits.
- `secrets.yml` — gitignored, materialized from `_templates/secrets.yml`.
  Reference values via `!secret <name>`.
- `libs/` — shared user code.  Things `import` from here.
- `packages/` — gitignored, mirror-cached external libs.
- `_templates/` — tool-owned template sources.  `setup` materializes
  any missing destination at the workspace root; `update` refreshes
  these sources from upstream so newer template skeletons reach
  existing workspaces.

## Worked example: `example-sensor`

The shipped `things/example-sensor/` exercises the full ChuMicro
runtime stack (wifi + sockets + mqtt + kvstore + workspace).  Boot
to first heartbeat on a plugged-in board:

```bash
# 1. Bootstrap the workspace (one-time, after clone)
python3 run.py setup

# 2. Tell the workspace about your board
python run.py add-device my-board --address /dev/cu.usbmodem1101 --runtime micropython

# 3. Fill in your wifi password (edit secrets.yml directly — it was
#    materialized from _templates/secrets.yml during setup, so just
#    open and edit; no copy needed)
$EDITOR secrets.yml          # set wifi_password to your AP passphrase

# 4. Point the sensor at your AP + a broker (one line each)
$EDITOR things/example-sensor/config.toml
#   [wifi]    ssid = "YourNetwork"
#   [mqtt]    broker = "broker.hivemq.com"   # public test broker; swap for your own
#   [sensor]  topic  = "chumicro/example/temperature"

# 5. Deploy + watch
python run.py deploy example-sensor

# Or, if you want to follow the REPL output afterward:
python run.py repl
```

Subscribe to the topic from any MQTT client (`mosquitto_sub -h
broker.hivemq.com -t 'chumicro/example/temperature'`) and you should
see one JSON message every 5 seconds carrying the boot counter, the
on-board temperature reading, and a sequence number.  Reset the board
and the boot counter increments — `chumicro-kvstore` persisted it.

`things/example-sensor/app.py` is short on purpose — it's the
canonical reference for how to wire `WifiService` + `MQTTClient` +
`KVStore` into a tick-shaped `Runner`.  Copy + tweak.

## ChuMicro-dev mode (optional)

Co-developing chumicro libraries / `chumicro-workspace` from a sibling
clone of the [`ChuMicro` mono-repo](https://github.com/ChuMicro/ChuMicro)
(or a fork)?  Drop a `chumicro-dev.toml` next to `run.py` with:

```toml
chumicro_path = "../chumicro"
```

When `chumicro-dev.toml` is present, `python3 run.py setup` walks
`<chumicro_path>/libraries/*` and `<chumicro_path>/workbench/*` and
pip-installs every package found there as editable, BEFORE installing
the workspace's own pyproject deps.  Edits to your chumicro checkouts
flow into the workspace immediately — no rebuild, no republish.
Delete the file (or unset the path) to revert to the PyPI install
path.  `chumicro-dev.toml` is gitignored by default since different
contributors keep their checkouts in different places.
