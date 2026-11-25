"""Synthetic dev set (TTS, fictional values): design checks for the capture layer.

Used to (1) compare normal capture vs EarIQ per field, (2) choose the confirm threshold so that
EarIQ asks at most ~1 question per 5 turns, (3) measure smart listening while a value is being
dictated (agent knows which field it asked for), (4) accent slice: Indian vs US/UK voices.
Synthetic speech is far cleaner than real callers: these numbers are NOT real-world accuracy.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eariq import asr  # noqa: E402
from eariq.capture import baseline_capture, capture  # noqa: E402
from eariq.endpointing import DEFAULT_POLICY, simulate  # noqa: E402
from experiments.log import log_run  # noqa: E402

INDIAN = {"Aman", "Rishi", "Tara"}


def norm(field, v):
    if v is None:
        return None
    if field == "phone":
        return re.sub(r"\D", "", v)[-10:]
    if field == "email":
        return v.lower().strip(".")
    return re.sub(r"\s+", " ", v).strip(" .").casefold()


def transcribe_all(rows, out):
    done = {}
    if out.exists():
        done = {json.loads(l)["id"]: json.loads(l) for l in out.open()}
    with out.open("a") as f:
        for r in rows:
            if r["id"] not in done:
                res = asr.transcribe(str(ROOT / r["audio_path"]), language="en")
                res["id"] = r["id"]
                f.write(json.dumps(res) + "\n")
                done[r["id"]] = res
    return done


def main(confirm_below=None):
    t0 = time.time()
    rows = [json.loads(l) for l in (ROOT / "data/synthetic/dev_manifest.jsonl").open()]
    hyp = transcribe_all(rows, ROOT / "results/asr/dev_turbo.jsonl")
    recs = []
    for r in rows:
        h = hyp[r["id"]]
        h["words"] = asr.merge_pieces(h["words"], h["text"])
        e = capture(h["words"], r["field"])
        b = baseline_capture(h["text"], r["field"])
        min_conf = e["confidence"] if e["confidence"] is not None else 0.0
        cut_base, _ = simulate(h["words"], {"fixed": DEFAULT_POLICY["short"]}, r["field"])
        cut_ours, _ = simulate(h["words"], DEFAULT_POLICY, r["field"])
        recs.append({"id": r["id"], "field": r["field"], "indian": r["voice"] in INDIAN,
                     "pause": r["pause_in_value"],
                     "base_ok": norm(r["field"], b["value"]) == norm(r["field"], r["gold"]),
                     "ours_ok": norm(r["field"], e["value"]) == norm(r["field"], r["gold"]),
                     "valid": e["action"] != "ask", "conf": min_conf,
                     "cut_base": cut_base is not None, "cut_ours": cut_ours is not None})

    def acc(sub, k):
        return round(sum(x[k] for x in sub) / len(sub), 3) if sub else None

    res = {"n": len(recs), "by_field": {}, "by_accent": {}}
    for f in ["phone", "email", "name", "id"]:
        sub = [x for x in recs if x["field"] == f]
        res["by_field"][f] = {"n": len(sub), "normal_ai": acc(sub, "base_ok"), "eariq": acc(sub, "ours_ok")}
    for name, sub in [("indian_english_voices", [x for x in recs if x["indian"]]),
                      ("us_uk_voices", [x for x in recs if not x["indian"]])]:
        res["by_accent"][name] = {"n": len(sub), "normal_ai": acc(sub, "base_ok"), "eariq": acc(sub, "ours_ok")}
    res["overall"] = {"normal_ai": acc(recs, "base_ok"), "eariq": acc(recs, "ours_ok")}

    # confirm threshold: ask about values below tau; pick the largest tau with <= 20% confirmations
    sweep = []
    for tau in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        asked = [x for x in recs if x["valid"] and x["conf"] < tau]
        wrong = [x for x in recs if x["valid"] and not x["ours_ok"]]
        caught = [x for x in wrong if x["conf"] < tau]
        sweep.append({"tau": tau, "confirm_rate": round(len(asked) / len(recs), 3),
                      "wrong_values_caught": round(len(caught) / len(wrong), 3) if wrong else None})
    res["confirm_threshold_sweep"] = sweep
    ok = [s for s in sweep if s["confirm_rate"] <= 0.2]
    res["chosen_confirm_below"] = max(ok, key=lambda s: s["tau"])["tau"] if ok else 0.3

    paused = [x for x in recs if x["pause"]]
    fluent = [x for x in recs if not x["pause"]]
    res["smart_listening_dictation"] = {
        "policy": DEFAULT_POLICY, "baseline_fixed_timeout_s": DEFAULT_POLICY["short"],
        "clips_with_pause_in_value": len(paused),
        "cut_off_normal_ai": acc(paused, "cut_base"), "cut_off_eariq": acc(paused, "cut_ours"),
        "fluent_clips_cut_off_normal_ai": acc(fluent, "cut_base"), "fluent_clips_cut_off_eariq": acc(fluent, "cut_ours")}
    (ROOT / "results" / "dev_synthetic.json").write_text(json.dumps(res, indent=2))
    log_run("M3", "capture_layer", "normal_ai_vs_eariq", "synthetic TTS dev set (120)", {},
            {"overall": res["overall"], "by_accent": res["by_accent"],
             "dictation_cutoffs": res["smart_listening_dictation"]}, time.time() - t0,
            notes="synthetic speech; design/tuning only")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
