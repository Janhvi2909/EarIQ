"""Baseline-ready, gold-separated local data interface. No network calls."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPLITS = {"train", "validation", "test", "external_entity_test", "external_timing_test"}

def _read(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def iter_inputs(split: str, context_level: int | None = None):
    """Inputs only. Context is opt-in and a single fixed level for fair comparisons."""
    if split not in SPLITS:
        raise ValueError(f"Unknown split: {split}")
    contexts = {}
    if context_level is not None:
        if context_level not in range(7) or split.startswith("external_"):
            raise ValueError("Context levels 0–6 apply only to the IndicContextEval project splits")
        contexts = {r["id"]:r[f"l{context_level}_prompt"]
            for r in _read(ROOT/"data/manifests"/(split+"_context.jsonl"))}
    for row in _read(ROOT/"data/manifests"/(split+".jsonl")):
        if context_level is not None:
            row["context_prompt"] = contexts[row["id"]]
            row["context_level"] = context_level
        yield row

def iter_supervised(split: str, *, allow_evaluation_labels=False, context_level=None):
    """Training/dev pairs; held-out gold requires an explicit evaluation opt-in."""
    if split not in {"train", "validation"} and not allow_evaluation_labels:
        raise ValueError("Held-out gold is evaluation-only; set allow_evaluation_labels=True explicitly")
    labels = {r["id"]:r for r in _read(ROOT/"data/manifests"/(split+"_labels.jsonl"))}
    for inputs in iter_inputs(split, context_level=context_level):
        yield inputs, labels[inputs["id"]]
