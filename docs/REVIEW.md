# Code review and plan (November 2026)

An honest assessment of r2-astromech as it stands, and the work planned to bring it up to a
standard I'd be happy to point people at. Items are roughly in priority order. When one is done,
tick it here and mention it in the commit.

## Where it stands

About 15,000 lines of Python in `src/`, written quickly in September 2025 with heavy use of AI
coding assistants. The architecture is reasonable for an experiment: modules behind interfaces
(`src/*/interfaces.py`), an async event bus and a dependency-injection container. The weak points
are the ones you'd expect from fast, assisted development: little verification, errors swallowed
everywhere, and more structure than the features need.

### Fixed in the November 2026 clean-up

- Three import bugs: `services/interfaces.py` used `@dataclass` without importing it;
  `ai/models/phi3_model.py` used `create_event`/`R2Events` without importing them;
  `discovery/utils/__init__.py` imported two modules that were never written.
- 23 lookups like `device.get('hostname', '').lower()` crashed when a scanner had stored `None`.
  That is the normal case for unknown hostnames: 8 of 11 devices in a real scan had none, so the
  training-data pipeline could not run on real data.
- `scan_director.py` always scanned `192.168.1.0/24` and ignored the config. It now uses
  `discovery.networks.default` from `config/r2_config.yaml`.
- `asyncio.iscoroutinefunction` (removed in Python 3.16) replaced with `inspect.iscoroutinefunction`.
- Two demos imported `modules.…` instead of `src.modules.…` and could not start.
- Real scan results (IP and MAC addresses, hostnames, open ports of a home network) were committed.
  They are now git-ignored; an anonymised example is in `data/devices/example/`.
- Tidied: demos moved to `examples/`, development notes to `docs/dev-notes/`, a stale backup of the
  old `main` deleted, safe lint fixes applied, MIT licence added, first tests, CI workflow.

## Correctness

1. **The scanners have no tests.** The 14 tests cover the device database, event bus and config.
   The parsing code (nmap XML, SSDP responses, mDNS records, ARP table) is where the bugs will be,
   and it can be tested offline: record real responses once, anonymise them, keep them in
   `tests/fixtures/`, and test the parsers against them. Start with
   `network_scanner.py` (2,500 lines, the largest file).
2. **Device classification doesn't classify.** Running the training-data example on the 11
   example devices gives `device_type: unknown` for every one. Find out why (the hostname is read
   in the classifier at `network_scanner.py` ~line 1562 and never used) and add tests with known
   devices: printer, NAS, router, phone.
3. **Values read and never used.** These six look like unfinished logic, not dead code (ruff F841,
   currently ignored in `pyproject.toml`; remove the ignore once they're dealt with):
   - `network_scanner.py`: `hostname` in device classification; `protocol` in nmap port parsing
   - `network_analyzer.py`: `services` in the security assessment
   - `model_manager.py`: `current_model_info` in the status report
   - `scan_director.py`: `hostname` in the results display
   - `examples/demo_r2_tinyllm_standalone.py`: `manufacturer` left out of the prompt
4. **Errors are swallowed.** There are about 275 `except Exception:` blocks that log and carry on,
   returning `False`, `None` or `{}`. When something breaks, the scan just finds fewer devices
   and nothing says why. Catch the specific exceptions each block expects (`OSError`,
   `asyncio.TimeoutError`, `json.JSONDecodeError`…) and let the rest surface.
5. **Blocking file writes inside async code.** The device database rewrites its whole JSON file
   on every device update, from inside the event loop (ruff ASYNC230 flags 11 such calls). Fine
   for 11 devices, slow and fragile at a few hundred, and a crash mid-write corrupts the file.
   SQLite (as in Colophon and Kepos) fixes all three.

## Safety and responsible use

6. **Ask before scanning anything other than your own subnet.** `scan_director.py` already has
   code to work out the current network (`_handle_network_selection`). Use it as the default,
   add a `--network` option, and require confirmation for any other range.
7. **Redacted export.** Add a command that writes an anonymised copy of the device database (the
   approach used to make `data/devices/example/`), so results can be shared in bug reports.

## Dependencies

8. **`netifaces` is unmaintained** and has no wheels for current Python. It is used in one place
   (`discovery_engine.py`, ~line 965); `psutil.net_if_addrs()` does the same and is already a
   dependency.
9. **`pygame`** has no wheels for Python 3.14. Either switch to `pygame-ce` or play the WAV files
   with `simpleaudio`/`aplay`, which is all the audio engine needs.
10. **The AI stack is heavy for a Pi.** torch + transformers is several GB. Decide what the
    language model adds that rules can't (see item 2), measure it on the training sets, and
    consider a smaller runtime (llama.cpp / ONNX) or moving AI analysis off the robot.

## Structure

11. **Make it an installable package.** Every script inserts `src/` into `sys.path`, and the code
    imports itself as `src.…`. Move to `src/r2_astromech/…`, declare dependencies in
    `pyproject.toml`, add console entry points (`r2-scan`, `r2-status`) and delete the `sys.path`
    lines.
12. **One entry point.** `scan_director.py` and `src/main.py` overlap. One CLI with subcommands
    (`r2 scan`, `r2 status`, `r2 export`) is easier to explain and test.
13. **Widen the lint.** CI checks Pyflakes (`F`) only. Next: import sorting (`I`), modern syntax
    (`UP`, about 800 automatic fixes), bugbear (`B`) and blind-except (`BLE`, item 4). Then type
    checking with mypy on `src/core` first.
14. **Legacy examples.** `examples/legacy/` targets an old layout. Rewrite them against the
    current modules or delete them.
15. **Generated training data is committed** (`data/training_sets/`, timestamped files). Generate
    it on demand instead, or attach a reference set to a GitHub release.
16. **Replace the development notes** in `docs/dev-notes/` with one `ARCHITECTURE.md` written from
    the code as it is: the modules, the events they publish, and how a scan flows through them.

## Direction

17. **The discovery module has a twin.** `src/modules/discovery/` was copied into the Raspberry Pi
    droid project, which is now the maintained copy. The two were identical until this clean-up;
    the fixes above (the `None`-safe lookups in particular) now need porting to that copy, or
    r2-astromech should take its discovery code from there instead of keeping its own. Decide which
    before changing the scanners further, so fixes land in one place. The network-awareness idea
    has also been taken further in a separate "what each machine believes" recorder; r2-astromech
    could become a discovery front end for it, or stay a self-contained demonstrator for the blog
    series.
18. **The physical droid.** The hardware side (Raspberry Pi 5, sensors) lives in other
    repositories. Link them here once they're public.
