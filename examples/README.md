# Examples

Run them from the repository root, e.g. `python examples/demo_ssdp_only.py`.

| Script | What it shows | Scans the network? | Needs `requirements-ai.txt`? |
|---|---|---|---|
| `demo_ssdp_only.py` | SSDP/UPnP discovery on its own | yes | no |
| `demo_simple_training_data.py` | Turn the device database into training data | no | no |
| `demo_r2_training_data_generator.py` | Full training-data pipeline | no | yes |
| `demo_modular_ai.py` | The AI model manager | no | yes |
| `demo_ai_network_integration.py` | AI analysis of discovered devices | yes | yes |
| `demo_tinyllm_only.py` | TinyLlama analysis of a live scan | yes | yes |
| `demo_r2_tinyllm_standalone.py` | TinyLlama device descriptions, minimal version | no | yes |
| `demo_r2_with_tinyllm.py` | Discovery plus TinyLlama commentary | no | yes |
| `check_tinyllm_model.py` | Manual check that the TinyLlama model loads and responds | no | yes |

The training-data examples read `data/devices/*.json`. To try them without scanning, copy in the
anonymised example data: `cp data/devices/example/*.json data/devices/`.

`legacy/` holds two examples written for an earlier layout of the code (`src.ai`,
`src.personality.r2_sounds`). They do not run against the current code; see `docs/REVIEW.md`.
