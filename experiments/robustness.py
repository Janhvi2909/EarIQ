"""Robustness: does EarIQ's gain hold under harder audio? 25 VoiceCodeBench recordings x 3 conditions
(+ clean from the main run). Same Whisper model; scored with the strict exact-value scorer."""
from __future__ import annotations

import json
import random
import sys
import time
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402
from scipy.signal import butter, resample_poly, sosfilt  # noqa: E402

from eariq import asr  # noqa: E402
from experiments.common import run_cached  # noqa: E402
from experiments.eval_entities import entity_rows  # noqa: E402
from experiments.log import log_run  # noqa: E402
from src.listening_data import iter_inputs  # noqa: E402

N = 25


def noise(a, snr_db, seed=0):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(len(a) + 1)
    pink = np.cumsum(w)[1:] - np.cumsum(w)[:-1] * 0.98  # leaky integrator -> low-frequency-heavy noise
    pink = pink[: len(a)]
    p_sig, p_n = np.mean(a ** 2), np.mean(pink ** 2)
    return (a + pink * np.sqrt(p_sig / (p_n * 10 ** (snr_db / 10)))).astype(np.float32)


def phone_line(a):
    nb = resample_poly(a, 1, 2)  # 8 kHz
    nb = sosfilt(butter(4, [300, 3400], btype="band", fs=8000, output="sos"), nb)
    return resample_poly(nb, 2, 1).astype(np.float32)


def faster(a, rate=1.15):
    up, down = 100, int(100 * rate)
    g = gcd(up, down)
    return resample_poly(a, up // g, down // g).astype(np.float32)


CONDITIONS = {"background_noise_10db": lambda a: noise(a, 10), "phone_line_8khz": phone_line,
              "speech_15pct_faster": faster}


def acc(rows, k):
    return round(sum(r[k] for r in rows) / len(rows), 4)


def main():
    t0 = time.time()
    ids = sorted(r["id"] for r in iter_inputs("external_entity_test"))
    ids = sorted(random.Random(20261125).sample(ids, N))
    paths = {r["id"]: ROOT / r["audio_path"] for r in iter_inputs("external_entity_test")}
    clean = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "results/asr/vcb_turbo.jsonl").open()}
    res = {"n_recordings": N}
    rows, _, _ = entity_rows({i: clean[i] for i in ids}, keep_regions=False)
    res["clean"] = {"n_entities": len(rows), "normal_ai": acc(rows, "base_strict"), "eariq": acc(rows, "ours_strict")}
    for name, fn in CONDITIONS.items():
        items = [(i, fn(asr.load_audio(str(paths[i])))) for i in ids]
        hyps = run_cached(f"robust_{name}", items, language="en")
        rows, _, _ = entity_rows(hyps, keep_regions=False)
        res[name] = {"n_entities": len(rows), "normal_ai": acc(rows, "base_strict"), "eariq": acc(rows, "ours_strict")}
        print(name, res[name], flush=True)
    for k, v in res.items():
        if isinstance(v, dict):
            v["eariq_gain_points"] = round(100 * (v["eariq"] - v["normal_ai"]), 1)
    (ROOT / "results" / "robustness.json").write_text(json.dumps(res, indent=2))
    log_run("M4", "robustness", "normal_ai_vs_eariq_per_condition", f"VoiceCodeBench subset ({N} rec)",
            {"conditions": list(CONDITIONS)}, res, time.time() - t0)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
