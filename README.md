# my-workspace

A clone-and-go ChuMicro project layout.  Safer than editing
`code.py` directly on the device — atomic deploys, no FAT-filesystem
wear from save-on-every-keystroke, no losing files when CIRCUITPY
hiccups.

**Recommended even if you only have one project on one board.**

> Rename this directory + this README's title to whatever you want
> to call your workspace.  This is your repo now.

## Why a workspace (instead of editing on the device)

When you mount a CircuitPython board and edit files on the
`/CIRCUITPY` drive, every save writes to the board's FAT filesystem.
Three things go wrong over time:

* **Flash wear.** CP boards typically have 2–4 MB of flash with
  modest erase-cycle budgets.  Save-on-every-keystroke editing eats
  through it faster than you'd think.
* **FAT corruption.**  CIRCUITPY uses FAT12/FAT16/FAT32, which isn't
  crash-safe.  An interrupted write — host suspending, cable jiggling,
  board resetting mid-save — leaves files truncated or corrupt.
  Worst case the drive becomes unmountable.
* **Lost work.**  When the drive does hiccup (on macOS, the
  FSKit / DiskArbitration wedge can leave the drive unmountable
  until you eject + re-plug), files you thought were saved may
  be gone.

A workspace keeps your code on your laptop in version control, runs
lint + tests against it like any normal Python project, and ships
it to the board only when you ask.  Deploys are atomic
(write-then-rename in flash mode, or RAM-mode for fast iteration
with no flash writes at all).  Your editor, your VCS, your tests,
your habits — no special "are you sure?" dance because the device
filesystem isn't in your edit loop.

## Quickstart

```bash
# Option A: clone this template
git clone --depth 1 https://github.com/ChuMicro/ChuMicro-Workspace-Template my-workspace
cd my-workspace
rm -rf .git && git init                 # start your own history

# Option B: GitHub UI -> "Use this template" -> clone the resulting repo

# Then, with the workspace cloned:
python3 run.py setup                    # creates .venv, installs chumicro-workspace, materializes workspace.yml + devices.yml
python run.py add-device my-board --address /dev/cu.usbmodem1101 --runtime micropython
python run.py new my_project            # scaffolds projects/my_project/
# Edit workspace.yml (wifi credentials) and projects/my_project/{config.toml, app.py}
python run.py dump-config my_project    # (optional) preview the merged config the device will read
python run.py deploy my_project
```

`python3 run.py setup` is self-bootstrapping: creates `.venv/`,
installs `chumicro-workspace`, materializes the gitignored
`workspace.yml` + `devices.yml` from the workbench's canonical
starters, and re-execs into the venv.  No `pip install` prerequisite
— system Python 3.11+ is enough.

For the full workflow walkthrough — including multi-board / multi-
project flows once you've outgrown a single project — see
[chumicro-workspace's hosted docs](https://chumicro.github.io/ChuMicro/workspace/stable/).

## Layout

- `projects/<name>/` — your projects.  `def run()` in `app.py`.  Names
  may be nested (`projects/upstairs/bedroom_sensor/`,
  `projects/garage/sensors/door_open/`); `python run.py projects` shows
  the tree.
  - `projects/_template/` — the blank project copied by `python run.py new`.
  - `projects/example_sensor/` — a worked example (wifi → mqtt
    heartbeat with persistent boot counter).  See the walkthrough
    below.
- `examples/` — read-only worked demos.  Scaffold a real project
  from one with `python run.py new <name> --from examples/<example>`;
  see [`examples/README.md`](examples/README.md) for the index.
  This folder is tool-owned: `python run.py update` rewrites it from
  the canonical template upstream.
- `devices.yml` — gitignored, materialized by `setup` from the
  `chumicro-workspace` package's canonical starter (single source of
  truth across every workspace).  Mutated in place by `add-device` /
  `rename` / `probe`.
- `workspace.yml` — gitignored, materialised by `setup` from the
  `chumicro-workspace` package's canonical starter.  Holds workspace-
  wide defaults *and* your credentials in one place; never commits
  to git.  Per-project `config.toml` deep-merges on top.
- `shared/` — flat user-authored helper modules shared between
  projects.  Drop a `.py` file and `import` it as `from shared.foo
  import bar`.  See [`shared/README.md`](shared/README.md).
- `packages/` — gitignored manual-drop area for third-party
  Python source trees that the workspace's projects import on the
  device.  See [`packages/README.md`](packages/README.md).
- `libraries/` — *not present by default.*  `python run.py new
  --library <name>` materialises it the first time you scaffold a
  full chumicro-style library package.
- `_workspace_template/` — tool-owned template sources for files
  this repo customises.  `setup` materializes any missing destination
  at the workspace root; `update` refreshes these sources from
  upstream.  Empty by default — the canonical `devices.yml` and
  `workspace.yml` starters live in the `chumicro-workspace` package's
  payloads.  Add files here only if you need to override the workbench
  defaults for a forked workspace template.

## Worked example: `example_sensor`

The shipped `projects/example_sensor/` exercises the full ChuMicro
runtime stack (wifi + sockets + mqtt + kvstore + workspace).  Boot
to first heartbeat on a plugged-in board:

```bash
# 1. Bootstrap the workspace (one-time, after clone)
python3 run.py setup

# 2. Tell the workspace about your board
python run.py add-device my-board --address /dev/cu.usbmodem1101 --runtime micropython

# 3. Fill in your wifi credentials (edit workspace.yml directly —
#    `setup` materialised it from the chumicro-workspace package's
#    canonical starter; the file is gitignored, so just open and edit)
$EDITOR workspace.yml  # set defaults.wifi.{ssid,password} to your AP

# 4. Point the sensor at your AP + a broker (one line each)
$EDITOR projects/example_sensor/config.toml
#   [wifi]    ssid = "YourNetwork"
#   [mqtt]    broker = "broker.hivemq.com"   # public test broker; swap for your own
#   [sensor]  topic  = "chumicro/example/temperature"

# 5. (Optional) Sanity-check the merged config before deploying.
#    Prints the dict that ends up on the device — handy when an
#    overlay layer didn't deep-merge how you expected.
python run.py dump-config example_sensor

# 6. Install the chumicro libraries onto the board.  AST-walks the
#    project for `chumicro_<name>` imports, then shells out to
#    `circup install ...` (CircuitPython) or `mpremote ... mip
#    install github:ChuMicro/ChuMicro-Bundle/...` (MicroPython) per
#    library.  Skip this step in chumicro-dev mode — the libraries
#    ship via `library_sources:` instead (see the collapsible note
#    below).  Add `--experimental` to install from
#    `ChuMicro-Bundle-Experimental`; add `--dry-run` to preview the
#    exact commands without executing.
python run.py install-libraries example_sensor

# 7. Deploy + watch
python run.py deploy example_sensor

# Or, if you want to follow the REPL output afterward:
python run.py repl
```

Subscribe to the topic from any MQTT client (`mosquitto_sub -h
broker.hivemq.com -t 'chumicro/example/temperature'`) and you should
see one JSON message every 5 seconds carrying the boot counter, the
on-board temperature reading, and a sequence number.  Reset the
board and the boot counter increments — `chumicro-kvstore` persisted
it across resets.

`projects/example_sensor/app.py` is short on purpose — it's the
canonical reference for how to wire `WifiService` + `MQTTClient` +
`KVStore` into a tick-shaped `Runner`.  Copy + tweak rather than
starting from scratch.

<details>
<summary>ChuMicro-dev mode — for co-developing chumicro libraries alongside the workspace</summary>

Co-developing chumicro libraries / `chumicro-workspace` from a
sibling chumicro source checkout (or a fork)?  Drop a
`chumicro-dev.toml` next to `run.py` with:

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

In dev mode, `setup` *also* writes a managed `library_sources:` block
into `workspace.yml` mapping every chumicro library it finds in the
sibling checkout to its `src/` directory.  `deploy --import-graph`
(and the `--boot-shim --import-graph` composition) reads that block
to ship the on-device libraries directly from the local checkout —
no `circup` / `mip` round-trip and no `install-libraries` step.
Pulling new chumicro libraries into the sibling checkout is a
re-run-`setup` away.

In regular mode (no `chumicro-dev.toml`), the `install-libraries`
step in the worked example above fetches each library from
`ChuMicro-Bundle` (stable) or `ChuMicro-Bundle-Experimental` and
installs it onto the board.  Manual fallback for air-gapped /
custom-registry rigs:

```bash
# CircuitPython — bundle-add once, then install per project
circup bundle-add ChuMicro/ChuMicro-Bundle
circup install chumicro-config chumicro-kvstore chumicro-mqtt \
               chumicro-msgpack chumicro-runner chumicro-sockets \
               chumicro-timing chumicro-wifi

# MicroPython — one mip install per library
mpremote connect /dev/cu.usbmodem1101 mip install \
    github:ChuMicro/ChuMicro-Bundle/chumicro_config
mpremote connect /dev/cu.usbmodem1101 mip install \
    github:ChuMicro/ChuMicro-Bundle/chumicro_kvstore
# ... repeat per library
```

`python run.py install-libraries <project> --dry-run` prints the
exact commands the workspace would have run — paste-into-elsewhere
when this host can't reach the bundle URL directly.

</details>
