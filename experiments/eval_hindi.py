"""Hindi / Hinglish contextual recognition (IndicContextEval Hindi, our speaker-grouped split).

Configs (same model, only the hint list changes):
  H0 no hints (baseline) | H5 clip's key-term list in Hindi script (L5) | H6 unrelated term list (L6, robustness)
Choose on a fixed validation subset; run the test split once with the baseline and the chosen config.
Metrics: WER, CER and borrowed-English-term error (share of tagged code-mixed terms missing from the output).
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import jiwer  # noqa: E402

from experiments.common import norm_hi, run_cached, terms_from_prompt  # noqa: E402
from experiments.log import log_run  # noqa: E402
from src.listening_data import iter_inputs, iter_supervised  # noqa: E402

VAL_N = 100
CONFIGS = {"H0_no_hints": None, "H5_key_terms": 5, "H6_unrelated_terms": 6}


def rows_for(split, n=None):
    gold = {g["id"]: g for _, g in iter_supervised(split, allow_evaluation_labels=True)}
    prompts = {lvl: {r["id"]: terms_from_prompt(r["context_prompt"]) for r in iter_inputs(split, context_level=lvl)}
               for lvl in (5, 6)}
    ids = sorted(gold)
    if n:
        ids = sorted(random.Random(20261125).sample(ids, n))
    return ids, gold, prompts


def term_pairs(tagged: str):
    """"प्रीटेस्ट (Pretest)" -> [("प्रीटेस्ट", "pretest")]"""
    return [(a, b.lower()) for a, b in re.findall(r"(\S+)\s*\(([^)]+)\)", tagged or "")]


def score(ids, gold, hyps):
    refs = [norm_hi(gold[i]["reference_nfc"]) for i in ids]
    hy = [norm_hi(hyps[i]["text"]) for i in ids]
    terms = hits = 0
    per = []
    for i, h in zip(ids, hy):
        pairs = term_pairs(gold[i].get("reference_with_tags"))
        t_hits = sum(norm_hi(a) in h or b in h for a, b in pairs)
        terms += len(pairs)
        hits += t_hits
        out = jiwer.process_words(norm_hi(gold[i]["reference_nfc"]), h or "∅")
        per.append((gold[i].get("speaker_group"), out.substitutions + out.deletions + out.insertions,
                    len(norm_hi(gold[i]["reference_nfc"]).split())))
    return {"n": len(ids), "wer": round(jiwer.wer(refs, [h or "∅" for h in hy]), 4),
            "cer": round(jiwer.cer(refs, [h or "∅" for h in hy]), 4),
            "term_error": round(1 - hits / terms, 4) if terms else None, "n_terms": terms}, per


def wer_diff_ci(per_a, per_b, n=2000):
    spk = defaultdict(list)
    for k, (s, _, _) in enumerate(per_a):
        spk[s].append(k)
    keys, rng, diffs = sorted(spk), random.Random(20261028), []
    for _ in range(n):
        rows = [k for s in rng.choices(keys, k=len(keys)) for k in spk[s]]
        wa = sum(per_a[k][1] for k in rows) / sum(per_a[k][2] for k in rows)
        wb = sum(per_b[k][1] for k in rows) / sum(per_b[k][2] for k in rows)
        diffs.append(wb - wa)
    diffs.sort()
    return [round(diffs[int(0.025 * n)], 4), round(diffs[int(0.975 * n)], 4)]


def run_config(tag, split, ids, gold, prompts, level):
    items = [(i, ROOT / gold[i]["audio_path"]) for i in ids]
    if level is None:
        return run_cached(f"hi_{split}_{tag}", items, language="hi")
    # prompts differ per clip -> transcribe clip by clip through the cache
    out = {}
    for i, a in items:
        out.update(run_cached(f"hi_{split}_{tag}", [(i, a)], language="hi", prompt=prompts[level][i] or None))
    return out


def main():
    t0 = time.time()
    res = {"validation_subset": {}, "test": {}}
    ids, gold, prompts = rows_for("validation", VAL_N)
    for tag, lvl in CONFIGS.items():
        res["validation_subset"][tag] = score(ids, gold, run_config(tag, "validation", ids, gold, prompts, lvl))[0]
    best = min((t for t in CONFIGS if t != "H6_unrelated_terms"),
               key=lambda t: res["validation_subset"][t]["wer"])
    res["chosen_on_validation"] = best
    ids, gold, prompts = rows_for("test")
    per = {}
    for tag in dict.fromkeys(["H0_no_hints", best]):
        res["test"][tag], per[tag] = score(ids, gold, run_config(tag, "test", ids, gold, prompts, CONFIGS[tag]))
    if best != "H0_no_hints":
        res["test"]["wer_diff_95ci_speaker_bootstrap"] = wer_diff_ci(per["H0_no_hints"], per[best])
    code_mixed = [i for i in ids if str(gold[i].get("code_mixing")) == "True"]
    res["test_code_mixed_slice"] = {tag: score(code_mixed, gold, run_config(tag, "test", code_mixed, gold, prompts, CONFIGS[tag]))[0]
                                    for tag in dict.fromkeys(["H0_no_hints", best])}
    (ROOT / "results" / "hindi.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    for split in ("validation_subset", "test"):
        for tag, m in res[split].items():
            if isinstance(m, dict):
                log_run("M4", "hindi_context", tag, f"IndicContextEval Hindi {split}", {"model": "large-v3-turbo"},
                        m, time.time() - t0)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
