# EarIQ viva prep

## Key numbers (memorise these)

- Exact values: **57.6% → 70.8%**, −31% errors (target −30%); CI +11.1 to +15.2 points. Priority fields 76.5% → 84.8% (−35%). Emails 0% → 49%. 195 fixed, 0 broken.
- Recordings with every value right: 12.0% → 20.3%.
- Dictation cut-offs (0.9 s pause, synthetic): 100% → 6.8% (−93%). Open conversation at 0.8 s: 11.0% vs 11.2%, no significant change; inside values 18.9% vs 24.3%.
- Follow-up questions: 0.4 per 5 values; 54% of questions point at a real error.
- Remaining errors: 76% near misses (formats, one-letter slips), 21.5% misheard, 2.5% format not covered.
- Hindi test WER: 38.7% (no hints).
- Added delay: 0.9 ms p95; answer in 5.8 s p50 on the M3 laptop; ₹0 API cost.
- Data: VoiceCodeBench 300 recordings / 1,482 values; LiveKit 800 turns; Hindi 3,102 recordings (2,169 / 466 / 467).

## Who answers what

| Area | Owner | Files |
|---|---|---|
| Problem, capture layer (formatting, checks, double-check), exact-value evaluation, UI, report | Janhvi | `eariq/normalize.py`, `eariq/capture.py`, `experiments/eval_entities.py`, `app/static/` |
| Smart listening: endpointing rules, completion model, LiveKit evaluation, v1 → v2 | Ronit | `eariq/endpointing.py`, `eariq/vad.py`, `experiments/train_completion.py`, `experiments/eval_endpointing.py` |
| Hindi / Hinglish evaluation, robustness tests | Asmit | `experiments/eval_hindi.py`, `experiments/robustness.py` |
| API, monitoring, failure handling, Docker, performance and speed tests | Vaishnav | `app/server.py`, `app/static/monitor.*`, `Dockerfile`, `tests/test_capture_layer.py`, `experiments/speed.py`, `experiments/load_test.py` |

## Likely questions

**Q: What exactly is new here? Whisper already exists.**
A: We don't train a new speech model. EarIQ is a layer on top of any speech model that (1) turns spoken forms into the exact values software needs, (2) decides when the person has really finished, and (3) asks only about the unsure part. The baseline is the *same* Whisper run without the layer, so the measured gain is caused only by EarIQ.

**Q: Why rules for formatting instead of a neural model?**
A: Exact values need exact, predictable behaviour: "double five" must always become 55, and a missing digit must never be invented. Rules are transparent, fast (milliseconds) and testable. Where learning helps (deciding if a speaker is finished), we trained a model.

**Q: What did you actually train?**
A: A "has the speaker finished?" classifier: TF-IDF features (character 2–5-grams and word 1–2-grams over the last six words) with logistic regression. Trained on complete sentences vs sentences cut at a random word, from the Hindi train split plus English sentences; v2 is refit on real conversational pauses from the LiveKit development half.

**Q: How did you avoid tuning on the test set?**
A: The two external benchmarks are test-only. English rules and the confirm threshold were designed on a synthetic practice set; Hindi choices used the validation split; smart-listening v2 settings were chosen on a development half of LiveKit (split by conversation) and frozen before scoring the test half. The Hindi test split was used once.

**Q: Your numbers are lower than the published leaderboard. Why?**
A: The official scorer is a paid GPT-based verifier that accepts any recoverable form. Ours is strict: the exact written value must appear. Both systems are scored the same way, so the comparison is fair; the absolute numbers are just harsher. Also, the official setting forbids post-processing, so EarIQ is reported as a separate "with capture layer" condition, not a leaderboard entry.

**Q: Did smart listening meet its target?**
A: In dictation, where the agent knows it asked for a phone number, yes (see the key numbers). In open conversation on real LiveKit calls, it reduces cut-offs *inside values* but gives no significant overall gain over a fixed timeout at the same delay. v1 was actually worse, because it treated real turn endings after a number as unfinished; v2 fixed that with stricter rules and an in-domain model. We report this honestly.

**Q: How do you compare endpointing fairly?**
A: At the same *average* waiting time. A system that simply waits longer always cuts off less, so we fix the delay budget, choose settings on dev, and compare cut-offs on test against a fixed timeout set to exactly the same measured delay.

**Q: Why are confidence intervals "speaker-grouped"?**
A: Recordings from the same speaker are not independent. The bootstrap resamples whole speakers (or conversations), so the interval isn't falsely narrow.

**Q: What are the main remaining errors?**
A: Most are the speech model mishearing (for example "Fernandez" for "Fernandes"). No formatter can fix those, so the double-check exists to catch them. The rest are formats we don't cover yet (dates, times, addresses, currency). A few values are broken by our rewrite; we count and report those too.

**Q: Why does the demo pause detection use audio energy, not Whisper timestamps?**
A: Whisper stretches word boundaries across silences ("98765" then "-43210" starting immediately). Real endpointers measure silence in the audio, so we do too.

**Q: How is this deployed? What happens when it fails?**
A: A FastAPI service with a web UI and a Docker image. Inputs are validated (empty, corrupt, silent, too long), the speech model has a timeout, requests queue for the GPU and return "busy" past a limit, and if the capture layer ever fails it degrades to the plain transcript and asks again, never inventing a value. Each failure path has a unit test.

**Q: What do you monitor in production?**
A: p50/p95 latency, EarIQ layer time, error and fallback counts, ask-again and confirm rates (a rising rate signals audio or model drift), language mix, and user feedback on confirmations. Alerts fire on thresholds. No audio is stored and values are masked in logs.

**Q: Privacy?**
A: Licensed public datasets only, pseudonymous speaker IDs, raw audio not redistributed. All demo voices are synthetic and all values fictional. The app runs on-device, with no cloud speech API.

**Q: What would you do with more time?**
A: A pilot on consented Indian-English and Hinglish calls, streaming integration with a voice-agent platform, more format rules, re-ranking several speech-model hypotheses with format checks, and fine-tuning on the Hindi train split.
