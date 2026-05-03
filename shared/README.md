# shared/

User-authored helper modules shared between projects in this workspace.

## Use it like this

Drop a Python file here:

    shared/sensor_helpers.py

Then import it from any project:

    from shared.sensor_helpers import calibrate

No `__init__.py` required — implicit namespace packages (Python 3.3+) handle the rest.  Just drop the file.

## When to use shared/ (vs libraries/)

| Use shared/ when... | Use libraries/ when... |
|---|---|
| You wrote it yourself | You wrote it yourself, *and* it deserves its own version + tests + docs |
| Multiple projects in this workspace need it | Multiple workspaces (or eventually PyPI) need it |
| It's small enough that a single file is fine | It's a real library — `pyproject.toml`, `src/`, `tests/` |
| You don't want the ceremony of a full package | You want to publish or distribute it later |

For full chumicro-style library packages: `python run.py new --library <name>` — that command creates `libraries/` the first time it runs.
