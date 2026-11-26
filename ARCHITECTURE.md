# Architecture

One Python package (`pipeline/`), one entry point (`pipeline/run.py: film()`), one contract (`storyboard.json`). `make film` → `python -m pipeline film`.

## Data flow

```
storyboard.json ──validate (schema/ + consistency)──▶ Storyboard
      │
      ├─ script ──────── Gemini text ──▶ Amharic drafts written back into storyboard.json (unreviewed)
      │                                   └─ review gate: `make film` refuses unreviewed lines
      ├─ narration ───── Gemini TTS ───▶ outputs/narration/<line>-<voice>-<hash>.wav
      │                                   └─ timing check: measured lengths, no overlaps, nothing past the last shot
      ├─ characters ──── FLUX.2 klein ─▶ outputs/characters/<name>-<hash>.jpg
      ├─ keyframes ───── FLUX.2 klein ─▶ outputs/keyframes/shot-NN-<hash>.jpg   (one reference image per shot)
      ├─ pans ────────── FFmpeg ───────▶ outputs/shots/shot-NN-<aspect>-<hash>.mp4  (placeholder if no keyframe)
      ├─ moving ──────── Wan 2.2 TI2V-5B on Kaggle ─▶ outputs/moving/shot-NN-<hash>.mp4 (shots 4, 5, 11)
      │                                   └─ fitted per aspect and length; no clip → the pan shot is kept
      ├─ cards ───────── FFmpeg ───────▶ outputs/cards/{saying,end}-<aspect>-<hash>.mp4
      ├─ music ───────── ACE-Step 1.5 on Kaggle ────▶ outputs/music/candidate-N-<hash>.wav, chosen.wav
      │                                   └─ no candidate → last chosen track → placeholder pad
      └─ assemble ────── FFmpeg ───────▶ outputs/film/film-{16x9,9x16}.mp4 + .en.srt
```

Model-calling stages: script, narration (and the voice trial), characters, keyframes, and the two GPU stages, moving shots and music. Pans, cards and assembly are pure FFmpeg: the same inputs give the same output.

**GPU stages (Kaggle).** Each GPU stage sends every item that missed the cache to one Kaggle job, because loading the model takes minutes. The notebook templates are in `kaggle/` (`wan22_i2v.py`, `acestep_score.py`). `KaggleJobs` embeds the job (items, plus inputs such as the 480p keyframes, as base64) at the top of the template, pushes it with `kaggle kernels push` as a private GPU script kernel with internet on, polls `kaggle kernels status` every minute, and downloads `/kaggle/working`. The notebook saves each item as soon as it finishes and rewrites `results.json` after each one, so a session that dies part-way still returns what it finished. The log gets one line for the job, plus one per item with the GPU seconds measured in the notebook. `make gpu` runs only these two stages.

## The contract: `storyboard.json`

Validated against `schema/storyboard.schema.json` (JSON Schema 2020-12) before any stage runs, then checked for consistency: unique ids, every line anchored to a real shot, total length 60–90 s. Errors name the shot or line and the field (`shots[1] (shot 2).duration_s: …`). Everything a model sees comes from here, so no prompt text lives in the code:

| Section | Holds | Read by |
|---|---|---|
| `title`, `saying`, `end_card` | card text and durations | cards |
| `style` | style words, copper/gold grade words, the character-sheet prompt, `reference_images` | characters, keyframes |
| `characters` | fixed description + seed for the Father, the Son, the coffee corner | characters, keyframes |
| `script` | translation instruction + seed | script |
| `narrator` | voice, `voice_reason`, style instruction, seed, `voice_trial` | narration, voices |
| `music` | caption, duration, candidate count + seed, `chosen` + `reason`, volume points (time → gain) | music, assemble |
| `shots[]` | id, act, duration, `pan`/`moving`, keyframe and motion prompts, seed, grade, characters, `references`, pan path per aspect | keyframes, pans, assemble |
| `narration[]` | id, anchored shot + offset, `en` (= subtitle), `am`, `am_pinned`, `am_reviewed`, `am_from_en` | script, narration, assemble |

The script stage is the only one that writes to the storyboard (Amharic drafts), and the file round-trips byte-for-byte through `json.dumps(indent=2)` so its diffs stay readable.

## Providers

`pipeline/providers.py` defines one small interface per capability: `TextProvider`, `SpeechProvider`, `ImageProvider` and `GpuJobs`. The real adapters live in `pipeline/adapters.py`. They are thin wrappers that use the standard library only:
- `GeminiText` and `GeminiSpeech` call the Gemini API (`generateContent`).
- `CloudflareImage` calls Workers AI with a multipart form.
- `KaggleJobs` drives the Kaggle CLI (`kaggle==2.2.5`): push, poll, download.

`default_providers()` reads the keys from `.env` only. Tests inject fakes that write tiny real media and record their calls.

## Caching

`pipeline/cache.py` hashes exactly the inputs that affect an item:
- **TTS:** model, text, language, voice, style and seed.
- **Image:** model, prompt (which already contains the style, grade and character descriptions), seed, size and reference images.
- **Amharic draft:** prompt and seed.
- **Moving shot:** model, the keyframe's bytes, motion prompt, seed, size, frame count, steps, guidance and flow shift.
- **Score candidate:** model, caption, duration, steps, shift and seed (`music.seed + i`).

The manifest `outputs/cache-manifest.json` maps hash → file. A stage asks the cache first, and a hit is logged too. So an unchanged re-run makes zero model calls, and a one-line edit makes exactly one. That is pinned by seam tests for narration and keyframes.

A few design choices follow from this:
- **Shared voice cache.** The TTS cache key doesn't name the stage, so the voice-trial clip in the chosen voice is reused as that line's narration.
- **Rendered clips aren't in the manifest.** FFmpeg outputs (pans, cards) are cached by file name: a hash of their inputs, including the keyframe's bytes.
- **Hand edits are safe.** A line is redrafted only when `en` differs from `am_from_en`, so hand corrections to the Amharic survive every re-run.

Media never goes to git (ADR 0003): the manifest is committed, the files it points to stay local.

## Failure handling

- **Validation first.** Every storyboard problem is reported before the first provider call.
- **Retries.** `pipeline/runlog.py` wraps every call: it retries with exponential backoff (2 s, 4 s), and logs one line per attempt with `outcome` ok, retry or error.
  - `PermanentError` (bad key, unknown model, rejected input) is not retried.
  - A rate limit with Google's `retryDelay` of up to 120 s is waited out. A longer one (a daily quota) fails at once, naming the quota (FAILURES.md F3).
- **Fallback models.** Text models are tried in order (`gemini-3.5-flash`, then `gemini-3.8-flash`), and the log shows which one answered (FAILURES.md F1).
- **Missing keys.** Without Cloudflare keys, a shot with no cached keyframe becomes a labelled placeholder, so the film always renders.
- **Timing.** Narration that overlaps or runs past the shots stops the run with the overrun in seconds. Nothing is auto-stretched.
- **Pan shots by default (ADR 0001).** Every shot is a pan shot first. A moving shot (4, 5, 11) with no clip (no keyframe, no Kaggle keys, or the job failed) keeps its pan shot. A missing score candidate falls back to the last chosen track (`outputs/music/chosen.wav`), then to the placeholder pad (ADR 0002). Each fallback is a `"outcome": "fallback"` line in `runs.jsonl` with the reason.
- **Crash safety.** The cache manifest is saved after every item, so a crash mid-run keeps everything already generated. Each save re-reads the manifest first, so two runs at once (a GPU job and `make film`) don't drop each other's entries.

## Decisions

- [ADR 0001](docs/adr/0001-pan-shots-by-default.md): pan shots by default; moving shots only for three key moments.
- [ADR 0002](docs/adr/0002-committed-outputs-and-gpu-fallback.md): GPU stages are optional, with fallbacks. Its "committed outputs" half is superseded by ADR 0003.
- [ADR 0003](docs/adr/0003-no-media-in-the-repo.md): no media in the repo; text evidence only.

## Tests

The pytest suite runs at the pipeline seam (`run.film`) with fake providers and real FFmpeg. It checks only what's visible from outside: errors raised, calls the fakes recorded, lines in `runs.jsonl`, and ffprobe/ffmpeg facts about the MP4s. The cases covered:
- Validation errors happen before any call.
- First run, second run with zero calls, and a one-line change making one call.
- Retries and permanent failures.
- Line placement, subtitle text, and the overlap check.
- The review gate.
- Both exports (size, duration, audio).
- One keyframe regenerated per prompt edit.
- The cost report.

The real adapters are exercised by real runs (`runs.jsonl`), not by unit tests.
