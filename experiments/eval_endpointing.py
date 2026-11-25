"""Smart listening evaluation on the external LiveKit timing set (800 English/Hindi turns).

At every pause the policy sees only words spoken before it (punctuation stripped) and the agent's
previous message. A hold pause longer than the policy's wait = false cut-off. Delay = the wait
applied at the true end of the turn.

v2 protocol: conversations are split 50/50 (seeded, balanced by turns) into a DEV half (design,
in-domain model training, setting selection) and a TEST half (reported). Settings are chosen on
DEV for each delay budget, then frozen. The baseline on TEST uses a fixed timeout equal to EarIQ's
measured TEST delay, so both are compared at exactly the same average wait.
(v1 = first design on all 800 turns, kept in results/endpointing_v1.json.)
"""
from __future__ import annotations

import ast
import json
import pickle
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.base import clone  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402

from eariq.endpointing import MODEL_PATH, MODEL_V2_PATH, clean, expected_field, hanging, prefix_text, value_in_progress  # noqa: E402
from eariq.normalize import DIGIT_WORDS, TEENS, TENS  # noqa: E402
from experiments.log import log_run  # noqa: E402
from src.listening_data import iter_supervised  # noqa: E402

NUMERIC = set(DIGIT_WORDS) | set(TEENS) | set(TENS)
BUDGETS = [0.5, 0.8, 1.0]
SEED = 20261125
METHODS = {
    "entity_rules": {"rules": True, "hanging": False, "model": False},
    "entity_rules+grammar": {"rules": True, "hanging": True, "model": False},
    "EarIQ (rules+grammar+model)": {"rules": True, "hanging": True, "model": True},
}


def _valueish(w):
    c = clean(w)
    return c.isdigit() or c in NUMERIC or (len(c) == 1 and c.isalpha() and c not in {"a", "i"})


def load_turns():
    turns = []
    for inp, gold in iter_supervised("external_timing_test", allow_evaluation_labels=True):
        msgs = inp.get("prior_messages") or "[]"
        msgs = ast.literal_eval(msgs) if isinstance(msgs, str) else msgs
        field = expected_field(msgs)
        words, pauses = gold["words"], []
        for span, label in zip(gold["silence_spans"], gold["pause_labels"]):
            ctx = [w["word"] for w in words if w["end"] <= span["start"] + 0.05]
            nxt = next((w["word"] for w in words if w["start"] >= span["end"] - 0.05), "")
            pauses.append({"len": span["end"] - span["start"], "end": label != "hold", "text": prefix_text(ctx),
                           "rules": value_in_progress(ctx, field), "hanging": hanging(ctx),
                           "in_value": bool(ctx) and _valueish(ctx[-1]) and _valueish(nxt)})
        # English ids carry a conversation id (livekit__en__<conv>__user_turn_k); Hindi turns don't
        conv = inp["id"].rsplit("__", 1)[0] if "__user_turn_" in inp["id"] else inp["id"]
        turns.append({"id": inp["id"], "lang": inp["language"], "conv": conv,
                      "field": field, "pauses": pauses})
    return turns


def split(turns):
    """50/50 by conversation, separately per language (so both halves have English and Hindi)."""
    dev = set()
    for lang in sorted({t["lang"] for t in turns}):
        sub = [t for t in turns if t["lang"] == lang]
        convs = sorted({t["conv"] for t in sub})
        random.Random(SEED).shuffle(convs)
        size = {c: sum(t["conv"] == c for t in sub) for c in convs}
        n = 0
        for c in convs:
            if n + size[c] <= len(sub) / 2:
                dev.add(c)
                n += size[c]
    return [t for t in turns if t["conv"] in dev], [t for t in turns if t["conv"] not in dev]


def pause_xy(turns):
    X, y, g = [], [], []
    for t in turns:
        for p in t["pauses"]:
            X.append(p["text"]), y.append(int(p["end"])), g.append(t["conv"])
    return X, np.array(y), np.array(g)


def attach_probs(turns, model):
    X, _, _ = pause_xy(turns)
    probs = iter(model.predict_proba(X)[:, 1] if X else [])
    for t in turns:
        for p in t["pauses"]:
            p["p"] = float(next(probs))


def fit_in_domain(dev):
    """Read-speech model refit with real conversational pauses (in-domain weight 3)."""
    base = pickle.loads(MODEL_PATH.read_bytes())
    X, y, g = pause_xy(dev)
    # cross-fitted DEV probabilities, so settings are not chosen on in-sample predictions
    oof = np.zeros(len(y))
    for tr, va in GroupKFold(n_splits=5).split(X, y, g):
        m = clone(base).fit([X[i] for i in tr], y[tr])
        oof[va] = m.predict_proba([X[i] for i in va])[:, 1]
    it = iter(oof)
    for t in dev:
        for p in t["pauses"]:
            p["p"] = float(next(it))
    final = clone(base).fit(X, y)
    return final


def run(turns, flags, short, long, thr=0.5):
    cut, delay, inval = [], [], []
    for t in turns:
        c, d = False, short
        for p in t["pauses"]:
            inc = flags and ((flags["rules"] and p["rules"]) or (flags["hanging"] and p["hanging"])
                             or (flags["model"] and p["p"] < thr))
            wait = long if inc else short
            if p["end"]:
                d = wait
                break
            if p["len"] > wait:
                c = True
                break
        cut.append(c), delay.append(d), inval.append(any(p["in_value"] for p in t["pauses"]))
    cut, delay, inval = map(np.array, (cut, delay, inval))
    return {"cutoff_rate": float(cut.mean()), "mean_delay": float(delay.mean()),
            "in_value_cutoff_rate": float(cut[inval].mean()) if inval.any() else None,
            "n_in_value_turns": int(inval.sum()), "_cut": cut}


def choose(dev, flags, budget):
    best = None
    for s in np.round(np.arange(0.2, 1.51, 0.1), 2):
        for lg in (1.5, 2.0, 2.5, 3.0):
            for thr in ((0.2, 0.3, 0.4, 0.5) if flags["model"] else (0.5,)):
                if lg <= s:
                    continue
                r = run(dev, flags, s, lg, thr)
                if r["mean_delay"] <= budget + 1e-9 and (best is None or r["cutoff_rate"] < best[0]["cutoff_rate"]):
                    best = (r, {"short": float(s), "long": lg, "threshold": thr})
    return best[1] if best else None


def bootstrap_diff(turns, a, b, n=1000):
    convs = sorted({t["conv"] for t in turns})
    idx = {c: [i for i, t in enumerate(turns) if t["conv"] == c] for c in convs}
    rng = random.Random(SEED)
    diffs = []
    for _ in range(n):
        rows = [i for c in rng.choices(convs, k=len(convs)) for i in idx[c]]
        diffs.append(b[rows].mean() - a[rows].mean())
    return [round(float(np.percentile(diffs, 2.5)), 4), round(float(np.percentile(diffs, 97.5)), 4)]


def r4(x):
    return None if x is None else round(x, 4)


def main():
    t0 = time.time()
    turns = load_turns()
    dev, test = split(turns)
    model = fit_in_domain(dev)
    attach_probs(test, model)
    MODEL_V2_PATH.write_bytes(pickle.dumps(model))

    out = {"protocol": "dev/test conversation split; settings chosen on dev; reported on test",
           "n_dev": len(dev), "n_test": len(test),
           "test_languages": {l: sum(t["lang"] == l for t in test) for l in ("en", "hi")},
           "budgets": {}}
    points = {}
    for budget in BUDGETS:
        row = {}
        for name, flags in METHODS.items():
            cfg = choose(dev, flags, budget)
            r = run(test, flags, cfg["short"], cfg["long"], cfg["threshold"])
            base = run(test, None, r["mean_delay"], r["mean_delay"])  # same average wait
            row[name] = {"settings_from_dev": cfg, "test_mean_delay": round(r["mean_delay"], 3),
                         "test_cutoff_rate": r4(r["cutoff_rate"]), "baseline_cutoff_rate": r4(base["cutoff_rate"]),
                         "relative_cutoff_reduction": r4(1 - r["cutoff_rate"] / base["cutoff_rate"]) if base["cutoff_rate"] else None,
                         "cutoff_diff_95ci": bootstrap_diff(test, base["_cut"], r["_cut"]),
                         "in_value_cutoff_rate": r4(r["in_value_cutoff_rate"]),
                         "baseline_in_value_cutoff_rate": r4(base["in_value_cutoff_rate"]),
                         "by_language": {l: {"cutoff_rate": r4(run(sub, flags, cfg["short"], cfg["long"], cfg["threshold"])["cutoff_rate"]),
                                             "baseline_cutoff_rate": r4(run(sub, None, r["mean_delay"], r["mean_delay"])["cutoff_rate"])}
                                         for l in ("en", "hi") for sub in [[t for t in test if t["lang"] == l]]}}
            points.setdefault(name, []).append((r["mean_delay"], r["cutoff_rate"]))
        out["budgets"][str(budget)] = row
    out["n_in_value_turns_test"] = run(test, None, 1, 1)["n_in_value_turns"]
    (ROOT / "results" / "endpointing.json").write_text(json.dumps(out, indent=2))

    fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=150)
    grid = np.round(np.arange(0.3, 1.61, 0.05), 2)
    ax.plot(grid, [100 * run(test, None, T, T)["cutoff_rate"] for T in grid], color="#8a8f98", lw=1.6,
            label="Fixed timeout (baseline)")
    for (name, pts), col in zip(points.items(), ["#7aa6f5", "#4b7bec", "#16a34a"]):
        ax.scatter([p[0] for p in pts], [100 * p[1] for p in pts], color=col, s=36, zorder=3, label=name)
    ax.set_xlabel("Average wait at the true end of turn (s)")
    ax.set_ylabel("Turns cut off early (%)")
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Smart listening on held-out conversations (LiveKit test half)", fontsize=9)
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "endpointing_tradeoff.png")

    for budget, row in out["budgets"].items():
        for name, m in row.items():
            log_run("M4", "smart_listening_v2", name, f"LiveKit test half ({len(test)} turns)",
                    {"delay_budget_s": float(budget), **m["settings_from_dev"]},
                    {k: m[k] for k in ("test_mean_delay", "test_cutoff_rate", "baseline_cutoff_rate",
                                       "relative_cutoff_reduction", "cutoff_diff_95ci")}, time.time() - t0)
    print(json.dumps({b: {n: {k: m[k] for k in ("test_mean_delay", "test_cutoff_rate", "baseline_cutoff_rate",
                                                 "relative_cutoff_reduction", "cutoff_diff_95ci", "settings_from_dev")}
                          for n, m in row.items()} for b, row in out["budgets"].items()}, indent=1))
    print({k: out[k] for k in ("n_dev", "n_test", "test_languages", "n_in_value_turns_test")})


if __name__ == "__main__":
    main()
