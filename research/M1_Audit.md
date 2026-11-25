# M1 audit: Voice AI capture layer

> **Scope update:** the user chose to keep the PDF unchanged and retain broad voice-AI scope (assistants, dictation and agents). Recommendations below are historical review notes; the current speaking flow is `M1 script.md`. Support intake is an example, not the product boundary.

Reviewed 28 October 2026. This is a review and proposed revision, not an edited presentation. Both original PDFs remain unchanged.

## Verdict

**All five M1 deliverable headings are present. M1 is structurally covered, but several statements and measurement definitions need tightening before submission.** A major expansion is unnecessary. Keep the visual style and approximately ten slides; replace weak evidence and sharpen slides 6, 8 and 9. Add at most one references slide with clickable sources.

The handbook's industry requirements are on PDF page 6; its industry checklist is on page 9. For M2, use the union of both: the detailed description explicitly includes statistical analysis, and the checklist explicitly includes train/validation/test splits. Model implementation and baseline results belong to industry M3, not M2.

## Requirement-by-requirement check

| Handbook requirement | Evidence in your PDF (physical page) | Assessment | Smallest useful change |
|---|---|---|---|
| Problem brief | p2: mishearing, cutoffs, WER limitations; p8: proposed capture layer | Present, scope too broad | State one initial workflow, languages, entity types, input and output. |
| User identification | p9: primary builders; secondary enterprises; end users | Present | Identify the actual builder persona: voice-agent engineer/product owner responsible for caller intake. Named companies are target examples, not validated customers. |
| Business objective | p9: first-try completion, fewer repeats/handoffs, low delay | Present | Define a measurable proxy: correct required fields committed in a mock intake record. Production revenue or handoff savings remain hypotheses until measured. |
| Success metrics | p9: 30% accuracy improvement, 50% fewer cutoffs, confirmations and latency | Present, ambiguous | Specify formulas, denominator, baseline, evaluation conditions and latency percentile. Treat all thresholds as proposed targets. |
| Feasibility analysis | p9: public data, open models, compute, risks | Present, currently optimistic | Distinguish available labels from labels we must create; identify licenses, streaming access and human annotation as dependencies. Replace the free-GPU guarantee with a bounded plan. |

The deck's industry research is visible in its company examples and quotations. However, footer labels such as “company blogs” and “PolyAI podcast” do not let an examiner locate the evidence. A few strong, dated links will add more credibility than additional unsupported statistics.

## Proposed project definition

> Build an entity-aware capture layer for customer-support intake voice agents. Starting with Indian English and Hindi–English code-mixed speech, it uses incremental speech recognition, the requested field type and conversational context to decide whether to keep listening, accept a captured value, or ask a focused clarification. Evaluate names, phone numbers, emails and order/reference IDs using exact field correctness, premature cutoffs, clarification burden and response delay.

Initial business scenario: a support callback that records a customer's name, callback number, email and order/reference ID in a mock CRM. This retains your business domain while giving the project a bounded, demonstrable outcome. Banking and healthcare can remain motivation examples rather than additional implementation domains.

## Claims that need attention

| Page / existing claim | Research finding | Proposed treatment |
|---|---|---|
| p2: RX-7704132 becomes RX-7704182 | A useful illustrative failure. The deck does not establish this as a documented customer incident. | Label “illustrative example”; provide an exact source only if the same example appears there. Explain that one important error can be diluted by a longer transcript. |
| p3: 295.9 WER for GPT-4o mini on Gujarati | Confirmed in Voice of India, Table 2(a), specifically **GPT-4o Mini Transcribe**. WER can exceed 100% because insertions count. The paper calls the benchmark closed-source. | Write “295.9% WER, Gujarati, GPT-4o Mini Transcribe, Voice of India, Apr 2026.” This is an extreme result in that setting, not a universal score for current systems or proof about Hinglish. [Paper](https://arxiv.org/html/2604.19151v1) |
| p3: critical-word errors are over twice WER “for every top model” | Current AssemblyAI material supports entity-sensitive evaluation, but I did not verify that universal multiplier under the deck's unspecified model/date/protocol. | Replace with a directly attributable exact-capture result below. [AssemblyAI metric documentation](https://www.assemblyai.com/docs/streaming/benchmarks) |
| p3: GPT-4o interrupts too eagerly | Talking Turns supports turn-taking problems in systems evaluated at that time. | Cite the paper and its 2025 evaluation setting; avoid presenting the result as a test of every current model. [ICLR paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/82f68b38747c406672f7f9f6bab86775-Paper-Conference.pdf) |
| p3: 55% dislike repeating themselves | Supported as an AssemblyAI survey finding. | Keep with “AssemblyAI survey”; identify the surveyed population and avoid generalising it to all users. [Report](https://www.assemblyai.com/voice-agent-report) |
| p4: LiveKit and Deepgram quotations | Their first-party material clearly describes premature turn endings as a major challenge. Exact quotation wording still needs the original linked post. | Prefer short attributed paraphrases with clickable links. [LiveKit](https://livekit.com/blog/solving-end-of-turn-detection), [Deepgram Flux launch](https://deepgram.com/learn/introducing-flux-conversational-speech-recognition) |
| p4: Deepgram CEO estimate of 10–20% misunderstood turns | Not independently verified to a precise source/timestamp in this review. | Remove unless the exact talk/post and timestamp can be attached. Do not replace it with a different statistic about missing transcript tails. |
| p4: PolyAI 6.4% vs 2–3% | Not independently verified to the named podcast episode and methodology. | Remove or supply the exact source/timestamp and evaluation scope. The project already has stronger reproducible evidence. |
| p5: $47.5B by 2034; 8× funding in 2025 | AssemblyAI's report instead states $47.5B by **2032** and an 8× funding increase in **2024**. Different market reports can use different definitions. | Do not mix dates from distinct sources. Prefer removing these figures: they are less relevant than field-capture failure and not needed for M1. [Report](https://www.assemblyai.com/voice-agent-report) |
| p5: ElevenLabs valuation/funding | Not independently checked against the financing announcement in this review. | Omit unless a direct dated announcement is attached; valuation does not establish the listening problem. |
| p6: hearing and timing are “never both together” | Too absolute: Flux already integrates transcription and turn detection. | Replace with a narrower, testable question: can field completeness improve capture decisions beyond a strong general turn detector? [Flux docs](https://developers.deepgram.com/docs/flux/quickstart) |
| p6: benchmarks score words rather than outcomes | Too absolute as of this review. Exact entity and repair benchmarks now exist. | Say “WER alone misses field-capture failures.” Position our benchmark as a focused Indian-English/Hinglish extension and integrated diagnostic. [τ-Entity](https://sierra.ai/blog/tau-entity-can-voice-agents-get-the-details-right) |
| p6: LiveKit 85% fewer interruptions | Historical vendor/employee material supports this as a reported figure, but it is not a universal production guarantee or our baseline. | Prefer versioned eot-bench results; otherwise retain the original model/date/comparator. [Historical employee post](https://www.linkedin.com/posts/kmashhoon_the-livekit-team-is-on-ive-experienced-activity-7282128117253447681-rPWy) |
| p8: valid names and Hindi words have a format | Names and unrestricted vocabulary do not have reliable regex validity rules. A valid-looking number can still be wrong. | Use “field-aware validation and candidate selection.” Constrain structured fields; preserve acoustic evidence and ask when a name is uncertain. |
| p8: capture layer follows a completed speech-model output | Endpointing must influence the live stream before premature finalisation occurs. Some APIs expose insufficient control. | Show the layer receiving partial transcripts and audio timing, and controlling commit/clarification decisions alongside ASR. |
| p9: public data plus “fake data only” solves privacy | Public speech can still contain identifiable voices or content. | Say “licensed public speech; consented new recordings with fictional field values; controlled audio access.” |
| p9: small models/free GPUs are enough | Plausible for a limited prototype, unmeasured for streaming, large ASR or multiple paid benchmarks. | Limit to frozen ASR plus a lightweight decision layer; benchmark a pilot, document hardware and API cost dependencies. |

## Better evidence for a compact deck

Use two or three of these, not every number:

1. **Exact capture:** VoiceCodeBench's frozen paper reports Deepgram Nova-3 batch at 90.9% entity recovery but only 68.7% of recordings with every entity recovered. That is particularly relevant to a multi-field intake workflow. It is a benchmark-author measurement, not a Deepgram production guarantee. [Paper, Table 6](https://arxiv.org/html/2608.28916v1)
2. **Repair versus delay:** Sierra's September paper reports 14–41% robust exact success across tested voice configurations; a prescribed verification protocol improves results but adds 21–28 seconds per call. This motivates selective clarification. These are simulated caller experiments, not customer traffic. [Paper](https://arxiv.org/html/2609.13602v1)
3. **Industry relevance to India:** Sarvam explicitly evaluates on Indian speech benchmarks and supports keyterm prompting. Existing capability is the comparator; the question is whether our layer adds measurable benefit on exact intake fields. [Saaras V4 announcement](https://www.sarvam.ai/blogs/introducing-saaras-v4)

Do not claim this is the first entity-aware voice system or the first entity benchmark. The defensible contribution is a measured integration and a carefully scoped Indian-English/Hinglish evaluation.

## Proposed metric wording for slide 9

These definitions are recommendations to approve, not results or changes already made to the PDF.

| Metric | Definition / proposed target |
|---|---|
| Exact field capture | Correct canonical field values / all required gold fields; omissions and wrong values fail. Report each entity type and language separately. |
| Capture improvement | Propose **at least 30% relative reduction in field error**, compared with the same ASR and workflow without our layer. Example: 80% accuracy becomes 86%, because error falls from 20% to 14%. This explicitly revises the ambiguous “30% accuracy” wording. |
| Premature cutoff | Turns committed before the caller has finished / eligible turns; separately report cutoffs within an entity span. Target 50% relative reduction at a matched endpoint-delay budget. |
| Clarification burden | Extra clarification questions / eligible intake turns; proposed target ≤0.2. Also report final accuracy, retries and unrecovered errors so asking less cannot hide failure. |
| Added processing delay | Proposed p95 incremental capture-layer processing overhead <200 ms on named hardware, under a stated concurrency. Measure listening delay, ASR/network delay and time spent clarifying separately; also report total endpoint delay. |
| Business proxy | Percentage of mock intake records with all required fields correct, with no correction needed after commit. This is not evidence of real revenue or handoff savings. |

All targets should be fixed before final test evaluation. Pilot feasibility findings may lead to a documented revision before M3 experiments; they must never be rewritten after seeing test scores.

## Minimal slide revision plan

- **p1–2:** preserve opening and three failure modes; label the example correctly.
- **p3–4:** retain the strongest dated evidence, replace untraceable statistics with exact-capture/repair evidence and clickable attribution.
- **p5:** keep the company/use-case map; shrink or remove market valuation figures.
- **p6:** accurately acknowledge integrated ASR/turn detection and existing entity benchmarks; state the remaining experimental question.
- **p7:** keep motivation; change “doable” into a bounded prototype commitment.
- **p8:** show incremental input, field state, keep-listening/commit/clarify outputs; distinguish candidate reranking from true constrained decoding.
- **p9:** use the narrower workflow, precise proposed targets and realistic data/privacy dependencies.
- **p10:** retain the roadmap and closing line.
- **Optional p11:** a concise linked references slide. Include only evidence actually used in the deck.

No extra literature survey is required for industry M1. No final M1 PDF has been produced at this planning stage.
