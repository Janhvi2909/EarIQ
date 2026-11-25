# IndicContextEval Hindi project corpus

- **Source:** https://huggingface.co/datasets/ai4bharat/IndicContextEval
- **Pinned revision:** `d9c03758652771b6ac9dc98d06a5ba6e15c6bd5a`
- **Acquired/retained:** 3,102 retained recordings; 9.075 hours; 124 known source speaker IDs (zero means unavailable, not zero people).
- **Language:** Hindi with source-labelled code mixing.
- **Origin and labels:** Read/extempore domain speech with native-script references, gloss tags, speakers, domains and L0–L6 contextual prompts. Original full benchmark: 8 languages; only Hindi downloaded. 3,110 original rows, eight empty-reference exclusions.
- **Role and splits:** Custom train/validation/test: 2,169 / 466 / 467 (69.92% / 15.02% / 15.05%), grouped speakers/duplicate components. Keep original_split=Hindi. These are project splits, not publisher train/test partitions; rerun providers on the same holdout.
- **License:** CC BY 4.0 per the acquired pinned dataset card. Preserve citation and attribute transformations. No new consent inferred from the license; no new recordings collected.
- **Transformations:** decoded audio QA; 16 kHz mono PCM16 derived files; lossless Unicode NFC/whitespace transcript form; preserved raw/canonical forms; no silence trimming or denoising. Detailed changes and exclusions in the cleaning ledger.
- **Privacy:** identifiable voices/content may remain; raw audio restricted locally. Hashes are pseudonyms, not anonymisation. No speaker identification, voice cloning or third-party audio uploads in this milestone.
- **Limitations:** Domain/code-mixing labels and transcript QC are publisher-provided. Glosses may be English equivalents of native terms; not verified time-aligned gold entities. Do not infer arbitrary phone/email ability or natural conversational repair from this corpus.
- **Audit:** decoded audio and exact hashes checked across prepared records; no new manual transcription/annotation claimed. Measured EDA and distributions in `reports/tables/`; source notes preserved in `docs/source_notices/`.
