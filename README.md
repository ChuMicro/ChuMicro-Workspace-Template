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
- `devices.yml` — registered boards.  Edit via `add-device` or by hand.
- `workspace.yml` — defaults every thing inherits.
- `secrets.yml` — gitignored credentials, materialized from
  `_templates/secrets.yml` by `setup`.  Reference via
  `!secret <name>`.
- `libs/` — shared user code.  Things `import` from here.
- `packages/` — gitignored, mirror-cached external libs.
- `_templates/` — tool-owned template sources for files like
  `secrets.yml`.  `setup` materializes them; `update` refreshes them
  from upstream.
