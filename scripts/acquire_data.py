"""Download public, pinned M2 source artifacts. Never reads local credentials."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
SOURCES = {
    "voicecodebench": "besimple-ai/voice-code-bench",
    "livekit": "livekit/eot-bench-data",
    "indiccontext": "AI4Bharat/IndicContextEval",
    "indiccontext_legacy": "SakshiJ/IndicContextEval",
    "spokenwoz": "AlibabaResearch/SpokenWOZ",
    "slue": "asapp/slue",
}

def session():
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=Retry(total=4, backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504])))
    return s

def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        return path
    with session().get(url, stream=True, timeout=(20, 120)) as r:
        r.raise_for_status()
        temp = path.with_suffix(path.suffix + ".part")
        with temp.open("wb") as f:
            for block in r.iter_content(1024 * 1024):
                f.write(block)
        temp.replace(path)
    print(f"saved {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)", flush=True)
    return path

def inspect():
    config_path = ROOT/"configs/sources.json"
    pins = {s["key"]:s["revision"] for s in json.loads(config_path.read_text())} if config_path.exists() else {}
    def one(item):
        key, repo = item
        revision_path = f"/revision/{pins[key]}" if key in pins else ""
        r = session().get(f"https://huggingface.co/api/datasets/{repo}{revision_path}?blobs=true", timeout=45)
        result = {"repo": repo, "http_status": r.status_code}
        if r.ok:
            meta = r.json()
            folder = RAW / key
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "repo_metadata.json").write_text(json.dumps(meta, indent=2))
            result.update(revision=meta.get("sha"), gated=meta.get("gated"),
                          files=[{"path": x["rfilename"], "size": x.get("size")} for x in meta.get("siblings", [])])
            for name in ["README.md", "LICENSE", "DATASET_CARD.md"]:
                if any(x["rfilename"] == name for x in meta.get("siblings", [])):
                    download(f"https://huggingface.co/datasets/{repo}/resolve/{meta['sha']}/{name}", folder/name)
        return key, result
    results = dict(concurrent.futures.ThreadPoolExecutor(6).map(one, SOURCES.items()))
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "access_audit.json").write_text(json.dumps(results, indent=2))
    for key, result in results.items():
        print(key, json.dumps(result, ensure_ascii=False)[:7000], flush=True)

def acquire(only=None):
    config = json.loads((ROOT/"configs/sources.json").read_text())
    if only:
        config = [s for s in config if s["key"] == only]
    jobs = []
    for source in config:
        for name in source["files"]:
            url = f"https://huggingface.co/datasets/{source['repo']}/resolve/{source['revision']}/{name}"
            jobs.append((url, RAW/source["key"]/name))
    with concurrent.futures.ThreadPoolExecutor(6) as executor:
        list(executor.map(lambda pair: download(*pair), jobs))
    manifest = []
    for source in config:
        meta = json.loads((RAW/source["key"]/"repo_metadata.json").read_text())
        upstream = {x["rfilename"]:x for x in meta["siblings"]}
        for name in source["files"]:
            path = RAW/source["key"]/name
            digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
            expected = upstream[name]
            if expected.get("size") is not None:
                assert path.stat().st_size == expected["size"], (source["key"], name, "size_mismatch")
            upstream_sha = expected.get("lfs", {}).get("sha256")
            if upstream_sha:
                assert digest == upstream_sha, (source["key"], name, "upstream_hash_mismatch")
            manifest.append({"source": source["key"], "repo": source["repo"],
                "revision": source["revision"], "file": name, "bytes": path.stat().st_size,
                "sha256": digest, "upstream_lfs_sha256": upstream_sha,
                "size_verified": expected.get("size") == path.stat().st_size})
    (RAW/(f"download_manifest_{only}.json" if only else "download_manifest.json")).write_text(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--inspect", action="store_true")
    p.add_argument("--metadata-only", action="store_true")
    p.add_argument("--source", choices=["voicecodebench", "livekit", "indiccontext"])
    args = p.parse_args()
    if args.inspect:
        inspect()
    elif args.metadata_only:
        config = json.loads((ROOT/"configs/sources.json").read_text())
        for source in config:
            for name in source["files"]:
                if name.endswith(".jsonl"):
                    download(f"https://huggingface.co/datasets/{source['repo']}/resolve/{source['revision']}/{name}", RAW/source["key"]/name)
    else:
        acquire(args.source)
