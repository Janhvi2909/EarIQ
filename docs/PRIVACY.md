# Privacy, licensing and responsible use

## This release

This milestone uses licensed, publicly accessible speech corpora for local academic NLP preparation. It collects no new participant recordings or real customer conversations and sends no audio to ASR, TTS or LLM APIs. Public release is not evidence that a voice is anonymous or that every downstream use is permitted.

- **Raw speech and source metadata:** local `data/raw/`; keep access limited to the project team. Do not upload the folder or embed audio/transcript examples in public presentations without checking the source terms and necessity.
- **Prepared speech:** `data/audio/`; still identifiable speech, even though container format/sample rate changed.
- **Pseudonyms:** speaker IDs are source-specific SHA-256-derived identifiers. These support grouping, not biometric identification or guaranteed anonymisation. No speaker-recognition models are used. Hashing an identifier does not remove identity from the voice.
- **Data minimisation:** inference manifests omit source filenames, source speaker names/IDs, age and gender. Training/evaluation references remain in separate local label files. Contextual prompt sidecars can contain source domain/region metadata; use only the chosen protocol and restrict their access too.
- **Outputs:** reports use counts and distributions; no newly recorded personal information. Example values in source data can resemble real values: never dial phone numbers, send email, execute dictated commands or connect IDs to real accounts.

## Source-specific terms

| Source | Applicable statement | Project handling |
| --- | --- | --- |
| VoiceCodeBench | MIT non-audio; separate audio terms prohibit voice cloning, cover derivatives and require notice preservation | External diagnostic evaluation only; preserve LICENSE; no speech synthesis or voice cloning |
| IndicContextEval | Pinned card: CC BY 4.0 | Attribute authors and transformations; local custom Hindi split, explicitly distinct from the publisher's benchmark protocol |
| LiveKit eot-bench | Pinned data card: CC BY 4.0; upstream code README describes Apache 2.0 for data too | Record the discrepancy, retain attribution and source metadata; do not redistribute raw audio until provenance is clarified |

Original notices are copied into `docs/source_notices/`. Code licenses do not override dataset or participant restrictions. The source VoiceCodeBench card states paid contributors consented to dataset use/release; no independent consent audit is claimed. For the other datasets, rely on the publisher's documented release terms, without inventing participant consent records.

## Retention, access and future collection

- Retain restricted raw/prepared speech only through project assessment and a planned **90-day correction window**; then review and delete local audio unless a documented permitted project purpose requires continued retention. This is a project policy, not a claim that deletion has already occurred.
- Share code, aggregate reports and acquisition instructions by default; raw audio/labels/manifests are ignored by Git. Review license/consent terms before any public data release or external API processing.
- If rights/accuracy/deletion concerns are reported, identify the source/sample, quarantine it, respect publisher removal instructions, then regenerate manifests and mark affected comparisons as superseded. No automatic legal-compliance certification is implied.
- Any new recordings need explicit adult consent covering research, storage/retention and separate choices for redistribution or external processing. Keep participant contact/consent material separate from audio/model inputs. Use fictional values and do not collect bank credentials or medical records.

## Limitations and fairness

Source code-mixing/accent/demographic labels are descriptive publisher metadata. There is no independently recruited representative population here. Do not infer fairness, disability coverage, all Indian accents, all Hinglish speakers or universal multilingual competence from these sources. Report source, sample size, per-task metrics and uncertainty in every comparison.
