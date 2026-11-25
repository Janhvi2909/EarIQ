# M2 — Data understanding and preparation

Prepared 28 October 2026. Scope: reliable listening across voice assistants, dictation, voice input and agent platforms. Call-centre intake is one example, not the project boundary. This report records **executed preparation**, not proposed data collection or model performance.

## Data and roles

| source | rows | hours | known_speakers |
| --- | --- | --- | --- |
| indiccontext | 3102 | 9.075 | 124 |
| livekit | 800 | 2.549 | 0 |
| voicecodebench | 300 | 5.587 | 85 |

Total: **4,202 retained recordings, 17.211 decoded audio hours**. Eight additional Hindi rows were excluded because the native-script reference was empty. All original source files are retained. The sources are complementary tasks, not one homogeneous training dataset.

- VoiceCodeBench: source-annotated **1,482 exact entities, 26 types, 8 workflow domains**. Human-read English recordings of synthetic scenarios. Includes only six source-labelled Indian-accent recordings: insufficient for an Indian-English generalisation claim.
- LiveKit: the pinned **public sample**, English/Hindi only, not the unpublished/full-revision reference population. **2,324 pause spans: 1,524 hold and 800 final spans**. Speaker/conversation IDs are not supplied, so no fabricated grouping IDs were inferred.
- IndicContextEval: the Hindi language split, repurposed as a **custom speaker-grouped project corpus**. It covers all 23 source domains, 1,868 extempore recordings and 1,973 source-labelled code-mixed recordings. The latter is a source label, not a new human language audit. Domain terms/borrowings are not equivalent to every natural Hinglish use case.

The formerly uncertain IndicContextEval URLs resolved through the public API; the old/new identifiers returned the same pinned revision. That alias is **not counted as two datasets**. No 720-speaker/turn collection was fabricated. New consented recordings remain a possible future extension, not a prerequisite claimed completed here.

## Split policy and actual split

| split | rows | known_speakers | pct_of_hindi_development_pool |
| --- | --- | --- | --- |
| external_entity_test | 300 | 85 | — |
| external_timing_test | 800 | 0 | — |
| test | 467 | 28 | 15.05% |
| train | 2169 | 65 | 69.92% |
| validation | 466 | 31 | 15.02% |

Percentages apply **only to the 3,102-row Hindi project corpus**. Targets were 70/15/15 by recording count, not by speaker count. Splitting connects shared speaker IDs, identical NFC/casefolded transcripts and identical decoded prepared audio before assignment. The selected assignment uses seed **20261028**, sample-count balance and source metadata coverage (domains, speech style, code-mixing); no model scores. Repeated domain vocabulary is allowed and its overlap is explicitly measured in `tables/gloss_vocabulary_overlap.csv`.

All train/validation/test speaker, transcript and decoded-audio intersections are zero. Exact transcript/audio intersections with the external corpora are also zero. This does not prove absence of acoustic near-duplicates, semantic paraphrases, shared unidentified people across sources or prior exposure in pretrained models.

Public source splits remain identifiable as `original_split`. The Hindi custom split changes the benchmark protocol; **never compare its test score directly to Sarvam's eight-language overall published score**. Rerun comparators on the same holdout for a claim about improvement. External English/timing benchmarks stay out of training and parameter selection.

## Cleaning and audio QC

- Decoded all included audio; checked finite samples, nonzero duration, channel layout and reference availability.
- Exported 16 kHz mono PCM16 WAV, retaining raw recordings and declared durations. Resampled all 300 VoiceCodeBench recordings from 48 kHz. Five had a near-silent first channel; select the second only after an RMS-ratio check. Ambiguous multichannel audio causes preparation to fail instead of silently mixing speakers.
- Kept source transcripts, NFC/whitespace-cleaned references and canonical values separate. **1,083 references changed under NFC/whitespace cleaning**. No digits, leading zeros, diacritics or identity-bearing punctuation were stripped from target values.
- Preserved silences, disfluencies and self-corrections. No amplitude normalisation, denoising or augmentation was performed.
- Excluded eight empty Hindi references using an explicit row ledger; none removed based on model errors. Two clipping flags (>0.1% near-full-scale samples) and two >0.1s declared-duration mismatches remain in the prepared set. These are flags, not automatic proof that the speech is unusable.
- Exact transcript duplicate groups are retained with connected grouping in Hindi. Official benchmark membership is preserved, including repeated short utterances. No decoded-audio duplicates were found within any source.

See the row-level `data/processed/cleaning_ledger.jsonl` and `exclusions.jsonl`. Paths and labels live outside the tracked report to avoid bundling raw speech in a code handover.

## EDA and statistical results

Seven figure groups and machine-readable supporting tables cover composition, entity imbalance/length, duration, domain/style/code-mixing coverage, pauses and audio quality. [Figure PDF](M2_EDA_Figures.pdf)

Hindi mean duration is **10.531s**, with speaker-cluster-bootstrap 95% interval **[9.920, 11.101]s**. The source-labelled code-mixing fraction is **63.60%**. Read-minus-extempore mean duration is **2.725s**, interval **[1.887, 3.602]s**. Use these as descriptive associations in this collected corpus, not causal or population-wide findings.

Bootstrap: **2,000 resamples of whole speakers**, seed 20261028, percentile intervals. Each resample retains all recordings of a sampled speaker. For missing LiveKit speaker/session IDs, pause statistics are descriptive only; we do not invent independent-speaker confidence intervals. Intervals describe observed-source sampling variation and do not establish demographic representativeness.

**Important artifact:** all 400 English final silence spans are exactly **1.5s** within floating-point tolerance. This is consistent with release/padding construction and is not evidence that natural English turn gaps always last 1.5s. Full-file duration, final-span length/end and future word timestamps must never be live decision features. Labels follow the source convention: earlier pauses are hold; final pause is end-of-turn. A causal evaluator must see audio/context only up to the decision time.

## Labels, input separation and privacy

- Separate `*_labels.jsonl` stores gold transcripts, entities, timing and QC; the inference manifest contains only audio pointers, language and source metadata. Prior LiveKit messages are legitimate preceding context, not the current gold transcript.
- Contextual Hindi prompts are in an opt-in sidecar. The loader selects **one fixed L0–L6 level**; it does not feed all prompt conditions at once. L4/L5 are source-provided domain vocabularies, not a dictionary mined from held-out answers. Training-derived statistics/vocabularies must use training only in M3.
- Hindi source glosses are preserved as textual evidence; no unverified native entity or audio spans were invented. Public source QC is documented; **no independent human reannotation is claimed**. Exact within-entity cutoff evaluation and genuine interactive repair require additional aligned/adjudicated labels or a compatible interactive benchmark later.
- Raw source speaker IDs/paths and demographic metadata are excluded from inference manifests. Speaker hashes are pseudonyms, not guaranteed anonymity; voice itself can identify someone. Local audio and gold are excluded from Git by default.
- Licenses: IndicContextEval CC BY 4.0; LiveKit card CC BY 4.0 with a code-README discrepancy documented separately; VoiceCodeBench MIT non-audio plus specific audio terms prohibiting voice cloning. Source notices are copied under `docs/source_notices/`.
- No new personal recordings, voice cloning, customer records, paid API calls or audio uploads to external ASR were performed. Raw audio is locally restricted and not bundled for public release. See [privacy policy](../docs/PRIVACY.md).

## Readiness and milestone checklist

| Industry M2 requirement | Executed artifact |
| --- | --- |
| Data card | Project and three source cards under `docs/data_cards/` |
| Exploratory analysis | `notebooks/M2_EDA.ipynb`, seven figure groups, CSV tables |
| Data cleaning | `scripts/prepare_data.py`, cleaning/exclusion ledgers |
| Statistical analysis | `statistical_analysis.json`, table and grouped bootstrap implementation |
| Train/validation/test | Frozen Hindi project manifests; independent external manifests; `leakage_audit.json` |
| Privacy | `docs/PRIVACY.md`, source notices and pseudonymous exports |

The prepared tasks are **Hindi contextual ASR, English exact-value evaluation and English/Hindi endpointing**. Their data preparation is complete. Coverage of every language, locale, Indian accent, entity audio boundary and interactive repair behaviour is **not** implied. Model development and accuracy/latency measurement begin in M3. Published baseline artifacts are preserved as references, not reported as our results.
