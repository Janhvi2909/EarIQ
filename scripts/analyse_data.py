"""Generate measured M2 EDA tables, figures and grouped statistical summaries."""
from __future__ import annotations
import collections
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT/".cache/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

REPORTS = ROOT/"reports"
TABLES, FIGURES = REPORTS/"tables", REPORTS/"figures"
SOURCE_NAMES = {"voicecodebench":"VoiceCodeBench", "livekit":"LiveKit EoT (en + hi)", "indiccontext":"IndicContextEval (Hindi)"}
COLOURS = {"voicecodebench":"#dd6b35", "livekit":"#39858e", "indiccontext":"#5062a3"}

def csv(name, rows):
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.to_csv(TABLES/(name+".csv"),index=False)
    return frame

def cluster_ratio(frame, numerator, denominator, group, seed=20261028, trials=2000):
    grouped = frame.groupby(group)[[numerator,denominator]].sum().to_numpy(float)
    rng = np.random.default_rng(seed)
    sums = grouped[rng.integers(0,len(grouped),size=(trials,len(grouped)))].sum(axis=1)
    values = sums[:,0]/sums[:,1]
    return {"estimate":float(grouped[:,0].sum()/grouped[:,1].sum()),
        "ci95_low":float(np.quantile(values,.025)),"ci95_high":float(np.quantile(values,.975)),
        "groups":len(grouped),"resamples":trials,"seed":seed}

def main():
    TABLES.mkdir(parents=True,exist_ok=True)
    FIGURES.mkdir(parents=True,exist_ok=True)
    rows = [json.loads(line) for line in (ROOT/"data/processed/records.jsonl").read_text().splitlines()]
    scalar_keys = ["id","source","split","speaker_group","language","domain","speech_style","duration_s",
        "original_sample_rate","original_channels","selected_channel","clipped_fraction","rms_dbfs","code_mixing",
        "text_changed_by_nfc_whitespace","audio_sha256","reference_sha256"]
    frame = pd.DataFrame([{k:r.get(k) for k in scalar_keys} for r in rows])
    frame["n"] = 1
    source_rows=[]
    for source,g in frame.groupby("source"):
        source_rows.append({"source":source,"rows":len(g),"hours":g.duration_s.sum()/3600,
            "known_speakers":g.speaker_group.nunique(),"median_s":g.duration_s.median(),
            "q25_s":g.duration_s.quantile(.25),"q75_s":g.duration_s.quantile(.75),
            "p95_s":g.duration_s.quantile(.95),"min_s":g.duration_s.min(),"max_s":g.duration_s.max(),
            "missing_speaker_rows":int(g.speaker_group.isna().sum())})
    sources=csv("source_summary",source_rows)
    split_rows=[]
    indic=frame[frame.source=="indiccontext"].copy()
    for split,g in frame.groupby("split"):
        split_rows.append({"split":split,"rows":len(g),"hours":g.duration_s.sum()/3600,
            "known_speakers":g.speaker_group.nunique(),
            "pct_of_hindi_development_pool":100*len(g)/len(indic) if split in {"train","validation","test"} else None,
            "code_mixing_true":int((g.code_mixing==True).sum()),
            "code_mixing_true_pct":100*float((g.code_mixing==True).mean()) if split in {"train","validation","test"} else None})
    splits=csv("split_summary",split_rows)
    csv("hindi_domain_counts",indic.groupby(["split","domain"]).size().rename("rows").reset_index())
    csv("speech_style_counts",frame.groupby(["source","split","speech_style"]).size().rename("rows").reset_index())
    csv("audio_format_counts",frame.groupby(["source","original_sample_rate","original_channels","selected_channel"]).size().rename("rows").reset_index())
    csv("audio_quality",frame[["id","source","clipped_fraction","rms_dbfs","original_sample_rate","original_channels"]])
    voice=[r for r in rows if r["source"]=="voicecodebench"]
    entity_counts=collections.Counter(e["type"] for r in voice for e in r["entities"])
    entities=csv("entity_types",[{"type":k,"entities":v,"pct":100*v/sum(entity_counts.values())} for k,v in entity_counts.most_common()])
    csv("entity_lengths",[{"type":e["type"],"canonical_chars":len(e["canonical"]),"spoken_words":len(e["acoustic"].split())} for r in voice for e in r["entities"]])
    csv("voice_domains",pd.DataFrame([{"domain":r["domain"],"difficulty":r["difficulty"]} for r in voice]).value_counts().rename("rows").reset_index())
    pauses=[]
    for r in rows:
        if r["source"]!="livekit": continue
        for i,(span,label) in enumerate(zip(r["silence_spans"],r["pause_labels"])):
            pauses.append({"id":r["id"],"language":r["language"],"label":label,"index":i,
                "start_s":span["start"],"end_s":span["end"],"duration_s":span["end"]-span["start"]})
    pause_frame=csv("pauses",pauses)
    pause_stats=csv("pause_summary",pause_frame.groupby(["language","label"]).duration_s.agg(["count","median","mean","min","max"]).reset_index())
    qc=collections.Counter(flag for r in rows for flag in r["qc_flags"])
    csv("qc_flags",[{"flag":k,"rows":v} for k,v in sorted(qc.items())])
    # Duplicate groups are counted, not dropped from official benchmark releases.
    duplicate_stats=[]
    for source,g in frame.groupby("source"):
        for field in ["reference_sha256","audio_sha256"]:
            counts=g[field].dropna().value_counts()
            duplicate_stats.append({"source":source,"field":field,"duplicate_groups":int((counts>1).sum()),
                "additional_rows":int((counts-1).clip(lower=0).sum())})
    csv("duplicates",duplicate_stats)
    stats={}
    for source,g in frame[frame.speaker_group.notna()].groupby("source"):
        stats[source+"_mean_duration_s"]=cluster_ratio(g,"duration_s","n","speaker_group")
    indic["code_mix_n"]=(indic.code_mixing==True).astype(int)
    stats["hindi_source_label_code_mixing_fraction"]=cluster_ratio(indic,"code_mix_n","n","speaker_group")
    # Mean duration difference: read vs extempore; resample speakers, not individual turns.
    style=indic.assign(read_s=indic.duration_s*(indic.speech_style=="Read"),
        read_n=(indic.speech_style=="Read").astype(int),
        ext_s=indic.duration_s*(indic.speech_style=="Extempore"),
        ext_n=(indic.speech_style=="Extempore").astype(int))
    groups=style.groupby("speaker_group")[["read_s","read_n","ext_s","ext_n"]].sum().to_numpy(float)
    rng=np.random.default_rng(20261028)
    sampled=groups[rng.integers(0,len(groups),size=(2000,len(groups)))].sum(axis=1)
    diff=sampled[:,0]/sampled[:,1]-sampled[:,2]/sampled[:,3]
    total=groups.sum(axis=0)
    stats["hindi_read_minus_extempore_mean_duration_s"]={"estimate":float(total[0]/total[1]-total[2]/total[3]),
        "ci95_low":float(np.quantile(diff,.025)),"ci95_high":float(np.quantile(diff,.975)),
        "groups":len(groups),"resamples":2000,"seed":20261028}
    (REPORTS/"statistical_analysis.json").write_text(json.dumps(stats,indent=2))
    csv("statistical_analysis",[{"statistic":k,**v} for k,v in stats.items()])
    # Measure vocabulary overlap openly; recurring domain words are allowed, exact utterances are grouped.
    vocab={s:{text.casefold() for r in rows if r["source"]=="indiccontext" and r["split"]==s for text in r["entity_glosses"]} for s in ["train","validation","test"]}
    csv("gloss_vocabulary_overlap",[{"a":a,"b":b,"a_terms":len(vocab[a]),"b_terms":len(vocab[b]),"shared_terms":len(vocab[a]&vocab[b])} for a,b in [("train","validation"),("train","test"),("validation","test")]])
    plt.rcParams.update({"font.family":"DejaVu Sans","axes.spines.top":False,"axes.spines.right":False,
        "figure.facecolor":"#fbfaf7","axes.facecolor":"#fbfaf7","axes.titleweight":"bold"})
    with PdfPages(REPORTS/"M2_EDA_Figures.pdf") as pdf:
        def save(fig,name):
            fig.tight_layout()
            fig.savefig(FIGURES/(name+".png"),dpi=160,bbox_inches="tight")
            pdf.savefig(fig,bbox_inches="tight")
            plt.close(fig)
        fig,ax=plt.subplots(1,2,figsize=(12,5))
        names=[SOURCE_NAMES[s] for s in sources.source]
        colors=[COLOURS[s] for s in sources.source]
        ax[0].barh(names,sources.rows,color=colors); ax[0].set_xlabel("Prepared recordings"); ax[0].set_title("Three complementary tasks")
        ax[1].barh(names,sources.hours,color=colors); ax[1].set_xlabel("Decoded audio hours"); ax[1].set_title("Actual audio coverage")
        save(fig,"01_corpus_coverage")
        fig,ax=plt.subplots(figsize=(11,8))
        ax.barh(entities.type.str.replace("_"," ")[::-1],entities.entities[::-1],color="#dd6b35")
        ax.set_xlabel("Gold entity instances (source annotations)"); ax.set_title("Exact-value benchmark: 26 entity types")
        save(fig,"02_entity_coverage")
        fig,axes=plt.subplots(1,3,figsize=(13,4))
        for ax,(source,g) in zip(axes,frame.groupby("source")):
            ax.hist(g.duration_s,bins=30,color=COLOURS[source],alpha=.9)
            ax.set_title(SOURCE_NAMES[source]); ax.set_xlabel("Recording length (seconds)"); ax.set_ylabel("Recordings")
            ax.axvline(g.duration_s.median(),ls="--",color="#172033",label=f"Median {g.duration_s.median():.1f}s"); ax.legend()
        save(fig,"03_duration_distributions")
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        internal=splits[splits.split.isin(["train","validation","test"])].set_index("split").reindex(["train","validation","test"])
        axes[0].bar(internal.index,internal.rows,color=["#5062a3","#39858e","#dd6b35"])
        for i,r in enumerate(internal.itertuples()): axes[0].text(i,r.rows,f"{r.rows}\n{r.pct_of_hindi_development_pool:.1f}%",ha="center",va="bottom")
        axes[0].set_ylim(0,internal.rows.max()*1.2); axes[0].set_title("Hindi: grouped project split"); axes[0].set_ylabel("Recordings")
        style_table=indic.groupby(["split","speech_style"]).size().unstack(fill_value=0).reindex(["train","validation","test"])
        style_table.plot.bar(stacked=True,ax=axes[1],color=["#39858e","#b2b8d1"],rot=0)
        axes[1].set_title("Read and extempore coverage"); axes[1].set_ylabel("Recordings")
        save(fig,"04_split_balance")
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        for ax,lang in zip(axes,["en","hi"]):
            for label,color in [("hold","#dd6b35"),("eot","#39858e")]:
                values=np.sort(pause_frame[(pause_frame.language==lang)&(pause_frame.label==label)].duration_s.to_numpy())
                ax.step(values,np.arange(1,len(values)+1)/len(values),label=f"{label} (n={len(values)})",color=color)
            ax.set_title("English" if lang=="en" else "Hindi"); ax.set_xlabel("Silence span length (seconds)"); ax.set_ylabel("Empirical cumulative fraction"); ax.legend()
        fig.suptitle("Silence length alone does not label a turn ending",fontweight="bold")
        save(fig,"05_pause_distributions")
        fig,ax=plt.subplots(figsize=(12,7))
        domains=indic.groupby("domain").size().sort_values()
        ax.barh(domains.index,domains.values,color="#5062a3"); ax.set_title("Hindi speech across 23 professional domains"); ax.set_xlabel("Recordings")
        save(fig,"06_hindi_domain_coverage")
        fig,ax=plt.subplots(1,2,figsize=(12,5))
        for source,g in frame.groupby("source"):
            ax[0].hist(g.rms_dbfs,bins=30,alpha=.5,label=SOURCE_NAMES[source],color=COLOURS[source])
        ax[0].set_title("Measured level, before normalisation"); ax[0].set_xlabel("RMS dBFS"); ax[0].legend(fontsize=8)
        bars=frame.assign(flag=frame.clipped_fraction>.001).groupby("source").flag.sum()
        ax[1].bar([SOURCE_NAMES[s] for s in bars.index],bars.values,color=[COLOURS[s] for s in bars.index]); ax[1].tick_params(axis="x",labelsize=8)
        ax[1].set_title("Recordings flagged for >0.1% near-full-scale samples"); ax[1].set_ylabel("Recordings (retained)")
        save(fig,"07_audio_quality")
    manifest_files={p.name:{"rows":sum(1 for _ in p.open()),"bytes":p.stat().st_size} for p in (ROOT/"data/manifests").glob("*.jsonl")}
    summary={"total_rows":len(rows),"total_hours":float(frame.duration_s.sum()/3600),
        "entity_instances":sum(entity_counts.values()),"entity_types":len(entity_counts),
        "hindi_source_code_mixing_true":int((indic.code_mixing==True).sum()),
        "hindi_extempore":int((indic.speech_style=="Extempore").sum()),
        "pause_instances":len(pauses),"hold_instances":sum(x["label"]=="hold" for x in pauses),
        "eot_instances":sum(x["label"]=="eot" for x in pauses),
        "resampled_rows":int((frame.original_sample_rate!=16000).sum()),
        "active_channel_selected_rows":int((frame.original_channels>1).sum()),
        "text_normalised_rows":int(frame.text_changed_by_nfc_whitespace.sum()),
        "source_code_mixing_label_not_independent_language_audit":True,
        "manifest_files":manifest_files}
    (REPORTS/"eda_summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
