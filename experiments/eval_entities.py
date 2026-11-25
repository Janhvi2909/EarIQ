"""Exact-value evaluation on VoiceCodeBench (300 recordings, 1,482 entities, external test only).

Systems (same audio, same Whisper run, so the difference is only the capture layer):
  normal AI  = Whisper large-v3-turbo transcript as-is
  EarIQ      = the same words through EarIQ's format-aware layer
Scorers (our free, deterministic stand-in for the paid LLM verifier; see report):
  exact value (strict) = the canonical value (what software needs) appears in the output
  recoverable (lenient) = canonical OR the spoken (acoustic) form appears
Matching ignores case and spaces; numeric IDs/phones also ignore separators (212-555-0100 == 2125550100).
Note: VoiceCodeBench's official setting forbids post-processing; "EarIQ" is reported as a separate
with-capture-layer condition, never as a leaderboard entry.
"""
from __future__ import annotations

import ast
import json
import random
import re
import sys
import time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import jiwer  # noqa: E402

from eariq.asr import merge_pieces  # noqa: E402
from eariq.capture import CONFIRM_BELOW, find_values  # noqa: E402
from eariq.normalize import detok, format_tokens  # noqa: E402
from experiments.log import log_run  # noqa: E402
from src.listening_data import iter_supervised  # noqa: E402

LOOSE = {"phone_number", "phone_extension", "account_or_record_number", "plain_number", "port_number"}
EDGE = ".,;:!?\"'()"
PUBLISHED_WHISPER_LARGE_V3 = {"CTEM": 0.876, "TSR": 0.543, "WER": 0.058, "source": "VoiceCodeBench paper, Table 6 (LLM verifier, hosted)"}


def key(s: str, typ: str) -> str:
    s = s.casefold().strip(EDGE)
    s = re.sub(r"\s+", "", s)
    return re.sub(r"[^0-9a-z]", "", s) if typ in LOOSE else s


def found(tokens: list[str], target: str, typ: str) -> bool:
    k = key(target, typ)
    if not k:
        return False
    maxn = min(len(target.split()) + 4, 45)
    for i in range(len(tokens)):
        acc = ""
        for n in range(maxn):
            if i + n >= len(tokens):
                break
            acc += tokens[i + n]
            kk = key(acc, typ)
            if kk == k:
                return True
            if len(kk) > len(k) + 8:
                break
    return False


def ref_tokens(template: str, ents: dict):
    """Reference acoustic tokens + span of each entity, from the template."""
    toks, spans = [], {}
    for part in re.split(r"(<[^>]+>)", template):
        if part.startswith("<") and part[1:-1] in ents:
            a = len(toks)
            toks += ents[part[1:-1]]["acoustic"].split()
            spans[part[1:-1]] = (a, len(toks))
        else:
            toks += part.split()
    return toks, spans


def _n(w):
    return re.sub(r"[^\w@]", "", w.lower())


def entity_regions(template, ents, hyp_words):
    ref, spans = ref_tokens(template, ents)
    hyp = [_n(w["word"]) for w in hyp_words]
    m = defaultdict(set)
    for op, a1, a2, b1, b2 in SequenceMatcher(None, [_n(w) for w in ref], hyp, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                m[a1 + k].add(b1 + k)
        elif op == "replace":
            for a in range(a1, a2):
                m[a].update(range(b1, b2))
    return {eid: set().union(*[m[i] for i in range(a, b)]) if b > a else set() for eid, (a, b) in spans.items()}


def grouped_bootstrap(groups, vals_a, vals_b, n=2000, seed=20261028):
    ids = sorted(set(groups))
    idx = defaultdict(list)
    for i, g in enumerate(groups):
        idx[g].append(i)
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        rows = [i for g in rng.choices(ids, k=len(ids)) for i in idx[g]]
        diffs.append(sum(vals_b[i] - vals_a[i] for i in rows) / len(rows))
    diffs.sort()
    return [round(diffs[int(0.025 * n)], 4), round(diffs[int(0.975 * n)], 4)]


def entity_rows(hyps: dict, keep_regions=True):
    """One row per gold entity: was it exact (strict) / recoverable (lenient) for normal AI and EarIQ?"""
    E, wer_ref, wer_hyp = [], [], []
    for inp, gold in iter_supervised("external_entity_test", allow_evaluation_labels=True):
        if inp["id"] not in hyps:
            continue
        h = hyps[inp["id"]]
        words = merge_pieces(h["words"], h["text"])
        toks = format_tokens([w["word"] for w in words])
        base_tokens = h["text"].split()
        ours_tokens = detok(toks).split()
        ents = gold["entities"] if isinstance(gold["entities"], list) else ast.literal_eval(gold["entities"])
        byid = {e["id"]: e for e in ents}
        regions = entity_regions(gold["template"], byid, words) if keep_regions else {}
        flagged = [set(v.src) for v in find_values(toks, words) if v.confidence < CONFIRM_BELOW or not v.valid]
        for e in ents:
            row = {"rec": inp["id"], "spk": gold.get("speaker_group") or inp["id"], "type": e["type"],
                   "domain": gold.get("domain"), "accent": gold.get("accent"), "difficulty": gold.get("difficulty")}
            for sysname, tk in (("base", base_tokens), ("ours", ours_tokens)):
                row[f"{sysname}_strict"] = found(tk, e["canonical"], e["type"])
                row[f"{sysname}_lenient"] = row[f"{sysname}_strict"] or found(tk, e["acoustic"], e["type"])
            reg = regions.get(e["id"], set())
            row["flagged"] = any(reg & f for f in flagged)
            E.append(row)
        wer_ref.append(re.sub(r"[^\w\s]", " ", gold["reference_nfc"].lower()))
        wer_hyp.append(re.sub(r"[^\w\s]", " ", h["text"].lower()))
    return E, wer_ref, wer_hyp


def main(asr_name="vcb_turbo"):
    t0 = time.time()
    hyps = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "results/asr" / f"{asr_name}.jsonl").open()}
    E, wer_ref, wer_hyp = entity_rows(hyps)

    def rate(rows, k):
        return round(sum(r[k] for r in rows) / len(rows), 4) if rows else None

    def tsr(rows, k):
        rec = defaultdict(list)
        for r in rows:
            rec[r["rec"]].append(r[k])
        return round(sum(all(v) for v in rec.values()) / len(rec), 4)

    res = {"n_recordings": len({r["rec"] for r in E}), "n_entities": len(E), "asr": asr_name,
           "wer_normal_ai": round(jiwer.wer(wer_ref, wer_hyp), 4), "published_reference": PUBLISHED_WHISPER_LARGE_V3}
    for metric in ("strict", "lenient"):
        b, o = rate(E, f"base_{metric}"), rate(E, f"ours_{metric}")
        res[metric] = {"normal_ai_entity_acc": b, "eariq_entity_acc": o,
                       "normal_ai_task_success": tsr(E, f"base_{metric}"), "eariq_task_success": tsr(E, f"ours_{metric}"),
                       "relative_error_reduction": round(1 - (1 - o) / (1 - b), 4) if b < 1 else None,
                       "diff_95ci_speaker_bootstrap": grouped_bootstrap([r["spk"] for r in E],
                                                                        [r[f"base_{metric}"] for r in E],
                                                                        [r[f"ours_{metric}"] for r in E])}
    res["by_type"] = {t: {"n": len(rows), "normal_ai": rate(rows, "base_strict"), "eariq": rate(rows, "ours_strict")}
                      for t in sorted({r["type"] for r in E}) for rows in [[r for r in E if r["type"] == t]]}
    res["by_accent"] = {a: {"n": len(rows), "normal_ai": rate(rows, "base_strict"), "eariq": rate(rows, "ours_strict")}
                        for a in sorted({str(r["accent"]) for r in E}) for rows in [[r for r in E if str(r["accent"]) == a]]}
    res["by_difficulty"] = {a: {"n": len(rows), "normal_ai": rate(rows, "base_strict"), "eariq": rate(rows, "ours_strict")}
                            for a in sorted({str(r["difficulty"]) for r in E}) for rows in [[r for r in E if str(r["difficulty"]) == a]]}
    wrong = [r for r in E if not r["ours_strict"]]
    flagged = [r for r in E if r["flagged"]]
    res["double_check"] = {
        "confirm_below": CONFIRM_BELOW,
        "questions_per_5_values": round(5 * len(flagged) / len(E), 3),
        "wrong_values_caught": round(sum(r["flagged"] for r in wrong) / len(wrong), 4) if wrong else None,
        "flagged_that_were_wrong": round(sum(not r["ours_strict"] for r in flagged) / len(flagged), 4) if flagged else None,
        "always_confirm_questions_per_5_values": 5.0}
    out_dir = ROOT / "results"
    (out_dir / "entities.json").write_text(json.dumps(res, indent=2))
    with (out_dir / "entities_rows.jsonl").open("w") as f:
        for r in E:
            f.write(json.dumps(r) + "\n")
    log_run("M4", "exact_values", "whisper_turbo_vs_eariq_layer", f"VoiceCodeBench ({res['n_recordings']} rec)",
            {"asr": asr_name, "confirm_below": CONFIRM_BELOW},
            {"strict": res["strict"], "lenient": res["lenient"], "double_check": res["double_check"], "wer": res["wer_normal_ai"]},
            time.time() - t0)
    print(json.dumps({k: res[k] for k in ("n_recordings", "n_entities", "wer_normal_ai", "strict", "lenient", "double_check")}, indent=1))
    return res


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "vcb_turbo")
