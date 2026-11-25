"""Optimisation: accuracy vs speed for the speech model behind EarIQ (15 VoiceCodeBench recordings),
plus the capture layer's own overhead over all 300 recordings (M1 target: < 200 ms added)."""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

from eariq.asr import merge_pieces  # noqa: E402
from eariq.capture import capture  # noqa: E402
from experiments.common import run_cached  # noqa: E402
from experiments.eval_entities import entity_rows  # noqa: E402
from experiments.log import log_run  # noqa: E402
from src.listening_data import iter_inputs  # noqa: E402

N = 15
CONFIGS = {
    "small · GPU fp16 · greedy": dict(model="small", device="mps", compute_type="float16", beam_size=1),
    "large-v3-turbo · GPU fp16 · greedy (chosen)": dict(model="large-v3-turbo", device="mps", compute_type="float16", beam_size=1),
    "large-v3-turbo · GPU fp16 · beam 5": dict(model="large-v3-turbo", device="mps", compute_type="float16", beam_size=5),
    "large-v3-turbo · CPU int8 · greedy (Docker)": dict(model="large-v3-turbo", device="cpu", compute_type="int8", beam_size=1),
}


def main():
    t0 = time.time()
    rows_in = {r["id"]: r for r in iter_inputs("external_entity_test")}
    ids = sorted(random.Random(7).sample(sorted(rows_in), N))
    res = {"n_recordings": N, "audio_minutes": round(sum(float(rows_in[i]["duration_s"]) for i in ids) / 60, 1),
           "hardware": "Apple M3 MacBook, 16 GB", "configs": {}}
    for name, kw in CONFIGS.items():
        tag = "speed_" + "_".join(str(v) for v in kw.values())
        hyps = run_cached(tag, [(i, ROOT / rows_in[i]["audio_path"]) for i in ids], language="en", **kw)
        rows, _, _ = entity_rows(hyps, keep_regions=False)
        rtf = sum(h["asr_seconds"] for h in hyps.values()) / sum(h["duration"] for h in hyps.values())
        res["configs"][name] = {"real_time_factor": round(rtf, 3), "x_faster_than_realtime": round(1 / rtf, 1),
                                "normal_ai_exact": round(np.mean([r["base_strict"] for r in rows]), 4),
                                "eariq_exact": round(np.mean([r["ours_strict"] for r in rows]), 4)}
        print(name, res["configs"][name], flush=True)
    # capture-layer overhead (no speech model involved)
    hyps = [json.loads(l) for l in (ROOT / "results/asr/vcb_turbo.jsonl").open()]
    times = []
    for h in hyps:
        w = merge_pieces(h["words"], h["text"])
        t = time.perf_counter()
        capture(w, "any")
        times.append((time.perf_counter() - t) * 1000)
    res["capture_layer_ms"] = {"n": len(times), "p50": round(float(np.percentile(times, 50)), 2),
                               "p95": round(float(np.percentile(times, 95)), 2), "max": round(max(times), 2),
                               "note": "per ~67 s recording, whole transcript at once"}
    (ROOT / "results" / "speed.json").write_text(json.dumps(res, indent=2))
    log_run("M4", "optimisation", "model_size_precision_beam", f"VoiceCodeBench subset ({N} rec)",
            {"configs": list(CONFIGS)}, res, time.time() - t0)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
