# M1 — presentation pointers

## Slide 1 · Opening

- **Voice AI talks well; listening remains unreliable.** Our project: **entity-aware capture layer + evaluation**.

## Slide 2 · Problem brief

- **Mishears** names/numbers/emails/IDs → **cuts off** incomplete information → **hides errors** behind average accuracy.
- **One wrong digit can break the outcome**; the prescription/ID example is **illustrative**.
- **WER weights words equally**; add **exact critical-information correctness**.

## Slides 3–4 · Research evidence

- **Voice of India:** **295.9% WER**, Gujarati, **GPT-4o Mini Transcribe**, Apr 2026. Benchmark-specific extreme; insertions explain >100%. **Closed-source** — motivation, not our reproducible dataset.
- **AssemblyAI survey:** **55%** identify repeating themselves as their leading frustration — a **survey finding**.
- **VoiceCodeBench:** Nova-3 batch **90.9% entity recovery**, but **68.7% all-entity success** in its frozen paper.
- **Correction while speaking:** avoid the unverified **10–20% CEO estimate**, **PolyAI 6.4%**, or universal **“2× for every model”** claim.

## Slide 5 · Domain and users

- **Broad scope:** **assistants, mic dictation, voice search, agents and enterprise platforms** — every product receiving speech.
- **Primary users:** speech/voice-AI engineers and product teams — **Sarvam, Bolna, Vapi-type platforms**.
- **Business customers:** banking, healthcare, commerce, travel, productivity. **End users:** people speaking in different accents/languages.
- **India focus:** Indian English, **Hinglish**, regional names and local formats; extend after validation.
- **Context matters:** abbreviations depend on **language, locale and intended meaning**. Expansion is also a **normalisation** problem; acoustics alone cannot resolve every ambiguity.

## Slides 6–7 · Existing solutions and opportunity

- **Flux:** ASR + turn detection; **LiveKit:** timing; **Sarvam:** Indic speech/keyterms; **Sierra τ-Entity:** capture/repair benchmarking.
- **Our question:** can **entity completeness + uncertainty + context** improve listening/commit/clarification decisions beyond existing capabilities?
- **Business objective:** information correct **first time**, fewer repeats/corrections/handoffs, acceptable delay. **Plug-in layer**, not a foundation model.

## Slide 8 · NLP task and solution

- **Input:** speech stream + partial transcripts + timing + available context.
- **Output:** **canonical value** and **keep listening / commit / clarify** decision.
- **Smart listening** through incomplete entities; **field-aware validation**; **targeted confirmation** of uncertain parts.
- **Valid format ≠ correct value**; no universal regex for names; **never invent** missing information.
- Evaluation slices make the broad problem measurable; **call centres are one example**, not the project boundary.

## Slide 9 · Metrics and feasibility

- **Exact field accuracy:** correct values / required values; missing/wrong values fail.
- Proposed **30% relative field-error reduction** vs **same ASR without our layer** — 80% → 86% accuracy.
- Proposed **50% fewer cutoffs at matched endpoint delay**; **≤1 clarification per 5 eligible turns**.
- Proposed **p95 added processing overhead <200 ms**; report listening/clarification delay separately. **Targets, not results**.
- **Business proxy:** required values correct in a downstream record/action; real savings need a pilot.
- **Feasibility:** licensed speech, existing ASR/VAD, lightweight decisions. **Risks:** labels, streaming control, latency, language coverage.
- **Privacy:** public audio is not anonymous; restricted access, licenses, **consent for new recordings**, fictional identifiers.

## Slide 10 · Roadmap and close

- **M1:** problem/users/objective/metrics/feasibility. **M2:** clean documented data/splits. **M3–M6:** models → evaluation → deployment → demo.
- **“We're not building a voice AI that talks better. We're building one that listens better.”**

**Source cues:** [Voice of India](https://arxiv.org/html/2604.19151v1) · [AssemblyAI survey](https://www.assemblyai.com/voice-agent-report) · [VoiceCodeBench, Table 6](https://arxiv.org/html/2608.28916v1) · [Flux](https://developers.deepgram.com/docs/flux/quickstart) · [LiveKit](https://github.com/livekit/eot-bench) · [Sarvam](https://www.sarvam.ai/blogs/introducing-saaras-v4) · [τ-Entity](https://sierra.ai/blog/tau-entity-can-voice-agents-get-the-details-right)

*PDF unchanged; pointers clarify evidence, scope and metric definitions.*
