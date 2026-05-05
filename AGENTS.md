# AGENTS.md — workspace conventions

This file is for AI coding agents working inside this workspace.
Tool-owned: `python run.py update` will rewrite it.  Skim
[CONTRIBUTING.md](CONTRIBUTING.md) for the human-side framing.

## What this is

A ChuMicro project workspace.  `projects/` are individual deployable
apps, `devices.yml` registers boards, and `python run.py <cmd>`
dispatches to the `chumicro-workspace` host CLI.  See the package's
[hosted docs](https://chumicro.github.io/ChuMicro/workspace/stable/)
for the workflow primer.

## Day-to-day commands

| Command | Purpose |
|---|---|
| `python3 run.py setup` | One-time: create `.venv`, install deps, materialize the workbench-owned `devices.yml` + `workspace.local.yml` starters and any files under `_workspace_template/`. |
| `python run.py bootstrap [--with-demo]` | End-to-end onboarding wizard: pick a port → probe → register → optionally deploy demo.  Skip prompts with `--port` / `--device-id`. |
| `python run.py status` | Workspace health snapshot — `workspace.yml` validity, `devices.yml` count, `workspace.local.yml` overlay status, projects-tree summary.  Exit 1 only on errors. |
| `python run.py doctor` | Strict sibling of `status` — adds Python ≥3.11 check and an AST scan for `def run`. |
| `python run.py new <name>` | Scaffold a new project under `projects/<name>/`.  Name may be nested (`upstairs/bedroom_sensor` or dotted `upstairs.bedroom_sensor`); each segment must be a valid Python identifier. |
| `python run.py new <name> --from <path>` | Scaffold from an existing tree instead of `projects/_template/`, e.g. `--from examples/wifi_only`. |
| `python run.py new <name> --library [--into <dir>]` | Scaffold a chumicro-style library tree (full `src/`, `tests/`, `docs/`, `examples/` layout).  Defaults to `<workspace>/libraries/<name>/`. |
| `python run.py projects` | Tree view of every project.  `--flat` for one-line-per-project slash-form output. |
| `python run.py discover` | List serial ports the host can see. |
| `python run.py add-device <id> --address <port> [--runtime <cp\|mp>]` | Probe + register a board.  Runtime auto-detected when omitted. |
| `python run.py probe` | Read `sys.implementation` from the default device. |
| `python run.py devices` | Print every entry in `devices.yml`. |
| `python run.py deploy <project>` | Ship a project to the default board.  Name accepts bare / slash / dotted; bare names disambiguate against the live tree. |
| `python run.py deploy <project> --device-id <id>` | Override the default device. |
| `python run.py deploy <project> --dry-run` | Print the file map without writing — useful for "did the overlay merge flatten?" debugging. |
| `python run.py deploy <project> --all-devices` | Loop over every device in `devices.yml`.  Failures don't abort the loop; exit code reflects whether any failed. |
| `python run.py deploy --all-projects` | Walk `workspace.yml`'s `deploy_targets:` mapping and deploy each project to its declared device(s).  Mutually exclusive with positional names / `--device` / `--runtime` / `--all-devices`. |
| `python run.py demo` | Deploy a built-in print-loop payload to the default board (no wifi, ~5s). |
| `python run.py repl` | Open an interactive REPL on the board.  Defaults to **line mode** in a TTY: host-side line editor with persistent per-device history, `:edit` opens `$EDITOR` with the recent buffer pre-seeded, `:save NAME` / `:load NAME` / `:snippets` round-trip reusable code, Tab completes against keywords + the on-device namespace (use `:rescan` after a new `import`).  Add `--mode passthrough` for the byte-by-byte mpremote-style flow (raw REPL framing, paste mode). |
| `python run.py repl --tail 30` | Stream output for 30 seconds (good for post-deploy follow). |
| `python run.py repl <project>` | Deploy a project then tail (default 30s window).  `--tail SECONDS` overrides. |
| `python run.py rename --project OLD NEW` | Rename a project dir.  Both sides accept slash/dotted paths; intermediate namespace dirs auto-created. |
| `python run.py install-firmware --method uf2` | Auto-derived firmware download + flash. |
| `python run.py upgrade-firmware --method esptool` | Same handler, conventionally for re-flashes. |
| `python run.py test [-- pytest-args]` | Run pytest across `tests/` + `projects/*/tests/`.  `workspace.yml`'s `quality.coverage_threshold` (when set) prepends `--cov-fail-under=N`. |
| `python run.py lint` | Run `ruff check` across the workspace.  `workspace.yml`'s `quality.lint.enabled = false` skips with a hint; `quality.lint.select` prepends `--select <list>`. |
| `python run.py update` | Pull tool-owned file refreshes from the canonical workspace template. |

## File ownership

| Path | Who edits | What `update` does |
|---|---|---|
| `projects/<your-name>/` | YOU | leaves alone |
| `devices.yml` | tool (via `add-device` / `rename` / `probe`) | leaves alone |
| `workspace.local.yml` | YOU (gitignored credential overlay; materialized by `setup` from the chumicro-workspace package's canonical starter) | leaves alone |
| `workspace.yml` | YOU | leaves alone |
| `shared/` | YOU (drop a `.py`, import as `from shared.foo import bar`) | leaves alone |
| `packages/` | YOU (manual-drop area; gitignored) | leaves alone |
| `libraries/` | YOU (lazy-created by `new --library`; absent by default) | leaves alone |
| `run.py` | NEVER edit | rewrites |
| `AGENTS.md` | NEVER edit | rewrites |
| `CONTRIBUTING.md` | NEVER edit | rewrites |
| `pyproject.toml` | NEVER edit | rewrites |
| `_workspace_template/` | NEVER edit | rewrites |
| `projects/_template/` | NEVER edit | rewrites |
| `.github/skills/` | NEVER edit | rewrites |
| `examples/` | NEVER edit | rewrites |

If the user asks for changes the tool-owned files would need, propose an upstream PR to the [`ChuMicro-Workspace-Template`](https://github.com/ChuMicro/ChuMicro-Workspace-Template) repo rather than editing in place.

## Skills index

Procedural knowledge for common workflows lives under `.github/skills/`.  Read the relevant skill BEFORE the task — they're tight checklists with the exact commands.

| Skill | When to read it |
|---|---|
| `add-new-project` | The user wants to create a new app (`new <name>`, fill config, first deploy). |
| `register-board` | First-time board onboarding, or when `add-device` errors out. |
| `deploy-and-debug` | A deploy failed, output is unclear, or the user wants to follow REPL after deploy. |

## Rules of thumb

- **Projects must export `def run(): ...` from `app.py`** (or define `code.py` / `main.py` directly).  The `workspace_runtime` boot module imports `projects.<name>.app` and calls `run()`.
- **Project names are Python identifiers.**  `python run.py new` rejects hyphens / dots / leading-digits / Python-keywords / leading-underscores up-front.  If the user typed a hyphenated name, suggest the underscore version.
- **Credentials always go in `workspace.local.yml`** under `defaults.<section>.<key>` (same shape as `workspace.yml`; deep-merged on top).  Never inline a real password into `config.toml` or `workspace.yml` — both are committed.
- **CP boards: do NOT add `CIRCUITPY_WIFI_SSID` to `settings.toml`.**  `chumicro-wifi` owns the radio; CircuitPython's auto-connect supervisor will compete with it.
- **Tight tick loop is the contract for networked projects.**  Don't suggest adding `time.sleep_ms()` inside the `while True: runner.tick()` body — it loses MQTT keepalive timing and stalls inbound bytes.  If the user is concerned about CPU usage, the right answer is a different runner shape (deep-sleep + scheduled wake), not a sleep call.
- **Flash mode is the default; RAM mode is opt-in for single-library experiments.**  `chumicro-deploy` ships with `deploy_mode: flash` as the default for project deploys, examples, and most functional tests — this matches how production deploys behave on the device.  RAM mode (`deploy_mode: ram`) is only useful for quick single-library iteration where state-doesn't-persist-across-resets is actually fine.  Heavier libraries (`chumicro-mqtt` / `chumicro-requests` / `chumicro-http-server` / `chumicro-websockets`) declare `[tool.chumicro] requires_flash = true` in their pyproject; if a project imports any of them and the device is in `ram` mode, the deployer auto-switches to flash and prints why.  Surface this when the user reports "messages stop after first publish" or `OSError: [Errno 2] ENOENT` on `/runtime_config.msgpack`.
- **Run `python run.py test` before reporting work as done** when the user has tests under `projects/<name>/tests/` or at the workspace root.

## Tests + lint

| Path | What lives there | Run with |
|---|---|---|
| `tests/` | Workspace-level smoke tests (e.g. "every project exposes `run()`"). | `python run.py test tests` |
| `projects/<name>/tests/` | Per-project host-side unit tests.  Scaffolded into every new project by `python run.py new <name>`. | `python run.py test projects/<name>/tests` |
| `projects/<name>/functional_tests/` | Real-network / real-hardware acceptance.  The `chumicro-pytest-device` plugin routes these to a connected board.  Tests skip cleanly when no board is configured. | `python run.py test projects/<name>/functional_tests` |

`python run.py test` with no args runs **everything** under `tests/` + `projects/`.  Functional tests deselect themselves on a sweep with no `functional_tests` path argument — only fire when targeted.

`python run.py lint` runs `ruff check` with the workspace's `[tool.ruff]` config (line-length 100, imports sorted, relative-import ban, pyflakes / bugbear / pyupgrade).  Tests + functional tests get the relative-import rule relaxed.  Set `quality.lint.enabled: false` in `workspace.yml` to skip lint without uninstalling ruff.  Set `quality.lint.select: ["E", "F", "I"]` to override the rule list per-workspace.

Coverage gate: `[tool.coverage.report] fail_under = 85` in `pyproject.toml` — the per-package floor.  Override per-workspace via `quality.coverage_threshold: <N>` in `workspace.yml` (forwarded to pytest as `--cov-fail-under`); user CLI args after `--` win on conflict.

## Working in a fresh workspace

When you join a session in a workspace that's been freshly cloned:

1. Read `workspace.yml` to see the merged-config defaults.
2. Read `devices.yml` to see what boards are registered.  If empty, `add-device` is the first move.
3. Read `projects/<name>/config.toml` for the project the user is working on.
4. If the user is hitting an error, read the full deploy / REPL output before suggesting fixes — the recovery layer's messages are precise.

## Project rules — non-negotiable

- **Don't fabricate.**  Read code / docs / output instead of guessing.  If you can't verify, say so.
- **Don't edit tool-owned files.**  See the table above.
- **Don't bypass `run.py`.**  All commands go through it (so the workspace's `.venv` and config resolution stay consistent).
- **Don't commit `.scratch/`, `.venv/`, `workspace.local.yml`, or `devices.yml`.**  All gitignored.
- **No emojis in files unless the user asks.**

## Common pitfalls

- Editing `workspace.local.yml.example` — there isn't one.  `workspace.local.yml` is materialized by `setup` from the chumicro-workspace package's canonical starter; just edit it directly.
- Running raw `pytest` — the workspace's pytest config wants `python run.py test` so the venv + paths resolve right.
- Re-running `setup` thinking it'll "fix" something — it's idempotent and won't overwrite anything.  If a project's broken, the fix is in your code, not in setup.
- Trying to debug a TLS handshake without setting the device clock — TLS validity-period checks fail with "validity starts in the future" on a fresh board.  NTP after wifi-up, or backdate the cert's notBefore for development.

## When you finish a unit of work

1. Run `python run.py test` if the user has tests.
2. Show the user the diff (or the file paths you touched).
3. If you ran a deploy, show the relevant REPL output.
4. Note anything you noticed but didn't change (out-of-scope tweaks the user might want).
