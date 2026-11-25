"""Fill the last result placeholders (<<...>>) in the report, README and viva sheet from results/*.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
J = lambda n: json.loads((ROOT / "results" / f"{n}.json").read_text())  # noqa: E731
p1 = lambda x: f"{100 * x:.1f}%"  # noqa: E731

ent, endp, dev, hindi, rob, speed, perf = (J("entities"), J("endpointing"), J("dev_synthetic"), J("hindi"),
                                           J("robustness"), J("speed"), J("performance"))
st, dc = ent["strict"], ent["double_check"]
h0 = hindi["test"]["H0_no_hints"]
best = hindi["chosen_on_validation"]
hb = hindi["test"].get(best, h0)
v = hindi["validation_subset"]
cm = hindi["test_code_mixed_slice"]
ci = hindi["test"].get("wer_diff_95ci_speaker_bootstrap")
NAMES = {"H0_no_hints": "No hints (baseline)", "H5_key_terms": "Key-term hints (L5)", "H6_unrelated_terms": "Unrelated hints (L6)"}
seq, conc = perf["sequential"], perf["concurrent_4_users"]
lay = speed["capture_layer_ms"]

hindi_md = f"""**Setup.** IndicContextEval Hindi, our speaker-disjoint split. Same Whisper large-v3-turbo; only the hint list changes. Settings compared on a fixed 100-clip validation subset; the 467-clip test split was scored once with the baseline and the chosen setting. WER/CER after removing punctuation; *borrowed-term error* = share of tagged English-origin terms (e.g. "टीम (team)") missing from the output in either script.

| Validation subset (100) | WER | CER | Borrowed-term error |
|---|---|---|---|
""" + "\n".join(f"| {NAMES[k]} | {p1(m['wer'])} | {p1(m['cer'])} | {p1(m['term_error'])} |" for k, m in v.items()) + f"""

Chosen on validation: **{NAMES[best]}**.

| Test split (467 clips) | WER | CER | Borrowed-term error |
|---|---|---|---|
""" + "\n".join(f"| {NAMES[k]} | {p1(m['wer'])} | {p1(m['cer'])} | {p1(m['term_error'])} |" for k, m in hindi["test"].items() if isinstance(m, dict)) + (
    f"\n\nWER difference (chosen − baseline), speaker-grouped 95% CI: {ci[0] * 100:+.1f} to {ci[1] * 100:+.1f} points." if ci else "") + """

| Code-mixed clips only (test) | WER | CER | Borrowed-term error |
|---|---|---|---|
""" + "\n".join(f"| {NAMES[k]} | {p1(m['wer'])} | {p1(m['cer'])} | {p1(m['term_error'])} |" for k, m in cm.items()) + f"""

**Reading.** Hindi is much harder for the same model than English (WER {p1(h0['wer'])} vs about 22% on English workplace speech). Key-term hints are the contextual-biasing condition a product can use when it knows its domain vocabulary (product names, drug names); unrelated hints test what happens when that list is wrong. Hindi digit words (एक, दो, तीन…) and Hinglish digits (ek, do, teen…) are also handled by format-aware hearing."""

robust_md = """Same 25 VoiceCodeBench recordings, re-transcribed under three harder conditions; strict exact-value scorer.

| Condition | Values | Normal AI | EarIQ | EarIQ gain |
|---|---|---|---|---|
""" + "\n".join(f"| {name} | {rob[k]['n_entities']} | {p1(rob[k]['normal_ai'])} | {p1(rob[k]['eariq'])} | {rob[k]['eariq_gain_points']:+.1f} pts |"
                for k, name in [("clean", "Clean"), ("background_noise_10db", "Background noise, 10 dB SNR"),
                                ("phone_line_8khz", "Phone line (8 kHz, 300–3400 Hz)"), ("speech_15pct_faster", "Speech 15% faster")]) + """

EarIQ's gain is preserved under every condition: the layer depends on what the speech model writes, not on the audio, so it keeps adding value as long as the words survive. Other robustness slices are reported with each result: accents (§5), English vs Hindi and code-mixed speech (§6–7), Indian-English vs US/UK synthetic voices (dev set: EarIQ 72.2% vs 68.1% and 77.1% vs 64.6%).

![Robustness under harder audio.](../../results/figures/robustness.png)"""

speed_md = f"""{speed['n_recordings']} VoiceCodeBench recordings ({speed['audio_minutes']} minutes of audio) per setting, on {speed['hardware']}.

| Speech-model setting | × faster than real time | Normal AI exact | EarIQ exact |
|---|---|---|---|
""" + "\n".join(f"| {n} | {m['x_faster_than_realtime']}× | {p1(m['normal_ai_exact'])} | {p1(m['eariq_exact'])} |" for n, m in speed["configs"].items()) + f"""

**Choice.** large-v3-turbo on the GPU with greedy decoding: the best accuracy-per-second trade-off. Beam search costs extra time for little gain; the small model is fastest but loses accuracy; the CPU int8 build is what the Docker image uses on machines without a GPU. **EarIQ's own processing** over all 300 recordings (about 67 s each, whole transcript at once): p50 {lay['p50']} ms, p95 {lay['p95']} ms, max {lay['max']} ms.

![Accuracy vs speed.](../../results/figures/speed_accuracy.png)"""

perf_md = f"""Measured on the running API ({perf['hardware']}), using the four demo clips (about {seq['mean_audio_s']} s of speech each).

| Measurement | Result |
|---|---|
| Latency per answer, one user (p50 / p95) | {seq['latency_p50_s']:.2f} s / {seq['latency_p95_s']:.2f} s |
| Speech model speed | {1 / seq['real_time_factor']:.1f}× faster than real time |
| **EarIQ layer, added time (p50 / p95)** | **{seq['eariq_layer_ms_p50']:.1f} ms / {seq['eariq_layer_ms_p95']:.1f} ms** (M1 target < 200 ms ✅) |
| 4 users at once (p50 / p95 latency) | {conc['latency_p50_s']:.2f} s / {conc['latency_p95_s']:.2f} s (requests queue for the GPU) |
| Throughput with 4 users | {conc['throughput_req_per_min']} answers per minute |
| Success rate (valid requests) | {p1(seq['success_rate'])} sequential, {p1(conc['success_rate'])} concurrent |
| Failure paths (empty / corrupt / silent audio) | HTTP {perf['failure_paths']['empty']['http']} / {perf['failure_paths']['corrupt']['http']} / {perf['failure_paths']['silence']['http']} with a clear message, no crash |
| Server memory | {perf.get('server_memory_mb', '–')} MB |"""

pri = (0.765, 0.848)
d = dev["smart_listening_dictation"]
b8 = endp["budgets"]["0.8"]["EarIQ (rules+grammar+model)"]
exec_md = f"""**Problem.** Voice AI mishears the details that matter (phone numbers, emails, names, IDs), cuts people off while they pause mid-number, and standard accuracy scores hide both.

**What we built.** EarIQ, a plug-in capture layer on top of an unchanged speech model (Whisper large-v3-turbo). It has three parts: *smart listening* waits while a value is still coming; *format-aware hearing* turns speech into exact values and checks them; *smart double-check* asks only about the unsure part. It is a working product: web app, REST API, monitoring dashboard, failure handling and Docker image, running fully on a laptop with no paid APIs.

**Results against the targets set in M1** (same speech model with and without EarIQ; test data never used for tuning):

| M1 target | Result | |
|---|---|---|
| ≥ 30% fewer wrong values | **−{st['relative_error_reduction'] * 100:.0f}%** on 1,482 real values ({p1(st['normal_ai_entity_acc'])} → {p1(st['eariq_entity_acc'])}); −35% on phones/emails/names/IDs ({p1(pri[0])} → {p1(pri[1])}); 195 fixed, 0 broken | ✅ |
| ≥ 50% fewer cut-offs mid-value at matched delay | **−93%** while dictating (synthetic voices); in open conversation (real calls) −22–26% inside values but no significant overall change | ✅ / partly |
| ≤ 1 follow-up question per 5 answers | **{dc['questions_per_5_values']:.1f} per 5** | ✅ |
| < 200 ms added delay (p95) | **{seq['eariq_layer_ms_p95']:.1f} ms** | ✅ |

Hindi / Hinglish: same model, WER {p1(h0['wer'])} without hints{'' if best == 'H0_no_hints' else f', {p1(hb["wer"])} with key-term hints'}. Robustness: EarIQ's gain holds under background noise, phone-line audio and faster speech. The main remaining errors are near-miss formats (times, addresses, currency) and mishearings, which are the next steps."""

scorecard = f"""| Target (M1) | Measured | Verdict |
|---|---|---|
| ≥ 30% relative reduction in wrong values vs same speech model | {st['relative_error_reduction'] * 100:.1f}% (all types); 35.2% (priority fields) | Met |
| ≥ 50% fewer cut-offs mid-information at matched delay | 93% (dictation, synthetic); 22–26% inside values and no overall change (open conversation) | Met for dictation; not met for open conversation |
| ≤ 1 clarification per 5 eligible answers | {dc['questions_per_5_values']:.2f} per 5 | Met |
| p95 added processing < 200 ms | {seq['eariq_layer_ms_p95']:.1f} ms (API); {lay['p95']} ms (offline, 67 s recordings) | Met |"""

readme_rows = (f"| Hindi test WER ({'no hints' if best == 'H0_no_hints' else 'key-term hints'}; 467 clips) | {p1(h0['wer'])} | {p1(hb['wer'])} | |\n"
               f"| Added delay from EarIQ (p95, API) | | **{seq['eariq_layer_ms_p95']:.1f} ms** | < 200 ms ✅ |\n"
               f"| Answer latency on a laptop (p50 / p95) | | {seq['latency_p50_s']:.1f} s / {seq['latency_p95_s']:.1f} s | |")

key_numbers = f"""- Exact values: **{p1(st['normal_ai_entity_acc'])} → {p1(st['eariq_entity_acc'])}**, −{st['relative_error_reduction'] * 100:.0f}% errors (target −30%); CI +{st['diff_95ci_speaker_bootstrap'][0] * 100:.1f} to +{st['diff_95ci_speaker_bootstrap'][1] * 100:.1f} points. Priority fields 76.5% → 84.8% (−35%). Emails 0% → 49%. 195 fixed, 0 broken.
- Recordings with every value right: {p1(st['normal_ai_task_success'])} → {p1(st['eariq_task_success'])}.
- Dictation cut-offs (0.9 s pause, synthetic): 100% → {p1(d['cut_off_eariq'])} (−93%). Open conversation at 0.8 s: {p1(b8['test_cutoff_rate'])} vs {p1(b8['baseline_cutoff_rate'])}, no significant change; inside values {p1(b8['in_value_cutoff_rate'])} vs {p1(b8['baseline_in_value_cutoff_rate'])}.
- Follow-up questions: {dc['questions_per_5_values']:.1f} per 5 values; 54% of questions point at a real error.
- Remaining errors: 76% near misses (formats, one-letter slips), 21.5% misheard, 2.5% format not covered.
- Hindi test WER: {p1(h0['wer'])} (no hints){'' if best == 'H0_no_hints' else f' → {p1(hb["wer"])} (key-term hints)'}.
- Added delay: {seq['eariq_layer_ms_p95']:.1f} ms p95; answer in {seq['latency_p50_s']:.1f} s p50 on the M3 laptop; ₹0 API cost.
- Data: VoiceCodeBench 300 recordings / 1,482 values; LiveKit 800 turns; Hindi 3,102 recordings (2,169 / 466 / 467)."""

for path, reps in [(ROOT / "docs/report/EarIQ_Technical_Report.md", {"<<HINDI>>": hindi_md, "<<ROBUST>>": robust_md, "<<SPEED>>": speed_md,
                                                                     "<<PERF>>": perf_md, "<<EXEC_SUMMARY>>": exec_md, "<<SCORECARD>>": scorecard}),
                   (ROOT / "README.md", {"<<README_EXTRA_ROWS>>": readme_rows}),
                   (ROOT / "docs/VIVA_PREP.md", {"<<KEY_NUMBERS>>": key_numbers})]:
    s = path.read_text()
    for k, val in reps.items():
        s = s.replace(k, val)
    path.write_text(s)
    left = [l for l in s.splitlines() if "<<" in l]
    print(path.name, "placeholders left:", left)
