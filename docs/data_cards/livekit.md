# LiveKit eot-bench public sample

- **Source:** https://huggingface.co/datasets/livekit/eot-bench-data
- **Pinned revision:** `ca9d98a9686b920a2d8c9eb984224ba9be74e4dd`
- **Acquired/retained:** 800 retained recordings; 2.549 hours; 0 known source speaker IDs (zero means unavailable, not zero people).
- **Language:** English + Hindi.
- **Origin and labels:** 400 turns per selected language from human–agent conversations. Source gives word timings, silence intervals and prior messages; final silence labelled eot, previous spans hold by source convention.
- **Role and splits:** External timing evaluation only. Original source split is validation. No project random train/test split invented. Published full-revision model scores cannot be attached to this sample without a same-revision rerun.
- **License:** Pinned dataset README metadata says CC BY 4.0; upstream code README also describes Apache 2.0 for the dataset. Follow the data-card attribution condition for local use; do not redistribute raw audio until conflicting provenance is clarified.
- **Transformations:** decoded audio QA; 16 kHz mono PCM16 derived files; lossless Unicode NFC/whitespace transcript form; preserved raw/canonical forms; no silence trimming or denoising. Detailed changes and exclusions in the cleaning ledger.
- **Privacy:** identifiable voices/content may remain; raw audio restricted locally. Hashes are pseudonyms, not anonymisation. No speaker identification, voice cloning or third-party audio uploads in this milestone.
- **Limitations:** No released speaker/conversation IDs; no speaker-disjointness guarantee across unknown people. Six rows lack transcript words but retain endpointing audio. Every English final span is 1.5s: beware release/padding leakage.
- **Audit:** decoded audio and exact hashes checked across prepared records; no new manual transcription/annotation claimed. Measured EDA and distributions in `reports/tables/`; source notes preserved in `docs/source_notices/`.
