# Tomorrow, Dad (ነገ አባባ ነገ)

An 89.5 s short film built around the Amharic saying **በእጅ የያዙት ወርቅ እንደ መዳብ ይቆጠራል** ("gold held in the hand is counted as copper"), and the pipeline that regenerates it from one file, `storyboard.json`.

An elderly Father makes coffee every morning and wants to talk; his Son keeps promising "tomorrow", until the Father has a stroke. The film is a composite story: no real person is depicted (`ETHICS.md`). It is narrated in Amharic with burned-in English subtitles, and exported at 16:9 and 9:16.

## One command

```sh
cp .env.example .env    # then fill in the keys (see "Keys" below)
make film
```

**Requirements:**
- `python3` (3.12+) with `venv`, plus `make`.
- `ffmpeg`/`ffprobe` 7+ with libass and libfreetype.
- The Noto fonts: Noto Sans and Noto Sans Ethiopic.

On Ubuntu: `sudo apt install make python3-venv ffmpeg fonts-noto-core`. The first run creates `.venv/` and installs the one Python dependency (`jsonschema`).

**Output:** `outputs/film/film-16x9.mp4` and `outputs/film/film-9x16.mp4`, with their English subtitle files (`*.en.srt`).

### What `make film` does, in order

1. **Validate** `storyboard.json` against `schema/storyboard.schema.json`. It also checks shot references and that the film is 60–90 s long. Any problem stops the run before a single model call, naming the shot or line and the field.
2. **Script:** Gemini drafts the Amharic for every narration line that isn't pinned, from its English and the translation instruction in the storyboard. Drafts are written back marked unreviewed. A line is redrafted only when its English changes. `make film` refuses to continue while any line is unreviewed (`make review` lists them).
3. **Narration:** Gemini TTS (`gemini-3.8-flash-tts`, voice Enceladus) speaks each line into its own file. Each line's audio is measured: one that overlaps the next line or runs past the last shot stops the run, with the overrun in seconds.
4. **Character sheet:** Cloudflare Workers AI, FLUX.2 klein 4B, makes one reference image each for the Father, the Son and the coffee corner.
5. **Keyframes:** one 16:9 image per shot (12). The prompt is built only from storyboard text, and each shot can be conditioned on its main character's reference image.
6. **Pan shots:** FFmpeg slowly pans and zooms across each keyframe, for exactly the shot's length, along its own path for 16:9 and for 9:16.
7. **Cards:** the saying (Amharic in Noto Sans Ethiopic, plus the English) and the end card stating the film was made with AI.
8. **Assembly:** each line is placed at its shot's start plus offset, and the English subtitles are burned in. A placeholder music bed is ducked under the voice. Loudness is normalised (-14 LUFS target), then both MP4s are exported.

**Logging and caching:**
- Every model call, every retry and every cache hit is one JSON line in `runs.jsonl`.
- Every generated file is cached by a hash of exactly its inputs (`outputs/cache-manifest.json`). A re-run only calls a model for what changed: edit one narration line or one keyframe prompt, run `make film`, and the log shows exactly one new call.

### Keys

Copy `.env.example` to `.env` (git-ignored) and fill it in. Keys are read only from `.env`, never from the shell environment.

| Key | Used for | Where to get it |
|---|---|---|
| `GEMINI_API_KEY` | Amharic drafts, narration | aistudio.google.com/apikey (free tier) |
| `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` | character sheet, keyframes | dash.cloudflare.com: the Workers AI page, then API Tokens with the "Workers AI" template |
| `KAGGLE_USERNAME`, `KAGGLE_KEY` | moving shots and score (not used yet) | kaggle.com → Settings → API |

**No media in the repo** (ADR 0003): images, audio and video are git-ignored, so the repo holds code, text, logs and docs, and the finished film is submitted separately. On a fresh clone, `make film` therefore regenerates the media with your keys and caches it in `outputs/`.
- Without the Cloudflare keys, shots show labelled placeholders.
- Without the Gemini key, narration stops with a message naming the missing key.

### Cost and time

All measured numbers are in `COSTS.md` (`make costs` prints them from `runs.jsonl`).

- **Money:** $0. Every call ran on a free tier. The same calls at list price come to about $0.11.
- **Time:** from a fresh clone with keys, a full build makes 15 images, 11 narration lines and 12 Amharic drafts.
  - Model time: about 14 s per image and about 3–20 s per TTS or text call.
  - FFmpeg: about 5 minutes to render the pans and both exports.
  - Altogether: about 15–20 minutes.
- **The binding limit is free-tier quota, not money.**
  - Gemini TTS allows 10 requests a day per Google Cloud project (FAILURES.md F3).
  - Workers AI gives 10,000 neurons a day, about 45 keyframes at this size.

## Other commands

| Command | What it does |
|---|---|
| `make review` | lists narration lines whose Amharic isn't reviewed, English beside Amharic. Fix `am` in `storyboard.json`, then set `am_reviewed: true`. |
| `make voices` | the voice trial: one narration line in each candidate voice (`narrator.voice_trial`), to pick the narrator by ear |
| `make radio-cut` | narration, subtitles and music on a black screen (16:9), for user test 1. Allows unreviewed Amharic. |
| `make rough-cut` | everything in `make film` but allows unreviewed Amharic; `outputs/film/rough-cut-*.mp4` |
| `make costs` | per-stage summary of `runs.jsonl`: calls, retries, failures, cache hits, latency, image list price |
| `make test` | pytest at the pipeline seam (fake providers, real FFmpeg) |
| `make typecheck` | mypy, strict |

## Where to read more

| File | What's in it |
|---|---|
| `DESIGN.md` | audience, intent, story, structure, look, and the user tests with what changed |
| `ARCHITECTURE.md` | stages, the storyboard contract, caching, failure handling |
| `EXPERIMENTS.md` | hypothesis → change → result |
| `FAILURES.md` | what broke, what was tried, what fixed it |
| `COSTS.md` | measured calls, latency and list-price equivalent per stage |
| `ETHICS.md` | consent (composite story), licences, labelling |
| `docs/adr/` | decisions: pan shots by default, GPU fallbacks, no media in the repo |

**Not done yet:**
- The moving shots (Wan 2.2 on Kaggle, ticket 07) and the ACE-Step score (06). Until they land, shots 4, 5 and 11 are pan shots, and the music is a generated placeholder pad (ADR 0001).
