---
license: cc-by-4.0
task_categories:
- automatic-speech-recognition
language:
- bn
- gu
- hi
- ml
- mr
- or
- te
- ur
tags:
- contextual-asr
- audio-llm
- speech-recognition
- indic
- multilingual
- benchmark
pretty_name: IndicContextEval
size_categories:
- 10K<n<100K
configs:
- config_name: default
  data_files:
  - split: Bengali
    path: data/Bengali-*
  - split: Gujarati
    path: data/Gujarati-*
  - split: Hindi
    path: data/Hindi-*
  - split: Malayalam
    path: data/Malayalam-*
  - split: Marathi
    path: data/Marathi-*
  - split: Odia
    path: data/Odia-*
  - split: Telugu
    path: data/Telugu-*
  - split: Urdu
    path: data/Urdu-*
dataset_info:
  features:
  - name: audio
    dtype: audio
  - name: reference_text_with_tags
    dtype: string
  - name: reference_text_no_tags
    dtype: string
  - name: reference_text_no_brackets
    dtype: string
  - name: language
    dtype: string
  - name: reference_text
    dtype: string
  - name: duration
    dtype: float64
  - name: task_name
    dtype: string
  - name: domain_name
    dtype: string
  - name: domain_description
    dtype: string
  - name: location
    dtype: string
  - name: speech_style
    dtype: string
  - name: code_mixing
    dtype: bool
  - name: audio_chunk_description
    dtype: string
  - name: l0_prompt
    dtype: string
  - name: l1_prompt
    dtype: string
  - name: l2_prompt
    dtype: string
  - name: l3_prompt
    dtype: string
  - name: l4_prompt
    dtype: string
  - name: l5_prompt
    dtype: string
  - name: l6_prompt
    dtype: string
  - name: audio_path
    dtype: string
  - name: speaker_id
    dtype: string
  - name: gender
    dtype: string
  - name: age
    dtype: string
  - name: file_name
    dtype: string

  splits:
  - name: Bengali
    num_bytes: 453299204
    num_examples: 1167
  - name: Gujarati
    num_bytes: 513084894
    num_examples: 1433
  - name: Hindi
    num_bytes: 1265929184
    num_examples: 3110
  - name: Malayalam
    num_bytes: 463355467
    num_examples: 1207
  - name: Marathi
    num_bytes: 1523363127
    num_examples: 3114
  - name: Odia
    num_bytes: 670758527
    num_examples: 1836
  - name: Telugu
    num_bytes: 1505064735
    num_examples: 4088
  - name: Urdu
    num_bytes: 393617253
    num_examples: 929
  download_size: 6481489663
  dataset_size: 6788472391
---

# IndicContextEval

**A Benchmark for Evaluating Context Utilisation in Audio Large Language Models Across 8 Indic Languages**

Code and resources: **https://github.com/AI4Bharat/IndicContextEval**

## Dataset at a glance

| | |
|---|---|
| Languages | Hindi, Bengali, Telugu, Marathi, Gujarati, Malayalam, Odia, Urdu |
| Speakers | 555 |
| Duration | 55.93 h |
| Utterances | 16,884 |
| Domains | 23 professional domains |
| Speech styles | Read, Extempore |
| Prompt levels | L0–L6 (7 levels) |

### Per-language statistics

| Language | Utterances | Hours | Speakers | Read | Extempore |
|---|---:|---:|---:|---:|---:|
| Bengali   | 1,167 | 3.81  | 30  | 770  | 397  |
| Gujarati  | 1,433 | 4.21  | 61  | 433  | 1,000|
| Hindi     | 3,110 | 9.08  | 124 | 1,237| 1,873|
| Malayalam | 1,207 | 4.03  | 15  | 826  | 381  |
| Marathi   | 3,114 | 11.67 | 74  | 2,075| 1,039|
| Odia      | 1,836 | 6.07  | 19  | 1,412| 424  |
| Telugu    | 4,088 | 13.70 | 205 | 1,425| 2,663|
| Urdu      | 929   | 3.37  | 27  | 833  | 96   |
| **Total** | **16,884** | **55.93** | **555** | | |

### Domains (23)

Academic Research & Publishing · Animal Sciences · Architecture & Urban Planning · Arts ·
Audio & Media Technology · Business · Core Engineering · Culinary Arts & Food Science ·
Data Science · Defense & Armed Forces · Film & Media Production · Forensics & Legal Sciences ·
Fundamental Sciences · Gaming & Media · Humanities · Linguistics · Materials Science ·
Medical Sciences · Robotics & Automation Engineering · Skilled Trades · Social Sciences ·
Supply Chain & Logistics · Textiles & Fashion

## Prompt taxonomy (L0–L6)

Each level adds exactly one contextual signal; everything else is held constant. Output is always
required in the native script of the target language.

| Level | Context added |
|---|---|
| **L0** | None — bare transcription instruction, no language hint |
| **L1** | Target language specified (baseline) |
| **L2** | + structured domain metadata (style, region, one-line domain description) |
| **L3** | + natural-language audio description |
| **L4** | + domain entity list in **English** script |
| **L5** | + the same domain entity list in **native** script |
| **L6** | + an entity list from an **unrelated** domain (adversarial control) |

## Loading

Each language is a split (with playable, embedded audio):

```python
from datasets import load_dataset

ds = load_dataset("SakshiJ/IndicContextEval", split="Hindi")   # Bengali, Telugu, ...
print(ds[0]["audio"], ds[0]["l5_prompt"])                       # audio decoded automatically
```

## License

Released under **CC-BY-4.0**. You may share and adapt the material for any purpose, including
commercially, provided you give appropriate credit.

## Citation

```bibtex
@misc{joshi2026indiccontextevalbenchmarkevaluatingcontext,
      title={IndicContextEval: A Benchmark for Evaluating Context Utilisation in Audio Large Language Models Across 8 Indic Languages},
      author={Sakshi Joshi and Dhruv Subhash Rathi and Sanskar Singh and Eldho Ittan George and R J Hari and Kaushal Bhogale and Mitesh M. Khapra},
      year={2026},
      eprint={2606.19157},
      archivePrefix={arXiv},
      primaryClass={eess.AS},
      url={https://arxiv.org/abs/2606.19157},
}
```
