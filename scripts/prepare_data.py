"""Offline M2 preparation. Preserve raw references; keep gold out of input manifests."""
from __future__ import annotations

import collections
import hashlib
import io
import json
import math
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import soundfile as sf
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
RAW, AUDIO, PROCESSED = (ROOT/"data"/p for p in ["raw", "audio", "processed"])
MANIFESTS = ROOT/"data/manifests"
REPORTS = ROOT/"reports"
SEED = 20261028
CONFIG = {s["key"]: s for s in json.loads((ROOT/"configs/sources.json").read_text())}

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def text_normalise(text):
    # Identity-bearing punctuation, script, leading zeros and diacritics survive.
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text or ""))).strip()

def text_key(text):
    return text_normalise(text).casefold()

def pseudonym(source, value):
    if value is None or str(value).strip().lower() in {"", "none", "nan", "unknown"}:
        return None
    return source + "_" + hashlib.sha256(str(value).encode()).hexdigest()[:16]

def audio_prepare(source, sample_id, reference, declared):
    raw_audio, sr = sf.read(reference, dtype="float32", always_2d=True)
    if not raw_audio.size or not np.isfinite(raw_audio).all():
        raise ValueError("empty_or_nonfinite_audio")
    channels = raw_audio.shape[1]
    selected_channel = 0
    # Five VCB files have a near-silent first channel and speech in the second.
    # Never mix potentially distinct speakers. Select the active channel only when
    # every other channel has <0.1% of its RMS; otherwise require manual policy.
    if channels != 1:
        channel_rms = np.sqrt(np.mean(raw_audio.astype(np.float64)**2, axis=0))
        selected_channel = int(np.argmax(channel_rms))
        other = np.delete(channel_rms, selected_channel)
        if np.any(other >= max(channel_rms[selected_channel], 1e-12)*.001):
            raise ValueError("multichannel_requires_manual_channel_policy")
    signal = raw_audio[:, selected_channel]
    duration = len(signal)/sr
    if duration <= 0:
        raise ValueError("nonpositive_duration")
    clipped = float(np.mean(np.abs(signal) >= .999))
    rms = float(np.sqrt(np.mean(signal.astype(np.float64)**2)))
    flags = []
    if declared is not None and abs(duration - float(declared)) > .1:
        flags.append("declared_duration_mismatch")
    if clipped > .001:
        flags.append("clipping_gt_0.1pct")
    if rms < 1e-5:
        flags.append("near_silent_audio")
    if sr != 16000:
        factor = math.gcd(sr, 16000)
        signal = resample_poly(signal, 16000//factor, sr//factor).astype(np.float32)
    dest = AUDIO/source/(sample_id + ".wav")
    dest.parent.mkdir(parents=True, exist_ok=True)
    sf.write(dest, signal, 16000, subtype="PCM_16")
    # Compare decoded prepared PCM, including rate. This catches container differences.
    pcm, _ = sf.read(dest, dtype="int16")
    return {"audio_path": str(dest.relative_to(ROOT)), "sample_rate": 16000,
        "original_sample_rate": sr, "original_channels": channels,
        "selected_channel": selected_channel,
        "duration_s": duration, "declared_duration_s": declared,
        "audio_sha256": hashlib.sha256(pcm.tobytes()).hexdigest(),
        "clipped_fraction": clipped, "rms_dbfs": 20*math.log10(max(rms, 1e-12)),
        "sample_peak": float(np.max(np.abs(raw_audio))),
        "qc_flags": flags}

def common(source, sample_id, language, text, audio, duration, speaker=None):
    clean = text_normalise(text)
    if not clean:
        raise ValueError("empty_reference")
    return {"id": source + "__" + sample_id, "source": source,
        "source_revision": CONFIG[source]["revision"], "language": language,
        "speaker_group": pseudonym(source, speaker),
        "reference_verbatim": text, "reference_nfc": clean,
        "reference_sha256": hashlib.sha256(text_key(clean).encode()).hexdigest(),
        "text_changed_by_nfc_whitespace": clean != text,
        **audio_prepare(source, sample_id, audio, duration)}

def load_voicecodebench():
    rows = []
    path = RAW/"voicecodebench/data/metadata.jsonl"
    for line in path.read_text().splitlines():
        item = json.loads(line)
        sid = item["audio_id"]
        r = common("voicecodebench", sid, "en", item["transcripts"]["acoustic"],
            RAW/"voicecodebench/data"/item["file_name"], item["duration"], item["speaker"]["id"])
        r.update(split="external_entity_test", original_split="test", domain=item["domain"],
            scenario=item["scenario"], difficulty=item["difficulty"],
            accent=item["speaker"].get("accent"), entities=item["entities"],
            canonical_transcript=item["transcripts"]["canonical"],
            template=item["transcripts"]["template"],
            source_audio_quality=item["audio_quality"], code_mixing=None,
            speech_style="scripted_human_read", context={})
        assert len(r["entities"]) == item["entity_count"]
        rows.append(r)
    return rows

def parquet_rows(path):
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(batch_size=16):
        yield from batch.to_pylist()

def embedded(audio, source_file):
    if audio.get("bytes"):
        return io.BytesIO(audio["bytes"])
    candidate = Path(audio["path"])
    if candidate.is_file():
        return candidate
    raise ValueError("embedded_audio_missing:" + source_file)

def load_livekit():
    rows = []
    for file in sorted((RAW/"livekit/data").glob("*/validation-*.parquet")):
        for item in parquet_rows(file):
            sid = item["id"]
            words = item["words"] or []
            text = " ".join(w["word"] for w in words)
            # Empty source transcripts remain available for audio endpointing.
            r = common("livekit", sid, item["language"], text or "[NO_REFERENCE_TRANSCRIPT]",
                embedded(item["audio"], file.name), item["duration"])
            r["reference_missing"] = not bool(text.strip())
            if r["reference_missing"]:
                r["reference_verbatim"] = r["reference_nfc"] = ""
                r["reference_sha256"] = None
            spans = item["silence_spans"] or []
            for i, span in enumerate(spans):
                if not (0 <= span["start"] <= span["end"] <= r["duration_s"]+.1):
                    r["qc_flags"].append("invalid_silence_interval")
            invalid_words = sum(not (0 <= w["start"] <= w["end"] <= r["duration_s"]+.1) for w in words)
            if invalid_words:
                r["qc_flags"].append("invalid_word_intervals")
            r.update(split="external_timing_test", original_split="validation",
                silence_spans=spans, words=words, messages=item["messages"],
                pause_labels=["hold"]*max(0, len(spans)-1)+(["eot"] if spans else []),
                domain="task_oriented_conversation", speech_style="human_agent_turn",
                code_mixing=None, entities=[], context={}, invalid_word_intervals=invalid_words)
            rows.append(r)
    return rows

def load_indiccontext():
    rows, excluded = [], []
    for file in sorted((RAW/"indiccontext/data").glob("Hindi-*.parquet")):
        for index, item in enumerate(parquet_rows(file)):
            identity = str(item.get("file_name") or item.get("audio_path") or f"{file.stem}_{index}")
            sid = hashlib.sha256(identity.encode()).hexdigest()[:20]
            try:
                r = common("indiccontext", sid, "hi", item["reference_text_no_tags"],
                    embedded(item["audio"], file.name), item.get("duration"), item.get("speaker_id"))
            except (ValueError, RuntimeError, sf.LibsndfileError) as error:
                excluded.append({"source": "indiccontext", "source_file": file.name,
                    "row_index": index, "id": sid, "reason": str(error)})
                continue
            tagged = item.get("reference_text_with_tags") or ""
            # The downloaded release uses parentheses, despite bracketed examples in the paper.
            # Preserve glosses as glossary evidence, not invented native-script/audio spans.
            glosses = [a or b for a,b in re.findall(r"\(([^()]*)\)|\[([^\[\]]+)\]", tagged)]
            r.update(original_split="Hindi", domain=item.get("domain_name"),
                speech_style=item.get("speech_style"), code_mixing=item.get("code_mixing"),
                reference_with_tags=tagged, reference_bilingual=item.get("reference_text_no_brackets"),
                entity_glosses=glosses, entities=[],
                context={k: item.get(k) for k in ["l0_prompt", "l1_prompt", "l2_prompt", "l3_prompt", "l4_prompt", "l5_prompt", "l6_prompt"]},
                source_file=file.name, source_row=index)
            # Full source path/name and demographic fields remain only in restricted raw data.
            if not r["speaker_group"]:
                excluded.append({"source": "indiccontext", "source_file": file.name,
                    "row_index": index, "id": sid, "reason": "missing_speaker_id"})
            else:
                rows.append(r)
    return rows, excluded

class UnionFind:
    def __init__(self, n):
        self.p = list(range(n))
    def find(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i
    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)

def split_indic(rows):
    # Connect shared speakers, exact transcript duplicates and decoded-audio duplicates.
    uf = UnionFind(len(rows))
    for field in ["speaker_group", "reference_sha256", "audio_sha256"]:
        seen = {}
        for i, row in enumerate(rows):
            value = row.get(field)
            if value is None:
                continue
            if value in seen:
                uf.union(i, seen[value])
            else:
                seen[value] = i
    groups = collections.defaultdict(list)
    for i in range(len(rows)):
        groups[uf.find(i)].append(i)
    ordered = sorted(groups.values(), key=lambda indices: min(rows[i]["id"] for i in indices))
    rng = np.random.default_rng(SEED)
    # Select a deterministic grouping using only sample counts, never model results.
    target = np.array([.70, .15, .15])*len(rows)
    # Additional pre-model metadata criteria: retain domain coverage and similar
    # source-labelled speech-style/code-mixing proportions when grouping permits.
    domains = sorted({r["domain"] for r in rows})
    domain_index = {d:i for i,d in enumerate(domains)}
    metadata = np.zeros((len(ordered), len(domains)+2))
    for j, indices in enumerate(ordered):
        for i in indices:
            metadata[j,domain_index[rows[i]["domain"]]] += 1
            metadata[j,-2] += int(rows[i]["code_mixing"] is True)
            metadata[j,-1] += int(rows[i]["speech_style"] == "Read")
    global_rates = metadata[:,-2:].sum(axis=0)/len(rows)
    best = None
    for _ in range(1500):
        permutation = rng.permutation(len(ordered))
        totals = np.zeros(3)
        assignment = []
        for groupidx in permutation:
            size = len(ordered[groupidx])
            costs = [np.sum(((totals+np.eye(3)[j]*size-target)/np.maximum(target, 1))**2) for j in range(3)]
            j = int(np.argmin(costs))
            totals[j] += size
            assignment.append((int(groupidx), j))
        cost = np.sum(((totals-target)/np.maximum(target,1))**2)
        balance = np.zeros((3,len(domains)+2))
        for g,j in assignment:
            balance[j] += metadata[g]
        cost += .01*int((balance[:,:len(domains)]==0).sum())
        cost += .02*float(np.sum((balance[:,-2:]/np.maximum(totals[:,None],1)-global_rates)**2))
        if best is None or cost < best[0]:
            best = (cost, assignment, totals)
    for groupidx, j in best[1]:
        name = ["train", "validation", "test"][j]
        indices = ordered[groupidx]
        groupid = "component_" + min(rows[i]["id"].split("__")[-1] for i in indices)
        for i in indices:
            rows[i].update(split=name, split_component=groupid)
    return {"seed": SEED, "target_proportions": {"train": .7, "validation": .15, "test": .15},
        "selection_criteria":"sample counts, domain coverage, source code-mixing/style proportions; no model scores",
        "connected_components": len(ordered), "largest_component_rows": max(map(len, ordered)),
        "counts": dict(collections.Counter(r["split"] for r in rows))}

def audit(rows):
    issues = []
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        issues.append("duplicate_sample_ids")
    overlap = {}
    for field in ["speaker_group", "reference_sha256", "audio_sha256", "split_component"]:
        by_split = {s: {r[field] for r in rows if r["split"] == s and r.get(field)} for s in ["train", "validation", "test"]}
        for a, b in [("train", "validation"), ("train", "test"), ("validation", "test")]:
            count = len(by_split[a] & by_split[b])
            overlap[f"{field}:{a}:{b}"] = count
            if count:
                issues.append(f"overlap:{field}:{a}:{b}")
    ext = [r for r in rows if r["split"].startswith("external_")]
    for field in ["reference_sha256", "audio_sha256"]:
        ext_values = {r[field] for r in ext if r.get(field)}
        internal_values = {r[field] for r in rows if r["split"] in {"train", "validation", "test"} and r.get(field)}
        overlap["external_vs_internal:" + field] = len(ext_values & internal_values)
        if overlap["external_vs_internal:" + field]:
            issues.append("external_internal_overlap:" + field)
    assert not issues, issues
    return {"passed": True, "sample_ids_unique": True, "overlap_counts": overlap,
        "limitations": ["No verified cross-source speaker identity mapping.",
            "No assurance that pretrained vendors never saw public benchmark audio.",
            "Distinct domain terms may intentionally recur; exact repeated utterances are grouped.",
            "No acoustic near-duplicate or semantic-paraphrase detector; exact hashes only."]}

def export(rows):
    write_jsonl(PROCESSED/"records.jsonl", rows)
    for split in sorted({r["split"] for r in rows}):
        selected = sorted([r for r in rows if r["split"] == split], key=lambda r:r["id"])
        inputs, labels = [], []
        for row in selected:
            inputs.append({k: row[k] for k in ["id", "source", "source_revision", "language", "audio_path", "sample_rate", "duration_s"]})
            if row["source"] == "livekit":
                # Prior messages are legitimate context; gold current-turn words are never inputs.
                inputs[-1]["prior_messages"] = row["messages"]
            labels.append({k:v for k,v in row.items() if k not in ["context", "messages"]})
        write_jsonl(MANIFESTS/(split + ".jsonl"), inputs)
        write_jsonl(MANIFESTS/(split + "_labels.jsonl"), labels)
        if selected[0]["source"] == "indiccontext":
            # Explicit contextual-ASR sidecar: only choose allowed levels for each experiment.
            write_jsonl(MANIFESTS/(split + "_context.jsonl"), [{"id":r["id"], **r["context"]} for r in selected])

def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    print("Preparing external structured-value benchmark", flush=True)
    voice = load_voicecodebench()
    print("Preparing external English/Hindi endpointing benchmark", flush=True)
    live = load_livekit()
    print("Preparing Hindi contextual-speech corpus", flush=True)
    indic, excluded = load_indiccontext()
    assert len(voice) == 300, len(voice)
    assert len(live) == 800, len(live)
    assert len(indic)+len(excluded) == 3110, len(indic)+len(excluded)
    assert len(indic) > 500
    split = split_indic(indic)
    all_rows = voice+live+indic
    checks = audit(all_rows)
    export(all_rows)
    write_json(REPORTS/"split_summary.json", split)
    write_json(REPORTS/"leakage_audit.json", checks)
    write_jsonl(PROCESSED/"exclusions.jsonl", excluded)
    write_jsonl(PROCESSED/"cleaning_ledger.jsonl", [{"id":r["id"], "source":r["source"],
        "original_sample_rate":r["original_sample_rate"], "prepared_sample_rate":16000,
        "text_changed":r["text_changed_by_nfc_whitespace"], "qc_flags":r["qc_flags"],
        "action":"preserved_raw;exported_16khz_pcm16;no_trimming;no_denoising"} for r in all_rows])
    write_json(REPORTS/"preparation_summary.json", {"rows":len(all_rows), "excluded":len(excluded),
        "sources":dict(collections.Counter(r["source"] for r in all_rows)),
        "split":split, "qc_flag_counts":dict(collections.Counter(f for r in all_rows for f in r["qc_flags"])),
        "status":"prepared", "no_model_results":True})
    print(json.dumps({"prepared":len(all_rows),"excluded":len(excluded),"split":split},indent=2), flush=True)

if __name__ == "__main__":
    main()
