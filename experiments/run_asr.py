"""Run ASR once over a split and cache outputs (resumable). The capture layer is evaluated on these cached outputs.

Example:
  python experiments/run_asr.py --split external_entity_test --language en --name vcb_turbo
  python experiments/run_asr.py --split validation --language hi --context-level 4 --limit 120 --name hi_val_l4
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eariq import asr  # noqa: E402
from src.listening_data import iter_inputs  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--split", required=True)
    p.add_argument("--language", default=None)
    p.add_argument("--context-level", type=int, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--model", default=asr.DEFAULT_MODEL)
    p.add_argument("--compute-type", default=asr.DEFAULT_COMPUTE)
    p.add_argument("--device", default=asr.DEFAULT_DEVICE)
    p.add_argument("--beam", type=int, default=1)
    p.add_argument("--name", required=True)
    a = p.parse_args()

    out = ROOT / "results/asr" / f"{a.name}.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["id"] for l in out.open(encoding="utf-8") if l.strip()}
    rows = list(iter_inputs(a.split, context_level=a.context_level))
    rows.sort(key=lambda r: r["id"])  # deterministic order; --limit takes a fixed subset
    if a.limit:
        rows = rows[: a.limit]
    todo = [r for r in rows if r["id"] not in done]
    print(f"{a.name}: {len(rows)} rows, {len(todo)} to do", flush=True)
    t0 = time.time()
    with out.open("a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            res = asr.transcribe(str(ROOT / r["audio_path"]), language=a.language,
                                 prompt=r.get("context_prompt"), beam_size=a.beam,
                                 model=a.model, compute_type=a.compute_type, device=a.device)
            res.update(id=r["id"], config={"model": a.model, "compute_type": a.compute_type,
                                           "device": a.device, "beam": a.beam, "language": a.language,
                                           "context_level": a.context_level})
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            if i % 10 == 0:
                print(f"  {i}/{len(todo)}  {time.time() - t0:.0f}s", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
