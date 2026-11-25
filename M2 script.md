# M2 — presentation pointers

## 1 · Objective and dataset choice

- **Objective:** understand, clean and split speech data responsibly — ready for **M3 baseline modelling**.
- **Broad scope:** listening across **assistants, dictation and voice-agent platforms**; evaluate exact values, language context and turn timing separately.
- **Three sources; 4,202 prepared recordings; 17.21 hours**. Pin versions and checksums.
- **VoiceCodeBench:** **300 recordings**, **1,482 entities / 26 types** — emails, names, numbers, IDs, URLs and dictated technical tokens. **External test only**.
- **LiveKit eot-bench:** **800 turns — 400 English + 400 Hindi**; **1,524 hold pauses + 800 turn endings**. **External timing test**.
- **IndicContextEval Hindi:** **3,110 downloaded → 3,102 retained**, **124 speakers**, **23 domains**. **Eight empty references excluded**; raw data retained.
- **1,973 source-labelled code-mixed recordings**; read + extempore speech. **Not an independently audited Hinglish-intake dataset**.

## 2 · Train / validation / test

- **Hindi project split:** **train 2,169 (69.92%)**; **validation 466 (15.02%)**; **test 467 (15.05%)**.
- **Speakers:** **65 train / 31 validation / 28 test**; no speaker crosses these splits.
- **Grouped split:** speakers + repeated transcripts + duplicate decoded audio stay together; **seed 20261028**.
- **Zero detected cross-split overlap** for those exact checks. Shared domain words are allowed; **no claim of unseen vocabulary everywhere**.
- **Public benchmarks stay separate**; do not train on them or combine their percentages with the Hindi split.

## 3 · Preprocessing and cleaning

- **Decoded and checked audio**; exported **16 kHz, mono, PCM16**. Resampled **300** original 48 kHz recordings.
- **Five stereo files:** selected the speech channel after checking the other channel was near-silent.
- **Unicode NFC + whitespace cleaning**; preserve **scripts, leading zeros, letters, decimals and punctuation**. Keep originals.
- **No silence trimming or blanket denoising** — preserve pauses and self-corrections.
- **Eight unusable text references excluded**; **two clipping flags + two duration mismatches retained and logged**.
- **Gold separated from inputs**: transcripts, exact values and future word/pause timings are **evaluation labels**, not live model features.

## 4 · EDA and statistical analysis

- **Seven figure groups:** dataset size/hours; entity classes; audio lengths; split/style balance; pauses; Hindi domains; audio quality.
- **Median duration:** Hindi **9.95s**, timing turns **8.49s**, exact-value recordings **65.52s**.
- **2,000 speaker-cluster bootstrap resamples**; **95% intervals** — related turns are not independent people.
- **Read speech averages 2.73s longer** than extempore; 95% interval **1.89–3.60s**. Descriptive association, not causation.
- **Timing artifact:** every English terminal silence is **1.5s** — do not use file ending/future silence to predict a turn ending.

## 5 · Privacy, limits and readiness

- **Licensed public data**, pseudonymous speaker IDs, restricted raw audio; no voice cloning, real customer collection or external ASR uploads in M2.
- **Data cards + provenance + cleaning log + split audit + EDA notebook** delivered; loader checked against all prepared files.
- **Benchmark caution:** custom Hindi holdout ≠ published full benchmark. Compare providers on the **same holdout** in M3/M4.
- **Available labels:** exact English entities, Hindi transcripts/context/glosses, turn pauses. **No invented gold entity audio boundaries or interactive repair outcomes**.
- **M2 prepares data; M3 measures models.** No new model accuracy result claimed.

*Evidence: [data report](reports/M2_Data_Report.md), [data cards](docs/data_cards/PROJECT.md), [EDA figures](reports/M2_EDA_Figures.pdf), [split audit](reports/leakage_audit.json).*
