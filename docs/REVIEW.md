# Review (November 2026)

r2-astromech was the first iteration of R2's network awareness, written quickly in September 2025
with heavy use of AI coding assistants. It was never finished. The ideas carried on in the
Raspberry Pi droid project and then in **Senchas**, so this repository is not being developed
further. This note records its state honestly: what was fixed when it was tidied up, what is still
wrong, and what changed in the projects that followed.

## Fixed in the November 2026 clean-up

- **Crashes on missing values.** 23 lookups like `device.get('hostname', '').lower()` crashed when a
  scanner had stored `None`, which is the normal case for unknown hostnames (8 of 11 devices in a
  real scan). The training-data pipeline could not run on real data.
- **Wrong scan target.** `scan_director.py` always scanned `192.168.1.0/24` and ignored the config.
  It now uses `discovery.networks.default` from `config/r2_config.yaml`.
- **Modules that could not load.** `services/interfaces.py` used `@dataclass` without importing it;
  `ai/models/phi3_model.py` used `create_event`/`R2Events` without importing them;
  `discovery/utils/__init__.py` imported two modules that were never written.
- **Future breakage.** `asyncio.iscoroutinefunction` (removed in Python 3.16) replaced with
  `inspect.iscoroutinefunction`.
- **Broken demos.** Two imported `modules.…` instead of `src.modules.…`.
- **Published scan data.** Real scan results (IP and MAC addresses, hostnames and open ports of a home
  network) had been committed. They are now git-ignored, and an anonymised example is in
  `data/devices/example/`.
- **Housekeeping.** Demos moved to `examples/`, development notes to `docs/dev-notes/`, a stale
  backup deleted, safe lint fixes applied, MIT licence, first tests and CI.

## Still wrong (left as they are)

These are recorded so nobody mistakes the code for more than it is:

- **The scanners have no tests.** The 14 tests cover the device database, event bus and config only.
- **Device classification doesn't classify.** On the 11 example devices every one comes out as
  `device_type: unknown`. The classifier reads the hostname (`network_scanner.py`, around line 1562)
  and never uses it.
- **Unfinished logic.** Six values are read and never used (ruff F841, ignored in `pyproject.toml`):
  `hostname` and `protocol` in `network_scanner.py`, `services` in `network_analyzer.py`,
  `current_model_info` in `model_manager.py`, `hostname` in `scan_director.py`, and `manufacturer`
  in `examples/demo_r2_tinyllm_standalone.py`.
- **Errors are swallowed.** About 275 `except Exception:` blocks log and carry on, so when something
  breaks a scan just finds fewer devices and nothing says why.
- **The device database** rewrites its whole JSON file on every update, from inside the async event
  loop.
- **Dependencies.** `netifaces` is unmaintained and has no wheels for current Python (`psutil` covers
  the one use); `pygame` has no wheels for Python 3.14; the optional AI stack (torch + transformers)
  is several GB, heavy for a Raspberry Pi.
- **Structure.** Every script adds `src/` to `sys.path` and the code imports itself as `src.…`;
  `scan_director.py` and `src/main.py` overlap; `examples/legacy/` targets an older layout;
  generated training data is committed; `docs/dev-notes/` may no longer match the code.

## What changed in the later projects

- **Asking instead of probing.** r2-astromech scans the network from outside and builds its own
  picture of each device. Senchas has each machine report what it believes and keeps an append-only
  record, so a fault can be traced back to the first point where those beliefs diverged.
- **A durable record.** The JSON device file here became an SQLite record in Senchas.
- **Tests against recorded data.** Senchas replays recorded windows through its rules and compares
  them with accepted results ("golden replays"), which is the testing r2-astromech never had.
- **No site data in shared documents.** Senchas's architecture document is written without
  addresses, hardware identifiers or hostnames; here, real scans ended up in the repository.
- **The discovery module.** `src/modules/discovery/` was copied into the Raspberry Pi droid project,
  which holds the maintained copy. The two were identical until this clean-up; the `None`-safe
  fixes above still need porting there.
