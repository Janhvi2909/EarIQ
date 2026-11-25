"""Shared helpers: cached ASR runs (resumable) and text metrics."""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eariq import asr  # noqa: E402


def run_cached(name: str, items: list[tuple[str, object]], **kw) -> dict:
    """items: [(id, audio path or array)] -> {id: asr result}. Cached in results/asr/<name>.jsonl."""
    out = ROOT / "results/asr" / f"{name}.jsonl"
    done = {}
    if out.exists():
        done = {r["id"]: r for r in map(json.loads, out.open(encoding="utf-8"))}
    todo = [(i, a) for i, a in items if i not in done]
    if todo:
        print(f"{name}: {len(todo)} to transcribe", flush=True)
    with out.open("a", encoding="utf-8") as f:
        for k, (i, a) in enumerate(todo, 1):
            res = asr.transcribe(a if not isinstance(a, (str, Path)) else str(a), **kw)
            res["id"] = i
            res["config"] = {k2: v for k2, v in kw.items() if k2 != "prompt"}
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            done[i] = res
            if k % 25 == 0:
                print(f"  {name}: {k}/{len(todo)}", flush=True)
    return {i: done[i] for i, _ in items}


def norm_hi(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    s = re.sub(r"[।॥,.?!;:\"'()\[\]\-–—]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def terms_from_prompt(prompt: str) -> str:
    """IndicContextEval L4-L6 prompts: keep only the term list (Whisper takes hints, not instructions)."""
    lines = [l.strip() for l in (prompt or "").splitlines() if l.strip()]
    return lines[1] if len(lines) > 1 and not lines[1].lower().startswith("transcribe") else ""
