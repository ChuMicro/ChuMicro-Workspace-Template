# Working in this workspace

Welcome.  This file is for **you**, the human who just cloned the
template — and for any AI coding agent helping you.

The [README](README.md) is the 30-second quickstart.  This file is
the "now what?" guide: workflows, debugging, where to look up help,
and how to collaborate with an agent without losing your bearings.

If you're an agent: start with [AGENTS.md](AGENTS.md) — it's the
distilled rules + commands for editing this workspace.  Skim this
file too so you understand the human's mental model.

## What this workspace is

A ChuMicro project workspace ships as a Git repo you clone (this
template) and edit in place.  Conceptually it has three pieces:

- **`projects/<name>/`** — your applications.  Each project is a
  directory with an `app.py` (defining `def run(): ...`) plus a
  `config.toml` for its knobs.  One project → one deployable program.
- **`devices.yml`** — your board registry.  One entry per
  physical board you deploy to.  Tool-managed by `add-device` /
  `rename` / `probe` so comments + key order survive every edit.
- **`run.py`** — the workspace dispatcher.  Every command you run
  goes through it: `python run.py setup`, `python run.py deploy`,
  `python run.py repl`, etc.  It bootstraps a `.venv` on first
  call and re-execs into it after that.

You write code in `projects/`.  The tooling owns deploys, REPL,
firmware flashing, config merging, and the boot shim that fires
your `run()` on the device.

## Day one — setup

```bash
git clone --depth 1 https://github.com/ChuMicro/ChuMicro-Workspace-Template my-workspace
cd my-workspace
rm -rf .git && git init       # start your own history
python3 run.py setup          # creates .venv, materializes secrets.yml, installs chumicro-workspace
```

`setup` is idempotent — re-run any time after pulling template
updates.  It won't overwrite anything you've edited.

If you're co-developing the underlying ChuMicro libraries from a
sibling clone, see the README's "ChuMicro-dev mode" section.

## Day-to-day — making and shipping projects

A typical session has four moves:

```bash
# 1. Register a board (once per physical board).  Use `bootstrap`
#    if you want the wizard to walk pick-port → probe → register
#    in one command.
python run.py add-device my-board --address /dev/cu.usbmodem1101 --runtime micropython

# 2. Scaffold a new project
python run.py new my_sensor    # creates projects/my_sensor/ from projects/_template/

# 3. Edit projects/my_sensor/{app.py, config.toml}, plus secrets.yml for credentials.

# 4. Deploy + watch — one command via `repl <project>` (deploys, then
#    tails for 30s).  For longer windows pass --tail SECONDS.
python run.py repl my_sensor
```

`python run.py status` (or the stricter `doctor`) is a useful
between-step sanity check — surfaces common mistakes before deploy
(`secrets.yml` still carrying `replace-me`, `app.py` missing a
`run()` definition, an unresolved `!secret` reference).

The shipped `projects/example_sensor/` is the canonical reference —
it wires `chumicro-wifi` + `chumicro-mqtt` + `chumicro-kvstore`
into a tick-shaped `Runner`.  Copy + tweak rather than starting
from scratch.

### Naming projects

Project directory names must be valid Python identifiers — letters,
digits, underscores; no hyphens, no dots, no leading digit.  The
runtime imports `projects.<your-name>.app`, so a hyphen breaks
deploy.  `python run.py new` checks this up-front and fails fast
with a clear message.

Nested layouts are first-class.  Slash- or dotted-form names land
under a parallel namespace tree:

```bash
python run.py new garage/sensors/door_open
python run.py new garage.sensors.door_open      # dotted form, same effect
```

Each path segment is validated independently against the same
identifier rules, and intermediate namespace directories
(`projects/garage/`, `projects/garage/sensors/`) are auto-created with
empty `__init__.py` markers.  `python run.py projects` shows the tree
(`--flat` switches to one-line-per-project slash-form).

### Scaffolding from an example

Instead of starting from the blank `projects/_template/`, scaffold
from any directory under `examples/`:

```bash
python run.py new garage/heater --from examples/wifi_only
```

That copies `examples/wifi_only/`'s tree into
`projects/garage/heater/`.  The example folder itself is read-only
(tool-owned, refreshed on `update`); your edits live under `projects/`.

### Workspace health checks

Two commands surface common pre-deploy mistakes:

```bash
python run.py status     # one-line-per-check snapshot
python run.py doctor     # stricter — adds AST scan for run() + !secret resolution
```

`status` catches un-edited `secrets.yml` placeholders, missing
`devices.yml`, malformed `workspace.yml`.  `doctor` adds Python
version, per-project `app.py` AST scan ("did you forget the `def run()`?"),
and a config-merge dry-run that rejects unresolved `!secret` references.

`deploy` runs the same fast checks `status` does as a pre-flight gate —
ERROR-level findings (malformed YAML files) abort before sending bytes
to the device; WARN-level findings (placeholder secrets, no devices
registered) print but proceed.  Pass `deploy --skip-health-check`
when you've already validated the workspace state externally and want
to skip the gate (CI flows, scripted runs).

### How config flows from your edits to the device

Every project receives a runtime config at boot.  That config is the
merge of three host-side sources, with secret references resolved at
deploy time:

```
secrets.yml                workspace.yml              projects/<name>/config.toml
   (host)                     (host)                          (host)
      │                          │                              │
      └──────────────┬───────────┴──────────────────────────────┘
                     ▼
                 deep merge                     (project wins over workspace defaults)
                     │
                     ▼
                 resolve "!secret <name>"       (replaces with secrets.yml value)
                     │
                     ▼
                 packb (msgpack)                (single source of truth on the wire)
                     │
                     ▼
       /runtime_config.msgpack on device
                     │
                     ▼
              chumicro_config.runtime           (READS the msgpack on the device)
```

Use `python run.py dump-config <project>` to print the merged dict
your project would receive without actually deploying — useful when
debugging which config section a key landed in or whether a `!secret`
resolved to what you expected.

### Quality gate

`python run.py preflight` runs `lint` then `test` as a single sanity
gate (chumicro mono-repo's preflight shape, scaled down for workspaces
without CI).  Set `quality:` knobs in `workspace.yml` to tune:

```yaml
quality:
  lint:
    enabled: true              # set to false to skip ruff
    select: [E, F, I]          # ruff rule set
  coverage_threshold: 70       # passed to pytest as --cov-fail-under
```

Both `lint` and `test` are also runnable on their own.

### Library-shaped code — `libs/` vs `libraries/`

Both hold code your projects can `import`.  Pick by *weight*:

| Want to ship… | Drop it under | Imports look like | Notes |
|---|---|---|---|
| A 50-line helper your projects share | `libs/foo.py` | `from libs.foo import bar` | No tests, no version, no scaffolding. |
| A full chumicro-style library you might publish someday | `libraries/<name>/` (via `python run.py new --library <name>`) | `import <name>` | Gets `src/`, `tests/`, `docs/`, `examples/`, `pyproject.toml`, `VERSION`. |
| A third-party package | `packages/` (via `sync`) | `import <name>` | Gitignored mirror cache. |

The import-graph search path resolves explicit `library_sources:`
overrides → `libs/` → every `libraries/<name>/src/` (auto-discovered)
→ `packages/`.  So a library scaffolded with `new --library` is
importable as `import <name>` from any project without further wiring.

`python run.py new --workbench <name>` is the host-only sibling — it
scaffolds the same shape but with a workbench-flavoured pyproject (CLI
entry point, no cross-runtime concerns) under `workbench/<name>/`.
Use this for tools you'd like to drive from the laptop alongside the
chumicro workbench packages.

### Device modes — RAM vs. flash

Every deploy chooses a mode:

- **RAM mode** (`deploy_mode: ram`, the default) — the device
  executes from host-mounted source.  Fast iteration, no flash
  wear, but state doesn't persist across resets.  Best for
  single-library experiments and testing one project at a time.
- **Flash mode** (`deploy_mode: flash`) — files actually land on
  the device's flash.  State persists, the device boots
  standalone, but each deploy writes to flash.  Required for
  multi-library compositions, persistent counters, OTA updates,
  anything that depends on filesystem state surviving a reset.

Set the default in `devices.yml` `defaults.deploy_mode` or
override per-board with the `deploy_mode:` field on a device
entry.

## Debugging — what to do when a deploy doesn't work

The `chumicro-deploy` recovery layer classifies most failure
modes into a precise message that points at a fix.  When deploy
fails, read the output before guessing — the message usually
*tells* you what to do (mount the CIRCUITPY drive, swap the
cable, install firmware, plug in the right board id, etc.).

Common patterns:

| Symptom | Likely cause | First project to try |
|---|---|---|
| `port not found` / `failed to access` | board unplugged or claimed by another process | `python run.py discover` to list what's actually visible |
| `no firmware detected` | board is in bootloader / fresh-flash state | `python run.py install-firmware --method uf2` (or `esptool` on ESP32) |
| `ImportError: no module named ...` on boot | missing library not yet on flash | check the deploy log — the error names the missing module |
| messages stop after first publish | RAM mode against a project that needs persistent state | switch to flash mode (per-device override in `devices.yml`) |
| TLS connection rejected | clock unset; cert validity-period check fails | NTP-sync after wifi connect, or backdate the cert's `notBefore` for development |

The skill files under `.github/skills/` (loaded by your AI agent
on demand) cover each of these in more detail.

## Working with an AI agent

The agent's instruction file is [AGENTS.md](AGENTS.md).  It
describes file ownership rules (so the agent doesn't clobber
files `update` will refresh) and the canonical workflows.

Three patterns that work well:

1. **Bring the agent into a real session, not a planning one.**
   "Help me deploy `my_sensor` to the Pi Pico W and watch the
   output" gets you concrete diagnostics; "design a wifi
   architecture" gets you analysis paralysis.

2. **Hand the agent the failure output, not your interpretation.**
   The deploy + REPL transcripts contain the precise error
   messages our recovery layer worked hard to produce; an agent
   can usually map them straight to a fix.

3. **Ask the agent to load the right skill.**  When the agent
   sees a file under `.github/skills/<topic>/SKILL.md` whose
   description matches your task, it'll load that file's
   procedure.  You can also reference one explicitly: "use the
   `deploy-and-debug` skill."

The agent can edit files freely under `projects/<your-name>/`,
`libs/`, `workspace.yml`, `devices.yml`, and `secrets.yml`.  It
should *not* edit `run.py`, `AGENTS.md`, `CONTRIBUTING.md`,
`pyproject.toml`, `projects/_template/`, `_templates/`, or anything
under `.github/` — those are tool-owned and `python run.py
update` will rewrite them next time you pull.

## Updating the workspace tooling

```bash
python run.py update              # pull tool-owned file refreshes from upstream
python run.py update --ref v0.5   # pin to a specific template version
```

`update` only touches tool-owned files (the `run.py`,
`AGENTS.md`, `CONTRIBUTING.md`, `pyproject.toml`, the
`projects/_template/` skeleton, `_templates/` template sources, and
the `.github/skills/` agent-skill index).  Your `projects/`,
`devices.yml`, `secrets.yml`, `workspace.yml`, `libs/`, and
`packages/` are never touched.

## Where to look up help

- **`AGENTS.md`** — concise rules for editing the workspace
  (file ownership, day-to-day commands, gotchas).
- **`.github/skills/<topic>/SKILL.md`** — agent-loadable
  procedures for the most common workflows.  Browse them as
  reference even without an agent.
- **`projects/example_sensor/`** — the worked example.  Read it
  when you're not sure how to wire a service into a `Runner`.
- **The chumicro-workspace
  [guide](https://github.com/ChuMicro/ChuMicro/blob/main/workbench/workspace/docs/guide.md)** —
  the upstream reference for the underlying CLI commands and
  Python API.
- **The chumicro library
  [docs](https://github.com/ChuMicro/ChuMicro/tree/main/libraries)** —
  per-library guides for `chumicro-wifi`, `chumicro-mqtt`, etc.
- **Issues** — file at the chumicro mono-repo for tooling
  issues, or in your own workspace repo for project-specific bugs.

## Project rules — quick reference

These match the rules in `AGENTS.md`; calling them out for
humans too.

- Project names are Python identifiers — no hyphens, no dots, no
  leading digits.
- Credentials live in `secrets.yml` (gitignored), referenced
  from any `config.toml` via `!secret <name>`.
- `devices.yml` is gitignored.  Re-run `add-device` on a fresh
  clone or copy your local `devices.yml` over by hand.
- On CircuitPython, do NOT add `CIRCUITPY_WIFI_SSID` to
  `settings.toml` — `chumicro-wifi` owns the radio and
  CircuitPython's auto-connect supervisor will fight it.
- Run `python run.py test` (forwards to `pytest`) before
  shipping.  Tests live under `projects/<name>/tests/` if you want
  per-project coverage.
- For network-attached projects (anything using `chumicro-mqtt` or
  similar), the main loop is a tight `while not
  _SHUTDOWN_REQUESTED: runner.tick()` — do *not* add
  `time.sleep_ms()` inside the loop.  Tick latency matters for
  packet timing.

## When something feels wrong

Sanity-check ladder:

1. Is the workspace itself well-formed?  `python run.py status`
   (or `doctor` for the strict version).
2. Is the board actually plugged in?  `python run.py discover`.
3. Is the right runtime registered for that port?  `python run.py
   devices` to inspect the registry.
4. Is the deploy actually reaching the device?  `python run.py
   repl` and look for the boot banner.
5. Is the failure in your code or in the chumicro stack?  Read
   the traceback's first line — `projects/<name>/app.py` is yours;
   anything under `chumicro_*` is the library stack and the fix
   probably belongs upstream (file an issue).  Failed deploys also
   carry a `--- hints ---` block under the traceback when the
   error matches a known pattern (missing `!secret`, library not
   installed, etc.).

Welcome aboard.  Have fun.
