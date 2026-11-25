---
annotations_creators:
  - expert-generated
language_creators:
  - expert-generated
language:
  - en
license: other
license_name: voicecodebench-license
license_link: LICENSE
multilinguality:
  - monolingual
pretty_name: VoiceCodeBench
size_categories:
  - n<1K
source_datasets: []
task_categories:
  - automatic-speech-recognition
tags:
  - audio
  - speech
  - speech-recognition
  - speech-to-text
  - automatic-speech-recognition
  - asr
  - asr-benchmark
  - benchmark
  - evaluation
  - structured-token-recovery
  - entity-recovery
  - workplace-speech
  - english
dataset_info:
  - config_name: default
    features:
      - name: file_name
        dtype: string
      - name: audio_id
        dtype: string
      - name: language
        dtype: string
      - name: duration
        dtype: float64
      - name: domain
        dtype: string
      - name: scenario
        dtype: string
      - name: difficulty
        dtype: string
      - name: speaker
        struct:
          - name: id
            dtype: string
          - name: sex
            dtype: string
          - name: accent
            dtype: string
          - name: age_bucket
            dtype: string
      - name: audio_quality
        struct:
          - name: snr_db
            dtype: float64
          - name: noise_rms_dbfs
            dtype: float64
          - name: speech_rms_dbfs
            dtype: float64
          - name: loudness_lufs
            dtype: float64
          - name: click_pop_count_per_min
            dtype: float64
      - name: transcripts
        struct:
          - name: template
            dtype: string
          - name: acoustic
            dtype: string
          - name: canonical
            dtype: string
      - name: entities
        list:
          - name: id
            dtype: string
          - name: type
            dtype: string
          - name: role
            dtype: string
          - name: acoustic
            dtype: string
          - name: canonical
            dtype: string
      - name: entity_types
        list: string
      - name: entity_count
        dtype: int64
    splits:
      - name: test
        num_bytes: 911121
        num_examples: 300
    download_size: 1068651
    dataset_size: 911121
configs:
  - config_name: default
    default: true
    data_files:
      - split: test
        path: data/metadata.jsonl
---

# VoiceCodeBench

VoiceCodeBench is a test-only benchmark for evaluating whether automatic
speech recognition (ASR) systems preserve exact structured values in English
workplace speech.

Paper: [VoiceCodeBench: Evaluating Exact Structured-Token Recovery in Automatic Speech Recognition](https://arxiv.org/abs/2608.28916)

The benchmark targets cases where a transcript is software input: callback
numbers, email addresses, command-line flags, file paths, URLs, account
identifiers, dates, measurements, and similar values that downstream systems may
parse, route, store, compare, or execute.

## Contents

- 300 human-recorded English WAV segments, totaling 5.587 hours.
- 85 anonymized speaker IDs.
- 1,482 audited target entities across 26 structured entity types.
- 8 workplace workflow domains.
- 23 tracked baseline ASR system outputs.

Released files:

- `data/audio/*.wav`: benchmark audio files.
- `data/metadata.jsonl`: transcripts, entity annotations, speaker metadata, and
  audio-quality metadata.
- `baselines/predictions/*.json`: baseline transcripts plus entity-match
  decisions.
- `baselines/paper_predictions/*.json`: archived AssemblyAI paper predictions
  referenced by the frozen verifier audit.
- `baselines/results.csv`: aggregate baseline table.
- `baselines/paper_results.csv`: frozen results reported in the arXiv paper.
- `scripts/`: transcription, entity verification, scoring, and figure commands.
- `DATASET_CARD.md`: datasheet-style documentation for motivation, composition,
  collection, consent, intended use, limits, maintenance, and licensing.

## Task

Each item contains an audio recording, three transcript layers, and target
entities:

- `template`: script text with entity placeholders.
- `acoustic`: what the speaker is expected to say aloud.
- `canonical`: the written value a downstream application needs.

For example, "double dash dry dash run" maps to `--dry-run`, and "all caps
database underscore URL" maps to `DATABASE_URL`.

ASR systems are evaluated under a raw-audio-only protocol. The system receives
only the audio file; benchmark-specific prompts, target entity lists, domain
labels, custom vocabulary, grammar constraints, candidate values, and post-ASR
correction are excluded from the main setting.

## Metrics

VoiceCodeBench reports format-invariant WER as a broad transcript-quality
diagnostic. For every target entity span, the scorer accepts either the
documented acoustic rendering or canonical rendering as the reference. A system
that writes `212-555-0100` is therefore not penalized relative to one that
writes `two one two five five five zero one zero zero`. Non-entity words use
ordinary word-level edit distance. The main entity-sensitive metrics are:

```text
CTEM = correct target entities / target entities
TSR  = recordings with all target entities correct / recordings
```

Canonical Token/Entity Match (CTEM) measures value-level recovery. Task Success
Rate (TSR) measures whether every target entity in a recording was recovered.

## Baselines

The tracked baseline suite contains 23 ASR systems across batch and streaming
modes. Current aggregate ranges:

- WER: 3.8% to 57.3%.
- CTEM: 33.9% to 91.8%.
- TSR: 6.3% to 68.7%.

The strongest baselines by TSR are `deepgram_nova3` and
`openai_gpt_live_transcribe_streaming`, tied at 68.7%. The strongest baseline
by CTEM is `openai_gpt_live_transcribe_streaming` at 91.8%.
`assemblyai_universal_3_5_pro` scores 3.8% WER, 86.5% CTEM, and 51.7% TSR in batch mode.
`assemblyai_universal_3_6_pro_streaming` scores 5.1% WER, 76.9% CTEM, and 27.7% TSR in streaming mode.
`openai_gpt_transcribe` scores 6.1% WER, 89.3% CTEM, and 61.0% TSR in batch mode.
`openai_gpt_live_transcribe_streaming` scores 5.9% WER, 91.8% CTEM, and 68.7% TSR in streaming mode.
`cartesia_ink_2_streaming` scores 9.3% WER, 90.1% CTEM, and 63.7% TSR in streaming mode.
`modal_inkling` scores 4.9% WER, 84.3% CTEM, and 49.7% TSR in batch mode.
`modal_nvidia_parakeet_tdt_0_6b_v3` scores 9.3% WER, 78.6% CTEM, and 37.3% TSR in batch mode.
`inworld_stt_1` scores 9.7% WER, 83.7% CTEM, and 44.0% TSR in batch mode.
`inworld_stt_1_streaming` scores 57.3% WER, 33.9% CTEM, and 6.3% TSR in streaming mode.
`meta_muse_voice_transcribe_1_0` scores 7.5% WER, 87.6% CTEM, and 55.3% TSR in batch mode.
`meta_muse_voice_transcribe_1_0_streaming` scores 7.4% WER, 86.8% CTEM, and 55.7% TSR in streaming mode.
`xai_grok_voice_transcribe_2_0` scores 7.7% WER, 86.1% CTEM, and 55.7% TSR in batch mode.
`xai_grok_voice_transcribe_2_0_streaming` scores 8.7% WER, 85.8% CTEM, and 56.0% TSR in streaming mode.
`mistral_voxtral_mini_transcribe_2` scores 5.5% WER, 86.9% CTEM, and 52.3% TSR in batch mode.
`mistral_voxtral_mini_transcribe_realtime_streaming` scores 6.6% WER, 83.7% CTEM, and 48.0% TSR in streaming mode.

## Install

For scoring released baseline artifacts:

```bash
python -m pip install -e .
```

Optional extras are available for heavier workflows:

```bash
python -m pip install -e ".[providers]"  # run new ASR baselines
python -m pip install -e ".[figures]"    # regenerate benchmark figures
python -m pip install -e ".[dev]"        # provider and figure dependencies
```

External tools are only needed for optional workflows:

- `ffmpeg` for live provider audio conversion, including streaming PCM and
  Inkling's 16 kHz WAV input.
- `gcloud` for Google Cloud transcription when application-default credentials
  are not already configured.

## Tests

```bash
python -m pytest
```

## Reproduce

```bash
./scripts/reproduce_release.sh
```

This creates `.venv` if needed, installs the package in editable mode with the
`figures` extra, validates metadata, scores the released baseline
transcripts/entity matches, rewrites `baselines/results.csv`, and regenerates
`baselines/figures/wer_entity_scatter.pdf` from the current results. It also
regenerates `baselines/figures/wer_entity_scatter_paper.pdf` from the frozen
12-model snapshot in `baselines/paper_results.csv`. Post-publication baselines
and later model replacements are excluded from the paper figure.

To generate the current benchmark figure with every row in
`baselines/results.csv`, run:

```bash
vcb-make-figures --model-set all
```

This writes `baselines/figures/wer_entity_scatter.pdf` by default. Use
`--model-set paper` to regenerate only the frozen paper figure, or `--output` to
choose another path.

## Experimental New Baselines

The released scoring and reproduction commands are the stable script surface.
Live provider runs are included to make the tracked baselines auditable, but
provider APIs and websocket protocols change over time.

Running new ASR baselines requires provider credentials. Copy
`scripts/.secret.example` to a private secret file or set equivalent environment
variables, including the Modal endpoint settings described below, then run:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[providers]"

vcb-run \
  --stt-mode all \
  --output-dir runs/full-local
```

### Mistral Voxtral transcription

[Mistral's batch transcription](https://docs.mistral.ai/studio/audio/speech_to_text/offline_transcription)
is registered as `mistral_voxtral_mini_transcribe_2`, pinned to
`voxtral-mini-2602` (Voxtral Mini Transcribe 2).
[Realtime transcription](https://docs.mistral.ai/studio/audio/speech_to_text/realtime_transcription)
is registered as `mistral_voxtral_mini_transcribe_realtime_streaming`, pinned to
`voxtral-mini-transcribe-realtime-2602`. Set `MISTRAL_API_KEY` in the environment
or your private secret file. The batch model is included in the default batch
selection; `--stt-mode all` includes both models.

Batch requests upload the original WAV file to `/v1/audio/transcriptions`,
with `language=en` and diarization disabled. Streaming uses the realtime
WebSocket endpoint and 16 kHz mono PCM16 audio in real-time-paced 100 ms chunks,
with `target_streaming_delay_ms=480`. It waits for `session.created`, sets the
audio format and delay, sends base64 audio chunks, then flushes and ends the
input. Only the full transcript in `transcription.done` is saved; provisional
text and segment events are ignored. Neither model receives context bias,
benchmark prompts, entity hints, or custom vocabulary. Model versions and
inference settings are recorded in run metadata. Internal realtime server
errors restart the entire recording in a fresh session, with at most five
attempts; failed-session text is discarded.

Smoke-test both models on one recording:

```bash
vcb-transcribe \
  --stt-model-ids mistral_voxtral_mini_transcribe_2,mistral_voxtral_mini_transcribe_realtime_streaming \
  --limit 1 \
  --model-concurrency 1 \
  --output-dir runs/mistral-smoke
```

Run the full benchmark (also requires `OPENAI_API_KEY` for entity verification):

```bash
vcb-run \
  --stt-model-ids mistral_voxtral_mini_transcribe_2,mistral_voxtral_mini_transcribe_realtime_streaming \
  --model-concurrency 2 \
  --datapoint-concurrency 1 \
  --entity-concurrency 8 \
  --evaluation-date 2026-10-09 \
  --output-dir runs/mistral-full \
  --resume
```

Both Mistral models were evaluated on all 300 recordings on 2026-10-09 using
`openai_gpt_5_5_v1`, the same entity verifier as the current suite. Transcripts
and all 1,482 entity decisions per model are released in
`baselines/predictions/mistral_voxtral_mini_transcribe_2.json` and
`baselines/predictions/mistral_voxtral_mini_transcribe_realtime_streaming.json`.
Streaming requests were resumed with up to 24 concurrent recordings and
request starts paced one second apart.
Aggregate and per-entity-type scores are in `baselines/results.csv` and the
current `--model-set all` figure.

### xAI Grok Voice Transcribe 2.0

[Grok Voice Transcribe 2.0](https://docs.x.ai/developers/model-capabilities/audio/speech-to-text)
is registered as `xai_grok_voice_transcribe_2_0` (batch) and
`xai_grok_voice_transcribe_2_0_streaming` (streaming). Set `XAI_API_KEY` in the
environment or your private secret file. The batch model is included in the
default batch selection; `--stt-mode all` includes both modes.

Batch requests upload the original audio to `https://api.x.ai/v1/stt` as
multipart form data, with all options before the `file` field. Streaming uses
`wss://api.x.ai/v1/stt`, waits for `transcript.created`, sends 16 kHz mono PCM16
in real-time-paced 100 ms chunks, and ends with `audio.done`. The adapter waits
for `transcript.done` before saving a result. It uses that event's transcript
when non-empty; when xAI sends empty completion text after finalizing
utterances, it joins the completed utterances instead. Interim results and
locked chunks are ignored to avoid duplicating text.

Both modes pin `model=grok-voice-transcribe-2.0`, `language=en`, and `format=true`
to enable xAI's inverse text normalization. Filler words, diarization, and
multichannel transcription are disabled. No key terms, entity hints, or custom
vocabulary are supplied. VAD thresholds use the documented defaults: `0.5`
for batch and `0.08` for streaming. Streaming pins `endpointing=400` and
`interim_results=false`. Run metadata records these settings and the mutable
hosted model revision.

Smoke-test both modes on one recording:

```bash
vcb-transcribe \
  --stt-model-ids xai_grok_voice_transcribe_2_0,xai_grok_voice_transcribe_2_0_streaming \
  --limit 1 \
  --model-concurrency 1 \
  --output-dir runs/grok-smoke
```

Run the full benchmark (also requires verifier credentials such as `OPENAI_API_KEY`):

```bash
vcb-run \
  --stt-model-ids xai_grok_voice_transcribe_2_0,xai_grok_voice_transcribe_2_0_streaming \
  --model-concurrency 1 \
  --datapoint-concurrency 1 \
  --output-dir runs/grok-full \
  --resume
```

Both Grok modes were evaluated on all 300 recordings on 2026-10-08 using the
same `openai_gpt_5_5_v1` entity verifier as the current suite. The released
transcripts and entity decisions are tracked in
`baselines/predictions/xai_grok_voice_transcribe_2_0.json` and
`baselines/predictions/xai_grok_voice_transcribe_2_0_streaming.json`. Aggregate
scores are in `baselines/results.csv` and the current `--model-set all` figure.

### AssemblyAI Universal Pro

The current AssemblyAI registrations are:

- `assemblyai_universal_3_5_pro`: batch, with `speech_models=["universal-3-5-pro"]`.
- `assemblyai_universal_3_6_pro_streaming`: realtime, with `speech_model=universal-3-6-pro`.

As of September 29, 2026, [Universal-3.6 Pro is released for realtime](https://www.assemblyai.com/blog/universal-3-6-pro-realtime),
while the [latest documented batch model is Universal-3.5 Pro](https://www.assemblyai.com/docs/getting-started/models).
Configure `ASSEMBLYAI_API_KEY` in the environment or private `scripts/.secret` file.
The streaming adapter sends 16 kHz PCM16 audio at realtime pace through the
existing v3 WebSocket API.

```bash
vcb-run \
  --stt-model-ids assemblyai_universal_3_5_pro,assemblyai_universal_3_6_pro_streaming \
  --resume \
  --datapoint-concurrency 4 \
  --output-dir runs/assemblyai-universal-upgrade
```

Both current AssemblyAI baselines were evaluated on all 300 recordings on
September 29, 2026, with the `openai_gpt_5_5_v1` entity verifier. Their
transcripts and entity decisions are in `baselines/predictions/`, and their
scores are in `baselines/results.csv`. The original Universal-3 Pro outputs
remain in `baselines/paper_predictions/` for the frozen paper snapshot and
verifier audit.

### OpenAI GPT-Transcribe

OpenAI's current [file transcription](https://developers.openai.com/api/docs/guides/speech-to-text)
and [realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription)
models are registered as
`openai_gpt_transcribe` for completed-file batch transcription and
`openai_gpt_live_transcribe_streaming` for continuously streamed realtime
transcription. Configure `OPENAI_API_KEY` in the environment or private
`scripts/.secret` file.

The batch adapter sends the original WAV to
`https://api.openai.com/v1/audio/transcriptions` with model `gpt-transcribe`
and the English language hint `languages[]=en`. The streaming adapter converts
audio to headerless 24 kHz mono PCM16, sends realtime-paced 100 ms Base64
chunks to the Realtime transcription WebSocket, explicitly commits the audio
turn, and stores the final transcript from the completed event. It uses model
`gpt-live-transcribe`, `languages=["en"]`, manual turn detection, and the
documented `low` delay setting.

Smoke-test one recording in both modes:

```bash
vcb-transcribe \
  --stt-model-ids openai_gpt_transcribe,openai_gpt_live_transcribe_streaming \
  --model-concurrency 2 \
  --limit 1 \
  --output-dir runs/openai-transcribe-smoke \
  --evaluation-date 2026-09-01
```

Run the full resumable benchmark with:

```bash
vcb-run \
  --stt-model-ids openai_gpt_transcribe,openai_gpt_live_transcribe_streaming \
  --resume \
  --model-concurrency 2 \
  --entity-concurrency 4 \
  --output-dir runs/openai-transcribe-full \
  --evaluation-date 2026-09-01
```

The released current-suite artifacts and aggregate scores are tracked in
`baselines/predictions/openai_gpt_transcribe.json`,
`baselines/predictions/openai_gpt_live_transcribe_streaming.json`, and
`baselines/results.csv`. The original paper's OpenAI rows remain only in the
frozen result snapshot, audit sample, and `baselines/paper_results.csv`.

### Cartesia Ink 2

Cartesia's current [Ink 2](https://docs.cartesia.ai/build-with-cartesia/stt/latest)
model is registered as `cartesia_ink_2_streaming`. Ink 2 is streaming-only;
Cartesia's batch `/stt` endpoint supports the older `ink-whisper` family rather
than `ink-2`. Configure `CARTESIA_API_KEY` in the environment or private
`scripts/.secret` file.

The adapter converts each recording to headerless 16 kHz mono PCM16, sends
realtime-paced 100 ms binary chunks to Cartesia's manual-finalize WebSocket,
sends `finalize` and `close`, and concatenates final transcript deltas verbatim.
It pins API version `2026-08-14`, sets the English language hint, and does not
send keyterms, custom vocabulary, or benchmark context.

Smoke-test one recording with:

```bash
vcb-transcribe \
  --stt-model-ids cartesia_ink_2_streaming \
  --limit 1 \
  --output-dir runs/cartesia-ink-2-smoke \
  --evaluation-date 2026-09-01
```

Run the full resumable benchmark with six parallel realtime streams:

```bash
vcb-run \
  --stt-model-ids cartesia_ink_2_streaming \
  --resume \
  --datapoint-concurrency 6 \
  --entity-concurrency 4 \
  --output-dir runs/cartesia-ink-2-full \
  --evaluation-date 2026-09-01
```

The released artifact and aggregate score are tracked in
`baselines/predictions/cartesia_ink_2_streaming.json` and
`baselines/results.csv`.

### Meta Muse Voice Transcribe

Meta Muse Voice Transcribe 1.0 is registered through the Meta Model API as
`meta_muse_voice_transcribe_1_0` for one-shot batch transcription and
`meta_muse_voice_transcribe_1_0_streaming` for realtime WebSocket streaming.
Configure the API credential as `MODEL_API_KEY` in the environment or private
`scripts/.secret` file.

Both modes use neutral `PUSH_TO_TALK` transcription with no keyword or language
bias. The batch adapter uploads a converted 16 kHz mono PCM WAV to
`https://api.meta.ai/v1/asr/transcribe`. The streaming adapter sends headerless
16 kHz mono PCM in engine-aligned 80 ms binary frames to
`wss://api.meta.ai/v1/asr/realtime`, paces the recording against an absolute
realtime schedule, and stores only the final verbatim transcript. The hosted
model is mutable and Meta does not expose a checkpoint revision.

Smoke-test one recording in both modes:

```bash
vcb-transcribe \
  --stt-model-ids meta_muse_voice_transcribe_1_0,meta_muse_voice_transcribe_1_0_streaming \
  --model-concurrency 1 \
  --limit 1 \
  --output-dir runs/meta-muse-smoke \
  --evaluation-date 2026-09-01
```

Run the full resumable benchmark with:

```bash
vcb-run \
  --stt-model-ids meta_muse_voice_transcribe_1_0,meta_muse_voice_transcribe_1_0_streaming \
  --resume \
  --model-concurrency 1 \
  --entity-concurrency 4 \
  --output-dir runs/meta-muse-full \
  --evaluation-date 2026-09-01
```

The streaming run is realtime-paced and therefore takes at least the duration
of the benchmark audio. Meta's one-shot endpoint accepts at most 10 minutes or
32 MB per recording; every VoiceCodeBench recording is within those limits.

The released baseline artifacts and aggregate scores are tracked in
`baselines/predictions/meta_muse_voice_transcribe_1_0.json`,
`baselines/predictions/meta_muse_voice_transcribe_1_0_streaming.json`, and
`baselines/results.csv`.

### Inworld STT 1

Inworld STT 1 is registered as two model IDs through Inworld's native STT API:
`inworld_stt_1` for synchronous batch transcription and
`inworld_stt_1_streaming` for realtime bidirectional WebSocket streaming. Both
use `inworld/inworld-stt-1` with 16 kHz mono LINEAR16 English input
(`en-US`). Configure a private Inworld API key as `INWORLD_API_KEY`; the adapter
sends it as `Authorization: Basic {INWORLD_API_KEY}` exactly as configured.
Never commit `scripts/.secret`; it is ignored by Git.

The batch adapter sends one complete 16 kHz mono PCM WAV, including its RIFF
header, as Base64 `audioData.content`. The streaming adapter sends headerless
little-endian PCM16 in 100 ms chunks, paces chunks in realtime, sends manual
`endTurn`, waits for a final non-empty transcript, then sends `closeStream`.
Both modes disable Voice Profile, transcription hints, custom vocabulary, domain
hints, VAD or automatic turn detection, canonicalization, and post-ASR
correction. Artifacts store only verbatim final transcripts, plus returned
`usage.modelId` row metadata when the API supplies it.

Smoke-test one recording in each mode after configuring real credentials:

```bash
vcb-transcribe \
  --stt-model-ids inworld_stt_1 \
  --limit 1 \
  --output-dir runs/inworld-batch-smoke \
  --evaluation-date 2026-07-28

vcb-transcribe \
  --stt-model-ids inworld_stt_1_streaming \
  --limit 1 \
  --output-dir runs/inworld-streaming-smoke \
  --evaluation-date 2026-07-28
```

Run the full publishable benchmark with resume and conservative model
concurrency:

```bash
vcb-run \
  --stt-model-ids inworld_stt_1,inworld_stt_1_streaming \
  --resume \
  --model-concurrency 1 \
  --entity-concurrency 4 \
  --output-dir runs/inworld-full \
  --evaluation-date 2026-07-28
```

If a run stops partway through, rerun the same command with `--resume`; completed
rows are reused and pending rows continue. Streaming is realtime-paced, so the
streaming half should take at least the 5.6-hour dataset duration before API and
verification overhead.

Pricing and limits verified on 2026-07-28: STT 1 is $0.15/hr on On-Demand;
$0.10/hr on Creator, Builder, Developer, and Growth; Enterprise pricing is
custom. On-Demand includes up to 400 minutes of STT. Streaming concurrency
limits are On-Demand 10, Creator 20, Builder 100, Developer 300, Growth 1,000,
and Enterprise custom.

To release the baselines after both 300-recording runs complete, copy
`runs/inworld-full/inworld_stt_1/entity_matches.json` to
`baselines/predictions/inworld_stt_1.json` and
`runs/inworld-full/inworld_stt_1_streaming/entity_matches.json` to
`baselines/predictions/inworld_stt_1_streaming.json`, then recompute scores and
the current all-model figure:

```bash
vcb-score-entities \
  --dataset-root . \
  --metadata data/metadata.jsonl \
  --entity-matches-dir baselines/predictions \
  --output-dir baselines \
  --scores-dir baselines/scores/entities \
  --output-csv baselines/results.csv

vcb-score-wer \
  --dataset-root . \
  --metadata data/metadata.jsonl \
  --transcripts-dir baselines/predictions \
  --output-dir baselines \
  --scores-dir baselines/scores/wer \
  --output-csv baselines/results.csv

vcb-make-figures --model-set all
```

Run `./scripts/reproduce_release.sh` to recompute the current results and both
figures from their respective prediction artifacts and snapshots.

### Modal Inkling

Thinking Machines Lab Inkling is available as the batch model ID
`modal_inkling`. Modal exposes `thinkingmachines/Inkling-NVFP4` through a shared,
OpenAI-compatible managed endpoint with token-based pricing; no dedicated model
deployment is required. Open the [Inkling endpoint page](https://modal.com/endpoints?model=thinkingmachines%2FInkling-NVFP4&type=managed),
create a Modal account if needed, create the managed endpoint, and copy its URL.
Create a proxy token and configure the private `scripts/.secret` file with the
endpoint URL, token ID, and token secret:

```dotenv
MODAL_INKLING_ENDPOINT=https://<your-endpoint-host>
MODAL_PROXY_TOKEN_ID=wk-...
MODAL_PROXY_TOKEN_SECRET=ws-...
```

The adapter accepts the base endpoint URL, `/v1` URL, or full
`/v1/chat/completions` URL shown by Modal. Check the endpoint page for current
pricing and rate limits before a full benchmark run. Never commit
`scripts/.secret`; it is ignored by Git.

To smoke-test one recording after configuring real credentials:

```bash
vcb-transcribe \
  --stt-model-ids modal_inkling \
  --limit 1 \
  --output-dir runs/inkling-smoke
```

To run the full transcription, entity-verification, and scoring pipeline, also
configure `OPENAI_API_KEY` for the entity verifier and run:

```bash
vcb-run \
  --stt-model-ids modal_inkling \
  --output-dir runs/inkling-full
```

The adapter converts source recordings to the model's documented 16 kHz mono
WAV input, sends the audio through Modal's chat-completions `audio_url` format,
uses Thinking Machines' documented transcription prompt and text-before-audio
message order, and sets reasoning effort to `max` (`0.99`). The transcript
response is stored verbatim without benchmark-specific hints or post-ASR
correction.

Thinking Machines' limited-time free Inkling Playground is useful for manually
spot-checking audio, but it is a chat interface rather than the reproducible
batch API used by this benchmark.

### Modal NVIDIA Parakeet TDT 0.6B v3

NVIDIA Parakeet TDT 0.6B v3 is available as the batch model ID
`modal_nvidia_parakeet_tdt_0_6b_v3` through an existing Modal HTTPS endpoint.
Configure these private secrets:

```dotenv
MODAL_PARAKEET_ENDPOINT=https://<your-parakeet-web-function>.modal.run
MODAL_PROXY_TOKEN_ID=wk-...
MODAL_PROXY_TOKEN_SECRET=ws-...
```

The full run command is:

```bash
vcb-run \
  --stt-model-ids modal_nvidia_parakeet_tdt_0_6b_v3 \
  --resume \
  --output-dir runs/parakeet-full
```

The adapter sends each source recording as one complete 16 kHz mono WAV and
stores the returned transcript verbatim.

For publishable results, report provider, model name, API endpoint or endpoint
family, evaluation date, mode, inference settings, and any prompting, custom
vocabulary, post-processing, fine-tuning, or canonicalization.

## Use And Limits

VoiceCodeBench is intended for diagnostic ASR evaluation, provider comparison,
regression tracking, and per-entity risk analysis. It is not intended as a
training corpus, hidden leaderboard, universal ASR-quality measure, speaker
identification resource, biometric dataset, or demographic profiling dataset.

See `DATASET_CARD.md` for the full dataset statement.

## Citation

```bibtex
@misc{baumgartner2026voicecodebench,
  title = {VoiceCodeBench: Evaluating Exact Structured-Token Recovery in Automatic Speech Recognition},
  author = {Baumgartner, Tyler and Tai, Brandon and Kaelin-Martin, Lisa and Fan, Candice and Debaupte, Luc and Wang, Bill and Zhong, Yi},
  year = {2026},
  eprint = {2608.28916},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL},
  url = {https://arxiv.org/abs/2608.28916}
}
```

## License

The repository's non-audio materials are released under the MIT License. The
benchmark audio is subject to an additional restriction prohibiting its use for
voice cloning. See `LICENSE` for the complete terms.
