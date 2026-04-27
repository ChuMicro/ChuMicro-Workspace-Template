# AGENTS.md — workspace conventions

This file is for AI coding agents working inside this workspace.
Tool-owned: `python run.py update` will rewrite it.  Skim
[CONTRIBUTING.md](CONTRIBUTING.md) for the human-side framing.

## What this is

A ChuMicro project workspace.  `things/` are individual deployable
apps, `devices.yml` registers boards, and `python run.py <cmd>`
dispatches to the `chumicro-workspace` host CLI.  See the package's
[guide](https://github.com/ChuMicro/ChuMicro/blob/main/workbench/workspace/docs/guide.md)
for the workflow primer.

## Day-to-day commands

| Command | Purpose |
|---|---|
| `python3 run.py setup` | One-time: create `.venv`, install deps, materialize `_templates/`. |
| `python run.py new <name>` | Scaffold a new thing under `things/<name>/`.  Name may be nested (`upstairs/bedroom_sensor` or dotted `upstairs.bedroom_sensor`); each segment must be a valid Python identifier. |
| `python run.py new <name> --from <path>` | Scaffold from an existing tree instead of `things/_template/`, e.g. `--from examples/wifi_only`. |
| `python run.py things` | Tree view of every thing.  `--flat` for one-line-per-thing slash-form output. |
| `python run.py discover` | List serial ports the host can see. |
| `python run.py add-device <id> --address <port> --runtime <cp\|mp>` | Probe + register a board. |
| `python run.py probe` | Read `sys.implementation` from the default device. |
| `python run.py devices` | Print every entry in `devices.yml`. |
| `python run.py deploy <thing>` | Ship a thing to the default board. |
| `python run.py deploy <thing> --device-id <id>` | Override the default. |
| `python run.py repl` | Open an interactive REPL on the board. |
| `python run.py repl --tail 30` | Stream output for 30 seconds (good for post-deploy follow). |
| `python run.py install-firmware --method uf2` | Auto-derived firmware download + flash. |
| `python run.py upgrade-firmware --method esptool` | Same handler, conventionally for re-flashes. |
| `python run.py test [-- pytest-args]` | Run pytest across `tests/` + `things/*/tests/`. |
| `python run.py lint` | Run `ruff check` across the workspace.  Same config the chumicro mono-repo uses. |
| `python run.py update` | Pull tool-owned file refreshes from the canonical workspace template. |

## File ownership

| Path | Who edits | What `update` does |
|---|---|---|
| `things/<your-name>/` | YOU | leaves alone |
| `devices.yml` | tool (via `add-device` / `rename` / `probe`) | leaves alone |
| `secrets.yml` | YOU (gitignored, materialized from `_templates/secrets.yml` by `setup`) | leaves alone |
| `workspace.yml` | YOU | leaves alone |
| `libs/` | YOU | leaves alone |
| `packages/` | tool (mirror cache) | leaves alone |
| `run.py` | NEVER edit | rewrites |
| `AGENTS.md` | NEVER edit | rewrites |
| `CONTRIBUTING.md` | NEVER edit | rewrites |
| `pyproject.toml` | NEVER edit | rewrites |
| `_templates/` | NEVER edit | rewrites |
| `things/_template/` | NEVER edit | rewrites |
| `.github/skills/` | NEVER edit | rewrites |
| `examples/` | NEVER edit | rewrites |

If the user asks for changes the tool-owned files would need, propose an upstream PR to the [`ChuMicro-Workspace-Template`](https://github.com/ChuMicro/ChuMicro-Workspace-Template) repo rather than editing in place.

## Skills index

Procedural knowledge for common workflows lives under `.github/skills/`.  Read the relevant skill BEFORE the task — they're tight checklists with the exact commands.

| Skill | When to read it |
|---|---|
| `add-new-thing` | The user wants to create a new app (`new <name>`, fill config, first deploy). |
| `register-board` | First-time board onboarding, or when `add-device` errors out. |
| `deploy-and-debug` | A deploy failed, output is unclear, or the user wants to follow REPL after deploy. |

## Rules of thumb

- **Things must export `def run(): ...` from `app.py`** (or define `code.py` / `main.py` directly).  The `workspace_runtime` boot module imports `things.<name>.app` and calls `run()`.
- **Thing names are Python identifiers.**  `python run.py new` rejects hyphens / dots / leading-digits / Python-keywords / leading-underscores up-front.  If the user typed a hyphenated name, suggest the underscore version.
- **Credentials always go in `secrets.yml`** and are referenced from `config.toml` files via `!secret <name>`.  Never inline a real password into `config.toml`.
- **CP boards: do NOT add `CIRCUITPY_WIFI_SSID` to `settings.toml`.**  `chumicro-wifi` owns the radio; CircuitPython's auto-connect supervisor will compete with it.
- **Tight tick loop is the contract for networked things.**  Don't suggest adding `time.sleep_ms()` inside the `while True: runner.tick()` body — it loses MQTT keepalive timing and stalls inbound bytes.  If the user is concerned about CPU usage, the right answer is a different runner shape (deep-sleep + scheduled wake), not a sleep call.
- **RAM mode is for single-library experiments.**  Anything that composes multiple libraries, depends on persistent state, or talks to a real broker needs flash mode.  Surface this when the user reports "messages stop after first publish" or `OSError: [Errno 2] ENOENT` on `/runtime_config.msgpack`.
- **Run `python run.py test` before reporting work as done** when the user has tests under `things/<name>/tests/` or at the workspace root.

## Tests + lint

| Path | What lives there | Run with |
|---|---|---|
| `tests/` | Workspace-level smoke tests (e.g. "every thing exposes `run()`"). | `python run.py test tests` |
| `things/<name>/tests/` | Per-thing host-side unit tests.  Scaffolded into every new thing by `python run.py new <name>`. | `python run.py test things/<name>/tests` |
| `things/<name>/functional_tests/` | Real-network / real-hardware acceptance.  The `chumicro-pytest-device` plugin routes these to a connected board.  Tests skip cleanly when no board is configured. | `python run.py test things/<name>/functional_tests` |

`python run.py test` with no args runs **everything** under `tests/` + `things/`.  Functional tests deselect themselves on a sweep with no `functional_tests` path argument — only fire when targeted.

`python run.py lint` runs `ruff check` with the same config the chumicro mono-repo uses (line-length 100, imports sorted, relative-import ban, pyflakes / bugbear / pyupgrade).  Tests + functional tests get the relative-import rule relaxed.

Coverage gate: `[tool.coverage.report] fail_under = 85` in `pyproject.toml`.  Lift it for stricter projects or drop it entirely for prototyping.

## Working in a fresh workspace

When you join a session in a workspace that's been freshly cloned:

1. Read `workspace.yml` to see the merged-config defaults.
2. Read `devices.yml` to see what boards are registered.  If empty, `add-device` is the first move.
3. Read `things/<name>/config.toml` for the thing the user is working on.
4. If the user is hitting an error, read the full deploy / REPL output before suggesting fixes — the recovery layer's messages are precise.

## Project rules — non-negotiable

- **Don't fabricate.**  Read code / docs / output instead of guessing.  If you can't verify, say so.
- **Don't edit tool-owned files.**  See the table above.
- **Don't bypass `run.py`.**  All commands go through it (so the workspace's `.venv` and config resolution stay consistent).
- **Don't commit `.scratch/`, `.venv/`, `secrets.yml`, or `devices.yml`.**  All gitignored.
- **No emojis in files unless the user asks.**

## Common pitfalls

- Editing `secrets.yml.example` — there isn't one.  `secrets.yml` is materialized from `_templates/secrets.yml` by `setup`; just edit it directly.
- Running raw `pytest` — the workspace's pytest config wants `python run.py test` so the venv + paths resolve right.
- Re-running `setup` thinking it'll "fix" something — it's idempotent and won't overwrite anything.  If a thing's broken, the fix is in your code, not in setup.
- Trying to debug a TLS handshake without setting the device clock — TLS validity-period checks fail with "validity starts in the future" on a fresh board.  NTP after wifi-up, or backdate the cert's notBefore for development.

## When you finish a unit of work

1. Run `python run.py test` if the user has tests.
2. Show the user the diff (or the file paths you touched).
3. If you ran a deploy, show the relevant REPL output.
4. Note anything you noticed but didn't change (out-of-scope tweaks the user might want).
