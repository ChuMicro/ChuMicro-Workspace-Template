"""Hello-world thing — proves the deploy chain works end-to-end.

No wifi, no sensors, no third-party imports — just a print loop.
Useful as your *first* deploy on a freshly-onboarded board: when
``run`` reaches the ``hello`` print, you know

* the host pushed code to the device;
* `workspace_runtime.boot()` imported `things.<name>.app` cleanly;
* ``run()`` was called.

Anything that breaks before that line is a deploy / boot-shim
problem; anything after is your code.

Scaffold a copy with ``python run.py new <name> --from examples/hello_world``,
then ``python run.py deploy <name>``.
"""

from chumicro_timing import ticks_add, ticks_diff, ticks_ms


def run() -> None:
    """Print a heartbeat once per second for ten seconds, then exit."""
    print("hello from a ChuMicro thing")
    next_tick = ticks_ms()
    for index in range(10):
        # Wraparound-safe wait — never `time.sleep` in real things;
        # see the `chumicro-timing` library docs for why.
        next_tick = ticks_add(next_tick, 1000)
        while ticks_diff(ticks_ms(), next_tick) < 0:
            pass
        print(f"  tick {index + 1}/10")
    print("hello_world: done")
