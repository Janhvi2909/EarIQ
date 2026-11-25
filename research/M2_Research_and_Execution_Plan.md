# M2: research findings and proposed execution plan

> **Historical planning document.** User approved implementation with a broader product scope on 28 October 2026: assistants, dictation and general voice input, not only support intake. The M1 PDF must remain unchanged. Executed dataset choices, counts and limitations are now recorded in `reports/M2_Data_Report.md`; presentation pointers are in `M1 script.md` and `M2 script.md`. IndicContextEval access succeeded during execution; no new participant corpus was fabricated.

Prepared 28 October 2026. **Awaiting approval; no dataset preparation, model training, baseline runs or PDF edits have been performed.** Published numbers below are source results, not our measurements. Counts proposed for new data are collection targets, not acquired data.

## 1. Project and milestone boundary

The proposed initial product is an entity-aware intake layer for voice-agent engineers building customer-support callbacks. Its first workflow captures names, phone numbers, emails and order/reference IDs into a mock CRM. Indian English and Hindi–English code-mixing are the priority languages. The layer can keep listening, commit a value or request a focused clarification; it must not invent missing information.

M2 must prepare evidence for three distinct questions:

1. Did the system recover the exact required value?
2. Did it finalise while a caller was still providing that value?
3. When it asked for a correction, did it actually repair the value, at what conversational cost?

A transcript corpus alone cannot answer all three. An offline recording cannot establish interactive repair success unless it includes the relevant follow-up responses.

The handbook's page 6 requires a data card, EDA, cleaning, statistical analysis and privacy considerations. Its page 9 adds an explicit train/validation/test checklist item. M2 will cover all six. Actual baseline development and model improvements remain M3; optimisation and final robustness results remain M4.

## 2. What the company research establishes

| Company/platform | First-party evidence | Implication for our project |
|---|---|---|
| Deepgram | Flux integrates recognition and end-of-turn decisions. Its evaluation discussion emphasises both cutoff frequency and timing. [Launch](https://deepgram.com/learn/introducing-flux-conversational-speech-recognition), [evaluation](https://deepgram.com/learn/evaluating-end-of-turn-detection-models) | General turn detection is an existing capability. Test our field-state decisions against a credible detector, not only silence thresholds. |
| LiveKit | Publishes an end-of-turn benchmark, adapters and prediction artifacts. [Repository](https://github.com/livekit/eot-bench) | A company directly named in the deck supplies a reproducible timing comparison. |
| AssemblyAI | Recommends entity metrics alongside WER; its published entity and latency evaluations use specified datasets and conditions. [Docs](https://www.assemblyai.com/docs/streaming/benchmarks) | Entity mistakes and timing are real industry concerns; a vendor's private-corpus score cannot become our public-corpus baseline. |
| Sarvam | Publishes evaluations on Indian speech, including Svarah and contextual entity prompting. [V4 announcement](https://www.sarvam.ai/blogs/introducing-saaras-v4) | Indian speech and contextual vocabulary are established comparison areas. We must evaluate benefit beyond existing keyterm support. |
| Bolna | Offers Sarvam and Deepgram transcription integrations. [Integrations](https://www.bolna.ai/integrations) | These providers are relevant to an Indian orchestration platform; integration support does not prove Bolna trained on any particular public dataset. |
| Vapi | Documents selectable STT providers and custom streaming transcribers. [Providers](https://docs.vapi.ai/providers/transcriber/overview), [custom transcriber](https://docs.vapi.ai/customization/custom-transcriber) | An external capture service is a plausible deployment route; verify actual timing/control hooks during M3 before promising a drop-in integration. |
| Sierra | Publishes τ-Entity for exact capture and repair, with public task definitions and scoring. [Announcement](https://sierra.ai/blog/tau-entity-can-voice-agents-get-the-details-right), [implementation](https://github.com/sierra-research/tau2-bench/blob/main/docs/elicitation.md) | Particularly close to our business problem; use as a later interactive evaluation, subject to runtime and cost feasibility. |

These are representative relevant companies, not a ranked list of the largest firms. There is no verified evidence here that every named Indian and US company uses a single common dataset or has reported our precise failure mode on it. We will distinguish provider-authored results, third-party measurements and our own reruns.

## 3. Recommended dataset decision

**Use VoiceCodeBench as the primary external exact-entity benchmark, LiveKit eot-bench for turn timing, and a small consented Indian-English/Hinglish intake corpus for development and integrated evaluation. Treat IndicContextEval as the preferred conditional Indian public extension.** Do not pool their scores into one leaderboard number.

This balances published comparisons with labels that actually test our capture layer. A single public corpus has not been verified to cover exact structured values, Indian accents, genuine Hinglish, within-entity pauses and interactive corrections together.

### A. VoiceCodeBench: primary public entity benchmark

The release describes 300 human-recorded English segments, 5.587 hours, 85 speaker IDs and 1,482 annotated entities across 26 types. It supplies acoustic and canonical reference forms and baseline artifacts. It is **test-only**, not our training data. Non-audio content is MIT licensed; audio has an additional voice-cloning restriction, so the search result's blanket “MIT” label is incomplete. [Dataset and terms](https://huggingface.co/datasets/besimple-ai/voice-code-bench)

Use the complete frozen release for official comparisons; show our four priority field classes as a separate diagnostic slice. English workplace material is relevant to exact capture, but it is not representative evidence for Hinglish or live customer service. Unsupported classes must remain visible in the full benchmark result rather than silently being dropped.

The official CTEM evaluates recoverability from transcripts through a versioned verifier. That differs from checking whether our system actually wrote the correct field into a CRM. Report the two separately. [Paper methodology](https://arxiv.org/html/2608.28916v1)

### B. LiveKit eot-bench: public timing benchmark

The current Hugging Face card describes a deterministic **5,454-turn public sample**, including 400 English and 400 Hindi turns, with audio, word timings, silence spans and preceding messages. It exposes a single `validation` split, not ready-made train/dev/test splits. The card points to a `full` revision. Its metadata says CC BY 4.0, while the code README describes Apache 2.0 for the dataset as well: record this discrepancy and inspect the actual pinned data license before redistribution. Code and data licenses must be documented independently. [Data card](https://huggingface.co/datasets/livekit/eot-bench-data)

Start with English and Hindi. These languages do not by themselves establish Hinglish coverage. Add human-checked entity spans only for a separately reported diagnostic subset; never imply these were original benchmark labels.

Keep published-benchmark data external to our training/tuning pool. Resolve which data revision produced the committed reference predictions. If only the current sample can be acquired, compare systems rerun on that sample and label the result accordingly. Do not attach full-revision published numbers to the sample. [Reference artifacts and evaluation harness](https://github.com/livekit/eot-bench)

### C. New consented intake corpus: development and integrated test

**Proposed target: 30 consenting adult speakers × 24 short intake turns = 720 base turns**, half Indian English and half Hinglish per speaker where feasible. Four field types receive balanced coverage. The resulting hours will be measured, not inferred as an established fact.

Include ordinary completions, pauses inside entities, digit grouping, spelled names, “double”/“triple” forms where natural, self-corrections, abandoned starts and explicit completion. Include fluent easy turns as controls; otherwise a strategy that always waits could appear artificially good. Do not force every speaker into unnatural code-mixing.

Split recording assignments **before collection** into 18/6/6 speakers for train/dev/test, targeting 432/144/144 turns. Use separate template-family and fictional-entity banks for the three partitions. English/Hinglish paraphrases of the same underlying prompt stay in the same partition. These are targets; report actual eligible counts and constraints after collection.

This is a small academic evaluation, not a production-representative customer dataset. Six test speakers will limit accent/subgroup conclusions even with many turns. If recruitment falls short, reduce the claims and document uncertainty instead of replacing people with undisclosed synthetic voices.

New recordings require human participation. I can prepare scripts, consent text, collection instructions and validation, but cannot independently supply a diverse set of genuine participant voices.

For repair testing, reserve a small consented **interactive** session set with repeated field values, corrections and final record outcomes. It can be collected at M3 once baseline/candidate policies exist, under the M2 protocol. One-way M2 recordings support clarification-trigger evaluation only; we will not claim they prove repair success.

### D. IndicContextEval: preferred optional Indian public extension

This is a stronger conceptual match than general ASR data for contextual domain vocabulary: it includes natural Indian speech, entity information and controlled prompt conditions, with results associated with AI4Bharat and Sarvam. Hindi is the first proposed slice. However, domain terminology is not equivalent to callback-number/email capture or multi-turn support calls. [Paper](https://arxiv.org/html/2606.19157v1)

The repository has inconsistent dataset identifiers (`AI4Bharat/IndicContextEval` versus a `SakshiJ` loading example), and the advertised dataset pages could not be retrieved in this review. It also says evaluation scripts are forthcoming. **Do not make the whole project depend on it.** At the first execution gate, verify access, schema, audio rights and an implementable scorer. Otherwise use a bounded IndicVoices Hindi subset for extra development data, or Svarah as an external Indian-English WER diagnostic, and keep our own Hinglish corpus. Both fallback pages currently require accepting Hugging Face access conditions. [Repository](https://github.com/AI4Bharat/IndicContextEval), [IndicVoices](https://huggingface.co/datasets/ai4bharat/IndicVoices), [Svarah](https://huggingface.co/datasets/ai4bharat/Svarah)

### Alternatives considered

| Candidate | Decision and reason |
|---|---|
| Voice of India | Strong evidence for the problem and already in the deck, but its paper explicitly calls it closed-source. Not the reproducible core. [Paper](https://arxiv.org/html/2604.19151v1) |
| SpokenWOZ | Useful existing audio/dialogue-state train/dev/test resource. Keep as a development fallback if participant collection is insufficient; exact entity/endpoint labels still need auditing. Its published JGA is not our exact-field score. CC BY-NC 4.0 limits commercial reuse. [Official project](https://spokenwoz.github.io/) |
| IndicVoices | Strong Indian speech development resource and used in Sarvam's evaluations. Not natively a labelled exact-intake/repair benchmark; do not assume Hindi utterances are Hinglish. [Dataset](https://huggingface.co/datasets/ai4bharat/IndicVoices), [Sarvam evaluation](https://www.sarvam.ai/blogs/asr) |
| Svarah | Relevant Indian-English external diagnostic with published ASR results, but no ready-made intake-field/repair labels. Preserve its test purpose. [Dataset](https://huggingface.co/datasets/ai4bharat/Svarah) |
| SLUE-VoxPopuli | Real speech and established ASR/NER metrics, but parliamentary entities differ substantially from the contact fields we intend to capture. Not the main corpus. [Tasks and licenses](https://asappresearch.github.io/slue-toolkit/slue-tasks.html) |
| Generic clean read-speech corpora | Useful for broad ASR checks, weaker than the shortlisted sources for this business task. |

## 4. Published comparisons we can actually plan around

| Benchmark / frozen source | Example published reference | Conditions for comparison |
|---|---|---|
| VoiceCodeBench paper v1, Table 6 | Deepgram Nova-3 batch: CTEM **90.9%**, TSR **68.7%**; streaming: CTEM **88.9%**, TSR **61.7%**. Whisper large-v3 batch: CTEM **87.6%**, TSR **54.3%**. | Same 300 recordings, release, evaluator and mode. Hosted Whisper's configuration may differ from our local implementation. A rerun is needed to isolate our layer's benefit. [Paper](https://arxiv.org/html/2608.28916v1) |
| LiveKit reference English table | Turn Detector v1: **9.9% false cutoffs at a 300 ms delay budget**; **543 ms endpoint delay at a 5% cutoff budget**. | Same dataset revision, policy/evaluator and operating-point selection. These are endpoint delays, not inference latency. [Reference table](https://github.com/livekit/eot-bench) |
| IndicContextEval paper/result file | Sarvam Audio at L1: **16.86% clamped WER / 25.93% NEER**; L5 NEER **21.69%**. | These aggregate eight languages and use specific prompts/normalisation. A Hindi subset is not comparable to the overall average. The paper's “Sarvam Audio” must not be silently renamed Saaras V4. [Frozen result file](https://raw.githubusercontent.com/AI4Bharat/IndicContextEval/main/results/paper_results.csv) |
| τ-Elicitation paper, later renamed τ-Entity | Tested voice configurations achieve **14–41% Pass³**; prescribed verification adds **21–28 seconds** per call. | Same task generator/scorer, caller voices/model, conditions and agent configuration. A modified Hinglish task set is an extension, not the official benchmark. [Paper](https://arxiv.org/html/2609.13602v1) |

The VoiceCodeBench live board and paper contain different snapshots and verifier versions. Select one frozen evaluation contract; never combine their columns. Similarly, current τ-Entity runtime documentation warns that released seeded voice draws can differ from historical research runs. Published values are reference points until exact reproduction conditions are established. [VoiceCodeBench live snapshot](https://openbenchmarks.com/structured-speech-to-text-benchmark), [τ-Entity runtime notes](https://github.com/sierra-research/tau2-bench/blob/main/docs/elicitation.md)

For the later causal experiment, hold ASR, audio, workflow, prompts permitted to both systems and hardware constant. Compare layer disabled versus enabled; then add a strong general turn detector and an always-confirm policy. A result on our new Hinglish set cannot be advertised as beating a published English benchmark result.

## 5. M2 execution sequence after approval

### Phase 1 — Access, provenance and scope gate

- Verify actual source artifacts, terms, dataset revisions, checksums, audio availability and evaluation scripts. Record exact IDs and access outcomes.
- Inspect bounded metadata/audio samples to establish fields and label quality. No paid full benchmark is needed for M2.
- Check whether LiveKit full-revision data and reference artifacts align; resolve license provenance. Check IndicContextEval access without assuming a broken web fetch proves the data does not exist.
- Pilot 40–60 consented development turns to estimate recording/annotation work and validate the label guide. Keep pilot speakers/templates out of the final test.
- Freeze workflow, first four field types, planned splits and metric definitions. If a source fails the gate, document the fallback rather than silently changing the comparison.

**Output:** source manifest, license/access notes, scope decision and collection packet.

### Phase 2 — Data cards and annotation guide

Create one card per source plus a combined project card: purpose, origin, version, collection method, population, language/style, domains, counts/hours, schema, existing versus added labels, license, consent, permitted use, restrictions, split policy, known limitations and maintenance.

Use separate model-input and evaluation-label schemas. A prepared record should identify:

| Group | Planned fields |
|---|---|
| Provenance | dataset/revision, source sample ID, checksum, collection date where available, license reference |
| Grouping | speaker/session/conversation, scenario/template family, base recording ID, split; unknown IDs explicitly marked |
| Audio | original path/rate/channels, derived path, duration, channel semantics, transform parameters |
| Language | utterance language, human-checked code-switching label, script policy, optional consented demographic metadata |
| Gold labels, evaluation-only | verbatim transcript; entity type, spoken and canonical forms; text/audio spans; completion time; corrections; ambiguity flags |
| Timing labels | pause spans, hold/end labels, turn completion and annotation confidence |
| Quality/privacy | consent/access status, QC flags, reviewer/adjudication state, exclusion reason |

Use manual listening to verify critical values. Forced alignment can propose times; it cannot certify whether a digit/name was spoken correctly. Double-annotate all own held-out critical values and a stratified sample of training labels; adjudicate disagreement. Report exact-value agreement and boundary differences, not only a generic agreement percentage. Unresolvable audio receives an explicit ambiguity/exclusion disposition independent of model outputs.

**Output:** data cards, label guide, schema and documented annotation audit.

### Phase 3 — Exploratory and statistical analysis

Produce a compact set of readable figures, with complete supporting tables in CSV:

1. Corpus composition: turns, unique grouping IDs, hours, missing IDs and exclusions by source/split.
2. Entity counts/lengths and examples of digit, letter and punctuation confusions; report class imbalance.
3. English/Hinglish and read/spontaneous coverage; manually audit language flags. Never label a whole source code-mixed by assumption.
4. Duration, pauses within entities, pauses between entities, and true-end timing; distinguish source annotations from our additions.
5. Audio condition: rates/channels, clipping, silence and quality proxies. Any estimated SNR must include its estimator/limitations.
6. Split balance and overlap: speaker/session/template/entity duplication and augmentation lineage; show actual support per slice.

Statistical analysis will include medians/IQR and upper percentiles for duration/pause distributions; entity proportions and uncertainty intervals; and descriptive comparisons of pauses inside versus outside entities. Use speaker/conversation-cluster bootstrap where groups are known, keeping related turns and variants together. Do not treat every word, pause or noise variant as an independent participant. Report sample sizes and avoid demographic claims with sparse support.

M2 statistics describe data, not future model performance. The evaluation specification will predefine paired cluster bootstrap confidence intervals for the baseline/candidate accuracy difference in M3/M4. This avoids inventing model results to fill the statistical-analysis deliverable.

**Output:** reproducible EDA notebook, figure exports, distribution tables and statistical note.

### Phase 4 — Cleaning without destroying the problem

- Preserve source audio and transcripts; derive a documented 16 kHz mono representation where appropriate. Preserve channel separation if it identifies caller versus agent. Downsample/up-sample explicitly; upsampling telephone speech does not restore lost bandwidth.
- Flag corrupt, empty, inconsistent or clipped samples; log every exclusion. Do not discard difficult accents, pauses, disfluencies or incorrect-looking entities simply because they are hard.
- Keep verbatim, WER-normalised and canonical field references separately. Use Unicode/script-aware normalisation; preserve identity-bearing digits, letters and email punctuation. Do not apply fuzzy matching that makes a wrong ID pass.
- Preserve leading zeros. Convert spoken grouping forms only when unambiguous. Names need spelling-aware matching and explicit policies, not arbitrary anglicisation or a “valid name” regex.
- Do not trim the silences that define the endpointing task. Keep self-corrections and mark the final intended value. Never infer an unknown value from a plausible format.
- Deduplicate with hashes and metadata; investigate near duplicates and repeated prompts. Keep official benchmark membership intact for official scoring and record quality findings separately.

**Output:** reproducible preparation commands, clean manifests and row-level cleaning/exclusion log.

### Phase 5 — Splits and leakage prevention

- The new corpus supplies train/dev/test, grouped by speaker and session, with separate scenario-template families and fictional-value banks. Reject all detected cross-split derived-audio lineage or exact duplicate overlap.
- Split before adding noise/codec variants; all children remain with the base recording. Count original samples separately from augmented observations.
- Public test-only resources remain external benchmarks. Do not randomly repartition VoiceCodeBench to manufacture a training set. Do not tune on all of LiveKit's single validation release and then call it an unseen test.
- If using SpokenWOZ or IndicVoices development data, respect official splits and audit speaker/conversation overlap. If grouping metadata is absent, state the limit: sample-disjoint does not prove speaker-disjoint.
- Fit vocabularies, statistics, confidence thresholds and any learned normalisers on training data; choose parameters on development data only. Public benchmark prompt dictionaries are allowed only under the corresponding contextual protocol, never created from test answers.
- Restrict live endpoint decisions to audio and transcript context available at that time. Full gold transcripts, future words, entity end times and final corrected values are labels, not model inputs. Report reference-transcript benchmark conditions separately from real streaming-ASR conditions.
- Keep test labels outside the inference input export, freeze checksums, and record every evaluation run. Public pretrained-model contamination cannot be ruled out; fresh recordings reduce but do not eliminate all leakage concerns.

**Output:** frozen split manifests, explicit overlap report and data-validation checks. These checks are necessary because split integrity is an M2 requirement.

### Phase 6 — Privacy, handover and acceptance

Public availability is not a claim that audio is anonymous. Use licensed access, pseudonymous IDs and restricted raw audio. For new recordings obtain purpose-specific consent, including separate choices for redistribution and external API processing. Store consent/contact material separately; define retention and deletion handling before collection.

Use fictional names and mock order/reference IDs; use `example.com` emails and controlled test-number conventions. Random plausible phone/account numbers can belong to real people, so fictional prompts are never dialled or matched to real customer systems. Do not collect real bank/medical records. Redact report examples as needed without altering the evaluated audio/labels; a voice remains identifying even if its transcript is masked.

Publish code, aggregate statistics, permitted manifests and data-acquisition instructions; package raw audio only if its license and participant permissions allow it. Document a practical retention/deletion policy without claiming legal compliance certification.

M2 is ready when every accepted sample has valid provenance and schema, all splits/augmentations pass the overlap audit, label QC and exclusions are recorded, cards/EDA/statistics/privacy notes are complete, and a documented loader yields the frozen splits. Unresolved access or unknown grouping fields remain visible limitations, not a claim of absolute leak freedom.

**Output:** baseline-ready data package, short M2 report/deck, reproducibility instructions and acceptance checklist. Training remains M3.

## 6. What will be handed in

| Handbook item | Concrete evidence |
|---|---|
| Data card | Source-specific cards plus project data card and licenses/provenance manifest |
| Exploratory analysis | Executable notebook, six figure groups and supporting tables |
| Data cleaning | Preparation code/config, preserved raw references and cleaning ledger |
| Statistical analysis | Distribution summaries, uncertainty estimates and grouped-analysis methodology |
| Train/validation/test | Frozen grouped manifests and overlap/lineage audit |
| Privacy | Consent/collection protocol, access/retention policy and permitted-release statement |

Presentation target: **8 concise M2 slides/pages plus linked appendix material**: business/data need; source decision; data card; entity/language EDA; timing/audio EDA; cleaning; splits/statistics; privacy/readiness. Exact figures and counts will come from execution. The notebook and manifests provide technical depth without making the presentation long.

M1 stays a concise PDF after approved revisions. M2 should include a concise PDF **and** the reproducible preparation artifacts: a presentation alone cannot demonstrate a cleaned, split, baseline-ready dataset.

## 7. Practical workload and dependency gates

Planning estimate, not a promised deadline: 1 focused day for source/access/pilot setup; 1–2 for adapters/cards/cleaning; 1–2 for EDA/split/statistical audits; 1 for report and handover. Participant recruitment, recording and independent annotation can extend the schedule and run alongside preparation work.

M2 can largely run on CPU using bounded audio samples and metadata. Do not assume a GPU or paid APIs are available. Before later model runs, measure pilot runtime and storage, then estimate total ASR hours, realtime-paced benchmark duration, verifier calls, API cost and human review workload. τ-Entity voice evaluation uses caller/ASR/TTS/agent services and is an optional M3/M4 expansion, not a prerequisite for completing M2. Its task definitions can be inspected and documented without those paid runs. [Runtime requirements](https://github.com/sierra-research/tau2-bench/blob/main/docs/elicitation.md)

## Approval scope

The proposed approval is for: the focused support-intake workflow; the core public entity/timing benchmarks plus consented Indian-English/Hinglish corpus; conditional IndicContextEval access checking and documented fallbacks; the six M2 phases; and concise M1 evidence/metric revisions. Approval does not imply that participant voices already exist, that test results are known, or that any paid service has been purchased.
