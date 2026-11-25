"""Train the "has the speaker finished?" text model used by smart listening.

Positives: complete sentences. Negatives: the same sentences cut at a random word (mid-thought,
often mid-value). Hindi: project train split (validation split held out). English: synthetic
intake sentences + GLUE SST-2 validation sentences (85/15 split). Benchmarks are never used.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pickle  # noqa: E402

import pandas as pd  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score  # noqa: E402
from sklearn.pipeline import make_pipeline, make_union  # noqa: E402

from eariq.endpointing import MODEL_PATH, clean, prefix_text  # noqa: E402
from experiments.log import log_run  # noqa: E402
from experiments.synth import sentences  # noqa: E402
from src.listening_data import iter_supervised  # noqa: E402


def examples(texts, rng, negatives=2):
    X, y = [], []
    for t in texts:
        words = [w for w in t.split() if clean(w)]
        if len(words) < 2:
            continue
        X.append(prefix_text(words)), y.append(1)
        for k in rng.sample(range(1, len(words)), min(negatives, len(words) - 1)):
            X.append(prefix_text(words[:k])), y.append(0)
    return X, y


def sst2_sentences():
    hub = Path(os.path.expanduser("~/.cache/huggingface/hub/datasets--glue/snapshots"))
    files = list(hub.glob("*/sst2/validation-*.parquet"))
    if not files:
        return []
    s = pd.read_parquet(files[0]).sentence.str.replace(r" (?=['.,!?;:])|(?<=\w) n't", "", regex=True)
    return [x.strip() for x in s if len(x.split()) >= 4]


def main():
    t0 = time.time()
    rng = random.Random(20261125)
    hi_train = [g["reference_nfc"] for _, g in iter_supervised("train")]
    hi_val = [g["reference_nfc"] for _, g in iter_supervised("validation")]
    en = sentences(2000) + sst2_sentences()
    rng.shuffle(en)
    cut = int(len(en) * 0.85)
    en_train, en_val = en[:cut], en[cut:]

    Xtr, ytr = examples(hi_train + en_train, rng)
    model = make_pipeline(
        make_union(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True),
                   TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, token_pattern=r"\S+")),
        LogisticRegression(max_iter=3000, C=4.0, class_weight="balanced"))
    model.fit(Xtr, ytr)

    metrics = {}
    for name, texts in [("hindi_validation", hi_val), ("english_validation", en_val)]:
        Xv, yv = examples(texts, random.Random(1))
        pred = model.predict(Xv)
        metrics[name] = {"n": len(yv), "accuracy": round(accuracy_score(yv, pred), 4),
                         "f1_complete": round(f1_score(yv, pred), 4)}
    MODEL_PATH.parent.mkdir(exist_ok=True)
    with MODEL_PATH.open("wb") as f:
        pickle.dump(model, f)
    out = {"train_examples": len(ytr), "train_sentences": {"hindi": len(hi_train), "english": len(en_train)},
           "validation": metrics}
    (ROOT / "results" / "completion_model.json").write_text(json.dumps(out, indent=2))
    log_run("M3", "smart_listening", "completion_model_tfidf_lr", "hindi train + synthetic/SST-2 English",
            {"features": "char 2-5 + word 1-2 tf-idf, last 6 words", "C": 4.0, "negatives_per_sentence": 2},
            metrics, time.time() - t0)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
