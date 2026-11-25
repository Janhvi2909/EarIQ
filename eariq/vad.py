"""Tiny energy-based voice activity detector: where is speech, where are the pauses.

Live endpointers decide on silence measured in the audio, not on ASR word timings
(Whisper stretches word boundaries across pauses).
"""
from __future__ import annotations

import numpy as np

FRAME_S = 0.02


def speech_segments(audio: np.ndarray, sr: int = 16000, min_pause: float = 0.25, min_speech: float = 0.08):
    """Return (speech [[start, end]], pauses [{start, end, length}]) between first and last speech."""
    fr = int(FRAME_S * sr)
    if len(audio) < fr:
        return [], []
    n = len(audio) // fr
    rms = np.sqrt(np.mean(audio[: n * fr].reshape(n, fr) ** 2, axis=1))
    db = 20 * np.log10(rms + 1e-9)
    thr = max(np.percentile(db, 95) - 30, np.percentile(db, 10) + 6, -55)
    voiced = db > thr
    segs, start = [], None
    for i, v in enumerate(np.append(voiced, False)):
        if v and start is None:
            start = i
        elif not v and start is not None:
            segs.append([start * FRAME_S, i * FRAME_S])
            start = None
    merged = []  # close tiny gaps, drop clicks
    for s, e in segs:
        if merged and s - merged[-1][1] < min_pause:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    merged = [[round(s, 2), round(e, 2)] for s, e in merged if e - s >= min_speech]
    pauses = [{"start": a[1], "end": b[0], "length": round(b[0] - a[1], 2)} for a, b in zip(merged, merged[1:])]
    return merged, pauses
