# Voice AI that listens better — industry NLP project

The problem covers voice assistants, mic dictation, voice search and agent platforms: preserving important information across accents, languages and contexts. A support call is one motivating use case. **The original M1 PDF is unchanged.**

- Present M1 with [M1 script.md](<M1 script.md>).
- Present executed M2 work with [M2 script.md](<M2 script.md>).
- Read the [measured M2 report](reports/M2_Data_Report.md), [project data card](docs/data_cards/PROJECT.md), [privacy policy](docs/PRIVACY.md) and [EDA figure PDF](reports/M2_EDA_Figures.pdf).
- Explore [the executed notebook](notebooks/M2_EDA.ipynb). Detailed CSVs/JSON are under `reports/`.

## Reproduce

Python 3.14 was used locally. `requirements.lock.txt` records exact installed versions; `requirements.txt` records direct dependencies. Audio acquisition requires internet access; subsequent preparation is local. Download about 3.3 GB; allow additional space for ~1.9 GB prepared audio and the environment. No credentials or paid model APIs are required for the selected files.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
.venv/bin/python scripts/acquire_data.py --inspect
.venv/bin/python scripts/acquire_data.py
.venv/bin/python scripts/run_m2.py
```

The checked-in `configs/sources.json` pins actual dataset revisions. `--inspect` obtains pinned metadata/license files for selected sources and probes current access for unused alternatives. For this delivered run all manifests correspond to the configured pins. Network/download actions may need your environment's network permission. Notebook execution needs permission to open local Jupyter communication sockets.

To avoid unnecessary reprocessing when viewing an existing run:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/verify_data.py
```

## Use the prepared data

```python
from src.listening_data import iter_inputs, iter_supervised

inputs, gold = next(iter_supervised("train"))
audio_path = inputs["audio_path"]
reference = gold["reference_nfc"]

# Choose exactly one contextual benchmark condition for each experiment.
example = next(iter_inputs("validation", context_level=1))

# Test and external gold require explicit evaluation opt-in.
example, gold = next(iter_supervised("test", allow_evaluation_labels=True))
```

`train`, `validation` and `test` refer to the **custom Hindi corpus**, not to all sources pooled together. `external_entity_test` and `external_timing_test` preserve separate public evaluation sets. Raw labels/audio are excluded from Git. Always review individual source terms before redistribution or new uses.

## Project layout

| Location | Purpose |
| --- | --- |
| `configs/` | Source pins and original PDF hashes |
| `scripts/` | Acquisition, cleaning/grouped splits, EDA, report generation and verification |
| `src/listening_data.py` | Gold-separated baseline loader |
| `data/raw/` | Restricted downloaded files, source metadata and download checksums |
| `data/audio/` | Derived 16 kHz mono PCM16 audio |
| `data/manifests/` | Input, gold and optional-context files for each split |
| `data/processed/` | Label-aware analytical records; cleaning/exclusion ledger |
| `reports/` | Actual counts, statistical summaries, split audit, figures and verification |
| `docs/` | Data cards, notices and privacy/use restrictions |
| `tests/` | Value preservation, split-overlap and label-leakage checks |
| `research/` | Historical planning/audit documents; see latest scope note |

M2 prepares three tasks: Hindi contextual recognition, English exact structured-value evaluation and English/Hindi turn timing. It does not claim new model accuracy, full Indian-English/Hinglish representativeness, human-adjudicated entity audio boundaries or measured interactive repair. Those distinctions are documented so future model comparisons remain meaningful.
