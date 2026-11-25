# VoiceCodeBench

- **Source:** https://huggingface.co/datasets/besimple-ai/voice-code-bench
- **Pinned revision:** `8edfa398aa5575816d940793e4e2b8c6430184da`
- **Acquired/retained:** 300 retained recordings; 5.587 hours; 85 known source speaker IDs (zero means unavailable, not zero people).
- **Language:** English.
- **Origin and labels:** Source human-read synthetic scenarios; exact spoken and canonical values. 26 entity types, 8 workflow domains; source-script/annotation generation was LLM-assisted, audio human-recorded. Paid contributors consented according to the publisher card.
- **Role and splits:** External entity test; official test-only membership retained. No training/tuning. Use official evaluator/version for CTEM/TSR comparisons; local canonical-field correctness is a different measure.
- **License:** MIT for non-audio; audio terms specifically prohibit voice cloning and require notice preservation. Copies/derived representations remain subject to audio terms.
- **Transformations:** decoded audio QA; 16 kHz mono PCM16 derived files; lossless Unicode NFC/whitespace transcript form; preserved raw/canonical forms; no silence trimming or denoising. Detailed changes and exclusions in the cleaning ledger.
- **Privacy:** identifiable voices/content may remain; raw audio restricted locally. Hashes are pseudonyms, not anonymisation. No speaker identification, voice cloning or third-party audio uploads in this milestone.
- **Limitations:** Controlled read speech; heavily American-accented. Only six rows labelled Indian accent. Source demographic metadata is coarse/unverified; no claim of authentic customer calls.
- **Audit:** decoded audio and exact hashes checked across prepared records; no new manual transcription/annotation claimed. Measured EDA and distributions in `reports/tables/`; source notes preserved in `docs/source_notices/`.
