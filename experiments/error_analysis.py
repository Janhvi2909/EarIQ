"""M4 error analysis: why is a value still wrong after EarIQ? (from results/entities_rows.jsonl)

  near_miss           a close version is there (>= 80% character similarity): a separator/format variant
                      ("8.30" for "8:30") or a one-letter slip ("Fernandez" for "Fernandes")
  misheard            nothing close to the value is in the output (misheard or missing)
  heard_not_formatted the spoken form is present but EarIQ did not turn it into the exact written value
  regression          normal AI had the exact value and EarIQ's rewrite broke it
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eariq.asr import merge_pieces  # noqa: E402
from eariq.normalize import detok, format_tokens  # noqa: E402
from src.listening_data import iter_supervised  # noqa: E402

ALNUM = lambda s: re.sub(r"[^0-9a-z]", "", s.lower())  # noqa: E731


def closeness():
    """Best character similarity between each entity's canonical value and any span of EarIQ's output."""
    hyps = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "results/asr/vcb_turbo.jsonl").open()}
    best = {}
    for inp, gold in iter_supervised("external_entity_test", allow_evaluation_labels=True):
        h = hyps[inp["id"]]
        toks = detok(format_tokens([w["word"] for w in merge_pieces(h["words"], h["text"])])).split()
        ents = gold["entities"] if isinstance(gold["entities"], list) else ast.literal_eval(gold["entities"])
        for e in ents:
            target, n = ALNUM(e["canonical"]), len(e["canonical"].split())
            score = 0.0
            for i in range(len(toks)):
                for k in range(1, n + 3):
                    score = max(score, SequenceMatcher(None, target, ALNUM("".join(toks[i:i + k]))).ratio())
            best.setdefault(inp["id"], []).append(score)
    return best


def category(r, close):
    if r["ours_strict"]:
        return None
    if r["base_strict"]:
        return "regression"
    if r["ours_lenient"] or r["base_lenient"]:
        return "heard_not_formatted"
    return "near_miss" if close >= 0.8 else "misheard"


def main():
    rows = [json.loads(l) for l in (ROOT / "results/entities_rows.jsonl").open()]
    close, seen = closeness(), Counter()
    for r in rows:  # rows are in the same per-recording entity order as the labels
        r["close"] = close[r["rec"]][seen[r["rec"]]]
        seen[r["rec"]] += 1
        r["cat"] = category(r, r["close"])
    wrong = [r for r in rows if not r["ours_strict"]]
    cats = Counter(r["cat"] for r in wrong)
    by_type = defaultdict(Counter)
    for r in wrong:
        by_type[r["type"]][r["cat"]] += 1
    n_type = Counter(r["type"] for r in rows)
    fixed = sum(1 for r in rows if r["ours_strict"] and not r["base_strict"])
    out = {"n_entities": len(rows), "n_wrong_after_eariq": len(wrong),
           "fixed_by_eariq": fixed, "broken_by_eariq": cats.get("regression", 0),
           "categories": {k: {"n": v, "share_of_errors": round(v / len(wrong), 3)} for k, v in cats.most_common()},
           "worst_types": [{"type": t, "n": n_type[t], "wrong": sum(c.values()),
                            "error_rate": round(sum(c.values()) / n_type[t], 3), **dict(c)}
                           for t, c in sorted(by_type.items(), key=lambda kv: -sum(kv[1].values()) / n_type[kv[0]])]}
    (ROOT / "results" / "error_analysis.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ("n_entities", "n_wrong_after_eariq", "fixed_by_eariq", "broken_by_eariq", "categories")}, indent=1))
    for w in out["worst_types"][:12]:
        print(w)


if __name__ == "__main__":
    main()
