"""Append-only experiment log (results/experiment_log.csv): one row per run."""
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "experiment_log.csv"
FIELDS = ["run_id", "timestamp", "milestone", "track", "approach", "data", "config", "metrics",
          "runtime_s", "git_commit", "notes"]


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "uncommitted"


def log_run(milestone, track, approach, data, config, metrics, runtime_s=None, notes=""):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        n = sum(1 for _ in LOG.open(encoding="utf-8")) if not new else 1
        w.writerow({"run_id": f"R{n:03d}", "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "milestone": milestone, "track": track, "approach": approach, "data": data,
                    "config": json.dumps(config, ensure_ascii=False),
                    "metrics": json.dumps(metrics, ensure_ascii=False),
                    "runtime_s": "" if runtime_s is None else round(runtime_s, 1),
                    "git_commit": _commit(), "notes": notes})
