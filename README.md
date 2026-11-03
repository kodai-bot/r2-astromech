# R2 Astromech: network discovery testbed

A hobby robotics project: the software side of a maintenance "droid" inspired by the astromechs of
Star Wars. R2 joins a local network, works out what is on it, and reports back in text and R2-style
sounds. The idea behind it, that devices should be easy to inspect and repair, is written up in a
three-part series on allismotion.org:

1. [Teaching an Old Droid New Tricks](https://allismotion.org/teaching-an-old-droid-new-tricks/)
2. [The Death of the Helper Droid](https://allismotion.org/the-death-of-the-helper-droid-how-modular-design-philosophy-gave-way-to-vendor-lock-in/)
3. [Universal Maintenance Design](https://allismotion.org/universal-maintenance-design-making-infrastructure-r2-accessible/)

**Status: experimental (2025).** A personal testbed, not a product or a service. It runs on a Linux
PC and is being moved to a Raspberry Pi 5. See [docs/REVIEW.md](docs/REVIEW.md) for an honest
assessment of the code and the planned work.

## What it does

- **Discovers devices** with several methods: the ARP table, mDNS/Bonjour, SSDP/UPnP, SNMP and
  port scans (via nmap), coordinated by a multi-phase discovery engine
  (`src/modules/discovery/scanners/`).
- **Keeps a device database**: each device's first and last sighting, open ports and a short
  status history (`src/modules/discovery/device_database.py`).
- **Reports in character**: text output plus R2-style sounds (`src/modules/personality/`).
- **Optional local AI analysis**: small language models (TinyLlama, Phi-3) describe devices
  (`src/modules/ai/`). This needs the large `requirements-ai.txt` stack.
- **Generates training data** for fine-tuning those models from discovery results
  (`src/modules/training/`).

Modules talk to each other through an async event bus (`src/core/events.py`) and are wired
together by a small dependency-injection container (`src/core/container.py`).

## Responsible use

R2 scans the network it is run on. **Only run it on networks you own or have permission to scan.**
The target is set in `config/r2_config.yaml` (`discovery.networks.default`).

Scan results are written to `data/devices/*.json`. They describe your network, so they are
git-ignored and never committed.

## Quick start

```bash
sudo apt install nmap portaudio19-dev libglib2.0-dev   # system tools used by the scanners and audio
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt           # core
pip install -r requirements-ai.txt        # optional: local AI analysis (large)

python src/main.py --status-only          # check the system starts
python scan_director.py                   # run a discovery scan of the configured network
```

Raspberry Pi: see [docs/RASPBERRY_PI.md](docs/RASPBERRY_PI.md) and `scripts/setup_rpi.sh`.

### Trying it without scanning

`data/devices/example/` holds an anonymised device database (documentation-range addresses,
made-up MAC addresses and hostnames). Copy it into place to try the training-data examples:

```bash
cp data/devices/example/*.json data/devices/
python examples/demo_simple_training_data.py
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest          # device database, event bus, configuration
ruff check .
```

The tests cover the core only; the scanners have none yet (see [docs/REVIEW.md](docs/REVIEW.md)).

## Layout

| Path | Contents |
|---|---|
| `scan_director.py` | Runs a full discovery scan with audio feedback |
| `src/main.py` | System entry point (`--status-only`, `--health-check`) |
| `src/core/` | Configuration, event bus, dependency container, interfaces |
| `src/modules/discovery/` | Scanners, discovery engine, device database |
| `src/modules/personality/` | Text and audio output |
| `src/modules/ai/`, `src/modules/training/` | Optional language-model analysis and training data |
| `examples/` | Demo scripts (see `examples/README.md`) |
| `config/` | Configuration files |
| `data/sounds/` | R2 sound samples |
| `docs/` | Review, Raspberry Pi guide, development notes |

## Licence

MIT; see [LICENSE](LICENSE). Provided as-is, without warranty.

Star Wars, R2-D2 and Industrial Automaton are trademarks of Lucasfilm Ltd. This is an unofficial fan
project and is not affiliated with or endorsed by Lucasfilm.
