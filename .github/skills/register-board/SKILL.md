---
name: register-board
description: Register a physical board in devices.yml so deploys can target it.  Use when the user has a freshly plugged-in board, an empty devices.yml, or `add-device` has surfaced a port or runtime detection issue.
---

# Register a board

`devices.yml` is the workspace's board registry — one entry per
physical board you deploy to.  `python run.py deploy` can't ship
without at least one matching entry.  This skill walks through
discovery → adding → verification.

## 1. Discover what the host can see

```bash
python run.py discover
```

Lists every serial port the host has noticed.  Output looks like:

```
/dev/cu.usbmodem11401   Pi Pico W
/dev/cu.usbmodem213101  Pi Pico W
/dev/cu.usbmodem211101  Lolin S2 Mini
```

If the user's board isn't here:

- **Cable might be charge-only.**  Try a different USB cable —
  even a known-working data cable is worth re-plugging.
- **Board might be in bootloader / DFU mode.**  Look for
  `RPI-RP2` or similar mass-storage drives; if so, jump to the
  `install-firmware` flow instead.
- **macOS may have just lost the port** after an unclean
  unplug.  Pull and re-seat once; if still missing, check
  `ls /dev/cu.*` for clues.

## 2. Pick an id

Convention: `<board-shape>-<runtime>-<location-or-purpose>`.  Examples:

- `pi-pico-w-mp-back-porch`
- `lolin-s2-cp-kitchen`
- `feather-s3-mp-test`

The id is the user's choice — anything string-shaped works.  But
`python run.py deploy` uses it as the `--device-id`, so memorable
names pay off.

## 3. Add the entry

```bash
python run.py add-device pi-pico-w-mp-back-porch \
    --address /dev/cu.usbmodem213101 \
    --runtime micropython
```

`add-device` does two things:

1. Probes the device over the serial port to capture
   `sys.implementation` (machine + version + UID).  Stores those
   in the `hardware:` block of the entry — this is the
   "did-the-user-swap-boards" guard.
2. Writes the entry into `devices.yml` preserving comments + key
   order via `ruamel.yaml`.

If `--runtime` is wrong (you said `micropython` but the board's
actually CircuitPython), the probe will surface a clear
mismatch — re-run with the correct value.

## 4. Make it the default

If this is the first board you've added, set it as the runtime
default so `python run.py deploy <thing>` doesn't need
`--device-id`:

```bash
python run.py set-default --runtime micropython pi-pico-w-mp-back-porch
```

Or edit `devices.yml` directly:

```yaml
defaults:
  micropython: pi-pico-w-mp-back-porch
  circuitpython: null
  deploy_mode: ram   # or `flash` per device class
```

## 5. Verify

```bash
python run.py probe                       # uses default
python run.py probe --device-id <id>      # specific board
```

Should print the device's runtime + version + machine + UID.  A
good sanity check before the first deploy.

```bash
python run.py devices
```

Shows every entry one-per-line.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `port not found` / `failed to access` | board unplugged or held by another process | check `lsof <address>` (macOS), close any open REPL/terminal sessions, replug |
| `runtime mismatch: probe says micropython, entry says circuitpython` | `--runtime` was wrong on `add-device` | rerun `add-device` with the right value |
| `no implementation marker` from probe | board hasn't booted into a Python REPL — likely in bootloader, freshly flashed without a `boot.py`, or wedged | run `install-firmware` first; if firmware looks OK, soft-reset the board |
| board flips between `usbmodem...1` and `usbmodem...2` between sessions | macOS sometimes reassigns the port for two physically-identical boards | UID-based matching in `chumicro-deploy` auto-corrects; the warning is informational |

## Rules

- **Don't hardcode `circuitpy_drive_path`** unless absolutely
  needed.  `chumicro-deploy` probes
  `microcontroller.cpu.uid` and matches it against
  `boot_out.txt` UID lines on each mounted CIRCUITPY drive, so
  the right drive is auto-selected even when macOS assigns
  `CIRCUITPY 1` / `CIRCUITPY 2` in different orders.
- **Don't edit `devices.yml` while `add-device` is running.**
  The round-trip writer holds an exclusive lock briefly; manual
  edits during that window risk corrupting the file.
- **Re-running `add-device` for an existing id** prompts before
  overwriting the `hardware:` block — that's the "did you swap
  boards?" guard.  Surface the prompt to the user; don't
  auto-accept.
