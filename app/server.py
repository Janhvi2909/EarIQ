"""EarIQ API + web app.

Run:  .venv/bin/uvicorn app.server:app --port 8000      then open http://localhost:8000
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import sys
import time
import uuid
from collections import Counter, deque
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eariq import asr  # noqa: E402
from eariq.capture import FIELDS, baseline_capture, capture  # noqa: E402
from eariq.endpointing import DEFAULT_POLICY, load_model, simulate_audio  # noqa: E402
from eariq.vad import speech_segments  # noqa: E402

MAX_BYTES = 10 * 1024 * 1024
MAX_SECONDS = 60
SILENCE_DBFS = -55.0
ASR_TIMEOUT_S = float(os.environ.get("EARIQ_ASR_TIMEOUT", "45"))
MAX_QUEUE = 4
ALERTS = {"p95_latency_s": 6.0, "error_rate": 0.02, "ask_rate": 0.30, "confirm_rate": 0.20}
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
log = logging.getLogger("eariq")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="EarIQ", version="1.0.0",
              description="Entity-aware capture layer: listens through pauses, formats exact values, asks only when unsure.")
STATE = {"started": time.time(), "model_ready": False, "requests": 0, "errors": 0, "fallbacks": 0,
         "actions": Counter(), "fields": Counter(), "languages": Counter(), "feedback": Counter(),
         "latency": deque(maxlen=500), "layer_ms": deque(maxlen=500), "recent": deque(maxlen=25),
         "inflight": 0}
_gpu = asyncio.Semaphore(1)  # one ASR job at a time on the GPU; others queue


@app.on_event("startup")
async def warm_up():
    async def _load():
        try:
            await asyncio.to_thread(asr.get_model)
            await asyncio.to_thread(load_model)
            await asyncio.to_thread(asr.transcribe, np.zeros(16000, dtype=np.float32), "en")
            STATE["model_ready"] = True
            log.info("model ready: %s on %s", asr.DEFAULT_MODEL, asr.DEFAULT_DEVICE)
        except Exception as e:  # keep serving the UI; /health reports it
            STATE["model_error"] = str(e)
            log.exception("model failed to load")
    asyncio.create_task(_load())


def _mask(v: str | None) -> str | None:
    """Monitoring never stores raw values (privacy)."""
    if not v:
        return None
    return v[:2] + "•" * max(len(v) - 4, 1) + v[-2:] if len(v) > 4 else "•" * len(v)


def _record(entry: dict):
    STATE["recent"].appendleft(entry)
    with (LOG_DIR / "requests.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")


@app.post("/api/v1/capture")
async def capture_endpoint(audio: UploadFile = File(...), field: str = Form("any"), language: str = Form("auto")):
    rid = uuid.uuid4().hex[:10]
    t0 = time.perf_counter()
    STATE["requests"] += 1
    field = field if field in FIELDS else "any"
    lang = None if language in ("auto", "", None) else language
    # ---- input validation (failure handling) ----
    raw = await audio.read()
    if not raw:
        raise HTTPException(400, "No audio received. Please record again.")
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "That recording is too large (max 10 MB).")
    try:
        samples = asr.load_audio(io.BytesIO(raw))
    except Exception:
        raise HTTPException(400, "Couldn't read that audio. Please send a WAV recording.")
    dur = len(samples) / asr.SAMPLE_RATE
    if dur > MAX_SECONDS:
        raise HTTPException(400, f"Please keep it under {MAX_SECONDS} seconds.")
    level = 20 * np.log10(np.sqrt(np.mean(samples ** 2)) + 1e-9) if len(samples) else -120
    if dur < 0.3 or level < SILENCE_DBFS:
        STATE["actions"]["ask"] += 1
        return {"request_id": rid, "status": "no_speech", "duration_s": round(dur, 2),
                "message": "I couldn't hear anything. Try again a little closer to the mic."}
    if STATE["inflight"] >= MAX_QUEUE:
        raise HTTPException(429, "EarIQ is busy. Please try again in a few seconds.")
    if not STATE["model_ready"]:
        raise HTTPException(503, "The speech model is still loading. Try again in a moment.")
    # ---- speech recognition (timeout -> clear error, never a hang) ----
    STATE["inflight"] += 1
    try:
        async with _gpu:
            t_asr = time.perf_counter()
            res = await asyncio.wait_for(asyncio.to_thread(asr.transcribe, samples, lang), ASR_TIMEOUT_S)
            asr_ms = (time.perf_counter() - t_asr) * 1000
    except asyncio.TimeoutError:
        STATE["errors"] += 1
        _record({"t": time.time(), "id": rid, "field": field, "status": "timeout"})
        raise HTTPException(503, "Speech recognition took too long. Please try a shorter clip.")
    except Exception as e:
        STATE["errors"] += 1
        log.exception("asr failed")
        _record({"t": time.time(), "id": rid, "field": field, "status": "asr_error", "error": type(e).__name__})
        raise HTTPException(503, "Speech recognition failed. Please try again.")
    finally:
        STATE["inflight"] -= 1
    words, pieces = res["words"], res["pieces"]
    if not words:
        STATE["actions"]["ask"] += 1
        return {"request_id": rid, "status": "no_speech", "duration_s": round(dur, 2),
                "message": "I couldn't make out any words. Could you say that again?"}
    # ---- capture layer (any failure -> degrade to plain transcript, never invent a value) ----
    t_layer = time.perf_counter()
    degraded = False
    speech, pauses = speech_segments(samples)

    def side(policy, capture_fn, wait):
        k, cut_t = simulate_audio(pieces, pauses, policy, field)
        heard = pieces if k is None else pieces[:k + 1]
        missed = [] if k is None else asr.join_pieces(pieces[k + 1:])
        out = capture_fn(asr.join_pieces(heard))
        out.update(cut_at=cut_t, stop_at=None if cut_t is None else round(cut_t + wait, 2),
                   missed=" ".join(w["word"] for w in missed))
        return out

    try:
        normal = side({"fixed": DEFAULT_POLICY["short"]},
                      lambda ws: baseline_capture(" ".join(w["word"] for w in ws), field), DEFAULT_POLICY["short"])
        ours = side(DEFAULT_POLICY, lambda ws: capture(ws, field), DEFAULT_POLICY["short"])
    except Exception:
        log.exception("capture layer failed; degrading")
        degraded = True
        STATE["fallbacks"] += 1
        normal = baseline_capture(res["text"], field)
        normal.update(cut_at=None, stop_at=None, missed="")
        ours = {"transcript": res["text"], "value": None, "display": None, "action": "ask",
                "question": f"Sorry, could you repeat your {FIELDS[field]}?", "confidence": None,
                "cut_at": None, "stop_at": None, "missed": "", "values": []}
    layer_ms = (time.perf_counter() - t_layer) * 1000
    total_s = time.perf_counter() - t0
    STATE["latency"].append(total_s)
    STATE["layer_ms"].append(layer_ms)
    STATE["actions"][ours["action"]] += 1
    STATE["fields"][field] += 1
    STATE["languages"][res["language"]] += 1
    _record({"t": time.time(), "id": rid, "field": field, "status": "ok", "language": res["language"],
             "duration_s": round(dur, 2), "latency_s": round(total_s, 3), "layer_ms": round(layer_ms, 1),
             "action": ours["action"], "normal_action": normal["action"], "degraded": degraded,
             "value": _mask(ours.get("value")), "confidence": ours.get("confidence")})
    return {"request_id": rid, "status": "ok", "field": field, "language": res["language"],
            "duration_s": round(dur, 2), "speech": speech, "pauses": pauses,
            "end_at": speech[-1][1] if speech else round(dur, 2), "degraded": degraded,
            "policy": {"normal_wait_s": DEFAULT_POLICY["short"], "eariq_short_s": DEFAULT_POLICY["short"],
                       "eariq_long_s": DEFAULT_POLICY["long"]},
            "latency_ms": {"asr": round(asr_ms), "layer": round(layer_ms, 1), "total": round(total_s * 1000)},
            "normal_ai": normal, "eariq": ours}


@app.post("/api/v1/feedback")
async def feedback(request_id: str = Form(...), correct: bool = Form(...)):
    STATE["feedback"]["correct" if correct else "wrong"] += 1
    _record({"t": time.time(), "id": request_id, "status": "feedback", "correct": correct})
    return {"ok": True}


@app.get("/api/v1/health")
async def health():
    return {"status": "ok" if STATE["model_ready"] else "loading", "model": asr.DEFAULT_MODEL,
            "device": asr.DEFAULT_DEVICE, "uptime_s": round(time.time() - STATE["started"]),
            "error": STATE.get("model_error")}


def _metrics():
    lat = sorted(STATE["latency"])
    n_ok = sum(STATE["actions"].values()) or 0
    pct = lambda q: round(lat[min(len(lat) - 1, int(q * len(lat)))], 3) if lat else None  # noqa: E731
    m = {"requests": STATE["requests"], "errors": STATE["errors"], "fallbacks": STATE["fallbacks"],
         "error_rate": round(STATE["errors"] / STATE["requests"], 4) if STATE["requests"] else 0.0,
         "p50_latency_s": pct(0.5), "p95_latency_s": pct(0.95),
         "layer_ms_p95": round(sorted(STATE["layer_ms"])[int(0.95 * (len(STATE["layer_ms"]) - 1))], 1) if STATE["layer_ms"] else None,
         "actions": dict(STATE["actions"]), "fields": dict(STATE["fields"]), "languages": dict(STATE["languages"]),
         "ask_rate": round(STATE["actions"]["ask"] / n_ok, 4) if n_ok else 0.0,
         "confirm_rate": round(STATE["actions"]["confirm"] / n_ok, 4) if n_ok else 0.0,
         "feedback": dict(STATE["feedback"]), "model_ready": STATE["model_ready"],
         "uptime_s": round(time.time() - STATE["started"]), "recent": list(STATE["recent"]),
         "latency_series": [round(x, 3) for x in STATE["latency"]][-60:]}
    m["alerts"] = [{"name": k, "threshold": v, "value": m.get(k),
                    "status": "ok" if m.get(k) is None or m.get(k) <= v else "alert"} for k, v in ALERTS.items()]
    return m


@app.get("/api/v1/metrics")
async def metrics():
    return _metrics()


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus():
    m = _metrics()
    lines = [f"eariq_requests_total {m['requests']}", f"eariq_errors_total {m['errors']}",
             f"eariq_fallbacks_total {m['fallbacks']}", f"eariq_latency_p95_seconds {m['p95_latency_s'] or 0}"]
    lines += [f'eariq_actions_total{{action="{a}"}} {n}' for a, n in m["actions"].items()]
    return "\n".join(lines) + "\n"


@app.get("/api/v1/benchmarks")
async def benchmarks():
    """Headline numbers straight from the results files (no hand-typed claims)."""
    out = {}
    for name in ("entities", "endpointing", "dev_synthetic", "performance"):
        p = ROOT / "results" / f"{name}.json"
        if p.exists():
            out[name] = json.loads(p.read_text())
    return out


@app.exception_handler(HTTPException)
async def http_error(_, exc: HTTPException):
    return JSONResponse({"status": "error", "message": exc.detail}, status_code=exc.status_code)


STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/monitor")
async def monitor():
    return FileResponse(STATIC / "monitor.html")
