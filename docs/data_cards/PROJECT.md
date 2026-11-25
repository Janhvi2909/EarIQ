# Project data card

- **Purpose:** prepare speech data for a capture layer across assistants, dictation and voice agents. Exact values, contextual recognition and endpoint timing are separate evaluation tracks.
- **Version:** 28 October 2026; source commits in `configs/sources.json`; downloaded-file SHA-256 and upstream LFS/size verification in `data/raw/download_manifest.json`; prepared manifest checksums in `reports/verification.json` after validation.
- **Composition:** 4,202 recordings / 17.211 hours; 3 sources. [Measured table](../../reports/tables/source_summary.csv)
- **Training/development:** 3,102 retained Hindi contextual-speech samples, split 2,169 / 466 / 467 (69.92% / 15.02% / 15.05%). Official Hindi source is a language split, not this train/dev/test partition.
- **External tests:** 300 English structured-value recordings; 800 English/Hindi endpointing turns. Kept out of training/tuning.
- **Labels available:** source transcripts/canonical entities/context/glosses and pause/word timings where supplied. No newly human-adjudicated audio entity boundaries or interactive repair outcomes.
- **Known speaker support:** 124 Hindi speakers; 85 VoiceCodeBench source IDs; LiveKit speaker IDs absent. No cross-corpus identity matching attempted.
- **Language limitations:** Hindi source code-mixing label includes domain terms; six VoiceCodeBench recordings carry an Indian accent label. Not enough for broad Indian-English, demographic or locale claims.
- **Splits/leakage:** grouped by source speakers and exact transcript/audio duplicate components; 70/15/15 target by rows, fixed seed; shared domain terms allowed and measured. Exact cross-split intersections zero; near-duplicates/pretraining contamination not ruled out.
- **Inputs:** audio pointers + language; preceding messages for timing; optional fixed contextual prompt level for Hindi. Gold labels are separate.
- **Audio:** derived 16 kHz mono PCM16; no pause trimming, denoising or augmentation. Raw files retained.
- **Licensing/privacy:** per-source rules differ; do not treat the bundle as uniformly MIT/CC. Local research use; no raw-audio public release by default. [Policy](../PRIVACY.md)
- **Access:** all selected source files acquired publicly without local credentials; public APIs were used. Other probed/gated datasets were not used.
- **Provenance and exclusions:** eight empty references excluded; all decisions logged. [Report](../../reports/M2_Data_Report.md)
- **Maintenance:** rerun acquisition/preparation/analysis/verification explicitly for a new release. Keep existing manifests frozen for comparisons. If a rights/access issue is reported, quarantine affected rows, regenerate a new version and report invalidated comparisons.
