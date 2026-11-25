"""Speech recognition wrapper: faster-whisper running locally (Mac GPU or CPU; no paid API, no upload)."""
from __future__ import annotations

import io
import os
import sys
import time

import numpy as np
import soundfile as sf

DEFAULT_MODEL = os.environ.get("EARIQ_ASR_MODEL", "large-v3-turbo")
# Apple-silicon GPU (MPS) when available, otherwise CPU (e.g. inside Docker).
DEFAULT_DEVICE = os.environ.get("EARIQ_DEVICE", "mps" if sys.platform == "darwin" else "cpu")
DEFAULT_COMPUTE = os.environ.get("EARIQ_COMPUTE_TYPE", "float16" if DEFAULT_DEVICE == "mps" else "int8")
SAMPLE_RATE = 16000
_MODELS: dict = {}


def get_model(name: str = DEFAULT_MODEL, compute_type: str = DEFAULT_COMPUTE,
              device: str = DEFAULT_DEVICE):
    key = (name, compute_type, device)
    if key not in _MODELS:
        from faster_whisper import WhisperModel
        _MODELS[key] = WhisperModel(name, device=device, compute_type=compute_type,
                                    cpu_threads=os.cpu_count() or 4)
    return _MODELS[key]


def load_audio(source) -> np.ndarray:
    """Path or raw WAV bytes -> 16 kHz mono float32."""
    if isinstance(source, (bytes, bytearray)):
        source = io.BytesIO(source)
    audio, sr = sf.read(source, dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    if sr != SAMPLE_RATE:
        from math import gcd
        from scipy.signal import resample_poly
        g = gcd(sr, SAMPLE_RATE)
        audio = resample_poly(audio, SAMPLE_RATE // g, sr // g).astype(np.float32)
    return audio


def transcribe(audio, language: str | None = None, prompt: str | None = None,
               hotwords: str | None = None, beam_size: int = 1,
               model: str = DEFAULT_MODEL, compute_type: str = DEFAULT_COMPUTE,
               device: str = DEFAULT_DEVICE) -> dict:
    """Return transcript text plus per-word timing and confidence."""
    if not isinstance(audio, np.ndarray):
        audio = load_audio(audio)
    m = get_model(model, compute_type, device)
    t0 = time.perf_counter()
    segments, info = m.transcribe(audio, language=language, beam_size=beam_size,
                                  word_timestamps=True, vad_filter=False,
                                  condition_on_previous_text=False,
                                  initial_prompt=prompt, hotwords=hotwords)
    parts, words = [], []
    for seg in segments:
        if seg.text.strip():
            parts.append(seg.text.strip())
        for w in seg.words or []:
            if w.word.strip():
                words.append({"word": w.word.strip(), "start": round(w.start, 3),
                              "end": round(w.end, 3), "prob": round(w.probability, 4),
                              "joined": not w.word[:1].isspace()})
    text = " ".join(parts)
    return {"text": text, "words": merge_pieces(words, text), "pieces": words, "language": info.language,
            "duration": round(info.duration, 3),
            "asr_seconds": round(time.perf_counter() - t0, 3)}


def merge_pieces(words: list[dict], text: str) -> list[dict]:
    """Whisper sometimes splits one written word into pieces ("INV" + "-53554"). Re-join pieces
    that touch in the transcript text (no space between them). Idempotent."""
    out, pos = [], 0
    for w in words:
        idx = text.find(w["word"], pos)
        if idx < 0:
            out.append(dict(w))
            continue
        if out and idx == pos and idx > 0 and not text[idx - 1].isspace():
            prev = out[-1]
            prev["word"] += w["word"]
            prev["end"] = w["end"]
            prev["prob"] = min(prev["prob"], w["prob"])
        else:
            out.append(dict(w))
        pos = idx + len(w["word"])
    return out


def join_pieces(pieces: list[dict]) -> list[dict]:
    """Merge raw pieces into written words using Whisper's own word-start flags."""
    out = []
    for w in pieces:
        if out and w.get("joined"):
            out[-1] = {**out[-1], "word": out[-1]["word"] + w["word"], "end": w["end"],
                       "prob": min(out[-1]["prob"], w["prob"])}
        else:
            out.append({k: v for k, v in w.items() if k != "joined"})
    return out
