# Changelog

Notable changes to the workspace template.  Versions are git tags;
pin a workspace to one with `python3 run.py update --ref v<version>`.

## v0.1.0 — 2026-07-18

First tagged release.  The template as of this tag:

- Clone-and-go workspace layout: `run.py` self-bootstrapping
  dispatcher, `projects/` (with `_template/` scaffold source and the
  `example_sensor` reference project), read-only `examples/`
  (hello_world, wifi_only, periodic_get, telemetry_publisher,
  two_board_handshake), `shared/`, `packages/`, committed
  `quality.toml`, and gitignored `workspace.yml` / `secrets.toml` /
  `devices.yml` materialized by `setup`.
- Agent support: `AGENTS.md` conventions plus four skills under
  `.github/skills/` — add-new-project, register-board,
  install-firmware, deploy-and-debug.
- Tooling pinned to the experimental release channel while the first
  stable wave publishes (`requirements.txt` carries the rationale and
  the flip-at-stable note).
- Host-side testing: workspace smoke tests cover every project and
  every shipped example (nested projects included), `conftest.py`
  mirrors the device import search path (`shared/` →
  `libraries/*/src` → `packages/`), and `example_sensor` ships both
  per-project unit tests and a board-routed functional test —
  `python3 run.py test projects/<name>/functional_tests` ships the
  tree to a registered board and runs it there (sweeps leave
  functional trees alone).  Requires the chumicro tooling wave that
  carries project-tree routing; `requirements.txt` pins it.
- Fixed in the run-up to this tag: dev-mode `setup` installs the
  sibling checkout's third-party requirements (fresh dev-mode venvs
  bootstrap cleanly), `run.py lint` survives `library add` (acquired
  library trees are excluded from the workspace ruff sweep), dead
  links and stale channel/behavior claims corrected across the docs,
  one `python3 run.py` spelling everywhere, and an MIT license.
