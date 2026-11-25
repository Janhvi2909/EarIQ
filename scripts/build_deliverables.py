"""Build the M2 cards, short report, speaking pointers and executable EDA notebook."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import nbformat as nbf
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/"reports"

def put(path,text):
    path=ROOT/path
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text.strip()+"\n",encoding="utf-8")

def markdown_table(frame):
    # Avoid an optional tabulate dependency.
    data=frame.fillna("")
    return "\n".join(["| "+" | ".join(data.columns)+" |",
        "| "+" | ".join(["---"]*len(data.columns))+" |"]+
        ["| "+" | ".join(str(x) for x in row)+" |" for row in data.itertuples(index=False,name=None)])

def main():
    summary=json.loads((REPORTS/"eda_summary.json").read_text())
    prep=json.loads((REPORTS/"preparation_summary.json").read_text())
    stats=json.loads((REPORTS/"statistical_analysis.json").read_text())
    sources=pd.read_csv(REPORTS/"tables/source_summary.csv").set_index("source")
    splits=pd.read_csv(REPORTS/"tables/split_summary.csv").set_index("split")
    configs={s["key"]:s for s in json.loads((ROOT/"configs/sources.json").read_text())}
    train,dev,test=[splits.loc[s] for s in ["train","validation","test"]]
    phase_counts=" / ".join(f"{int(x.rows):,}" for x in [train,dev,test])
    shares=" / ".join(f"{x.pct_of_hindi_development_pool:.2f}%" for x in [train,dev,test])
    extra=stats["hindi_read_minus_extempore_mean_duration_s"]
    duration=stats["indiccontext_mean_duration_s"]
    put("M2 script.md",f"""
# M2 — presentation pointers

## 1 · Objective and dataset choice

- **Objective:** understand, clean and split speech data responsibly — ready for **M3 baseline modelling**.
- **Broad scope:** listening across **assistants, dictation and voice-agent platforms**; evaluate exact values, language context and turn timing separately.
- **Three sources; {summary['total_rows']:,} prepared recordings; {summary['total_hours']:.2f} hours**. Pin versions and checksums.
- **VoiceCodeBench:** **300 recordings**, **1,482 entities / 26 types** — emails, names, numbers, IDs, URLs and dictated technical tokens. **External test only**.
- **LiveKit eot-bench:** **800 turns — 400 English + 400 Hindi**; **{summary['hold_instances']:,} hold pauses + {summary['eot_instances']:,} turn endings**. **External timing test**.
- **IndicContextEval Hindi:** **3,110 downloaded → 3,102 retained**, **124 speakers**, **23 domains**. **Eight empty references excluded**; raw data retained.
- **{summary['hindi_source_code_mixing_true']:,} source-labelled code-mixed recordings**; read + extempore speech. **Not an independently audited Hinglish-intake dataset**.

## 2 · Train / validation / test

- **Hindi project split:** **train {int(train.rows):,} ({train.pct_of_hindi_development_pool:.2f}%)**; **validation {int(dev.rows):,} ({dev.pct_of_hindi_development_pool:.2f}%)**; **test {int(test.rows):,} ({test.pct_of_hindi_development_pool:.2f}%)**.
- **Speakers:** **{int(train.known_speakers)} train / {int(dev.known_speakers)} validation / {int(test.known_speakers)} test**; no speaker crosses these splits.
- **Grouped split:** speakers + repeated transcripts + duplicate decoded audio stay together; **seed 20261028**.
- **Zero detected cross-split overlap** for those exact checks. Shared domain words are allowed; **no claim of unseen vocabulary everywhere**.
- **Public benchmarks stay separate**; do not train on them or combine their percentages with the Hindi split.

## 3 · Preprocessing and cleaning

- **Decoded and checked audio**; exported **16 kHz, mono, PCM16**. Resampled **300** original 48 kHz recordings.
- **Five stereo files:** selected the speech channel after checking the other channel was near-silent.
- **Unicode NFC + whitespace cleaning**; preserve **scripts, leading zeros, letters, decimals and punctuation**. Keep originals.
- **No silence trimming or blanket denoising** — preserve pauses and self-corrections.
- **Eight unusable text references excluded**; **two clipping flags + two duration mismatches retained and logged**.
- **Gold separated from inputs**: transcripts, exact values and future word/pause timings are **evaluation labels**, not live model features.

## 4 · EDA and statistical analysis

- **Seven figure groups:** dataset size/hours; entity classes; audio lengths; split/style balance; pauses; Hindi domains; audio quality.
- **Median duration:** Hindi **{sources.loc['indiccontext','median_s']:.2f}s**, timing turns **{sources.loc['livekit','median_s']:.2f}s**, exact-value recordings **{sources.loc['voicecodebench','median_s']:.2f}s**.
- **2,000 speaker-cluster bootstrap resamples**; **95% intervals** — related turns are not independent people.
- **Read speech averages {extra['estimate']:.2f}s longer** than extempore; 95% interval **{extra['ci95_low']:.2f}–{extra['ci95_high']:.2f}s**. Descriptive association, not causation.
- **Timing artifact:** every English terminal silence is **1.5s** — do not use file ending/future silence to predict a turn ending.

## 5 · Privacy, limits and readiness

- **Licensed public data**, pseudonymous speaker IDs, restricted raw audio; no voice cloning, real customer collection or external ASR uploads in M2.
- **Data cards + provenance + cleaning log + split audit + EDA notebook** delivered; loader checked against all prepared files.
- **Benchmark caution:** custom Hindi holdout ≠ published full benchmark. Compare providers on the **same holdout** in M3/M4.
- **Available labels:** exact English entities, Hindi transcripts/context/glosses, turn pauses. **No invented gold entity audio boundaries or interactive repair outcomes**.
- **M2 prepares data; M3 measures models.** No new model accuracy result claimed.

*Evidence: [data report](reports/M2_Data_Report.md), [data cards](docs/data_cards/PROJECT.md), [EDA figures](reports/M2_EDA_Figures.pdf), [split audit](reports/leakage_audit.json).*
""")
    source_table=sources.reset_index()[["source","rows","hours","known_speakers"]].copy()
    source_table["hours"]=source_table.hours.map(lambda x:f"{x:.3f}")
    split_table=splits.reset_index()[["split","rows","known_speakers","pct_of_hindi_development_pool"]].copy()
    split_table["pct_of_hindi_development_pool"]=split_table.pct_of_hindi_development_pool.map(lambda x:"—" if pd.isna(x) else f"{x:.2f}%")
    put("reports/M2_Data_Report.md",f"""
# M2 — Data understanding and preparation

Prepared 28 October 2026. Scope: reliable listening across voice assistants, dictation, voice input and agent platforms. Call-centre intake is one example, not the project boundary. This report records **executed preparation**, not proposed data collection or model performance.

## Data and roles

{markdown_table(source_table)}

Total: **{summary['total_rows']:,} retained recordings, {summary['total_hours']:.3f} decoded audio hours**. Eight additional Hindi rows were excluded because the native-script reference was empty. All original source files are retained. The sources are complementary tasks, not one homogeneous training dataset.

- VoiceCodeBench: source-annotated **1,482 exact entities, 26 types, 8 workflow domains**. Human-read English recordings of synthetic scenarios. Includes only six source-labelled Indian-accent recordings: insufficient for an Indian-English generalisation claim.
- LiveKit: the pinned **public sample**, English/Hindi only, not the unpublished/full-revision reference population. **2,324 pause spans: 1,524 hold and 800 final spans**. Speaker/conversation IDs are not supplied, so no fabricated grouping IDs were inferred.
- IndicContextEval: the Hindi language split, repurposed as a **custom speaker-grouped project corpus**. It covers all 23 source domains, {summary['hindi_extempore']:,} extempore recordings and {summary['hindi_source_code_mixing_true']:,} source-labelled code-mixed recordings. The latter is a source label, not a new human language audit. Domain terms/borrowings are not equivalent to every natural Hinglish use case.

The formerly uncertain IndicContextEval URLs resolved through the public API; the old/new identifiers returned the same pinned revision. That alias is **not counted as two datasets**. No 720-speaker/turn collection was fabricated. New consented recordings remain a possible future extension, not a prerequisite claimed completed here.

## Split policy and actual split

{markdown_table(split_table)}

Percentages apply **only to the 3,102-row Hindi project corpus**. Targets were 70/15/15 by recording count, not by speaker count. Splitting connects shared speaker IDs, identical NFC/casefolded transcripts and identical decoded prepared audio before assignment. The selected assignment uses seed **20261028**, sample-count balance and source metadata coverage (domains, speech style, code-mixing); no model scores. Repeated domain vocabulary is allowed and its overlap is explicitly measured in `tables/gloss_vocabulary_overlap.csv`.

All train/validation/test speaker, transcript and decoded-audio intersections are zero. Exact transcript/audio intersections with the external corpora are also zero. This does not prove absence of acoustic near-duplicates, semantic paraphrases, shared unidentified people across sources or prior exposure in pretrained models.

Public source splits remain identifiable as `original_split`. The Hindi custom split changes the benchmark protocol; **never compare its test score directly to Sarvam's eight-language overall published score**. Rerun comparators on the same holdout for a claim about improvement. External English/timing benchmarks stay out of training and parameter selection.

## Cleaning and audio QC

- Decoded all included audio; checked finite samples, nonzero duration, channel layout and reference availability.
- Exported 16 kHz mono PCM16 WAV, retaining raw recordings and declared durations. Resampled all 300 VoiceCodeBench recordings from 48 kHz. Five had a near-silent first channel; select the second only after an RMS-ratio check. Ambiguous multichannel audio causes preparation to fail instead of silently mixing speakers.
- Kept source transcripts, NFC/whitespace-cleaned references and canonical values separate. **{summary['text_normalised_rows']:,} references changed under NFC/whitespace cleaning**. No digits, leading zeros, diacritics or identity-bearing punctuation were stripped from target values.
- Preserved silences, disfluencies and self-corrections. No amplitude normalisation, denoising or augmentation was performed.
- Excluded eight empty Hindi references using an explicit row ledger; none removed based on model errors. Two clipping flags (>0.1% near-full-scale samples) and two >0.1s declared-duration mismatches remain in the prepared set. These are flags, not automatic proof that the speech is unusable.
- Exact transcript duplicate groups are retained with connected grouping in Hindi. Official benchmark membership is preserved, including repeated short utterances. No decoded-audio duplicates were found within any source.

See the row-level `data/processed/cleaning_ledger.jsonl` and `exclusions.jsonl`. Paths and labels live outside the tracked report to avoid bundling raw speech in a code handover.

## EDA and statistical results

Seven figure groups and machine-readable supporting tables cover composition, entity imbalance/length, duration, domain/style/code-mixing coverage, pauses and audio quality. [Figure PDF](M2_EDA_Figures.pdf)

Hindi mean duration is **{duration['estimate']:.3f}s**, with speaker-cluster-bootstrap 95% interval **[{duration['ci95_low']:.3f}, {duration['ci95_high']:.3f}]s**. The source-labelled code-mixing fraction is **{100*stats['hindi_source_label_code_mixing_fraction']['estimate']:.2f}%**. Read-minus-extempore mean duration is **{extra['estimate']:.3f}s**, interval **[{extra['ci95_low']:.3f}, {extra['ci95_high']:.3f}]s**. Use these as descriptive associations in this collected corpus, not causal or population-wide findings.

Bootstrap: **2,000 resamples of whole speakers**, seed 20261028, percentile intervals. Each resample retains all recordings of a sampled speaker. For missing LiveKit speaker/session IDs, pause statistics are descriptive only; we do not invent independent-speaker confidence intervals. Intervals describe observed-source sampling variation and do not establish demographic representativeness.

**Important artifact:** all 400 English final silence spans are exactly **1.5s** within floating-point tolerance. This is consistent with release/padding construction and is not evidence that natural English turn gaps always last 1.5s. Full-file duration, final-span length/end and future word timestamps must never be live decision features. Labels follow the source convention: earlier pauses are hold; final pause is end-of-turn. A causal evaluator must see audio/context only up to the decision time.

## Labels, input separation and privacy

- Separate `*_labels.jsonl` stores gold transcripts, entities, timing and QC; the inference manifest contains only audio pointers, language and source metadata. Prior LiveKit messages are legitimate preceding context, not the current gold transcript.
- Contextual Hindi prompts are in an opt-in sidecar. The loader selects **one fixed L0–L6 level**; it does not feed all prompt conditions at once. L4/L5 are source-provided domain vocabularies, not a dictionary mined from held-out answers. Training-derived statistics/vocabularies must use training only in M3.
- Hindi source glosses are preserved as textual evidence; no unverified native entity or audio spans were invented. Public source QC is documented; **no independent human reannotation is claimed**. Exact within-entity cutoff evaluation and genuine interactive repair require additional aligned/adjudicated labels or a compatible interactive benchmark later.
- Raw source speaker IDs/paths and demographic metadata are excluded from inference manifests. Speaker hashes are pseudonyms, not guaranteed anonymity; voice itself can identify someone. Local audio and gold are excluded from Git by default.
- Licenses: IndicContextEval CC BY 4.0; LiveKit card CC BY 4.0 with a code-README discrepancy documented separately; VoiceCodeBench MIT non-audio plus specific audio terms prohibiting voice cloning. Source notices are copied under `docs/source_notices/`.
- No new personal recordings, voice cloning, customer records, paid API calls or audio uploads to external ASR were performed. Raw audio is locally restricted and not bundled for public release. See [privacy policy](../docs/PRIVACY.md).

## Readiness and milestone checklist

| Industry M2 requirement | Executed artifact |
| --- | --- |
| Data card | Project and three source cards under `docs/data_cards/` |
| Exploratory analysis | `notebooks/M2_EDA.ipynb`, seven figure groups, CSV tables |
| Data cleaning | `scripts/prepare_data.py`, cleaning/exclusion ledgers |
| Statistical analysis | `statistical_analysis.json`, table and grouped bootstrap implementation |
| Train/validation/test | Frozen Hindi project manifests; independent external manifests; `leakage_audit.json` |
| Privacy | `docs/PRIVACY.md`, source notices and pseudonymous exports |

The prepared tasks are **Hindi contextual ASR, English exact-value evaluation and English/Hindi endpointing**. Their data preparation is complete. Coverage of every language, locale, Indian accent, entity audio boundary and interactive repair behaviour is **not** implied. Model development and accuracy/latency measurement begin in M3. Published baseline artifacts are preserved as references, not reported as our results.
""")
    put("docs/data_cards/PROJECT.md",f"""
# Project data card

- **Purpose:** prepare speech data for a capture layer across assistants, dictation and voice agents. Exact values, contextual recognition and endpoint timing are separate evaluation tracks.
- **Version:** 28 October 2026; source commits in `configs/sources.json`; downloaded-file SHA-256 and upstream LFS/size verification in `data/raw/download_manifest.json`; prepared manifest checksums in `reports/verification.json` after validation.
- **Composition:** {summary['total_rows']:,} recordings / {summary['total_hours']:.3f} hours; 3 sources. [Measured table](../../reports/tables/source_summary.csv)
- **Training/development:** 3,102 retained Hindi contextual-speech samples, split {phase_counts} ({shares}). Official Hindi source is a language split, not this train/dev/test partition.
- **External tests:** 300 English structured-value recordings; 800 English/Hindi endpointing turns. Kept out of training/tuning.
- **Labels available:** source transcripts/canonical entities/context/glosses and pause/word timings where supplied. No newly human-adjudicated audio entity boundaries or interactive repair outcomes.
- **Known speaker support:** 124 Hindi speakers; 85 VoiceCodeBench source IDs; LiveKit speaker IDs absent. No cross-corpus identity matching attempted.
- **Language limitations:** Hindi source code-mixing label includes domain terms; six VoiceCodeBench recordings carry an Indian accent label. Not enough for broad Indian-English, demographic or locale claims.
- **Splits/leakage:** grouped by source speakers and exact transcript/audio duplicate components; 70/15/15 target by rows, fixed seed; shared domain terms allowed and measured. Exact cross-split intersections zero; near-duplicates/pretraining contamination not ruled out.
- **Inputs:** audio pointers + language; preceding messages for timing; optional fixed contextual prompt level for Hindi. Gold labels are separate.
- **Audio:** derived 16 kHz mono PCM16; no pause trimming, denoising or augmentation. Raw files retained.
- **Licensing/privacy:** per-source rules differ; do not treat the bundle as uniformly MIT/CC. Local research use; no raw-audio public release by default. [Policy](../PRIVACY.md)
- **Access:** all selected source files acquired publicly without local credentials; public APIs were used. Other probed/gated datasets were not used.
- **Provenance and exclusions:** eight empty references excluded; all decisions logged. [Report](../../reports/M2_Data_Report.md)
- **Maintenance:** rerun acquisition/preparation/analysis/verification explicitly for a new release. Keep existing manifests frozen for comparisons. If a rights/access issue is reported, quarantine affected rows, regenerate a new version and report invalidated comparisons.
""")
    details={
        "voicecodebench":("VoiceCodeBench", "English", "Source human-read synthetic scenarios; exact spoken and canonical values. 26 entity types, 8 workflow domains; source-script/annotation generation was LLM-assisted, audio human-recorded. Paid contributors consented according to the publisher card.",
            "External entity test; official test-only membership retained. No training/tuning. Use official evaluator/version for CTEM/TSR comparisons; local canonical-field correctness is a different measure.",
            "MIT for non-audio; audio terms specifically prohibit voice cloning and require notice preservation. Copies/derived representations remain subject to audio terms.",
            "Controlled read speech; heavily American-accented. Only six rows labelled Indian accent. Source demographic metadata is coarse/unverified; no claim of authentic customer calls."),
        "livekit":("LiveKit eot-bench public sample", "English + Hindi", "400 turns per selected language from human–agent conversations. Source gives word timings, silence intervals and prior messages; final silence labelled eot, previous spans hold by source convention.",
            "External timing evaluation only. Original source split is validation. No project random train/test split invented. Published full-revision model scores cannot be attached to this sample without a same-revision rerun.",
            "Pinned dataset README metadata says CC BY 4.0; upstream code README also describes Apache 2.0 for the dataset. Follow the data-card attribution condition for local use; do not redistribute raw audio until conflicting provenance is clarified.",
            "No released speaker/conversation IDs; no speaker-disjointness guarantee across unknown people. Six rows lack transcript words but retain endpointing audio. Every English final span is 1.5s: beware release/padding leakage."),
        "indiccontext":("IndicContextEval Hindi project corpus", "Hindi with source-labelled code mixing", "Read/extempore domain speech with native-script references, gloss tags, speakers, domains and L0–L6 contextual prompts. Original full benchmark: 8 languages; only Hindi downloaded. 3,110 original rows, eight empty-reference exclusions.",
            f"Custom train/validation/test: {phase_counts} ({shares}), grouped speakers/duplicate components. Keep original_split=Hindi. These are project splits, not publisher train/test partitions; rerun providers on the same holdout.",
            "CC BY 4.0 per the acquired pinned dataset card. Preserve citation and attribute transformations. No new consent inferred from the license; no new recordings collected.",
            "Domain/code-mixing labels and transcript QC are publisher-provided. Glosses may be English equivalents of native terms; not verified time-aligned gold entities. Do not infer arbitrary phone/email ability or natural conversational repair from this corpus."),
    }
    for key,(title,lang,origin,role,license_text,limits) in details.items():
        row=sources.loc[key]
        put(f"docs/data_cards/{key}.md",f"""
# {title}

- **Source:** https://huggingface.co/datasets/{configs[key]['repo']}
- **Pinned revision:** `{configs[key]['revision']}`
- **Acquired/retained:** {int(row.rows):,} retained recordings; {row.hours:.3f} hours; {int(row.known_speakers)} known source speaker IDs (zero means unavailable, not zero people).
- **Language:** {lang}.
- **Origin and labels:** {origin}
- **Role and splits:** {role}
- **License:** {license_text}
- **Transformations:** decoded audio QA; 16 kHz mono PCM16 derived files; lossless Unicode NFC/whitespace transcript form; preserved raw/canonical forms; no silence trimming or denoising. Detailed changes and exclusions in the cleaning ledger.
- **Privacy:** identifiable voices/content may remain; raw audio restricted locally. Hashes are pseudonyms, not anonymisation. No speaker identification, voice cloning or third-party audio uploads in this milestone.
- **Limitations:** {limits}
- **Audit:** decoded audio and exact hashes checked across prepared records; no new manual transcription/annotation claimed. Measured EDA and distributions in `reports/tables/`; source notes preserved in `docs/source_notices/`.
""")
    notices=ROOT/"docs/source_notices"
    notices.mkdir(parents=True,exist_ok=True)
    for key in configs:
        for name in ["README.md","LICENSE","DATASET_CARD.md"]:
            file=ROOT/"data/raw"/key/name
            if file.exists(): shutil.copy2(file,notices/f"{key}_{name}")
    shutil.copy2(ROOT/"data/raw/voicecodebench/baselines/paper_results.csv",REPORTS/"tables/published_voicecodebench_paper_reference.csv")
    nb=nbf.v4.new_notebook()
    nb.metadata.kernelspec={"display_name":"NLP M2 (local .venv)","language":"python","name":"python3"}
    nb.cells=[nbf.v4.new_markdown_cell("# M2 — executed data exploration\n\nReal prepared data. No model performance is claimed. Rerun the preparation scripts before this notebook if source versions change. Counts below come from local manifests/CSV tables."),
        nbf.v4.new_code_cell("from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import display, Image\nROOT = Path.cwd()\nif not (ROOT / 'reports').exists(): ROOT = ROOT.parent\nREPORTS = ROOT / 'reports'\nsummary = json.loads((REPORTS / 'eda_summary.json').read_text())\nprint({k:v for k,v in summary.items() if k != 'manifest_files'})"),
        nbf.v4.new_markdown_cell("## Data cards and composition\nThree complementary tasks; external benchmarks are not training splits."),
        nbf.v4.new_code_cell("display(pd.read_csv(REPORTS / 'tables/source_summary.csv'))\ndisplay(pd.read_csv(REPORTS / 'tables/split_summary.csv'))"),
        nbf.v4.new_markdown_cell("## Cleaning, formats and duplicates\nRetain source membership in external tests. Hindi duplicate utterances remain within connected speaker groups. Raw speech is retained; eight empty native-script references were excluded."),
        nbf.v4.new_code_cell("for name in ['audio_format_counts', 'qc_flags', 'duplicates', 'gloss_vocabulary_overlap']:\n    print(name)\n    display(pd.read_csv(REPORTS / f'tables/{name}.csv'))"),
        nbf.v4.new_markdown_cell("## Statistical analysis\n2,000 whole-speaker bootstrap resamples, fixed seed 20261028, percentile 95% intervals. LiveKit lacks grouping IDs, so only descriptive pause summaries are given. These are collected-corpus distributions, not model results or population-wide causal estimates."),
        nbf.v4.new_code_cell("display(pd.read_csv(REPORTS / 'tables/statistical_analysis.csv'))\ndisplay(pd.read_csv(REPORTS / 'tables/pause_summary.csv'))"),
        nbf.v4.new_markdown_cell("## Figures\nEnglish terminal spans are all 1.5s. Do not use future file-end/padding information for endpoint predictions. Source code-mixing flags are not an independent Hinglish audit."),
        nbf.v4.new_code_cell("for path in sorted((REPORTS / 'figures').glob('*.png')):\n    print(path.name)\n    display(Image(filename=str(path)))"),
        nbf.v4.new_markdown_cell("## Leakage audit and baseline loader\nGold references live outside inference inputs. Context is an optional fixed prompt condition; no future transcript/word/end labels are input features."),
        nbf.v4.new_code_cell("import sys\nsys.path.insert(0, str(ROOT))\nfrom src.listening_data import iter_inputs, iter_supervised\naudit = json.loads((REPORTS / 'leakage_audit.json').read_text())\nassert audit['passed']\nassert all(v == 0 for v in audit['overlap_counts'].values())\nprint(audit)\nfirst = next(iter_inputs('train'))\nprint('Input fields:', sorted(first))\nassert 'reference_nfc' not in first and 'entities' not in first\nprint('Loader rows:', {s: sum(1 for _ in iter_inputs(s)) for s in ['train', 'validation', 'test', 'external_entity_test', 'external_timing_test']})"),
        nbf.v4.new_markdown_cell("## Privacy and limitations\nLicensed public data; restricted raw audio; no new participants or API uploads. Source notices/privacy policy are under `docs/`. Audio can identify people even after speaker IDs are hashed. Exact overlap checks do not rule out near-duplicates or pretrained-model exposure. Entity audio boundaries and interactive repair outcomes are not invented.")]
    notebook=ROOT/"notebooks/M2_EDA.ipynb"
    notebook.parent.mkdir(exist_ok=True)
    nbf.write(nb,notebook)
    print("Generated report, 4 data cards, M2 pointer script, source notices and notebook.")

if __name__=="__main__": main()
