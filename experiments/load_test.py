"""M5 performance measurements against the running API (start the server first).

Sequential: each demo sample 5x -> latency p50/p95 and EarIQ layer overhead.
Concurrent: 4 users at once x 3 rounds -> throughput and p95 under load (requests queue for the GPU).
Failure paths: empty / corrupt / silent audio must return clear errors, never crash.
"""
from __future__ import annotations

import io
import json
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.log import log_run  # noqa: E402

URL = "http://localhost:8000"
SAMPLES = {"phone": "phone", "email": "email", "name": "name", "order": "id"}


def post(name, field):
    data = (ROOT / "app/static/samples" / f"{name}.wav").read_bytes()
    t = time.perf_counter()
    r = requests.post(f"{URL}/api/v1/capture", files={"audio": ("a.wav", data)}, data={"field": field}, timeout=120)
    j = r.json()
    return {"ok": r.status_code == 200 and j.get("status") == "ok", "wall_s": time.perf_counter() - t,
            "layer_ms": j.get("latency_ms", {}).get("layer"), "asr_ms": j.get("latency_ms", {}).get("asr"),
            "audio_s": j.get("duration_s")}


def pct(xs, q):
    return round(float(np.percentile(xs, q)), 3)


def main():
    assert requests.get(f"{URL}/api/v1/health", timeout=5).json()["status"] == "ok", "start the server first"
    t0 = time.time()
    seq = [post(n, f) for _ in range(5) for n, f in SAMPLES.items()]
    wall = [r["wall_s"] for r in seq]
    layer = [r["layer_ms"] for r in seq]
    res = {"hardware": "Apple M3 MacBook, 16 GB, speech model on the Mac GPU (large-v3-turbo fp16)",
           "sequential": {"n": len(seq), "success_rate": sum(r["ok"] for r in seq) / len(seq),
                          "latency_p50_s": pct(wall, 50), "latency_p95_s": pct(wall, 95),
                          "mean_audio_s": round(statistics.mean(r["audio_s"] for r in seq), 2),
                          "real_time_factor": round(sum(r["asr_ms"] for r in seq) / 1000 / sum(r["audio_s"] for r in seq), 3),
                          "eariq_layer_ms_p50": pct(layer, 50), "eariq_layer_ms_p95": pct(layer, 95)}}
    conc = []
    t = time.perf_counter()
    with ThreadPoolExecutor(4) as ex:
        for _ in range(3):
            conc += list(ex.map(lambda nf: post(*nf), list(SAMPLES.items())))
    span = time.perf_counter() - t
    cw = [r["wall_s"] for r in conc]
    res["concurrent_4_users"] = {"n": len(conc), "success_rate": sum(r["ok"] for r in conc) / len(conc),
                                 "latency_p50_s": pct(cw, 50), "latency_p95_s": pct(cw, 95),
                                 "throughput_req_per_min": round(60 * len(conc) / span, 1)}
    fails = {}
    for name, payload in {"empty": b"", "corrupt": b"not audio"}.items():
        r = requests.post(f"{URL}/api/v1/capture", files={"audio": ("a.wav", payload)}, data={"field": "phone"})
        fails[name] = {"http": r.status_code, "message": r.json().get("message")}
    buf = io.BytesIO()
    sf.write(buf, np.zeros(32000, dtype=np.float32), 16000, format="WAV")
    r = requests.post(f"{URL}/api/v1/capture", files={"audio": ("a.wav", buf.getvalue())}, data={"field": "phone"})
    fails["silence"] = {"http": r.status_code, "message": r.json().get("message")}
    res["failure_paths"] = fails
    try:
        pid = subprocess.run(["pgrep", "-f", "uvicorn app.server"], capture_output=True, text=True).stdout.split()[0]
        rss = int(subprocess.run(["ps", "-o", "rss=", "-p", pid], capture_output=True, text=True).stdout)
        res["server_memory_mb"] = round(rss / 1024)
    except Exception:
        pass
    res["m1_target_added_delay_under_200ms"] = res["sequential"]["eariq_layer_ms_p95"] < 200
    (ROOT / "results" / "performance.json").write_text(json.dumps(res, indent=2))
    log_run("M5", "performance", "api_load_test", "4 demo samples", {"sequential_x5": True, "concurrency": 4},
            res, time.time() - t0)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
