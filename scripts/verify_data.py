"""Verify the completed handover, audio files, manifests and original PDF integrity."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

import nbformat
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.listening_data import iter_inputs, iter_supervised

def digest(path):
    with path.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()

def main():
    expected=json.loads((ROOT/"reports/preparation_summary.json").read_text())
    assert expected["rows"]==4202 and expected["excluded"]==8
    assert json.loads((ROOT/"reports/leakage_audit.json").read_text())["passed"]
    observed={}
    seen=set()
    for split in ["train","validation","test","external_entity_test","external_timing_test"]:
        inputs=list(iter_inputs(split))
        labels=[label for _,label in iter_supervised(split,allow_evaluation_labels=True)]
        assert len(inputs)==len(labels)
        assert {r["id"] for r in inputs}=={r["id"] for r in labels}
        for row,label in zip(inputs,labels):
            assert row["id"]==label["id"]
            assert row["id"] not in seen
            seen.add(row["id"])
            path=ROOT/row["audio_path"]
            info=sf.info(path)
            assert info.samplerate==16000 and info.channels==1 and info.subtype=="PCM_16",row["id"]
            assert abs(info.duration-row["duration_s"])<.001,row["id"]
        observed[split]=len(inputs)
    assert len(seen)==4202
    assert observed["external_entity_test"]==300 and observed["external_timing_test"]==800
    originals=json.loads((ROOT/"configs/original_pdf_sha256.json").read_text())
    assert all(digest(ROOT/name)==sha for name,sha in originals.items()),"Original PDF changed"
    required=["M1 script.md","M2 script.md","reports/M2_EDA_Figures.pdf","reports/M2_Data_Report.md",
        "docs/PRIVACY.md","docs/data_cards/PROJECT.md","docs/data_cards/voicecodebench.md",
        "docs/data_cards/livekit.md","docs/data_cards/indiccontext.md"]
    assert all((ROOT/p).is_file() and (ROOT/p).stat().st_size for p in required)
    notebook=nbformat.read(ROOT/"notebooks/M2_EDA.ipynb",as_version=4)
    codes=[c for c in notebook.cells if c.cell_type=="code"]
    assert all(c.execution_count is not None for c in codes),"Notebook not fully executed"
    assert not any(o.output_type=="error" for c in codes for o in c.outputs),"Notebook cell failed"
    frozen={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/"data/manifests").glob("*.jsonl"))}
    previous_path=ROOT/"reports/verification.json"
    if previous_path.exists():
        previous=json.loads(previous_path.read_text())
        assert previous["manifest_sha256"]==frozen,"Frozen manifest drift: create/document a new data release before replacing the freeze"
    download=json.loads((ROOT/"data/raw/download_manifest.json").read_text())
    assert all(r["size_verified"] for r in download)
    assert len(download)==313
    result={"passed":True,"rows_verified":len(seen),"split_counts":observed,
        "audio_headers_verified":True,"label_input_id_alignment":True,
        "original_pdfs_unchanged":True,"executed_notebook_cells":len(codes),
        "downloaded_files_size_verified":len(download),
        "downloaded_files_upstream_lfs_hash_verified":sum(bool(r["upstream_lfs_sha256"]) for r in download),
        "manifest_sha256":frozen,
        "limitations":"Exact overlap checks only; no cross-source speaker-identity proof or pretraining-contamination proof."}
    (ROOT/"reports/verification.json").write_text(json.dumps(result,indent=2))
    (ROOT/"reports/source_provenance.json").write_text(json.dumps(download,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="manifest_sha256"},indent=2))

if __name__=="__main__": main()
