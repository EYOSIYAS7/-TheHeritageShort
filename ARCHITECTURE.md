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
      ├─ cards ───────── FFmpeg ───────▶ outputs/cards/{saying,end}-<aspect>-<hash>.mp4
      └─ assemble ────── FFmpeg ───────▶ outputs/film/film-{16x9,9x16}.mp4 + .en.srt
```

Model-calling stages: script, narration (and the voice trial), characters, keyframes. Pans, cards and assembly are pure FFmpeg: the same inputs give the same output. Not yet built: the score (ACE-Step 1.5) and moving shots (Wan 2.2), both on Kaggle (tickets 06, 07).

## The contract: `storyboard.json`

Validated against `schema/storyboard.schema.json` (JSON Schema 2020-12) before any stage runs, then checked for consistency: unique ids, every line anchored to a real shot, total length 60–90 s. Errors name the shot or line and the field (`shots[1] (shot 2).duration_s: …`). Everything a model sees comes from here, so no prompt text lives in the code:

| Section | Holds | Read by |
|---|---|---|
| `title`, `saying`, `end_card` | card text and durations | cards |
| `style` | style words, copper/gold grade words, the character-sheet prompt, `reference_images` | characters, keyframes |
| `characters` | fixed description + seed for the Father, the Son, the coffee corner | characters, keyframes |
| `script` | translation instruction + seed | script |
| `narrator` | voice, `voice_reason`, style instruction, seed, `voice_trial` | narration, voices |
| `music` | caption, volume points (time → gain) | assemble (pad now, ACE-Step later) |
| `shots[]` | id, act, duration, `pan`/`moving`, keyframe and motion prompts, seed, grade, characters, `references`, pan path per aspect | keyframes, pans, assemble |
| `narration[]` | id, anchored shot + offset, `en` (= subtitle), `am`, `am_pinned`, `am_reviewed`, `am_from_en` | script, narration, assemble |

The script stage is the only one that writes to the storyboard (Amharic drafts), and the file round-trips byte-for-byte through `json.dumps(indent=2)` so its diffs stay readable.

## Providers

`pipeline/providers.py` defines one small interface per capability: `TextProvider`, `SpeechProvider`, `ImageProvider` and `GpuJobs`. The real adapters live in `pipeline/adapters.py`. They are thin wrappers that use the standard library only:
- `GeminiText` and `GeminiSpeech` call the Gemini API (`generateContent`).
- `CloudflareImage` calls Workers AI with a multipart form.
- `KaggleJobs` calls the Kaggle REST API (authentication only so far).

`default_providers()` reads the keys from `.env` only. Tests inject fakes that write tiny real media and record their calls.

## Caching

`pipeline/cache.py` hashes exactly the inputs that affect an item:
- **TTS:** model, text, language, voice, style and seed.
- **Image:** model, prompt (which already contains the style, grade and character descriptions), seed, size and reference images.
- **Amharic draft:** prompt and seed.

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
- **Pan shots by default (ADR 0001).** Every shot is a pan shot first. The three moving shots (4, 5, 11) fall back to their pan shot, and the score to the placeholder pad, when Kaggle is unavailable (ADR 0002).
- **Crash safety.** The cache manifest is saved after every item, so a crash mid-run keeps everything already generated.

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
